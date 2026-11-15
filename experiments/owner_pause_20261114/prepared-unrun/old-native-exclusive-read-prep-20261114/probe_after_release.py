"""UNRUN read-only sharing probe for exactly two historical native test roots.

Root may run this only after the full suite, final review and publication close.
No candidate file is written, deleted, renamed or given delete/write access.
Each GENERIC_READ/share-zero handle is closed before the next file is opened.
This is bounded sharing evidence, never a deletion authorization or reservation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time


ROOT = Path(r"C:\a\Programming\cloudflare\has-acceptance-session-20261111")
HERE = ROOT/"output/old-native-exclusive-read-prep-20261114"
AUDIT = ROOT/"output/source-choices-native-independent-cleanup-audit-20261114"
EXPECTED = (
    ("core14", ROOT/"output/source-choices-native/1794615194930984000-ae0e0967",
     "core14-fresh-inventory.json", 1699274, "846d0015644af0b8fca2eebed64c247dc6cee3a95c03240133ccd0c70fd9f20c", 4707, 791, 387640663),
    ("wider11", ROOT/"output/source-choices-native/1794615438168999800-42f0686d",
     "wider11-fresh-inventory.json", 1659153, "0d5fbd84a774958d53ac6d7f8f1065e319b0d6c8e1ab413a73febf31b73dee29", 4600, 746, 1054546425),
)
REPARSE = 0x400


def need(ok, detail):
    if not ok:
        raise RuntimeError(detail)


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, indent=2)
        stream.write("\n")


def ancestors_clear(path):
    need(path.is_absolute(), "Absolute local path required")
    for current in (path, *path.parents):
        row = current.lstat()
        need(not stat.S_ISLNK(row.st_mode) and not getattr(row, "st_file_attributes", 0)&REPARSE,
             "Reparse/symlink refused: "+str(current))


def stamp(row):
    return (row.st_size, row.st_mtime_ns, row.st_ino, row.st_dev, row.st_nlink,
            getattr(row, "st_file_attributes", 0))


def digest_file(path):
    ancestors_clear(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "Regular single-link file required: "+str(path))
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        value = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    final = path.lstat()
    need(all(stamp(row) == stamp(before) for row in (opened, after, final)), "File changed while hashed: "+str(path))
    return {"bytes": before.st_size, "mtime_ns": before.st_mtime_ns, "sha256": value,
            "hardlinks": before.st_nlink, "stat_device": before.st_dev, "stat_inode": before.st_ino}


def safe_relative(name):
    path = PurePosixPath(name)
    need(isinstance(name, str) and name and not path.is_absolute() and not any(c in name for c in ("\\", ":", "\0")),
         "Unsafe inventory name")
    need(all(part not in ("", ".", "..") and part == part.rstrip(" .") and
             not any(ord(c) < 32 for c in part) for part in path.parts), "Unsafe inventory component")
    need(path.as_posix() == name, "Noncanonical inventory name")
    return path


def references():
    result = []
    for phase, base, filename, size, sha, files, dirs, total in EXPECTED:
        path = AUDIT/filename
        raw = path.read_bytes()
        need(len(raw) == size and hashlib.sha256(raw).hexdigest() == sha, "Frozen independent inventory differs")
        parsed = json.loads(raw)
        need(Path(parsed["absolute_root"]) == base and parsed.get("reparse_points") == [], "Inventory root/reparse mismatch")
        rows = parsed["files"]
        need(len(rows) == files and len(parsed["directories"]) == dirs and
             sum(row["bytes"] for row in rows) == total, "Exact old inventory count/size required")
        names = [row["path"] for row in rows]
        for name in names+parsed["directories"]:
            safe_relative(name)
        need(len(set(names)) == files and len(set(parsed["directories"])) == dirs and
             not set(names)&set(parsed["directories"]), "Duplicate or mixed-kind inventory path")
        need(all(row["hardlinks"] == 1 for row in rows), "Historical hardlink refused")
        result.append({"phase": phase, "root": base, "files": {row["path"]: row for row in rows},
                       "directories": set(parsed["directories"]), "reference": {"path": str(path), "bytes": size, "sha256": sha}})
    need(sum(len(row["files"]) for row in result) == 9307, "Exact9307-file scope required")
    return result


def inventory(reference):
    base = reference["root"]
    need(base.parent == ROOT/"output/source-choices-native", "Exact literal old-run boundary required")
    ancestors_clear(base)
    need(base.resolve(strict=True) == base, "Resolved old-run root differs")
    files = {}
    directories = {}
    pending = [base]
    while pending:
        directory = pending.pop()
        before = directory.lstat()
        need(stat.S_ISDIR(before.st_mode) and not getattr(before, "st_file_attributes", 0)&REPARSE, "Directory changed/reparse refused")
        relative_dir = directory.relative_to(base).as_posix()
        directories[relative_dir] = {"mtime_ns": before.st_mtime_ns, "stat_device": before.st_dev, "stat_inode": before.st_ino}
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                current = entry.stat(follow_symlinks=False)
                need(not stat.S_ISLNK(current.st_mode) and not getattr(current, "st_file_attributes", 0)&REPARSE,
                     "Reparse entry refused: "+str(path))
                name = path.relative_to(base).as_posix()
                if stat.S_ISDIR(current.st_mode):
                    need(name in reference["directories"], "Unexpected directory: "+name)
                    pending.append(path)
                else:
                    need(stat.S_ISREG(current.st_mode) and name in reference["files"], "Unexpected file/kind: "+name)
                    actual = digest_file(path)
                    expected = reference["files"][name]
                    need(all(actual[key] == expected[key] for key in ("bytes", "mtime_ns", "sha256", "hardlinks")),
                         "Historical file identity differs: "+name)
                    files[name] = actual
        need(directory.lstat().st_mtime_ns == before.st_mtime_ns, "Directory membership changed while inventoried")
    need(set(files) == set(reference["files"]) and set(directories)-{"."} == reference["directories"], "Incomplete root inventory")
    return {"files": files, "directories_including_root": directories}


def windows_probe():
    # Deliberately deferred: importing this source does not load a Windows DLL.
    import ctypes
    import ctypes.wintypes as W

    class Info(ctypes.Structure):
        _fields_ = [("attrs", W.DWORD), ("ctime", W.FILETIME), ("atime", W.FILETIME), ("mtime", W.FILETIME),
                    ("volume", W.DWORD), ("sizehi", W.DWORD), ("sizelo", W.DWORD), ("links", W.DWORD),
                    ("indexhi", W.DWORD), ("indexlo", W.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.POINTER(Info)]
    kernel.GetFileInformationByHandle.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    invalid = ctypes.c_void_p(-1).value

    def probe(path, expected):
        ancestors_clear(path)
        start = time.time_ns()
        handle = kernel.CreateFileW("\\\\?\\"+str(path), 0x80000000, 0, None, 3, 0x00200000, None)
        if handle == invalid:
            return {"opened": False, "winerror": ctypes.get_last_error(), "started_ns": start, "finished_ns": time.time_ns()}
        result = {"opened": True, "started_ns": start}
        try:
            info = Info()
            if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
                result["information_error"] = ctypes.get_last_error()
            else:
                observed = {"bytes": (int(info.sizehi)<<32)|int(info.sizelo),
                            "mtime_ns": (((int(info.mtime.dwHighDateTime)<<32)|int(info.mtime.dwLowDateTime))-116444736000000000)*100,
                            "hardlinks": int(info.links), "device": int(info.volume),
                            "file_index": (int(info.indexhi)<<32)|int(info.indexlo)}
                result["identity_equal"] = all(observed[key] == expected[key] for key in observed)
                result["regular_no_reparse"] = not int(info.attrs)&(REPARSE|0x10|0x40)
                result["identity"] = observed
        finally:
            # No file reads or waits occur while the exclusive handle is held.
            closed = bool(kernel.CloseHandle(handle))
            result["closed"] = closed
            if not closed:
                result["close_error"] = ctypes.get_last_error()
            result["finished_ns"] = time.time_ns()
        return result

    return probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-full-and-final-review-closed", action="store_true", required=True)
    parser.add_argument("--root-release-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(os.name == "nt", "Windows only; no fallback")
    release_path = args.root_release_evidence.absolute()
    ancestors_clear(release_path)
    release_raw = release_path.read_bytes()
    need(len(release_raw) <= 1024*1024, "Bounded root release required")
    release = json.loads(release_raw)
    need(release.get("format") == "has_old_native_exclusive_probe_root_release_1" and
         all(release.get(key) is True for key in ("root_approved_readonly_probe", "full_terminal_passed",
             "final_review_runtime_closed", "publication_remote_verified", "current_source_preserved")),
         "Root must first establish full/final-review/publication closure; this script does not infer it")
    need(release.get("literal_roots") == [str(row[1]) for row in EXPECTED], "Release scope differs")
    output = args.output.absolute()
    need(output.parent == ROOT/"output" and re.fullmatch(r"old-native-exclusive-read-[A-Za-z0-9_]+", output.name) and
         not output.exists(), "New direct output child required")
    ancestors_clear(output.parent)
    pinned = references()
    output.mkdir(exist_ok=False)
    save(output/"root-release.json", release)
    results = []
    errors = []
    before = {}
    after = {}
    started = utc()
    try:
        for reference in pinned:
            before[reference["phase"]] = inventory(reference)
        save(output/"inventory-before.json", before)
        probe = windows_probe()
        for reference in pinned:
            phase = reference["phase"]
            for name, expected in sorted(reference["files"].items()):
                result = probe(reference["root"]/name, expected)
                results.append({"phase": phase, "path": name, **result})
                if result.get("closed") is False:
                    raise RuntimeError("CloseHandle failed; stop immediately and retain output")
    except BaseException as exc:
        errors.append({"phase": "inventory_or_exclusive_probe", "type": type(exc).__name__, "detail": str(exc)})
    finally:
        for reference in pinned:
            try:
                after[reference["phase"]] = inventory(reference)
            except BaseException as exc:
                errors.append({"phase": "after_"+reference["phase"], "type": type(exc).__name__, "detail": str(exc)})
        try:
            references()
            need(release_path.read_bytes() == release_raw, "Root release changed")
        except BaseException as exc:
            errors.append({"phase": "pinned_evidence_after", "type": type(exc).__name__, "detail": str(exc)})
        save(output/"inventory-after.json", after)
        save(output/"exclusive-open-results.json", results)
        successful = [row for row in results if row.get("opened") is True and row.get("closed") is True and
                      row.get("identity_equal") is True and row.get("regular_no_reparse") is True and "information_error" not in row]
        preserved = before == after and set(before) == {row[0] for row in EXPECTED}
        report = {"format": "has_old_native_exclusive_read_evidence_1", "started_utc": started, "finished_utc": utc(),
                  "passed": not errors and preserved and len(results) == len(successful) == 9307,
                  "files_expected": 9307, "files_attempted": len(results), "files_exclusively_opened_closed_verified": len(successful),
                  "literal_roots": [str(row[1]) for row in EXPECTED], "inventories_before_after_identical": preserved,
                  "root_release_sha256": hashlib.sha256(release_raw).hexdigest(),
                  "reference_inventories": [row["reference"] for row in pinned], "errors": errors,
                  "windows_request": {"desired_access": "GENERIC_READ(0x80000000)", "share_mode": 0,
                      "disposition": "OPEN_EXISTING(3)", "flags": "FILE_FLAG_OPEN_REPARSE_POINT(0x00200000)",
                      "security_attributes": None, "template_handle": None},
                  "candidate_writes_or_deletions": False, "delete_or_write_access_requested": False,
                  "runtime_or_control_process_launched": False, "cleanup_authorized": False,
                  "limitations": "Sequential immediate-close read-sharing observations only. No all-files simultaneous lock, later reservation, process identity census, metadata-only handle exclusion, mapped-view exclusion, directory open exclusion or deletion access proof. Root must retain prior closure/dependency/preservation evidence and decide any later literal removal separately."}
        save(output/"verification.json", report)
        print(json.dumps({key: report[key] for key in ("passed", "files_attempted", "files_exclusively_opened_closed_verified", "cleanup_authorized")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
