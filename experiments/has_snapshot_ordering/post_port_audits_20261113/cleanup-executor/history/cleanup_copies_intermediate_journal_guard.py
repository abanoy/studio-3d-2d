"""Exact-file cleanup proposal. Default is read-only; no recursive operation exists."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import stat
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PLAN = ROOT / "output/save-order-safe-cleanup-plan-20261113/PLAN.json"
PLAN_SHA = "00c8ecafaa93c5dc92256e31cfb2841f347dbd84896da516bc1e3fe56400fa24"
REMOTE = ROOT / "output/has-snapshot-launch-remote-verified.json"
REMOTE_SHA = "49b9d8cfa66e610105111ee81621fdaa95481bcab0d62474152bec59a083ceb6"
COMMIT = "12071fe182a17d17e2a1547c7dbb97f6aa4dd160"
PAIRS = (
    ("output/has-snapshot-ordering-candidate-20261113/publication-candidate", "experiments/has_snapshot_ordering/candidate_20261113"),
    ("output/source_currentdir_race_20261113/publication-candidate", "experiments/has_snapshot_ordering/cwd_probe_20261113"),
    ("output/sfm-static-choice-main-candidate-20261113/publication-candidate", "experiments/source_appearance/static_choice_draft_20261113"),
)

def require(value, message):
    if not value: raise RuntimeError(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def raw_file(path, limit=2 * 1024 * 1024):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and not before.st_file_attributes & 0x400 and before.st_nlink == 1 and before.st_size <= limit, "Nonregular/reparse/linked/oversize file")
    with path.open("rb") as stream: raw = stream.read(limit + 1)
    after = path.lstat()
    require((before.st_size, before.st_mtime_ns, before.st_dev, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_dev, after.st_ino) and len(raw) == before.st_size, "File changed while reading")
    return raw

def json_file(path, expected_sha):
    raw = raw_file(path)
    require(sha(raw) == expected_sha, "Metadata fingerprint differs: " + str(path))
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key"); result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)

def file_identity(path):
    raw = raw_file(path); info = path.lstat()
    return {"sha256": sha(raw), "bytes": len(raw), "mtime_ns": info.st_mtime_ns,
            "device": info.st_dev, "inode": info.st_ino, "links": info.st_nlink}

def ancestors(path):
    while True:
        yield path
        if path.parent == path: break
        path = path.parent

def guard(path, boundary, plan, missing=False):
    require(path.is_absolute() and path.is_relative_to(boundary) and path == Path(str(path)), "Nonliteral or escaped absolute path")
    for part in ancestors(path.parent if missing else path):
        info = part.lstat(); expected = plan["component_no_reparse_guard"].get(str(part))
        require(expected is not None and not stat.S_ISLNK(info.st_mode) and not info.st_file_attributes & 0x400, "Unlisted/reparse component")
        actual = {"device": info.st_dev, "inode": info.st_ino, "attributes": info.st_file_attributes, "kind": "directory" if stat.S_ISDIR(info.st_mode) else "file"}
        require(actual == expected, "Path component identity changed: " + str(part))
    if not missing: require(path.resolve(strict=True) == path, "Resolved path differs")

def pair_for(row):
    source = Path(row["source"]); backup = Path(row["backup"])
    for left, right in PAIRS:
        a, b = ROOT / left, ROOT / right
        if source.is_relative_to(a):
            require(backup == b / source.relative_to(a) and row["backup_relative"] == backup.relative_to(ROOT).as_posix(), "Source/backup pairing differs")
            return source, backup, a, b
    raise RuntimeError("Candidate is outside all three literal roots")

def verify_row(row, plan, deleted=False):
    source, backup, a, b = pair_for(row)
    require(not source.name.lower().endswith((".log", ".log.gz")), "A full log cannot be deleted")
    guard(backup, b, plan); require(file_identity(backup) == row["backup_identity"], "Backup changed")
    blob = subprocess.run(["git", "cat-file", "blob", row["blob_sha1"]], cwd=ROOT, capture_output=True, check=True, timeout=15).stdout
    require(len(blob) == row["bytes"] and sha(blob) == row["sha256"], "Committed Git blob differs")
    if deleted:
        guard(source, a, plan, missing=True); require(not os.path.lexists(source), "A journalled removed path reappeared")
    else:
        guard(source, a, plan); require(file_identity(source) == row["source_identity"], "Source copy changed")

def aware(text):
    value = datetime.fromisoformat(text)
    require(value.tzinfo is not None, "Naive authority timestamp refused")
    return value.astimezone(timezone.utc)

def authority(args, self_sha):
    require(all((args.review, args.review_sha256, args.process_proof, args.process_proof_sha256)), "Execution requires hash-bound reviewed-source receipt and fresh authoritative process proof")
    review = json_file(args.review, args.review_sha256)
    require(review.get("format") == "studio_publication_copy_cleanup_review_1" and review.get("executor_sha256") == self_sha and review.get("plan_sha256") == PLAN_SHA and review.get("unresolved_findings") == [], "Reviewed-source approval differs")
    proof = json_file(args.process_proof, args.process_proof_sha256)
    require(proof.get("format") == "has_relocated_review_authoritative_host_termination_1" and proof.get("review_source_commit") == COMMIT, "Wrong authoritative proof scope")
    require(proof.get("coordinator_absent") is True and proof.get("owned_runtime_command_matches_absent") is True and proof.get("owned_matches") == [] and proof.get("no_process_killed") is True, "Owned-runtime absence was not established")
    require("Authoritative Windows host CIM" in proof.get("query", ""), "Wrong query provenance")
    observed = aware(proof["observed_utc"]); age = (datetime.now(timezone.utc) - observed).total_seconds()
    require(observed >= aware(review["reviewed_utc"]) and -5 <= age <= 300, "Proof must be after review and no older than five minutes")

def append(journal, record):
    require(journal.is_absolute() and journal.is_relative_to(TASK / "attempts"), "Journal escaped owned output")
    for part in ancestors(journal): require(not part.lstat().st_file_attributes & 0x400 and not part.is_symlink(), "Reparse journal component")
    require(journal.lstat().st_nlink == 1, "Linked journal refused")
    with journal.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n"); stream.flush(); os.fsync(stream.fileno())

def progress(journal, rows, self_sha):
    require(journal.is_absolute() and journal.is_relative_to(TASK / "attempts"), "Resume journal must be in this executor's owned attempts folder")
    require(journal.resolve(strict=True) == journal, "Resume journal must be a resolved literal absolute path")
    for part in ancestors(journal): require(not part.lstat().st_file_attributes & 0x400 and not part.is_symlink(), "Reparse journal path")
    records = [json.loads(line) for line in raw_file(journal).decode("utf-8").splitlines()]
    require(records and records[0] == {"phase": "header", "plan_sha256": PLAN_SHA, "executor_sha256": self_sha}, "Journal belongs to different plan/source")
    done = set(); pending = None
    for record in records[1:]:
        phase = record.get("phase")
        if phase == "authority": continue
        if phase == "before":
            require(pending is None and record["index"] == len(done) and record["source"] == rows[record["index"]]["source"], "Journal is not an ordered prefix")
            pending = record["index"]
        elif phase == "after":
            require(pending is not None and type(record["index"]) is int and record["index"] == pending and record["removed"] is True and record["backup_exact"] is True, "Ambiguous/failed unlink journal")
            done.add(pending); pending = None
        else: raise RuntimeError("Failure/unknown journal entry requires independent manual reconciliation")
    require(pending is None, "Incomplete before/after pair: refuse ambiguous partial retry")
    return done

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--review", type=Path); parser.add_argument("--review-sha256")
    parser.add_argument("--process-proof", type=Path); parser.add_argument("--process-proof-sha256")
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args(); self_sha = sha(Path(__file__).read_bytes())
    plan = json_file(PLAN, PLAN_SHA); remote = json_file(REMOTE, REMOTE_SHA)
    require(plan["repository"] == str(ROOT) and plan["candidate_count"] == 88 and plan["candidate_bytes"] == 498427 and plan["committed_backup"] == COMMIT, "Frozen plan scope differs")
    require(all(remote.get(key) == COMMIT for key in ("expected", "ls_remote", "fetched")) and remote.get("raw_bytes_without_strip") is True, "Saved remote verification differs")
    rows = plan["candidates"]; require(len(rows) == 88 and sum(r["bytes"] for r in rows) == 498427 and len({r["source"] for r in rows}) == 88, "Frozen row cardinality differs")
    require(not args.resume or args.execute, "Resume is execution-only")
    done = progress(args.resume, rows, self_sha) if args.resume else set()
    tree = subprocess.run(["git", "ls-tree", "-r", "-z", COMMIT, "--", *[b for _, b in PAIRS]], cwd=ROOT, capture_output=True, check=True, timeout=15).stdout
    entries = {}
    for item in tree.split(b"\0"):
        if item:
            header, name = item.split(b"\t", 1); entries[name.decode()] = header.decode().split()
    for row in rows + plan["excluded_retained"]:
        require(entries.get(row["backup_relative"]) == ["100644", "blob", row["blob_sha1"]], "Backup Git path/blob binding differs")
        if row in rows: verify_row(row, plan, rows.index(row) in done)
        else:
            # Retained logs are verified too; never route them to unlink.
            source, backup, a, b = pair_for(row)
            guard(source, a, plan); guard(backup, b, plan)
            require(file_identity(source) == row["source_identity"] and file_identity(backup) == row["backup_identity"], "Retained log/backup changed")
    if not args.execute:
        target = TASK / ("DRY_RUN_" + str(time.time_ns()) + ".json")
        with target.open("x", encoding="utf-8") as stream: json.dump({"plan_sha256": PLAN_SHA, "executor_sha256": self_sha, "candidate_count": 88, "candidate_bytes": 498427, "retained_logs": 18, "all_file_and_git_guards_passed": True, "deletions": 0, "process_scans": 0}, stream, indent=2)
        print(str(target)); return
    authority(args, self_sha)
    if args.resume: journal = args.resume
    else:
        for part in ancestors(TASK): require(not part.lstat().st_file_attributes & 0x400 and not part.is_symlink(), "Reparse executor output parent")
        attempts = TASK / "attempts"
        if not attempts.exists(): attempts.mkdir()
        require(attempts.is_dir() and not attempts.is_symlink() and not attempts.lstat().st_file_attributes & 0x400, "Unsafe attempts folder")
        folder = attempts / (str(time.time_ns()) + "-" + uuid.uuid4().hex[:8]); folder.mkdir(exist_ok=False)
        journal = folder / "journal.jsonl"
        with journal.open("x", encoding="utf-8") as stream: pass
        append(journal, {"phase": "header", "plan_sha256": PLAN_SHA, "executor_sha256": self_sha})
    append(journal, {"phase": "authority", "review_sha256": args.review_sha256, "process_proof_sha256": args.process_proof_sha256})
    for index, row in enumerate(rows):
        if index in done: continue
        authority(args, self_sha); require(sha(Path(__file__).read_bytes()) == self_sha, "Executor source changed")
        verify_row(row, plan)
        append(journal, {"phase": "before", "index": index, "source": row["source"], "sha256": row["sha256"], "bytes": row["bytes"]})
        try:
            verify_row(row, plan)
            source, backup, _, b = pair_for(row)
            source.unlink()  # The sole removal call: one fully checked literal file.
            removed = not os.path.lexists(source)
            guard(backup, b, plan); backup_exact = file_identity(backup) == row["backup_identity"]
            append(journal, {"phase": "after", "index": index, "removed": removed, "backup_exact": backup_exact})
            require(removed and backup_exact, "Unlink postcondition failed")
        except Exception as error:
            append(journal, {"phase": "failure", "index": index, "error": str(error)})
            raise
    print(json.dumps({"removed": len(rows), "bytes": sum(r["bytes"] for r in rows), "journal": str(journal), "recursive_operation": False}))

if __name__ == "__main__": main()
