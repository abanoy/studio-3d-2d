"""Port the reviewed five Python seams only; no tool/app/test is launched here."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DRAFT = ROOT / "experiments/source_appearance/static_choice_draft_20261113"
HEAD = "489215fcbfb69acde05d4a1341cc872cc69a9132"
TOOLS = ("source_appearance.py", "source_mdl_choices.py", "source_choice_io.py", "prepare_source.py", "blender_source_bridge.py")

def stamp(path):
    raw = path.read_bytes(); info = path.stat()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": info.st_mtime_ns}

def main():
    require = lambda ok, why: None if ok else (_ for _ in ()).throw(RuntimeError(why))
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == HEAD, "Main HEAD changed")
    index = json.loads((DRAFT / "SOURCE_INDEX.json").read_bytes())
    context = json.loads((DRAFT / "FINAL_SOURCE_CONTEXT.json").read_bytes())
    frozen = {}
    for name, expected in index["files"].items():
        path = DRAFT / "overlay" / name
        actual = stamp(path)
        require(all(actual[k] == expected[k] for k in ("sha256", "bytes")), "Frozen draft differs: " + name)
        frozen[name] = actual
    before = {}
    for name, expected in context["main_files"].items():
        if not name.startswith("tools/"): continue
        actual = stamp(ROOT / name)
        require(all(actual[k] == expected[k] for k in ("sha256", "bytes")), "Current importer baseline differs: " + name)
        before[name] = actual
    for name in TOOLS[:3]: require(not (ROOT / "tools" / name).exists(), "New tool already exists: " + name)
    for name in ("test_source_mdl_choices.py", "test_source_appearance.py"):
        require(not (ROOT / "tests" / name).exists(), "New test already exists: " + name)
    proposal = {"tools/" + name: (DRAFT / "overlay/tools" / name).read_bytes() for name in TOOLS}
    catalogue = (DRAFT / "overlay/tests/test_source_mdl_choices.py").read_text(encoding="utf-8")
    old = 'destination = HERE.parent.parent / "runs" / (str(time.time_ns()) + "-catalogue-" + uuid.uuid4().hex[:8])'
    new = 'destination = HERE.parent / "output/source-mdl-choices-cpu" / (str(time.time_ns()) + "-catalogue-" + uuid.uuid4().hex[:8])'
    require(catalogue.count(old) == 1, "Catalogue runner seam differs")
    catalogue = catalogue.replace(old, new)
    proposal["tests/test_source_mdl_choices.py"] = catalogue.encode("utf-8")
    tests = (DRAFT / "overlay/tests/test_static_choices_draft.py").read_text(encoding="utf-8")
    require(tests.count("TASK = OVERLAY.parent") == 1, "Appearance runner root seam differs")
    tests = tests.replace("TASK = OVERLAY.parent", 'TASK = OVERLAY / "output/source-appearance-cpu"')
    start = tests.index("    def test_ui_default_map_and_nondefault_source_seams_are_present(self):")
    end = tests.index("\n\ndef main():", start)
    tests = tests[:start] + '''    def test_json_numeric_request_boundary_requires_canonical_integer_keys(self):
        # JSON/Godot metadata numbers can be floats. Worker identity remains
        # strict; the caller must construct canonical integer-index strings.
        decoded = json.loads(json.dumps({**request(2), "bodygroups": {0.0: 0}}))
        with self.assertRaises(ValueError): A.validate(decoded)
        canonical = {**decoded, "bodygroups": {str(int(key)): value for key, value in {0.0: 0}.items()}}
        self.assertEqual(A.validate(canonical)["bodygroups"], {"0": 0})
        for bad in [{"0.0": 0}, {"0": 0.0}, {"0": False}, {"00": 0}]:
            with self.assertRaises(ValueError): A.validate({**request(), "bodygroups": bad})
''' + tests[end:]
    tests = tests.replace('"studio_static_choices_draft_cpu_1"', '"studio_source_appearance_cpu_1"')
    tests = tests.replace('"source_preserved": preserved, "sources": before, "run": str(RUN),',
        '"source_preserved": preserved, "sources": before, "run": str(RUN), "main_python_port": True,')
    proposal["tests/test_source_appearance.py"] = tests.encode("utf-8")
    backup = OUT / "before"; backup.mkdir(exist_ok=False)
    for name in ("tools/prepare_source.py", "tools/blender_source_bridge.py"):
        target = backup / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / name, target)
    # Every source seam above was admitted before the first main-file write.
    for name, raw in proposal.items(): (ROOT / name).write_bytes(raw)
    for name, expected in before.items():
        if name not in proposal: require(stamp(ROOT / name) == expected, "Shared importer dependency changed")
    require(all(stamp(DRAFT / "overlay" / name) == expected for name, expected in frozen.items()), "Frozen experiment changed")
    changed = {name: stamp(ROOT / name) for name in proposal}
    patches = []
    for name in ("tools/prepare_source.py", "tools/blender_source_bridge.py"):
        patches.extend(difflib.unified_diff((backup / name).read_text(encoding="utf-8").splitlines(keepends=True),
            (ROOT / name).read_text(encoding="utf-8").splitlines(keepends=True), fromfile="a/" + name, tofile="b/" + name))
    (OUT / "worker-port.patch").write_text("".join(patches), encoding="utf-8")
    (OUT / "PORT_RECEIPT.json").write_text(json.dumps({"format": "studio_source_appearance_main_python_port_1",
        "base_head": HEAD, "functional_baseline": "12071fe182a17d17e2a1547c7dbb97f6aa4dd160",
        "frozen_source_index_sha256": hashlib.sha256((DRAFT / "SOURCE_INDEX.json").read_bytes()).hexdigest(),
        "main_before": before, "main_after": changed, "frozen_experiment_preserved": True,
        "shared_importer_dependencies_preserved": True, "python_tests": "UNRUN; awaiting coordinated source freeze",
        "native_conversion_graphics_original_extraction": "UNRUN", "git_mutation": False,
        "test_adaptation": "Fresh main/output paths; authored fixtures from sibling test module; draft GD source-string assertion replaced with strict JSON request numeric-identity behavior. Actual GD/UI coverage is root-owned."}, indent=2), encoding="utf-8")
    print(json.dumps({"ported_files": len(changed), "main_after": changed, "tests": "UNRUN"}))

if __name__ == "__main__": main()
