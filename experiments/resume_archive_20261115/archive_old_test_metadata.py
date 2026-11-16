"""Archive fixed historical test metadata; never changes inputs or removes files.

Only this packet directory is writable. No app, native converter, process query,
resource/handle probe, network call, Git mutation or cleanup is performed.
"""
from __future__ import annotations

import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


ROOT = Path(r"C:\a\Programming\cloudflare\has-acceptance-session-20261111")
PACKET = ROOT / "experiments/resume_archive_20261115"
SOURCE = ROOT / "output/source-choices-native-independent-cleanup-audit-20261114"
PINNED = {
    "core14-fresh-inventory.json": "846d0015644af0b8fca2eebed64c247dc6cee3a95c03240133ccd0c70fd9f20c",
    "wider11-fresh-inventory.json": "0d5fbd84a774958d53ac6d7f8f1065e319b0d6c8e1ab413a73febf31b73dee29",
    "FINAL_AUDIT.json": "1002daf4b501843091f3abd4ba8918365951903c048e0ba5cd5ed9136707c7c1",
    "GIT_RECOVERY_BATCH_PROOF.json": "0bce42ead2142ea1c49ce6655e0c9e0dcca5e3fc02133b6aadd538c93cf456bc",
    "retained-originals-fresh-proof.json": "80de0389dc4c2220b2ac6a3751f525bf001259810d27a2e799d169cd759e7f1c",
    "executable-dependency-scan.json": "bee893b54d35eb4f81d5f51affde7c0a5cbe372aa72f644b01b4748f27989699",
    "delete-access-readonly-proof.json": "55fda6fe83207abe1faa82b5e435951efde03afc57d1a423a34a3f4215c08bd9",
    "restart-manager-proof.json": "2506ba3e42b061bbc1aaf8af21cc3d8f875773ea690e46a68835e87446125e1e",
    "restart-manager-host-proof.json": "c25bc30143f190283f9aac2be9702846e9f353f56c00d31741755c7a9478d1a1",
    "restart-manager-extended-host-proof.json": "58901936bfef9b8b5ed8f4d57c6f7938b90395ce141cbf74976acbef584b1f29",
    "audit_readonly.py": "6565e7e442b3c2ff1297a781f2b136d39427b7f45303d3757c65da8a1edc438f",
    "git_recovery_batch_readonly.py": "3f8795c477d5737fbe72a3c5d827f0e4b5bf4202813ef6c464fd8c23ce8a4f15",
    "delete_access_readonly.py": "f1a13188aaa669daaafed6429cedb5bc19f0235a85e5e61cccd3e1772dc26ef3",
    "restart_manager_readonly.py": "fb0acb65e193c7e16a21b7b5e2a644e2197f354f9c561e9cbcb7b45018469b9d",
    "restart_manager_extended_readonly.py": "685236994ad08f24bfec13d90f201f16a2daf5bd9c264966ca78effc2e98eb4c",
    "REMOVAL_REVIEW_ONLY.ps1.txt": "90ea64fdc13523b1a03ffb67d942317887080cd7e57b0349496ffb6608919bed",
}
REPARSE = 0x400


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def clear_ancestors(path):
    for current in (path, *path.parents):
        value = current.lstat()
        need(not stat.S_ISLNK(value.st_mode) and not getattr(value, "st_file_attributes", 0) & REPARSE,
             "Reparse/symlink refused: " + str(current))


def stamp(value):
    return [value.st_size, value.st_mtime_ns, value.st_dev, value.st_ino,
            value.st_nlink, getattr(value, "st_file_attributes", 0)]


def read_stable(path):
    clear_ancestors(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
         "Regular single-link source required: " + str(path))
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read()
        closed = os.fstat(stream.fileno())
    after = path.lstat()
    need(all(stamp(row) == stamp(before) for row in (opened, closed, after)),
         "Source changed while read: " + str(path))
    return raw, stamp(before)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def save_json(path, value):
    clear_ancestors(path.parent)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, indent=2)
        stream.write("\n")


