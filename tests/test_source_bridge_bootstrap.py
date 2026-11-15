"""Execute the real bridge bootstrap in a fresh host lacking the tools directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tools/blender_source_bridge.py"
APPEARANCE = ROOT / "tools/source_appearance.py"
JIGGLE_MODULES = [ROOT / "tools" / name for name in (
    "source_jiggle_metadata.py", "source_jiggle_values.py", "source_mdl_snapshot.py",
    "source_jiggle_crosswalk.py", "source_bone_metadata.py", "source_bone_export.py")]

# The prefix is cut at the next local dependency, before any SourceIO library,
# Blender API or worker function is used. It still executes the actual request,
# host loader, sys.path insertion and source_appearance import in source order.
PROBE = r'''
import ast, hashlib, json, os, sys, types
from pathlib import Path
bridge, request_path, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
tools = bridge.parent.resolve()
assert all(not p or Path(p).resolve() != tools for p in sys.path)
assert "source_appearance" not in sys.modules and "SourceIO" not in sys.modules
sys.modules["bpy"] = types.ModuleType("bpy")
sys.modules["bpy"].bootstrap_host_stub = True
tree = ast.parse(bridge.read_text(encoding="utf-8"), filename=str(bridge))
boundary = next(i for i, node in enumerate(tree.body)
                if isinstance(node, ast.ImportFrom) and node.module == "asset_audit")
body = tree.body[:boundary]
imports = [node for node in body if isinstance(node, ast.Import)
           and any(alias.name == "source_appearance" for alias in node.names)]
assert len(imports) == 1, "Expected the real module dependency before worker imports"
if mode == "early":
    body = [imports[0]] + [node for node in body if node is not imports[0]]
prefix = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
sys.argv = [str(bridge), "--", str(request_path)]
namespace = {"__name__": "source_bridge_bootstrap_probe", "__file__": str(bridge)}
result = {"initial_tools_absent": True, "mode": mode}
try:
    exec(compile(prefix, str(bridge), "exec"), namespace)
    module = namespace["source_appearance"]
    sample = {"format": "studio_source_appearance_request_1",
              "source_sha256": "a" * 64, "native_mdl_sha256": "b" * 64,
              "skin": 1, "bodygroups": {"0": 0, "1": 1}}
    checked = module.validate(sample)
    result.update(ok=True, appearance_file=str(Path(module.__file__).resolve()),
                  appearance_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                  validated_request=checked, no_bpy=os.environ.get("NO_BPY"),
                  dont_write_bytecode=sys.dont_write_bytecode)
    jiggle = namespace["source_jiggle_metadata"]
    capture = namespace["source_mdl_snapshot"]
    crosswalk = namespace["source_bone_export"]
    result["jiggle_modules"] = {name: {"file": str(Path(value.__file__).resolve()),
        "sha256": hashlib.sha256(Path(value.__file__).read_bytes()).hexdigest()}
        for name, value in (("source_jiggle_metadata", jiggle),
                            ("source_jiggle_values", jiggle.Raw),
                            ("source_mdl_snapshot", capture),
                            ("source_jiggle_crosswalk", crosswalk.C),
                            ("source_bone_metadata", crosswalk.M),
                            ("source_bone_export", crosswalk))}
except BaseException as error:
    result.update(ok=False, error_type=type(error).__name__,
                  error_name=getattr(error, "name", None), error=str(error))
host = sys.modules.get("SourceIO")
result["sourceio_stub_loaded"] = bool(host and getattr(host, "bootstrap_host_stub", False))
result["sourceio_library_modules"] = [name for name in sys.modules if name.startswith("SourceIO.library")]
result["worker_dependency_loaded"] = "asset_audit" in sys.modules
print(json.dumps(result))
'''


def identity(path):
    info = path.stat()
    return info.st_size, info.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


class SourceBridgeBootstrapTests(unittest.TestCase):
    def probe(self, mode):
        before = {path: identity(path) for path in [BRIDGE, APPEARANCE, *JIGGLE_MODULES]}
        with tempfile.TemporaryDirectory(prefix="has-source-bootstrap-") as temporary:
            root = Path(temporary).resolve()
            host = root / "sourceio-host-stub"
            host.mkdir()
            (host / "__init__.py").write_text("bootstrap_host_stub = True\n", encoding="utf-8")
            request = root / "request.json"
            request.write_text(json.dumps({"output": str(root / "unused-output"), "sourceio": str(host)}), encoding="utf-8")
            request_before = identity(request)
            args = [sys.executable, "-I", "-S", "-B", "-c", PROBE, str(BRIDGE), str(request), mode]
            process = subprocess.run(args, cwd=root, capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", timeout=20,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertFalse((root / "unused-output").exists(), "The conversion worker must not run")
            self.assertEqual(identity(request), request_before)
            result = json.loads(process.stdout)
        self.assertEqual({path: identity(path) for path in before}, before)
        return result

    def test_actual_prefix_resolves_local_appearance_without_preloaded_tools(self):
        result = self.probe("current")
        self.assertTrue(result["initial_tools_absent"])
        self.assertTrue(result["ok"], result)
        self.assertEqual(Path(result["appearance_file"]), APPEARANCE.resolve())
        self.assertEqual(result["appearance_sha256"], identity(APPEARANCE)[2])
        for path in JIGGLE_MODULES:
            self.assertEqual(result["jiggle_modules"][path.stem],
                             {"file": str(path.resolve()), "sha256": identity(path)[2]})
        self.assertEqual(result["validated_request"]["skin"], 1)
        self.assertEqual(result["validated_request"]["bodygroups"], {"0": 0, "1": 1})
        self.assertTrue(result["sourceio_stub_loaded"])
        self.assertEqual(result["sourceio_library_modules"], [])
        self.assertFalse(result["worker_dependency_loaded"])
        self.assertEqual(result["no_bpy"], "1")
        self.assertTrue(result["dont_write_bytecode"])

    def test_old_early_import_order_fails_in_the_same_isolated_host(self):
        result = self.probe("early")
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error_type"], "ModuleNotFoundError")
        self.assertEqual(result["error_name"], "source_appearance")
        self.assertFalse(result["sourceio_stub_loaded"])
        self.assertEqual(result["sourceio_library_modules"], [])
        self.assertFalse(result["worker_dependency_loaded"])


if __name__ == "__main__":
    unittest.main()
