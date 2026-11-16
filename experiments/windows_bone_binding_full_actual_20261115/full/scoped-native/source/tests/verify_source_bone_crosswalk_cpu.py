"""Authored-only export crosswalk, compact wire/report and bridge adapter suite."""
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
CASES = [("collector", "test_source_jiggle_crosswalk.py", 47),
         ("metadata", "test_source_bone_metadata.py", 11),
         ("adapter", "test_source_bone_export.py", 19)]
SOURCES = ["tools/blender_source_bridge.py", "tools/source_jiggle_crosswalk.py",
           "tools/source_bone_metadata.py", "tools/source_bone_export.py", "tools/source_jiggle_metadata.py",
           "tools/source_jiggle_values.py", "tools/source_mdl_snapshot.py", "tests/source_jiggle_fixtures.py",
           "tests/verify_source_bone_crosswalk_cpu.py", *["tests/"+name for _, name, _ in CASES]]


def identity(path):
    info = path.stat()
    return {"bytes": info.st_size, "mtime_ns": info.st_mtime_ns,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path); args = parser.parse_args()
    folder = (args.output or ROOT/"output/source-bone-crosswalk-cpu"/str(time.time_ns())).resolve()
    if not folder.is_relative_to((ROOT/"output").resolve()) or folder.exists():
        raise ValueError("Use a new owned output directory")
    folder.mkdir(parents=True); before = {name: identity(ROOT/name) for name in SOURCES}; reports = {}
    for label, name, expected in CASES:
        process = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", name, "-v"],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        text = process.stdout+process.stderr; (folder/(label+".log")).write_text(text, encoding="utf-8")
        count = re.search(r"Ran ([0-9]+) tests", text)
        if process.returncode != 0 or not count or int(count.group(1)) != expected or "skipped" in text:
            raise RuntimeError(str(folder)+"\n"+text)
        reports[label] = {"checks": expected, "passed": True, "log": str(folder/(label+".log"))}
    if before != {name: identity(ROOT/name) for name in SOURCES}: raise RuntimeError("CPU source identity changed")
    result = {"format": "has_source_bone_crosswalk_cpu_1", "passed": True,
              "checks": sum(row[2] for row in CASES), "reports": reports, "source_unchanged": True,
              "source_identity": before, "native_conversion": False, "graphics": False,
              "actual_main_bridge_adoption_persistence": "UNRUN_requires_fresh_native_and_app_verification",
              "native_solver": "not_implemented", "scope": "Authored bytes/RNA mocks, integer wires, whole nested CRLF budget and file identity races"}
    (folder/"verification.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("SOURCE_BONE_CROSSWALK_CPU "+json.dumps({"passed": True, "checks": result["checks"], "verification": str(folder/"verification.json")}))


if __name__ == "__main__": main()
