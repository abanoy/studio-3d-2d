"""Freeze this read-only plan as an indexed source/metadata-only packet.

Does not import or invoke app/conversion runtimes. Existing packet is never reused.
"""
import hashlib
import json
from pathlib import Path
import stat

TASK = Path(__file__).absolute().parent
NAMES = (
    "README.md", "PLAN.md", "shape_ui_actions.gd", "inspect_targets.py",
    "TARGET_INVENTORY.json", "freeze_packet.py", "review/API_REVIEW.md",
    "review/SOURCE_HASHES.json", "review/INDEX.json",
)

def checked(path):
    for item in (path, *path.parents):
        entry = item.lstat()
        if stat.S_ISLNK(entry.st_mode) or getattr(entry, "st_file_attributes", 0) & 0x400:
            raise ValueError("Reparse path refused")
    if not path.is_file():
        raise ValueError("Expected regular file")
    raw = path.read_bytes()
    return raw, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def main():
    reviewed = json.loads((TASK / "review/SOURCE_HASHES.json").read_bytes())
    # Keep the already reviewed bytes unchanged; the independent review remains
    # provenance for inspected source, not an assertion that external files ship.
    entries = reviewed["files"]
    for name in ("PLAN.md", "shape_ui_actions.gd", "TARGET_INVENTORY.json"):
        path = TASK / name
        match = [entry for entry in entries if entry.get("absolute_path", entry.get("path")) == str(path)]
        if len(match) != 1 or checked(path)[1]["sha256"] != match[0]["sha256"]:
            raise ValueError("Reviewed file changed: " + name)
    destination = TASK / "publication-candidate"
    destination.mkdir(exist_ok=False)
    rows = []
    for name in NAMES:
        source = TASK / name
        raw, before = checked(source)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        if checked(source)[1] != before or checked(target)[1] != before:
            raise ValueError("Packet preservation failure: " + name)
        rows.append({"path": name, **before})
    index = {"format": "has_sfm_shape_ui_plan_packet_1", "status": "READ_ONLY_PLAN_ALL_NEW_UI_CASES_UNRUN",
        "parent_supplied_main_revision": "9f6f531538156fc34e3652bc81da8a608e379156",
        "helper_godot_parsed": False, "helper_executed": False,
        "new_resources_staged": False, "payload_file_count": len(rows),
        "payload_bytes": sum(row["bytes"] for row in rows), "files": rows}
    raw = (json.dumps(index, indent=2) + "\n").encode("utf-8")
    with (destination / "INDEX.json").open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"packet": str(destination), "payload_files": len(rows),
        "payload_bytes": index["payload_bytes"], "index_bytes": len(raw),
        "index_sha256": hashlib.sha256(raw).hexdigest()}))

if __name__ == "__main__":
    main()
