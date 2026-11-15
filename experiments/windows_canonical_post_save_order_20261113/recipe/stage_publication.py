"""Stage completed metadata only; final index waits for root audit/release paths."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
RUN = ROOT / "output/canonical-owned-20261113T211216019"
SUMMARY = ROOT / "output/canonical-post-save-summary-20261113"
RAW_SHA = "c431e33c5374c7881683713cca1c22ee415fa98fe5b66973f3785731f6acb79c"
GZIP_SHA = "7d27878353f349df5d71b65d94bdbc34c781989b19559b5f045dffa8582066f7"
SUMMARY_INDEX_SHA = "1bbd2149f55482b6d48b154d4df33f67d6b030e553b04d8a07af6bc616485ba7"
COMMIT = "12071fe182a17d17e2a1547c7dbb97f6aa4dd160"

def digest(raw): return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def read(path, maximum=4 * 1024 * 1024):
    info = path.stat()
    if path.is_symlink() or info.st_file_attributes & 0x400 or info.st_size > maximum:
        raise RuntimeError("Unexpected input kind/size")
    with path.open("rb") as stream: raw = stream.read(maximum + 1)
    after = path.stat()
    if len(raw) != info.st_size or len(raw) > maximum or (info.st_size, info.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("Input changed during read")
    return raw, {**digest(raw), "mtime_ns": after.st_mtime_ns}

def main():
    destination = TASK / "publication-candidate"
    destination.mkdir(exist_ok=False)
    initial = {}; files = {}; gzip_originals = {}
    def put(relative, raw):
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()): raise RuntimeError("Escaped stage")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream: stream.write(raw)
        if target.read_bytes() != raw: raise RuntimeError("Stage copy differs")
        files[relative] = digest(raw)
    def acquire(path):
        raw, identity = read(path); initial[str(path)] = identity; return raw
    raw = acquire(ROOT / "output/verification.json")
    if digest(raw) != {"sha256": RAW_SHA, "bytes": 2090687}: raise RuntimeError("Fresh full report differs")
    json.loads(raw)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    if digest(compressed) != {"sha256": GZIP_SHA, "bytes": 785510} or gzip.decompress(compressed) != raw:
        raise RuntimeError("Expected deterministic report gzip differs")
    put("verification.json.gz", compressed)
    gzip_originals["verification.json.gz"] = digest(raw)
    for name in ("source-before.json", "source-after.json", "state.json", "launch.json", "authoritative-host-termination.json", "desktop-enumeration.json"):
        data = acquire(RUN / name); json.loads(data); put("canonical/" + name, data)
    state = json.loads((destination / "canonical/state.json").read_bytes())
    before = json.loads((destination / "canonical/source-before.json").read_bytes())
    after = json.loads((destination / "canonical/source-after.json").read_bytes())
    if state.get("status") != "passed" or state.get("suite_exit") != 0 or state.get("source_commit") != COMMIT or not state.get("source_unchanged") or before != after:
        raise RuntimeError("Actual canonical state/source context does not pass")
    log = acquire(RUN / "canonical.log")
    log_text = log.decode("utf-8-sig").replace("\r\n", "\n")
    normalized_report = raw.decode("utf-8-sig").replace("\r\n", "\n").rstrip()
    if not log_text.rstrip().endswith(normalized_report): raise RuntimeError("Canonical log does not end with this exact normalized report")
    prefix = log_text.rstrip()[:-len(normalized_report)]
    prefix_lines = [line for line in prefix.splitlines() if line.strip()]
    if not all(line.startswith("PASS ") for line in prefix_lines): raise RuntimeError("Unexpected nonmetadata log prefix")
    put("canonical/canonical.log.gz", gzip.compress(log, compresslevel=9, mtime=0))
    gzip_originals["canonical/canonical.log.gz"] = digest(log)
    put("canonical/pass-markers.txt", ("\n".join(prefix_lines) + "\n").encode("utf-8"))
    summary_index_raw = acquire(SUMMARY / "INDEX.json")
    if digest(summary_index_raw)["sha256"] != SUMMARY_INDEX_SHA: raise RuntimeError("Frozen summary index differs")
    summary_index = json.loads(summary_index_raw)
    if summary_index["file_count"] != 5 or summary_index["total_bytes"] != 28995: raise RuntimeError("Frozen summary count differs")
    actual_summary = {p.relative_to(SUMMARY).as_posix() for p in SUMMARY.rglob("*") if p.is_file()}
    if actual_summary != set(summary_index["files"]) | {"INDEX.json"}: raise RuntimeError("Frozen summary membership differs")
    for name, expected in summary_index["files"].items():
        data = acquire(SUMMARY / name)
        if digest(data) != expected: raise RuntimeError("Frozen summary file differs")
        put("summary/" + name, data)
    put("summary/INDEX.json", summary_index_raw)
    put("recipe/stage_publication.py", acquire(Path(__file__)))
    if any(read(Path(path))[1] != expected for path, expected in initial.items()): raise RuntimeError("Metadata originals changed during staging")
    receipt = {"format": "studio_canonical_metadata_staging_1", "source_commit": COMMIT,
        "stage": "Awaiting root final receipt-audit and graphics-release paths; no final INDEX/README yet",
        "files": files, "file_count": len(files), "total_bytes": sum(row["bytes"] for row in files.values()),
        "gzip_originals": gzip_originals, "input_identities_preserved": initial, "source_before_after_files": len(before["source_sha256"]),
        "canonical_pass_marker_lines": len(prefix_lines), "raw_report_artifact_copied": False,
        "no_private_assets_media_or_runtime_included": True, "source_git_test_graphics_or_release_action": False}
    with (TASK / "STAGING_RECEIPT.json").open("x", encoding="utf-8") as stream: json.dump(receipt, stream, indent=2)
    print(json.dumps({key: receipt[key] for key in ("stage", "file_count", "total_bytes", "source_before_after_files", "canonical_pass_marker_lines")}))

if __name__ == "__main__": main()
