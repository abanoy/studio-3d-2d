"""Focused persistence/restart and patched-real-Studio checks, using run.command."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run


def execute(script, folder, extra=(), stage=None, graphical=False):
    args = (["--path", stage.as_posix()] if stage else []) + ["--", folder.as_posix(), *extra]
    command = run.command(script, headless=not graphical, extra=args)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=65)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    log = ROOT / "output" / (Path(script).stem + "-engine.log")
    diagnostics = log.read_text(encoding="utf-8") if log.exists() else ""
    if result.returncode or any(item in diagnostics for item in ["SCRIPT ERROR", "ERROR:", "Unicode parsing error"]):
        raise RuntimeError(f"{script} failed; inspect {log}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--graphical", action="store_true")
    parser.add_argument("--persistence-only", action="store_true")
    parser.add_argument("--notices-only", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "output" / f"discovery-additions-{time.time_ns()}"
    folder.mkdir(parents=True)
    reports = {}
    print("Source requirements notices and restart")
    for phase, extra in [("write", []), ("read", ["--read"])]:
        execute("tests/asset_discovery_notices.gd", folder, extra, graphical=args.graphical)
        reports["notices_" + phase] = json.loads((folder / f"notices-{phase}.json").read_text(encoding="utf-8"))
    if args.notices_only:
        (folder / "result.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
        assert all(not report["failures"] for report in reports.values())
        print(f"Notice checks passed: {sum(report['checks'] for report in reports.values())}; {folder}")
        return 0
    print("Local geometry preview")
    execute("tests/asset_discovery_preview.gd", folder)
    reports["geometry_preview"] = json.loads((folder / "preview-result.json").read_text(encoding="utf-8"))
    print("Optional thumbnail preview")
    execute("tests/asset_discovery_thumbnail.gd", folder)
    reports["thumbnails"] = json.loads((folder / "thumbnail-result.json").read_text(encoding="utf-8"))
    print("Persistence and restart")
    execute("tests/asset_discovery_persistence.gd", folder)
    execute("tests/asset_discovery_persistence.gd", folder, ["--read"])
    for phase in ["write", "read"]:
        reports[phase] = json.loads((folder / f"persistence-{phase}.json").read_text(encoding="utf-8"))
    if not args.persistence_only:
        print("Patched Studio integration")
        # Copy only the application source needed by this test, never owner projects,
        # installed tools, Git objects, artwork corpora or generated earlier outputs.
        stage = folder / "studio-copy"
        stage.mkdir()
        for directory in ["src", "data", "web", "examples"]:
            shutil.copytree(ROOT / directory, stage / directory)
        for name in ["main.tscn", "project.godot"]:
            shutil.copy2(ROOT / name, stage / name)
        (stage / "tests").mkdir()
        shutil.copy2(ROOT / "tests/asset_discovery_studio_smoke.gd", stage / "tests/asset_discovery_studio_smoke.gd")
        original = hashlib.sha256((ROOT / "src/app.gd").read_bytes()).hexdigest()
        staged_app = (stage / "src/app.gd").read_text(encoding="utf-8")
        if 'get_node("AssetDiscoveryBridge").open()' not in staged_app:
            subprocess.run(["git", "apply", "--directory=" + stage.relative_to(ROOT).as_posix(),
                            "docs/asset_discovery_integration.patch"], cwd=ROOT, check=True)
        else:
            assert staged_app.count('preload("res://src/discovery/studio_bridge.gd").install(self, toolbar)') == 1
        assert hashlib.sha256((ROOT / "src/app.gd").read_bytes()).hexdigest() == original
        for theme in ["neon", "classic"]:
            case = folder / theme
            case.mkdir()
            execute("tests/asset_discovery_studio_smoke.gd", case,
                    ["--classic"] if theme == "classic" else [], stage, args.graphical)
            reports[theme] = json.loads((case / "studio-result.json").read_text(encoding="utf-8"))
        assert hashlib.sha256((ROOT / "src/app.gd").read_bytes()).hexdigest() == original
    report = {"cases": reports, "checks": sum(x["checks"] for x in reports.values()),
              "failures": [item for value in reports.values() for item in value["failures"]]}
    (folder / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Discovery additions: {report['checks']} checks; {len(report['failures'])} failures. {folder}")
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
