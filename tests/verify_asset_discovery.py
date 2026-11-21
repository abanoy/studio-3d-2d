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
    parser.add_argument("--close-live", action="store_true", help="Close the real browser during a native metadata request; verify cleanup")
    parser.add_argument("--quit-live", action="store_true", help="Quit real Studio with a browser metadata request pending; verify cleanup")
    parser.add_argument("--require-listings", action="store_true", help="With --live, require 100 mixed results, another batch and real English/Japanese name hits")
    options = parser.parse_args()
    if sum([options.live, options.close_live, options.quit_live]) > 1:
        parser.error("Choose --live, --close-live or --quit-live.")
    lifecycle = options.close_live or options.quit_live
    script = "tests/asset_discovery_close_live.gd" if lifecycle else "tests/asset_discovery_live.gd" if options.live else "tests/asset_discovery_smoke.gd"
    command = run.command(script, headless=not options.graphical, extra=("--", "--studio-quit") if options.quit_live else ())
    report_path = ROOT / ("output/asset-discovery-quit-live.json" if options.quit_live else "output/asset-discovery-close-live.json" if options.close_live else "output/asset-discovery-live.json" if options.live else "output/asset-discovery-test.json")
    # Never accept an old report after a failed launcher or parse error.
    report_path.unlink(missing_ok=True)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    log = ROOT / f"output/{Path(script).stem}-engine.log"
    diagnostics = log.read_text(encoding="utf-8") if log.exists() else ""
    if result.returncode or any(item in diagnostics for item in ["SCRIPT ERROR", "ERROR:", "ObjectDB instances leaked", "resources still in use"]):
        if "--receipt" in command:
            receipt = Path(command[command.index("--receipt") + 1])
            if receipt.exists(): print(receipt.read_text(encoding="utf-8"), file=sys.stderr)
        return 1
    if not report_path.exists():
        print("No fresh discovery result was produced.", file=sys.stderr)
        return 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if lifecycle:
        assert all(report[key] for key in ["native_request_existed", "loading_before_close", "window_freed", "service_freed", "request_freed"])
        print("Native request-close lifecycle passed without leaked-resource diagnostics.")
        return 0
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
            assert report["mmd_filter"]["listings"] > 0 and set(report["mmd_filter"]["sources"]) == {"sketchfab"}, "Need actual filtered model metadata"
            assert report.get("thumbnail", {}).get("loaded"), "Need one explicitly enabled live thumbnail preview"
        print("Live metadata observations recorded; required listing checks passed." if options.require_listings else "Live provider observations recorded; availability is not asserted.")
        return 0
    print(f"Discovery: {report['checks']} runtime checks, {len(report['failures'])} failures; {report['display_driver']}")
    return int(bool(report["failures"]) or report["checks"] < 50)


if __name__ == "__main__":
    raise SystemExit(main())
