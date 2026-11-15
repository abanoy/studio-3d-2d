"""Copy only this owned draft's source/metadata evidence into a fresh packet."""
import hashlib
import json
from pathlib import Path
import stat

TASK = Path(__file__).absolute().parent
CPU = "cpu-run-1794617947420423500"

def read(path):
    for item in (path, *path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Reparse path refused")
    raw = path.read_bytes()
    if len(raw) > 1024 * 1024 or path.suffix not in (".py", ".md", ".json", ".log"):
        raise ValueError("Not a bounded source/metadata payload")
    return raw

def main():
    names = ["README.md", "source/source_mdl_snapshot.py", "source/test_source_mdl_snapshot.py", "run_cpu.py", "freeze_packet.py"]
    names += [CPU + "/" + name for name in ("command.json", "stdout.log", "stderr.log", "result.json")]
    review = TASK / "review"
    if not (review / "INDEX.json").is_file():
        raise ValueError("Independent review has not been frozen")
    names += [path.relative_to(TASK).as_posix() for path in sorted(review.iterdir()) if path.is_file()]
    result = json.loads(read(TASK / CPU / "result.json"))
    if not result["passed"] or not result["preserved"] or result["exit_code"] != 0:
        raise ValueError("CPU proof did not pass")
    for name in ("run_cpu.py", "source/source_mdl_snapshot.py", "source/test_source_mdl_snapshot.py"):
        raw = read(TASK / name)
        if hashlib.sha256(raw).hexdigest() != result["source_runtime_before"][str(TASK / name)]["sha256"]:
            raise ValueError("CPU-bound source changed")
    destination = TASK / "publication-candidate"
    destination.mkdir(exist_ok=False)
    rows = []
    for name in names:
        source = TASK / name
        raw = read(source)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        if read(source) != raw or read(target) != raw:
            raise ValueError("Packet source/readback changed")
        rows.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    index = {"format": "has_selected_mdl_capture_draft_packet_1", "scope": "OUTPUT_ONLY_SOURCE_AUTHORED_CPU",
        "native_inputs_used": False, "app_converter_gpu_runs": False,
        "main_integration_and_real_native_report_fit": "UNRUN", "authored_unittest_cases_passed": 18,
        "payload_files": len(rows), "payload_bytes": sum(row["bytes"] for row in rows), "files": rows}
    raw = (json.dumps(index, indent=2) + "\n").encode("utf-8")
    with (destination / "INDEX.json").open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"packet": str(destination), "payload_files": len(rows), "payload_bytes": index["payload_bytes"],
        "index_bytes": len(raw), "index_sha256": hashlib.sha256(raw).hexdigest()}))

if __name__ == "__main__":
    main()
