"""Read-only exact-copy plan. Contains no cleanup, process or runtime launcher."""
from pathlib import Path, PureWindowsPath
import hashlib
import json
import os
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
COMMIT = "12071fe182a17d17e2a1547c7dbb97f6aa4dd160"
PAIRS = (
    ("output/has-snapshot-ordering-candidate-20261113/publication-candidate", "experiments/has_snapshot_ordering/candidate_20261113"),
    ("output/source_currentdir_race_20261113/publication-candidate", "experiments/has_snapshot_ordering/cwd_probe_20261113"),
    ("output/sfm-static-choice-main-candidate-20261113/publication-candidate", "experiments/source_appearance/static_choice_draft_20261113"),
)
REPARSE = 0x400
ALLOW = {".py", ".gd", ".md", ".json", ".patch", ".txt"}
FORBIDDEN_PARTS = {".godot", "project", "authored", "fixtures", "stage", "runtimes", "dependencies", "recovery"}

def digest(raw): return hashlib.sha256(raw).hexdigest()

def safe_relative(value):
    return isinstance(value, str) and not PureWindowsPath(value).drive and not value.startswith(("/", "\\")) and all(part not in {"", ".", ".."} and ":" not in part for part in value.replace("\\", "/").split("/"))

def components(path):
    path = path.absolute()
    result = []
    while True:
        result.append(path)
        if path.parent == path: return list(reversed(result))
        path = path.parent

def guard(path, boundary):
    path = path.absolute(); boundary = boundary.absolute()
    if not path.is_relative_to(boundary): raise RuntimeError("Path escapes its literal packet boundary")
    rows = {}
    for component in components(path):
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_file_attributes & REPARSE:
            raise RuntimeError("Reparse path refused: " + str(component))
        rows[str(component)] = {"device": info.st_dev, "inode": info.st_ino,
            "attributes": info.st_file_attributes, "kind": "directory" if stat.S_ISDIR(info.st_mode) else "file"}
    if not path.is_file(): raise RuntimeError("Expected a regular packet file")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError("Nonregular or multiply linked packet copy refused")
    return rows

def identity(path):
    info = path.stat(); raw = path.read_bytes()
    after = path.stat()
    if (info.st_size, info.st_mtime_ns, info.st_ino, info.st_dev) != (after.st_size, after.st_mtime_ns, after.st_ino, after.st_dev):
        raise RuntimeError("File changed during plan read")
    return {"sha256": digest(raw), "bytes": len(raw), "mtime_ns": after.st_mtime_ns,
            "device": after.st_dev, "inode": after.st_ino, "links": after.st_nlink}

