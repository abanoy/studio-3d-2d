"""Authored-only inactive native-jiggle, file-identity and real bridge CPU checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CASES = [("metadata", "test_source_jiggle_metadata.py", 25),
         ("capture", "test_source_mdl_snapshot.py", 18),
         ("capture_review", "test_source_mdl_snapshot_review.py", 9),
         ("bridge", "test_source_jiggle_bridge.py", 14)]
SOURCES = ["tools/blender_source_bridge.py", "tools/source_jiggle_values.py",
           "tools/source_jiggle_metadata.py", "tools/source_mdl_snapshot.py",
           "tests/source_jiggle_fixtures.py", "tests/verify_source_jiggle_cpu.py",
           *["tests/" + name for _, name, _ in CASES]]


def identity(path):
    info = path.stat()
    return {"bytes": info.st_size, "mtime_ns": info.st_mtime_ns,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    folder = (options.output or ROOT / "output/source-jiggle-cpu" / str(time.time_ns())).resolve()
    if not folder.is_relative_to((ROOT / "output").resolve()) or folder.exists():
        raise ValueError("Use a new owned output directory")
    folder.mkdir(parents=True)
    before = {name: identity(ROOT / name) for name in SOURCES}
    reports = {}
    for label, name, expected in CASES:
        args = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", name, "-v"]
        process = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=60)
        text = process.stdout + process.stderr
        (folder / (label + ".log")).write_text(text, encoding="utf-8")
        count = re.search(r"Ran ([0-9]+) tests", text)
        if process.returncode != 0 or not count or int(count.group(1)) != expected or "skipped" in text:
            raise RuntimeError(str(folder) + "\n" + text)
        reports[label] = {"checks": expected, "passed": True, "log": str(folder / (label + ".log"))}
    after = {name: identity(ROOT / name) for name in SOURCES}
    if before != after:
        raise RuntimeError("Jiggle CPU source identities changed during verification")
    report = {"format": "has_source_jiggle_cpu_1", "passed": True,
              "checks": sum(row[2] for row in CASES), "reports": reports,
              "source_unchanged": True, "source_identity": before,
              "native_conversion": False, "graphics": False,
              "scope": "Authored MDL bytes/files, exact final report bytes, CPU bridge seams and observed file races only",
              "actual_Junko_full_report_adoption_persistence": "UNRUN_requires_fresh_native_and_app_verification"}
    (folder / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("SOURCE_JIGGLE_CPU " + json.dumps({"passed": True, "checks": report["checks"], "verification": str(folder / "verification.json")}))


if __name__ == "__main__":
    main()
