"""CPU-only prototype evidence; no Blender, extraction, GPU or network."""
from pathlib import Path
import ast
import difflib
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

PROTOTYPE = Path(__file__).resolve().parent
ROOT = PROTOTYPE.parents[1]
STUDIO = PROTOTYPE / "Studio"
PIN = ROOT / "output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
INVENTORY = ROOT / "output/sfm-extra-native-inventory/portable-root-639301165838922272"
OWNED = ["tools/prepare_source.py", "tools/blender_source_bridge.py", "tools/source_appearance.py", "tests/test_source_appearance.py"]
COMMIT = "85fa482b3ef1ed752e8a97191b5ea7b235cea7aa"
sys.dont_write_bytecode = True


def stamp(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}


def main():
    (STUDIO / "output").mkdir(exist_ok=True)
    baseline = PROTOTYPE / "baseline"
    baseline.mkdir(exist_ok=True)
    base_files = {}
    for name in OWNED[:2]:
        data = subprocess.check_output(["git", "cat-file", "blob", COMMIT + ":" + name], cwd=ROOT)
        path = baseline / Path(name).name
        if path.exists():
            assert path.read_bytes() == data
        else:
            path.write_bytes(data)
        base_files[name] = path
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", HYBRID_SOURCEIO=str(PIN), HAS_APPEARANCE_BASE_BRIDGE=str(base_files["tools/blender_source_bridge.py"]))
    before = {name: stamp(STUDIO / name) for name in OWNED}
    protected = [ROOT / name for name in OWNED[:2]] + [PIN / "__init__.py", PIN / "blender_bindings/shared/skins.py", PIN / "blender_bindings/models/mdl49/import_mdl.py"]
    source_before = {str(path): stamp(path) for path in protected}
    plans = json.loads((INVENTORY / "staging.json").read_bytes())
    cases = json.loads((ROOT / "docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json").read_bytes())["next_cases"]
    selected = [cases["multi_skin_glove"], cases["keiki_tools_chisels"]]
    full_metadata = json.loads((INVENTORY / "metadata.json").read_bytes())
    full_by_sha = {row["sha256"]: row for row in full_metadata["models"]}
    assert full_by_sha[selected[0]["sha256"]]["skin_groups"] == selected[0]["skin_groups"]
    tree = ast.parse((STUDIO / "tests/test_source_appearance.py").read_text())
    keiki_literal = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "KEIKI_SKINS" for target in node.targets))
    assert full_by_sha[selected[1]["sha256"]]["skin_groups"] == keiki_literal
    archives = {row["archive"]: row for row in plans["archives"]}
    definitions = {(row["archive"], row["member"]): row for row in plans["models"]}
    inputs = {}
    for case in selected:
        original = Path(archives[case["archive"]]["path"])
        path = INVENTORY / "stage" / definitions[(case["archive"], case["member"])]["staged_member"]
        assert stamp(original)["sha256"] == archives[case["archive"]]["sha256"]
        assert stamp(path)["sha256"] == case["sha256"]
        inputs[str(original)] = stamp(original)
        inputs[str(path)] = stamp(path)
    reports = []
    for script, expected in [("test_source_appearance.py", 18), ("test_source_failure.py", 3)]:
        args = [sys.executable, "-u", str(STUDIO / "tests" / script), "-v"]
        result = subprocess.run(args, cwd=STUDIO, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        log = result.stdout + result.stderr
        target = PROTOTYPE / (script.removesuffix(".py") + "-final.log")
        target.write_text(log, encoding="utf-8")
        assert result.returncode == 0 and f"Ran {expected} tests" in log and "\nOK" in log and "skipped" not in log, log
        reports.append({"command": args, "exit": result.returncode, "tests": expected, "log": str(target), "log_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "gpu": False})
    spec = importlib.util.spec_from_file_location("appearance_checked_binding", STUDIO / "tools/source_appearance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native_bindings = []
    for case in selected:
        native = INVENTORY / "stage" / definitions[(case["archive"], case["member"])]["staged_member"]
        request = {"format": module.FORMAT, "source_sha256": archives[case["archive"]]["sha256"], "native_mdl_sha256": case["sha256"], "skin": 0, "bodygroups": {}}
        assert module.bind(request, request["source_sha256"], native) == request
        native_bindings.append({"archive": case["archive"], "member": case["member"], "sha256": case["sha256"], "existing_private_definition": str(native), "verified_binding_only": True})
    for name in OWNED:
        ast.parse((STUDIO / name).read_text(encoding="utf-8"))
    assert all(stamp(STUDIO / name) == value for name, value in before.items())
    assert all(stamp(Path(path)) == value for path, value in source_before.items())
    assert all(stamp(Path(path)) == value for path, value in inputs.items())
    patch = ""
    base = json.loads((PROTOTYPE / "base-source.json").read_bytes())
    for name in OWNED:
        original = base_files[name].read_text() if name in base_files else ""
        patch += "".join(difflib.unified_diff(original.splitlines(True), (STUDIO / name).read_text().splitlines(True), fromfile="85fa482/" + name, tofile="prototype/" + name))
    (PROTOTYPE / "runtime-review.patch").write_text(patch, encoding="utf-8", newline="\n")
    report = {"format": "has_source_appearance_prototype_cpu_1", "base_commit": COMMIT, "source_copy_files": base["files"], "owned_files": before, "runs": reports, "cpu_tests": 21, "skips": 0, "failures": 0, "native_definition_hash_bindings": native_bindings, "actual_selected_skin_rows_confirmed": True, "metadata_provenance": {"compact_inventory": stamp(ROOT / "docs/benchmarks/sfm_native_feature_inventory_2026-11-12.json"), "complete_private_metadata": stamp(INVENTORY / "metadata.json")}, "source_and_runtime_before": source_before, "source_and_runtime_unchanged": True, "protected_inputs_before": inputs, "protected_inputs_unchanged": True, "prototype_files_unchanged_during_tests": True, "all_owned_ast_parse": True, "gpu": False, "blender_app_invoked": False, "native_extraction": False, "real_skin_helper_scope": "Actual pinned functions executed with inert materials/containers; no real Blender material slot, mesh, skeleton, morph, texture or exporter proof.", "worker_scope": "Actual prepare_source.main request path with conversion-context and Popen mocked; no native scene conversion.", "limits": ["Static import-time appearance prototype only; no app selector or project-schema change.", "Native full dependency staging, Blender conversion, rendered appearance, HAS/Undo/cold replay, real morph preservation and movie agreement remain UNRUN.", "Runtime/animated bodygroup or skin switching and native jiggle/assembly fidelity remain separate.", "Ambiguous duplicate or nonidentity default skin columns refuse nondefault selection rather than guessing native mesh-slot mappings."]}
    (PROTOTYPE / "cpu-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cpu_tests": report["cpu_tests"], "failures": 0, "native_hash_bindings": len(native_bindings), "protected_inputs_unchanged": True, "gpu": False, "blender_app_invoked": False}, indent=2))


if __name__ == "__main__":
    main()
