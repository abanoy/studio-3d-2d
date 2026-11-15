"""Bounded, output-only resource staging for two checksum-bound SFM cases.

Default mode indexes and verifies only. --execute is a separate explicit step.
Never installs, launches Blender/Godot, mounts Steam, or deletes partial evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import threading
import time
import zlib

sys.dont_write_bytecode = True
TASK = Path(__file__).absolute().parents[1]
CHECKOUT = TASK.parents[1]
sys.path.insert(0, str(TASK / "overlay/tools"))
from source_archive import resource_path

PLAN_SHA = "4a747c6bc883af7e69ca448a0d7ac60f76f14b78550682647f683449cd1d2aaf"
SEVEN_SHA = "e2ca3ec168ae9c0b4115cd4fe220145ea9b2dc4b6fc79d765e91f415b34d00de"
CASE_COUNTS = {"multi_skin_glove": (230, 134276708), "keiki_tools_chisels": (66, 47183776)}
MAX_INDEX = 4 * 1024 * 1024
MAX_RESOURCE = 128 * 1024 * 1024
MAX_STDERR = 64 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def no_reparse(path):
    path = Path(path).absolute()
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400),
                "Link/reparse path refused: " + str(part))


def identity(path):
    path = Path(path)
    no_reparse(path)
    initial = path.stat()
    require(path.is_file(), "Expected regular file: " + str(path))
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    final = path.stat()
    require((initial.st_size, initial.st_mtime_ns) == (final.st_size, final.st_mtime_ns),
            "Input changed during read: " + str(path))
    return {"sha256": digest, "bytes": initial.st_size, "mtime_ns": initial.st_mtime_ns}


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, "Invalid " + label)
    return value


def safe_name(value):
    require(isinstance(value, str) and len(value) <= 2048, "Invalid/excessive member name")
    name = resource_path(value)
    require(not any(c in name for c in '<>"|?*'), "Invalid Windows member characters")
    return name


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def load_plan(path, expected_sha):
    no_reparse(path)
    require(path.stat().st_size <= 512 * 1024, "Plan exceeds512KiB")
    raw = path.read_bytes()
    require(len(raw) <= 512 * 1024 and hashlib.sha256(raw).hexdigest() == expected_sha,
            "Plan does not match the reviewed byte hash")
    value = json.loads(raw, object_pairs_hook=unique_object,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    return validate_plan(value)


def validate_plan(plan):
    require(isinstance(plan, dict) and plan.get("format") == "has_sfm_next_native_case_plan_1", "Wrong plan format")
    cases = plan.get("cases")
    require(isinstance(cases, list) and len(cases) == 2, "Exactly two reviewed cases required")
    seen = set()
    result = []
    for case in cases:
        key = case.get("case")
        require(key in CASE_COUNTS and key not in seen, "Unknown/duplicate case")
        seen.add(key)
        archive = case["archive"]
        require(Path(archive["archive"]).name == archive["archive"] and archive["archive"].lower().endswith(".rar"), "Unsafe archive name")
        require(re.fullmatch("[0-9a-f]{64}", archive["sha256"]) is not None, "Invalid archive checksum")
        integer(archive["bytes"], 1, 512 * 1024 * 1024, "archive size")
        integer(archive["mtime_ns"], 1, 2**64 - 1, "archive modification time")
        native = safe_name(case["native_member"])
        require(native.lower().endswith(".mdl"), "Native member must be MDL")
        require(re.fullmatch("[0-9a-f]{64}", case["native_mdl_sha256"]) is not None, "Invalid MDL checksum")
        entries = []
        names = set()
        for category, field in [("models", "model_allowlist"), ("materials", "material_allowlist")]:
            rows = case.get(field)
            require(isinstance(rows, list) and rows, "Missing resource allowlist")
            for row in rows:
                require(isinstance(row, dict) and set(row) == {"member", "bytes", "crc32"}, "Unexpected allowlist fields")
                name = safe_name(row["member"])
                parts = name.split("/")
                require(len(parts) >= 3 and parts[0] == native.split("/")[0] and parts[1] == category,
                        "Resource escaped its package/category")
                suffix = Path(name).suffix.lower()
                require(suffix in ({".mdl", ".vvd", ".vtx"} if category == "models" else {".vmt", ".vtf"}),
                        "Unlisted resource type")
                require(name.casefold() not in names, "Duplicate case-insensitive planned path")
                names.add(name.casefold())
                integer(row["bytes"], 1, MAX_RESOURCE, "resource size")
                require(re.fullmatch("[0-9A-F]{8}", row["crc32"]) is not None, "Invalid planned CRC")
                entries.append(dict(row, category=category))
        expected_models = {str(Path(native).with_suffix(suffix)).replace("\\", "/")
                           for suffix in [".mdl", ".vvd", ".dx80.vtx", ".dx90.vtx", ".sw.vtx"]}
        require({row["member"] for row in entries if row["category"] == "models"} == expected_models,
                "Model sidecar set differs from the five reviewed resources")
        require((len(entries), sum(row["bytes"] for row in entries)) == CASE_COUNTS[key], "Case file/byte budget differs")
        result.append({"case": key, "archive": archive, "native_member": native,
                       "native_mdl_sha256": case["native_mdl_sha256"], "entries": entries})
    require(seen == set(CASE_COUNTS), "Missing reviewed case")
    return result


def parse_index(raw):
    require(len(raw) <= MAX_INDEX, "Archive index exceeds4MiB")
    text = raw.decode("utf-8").replace("\r\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    entries, names, current = [], set(), {}
    for line in text.splitlines() + [""]:
        require(len(line) <= 8192, "Excessive archive index field")
        if line.strip():
            require(" = " in line, "Unexpected archive index line")
            key, value = line.split(" = ", 1)
            require(key not in current, "Duplicate archive index field")
            current[key] = value
            continue
        if not current:
            continue
        require("Path" in current and current.get("Folder") in {"+", "-"}, "Invalid archive index record")
        directory = current["Folder"] == "+"
        raw_name = current["Path"]
        name = safe_name(raw_name.rstrip("/\\") if directory else raw_name)
        require(name.casefold() not in names, "Duplicate case-insensitive archive member")
        names.add(name.casefold())
        for flag in ["Encrypted", "Anti", "Alternate Stream", "Split Before", "Split After"]:
            require(current.get(flag, "-") == "-", "Unsupported archive flag: " + flag)
        for flag in ["Symbolic Link", "Hard Link", "Copy Link", "Reparse Point"]:
            require(current.get(flag, "") in {"", "-"}, "Archive link refused")
        require("l" not in current.get("Attributes", "").lower(), "Archive link attribute refused")
        require(re.fullmatch("[0-9]+", current.get("Size", "")) is not None, "Invalid archive member size")
        size = integer(int(current["Size"]), 0, 512 * 1024 * 1024, "indexed size")
        if not directory:
            require(re.fullmatch("[0-9A-Fa-f]{8}", current.get("CRC", "")) is not None, "Missing/invalid indexed CRC")
        entries.append({"member": name, "native_name": raw_name, "bytes": size,
                        "crc32": current.get("CRC", "").upper(), "directory": directory})
        current = {}
        require(len(entries) <= 10000, "Archive index exceeds10000entries")
    require(entries, "Empty archive index")
    return entries


def match_index(case, entries):
    require(len(entries) == case["archive"]["index_entries"], "Archive index entry count changed")
    indexed = {row["member"].casefold(): row for row in entries}
    result = []
    for row in case["entries"]:
        item = indexed.get(row["member"].casefold())
        require(item is not None and not item["directory"] and item["member"] == row["member"]
                and item["bytes"] == row["bytes"] and item["crc32"] == row["crc32"],
                "Allowlisted resource is missing or changed: " + row["member"])
        result.append(dict(item, category=row["category"]))
    return result


class ResourceSink:
    def __init__(self, stream, limit):
        self.stream, self.limit = stream, limit
        self.count, self.crc, self.hash = 0, 0, hashlib.sha256()

    def write(self, block):
        require(self.count + len(block) <= self.limit, "Process output exceeds its byte budget")
        self.stream.write(block)
        self.count += len(block)
        self.crc = zlib.crc32(block, self.crc)
        self.hash.update(block)

    def result(self):
        return {"bytes": self.count, "crc32": f"{self.crc & 0xffffffff:08X}", "sha256": self.hash.hexdigest()}


def run_tool(args, sink, stderr_path, timeout=60):
    """Stream both pipes with independent caps; never invoke a shell."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    errors = []
    timed_out = []
    def kill_on_timeout():
        timed_out.append(True)
        if process.poll() is None:
            process.kill()
    def pump(pipe, target):
        try:
            while block := pipe.read(65536):
                target.write(block)
        except BaseException as error:
            errors.append(error)
            if process.poll() is None:
                process.kill()
        finally:
            pipe.close()
    with stderr_path.open("xb") as error_file:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, creationflags=flags)
        timer = threading.Timer(timeout, kill_on_timeout)
        error_sink = ResourceSink(error_file, MAX_STDERR)
        threads = [threading.Thread(target=pump, args=(process.stdout, sink)),
                   threading.Thread(target=pump, args=(process.stderr, error_sink))]
        for thread in threads:
            thread.start()
        timer.start()
        try:
            code = process.wait(timeout=timeout + 5)
            for thread in threads:
                thread.join(timeout=5)
            require(not any(thread.is_alive() for thread in threads), "Tool pipe did not finish")
            if errors:
                raise ValueError("Bounded process stream failed: " + str(errors[0]))
            require(not timed_out, "Archive tool timed out")
            require(code == 0, "Archive tool failed: " + str(code))
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