def main():
    if (OUT / "PLAN.json").exists(): raise RuntimeError("Plan output already exists; preserve it")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != COMMIT: raise RuntimeError("Expected frozen committed base")
    remote = subprocess.check_output(["git", "rev-parse", "refs/remotes/origin/main"], cwd=ROOT, text=True).strip()
    # Read Git's object database only. No fetch/index/worktree write occurs.
    raw_tree = subprocess.check_output(["git", "ls-tree", "-r", "-z", "--long", COMMIT, "--", *[right for _, right in PAIRS]], cwd=ROOT)
    tree = {}
    for item in raw_tree.split(b"\0"):
        if not item: continue
        header, name = item.split(b"\t", 1)
        mode, kind, oid, size = header.decode("ascii").split()
        if kind != "blob" or mode != "100644": raise RuntimeError("Nonordinary committed packet entry")
        tree[name.decode("utf-8")] = {"mode": mode, "blob_sha1": oid, "bytes": int(size)}
    admitted = []; excluded = []; initial = {}; guards = {}; packet_rows = []
    for source_name, backup_name in PAIRS:
        source_root = ROOT / source_name; backup_root = ROOT / backup_name
        index_path = source_root / "FILE_INDEX.json"
        index = json.loads(index_path.read_bytes())
        listed = {**index["files"], "FILE_INDEX.json": {"sha256": digest(index_path.read_bytes()), "bytes": index_path.stat().st_size}}
        actual = {path.relative_to(source_root).as_posix() for path in source_root.rglob("*") if path.is_file()}
        if actual != set(listed): raise RuntimeError("Publication copy has missing/extra files")
        packet_rows.append({"source_root": str(source_root), "committed_backup_root": backup_name,
                            "publication_copy_files": len(listed), "publication_copy_bytes": sum(row["bytes"] for row in listed.values())})
        seen = set()
        for relative, expected in listed.items():
            if not safe_relative(relative) or relative.casefold() in seen: raise RuntimeError("Unsafe or duplicate indexed path")
            seen.add(relative.casefold())
            source = source_root / relative; backup = backup_root / relative
            guards.update(guard(source, source_root)); guards.update(guard(backup, backup_root))
            source_stamp = identity(source); backup_stamp = identity(backup)
            initial[str(source)] = source_stamp; initial[str(backup)] = backup_stamp
            if any(source_stamp[key] != expected[key] or backup_stamp[key] != expected[key] for key in ("sha256", "bytes")):
                raise RuntimeError("Publication-copy byte identity differs: " + relative)
            git_path = backup.relative_to(ROOT).as_posix()
            if git_path not in tree or tree[git_path]["bytes"] != source_stamp["bytes"]:
                raise RuntimeError("Exact backup is absent from the committed tree")
            reason = None
            if any(part.casefold() in FORBIDDEN_PARTS for part in Path(relative).parts): reason = "Retain fixture/runtime/project/recovery path"
            elif relative.lower().endswith((".log", ".log.gz")): reason = "Retain every full log copy conservatively, even when backed by Git"
            elif source.suffix.lower() not in ALLOW and not relative.lower().endswith(".json.gz"): reason = "Outside source/metadata allowlist"
            row = {"source": str(source), "source_relative": source.relative_to(ROOT).as_posix(),
                   "backup_relative": git_path, "backup": str(backup), "sha256": source_stamp["sha256"], "bytes": source_stamp["bytes"],
                   "source_identity": source_stamp, "backup_identity": backup_stamp, **tree[git_path]}
            if reason:
                excluded.append({**row, "reason": reason})
            else: admitted.append(row)
    # Validate ALL plan/retained-copy pairs against exact committed blob bytes
    # through one read-only batch process, rather than trusting current worktree.
    all_rows = admitted + excluded
    batch_input = "".join(row["blob_sha1"] + "\n" for row in all_rows).encode("ascii")
    blobs = subprocess.run(["git", "cat-file", "--batch"], input=batch_input, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    cursor = 0
    for row in all_rows:
        end = blobs.index(b"\n", cursor); header = blobs[cursor:end].decode("ascii").split(); cursor = end + 1
        if header != [row["blob_sha1"], "blob", str(row["bytes"])]: raise RuntimeError("Unexpected Git blob response")
        raw = blobs[cursor:cursor + row["bytes"]]; cursor += row["bytes"]
        if blobs[cursor:cursor+1] != b"\n": raise RuntimeError("Bad Git blob boundary")
        cursor += 1
        if digest(raw) != row["sha256"]: raise RuntimeError("Committed blob SHA256 differs")
        row["git_blob_sha256_verified"] = True
    if cursor != len(blobs): raise RuntimeError("Unexpected trailing Git batch bytes")
    if any(identity(Path(path)) != before for path, before in initial.items()): raise RuntimeError("Packet file changed during plan")
    for path, expected in guards.items():
        component = Path(path); info = component.lstat()
        actual = {"device": info.st_dev, "inode": info.st_ino, "attributes": info.st_file_attributes,
                  "kind": "directory" if stat.S_ISDIR(info.st_mode) else "file"}
        if actual != expected or info.st_file_attributes & REPARSE or stat.S_ISLNK(info.st_mode): raise RuntimeError("Path guard changed")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != head:
        raise RuntimeError("HEAD changed during plan")
    result = {"format": "studio_exact_publication_copy_cleanup_plan_1", "plan_only": True, "deletion_performed": False,
        "repository": str(ROOT), "committed_backup": COMMIT, "head_before_after": head,
        "cached_origin_main": remote, "remote_verification": "Root reported push/fetch/ls-remote verification; this plan performs no network request",
        "packets": packet_rows, "candidate_count": len(admitted), "candidate_bytes": sum(row["bytes"] for row in admitted),
        "excluded_count": len(excluded), "excluded_bytes": sum(row["bytes"] for row in excluded),
        "candidates": admitted, "excluded_retained": excluded, "component_no_reparse_guard": guards,
        "all_files_exact_and_preserved": True, "all_git_blob_sha256_verified": True,
        "scope": "Only literal per-file publication copies below these three source roots; no recursive cleanup or directory removal",
        "future_requirement": "Root must independently revalidate exact bytes/stamps/containment/no-reparse and current process use before any separately authorized nonrecursive per-file cleanup",
        "forbidden": ["No process scan, kill or test", "No old SFM cleanup executor", "No runtime/.godot/project/fixture/native input/review/recovery/coordinator removal", "No raw full-log removal", "No Git mutation"]}
    (OUT / "PLAN.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_count": result["candidate_count"], "candidate_bytes": result["candidate_bytes"],
                      "excluded_count": result["excluded_count"], "excluded_bytes": result["excluded_bytes"],
                      "committed_backup": COMMIT, "cached_origin_main": remote, "all_files_exact_and_preserved": True}))

if __name__ == "__main__": main()
