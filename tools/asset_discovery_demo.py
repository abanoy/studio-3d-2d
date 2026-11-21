"""Owner-launched standalone discovery demo; does not edit app.gd or project.godot."""
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run

if __name__ == "__main__":
    # An explicit user demo launch is interactive. Automated tests use run.command.
    engine = run.engine_path()
    version = subprocess.check_output([engine, "--version"], text=True,
                                      creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if not version.startswith("4.6.stable"):
        raise SystemExit("Godot 4.6 stable standard is required.")
    (ROOT / "output").mkdir(exist_ok=True)
    raise SystemExit(subprocess.call([engine, "--path", str(ROOT), "--log-file",
                                     str(ROOT / "output/asset-discovery-demo.log"),
                                     "--script", "demos/asset_discovery.gd"], cwd=ROOT))
