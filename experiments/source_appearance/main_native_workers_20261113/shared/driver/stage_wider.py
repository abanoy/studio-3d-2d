"""Stage exactly265 allowlisted resource bytes, never run model scripts or convert.

Cached Mima bytes are eligible only with retained archive-bound per-member SHA,
fresh SHA/length and current original archive index CRC. All other bytes use
the previously audited bounded7z stdout path. No broad filesystem extraction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
sys.path.insert(0, str(TASK / "source"))
import archive_safety as S

PLAN_SHA = "9dbf1ac891379505a8c56657d93ee6efb8bac9ce41a14d0f76ffdbba5aa15cad"
CACHE_RECEIPT = ROOT / "output/resume-mima-repro/staging.json"
CACHE_ROOT = ROOT / "output/resume-mima-repro/stage"
CACHE_SHA = "9cf6d9c09909e516090a8b375ac961f422a5d7be229cf6295c3eb2526066cdbb"

def read(path, sha=None):
    S.no_reparse(path)
    raw = path.read_bytes()
    S.require(len(raw) <= 8 * 1024 * 1024, "Metadata exceeds bound")
    if sha: S.require(hashlib.sha256(raw).hexdigest() == sha, "Metadata hash differs")
    return json.loads(raw, object_pairs_hook=S.unique_object)

def target(stage, family, member):
    S.require(family in {"junko_v25", "mima", "kanako"}, "Unknown family")
    result = stage / family / S.safe_name(member)
    S.no_reparse(result)
    S.require(result.is_relative_to(stage / family) and not result.exists(), "Target escaped or would overwrite")
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    options = parser.parse_args(argv)
    plan_path = TASK / "RESOURCE_PLAN.json"
    plan = read(plan_path, PLAN_SHA)
    stage = TASK / "stage"
    S.no_reparse(stage)
    S.require(not stage.exists(), "Fresh stage required; retain partial evidence")
    seven = Path(plan["extractor"])
    S.require(S.identity(seven)["sha256"] == S.SEVEN_SHA, "Approved archive tool changed")
    cache = read(CACHE_RECEIPT, CACHE_SHA)
    mima = next(case for case in plan["cases"] if case["family"] == "mima")
    S.require(cache["source"] == mima["archive"] and cache["original_sha256"] == mima["archive_identity"]["sha256"] and cache["original_unchanged"] is True, "Cache provenance differs")
    cached = {S.safe_name(row["path"]): row for row in cache["resource_files"]}
    S.require(len(cached) == len(cache["resource_files"]) == 115, "Cache receipt duplicate/count differs")
    before = {path: S.identity(Path(path)) for path in plan["protected_inputs_before_after"]}
    S.require(before == plan["protected_inputs_before_after"], "Core/current protected input differs")
    for path in (Path(__file__), plan_path, seven, CACHE_RECEIPT, Path(S.__file__), ROOT / "tools/source_archive.py"):
        before[str(path)] = S.identity(path)
    run = TASK / "runs" / ("wider-" + ("execute-" if options.execute else "preflight-") + str(time.time_ns()))
    run.mkdir(exist_ok=False)
    report = {"format": "has_sfm_wider_owned_resource_stage_1", "mode": "execute" if options.execute else "preflight",
        "stage": str(stage), "passed": False, "rows": [], "cache_source_inputs": {}, "protected_before": before,
        "native_conversion_gpu_toolinstall_steamwrites": False, "automatic_cleanup": False}
    selected = []
    try:
        for case in plan["cases"]:
            archive = Path(case["archive"])
            S.require(S.identity(archive) == case["archive_identity"], "Original archive differs")
            index = run / (case["family"] + "-index.log")
            with index.open("xb") as stream:
                S.run_tool([str(seven), "l", "-slt", "-ba", "-sccUTF-8", "-pHAS_NO_PASSWORD", "--", str(archive)], S.ResourceSink(stream, S.MAX_INDEX), run / (case["family"] + "-index-stderr.log"), 30)
            entries = S.parse_index(index.read_bytes())
            table = {row["member"]: row for row in entries}
            S.require(len(entries) == case["index_entries"] and len(table) == len(entries), "Archive index membership differs")
            for row in case["resources"]:
                S.require(table.get(row["member"]) == row, "Allowlisted archive row/CRC/length differs")
                selected.append((case, archive, row))
        S.require(len(selected) == 265 and sum(r[2]["bytes"] for r in selected) == 287669903, "Frozen wider resource budget differs")
        eligible = {}
        for case, _, row in selected:
            if case["family"] == "mima" and row["member"] in cached:
                previous = cached[row["member"]]; path = CACHE_ROOT / row["member"]
                actual = S.identity(path)
                S.require(actual["sha256"] == previous["sha256"] and actual["bytes"] == previous["bytes"] == row["bytes"], "Proven retained Mima bytes differ")
                eligible[row["member"]] = path
                report["cache_source_inputs"][str(path)] = actual
        if options.execute:
            stage.mkdir(exist_ok=False)
            with (run / "progress.jsonl").open("x", encoding="utf-8") as progress:
                for index, (case, archive, row) in enumerate(selected):
                    destination = target(stage, case["family"], row["member"])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    cached_path = eligible.get(row["member"]) if case["family"] == "mima" else None
                    with destination.open("xb") as stream:
                        sink = S.ResourceSink(stream, row["bytes"])
                        if cached_path:
                            with cached_path.open("rb") as source:
                                while block := source.read(1024 * 1024): sink.write(block)
                        else:
                            S.run_tool([str(seven), "x", "-so", "-spd", "-pHAS_NO_PASSWORD", "--", str(archive), row["native_name"]], sink,
                                run / (case["family"] + f"-{index:03d}-stderr.log"))
                    mdl_sha = next((item["native_mdl_sha256"] for item in case["selected_models"] if item["native_member"] == row["member"]), None)
                    observed = S.verify_resource(destination, row, sink.result(), mdl_sha)
                    item = {"family": case["family"], "member": row["member"], "path": str(destination), "crc32": row["crc32"],
                        "origin": "archive-bound retained copy" if cached_path else "bounded7z member stdout", **observed}
                    report["rows"].append(item); progress.write(json.dumps(item) + "\n"); progress.flush()
            expected = {str(stage / c["family"] / r["member"]) for c, _, r in selected}
            actual = set()
            for base, dirs, files in os.walk(stage, followlinks=False):
                for name in dirs + files: S.no_reparse(Path(base) / name)
                actual.update(str(Path(base) / name) for name in files)
            S.require(actual == expected, "Owned stage membership differs")
        report["passed"] = True
    except BaseException as error:
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        report["protected_after"] = {path: S.identity(Path(path)) for path in before}
        report["protected_unchanged"] = report["protected_after"] == before
        report["cache_inputs_unchanged"] = all(S.identity(Path(path)) == value for path, value in report["cache_source_inputs"].items())
        report["staged_outputs_unchanged"] = all(S.identity(Path(r["path"])) == {k: r[k] for k in ("sha256", "bytes", "mtime_ns")} for r in report["rows"])
        report["passed"] = report["passed"] and report["protected_unchanged"] and report["cache_inputs_unchanged"] and report["staged_outputs_unchanged"]
        report["staged_files"] = len(report["rows"]); report["staged_bytes"] = sum(r["bytes"] for r in report["rows"])
        report["eligible_cache_files"] = len(report["cache_source_inputs"])
        S.save(run / "verification.json", report)
        print(json.dumps({key: report[key] for key in ("mode", "passed", "staged_files", "staged_bytes", "eligible_cache_files", "protected_unchanged")}), flush=True)
    S.require(report["passed"], "Wider resource stage/preservation failed; retain evidence")

if __name__ == "__main__": main()
