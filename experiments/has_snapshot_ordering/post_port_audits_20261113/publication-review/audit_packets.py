"""Read-only packet byte/content audit; never imports or executes packet code."""
from pathlib import Path, PureWindowsPath
import gzip
import hashlib
import io
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PACKETS = ["experiments/has_snapshot_ordering/" + name for name in (
    "canonical_failure_20261113", "candidate_20261113", "cwd_probe_20261113", "main_actual_20261113")]
PACKETS += ["experiments/source_appearance/static_choice_draft_20261113", "experiments/owner_review/relocatable_prep_20261113"]
ALLOWED = {".py", ".gd", ".json", ".md", ".txt", ".patch", ".log", ".gz"}

def stamp(path):
    stat = path.stat(); raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": stat.st_mtime_ns}

def safe_relative(name):
    return isinstance(name, str) and not PureWindowsPath(name).drive and not name.startswith(("/", "\\")) and not any(part in {"", ".", ".."} or ":" in part for part in name.replace("\\", "/").split("/"))

def indexed(root, path):
    data = json.loads(path.read_bytes()); files = data.get("files", {}); errors = []
    if not isinstance(files, dict): return {"error": "index files is not a mapping"}
    names = set(); total = 0; originals = []
    for name, expected in files.items():
        if not safe_relative(name): errors.append({"name": name, "error": "unsafe indexed path"}); continue
        key = name.casefold()
        if key in names: errors.append({"name": name, "error": "casefold duplicate"})
        names.add(key)
        target = root / name
        if not target.is_file(): errors.append({"name": name, "error": "missing"}); continue
        actual = stamp(target); total += actual["bytes"]
        for field in ("sha256", "bytes"):
            if expected.get(field) != actual[field]: errors.append({"name": name, "field": field, "expected": expected.get(field), "actual": actual[field]})
        if "original" in expected:
            if target.suffix == ".gz":
                with gzip.GzipFile(fileobj=io.BytesIO(target.read_bytes())) as stream: raw = stream.read(16 * 1024 * 1024 + 1)
            else: raw = target.read_bytes()
            original = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            if expected["original"] != original: errors.append({"name": name, "error": "original receipt differs"})
            originals.append(name)
    actual_names = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != path}
    # A nested index can intentionally cover a subset; only top-level packet
    # admission uses this extras check.
    extras = sorted(actual_names - set(files))
    count_fields = {k: data[k] for k in ("file_count", "files_count", "count") if k in data}
    byte_fields = {k: data[k] for k in ("total_bytes", "bytes") if isinstance(data.get(k), int)}
    for key, value in count_fields.items():
        if value != len(files): errors.append({"field": key, "expected": value, "actual": len(files)})
    for key, value in byte_fields.items():
        if value != total: errors.append({"field": key, "expected": value, "actual": total})
    return {"index": path.relative_to(ROOT).as_posix(), "index_identity": stamp(path), "format": data.get("format"),
            "indexed_files": len(files), "indexed_bytes": total, "declared_counts": count_fields, "declared_bytes": byte_fields,
            "errors": errors, "unindexed_files": extras, "original_receipts_checked": originals}

def main():
    before = {}; reports = []
    for relative in PACKETS:
        root = ROOT / relative
        paths = sorted(p for p in root.rglob("*") if p.is_file())
        if any(p.is_symlink() or p.stat().st_file_attributes & 0x400 for p in root.rglob("*")):
            raise RuntimeError("Reparse packet entry")
        before.update({str(path): stamp(path) for path in paths})
        index = root / ("INDEX.json" if (root / "INDEX.json").is_file() else "FILE_INDEX.json")
        report = indexed(root, index); content_errors = []; types = {}; decoded_count = 0
        for path in paths:
            types[path.suffix] = types.get(path.suffix, 0) + 1
            if path.suffix not in ALLOWED: content_errors.append({"path": str(path), "error": "unexpected payload suffix"})
            raw = path.read_bytes()
            if path.suffix == ".gz":
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream: raw = stream.read(16 * 1024 * 1024 + 1)
                decoded_count += 1
                if len(raw) > 16 * 1024 * 1024: content_errors.append({"path": str(path), "error": "gzip over16MiB"}); continue
            if raw.startswith((b"glTF", b"IDST", b"VBSP", b"GMAD", b"\x89PNG", b"PK\x03\x04", b"MZ")):
                content_errors.append({"path": str(path), "error": "binary asset signature"})
            try: text = raw.decode("utf-8-sig")
            except UnicodeError: content_errors.append({"path": str(path), "error": "not UTF8 source/metadata"}); continue
            if "\0" in text: content_errors.append({"path": str(path), "error": "embedded NUL"})
            if path.name.endswith((".json", ".json.gz")):
                try: json.loads(text)
                except ValueError: content_errors.append({"path": str(path), "error": "invalid JSON metadata"})
        report.update(packet=relative, actual_files=len(paths), actual_bytes=sum(p.stat().st_size for p in paths),
                      suffix_counts=types, gzip_streams_decoded=decoded_count, content_errors=content_errors)
        reports.append(report)
    preserved = all(stamp(Path(path)) == expected for path, expected in before.items())
    result = {"format": "studio_publication_packet_readonly_audit_1", "packets": reports,
        "packet_files_preserved": preserved, "all_top_indexes_exact": all(not r["errors"] and not r["unindexed_files"] for r in reports),
        "all_source_metadata_text": all(not r["content_errors"] for r in reports),
        "checked_files": len(before), "packet_code_or_graphics_executed": False, "audit_python_only": True,
        "limit": "Content type/signature/JSON and index verification; paths and numeric metadata are allowed, no claim that embedded arbitrary source is safe to execute"}
    (OUT / "RESULTS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("packet_files_preserved", "all_top_indexes_exact", "all_source_metadata_text", "checked_files")}))
    for row in reports: print(json.dumps({key: row[key] for key in ("packet", "indexed_files", "indexed_bytes", "errors", "unindexed_files", "content_errors")}))

if __name__ == "__main__": main()
