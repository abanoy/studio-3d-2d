"""Construct one output-only two-phase snapshot draft from exact main1236796."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
BASE = "1236796865e677b150a2d7e2add20f2aac5325fe"

def stamp(path):
    raw = path.read_bytes(); stat = path.stat()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": stat.st_mtime_ns}

def replace_once(text, old, new):
    if text.count(old) != 1: raise RuntimeError("Nonunique seam: " + old[:100])
    return text.replace(old, new, 1)

def main():
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != BASE:
        raise RuntimeError("Main HEAD changed")
    overlay = TASK / "overlay"; (overlay / "src").mkdir(parents=True, exist_ok=False)
    before = {}
    for name in ("src/has_snapshot_writer.gd", "src/has_project.gd"):
        raw = (ROOT / name).read_bytes()
        blob = subprocess.check_output(["git", "show", BASE + ":" + name], cwd=ROOT)
        if raw.replace(b"\r\n", b"\n") != blob.replace(b"\r\n", b"\n"):
            raise RuntimeError("Main working bytes differ: " + name)
        before[name] = stamp(ROOT / name)
        shutil.copy2(ROOT / name, overlay / name)
    writer = (overlay / "src/has_snapshot_writer.gd").read_text(encoding="utf-8")
    writer = replace_once(writer, "var thread: Thread\n", "var thread: Thread\nvar _prepared: Dictionary={}\n")
    writer = replace_once(writer, "func start(project: Dictionary,request: Dictionary) -> String:\n\tif busy():return", "func prepare(project: Dictionary,request: Dictionary) -> String:\n\tif busy() or has_prepared():return")
    writer = replace_once(writer,
        '\tthread=Thread.new();var why:=thread.start(_run.bind(frozen.project,copied),Thread.PRIORITY_LOW)\n'
        '\tif why!=OK:thread=null;return "Cannot start project snapshot worker."\n\treturn ""\n',
        '\t_prepared={"project":frozen.project,"request":copied}\n\treturn ""\n'
        'func has_prepared() -> bool:return not _prepared.is_empty()\n'
        'func discard_prepared() -> void:_prepared={}\n'
        'func _start_thread(work: Callable) -> Error:return thread.start(work,Thread.PRIORITY_LOW)\n'
        'func launch() -> String:\n'
        '\tif busy():return "A project snapshot is already being saved."\n'
        '\tif not has_prepared():return "No captured project snapshot is ready to start."\n'
        '\tvar captured: Dictionary=_prepared;_prepared={}\n'
        '\tthread=Thread.new();var why:=_start_thread(_run.bind(captured.project,captured.request))\n'
        '\tif why!=OK:thread=null;return "Cannot start project snapshot worker."\n'
        '\treturn ""\n'
        'func start(project: Dictionary,request: Dictionary) -> String:\n'
        '\tvar why:=prepare(project,request)\n'
        '\treturn why if not why.is_empty() else launch()\n')
    writer = replace_once(writer, 'func finish() -> Dictionary:\n\tif not busy():return {}',
        'func finish() -> Dictionary:\n\tdiscard_prepared()\n\tif not busy():return {}')
    (overlay / "src/has_snapshot_writer.gd").write_text(writer, encoding="utf-8")
    project = (overlay / "src/has_project.gd").read_text(encoding="utf-8")
    project = replace_once(project, 'snapshot_writer.start(snapshot_state,', 'snapshot_writer.prepare(snapshot_state,')
    project = replace_once(project, '\tapp.exporting = true\n\tprogress = Window.new();',
        '\t# The packer already waits for snapshot_ready. Start our directory-writing\n'
        '\t# Thread only after child creation, removing this avoidable CWD overlap.\n'
        '\tif not snapshot_state.is_empty():\n'
        '\t\tvar why: String=snapshot_writer.launch()\n'
        '\t\tif not why.is_empty():_snapshot_error=why;_write_cancel();snapshot_writer.finish()\n'
        '\t# A launch failure keeps this child owned until normal polling observes\n'
        '\t# cancellation/exit; no orphan or second completion signal is introduced.\n'
        '\tapp.exporting = true\n\tprogress = Window.new();')
    project = replace_once(project, 'func _exit_tree() -> void:\n',
        'func _exit_tree() -> void:\n\tsnapshot_writer.discard_prepared()\n')
    (overlay / "src/has_project.gd").write_text(project, encoding="utf-8")
    patch = []
    for name in before:
        patch.extend(difflib.unified_diff((ROOT / name).read_text(encoding="utf-8").splitlines(keepends=True),
            (overlay / name).read_text(encoding="utf-8").splitlines(keepends=True), fromfile="a/" + name, tofile="b/" + name))
    (TASK / "candidate.patch").write_text("".join(patch), encoding="utf-8")
    after = {name: stamp(ROOT / name) for name in before}
    if before != after: raise RuntimeError("Main sources changed during construction")
    (TASK / "BASE_SOURCE_CONTEXT.json").write_text(json.dumps({"base_revision": BASE, "main_sources": before,
        "main_preserved": before == after, "unshipped": True, "hypothesis": "Avoidable snapshot-thread/child-create CWD overlap; original Win32 error unknown"}, indent=2), encoding="utf-8")
    print(json.dumps({"base": BASE, "main_preserved": True, "overlay": {name: stamp(overlay / name) for name in before}}))

if __name__ == "__main__": main()
