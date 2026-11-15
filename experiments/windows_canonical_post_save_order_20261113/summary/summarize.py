"""Read completed result metadata only; no tests, graphics, release or source edits."""
from pathlib import Path
from datetime import datetime
import gzip
import hashlib
import json
import platform
import zlib

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RUN = ROOT / "output/canonical-owned-20261113T211216019"
REPORT = ROOT / "output/verification.json"

def read(path, maximum=4 * 1024 * 1024):
    before = path.stat()
    if before.st_size > maximum: raise RuntimeError("Metadata input over bound")
    with path.open("rb") as stream: raw = stream.read(maximum + 1)
    after = path.stat()
    if len(raw) != before.st_size or len(raw) > maximum or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("Metadata changed during read")
    return raw, {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": after.st_mtime_ns}

def main():
    raw, identity = read(REPORT); result = json.loads(raw)
    state_raw, state_id = read(RUN / "state.json"); state = json.loads(state_raw)
    before_raw, before_id = read(RUN / "source-before.json"); before = json.loads(before_raw)
    after_raw, after_id = read(RUN / "source-after.json"); after = json.loads(after_raw)
    if state["status"] != "passed" or state["suite_exit"] != 0 or not state["source_unchanged"]:
        raise RuntimeError("Not a passed source-preserved canonical")
    if before != after or before["commit"] != state["source_commit"]:
        raise RuntimeError("Canonical source before/after differs")
    movies = {name: value for name, value in result.items() if isinstance(value, dict) and set(value) == {"frames", "fps", "duration"}}
    movie_shapes = sorted({(m["frames"], m["fps"], m["duration"]) for m in movies.values()})
    helper = {}
    for key in ("helper_preview_cpu", "helper_preview_graphical"):
        row = result[key]
        helper[key] = {name: row[name] for name in ("mode", "source_context", "overlay_files", "native_requested", "native_inputs_checked", "native_fidelity", "gpu_used", "checks", "passed", "preservation")}
        helper[key]["rows"] = [{name: child[name] for name in ("label", "checks", "expected_checks", "passed", "result_source_context_bound")} for child in row["results"]]
        if not row["passed"] or not all(row["preservation"].values()): raise RuntimeError("Helper gate failed")
    background = result["has_background_save"]["reports"]
    background_counts = {key: {"checks": value["checks"], "failures": value["failures"]} for key, value in background.items()}
    body = {key: {"checks": row["checks"], "failures": row["failures"]} for key, row in result["body_animation"]["reports"].items()}
    wind = result["wind_review"]
    audio_streams = {}
    for key in movies:
        if key.startswith("posed_model_video_"): continue
        name = key.removesuffix("_video")
        metadata_raw, metadata_id = read(ROOT / "output" / (name + "-ffprobe.json"))
        metadata = json.loads(metadata_raw)
        streams = metadata["streams"]
        video = next(row for row in streams if row["codec_type"] == "video")
        audio_streams[name] = {"metadata": metadata_id, "audio_codecs": [row["codec_name"] for row in streams if row["codec_type"] == "audio"],
            "video_codec": video["codec_name"], "width": video["width"], "height": video["height"]}
    # Compression is evaluated in memory only. This creates no publication,
    # release, graphics lease or compressed report on disk.
    first = gzip.compress(raw, compresslevel=9, mtime=0)
    second = gzip.compress(raw, compresslevel=9, mtime=0)
    compression = {"method": "gzip.compress(level=9, mtime=0)", "python": platform.python_version(),
        "zlib": zlib.ZLIB_VERSION, "bytes": len(first), "sha256": hashlib.sha256(first).hexdigest(),
        "two_in_memory_results_identical": first == second, "roundtrip_exact": gzip.decompress(first) == raw,
        "compressed_artifact_written": False, "note": "Exact compressed bytes are bound to these runtime/library versions; raw SHA remains the authority"}
    summary = {"format": "studio_canonical_post_save_metadata_summary_1", "canonical_folder": str(RUN),
        "source_commit": state["source_commit"], "status": state["status"], "suite_exit": state["suite_exit"],
        "started_utc": state["started_utc"], "finished_utc": state["finished_utc"],
        "elapsed_seconds": (datetime.fromisoformat(state["finished_utc"]) - datetime.fromisoformat(state["started_utc"])).total_seconds(),
        "verification_json": identity, "root_keys": len(result), "source_files_before": len(before["source_sha256"]),
        "source_files_after": len(after["source_sha256"]), "source_before_after_exact": before == after,
        "canonical_metadata_inputs": {"state": state_id, "source_before": before_id, "source_after": after_id},
        "root_movie_probe_count": len(movies), "root_movie_names": list(movies), "root_movie_shapes": movie_shapes,
        "audio": {"tone_onset_seconds": result["tone_onset_seconds"], "editor_audio": result["editor_audio"],
                  "silent_and_tone_movies_have_distinct_folders": result["spike_fixture"]["silent_movie"] != result["spike_fixture"]["tone_movie"],
                  "existing_ffprobe_metadata": audio_streams, "existing_ffprobe_count": len(audio_streams),
                  "aac_movie_count": sum("aac" in row["audio_codecs"] for row in audio_streams.values()),
                  "no_audio_movie_count": sum(not row["audio_codecs"] for row in audio_streams.values()),
                  "note": "Existing generated JSON only; no media file or ffprobe process opened here. Two posed movie entries retain canonical video checks only."},
        "helper_preview": helper, "background_save_reports": background_counts,
        "background_save_scoped_sum": sum(row["checks"] for row in background_counts.values()),
        "body_animation_reports": body, "body_native_fixture_count": result["body_animation"]["native_fixture_count"],
        "body_profiles": list(result["body_animation"]["metrics"]),
        "wind_graphical_checks": sum(row["checks"] for row in wind["results"]), "wind_graphical_cases": len(wind["results"]),
        "wind_passed": wind["passed"], "compression_analysis": compression,
        "limits": ["Counts are named scoped reports, not a deduplicated total of every suite assertion",
            "The new helper default registration requests no native fixture; native fidelity is explicitly false",
            "Native fixture/body tests do not certify full native shader/flex/jiggle fidelity",
            "No new graphics/test/runtime worker or release was launched by this metadata summary",
            "Metadata includes local paths, names, hashes, authored document/pose snapshots and hardware/timing details; it is not anonymized"]}
    if read(REPORT)[1] != identity: raise RuntimeError("Fresh report changed while summarizing")
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("source_commit", "status", "elapsed_seconds", "root_keys", "source_files_before", "source_files_after", "source_before_after_exact", "root_movie_probe_count", "root_movie_shapes", "background_save_scoped_sum", "body_animation_reports", "wind_graphical_checks", "wind_graphical_cases", "compression_analysis")}))

if __name__ == "__main__": main()