def checked_target(stage, case, member):
    require(case in CASE_COUNTS, "Unknown staged case")
    name = safe_name(member)
    base = stage / case
    target = base / name
    no_reparse(stage)
    no_reparse(target)
    require(base.parent == stage and target.absolute().is_relative_to(base.absolute()) and target != base,
            "Staged target escaped its case")
    require(not target.exists(), "Refusing to overwrite staged target")
    return target


def verify_resource(path, entry, result, expected_mdl_sha=None):
    require(result["bytes"] == entry["bytes"] and result["crc32"] == entry["crc32"],
            "Resource bytes/CRC differ: " + entry["member"])
    observed = identity(path)
    require(observed["bytes"] == result["bytes"] and observed["sha256"] == result["sha256"], "Staged resource changed")
    require(path.stat().st_nlink == 1, "Unexpected hard-linked staged file")
    if expected_mdl_sha is not None:
        require(result["sha256"] == expected_mdl_sha, "Selected MDL SHA differs")
        with path.open("rb") as stream:
            header = stream.read(80)
        require(len(header) == 80 and header[:4] == b"IDST" and struct.unpack_from("<I", header, 4)[0] == 49
                and struct.unpack_from("<I", header, 76)[0] == result["bytes"], "Selected MDL header differs")
    return observed


