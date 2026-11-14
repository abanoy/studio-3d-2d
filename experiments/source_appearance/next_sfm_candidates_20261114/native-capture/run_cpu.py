"""Retain a fresh authored-CPU result; never invokes conversion/app runtimes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

TASK = Path(__file__).absolute().parent
PYTHON = Path(r"C:\Program Files\Python313\python.exe")
PYTHON_SHA = "03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9"

def identity(path):
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_dev, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_dev, after.st_ino):
        raise ValueError("Identity changed during hash")
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "mtime_ns": before.st_mtime_ns,
        "device": before.st_dev, "inode": before.st_ino}

def main():
    run = TASK / ("cpu-run-" + str(time.time_ns()))
    run.mkdir(exist_ok=False)
    protected = [PYTHON, Path(__file__).absolute(), *(TASK / "source").glob("*.py")]
    before = {str(path): identity(path) for path in protected}
    if before[str(PYTHON)]["sha256"] != PYTHON_SHA:
        raise ValueError("Unapproved Python runtime")
    command = [str(PYTHON), "-B", "-m", "unittest", "discover", "-s", str(TASK / "source"), "-p", "test_source_mdl_snapshot.py", "-v"]
    (run / "command.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    started = time.monotonic()
    child = subprocess.run(command, cwd=TASK, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (run / "stdout.log").write_bytes(child.stdout)
    (run / "stderr.log").write_bytes(child.stderr)
    after = {str(path): identity(path) for path in protected}
    result = {"format": "has_selected_mdl_snapshot_cpu_result_1", "exit_code": child.returncode,
        "elapsed_seconds": time.monotonic() - started, "command": command,
        "source_runtime_before": before, "source_runtime_after": after, "preserved": before == after,
        "app_native_converter_gpu_runs": False, "native_originals_used": False,
        "all_actual_blender_adoption_fit_claims": "UNRUN", "passed": child.returncode == 0 and before == after}
    (run / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": str(run), "passed": result["passed"], "exit_code": child.returncode, "preserved": before == after}))
    if not result["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
