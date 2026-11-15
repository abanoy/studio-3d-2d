"""One isolated, headless current-directory concurrency experiment."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PYTHON = Path(r"C:\Program Files\Python313\python.exe")
GODOT = Path(r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe")
PINS = {PYTHON: "03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9",
        GODOT: "63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf"}

def stamp(path):
    stat = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}

def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)

def main():
    folder = TASK / "runs" / (str(time.time_ns()) + "-" + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    files = [Path(__file__), TASK / "probe.gd", ROOT / "run.py", ROOT / "src/has_snapshot_writer.gd",
             ROOT / "src/has_project.gd", ROOT / "src/source_import.gd", *PINS]
    before = {str(path): stamp(path) for path in files}
    if not all(before[str(path)]["sha256"] == sha for path, sha in PINS.items()):
        raise RuntimeError("Approved runtime differs")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    project = folder / "project"; project.mkdir()
    (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Owned CWD race probe"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n', encoding="utf-8")
    shutil.copy2(TASK / "probe.gd", project / "probe.gd")
    short = folder / "short"; short.mkdir()
    long = folder / ("long_" + "x" * 80) / ("y" * 90) / ("z" * 80)
    long.mkdir(parents=True)
    if len(str(long)) <= 260:
        raise RuntimeError("The long control must exceed260 characters")
    request = {"format": "studio_source_cwd_race_probe_1", "python": str(PYTHON),
        "python_sha256": PINS[PYTHON], "short_dir": str(short), "long_dir": str(long),
        "result": str(folder / "result.json")}
    write(folder / "request.json", request)
    spec = importlib.util.spec_from_file_location("owned_cwd_probe_run_" + uuid.uuid4().hex, ROOT / "run.py")
    run = importlib.util.module_from_spec(spec); spec.loader.exec_module(run)
    if run.ROOT.resolve() != ROOT.resolve():
        raise RuntimeError("Main launcher context differs")
    # Literal run.command is retained; this CPU-only project has no main app copy.
    run.ROOT = project
    old = os.environ.get("HYBRID_GODOT")
    os.environ["HYBRID_GODOT"] = str(GODOT)
    try:
        command = run.command("probe.gd", headless=True, extra=["--audio-driver", "Dummy", "--log-file", str(folder / "engine.log"), "--", str(folder / "request.json")])
    finally:
        if old is None: os.environ.pop("HYBRID_GODOT", None)
        else: os.environ["HYBRID_GODOT"] = old
    if command[0] != str(GODOT) or command[command.index("--path") + 1] != str(project) or "--headless" not in command:
        raise RuntimeError("Unexpected CPU command")
    write(folder / "command.json", command)
    process = None; error = None; code = None; started = time.time_ns()
    try:
        with (folder / "stdout.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=project, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            write(folder / "process.json", {"pid": process.pid, "started_ns": started})
            try: code = process.wait(timeout=120)
            finally:
                if process.poll() is None: process.terminate(); process.wait(timeout=15)
    except Exception as exc:
        error = str(exc)
    preserved = {str(path): stamp(path) for path in files} == before
    head_after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    actual = json.loads((folder / "result.json").read_bytes()) if (folder / "result.json").is_file() else None
    summary = {"format": "studio_source_cwd_race_proof_1", "folder": str(folder), "head_before": head,
        "head_after": head_after, "source_and_runtime_before": before, "source_runtime_preserved": preserved,
        "exit": code, "error": error, "retained_Popen_reaped": process is not None and process.poll() is not None,
        "elapsed_seconds": (time.time_ns() - started) / 1e9, "result": actual,
        "gpu_or_native_inputs_used": False, "main_source_edits": False}
    write(folder / "proof.json", summary)
    compact = {key: summary[key] for key in ("folder", "exit", "error", "source_runtime_preserved", "retained_Popen_reaped", "elapsed_seconds")}
    compact["rows"] = [{key: row.get(key) for key in ("label", "attempts", "launch_failures", "nonzero_child_exits", "timeouts", "map_close_failures", "thread_result")} for row in actual.get("rows", [])] if actual else None
    print(json.dumps(compact))
    return 0 if code == 0 and preserved and head_after == head and actual else 1

if __name__ == "__main__":
    raise SystemExit(main())