def save(path, value):
    no_reparse(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=TASK / "plan.json")
    parser.add_argument("--plan-sha256", default=PLAN_SHA)
    parser.add_argument("--seven-zip", type=Path, default=Path(r"C:\Program Files\7-Zip\7z.exe"))
    parser.add_argument("--archive-root", type=Path, help="Optional explicit read-only folder containing the same two checksum-bound RAR names")
    parser.add_argument("--stage-root", type=Path, default=TASK / "stage")
    parser.add_argument("--execute", action="store_true", help="Explicitly stage only the reviewed allowlisted resources after all preflight checks")
    options = parser.parse_args(argv)
    no_reparse(Path(__file__).absolute())
    no_reparse(TASK)
    stage = options.stage_root.absolute()
    require(stage.parent == TASK and re.fullmatch(r"stage(?:-[A-Za-z0-9_]+)?", stage.name), "Stage must be a fresh direct stage child of this task folder")
    no_reparse(stage)
    require(not stage.exists(), "Stage root must be fresh; failed/partial runs are retained")
    require(options.plan_sha256 == PLAN_SHA, "Only the frozen reviewed plan hash is accepted")
    cases = load_plan(options.plan.absolute(), PLAN_SHA)
    seven = options.seven_zip.absolute()
    require(identity(seven)["sha256"] == SEVEN_SHA, "7-Zip differs from the approved executable")
    if options.archive_root:
        no_reparse(options.archive_root)
        require(options.archive_root.is_dir(), "Archive root is absent")
    runs = TASK / "runs"
    no_reparse(runs)
    runs.mkdir(exist_ok=True)
    evidence = runs / ("execute-" if options.execute else "preflight-")
    evidence = evidence.with_name(evidence.name + str(time.time_ns()))
    evidence.mkdir(exist_ok=False)
    original_before, selected, staged = {}, [], []
    protected_paths = [Path(__file__).absolute(), options.plan.absolute(), seven,
                       CHECKOUT / "tools/source_archive.py", CHECKOUT / "tools/asset_audit.py"]
    protected_before = {str(path): identity(path) for path in protected_paths}
    report = {"format": "has_sfm_resource_staging_1", "mode": "execute" if options.execute else "preflight-only",
              "plan_sha256": PLAN_SHA, "stage": str(stage), "evidence": str(evidence),
              "blender_gpu_network_or_installed_writes": False, "automatic_cleanup": False,
              "staged": staged, "original_before": original_before, "passed": False}
    report["protected_tool_plan_sources_before"] = protected_before
    try:
        for case in cases:
            archive = ((options.archive_root / case["archive"]["archive"]) if options.archive_root else Path(case["archive"]["path"])).absolute()
            require(archive.name == case["archive"]["archive"], "Archive name differs")
            if options.archive_root:
                require(archive.parent == options.archive_root.absolute(), "Archive escaped explicit root")
            before = identity(archive)
            original_before[str(archive)] = before
            require(before == {key: case["archive"][key] for key in ["sha256", "bytes", "mtime_ns"]}, "Original archive identity differs")
            log = evidence / (case["case"] + "-index.log")
            with log.open("xb") as output:
                sink = ResourceSink(output, MAX_INDEX)
                run_tool([str(seven), "l", "-slt", "-ba", "-sccUTF-8", "-pHAS_NO_PASSWORD", "--", str(archive)], sink,
                         evidence / (case["case"] + "-index-stderr.log"), 30)
            matched = match_index(case, parse_index(log.read_bytes()))
            selected.append((case, archive, matched))
        require(sum(len(rows) for _, _, rows in selected) == 296 and sum(row["bytes"] for _, _, rows in selected for row in rows) == 181460484,
                "Combined resource budget differs")
        require(identity(seven)["sha256"] == SEVEN_SHA, "Archive tool changed before staging")
        require(all(identity(Path(path)) == value for path, value in original_before.items()), "Original changed during preflight")
        save(evidence / "preflight.json", {"passed": True, "files": 296, "bytes": 181460484,
                                           "archives": original_before, "stage_created": False})
        if options.execute:
            no_reparse(stage)
            stage.mkdir(exist_ok=False)
            with (evidence / "staged-progress.jsonl").open("x", encoding="utf-8") as progress:
                for case, archive, rows in selected:
                    for index, row in enumerate(rows):
                        target = checked_target(stage, case["case"], row["member"])
                        target.parent.mkdir(parents=True, exist_ok=True)
                        no_reparse(target)
                        with target.open("xb") as output:
                            sink = ResourceSink(output, row["bytes"])
                            run_tool([str(seven), "x", "-so", "-spd", "-pHAS_NO_PASSWORD", "--", str(archive), row["native_name"]], sink,
                                     evidence / (case["case"] + f"-{index:03d}-stderr.log"))
                        result = sink.result()
                        verified = verify_resource(target, row, result,
                                                   case["native_mdl_sha256"] if row["member"] == case["native_member"] else None)
                        item = {"case": case["case"], "archive": str(archive), "member": row["member"],
                                "path": str(target), "crc32": row["crc32"], **verified}
                        staged.append(item)
                        progress.write(json.dumps(item) + "\n")
                        progress.flush()
            expected = {str(stage / case["case"] / row["member"]) for case, _, rows in selected for row in rows}
            actual = set()
            for base, dirs, files in os.walk(stage, followlinks=False):
                for name in dirs + files:
                    no_reparse(Path(base) / name)
                actual.update(str(Path(base) / name) for name in files)
            require(actual == expected and len(staged) == 296 and sum(row["bytes"] for row in staged) == 181460484, "Staged inventory differs")
            require(all(identity(Path(row["path"])) == {key: row[key] for key in ["sha256", "bytes", "mtime_ns"]} for row in staged), "Staged data changed after verification")
        report["passed"] = True
    except BaseException as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        final = {}
        for path, before in original_before.items():
            try:
                final[path] = identity(Path(path))
            except BaseException as error:
                final[path] = {"error": str(error)}
        report["original_after"] = final
        report["originals_unchanged"] = final == original_before
        if not report["originals_unchanged"]:
            report["passed"] = False
        report["staged_files"] = len(staged)
        report["staged_bytes"] = sum(row["bytes"] for row in staged)
        protected_after = {}
        for path in protected_paths:
            try:
                protected_after[str(path)] = identity(path)
            except BaseException as error:
                protected_after[str(path)] = {"error": str(error)}
        report["protected_tool_plan_sources_after"] = protected_after
        report["tool_plan_sources_unchanged"] = protected_before == protected_after
        if not report["tool_plan_sources_unchanged"]:
            report["passed"] = False
        save(evidence / "verification.json", report)
        print(json.dumps({key: report[key] for key in ["mode", "passed", "stage", "evidence", "staged_files", "staged_bytes", "originals_unchanged"]}), flush=True)
    require(report["passed"], "Staging/preservation did not pass")


if __name__ == "__main__":
    main()
