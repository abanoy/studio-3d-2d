"""Only discovery tests. Uses the existing private desktop for --graphical."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--graphical", action="store_true")
    parser.add_argument("--live", action="store_true", help="Explicit real metadata probe, separate from fixture interactions")
    parser.add_argument("--require-listings", action="store_true", help="With --live, require 100 mixed results, another batch and real English/Japanese name hits")
    options = parser.parse_args()
    script = "tests/asset_discovery_live.gd" if options.live else "tests/asset_discovery_smoke.gd"
    command = run.command(script, headless=not options.graphical)
    report_path = ROOT / ("output/asset-discovery-live.json" if options.live else "output/asset-discovery-test.json")
    # Never accept an old report after a failed launcher or parse error.
    report_path.unlink(missing_ok=True)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    log = ROOT / f"output/{Path(script).stem}-engine.log"
    diagnostics = log.read_text(encoding="utf-8") if log.exists() else ""
    if result.returncode or "SCRIPT ERROR" in diagnostics or "ERROR:" in diagnostics:
        if "--receipt" in command:
            receipt = Path(command[command.index("--receipt") + 1])
            if receipt.exists(): print(receipt.read_text(encoding="utf-8"), file=sys.stderr)
        return 1
    if not report_path.exists():
        print("No fresh discovery result was produced.", file=sys.stderr)
        return 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if options.live:
        if report.get("failures"):
            return 1
        if options.require_listings:
            assert report["cold_start_offline"], "Cold start must remain offline"
            assert report["initial"]["listings"] == 100 and len(report["initial"]["sources"]) >= 2, "Need 100 real mixed listings"
            assert report["second_batch"]["listings"] == 200, "Need another 100 real listings"
            assert report["name_search"]["listings"] > 0 and report["japanese_search"]["listings"] > 0, "Need real name and original-script hits"
            assert report["source_click_intercepted"], "Need a real listing opened through the source-page boundary"
            assert report["cancel"]["request_existed"] and report["cancel"]["http_released"] and not report["cancel"]["loading"], "Need actual in-flight cancellation and HTTP cleanup"
        print("Live metadata observations recorded; required listing checks passed." if options.require_listings else "Live provider observations recorded; availability is not asserted.")
        return 0
    print(f"Discovery: {report['checks']} runtime checks, {len(report['failures'])} failures; {report['display_driver']}")
    return int(bool(report["failures"]) or report["checks"] < 50)


if __name__ == "__main__":
    raise SystemExit(main())