def main():
    need(Path.cwd().resolve() == ROOT and Path(__file__).resolve().parent == PACKET,
         "Exact session/packet paths required")
    clear_ancestors(PACKET)
    payload = PACKET / "historical-cleanup-audit"
    need(not payload.exists(), "Existing packet payload must never be overwritten")
    need(not (PACKET / "INDEX.json").exists(), "Existing index must never be overwritten")
    head = git("rev-parse", "HEAD").decode().strip()
    reachable = {}
    for line in git("rev-list", "--objects", "--all").decode().splitlines():
        if " " in line:
            oid, path = line.split(" ", 1)
            reachable.setdefault(oid, path)

    # Stage all fixed inputs in memory before writing any derived evidence.
    inputs = {}
    for name, expected in PINNED.items():
        raw, identity = read_stable(SOURCE / name)
        need(sha(raw) == expected, "Pinned historical input changed: " + name)
        if name.endswith(".json"):
            json.loads(raw)
        inputs[name] = (raw, identity)
    payload.mkdir(exist_ok=False)
    rows = []
    for name, (raw, identity) in inputs.items():
        compressed = name.endswith(".json")
        stored = gzip.compress(raw, mtime=0) if compressed else raw
        destination = payload / (name + ".gz" if compressed else name)
        with destination.open("xb") as stream:
            stream.write(stored)
        actual, _ = read_stable(destination)
        restored = gzip.decompress(actual) if compressed else actual
        need(actual == stored and restored == raw, "Stored round-trip differs: " + name)
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        rows.append({"source": (SOURCE / name).relative_to(ROOT).as_posix(),
                     "path": destination.relative_to(PACKET).as_posix(),
                     "encoding": "gzip" if compressed else "identity",
                     "raw_bytes": len(raw), "raw_sha256": sha(raw),
                     "stored_bytes": len(stored), "stored_sha256": sha(stored),
                     "source_stat_size_mtime_dev_ino_nlink_attrs": identity,
                     "exact_raw_git_blob_oid": oid,
                     "preexisting_reachable_exact_raw_blob": reachable.get(oid),
                     "decompression_exact": True})

    # Only metadata/source copies that already have byte-exact Git backups.
    old_packet = ROOT / "experiments/owner_pause_20261114/prepared-unrun"
    candidates = []
    for backup in sorted(old_packet.rglob("*")):
        if not backup.is_file():
            continue
        relative = backup.relative_to(old_packet)
        source = ROOT / "output" / relative
        if not source.is_file():
            continue
        before_raw, identity = read_stable(source)
        backup_raw, _ = read_stable(backup)
        indexed = git("show", head + ":" + backup.relative_to(ROOT).as_posix())
        need(before_raw == backup_raw == indexed, "Git-backed duplicate differs: " + str(relative))
        candidates.append({"literal_path": str(source),
                           "backing_path": backup.relative_to(ROOT).as_posix(),
                           "backing_commit": head, "bytes": len(before_raw),
                           "sha256": sha(before_raw),
                           "stat_size_mtime_dev_ino_nlink_attrs": identity,
                           "git_bytes_exact": True,
                           "nonuse": "UNESTABLISHED; root must check current recipe dependencies",
                           "cleanup_authorized": False})
    save_json(PACKET / "DUPLICATE_PUBLIC_PREPARATION_CANDIDATES.json", {
        "format": "has_duplicate_public_preparation_candidates_1", "plan_only": True,
        "files": candidates, "count": len(candidates),
        "bytes": sum(row["bytes"] for row in candidates),
        "recursive_removal_allowed": False, "cleanup_authorized": False,
        "scope": "Only these literal source/metadata duplicates; no private art or native run content",
        "required": "Fresh root dependency/nonuse evidence, exact file stamps/bytes/reparse/link checks, "
                    "remote retrieval verification, and a separate reviewed literal-file decision"})
    excluded = []
    for name in ("AUDIT.json", "process-reference-scan.json"):
        raw, _ = read_stable(SOURCE / name)
        excluded.append({"source": (SOURCE / name).relative_to(ROOT).as_posix(),
                         "bytes": len(raw), "sha256": sha(raw),
                         "reason": "Retained local; raw broader process/environment audit not needed for this compact packet"})
    need(git("rev-parse", "HEAD").decode().strip() == head, "HEAD changed during archive")
    save_json(PACKET / "INDEX.json", {
        "format": "has_resumed_old_test_metadata_archive_1",
        "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_head": head, "historical_audit_date": "2026-11-14",
        "files": rows, "raw_bytes": sum(row["raw_bytes"] for row in rows),
        "stored_bytes": sum(row["stored_bytes"] for row in rows),
        "exact_archived_payloads": len(rows), "excluded_local_only": excluded,
        "new_nonuse_or_resource_probe": False, "native_runtime_or_app_run": False,
        "historical_two_root_verdict": "RETAIN_FOR_NOW; no new deletion clearance",
        "old_two_roots": {"files": 9307, "bytes": 1442187088,
                          "full_qualification_and_final_review_remote_publication": "REQUIRED",
                          "exclusive_read_probe": "UNRUN"},
        "deletions": 0, "reclaimed_bytes": 0, "remote_upload_performed": False,
        "private_asset_payloads": 0,
        "restore": "Read the committed packet, decompress gzip members, verify raw_sha256, "
                   "then have root choose an explicit destination. Never execute historical recipes automatically.",
        "limitation": "Historical test/audit outcomes are preserved, not rerun or upgraded to current PASS."})
    print(json.dumps({"archived_payloads": len(rows), "raw_bytes": sum(row["raw_bytes"] for row in rows),
                      "stored_bytes": sum(row["stored_bytes"] for row in rows),
                      "duplicate_candidates": len(candidates),
                      "duplicate_candidate_bytes": sum(row["bytes"] for row in candidates),
                      "deletions": 0, "reclaimed_bytes": 0}, indent=2))


if __name__ == "__main__":
    main()
