"""Read-only wider admission audit; never import workers or launch a converter."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

OUT = Path(__file__).absolute().parent
TASK = OUT.parent
ROOT = TASK.parents[1]

def identity(path):
    path = Path(path)
    for parent in (path, *path.parents):
        info = parent.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400)
    before = path.stat()
    with path.open("rb") as stream: sha = hashlib.file_digest(stream, "sha256").hexdigest()
    assert (before.st_size, before.st_mtime_ns) == (path.stat().st_size, path.stat().st_mtime_ns)
    return {"sha256": sha, "bytes": before.st_size, "mtime_ns": before.st_mtime_ns}

def read(path): return json.loads(path.read_bytes())

def main():
    ready = read(TASK / "READY.json")
    plan = read(TASK / "REBIND_PLAN.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == ready["root_revision"]
    index = read(TASK / "SOURCE_INDEX.json")
    assert all(identity(TASK / path) == row for path, row in index["files"].items())
    assert all(identity(Path(path)) == row for path, row in plan["preserved_old_metadata_driver_request_lock_inputs"].items())
    lock_path = TASK / "conversion-inputs-wide2.json"; lock = read(lock_path)
    assert identity(lock_path) == {k: ready["batches"]["wider"]["lock"][k] for k in ("sha256", "bytes", "mtime_ns")}
    assert all(identity(Path(path)) == row for path, row in lock["files"].items())
    runtime = ROOT / "output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
    observed_runtime = {}
    for base, dirs, files in os.walk(runtime, followlinks=False):
        dirs[:] = [value for value in dirs if value not in {"__pycache__", ".git"}]
        for name in files:
            path = Path(base) / name
            if path.suffix not in {".pyc", ".pyo"}: observed_runtime[path.relative_to(runtime).as_posix()] = identity(path)
    assert observed_runtime == lock["sourceio_tree"]
    input_stage = ROOT / "output/sfm-broader-native-cases-20261113/stage"
    assert sorted(path.relative_to(input_stage).as_posix() for path in input_stage.rglob("*") if path.is_file()) == lock["staged_members"]
    manifest = read(TASK / "native-wider-cases.json")
    assert len(manifest["cases"]) == 11 and sum(row["expect_all_blank"] for row in manifest["cases"]) == 1
    commands = read(TASK / "RUN_COMMANDS.json")
    assert "--output" not in commands["commands"]["wider"] and "--output" not in commands["commands"]["core"]
    invalid = TASK / "core2-launch-20261113T234201905"
    assert "Execution/preflight output must be a fresh direct conversion-run child" in (invalid / "stderr.log").read_text()
    assert (invalid / "stdout.log").stat().st_size == 0
    cases = {row["case"]: row for row in lock["cases"]}
    native_scope = {}
    for name, case in cases.items():
        native = lock["native"][name]; closure = lock["native_closure"][name]
        native_scope[name] = {"mdl_sha256": case["native_mdl_sha256"], "bones": len(native["bones"]), "skin_families": len(case["skin_table"]),
            "groups": [{"index": g["index"], "name": g["name"], "blank_choices": [c["index"] for c in g["choices"] if c["blank"]]} for g in case["actual_metadata"]["bodygroups"]],
            "material_vmt_files": len(closure["vmts"]), "observed_references": len(closure["references"]), "missing_references": len(closure["missing_native_references"]),
            "supported_bridge_base_inputs_complete": closure["supported_bridge_base_inputs_complete"], "native_reference_closure_complete": closure["native_observed_file_references_complete"],
            "diagnostics": closure["diagnostics"]}
    result = {"format": "has_wider_static_native_go_audit_1", "root_revision": ready["root_revision"],
        "decision": "GO_FOR_BOUNDED_WORKER_ATTEMPT_AFTER_ROOT_CORE14_PASS_AND_EXCLUSIVE_LEASE",
        "unresolved_driver_admission_blockers": [], "wider_lock": {"path": str(lock_path), **identity(lock_path)},
        "source_index": identity(TASK / "SOURCE_INDEX.json"), "sources_files_verified": len(index["files"]),
        "flat_wider_lock_inputs_verified": len(lock["files"]), "wider_stage_files": len(lock["staged_members"]), "sourceio_files": len(observed_runtime),
        "old_metadata_driver_request_lock_inputs_verified": len(plan["preserved_old_metadata_driver_request_lock_inputs"]),
        "native_scope": native_scope, "cases": 11, "expected_successes": 10, "expected_allblank_refusals": 1,
        "invalid_output_attempt": "Rejected by safe-name guard before run creation/private child; stdout empty and exact rejection stderr retained. Root owns PID6448 authoritative closure.",
        "preflight_passed": True, "cpu_controls": 18, "core_retry_owned_by_root": "PID15400, creation2026-11-13T23:44:57.2710029Z; this audit does not launch/close/kill any runtime",
        "converter_or_gpu_launched": False, "production_sources_locks_or_HEAD_mutated": False,
        "caveats": ["Go admits a serial attempt, not a promise that unseen native conversions will satisfy every metadata/structure predicate.",
            "Root must finish Core14 and close its owned workers before starting Wider11; fresh automatic run name, stop first unexpected failure.",
            "Names/parents and decoded GLB structure are checked; independent native geometry/material pixels/flex-controller evaluation remain separate.",
            "Junko native jiggle declarations are inventory only. Mima head control metadata is staged/inventoried but excluded from the11conversions.",
            "No inferred assembly across Junko or Mima rigs; Kanako all4blank is the only trueallblank broader case.",
            "Nitori's known native missinghairbump/additiveglow approximation is outside wider resources and remains recorded.",
            "Whole-source/GDScript/app/GPU adoption is not claimed by the17-file Python worker freeze."]}
    with (OUT / "WIDER_GO_AUDIT.json").open("x", encoding="utf-8") as stream: json.dump(result, stream, indent=2)
    print(json.dumps({"decision": result["decision"], "file": str(OUT / "WIDER_GO_AUDIT.json"), **identity(OUT / "WIDER_GO_AUDIT.json")}))

if __name__ == "__main__": main()
