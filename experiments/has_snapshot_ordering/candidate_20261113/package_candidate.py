"""Retain compact source and every diagnostic attempt; no generated payloads."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil

TASK = Path(__file__).resolve().parent

def identity(raw): return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def main():
    target_root = TASK / "publication-candidate"; target_root.mkdir(exist_ok=False)
    records = {}
    def copy_raw(relative, raw, compressed=False):
        data = gzip.compress(raw, mtime=0) if compressed else raw
        target_name = relative + ".gz" if compressed else relative
        target = target_root / target_name
        if not target.resolve().is_relative_to(target_root.resolve()): raise RuntimeError("Escaped destination")
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        records[target_name] = {**identity(data), "original": identity(raw)}
        if compressed and gzip.decompress(data) != raw: raise RuntimeError("Bad compact proof")
    for name in ("README.md", "BASE_SOURCE_CONTEXT.json", "build_candidate.py", "candidate.patch", "ordering_unit.gd", "verify_candidate.py", "package_candidate.py", "overlay/src/has_snapshot_writer.gd", "overlay/src/has_project.gd", "overlay/tests/has_snapshot_ordering_unit.gd"):
        copy_raw(name, (TASK / name).read_bytes())
    # Retain exact used harness sources, checking reconstruction against each
    # existing proof hash before copying any historical driver bytes.
    first_driver = (TASK / "runs/1794602791903330600-27680230/driver_used.py").read_bytes()
    current_driver = (TASK / "verify_candidate.py").read_bytes()
    second_driver = first_driver.replace(b'([^"\\n]+\\.gd)', b'([^"\\n]+\\.gd(?:shader)?)')
    proofs = []
    for folder in sorted((TASK / "runs").iterdir()):
        if not folder.is_dir(): continue
        proof = json.loads((folder / "proof.json").read_bytes()); proofs.append({"run": folder.name, "passed": proof["passed"], "actual": proof["actual"], "exit": proof["exit"], "forbidden_log_lines": proof["forbidden_log_lines"]})
        for name in ("command.json", "process.json", "proof.json", "stdout.log", "engine.log"):
            copy_raw("actual/" + folder.name + "/" + name, (folder / name).read_bytes(), name in {"proof.json", "stdout.log", "engine.log"})
        used_unit = folder / "project/ordering_unit.gd"
        copy_raw("actual/" + folder.name + "/ordering_unit_used.gd", used_unit.read_bytes())
        expected = proof["source_before"][str(TASK / "verify_candidate.py")]["sha256"]
        matched = next((raw for raw in (first_driver, second_driver, current_driver) if identity(raw)["sha256"] == expected), None)
        if matched is None: raise RuntimeError("Cannot reconstruct used driver exactly: " + folder.name)
        copy_raw("actual/" + folder.name + "/driver_used.py", matched)
    if (TASK / "review").is_dir():
        for path in sorted((TASK / "review").glob("*")):
            if path.is_file(): copy_raw("review/" + path.name, path.read_bytes())
    copy_raw("ACTUAL_ATTEMPTS.json", json.dumps({"format": "studio_snapshot_ordering_attempts_1", "attempts": proofs,
        "main_application_acceptance": "UNRUN", "original_failure_cause": "Unknown; no causal relabelling"}, indent=2).encode())
    index = {"format": "studio_snapshot_ordering_source_packet_1", "base_revision": "1236796865e677b150a2d7e2add20f2aac5325fe",
        "unshipped": True, "files": records, "file_count": len(records), "total_bytes": sum(row["bytes"] for row in records.values()),
        "raw_native_assets_or_generated_rasters_included": False, "main_or_runtime_edits": False}
    path = target_root / "FILE_INDEX.json"; path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(json.dumps({"folder": str(target_root), "files": len(records), "bytes": index["total_bytes"], "index": identity(path.read_bytes())}))

if __name__ == "__main__": main()
