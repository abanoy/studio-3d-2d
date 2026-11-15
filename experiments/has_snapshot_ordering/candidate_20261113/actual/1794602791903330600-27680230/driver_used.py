"""Fresh isolated headless authored contract; never import the main app."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
GODOT = Path(r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe")
GODOT_SHA = "63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf"

def stamp(path):
    stat = path.stat(); raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": stat.st_mtime_ns}

def write(path, value):
    with path.open("x", encoding="utf-8") as stream: json.dump(value, stream, indent=2)

def main():
    folder = TASK / "runs" / (str(time.time_ns()) + "-" + uuid.uuid4().hex[:8]); folder.mkdir(parents=True, exist_ok=False)
    base = json.loads((TASK / "BASE_SOURCE_CONTEXT.json").read_bytes())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != base["base_revision"]: raise RuntimeError("Main HEAD differs")
    project = folder / "project"; project.mkdir()
    source_names = set(); pending = ["src/has_snapshot_writer.gd"]
    while pending:
        name = pending.pop()
        if name in source_names: continue
        source_names.add(name)
        source = TASK / "overlay" / name
        if not source.is_file(): source = ROOT / name
        text = source.read_text(encoding="utf-8")
        pending.extend(re.findall(r'(?:preload|load)\("res://([^"\n]+\.gd)"\)', text))
    before = {str(ROOT / name): stamp(ROOT / name) for name in source_names}
    before.update({str(ROOT / name): stamp(ROOT / name) for name in base["main_sources"]})
    sources = [TASK / "overlay/src/has_snapshot_writer.gd", TASK / "overlay/src/has_project.gd", TASK / "ordering_unit.gd", Path(__file__), ROOT / "run.py", GODOT]
    before.update({str(path): stamp(path) for path in sources})
    if before[str(GODOT)]["sha256"] != GODOT_SHA: raise RuntimeError("Approved engine differs")
    for name in source_names:
        source = TASK / "overlay" / name
        if not source.is_file(): source = ROOT / name
        target = project / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    shutil.copy2(TASK / "ordering_unit.gd", project / "ordering_unit.gd")
    (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Authored snapshot ordering contract"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n', encoding="utf-8")
    # An explicit source-order guard supplements (and never replaces) runtime tests.
    main_text = (TASK / "overlay/src/has_project.gd").read_text(encoding="utf-8")
    start = main_text[main_text.index("func start("):main_text.index("func _write_cancel(")]
    if not start.index("snapshot_writer.prepare(") < start.index("pid = OS.create_process(") < start.index("snapshot_writer.launch()"):
        raise RuntimeError("Requested child/snapshot ordering is absent")
    spec = importlib.util.spec_from_file_location("ordering_run_" + uuid.uuid4().hex, ROOT / "run.py")
    launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
    if launcher.ROOT != ROOT: raise RuntimeError("Main launcher ROOT differs")
    launcher.ROOT = project
    old = os.environ.get("HYBRID_GODOT"); os.environ["HYBRID_GODOT"] = str(GODOT)
    try: command = launcher.command("ordering_unit.gd", headless=True, extra=["--audio-driver", "Dummy", "--log-file", str(folder / "engine.log"), "--", str(folder / "authored")])
    finally:
        if old is None: os.environ.pop("HYBRID_GODOT", None)
        else: os.environ["HYBRID_GODOT"] = old
    if command[0] != str(GODOT) or command[command.index("--path") + 1] != str(project) or "--headless" not in command:
        raise RuntimeError("Unexpected owned headless command")
    write(folder / "command.json", command)
    process = None; error = None; exit_code = None
    try:
        with (folder / "stdout.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=project, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            write(folder / "process.json", {"pid": process.pid})
            try: exit_code = process.wait(timeout=60)
            finally:
                if process.poll() is None: process.terminate(); process.wait(timeout=15)
    except Exception as exc: error = str(exc)
    actual = json.loads((folder / "authored/result.json").read_bytes()) if (folder / "authored/result.json").is_file() else None
    logs = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in (folder / "stdout.log", folder / "engine.log") if path.is_file())
    bad = [line for line in logs.splitlines() if any(token in line for token in ("ERROR:", "SCRIPT ERROR:", "WARNING:", "ObjectDB instances leaked", "FAIL "))]
    preserved = all(stamp(Path(path)) == expected for path, expected in before.items())
    same_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == head
    report = {"format": "studio_snapshot_ordering_authored_proof_1", "folder": str(folder), "exit": exit_code,
        "error": error, "actual": actual, "source_runtime_preserved": preserved, "head_preserved": same_head,
        "source_before": before, "forbidden_log_lines": bad, "retained_Popen_reaped": process is not None and process.poll() is not None,
        "main_application_runtime_tested": False, "gpu_native_or_blender": False, "source_order_guard": True}
    report["passed"] = exit_code == 0 and actual and actual["failures"] == 0 and not bad and preserved and same_head and report["retained_Popen_reaped"]
    write(folder / "proof.json", report)
    print(json.dumps({key: report[key] for key in ("folder", "exit", "error", "actual", "source_runtime_preserved", "head_preserved", "forbidden_log_lines", "retained_Popen_reaped", "passed")}))
    return 0 if report["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
