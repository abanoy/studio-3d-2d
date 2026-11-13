"""Freeze source/metadata readiness after two no-conversion preflights."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
REVISION = "cf7a805dd6ec76890da048ff28aa0080757e7c34"
PYTHON = r"C:\Program Files\Python313\python.exe"
ROWS = {
    "core": {"driver": "core-source/background_conversion_driver.py", "lock": "conversion-inputs-core2.json",
        "sha256": "e99fd831dc9c8c939f7c2b3c29e1d43c7c5d7708567ac68b37e8c22b8ece7f51",
        "preflight": "conversion-run-1794613244382131500/verification.json", "cpu": "rebind-cpu-core-1794613242127697500/verification.json"},
    "wider": {"driver": "wider-source/background_conversion_driver.py", "lock": "conversion-inputs-wide2.json",
        "sha256": "031b16a7c1e5b12003391650f113703e81b9dc602d092a335f803d3e42c2c94c",
        "preflight": "conversion-run-1794613244337061700/verification.json", "cpu": "rebind-cpu-wider-1794613242128972700/verification.json"}}

def identity(path):
    raw = path.read_bytes(); st = path.stat()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": st.st_mtime_ns}

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write("\n")

def main():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == REVISION
    plan = json.loads((TASK / "REBIND_PLAN.json").read_bytes())
    assert all(identity(Path(path)) == expected for path, expected in plan["preserved_old_metadata_driver_request_lock_inputs"].items())
    commands = {}; batches = {}
    for label, row in ROWS.items():
        lock_path = TASK / row["lock"]; pre_path = TASK / row["preflight"]; cpu_path = TASK / row["cpu"]
        assert identity(lock_path)["sha256"] == row["sha256"]
        lock = json.loads(lock_path.read_bytes()); pre = json.loads(pre_path.read_bytes()); cpu = json.loads(cpu_path.read_bytes())
        assert lock["root_revision"] == REVISION and pre["passed"] and pre["mode"] == "preflight-only"
        assert pre["protected_main_python_runtime_original_stage_request_inputs_unchanged"] and pre["lock_file_unchanged"]
        assert cpu["passed"] and cpu["checks"] == 9 and cpu["failures"] == cpu["errors"] == 0 and cpu["unchanged"]
        assert {name: identity(ROOT / name) for name in lock["main_python_sources"]} == lock["main_python_sources"]
        commands[label] = [PYTHON, "-B", str(TASK / row["driver"]), "--input-lock", str(lock_path), "--lock-sha256", row["sha256"], "--run-conversions", "--lease-confirmed"]
        batches[label] = {"lock": {"path": str(lock_path), **identity(lock_path)},
            "driver": {"path": str(TASK / row["driver"]), **identity(TASK / row["driver"])},
            "preflight": {"path": str(pre_path), **identity(pre_path)}, "focused_cpu": {"path": str(cpu_path), **identity(cpu_path)},
            "cases": len(lock["schedule"]), "expected_successes": sum(r["expected_success"] for r in lock["schedule"]),
            "expected_refusals": sum(not r["expected_success"] for r in lock["schedule"]), "resource_files": len(lock["staged_members"]),
            "sourceio_files": len(lock["sourceio_tree"]), "main_python_files": len(lock["main_python_sources"]), "native_execution": "UNRUN"}
    source_paths = [TASK / name for name in ("prepare_rebind.py", "test_rebind.py", "freeze_ready.py")]
    source_paths += [path for directory in ("core-source", "wider-source") for path in (TASK / directory).iterdir() if path.is_file()]
    sources = {path.relative_to(TASK).as_posix(): identity(path) for path in sorted(source_paths)}
    save(TASK / "SOURCE_INDEX.json", {"format": "has_native_rebind_source_index_1", "files": sources, "count": len(sources), "bytes": sum(r["bytes"] for r in sources.values())})
    save(TASK / "RUN_COMMANDS.json", {"format": "has_native_rebind_future_execution_commands_1", "root_revision": REVISION,
        "authorization": "Review-ready only. Root must explicitly grant an exclusive serial core14 then wider11 lease. Do not run both concurrently.",
        "automatic_fresh_run_root": str(TASK), "automatic_child_pattern": "conversion-run-<time_ns>", "commands": commands})
    save(TASK / "READY.json", {"format": "has_source_native_rebind_ready_1", "root_revision": REVISION, "batches": batches,
        "sources": identity(TASK / "SOURCE_INDEX.json"), "commands": identity(TASK / "RUN_COMMANDS.json"), "diff": identity(TASK / "REBIND_NORMALIZED_DIFF.patch"),
        "old_metadata_driver_request_lock_inputs_preserved": len(plan["preserved_old_metadata_driver_request_lock_inputs"]),
        "focused_cpu_checks": 18, "focused_cpu_failures": 0, "preflights_passed": 2, "converter_private_blender_gpu_launched": False,
        "scope": "New actual-main request/source bindings at tested long-path fix, no conversion or native fidelity acceptance",
        "limits": ["Old root-owned Keiki Win206 failure remains failed and preserved.", "Nitori native missing hairbump and opaque additiveglow approximation remain.",
            "Static variants only; no native shader, flex/controller evaluation, jiggle, animation or rig assembly acceptance.", "Source checks cover17mainPython files; no whole-tree/GDScript freeze claim."]})
    print(json.dumps({"ready": str(TASK / "READY.json"), **identity(TASK / "READY.json"), "source_index": identity(TASK / "SOURCE_INDEX.json"), "batches": 2, "native_execution": "UNRUN"}))

if __name__ == "__main__": main()
