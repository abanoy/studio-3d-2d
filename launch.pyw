"""Windowed Windows entry point. Keep startup failures reviewable without a console."""
from pathlib import Path
import contextlib
import ctypes
import traceback

from run import main

root = Path(__file__).resolve().parent
(root / "output").mkdir(exist_ok=True)
log_path = root / "output" / "launcher.log"
with log_path.open("a", encoding="utf-8") as log:
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            code = main(quiet=True)
        except Exception:
            traceback.print_exc()
            code = 1
if code:
    ctypes.windll.user32.MessageBoxW(
        None, f"The studio could not start or stopped unexpectedly.\n\nDetails: {log_path}",
        "Hybrid Animation Studio", 0x10)
