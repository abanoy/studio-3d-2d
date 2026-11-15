"""Summarize a terminal, source-preserved canonical using metadata only.

Do not execute until root grants terminal permission and supplies fresh closure
and receipt-audit files. No subprocess, runtime import, asset read or release.
"""
import argparse
import calendar
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import stat
import zlib

TASK = Path(__file__).absolute().parent
ROOT = TASK.parents[1]
DEFAULT_RUN = ROOT / "output/windows-canonical-sfm-20261114T002803393"
DEFAULT_COMMIT = "9f6f531538156fc34e3652bc81da8a608e379156"
MAXIMUM = 64 * 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def utc_ns(value):
    match = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z", value)
    require(match is not None, "Expected bounded UTC timestamp")
    seconds = calendar.timegm(datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%S").timetuple())
    return seconds * 1_000_000_000 + int((match[2] or "").ljust(9, "0"))


def digest(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def identity(path):
    for parent in (path, *path.parents):
        info = parent.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                "Reparse metadata path refused")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_size <= MAXIMUM, "Unexpected metadata kind/size")
    return (info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino)


def read(path):
    before = identity(path)
    with path.open("rb") as stream:
        raw = stream.read(MAXIMUM + 1)
    require(len(raw) == before[0] and identity(path) == before, "Metadata changed during read")
    return raw, {**digest(raw), "mtime_ns": before[1], "device": before[2], "inode": before[3]}


def parse(raw):
    def nonfinite(value):
        raise ValueError("Nonfinite JSON number refused: " + value)
    return json.loads(raw.decode("utf-8-sig"), parse_constant=nonfinite)


def count(row, field):
    value = row[field]
    require(type(value) is int and value >= 0, "Invalid scoped count: " + field)
    return value


def named_reports(rows):
    answer = {}
    for name, row in rows.items():
        require(count(row, "failures") == 0, "Named report has failures: " + name)
        answer[name] = {"checks": count(row, "checks"), "failures": 0}
    return answer


def content_audit(value):
    """Conservative metadata gate; refuse unfamiliar payload-shaped fields."""
    counts = dict(objects=0, arrays=0, strings=0, numbers=0, booleans=0, nulls=0)
    suspects, large_arrays = [], []
    maximum_string = maximum_depth = 0
    def walk(item, path, depth):
        nonlocal maximum_string, maximum_depth
        maximum_depth = max(maximum_depth, depth)
        require(depth <= 80, "Metadata nesting over bound")
        if isinstance(item, dict):
            counts["objects"] += 1
            for key, child in item.items():
                lower = key.casefold()
                if lower in {"pixels", "image_data", "audio_data", "vertex_buffer", "index_buffer", "base64"} and child:
                    suspects.append(path + "." + key)
                if lower in {"vertices", "indices", "triangles"} and isinstance(child, (list, dict)):
                    suspects.append(path + "." + key)
                walk(child, path + "." + key, depth + 1)
        elif isinstance(item, list):
            counts["arrays"] += 1
            if len(item) >= 16:
                large_arrays.append({"path": path, "count": len(item)})
                if all(type(child) in (float, int) for child in item):
                    suspects.append(path)
                if all(isinstance(child, list) and child and all(type(n) in (float, int) for n in child) for child in item):
                    suspects.append(path)
            for index, child in enumerate(item):
                walk(child, path + "[" + str(index) + "]", depth + 1)
        elif isinstance(item, str):
            counts["strings"] += 1
            maximum_string = max(maximum_string, len(item))
            if len(item) > 1024 or re.search(r"data:[^\s,]*;base64,", item, re.I) or item.startswith(("iVBORw0KGgo", "/9j/")):
                suspects.append(path)
        elif type(item) is bool:
            counts["booleans"] += 1
        elif type(item) in (float, int):
            counts["numbers"] += 1
            require(type(item) is int or math.isfinite(item), "Nonfinite metadata")
        elif item is None:
            counts["nulls"] += 1
        else:
            raise ValueError("Unexpected JSON value")
    walk(value, "$", 0)
    require(not suspects, "Manual content review required for payload-shaped paths: " + repr(suspects[:12]))
    return {**counts, "maximum_string_characters": maximum_string, "maximum_depth": maximum_depth,
            "large_arrays": large_arrays, "payload_suspects": [], "referenced_assets_opened": False,
            "scope": "Conservative structural metadata inspection; local paths/authored document snapshots retained"}


