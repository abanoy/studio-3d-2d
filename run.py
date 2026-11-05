"""Launch the offline Godot/GDScript prototype, without installing dependencies."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent


def engine_path():
    candidates = [os.environ.get("HYBRID_GODOT"),
                  r"C:\a\tools\Godot\Godot_v4.6-stable_win64_console.exe",
                  shutil.which("godot"), shutil.which("godot4")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError("Godot 4.6 standard is missing. Extract the portable Windows build "
                       "and set HYBRID_GODOT to its full executable path. See README.md.")


def command(script=None, headless=False, extra=(), quiet=False):
    engine = engine_path()
    version = subprocess.check_output([engine, "--version"], text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0).strip()
    if not version.startswith("4.6.stable"):
        raise RuntimeError(f"Pinned Godot 4.6 stable required; found {version}")
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    log_name = Path(script).stem if script else "studio"
    testing = script is not None or headless or bool(extra)
    if (quiet or testing) and os.name == "nt":
        windowed = Path(engine).with_name(Path(engine).name.replace("_console", ""))
        if windowed.is_file():
            engine = str(windowed)
    args = [engine, "--path", str(ROOT), "--log-file", str(output / f"{log_name}-engine.log")]
    if quiet:
        args.append("--quiet")
    if headless:
        args.append("--headless")
    if script:
        args += ["--script", script]
    args += list(extra)
    if testing and "--" not in args: args.append("--")
    if testing and not headless and os.name == "nt":
        # Use the actual windowed engine, never its console wrapper: the wrapper
        # creates another process and hides the real window owner's identity.
        if Path(engine).name.endswith("_console.exe"):
            raise RuntimeError("Hidden GPU tests require the matching windowed Godot executable.")
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if not pythonw.is_file(): raise RuntimeError("Hidden GPU tests require the installed pythonw.exe; no visible fallback is used.")
        receipt = output / "private-desktop" / (log_name + "_" + uuid.uuid4().hex + ".json")
        args = [str(pythonw), str(ROOT / "tools/private_desktop.py"), "--receipt", str(receipt), "--", *args]
    return args


def main(quiet=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", choices=["unit", "spikes", "editor", "legacy", "ui", "recovery", "recovery-write", "pose", "source", "source-browser"])
    options = parser.parse_args()
    try:
        if options.test == "unit":
            args = command("tests/unit.gd", headless=True)
        elif options.test == "spikes":
            args = command("tests/spikes.gd")
        elif options.test == "editor":
            args = command(extra=["--", "--smoke"])
        elif options.test == "ui":
            args = command(extra=["--", "--ui-smoke"])
        elif options.test == "pose":
            args = command(extra=["--", "--pose-smoke"])
        elif options.test in ("recovery", "recovery-write"):
            args = command(extra=["--", "--recovery-smoke"] + (["--recovery-write"] if options.test == "recovery-write" else []))
        elif options.test == "legacy":
            args = command("tests/legacy_render_smoke.gd")
        elif options.test == "source":
            args = command("tests/source_render_smoke.gd")
        elif options.test == "source-browser":
            args = command("tests/source_browser_smoke.gd")
        else:
            args = command(quiet=quiet)
        if options.test:
            if "--" not in args: args.append("--")
            args.append("--demo-room")
        if quiet:
            with (ROOT / "output" / "launcher.log").open("a", encoding="utf-8") as log:
                return subprocess.call(args, cwd=ROOT, stdout=log, stderr=log,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        return subprocess.call(args, cwd=ROOT)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
