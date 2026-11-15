"""Copy an explicit source/text-only draft packet; never remove originals."""
from pathlib import Path
import hashlib
import json
import shutil

TASK = Path(__file__).resolve().parent

def stamp(path):
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def main():
    destination = TASK / "publication-candidate"
    destination.mkdir(exist_ok=False)
    source_index = json.loads((TASK / "SOURCE_INDEX.json").read_bytes())
    selected = [TASK / "overlay" / name for name in source_index["files"]]
    selected += [TASK / name for name in ("README.md", "BASE_SOURCE_CONTEXT.json", "FINAL_SOURCE_CONTEXT.json",
        "SOURCE_INDEX.json", "PRESERVATION.json", "existing-main-seams.patch", "build_candidate.py",
        "integrate_dialog.py", "freeze_packet.py", "compact_packet.py", "review/READ_ONLY_REVIEW.md")]
    selected += sorted((TASK / "failures").glob("*.txt"))
    selected += [TASK / "catalogue_source" / name for name in ("README.md", "SOURCE_BASES.json", "PACKET.json", "FILE_INDEX.json", "test_source_mdl_choices.py")]
    selected += [path for path in sorted((TASK / "runs").rglob("*")) if path.is_file() and path.name in {"result.json", "unittest.log"}]
    selected += [path for path in sorted((TASK / "catalogue_source/runs").rglob("*")) if path.is_file() and path.name in {"result.json", "unittest.log"}]
    rows = {}
    for source in selected:
        if source.is_symlink() or source.stat().st_file_attributes & 0x400:
            raise RuntimeError("Unexpected reparse file")
        relative = source.relative_to(TASK)
        if source.suffix not in {".py", ".gd", ".md", ".json", ".patch", ".txt", ".log"}:
            raise RuntimeError("Not a compact source/text file")
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()):
            raise RuntimeError("Destination escaped")
        before = stamp(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if stamp(source) != before or stamp(target) != before:
            raise RuntimeError("Copy changed source or target")
        rows[relative.as_posix()] = before
    manifest = {"format": "studio_static_choice_unshipped_packet_1", "base_revision": source_index["base_revision"],
        "unshipped": True, "files": rows, "file_count": len(rows), "total_bytes": sum(row["bytes"] for row in rows.values()),
        "actual_tests": {"python_authored_methods": 82, "godot": "UNRUN", "native": "UNRUN", "graphics": "UNRUN"},
        "excluded": "All generated authored model/archive/fake GLB payloads, caches, installed tools and original native assets"}
    index = destination / "FILE_INDEX.json"
    index.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"path": str(destination), "files": len(rows), "bytes": manifest["total_bytes"], "index": stamp(index)}))

if __name__ == "__main__":
    main()
