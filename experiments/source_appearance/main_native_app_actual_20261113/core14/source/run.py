"""Launch the offline Godot/GDScript prototype, without installing dependencies."""
from pathlib import Path
import argparse
import atexit
import ctypes
import ctypes.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
_PRIVATE_DISPLAY = None


def configure_private_display(display):
    """Select an explicitly provisioned local test display; graphical calls stay X11."""
    if sys.platform != "linux" or not isinstance(display,str) or not re.fullmatch(r":[0-9]+(?:\.[0-9]+)?",display):
        raise ValueError("Private Linux tests require a local X display such as :102.")
    global _PRIVATE_DISPLAY
    # Godot can try Wayland even with an explicit X11 driver. Keep its fallback
    # in an empty owned runtime directory, never the user's graphical session.
    runtime = tempfile.mkdtemp(prefix="has-private-display-")
    atexit.register(shutil.rmtree,runtime,ignore_errors=True)
    os.environ["XDG_RUNTIME_DIR"] = runtime
    os.environ["WAYLAND_DISPLAY"] = "has-disabled-wayland"
    os.environ["DISPLAY"] = display
    _PRIVATE_DISPLAY = display


def _check_private_display(display):
    library = ctypes.util.find_library("X11")
    if not library:
        raise RuntimeError("Private graphical tests require libX11 for their display readiness check.")
    x11 = ctypes.CDLL(library)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.restype = ctypes.c_int
    connection = x11.XOpenDisplay(display.encode("ascii"))
    if not connection:
        raise RuntimeError("Private X11 display is unavailable; no graphical fallback is permitted.")
    x11.XCloseDisplay(connection)


def _pin_private_driver(args, headless):
    if sys.platform != "linux" or _PRIVATE_DISPLAY is None:
        return
    boundary = args.index("--") if "--" in args else len(args)
    engine_args = args[:boundary]
    headless = headless or "--headless" in engine_args
    required = "headless" if headless else "x11"
    for index,option in enumerate(engine_args):
        option = os.fsdecode(option)
        if option == "--display-driver":
            value = engine_args[index+1] if index+1 < len(engine_args) else ""
        elif option.startswith("--display-driver="):
            value = option.split("=",1)[1]
        else:
            continue
        if value != required:
            raise RuntimeError("Private tests cannot select a competing display driver; no graphical fallback is permitted.")
    if headless:
        return
    if os.environ.get("DISPLAY") != _PRIVATE_DISPLAY:
        raise RuntimeError("Selected private DISPLAY changed; no graphical fallback is permitted.")
    _check_private_display(_PRIVATE_DISPLAY)
    # Last engine option, before script arguments: a missing X server fails
    # while the private runtime directory also isolates any driver fallback.
    args[boundary:boundary] = ["--display-driver","x11"]


def engine_path():
    candidates = [os.environ.get("HYBRID_GODOT"),
                  r"C:\a\tools\Godot\Godot_v4.6-stable_win64_console.exe",
                  shutil.which("godot"), shutil.which("godot4")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError("Godot 4.6 standard is missing. Extract the portable Windows build "
                       "and set HYBRID_GODOT to its full executable path. See README.md.")


def command(script=None, headless=False, extra=(), quiet=False, project=None):
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
    if project is not None:
        path = Path(project).expanduser().resolve(strict=True)
        if not path.is_file() or path.suffix.lower() != ".has":
            raise ValueError("Choose a .has project file.")
        if "--" not in args:
            args.append("--")
        args.extend(["--open-project", str(path)])
    _pin_private_driver(args, headless)
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
    parser.add_argument("project", nargs="?", help="Open this .has project at startup")
    parser.add_argument("--test", choices=["unit", "spikes", "editor", "legacy", "ui", "recovery", "recovery-write", "pose", "source", "source-browser"])
    options = parser.parse_args()
    if options.test and options.project:
        parser.error("Choose either a project or a test.")
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
            args = command(quiet=quiet, project=options.project)
        if options.test:
            if "--" not in args: args.append("--")
            args.append("--demo-room")
        if quiet:
            with (ROOT / "output" / "launcher.log").open("a", encoding="utf-8") as log:
                return subprocess.call(args, cwd=ROOT, stdout=log, stderr=log,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        return subprocess.call(args, cwd=ROOT)
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
