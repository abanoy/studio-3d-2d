"""Focused headless component regression; ordinary UI checks run separately."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

SUITES = ("curves", "clips", "document", "first_key", "gap", "motion",
          "virtual", "backward", "pose", "paste", "keys", "delete", "path", "shapes", "authoring", "settings", "recording", "channels")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-plans", type=Path,
                        default=ROOT / "output/root-component-native-plans.json")
    args = parser.parse_args()
    folder = ROOT / "output/component-regression" / str(time.time_ns())
    folder.mkdir(parents=True)
    report = {"folder": str(folder), "suites": [], "skipped": [],
              "ordinary_model9_admission": True, "checks": 0, "ok": True}
    sources = list((ROOT / "src").glob("root_component*.gd"))
    sources += [ROOT / f"tests/root_component_{name}_unit.gd" for name in SUITES]
    report["source_sha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sources}
    for name in SUITES:
        extra = []
        if name in ("document", "settings"):
            if not args.native_plans.is_file():
                report["skipped"].append(name + ": native plans file unavailable")
                continue
            extra = ["--", str(args.native_plans.resolve())]
        script = f"tests/root_component_{name}_unit.gd"
        started = time.monotonic()
        row = {"name": name, "ok": False}
        output = ""
        try:
            process = subprocess.run(command(script, headless=True, extra=extra), cwd=ROOT,
                                     capture_output=True, encoding="utf-8", errors="replace", timeout=30)
            output = process.stdout + process.stderr
            markers = [line.split(" ", 1)[1] for line in output.splitlines()
                       if line.startswith("ROOT_COMPONENT") and " {" in line]
            result = json.loads(markers[0]) if len(markers) == 1 else {}
            row.update(exit=process.returncode, result=result)
            row["ok"] = (process.returncode == 0 and result.get("failures") == 0
                         and result.get("checks", 0) > 0
                         and not any(token in output for token in ("ERROR:", "FAIL ", "ObjectDB instances leaked")))
            if row["ok"]:
                report["checks"] += result["checks"]
        except subprocess.TimeoutExpired as error:
            row["error"] = "30-second test timeout; owned child terminated by subprocess.run"
            output = "\n".join(part.decode("utf-8", "replace") if isinstance(part, bytes) else part or ""
                               for part in (error.stdout, error.stderr))
        except (OSError, RuntimeError, ValueError) as error:
            row["error"] = str(error)
        row["seconds"] = round(time.monotonic() - started, 3)
        (folder / f"{name}.log").write_text(output, encoding="utf-8")
        report["suites"].append(row)
        report["ok"] = report["ok"] and row["ok"]
        print(f"{name}: {'PASS' if row['ok'] else 'FAIL'}", flush=True)
        (folder / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (ROOT / "output/component-regression-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("folder", "ok", "checks", "skipped")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
