"""Compact this completed headless probe without copying directories or deleting."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil

TASK = Path(__file__).resolve().parent
RUN = TASK / "runs/1794602441029208700-3d929ffb"
DESTINATION = TASK / "publication-candidate"

def digest(raw):
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def main():
    DESTINATION.mkdir(exist_ok=False)
    rows = {}
    for name in ("README.md", "probe.gd", "run_probe.py", "package_probe.py"):
        source = TASK / name; target = DESTINATION / name
        shutil.copy2(source, target)
        rows[name] = digest(source.read_bytes())
        if digest(target.read_bytes()) != rows[name]: raise RuntimeError("Source copy differs")
    for name in ("request.json", "command.json", "process.json", "proof.json", "result.json", "engine.log", "stdout.log"):
        source = RUN / name; raw = source.read_bytes()
        compressed = name in ("proof.json", "result.json", "engine.log", "stdout.log")
        output = gzip.compress(raw, mtime=0) if compressed else raw
        target_name = name + ".gz" if compressed else name
        target = DESTINATION / "actual" / target_name; target.parent.mkdir(exist_ok=True)
        target.write_bytes(output)
        rows["actual/" + target_name] = {**digest(output), "original": digest(raw)}
        if compressed and gzip.decompress(target.read_bytes()) != raw: raise RuntimeError("Compressed proof differs")
    value = {"format": "studio_cwd_race_probe_packet_1", "main_revision": "1236796865e677b150a2d7e2add20f2aac5325fe",
        "outcome": "240 successful absolute Python launches; suspected race not reproduced",
        "files": rows, "file_count": len(rows), "total_bytes": sum(row["bytes"] for row in rows.values()),
        "private_native_assets_included": False, "godot_gpu_or_blender": False}
    index = DESTINATION / "FILE_INDEX.json"
    index.write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(json.dumps({"folder": str(DESTINATION), "files": len(rows), "bytes": value["total_bytes"], "index": digest(index.read_bytes())}))

if __name__ == "__main__":
    main()
