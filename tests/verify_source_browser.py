"""Optional installed-game browser checks; all private artifacts stay under output/."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command
from test_source_archive import archive
sys.path.insert(0, str(ROOT / "tools"))
from source_content import discover
from source_paths import DEFAULT_GMOD, DEFAULT_WORKSHOP


def run(args, timeout=210):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode: raise RuntimeError(f"Exit {result.returncode}: {args}\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def main():
    print(run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_source_content.py"]))
    text = run(command("tests/source_browser_smoke.gd"))
    (ROOT / "output/source-browser-verification.log").write_text(text, encoding="utf-8")
    if "SOURCE_BROWSER " not in text or '"failures":0' not in text or any(s in text for s in ("SCRIPT ERROR", "FAIL ", "ObjectDB instances leaked", "another exclusive child")):
        raise RuntimeError("Browser integration failed; inspect output/source-browser-verification.log")
    report = json.loads((ROOT / "output/source-browser-smoke/result.json").read_text(encoding="utf-8"))
    # Prove that an explicitly mounted separate GMA can supply a missing VMT/VTF.
    # Use only private copies of the installed CSS chair, never edit the game files.
    bundle = Path(report["css_bundle"])
    folder = ROOT / "output" / ("source-cross-addon-" + str(time.time_ns()))
    folder.mkdir()
    resources = [(p.relative_to(bundle / "resolved-native").as_posix(), p.read_bytes())
                 for p in (bundle / "resolved-native/materials").rglob("*") if p.is_file()]
    assert resources
    package = folder / "material-pack.gma"
    package.write_bytes(archive(resources + [("lua/autorun/never.lua", b"This file is data only and must never execute.")]))
    original = hashlib.sha256(package.read_bytes()).hexdigest()
    # Exercise the saved-settings path used by ordinary native file imports too.
    known = discover(DEFAULT_GMOD, DEFAULT_WORKSHOP)
    overrides = {p["path"]: False for p in known["providers"]}
    overrides[str(package)] = True
    plan = folder / "mount-settings.json"
    plan.write_text(json.dumps({"extra": [str(package)], "overrides": overrides}), encoding="utf-8")
    model = bundle / "native/models/props/cs_office/chair_office.mdl"
    print(run([sys.executable, "tools/prepare_source.py", str(model), "--mount-settings", str(plan), "--output", str(folder / "prepared")]))
    native = json.loads((folder / "prepared/parameters.json").read_text(encoding="utf-8"))
    dependencies = json.loads((folder / "prepared/dependencies.json").read_text(encoding="utf-8"))
    assert native["counts"]["textures"] > 0 and not native["warnings"]
    assert any(Path(d["provider"]).resolve() == package.resolve() and d["path"].endswith(".vtf") for d in dependencies["resolved"])
    assert hashlib.sha256(package.read_bytes()).hexdigest() == original
    report["cross_addon_materials"] = {"ok": True, "bundle": str(folder / "prepared"), "textures": native["counts"]["textures"]}
    (ROOT / "output/source-browser-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
