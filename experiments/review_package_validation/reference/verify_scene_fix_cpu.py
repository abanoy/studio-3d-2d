"""Reproduce the 22 CPU/parse/scene-resource checks from the inline fix audit.

Run from the repository, using the retained c678 review snapshot and first
failed six-project replay. Each invocation creates a fresh output directory.
No application scene is instantiated; no GPU or owner launcher runs.
"""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
FIRST_FAILED = ROOT / "output/owner-review-validation/replay-1794541459557567800"


def stamp(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}


def main():
    owned = ROOT / "output/owner-review-validation" / ("scene-fix-cpu-replay-" + str(time.time_ns()))
    owned.mkdir()
    script = ROOT / "tools/verify_owner_review.py"
    ast.parse(script.read_text())
    spec = importlib.util.spec_from_file_location("review_scene_fix", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EVIDENCE_ROOT = owned
    case = owned / "case"
    (case / "has-cache/payload").mkdir(parents=True)
    (case / "has-cache-escape/payload").mkdir(parents=True)
    checks = {}

    def check(name, ok):
        checks[name] = bool(ok)
        if not ok:
            raise AssertionError(name)

    actual = case / "has-cache/payload"
    check("native_windows_separator_path_contained", module.cache_containment(case, str(actual))["contained"])
    check("forward_separator_path_contained", module.cache_containment(case, str(actual).replace("\\", "/"))["contained"])
    check("dot_segment_path_contained", module.cache_containment(case, str(actual / ".." / "payload"))["contained"])
    check("similar_prefix_sibling_refused", not module.cache_containment(case, str(case / "has-cache-escape/payload"))["contained"])
    check("cache_root_itself_refused", not module.cache_containment(case, str(case / "has-cache"))["contained"])
    check("other_existing_source_directory_refused", not module.cache_containment(case, str(ROOT / "tools"))["contained"])
    check("missing_directory_refused", not module.cache_containment(case, str(case / "has-cache/absent"))["contained"])
    check("missing_report_refused", not module.cache_containment(case, None)["contained"])
    scene = module.write_replay_scene(case)
    scene_text = scene.read_text()
    check("external_script_path_json_escaped", ("path=" + json.dumps(str(module.REPLAY_SCRIPT).replace("\\", "/"), ensure_ascii=False)) in scene_text)
    check("generated_scene_has_node_harness", 'type="Node"' in scene_text and 'ExtResource("1_replay")' in scene_text)
    try:
        module.write_replay_scene(case)
    except RuntimeError:
        checks["existing_scene_refuses_overwrite"] = True
    else:
        raise AssertionError("overwrote existing scene")
    source = (ROOT / "tests/owner_review_replay.gd").read_text()
    check("node_harness_uses_normal_startup_signal", "extends Node\n" in source and "startup_recovery_finished.connect(startup_completed)" in source)
    check("home_not_forced", "open_home(" not in source and ".home.show(" not in source and ".change_mode(" not in source)
    check("home_assertion_preserved", "fresh process starts empty at Home" in source)

    studio = ROOT / "output/owner-review-verified/Studio"
    builder = json.loads((ROOT / "output/owner-review-verified/source-snapshot-verification.json").read_bytes())
    before = {name: stamp(studio / name) for name in builder["source_hashes"]}
    check("built_snapshot_source_matches_before", all(before[name]["sha256"] == sha for name, sha in builder["source_hashes"].items()))
    runner = module.load_runner(studio)
    args = runner.command(extra=[str(scene), "--audio-driver", "Dummy", "--log-file", str(case / "engine.log"), "--", str(case / "request.json")])
    check("scene_command_contains_no_script_flag", "--script" not in args)
    check("scene_command_uses_private_desktop", "--receipt" in args and "private_desktop.py" in args[1])
    check("scene_is_before_user_argument_boundary", args.index(str(scene)) < args.index("--", args.index("--path")))

    # Engine call 1: parse the Node script only. This does not run _ready().
    parse_args = runner.command(str(ROOT / "tests/owner_review_replay.gd"), headless=True, extra=["--check-only", "--log-file", str(owned / "syntax-engine.log")])
    process = subprocess.run(parse_args, cwd=studio, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    log = process.stdout + process.stderr
    (owned / "syntax.log").write_text(log, encoding="utf-8")
    check("headless_node_script_parse_passed", process.returncode == 0 and not any(bad in log for bad in ["ERROR:", "FAIL ", "ObjectDB instances leaked"]))

    # Engine call 2: a headless resource loader checks the external PackedScene.
    # It deliberately does not instantiate that scene or its app children.
    probe = owned / "load_scene.gd"
    probe.write_text('extends SceneTree\nfunc _initialize() -> void:\n\tvar loaded=load(OS.get_cmdline_user_args()[0])\n\tif loaded is PackedScene:\n\t\tprint("OWNER_REPLAY_SCENE_LOAD_OK")\n\t\tquit(0)\n\telse:\n\t\tpush_error("External replay scene did not load as PackedScene")\n\t\tquit(1)\n', encoding="utf-8")
    load_args = runner.command(str(probe), headless=True, extra=["--log-file", str(owned / "scene-load-engine.log"), "--", str(scene)])
    loaded = subprocess.run(load_args, cwd=studio, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    load_log = loaded.stdout + loaded.stderr
    (owned / "scene-load.log").write_text(load_log, encoding="utf-8")
    check("external_scene_loads_as_packed_scene_without_instantiation", loaded.returncode == 0 and "OWNER_REPLAY_SCENE_LOAD_OK" in load_log and not any(bad in load_log for bad in ["ERROR:", "FAIL ", "ObjectDB instances leaked"]))

    after = {name: stamp(studio / name) for name in builder["source_hashes"]}
    check("built_snapshot_source_hash_size_mtime_unchanged", before == after)
    check("all_six_original_failed_results_retained", len(list(FIRST_FAILED.glob("*/result.json"))) == 6)
    files = {name: stamp(ROOT / name) for name in ["tools/verify_owner_review.py", "tests/owner_review_replay.gd", "docs/owner_review_validation.md"]}
    report = {"format": "has_owner_review_scene_fix_cpu_1", "checks": checks, "count": len(checks), "all_passed": all(checks.values()), "source_files": files, "snapshot_commit": builder["source_commit"], "snapshot_files_checked": len(before), "snapshot_unchanged": before == after, "command_example": args, "syntax_command": parse_args, "syntax_exit": process.returncode, "syntax_log": str(owned / "syntax.log"), "scene_load": {"command": load_args, "exit": loaded.returncode, "log": str(owned / "scene-load.log"), "scene_instantiated": False, "gpu": False}, "generated_scene": str(scene), "gpu_launched": False, "engine_actions": "Version probes, headless --check-only, and a headless resource-only PackedScene load. No app scene instantiation or graphical replay.", "original_failed_attempt": str(FIRST_FAILED), "reproduction_source": str(Path(__file__).resolve())}
    (owned / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(owned), "checks": len(checks), "all_passed": report["all_passed"], "snapshot_files_checked": len(before), "snapshot_unchanged": report["snapshot_unchanged"], "syntax_exit": process.returncode, "scene_load_exit": loaded.returncode, "gpu": False}, indent=2))


if __name__ == "__main__":
    main()
