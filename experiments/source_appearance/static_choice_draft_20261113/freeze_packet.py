"""Index this draft and compact metadata without publishing or changing main."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import shutil
import subprocess

from build_candidate import ROOT, TASK, BASE, FILES, stamp

DEPENDENCIES = ("tools/source_paths.py", "tools/source_installation.py", "tools/source_case.py")
PORT = ("tools/source_appearance.py", "tools/prepare_source.py", "tools/blender_source_bridge.py",
        "tools/source_mdl_choices.py", "tools/source_choice_io.py", "src/source_import.gd",
        "src/source_choice_dialog.gd", "tests/test_static_choices_draft.py", "tests/test_source_mdl_choices.py")

def main():
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != BASE:
        raise RuntimeError("Frozen HEAD changed")
    initial = json.loads((TASK / "BASE_SOURCE_CONTEXT.json").read_bytes())
    records = {}
    for name in FILES + DEPENDENCIES:
        raw = (ROOT / name).read_bytes()
        commit = subprocess.check_output(["git", "show", BASE + ":" + name], cwd=ROOT)
        if raw.replace(b"\r\n", b"\n") != commit.replace(b"\r\n", b"\n"):
            raise RuntimeError("Main working source changed: " + name)
        records[name] = stamp(ROOT / name)
        if name in initial["source_files"] and records[name] != initial["source_files"][name]:
            raise RuntimeError("Main source bytes/stamp changed: " + name)
    prototype = ROOT / "experiments/source_appearance/overlay/tools/source_appearance.py"
    if stamp(prototype) != initial["prototype_validator"]:
        raise RuntimeError("Published validator changed")
    overlay = TASK / "overlay"
    expected = {p.relative_to(overlay).as_posix(): stamp(p) for p in sorted(overlay.rglob("*")) if p.is_file()}
    # The copied baseline function is recoverable, and exactly matches this base.
    test_tree = ast.parse((overlay / "tests/test_static_choices_draft.py").read_text(encoding="utf-8"))
    baseline_text = next(ast.literal_eval(n.value) for n in test_tree.body if isinstance(n, ast.Assign)
                         and any(isinstance(t, ast.Name) and t.id == "BASE_LOAD_MODEL" for t in n.targets))
    base_tree = ast.parse((ROOT / "tools/blender_source_bridge.py").read_text(encoding="utf-8"))
    base_function = next(n for n in base_tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_model")
    fixed_function = ast.parse(baseline_text).body[0]
    if ast.dump(base_function, include_attributes=False) != ast.dump(fixed_function, include_attributes=False):
        raise RuntimeError("Test baseline no longer matches the recorded base")
    diffs = []
    for name in ("tools/prepare_source.py", "tools/blender_source_bridge.py", "src/source_import.gd"):
        before = (ROOT / name).read_text(encoding="utf-8").splitlines(keepends=True)
        after = (overlay / name).read_text(encoding="utf-8").splitlines(keepends=True)
        diffs.extend(difflib.unified_diff(before, after, fromfile="a/" + name, tofile="b/" + name))
    (TASK / "existing-main-seams.patch").write_text("".join(diffs), encoding="utf-8")
    context = {"format": "studio_static_choice_draft_context_1", "base_revision": BASE,
        "unshipped": True, "source_context": "output_only_overlay_from_exact_main",
        "main_files": records, "main_initial_files_preserved": True,
        "published_validator_preserved": True, "baseline_load_model_ast_matches_base": True,
        "proposed_port_files": list(PORT), "unchanged_isolation_dependencies": [name for name in expected if name not in PORT],
        "actual_runtime": {"godot": "UNRUN", "blender": "UNRUN", "conversion": "UNRUN", "gpu": "UNRUN", "native_models_read": 0},
        "pure_python": {"executable": r"C:\Program Files\Python313\python.exe",
                        "sha256": hashlib.sha256(Path(r"C:\Program Files\Python313\python.exe").read_bytes()).hexdigest()},
        "historical_prototype_evidence": ["docs/sfm_static_appearance_actual_2026-11-13.md", "docs/sfm_derived_render_app_2026-11-13.md"],
        "note": "Historical prototype/native and derived app passes do not certify this candidate"}
    (TASK / "FINAL_SOURCE_CONTEXT.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
    source_index = {"format": "studio_source_only_draft_index_1", "base_revision": BASE, "files": expected,
                    "files_count": len(expected), "bytes": sum(row["bytes"] for row in expected.values())}
    (TASK / "SOURCE_INDEX.json").write_text(json.dumps(source_index, indent=2), encoding="utf-8")
    (TASK / "PRESERVATION.json").write_text(json.dumps({"base_revision": BASE, "main_files_exact": True,
        "main_head_exact": True, "main_files": records, "overlay_index_sha256": stamp(TASK / "SOURCE_INDEX.json")["sha256"],
        "private_native_inputs_read_or_written": False, "installed_runtime_changes": False,
        "gpu_blender_godot_conversion_launched": False, "main_git_mutations": False}, indent=2), encoding="utf-8")
    print(json.dumps({"source_index": stamp(TASK / "SOURCE_INDEX.json"), "context": stamp(TASK / "FINAL_SOURCE_CONTEXT.json"),
                      "files": len(expected), "source_bytes": source_index["bytes"], "main_preserved": True}))

if __name__ == "__main__":
    main()