def summarize(result):
    # All new expected scopes must exist; a stale pre-SFM report is insufficient.
    foundation = result["source_choice_foundation"]
    require(foundation["passed"] is True and foundation["source_unchanged"] is True and foundation["native_conversion"] is False,
            "Source-choice foundation did not pass")
    reports = foundation["reports"]
    split = {"catalogue": count(reports["catalogue"], "tests"), "appearance": count(reports["appearance"], "tests"),
             "unit": count(reports["unit"], "checks"), "ui": count(reports["ui"]["result"], "checks")}
    require(sum(split.values()) == count(foundation, "checks"), "Foundation total disagrees with its named scopes")
    resource, bootstrap = reports["resource_write"], reports["bridge_bootstrap"]
    require(count(resource, "passed") + count(resource, "skipped") == count(resource, "tests"), "Resource method count mismatch")
    require(count(bootstrap, "passed") == count(bootstrap, "tests"), "Bootstrap methods did not all pass")
    placement = result["import_placement"]
    require(count(placement, "failures") == 0 and placement["headless_bounds"] == placement["bounds"], "Placement gate failed")
    require(count(placement["headless_bounds"], "failures") == 0, "Placement bounds failed")
    helper = {}
    for key in ("helper_preview_cpu", "helper_preview_graphical"):
        row = result[key]
        require(row["passed"] is True and all(item is True for item in row["preservation"].values()), "Helper preservation failed")
        children = [{name: child[name] for name in ("label", "checks", "expected_checks", "passed", "result_source_context_bound")} for child in row["results"]]
        require(all(child["passed"] is True and child["result_source_context_bound"] is True and child["checks"] == child["expected_checks"] for child in children), "Helper result admission failed")
        require(sum(child["checks"] for child in children) == count(row, "checks"), "Helper scoped total mismatch")
        helper[key] = {name: row[name] for name in ("mode", "source_context", "overlay_files", "native_requested", "native_inputs_checked", "native_fidelity", "gpu_used", "checks", "passed", "preservation")}
        helper[key]["rows"] = children
    wind = result["wind_review"]
    require(wind["passed"] is True and all(row["passed"] is True for row in wind["results"]), "Wind gate failed")
    background = named_reports(result["has_background_save"]["reports"])
    body = named_reports(result["body_animation"]["reports"])
    core = {name: row for name, row in result.items() if isinstance(row, dict) and set(row) == {"exit", "seconds"}}
    require(core and all(type(row["exit"]) is int and row["exit"] == 0 for row in core.values()), "Core process scope did not pass")
    return {"result_key_count": len(result), "result_keys": list(result), "core_process_groups": core,
        "core_process_group_count": len(core), "source_choice_foundation": {"checks": foundation["checks"], "split": split,
            "resource_write_methods": resource, "bridge_bootstrap_methods": bootstrap},
        "import_placement": {"graphical_checks": count(placement, "checks"), "headless_bounds": placement["headless_bounds"],
            "separate_named_scoped_sum": count(placement, "checks") + count(placement["headless_bounds"], "checks"), "video": placement["video"]},
        "helper_preview": helper, "wind": {"checks": sum(count(row, "checks") for row in wind["results"]), "cases": len(wind["results"]), "passed": wind["passed"]},
        "background_save_reports": background, "background_save_named_scoped_sum": sum(row["checks"] for row in background.values()),
        "body_animation_reports": body, "body_native_fixture_count": result["body_animation"]["native_fixture_count"],
        "pose_checks": result["pose_checks"], "actual_mmd_tested": result["actual_mmd_tested"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal-permission", action="store_true", required=True)
    parser.add_argument("--run-directory", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--expected-commit", default=DEFAULT_COMMIT)
    parser.add_argument("--expected-pid", type=int, default=3136)
    parser.add_argument("--host-proof", type=Path, required=True)
    parser.add_argument("--host-sha256", required=True)
    parser.add_argument("--receipt-inventory", type=Path, required=True)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    options = parser.parse_args()
    run = options.run_directory.absolute()
    require(".." not in run.parts and run.parent == ROOT / "output", "Canonical must be a direct owned output folder")
    inputs = {}
    def acquire(path):
        path = path.absolute()
        require(".." not in path.parts and path.is_relative_to(ROOT / "output"), "Metadata outside owned output refused")
        raw, proof = read(path)
        inputs[str(path)] = proof
        return raw
    # FIRST metadata gate: no output or other report read can precede terminal PASS.
    state_raw = acquire(run / "state.json")
    state = parse(state_raw)
    require(state["status"] == "passed" and type(state["suite_exit"]) is int and state["suite_exit"] == 0 and state["source_unchanged"] is True,
            "Refused: canonical is running, failed, or source-changed")
    require(state["source_commit"] == options.expected_commit and state["pid"] == options.expected_pid, "Wrong canonical revision/PID")
    start, finish = utc_ns(state["started_utc"]), utc_ns(state["finished_utc"])
    require(start <= finish, "Canonical time interval invalid")
    source_before_raw, source_after_raw = acquire(run / "source-before.json"), acquire(run / "source-after.json")
    before, after = parse(source_before_raw), parse(source_after_raw)
    require(before == after and before["commit"] == options.expected_commit and before["source_sha256"], "Canonical before/after mismatch")
    launch_raw = acquire(run / "launch.json")
    launch = parse(launch_raw)
    require(launch["pid"] == state["pid"] and launch["creation_utc"] == state["process_started"] and launch["source_commit"] == state["source_commit"], "Launch identity mismatch")
    require(Path(state["run_folder"]).absolute() == Path(launch["run_folder"]).absolute() == run and Path(state["checkout"]).absolute() == ROOT,
            "Wrong canonical paths")
    require(launch["runner_sha256"] == state["script_sha256"] and launch["authoritative_owned_workers_absent_before_launch"] is True and launch["exclusive_private_graphics_lease"] is True,
            "Launch source/lease guard failed")
    host_raw, receipt_raw = acquire(options.host_proof), acquire(options.receipt_inventory)
    require(digest(host_raw)["sha256"] == options.host_sha256 and digest(receipt_raw)["sha256"] == options.receipt_sha256, "Fresh closure SHA mismatch")
    host, inventory = parse(host_raw), parse(receipt_raw)
    require(host["format"] == "has_canonical_authoritative_host_termination_1" and host["canonical_run"] == run.name and host["source_commit"] == state["source_commit"], "Wrong host closure context")
    require(host["coordinator_pid"] == state["pid"] and host["expected_creation_utc"] == state["process_started"] and utc_ns(host["observed_utc"]) >= finish,
            "Stale/wrong host closure")
    require(host["coordinator_absent"] is True and host["owned_runtime_command_matches_absent"] is True and not host["coordinator_matches"] and not host["owned_runtime_matches"], "Canonical owner/runtime still present")
    audit = inventory["summary"]
    require(audit["passed"] is True and audit["source_commit"] == state["source_commit"] and Path(audit["run_directory"]).absolute() == run and audit["state"] == state,
            "Wrong receipt-audit context")
    require(audit["source_before_after_equal"] is True and audit["functional_source_entries"] == len(before["source_sha256"]), "Receipt source binding mismatch")
    require(all(audit[key] is True for key in ("fresh_root_all_exit_0", "fresh_root_all_private_closed", "all_receipts_private_closed", "all_receipts_fresh_for_run", "all_inline_exact_physical_matches"))
            and not audit["unexpected_failures"] and audit["missing_referenced_receipts"] == 0, "Receipt audit not clean")
    report_path = ROOT / "output/verification.json"
    report_raw = acquire(report_path)
    require(start <= inputs[str(report_path)]["mtime_ns"] <= finish, "Verification report is stale/outside this run")
    result = parse(report_raw)
    log_raw = acquire(run / "canonical.log")
    log = log_raw.decode("utf-8-sig").replace("\r\n", "\n").rstrip()
    normalized_report = report_raw.decode("utf-8-sig").replace("\r\n", "\n").rstrip()
    require(log.endswith(normalized_report), "Canonical log does not end with the exact normalized fresh report")
    prefix = log[:-len(normalized_report)]
    markers = [line for line in prefix.splitlines() if line.strip()]
    require(markers and all(line.startswith("PASS ") for line in markers), "Unexpected canonical log prefix")
    summary = summarize(result)
    summary.update(format="has_canonical_sfm_metadata_summary_1", run_directory=str(run), source_commit=state["source_commit"],
        status=state["status"], suite_exit=state["suite_exit"], started_utc=state["started_utc"], finished_utc=state["finished_utc"],
        elapsed_seconds=(finish-start)/1_000_000_000, source_before_after_equal=True,
        source_files_before=len(before["source_sha256"]), source_files_after=len(after["source_sha256"]),
        pass_marker_count=len(markers), pass_markers=markers, verification=digest(report_raw), receipt_audit_summary=audit,
        content_audit=content_audit(result))
    movies = {name: row for name, row in result.items() if isinstance(row, dict) and set(row) == {"frames", "fps", "duration"}}
    probes = {}
    for key, movie in movies.items():
        if key.startswith("posed_model_video_"):
            continue
        name = key.removesuffix("_video")
        probe_path = ROOT / "output" / (name + "-ffprobe.json")
        probe = parse(acquire(probe_path))
        require(start <= inputs[str(probe_path)]["mtime_ns"] <= finish, "Stale media metadata")
        streams = probe["streams"]
        videos = [row for row in streams if row["codec_type"] == "video"]
        require(len(videos) == 1, "Ambiguous video stream")
        video = videos[0]
        require(int(video["nb_read_frames"]) == movie["frames"] and video["r_frame_rate"] == movie["fps"], "Media/report mismatch")
        probes[name] = {"metadata_identity": inputs[str(probe_path)], "video_codec": video["codec_name"], "width": video["width"], "height": video["height"],
                        "audio_codecs": [row["codec_name"] for row in streams if row["codec_type"] == "audio"]}
    summary["media"] = {"root_movie_count": len(movies), "root_movies": movies, "fresh_ffprobe_count": len(probes), "fresh_ffprobe_metadata": probes,
        "aac_movie_count": sum("aac" in row["audio_codecs"] for row in probes.values()), "no_audio_movie_count": sum(not row["audio_codecs"] for row in probes.values()),
        "tone_onset_seconds": result["tone_onset_seconds"], "editor_audio": result["editor_audio"],
        "distinct_silent_tone_paths": result["spike_fixture"]["silent_movie"] != result["spike_fixture"]["tone_movie"],
        "media_files_opened": False, "posed_movie_limit": "Root canonical checks retained; no separate posed ffprobe JSON was published by the suite"}
    summary["limits"] = ["Named scopes overlap; no deduplicated all-assertion total is claimed", "Metadata retains local paths, names, hashes and authored test/document/pose snapshots",
        "No referenced asset/media/runtime was opened; no source code/test/graphics worker or lease release ran", "Native controller/shader/jiggle fidelity and manual owner acceptance remain separate"]
    payloads = {"canonical/state.json": state_raw, "canonical/launch.json": launch_raw, "closure/host-proof.json": host_raw,
                "canonical/pass-markers.txt": ("\n".join(markers)+"\n").encode(), "recipe/summarize_canonical.py": acquire(Path(__file__))}
    originals = {}
    for name, raw in (("verification.json", report_raw), ("canonical/source-before.json", source_before_raw), ("canonical/source-after.json", source_after_raw),
                      ("canonical/canonical.log", log_raw), ("closure/receipt-inventory.json", receipt_raw)):
        compressed = gzip.compress(raw, compresslevel=9, mtime=0)
        require(gzip.decompress(compressed) == raw and gzip.compress(raw, compresslevel=9, mtime=0) == compressed, "Lossless deterministic gzip failed")
        payloads[name + ".gz"] = compressed
        originals[name + ".gz"] = digest(raw)
    summary["compression"] = {"method": "gzip.compress(level=9,mtime=0)", "python": platform.python_version(), "zlib": zlib.ZLIB_VERSION,
        "raw_identities": originals, "raw_SHA_is_authority_across_library_versions": True}
    summary["input_identities"] = inputs
    require(all(read(Path(path))[1] == expected for path, expected in inputs.items()), "Canonical metadata changed during summary")
    payloads["SUMMARY.json"] = (json.dumps(summary, indent=2, allow_nan=False)+"\n").encode()
    destination = options.destination.absolute()
    require(destination.parent == TASK and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,100}", destination.name) is not None and not destination.exists(),
            "Require a fresh direct owned summary destination")
    destination.mkdir(parents=False, exist_ok=False)
    rows = []
    for name, raw in payloads.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        require(target.read_bytes() == raw, "Summary readback differs")
        rows.append({"path": name, **digest(raw)})
    require(all(read(Path(path))[1] == expected for path, expected in inputs.items()), "Canonical metadata changed while writing summary")
    index = {"format": "has_canonical_sfm_summary_packet_1", "source_commit": state["source_commit"], "payload_files": len(rows),
             "payload_bytes": sum(row["bytes"] for row in rows), "gzip_originals": originals, "files": rows}
    with (destination / "INDEX.json").open("x", encoding="utf-8") as stream:
        json.dump(index, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"destination": str(destination), "index": digest((destination / "INDEX.json").read_bytes()),
                      "payload_files": len(rows), "payload_bytes": index["payload_bytes"]}))


if __name__ == "__main__":
    main()
