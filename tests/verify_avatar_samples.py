"""Optional private VRoid2.1.3 VRM0/1 samples through the shared GLB runtime.

This prepares byte-identical GLB test copies, not a shipping VRM importer. No game
application is launched and no original image/model is rewritten.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command


def main():
    samples = [Path.home() / "Desktop" / name for name in ("AvatarSample_A.vrm", "AvatarSample_Avrm0.vrm")]
    if not all(path.is_file() for path in samples):
        print("SKIP: private owner VRM samples absent")
        return
    rows, originals = [], {}
    for index, path in enumerate(samples):
        if path.stat().st_size > 128 * 1024 * 1024: raise ValueError("Sample exceeds GLB budget")
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        originals[path] = (sha, path.stat().st_mtime_ns)
        magic, version, length, json_size, kind = struct.unpack_from("<4sIIII", raw)
        assert (magic, version, length, kind) == (b"glTF", 2, len(raw), 0x4e4f534a)
        assert json_size <= min(16 * 1024 * 1024, len(raw) - 20)
        doc = json.loads(raw[20:20 + json_size])
        for collection in (doc.get("images", []), doc.get("buffers", [])):
            assert all("uri" not in item for item in collection), "Only embedded samples in this test"
        extensions = doc["extensions"]
        family = "1.0" if "VRMC_vrm" in extensions else "0.x"
        assert "VRMC_vrm" in extensions or "VRM" in extensions
        folder = ROOT / "output/compatibility/vrm-owner-samples" / str(index)
        folder.mkdir(parents=True, exist_ok=True)
        glb = folder / "scene.glb"
        glb.write_bytes(raw)
        metadata = {"kind": "vrm_test_preparation", "source_file": path.name,
                    "source_sha256": sha, "vrm_version": family, "extensions": list(extensions),
                    "warning": "Test GLB path; extension bytes retained. Native VRM materials, springs, gaze, IK and expression UI not implemented."}
        (folder / "parameters.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        rows.append({"source": str(path), "sha256": sha, "glb": str(glb), "version": family})
    (ROOT / "output/vrm-owner-test-request.json").write_text(json.dumps({"models": rows}, indent=2), encoding="utf-8")
    result = subprocess.run(command("tests/avatar_samples_smoke.gd"), cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=120)
    log = result.stdout + result.stderr
    (ROOT / "output/avatar-samples-verification.log").write_text(log, encoding="utf-8")
    if result.returncode or '"failures":0' not in log or any(x in log for x in ("SCRIPT ERROR", "SHADER ERROR", "FAIL ", "ObjectDB instances leaked")):
        raise RuntimeError(log)
    report = json.loads((ROOT / "output/avatar-samples-result.json").read_text(encoding="utf-8"))
    probe = subprocess.run([r"C:\Program Files\ffmpeg\bin\ffprobe.exe", "-v", "error", "-count_frames",
                            "-show_streams", "-show_format", "-of", "json", report["movie"]], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["codec_name"], video["width"], video["height"], video["r_frame_rate"], video["nb_read_frames"]) == ("h264", 1920, 1080, "24/1", "48")
    assert abs(float(info["format"]["duration"]) - 2) < .001
    for path, before in originals.items():
        assert before == (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    report["originals_unchanged"] = True
    report["video"] = {"codec": "h264", "width": 1920, "height": 1080, "fps": "24/1", "frames": 48, "duration": "2.000000"}
    project = Path.home() / "Desktop/model.vroid"
    if project.is_file():
        # Inspect the small index/metadata only; do not decompress the native model.
        with zipfile.ZipFile(project) as archive:
            members = archive.infolist()
            assert len(members) <= 128
            meta = archive.getinfo("meta.json")
            assert meta.file_size <= 65536 and meta.compress_type in (0, 8)
            metadata = json.loads(archive.read(meta))
        report["vroid"] = {"entries": len(members), "model_imported": False,
                           "saved_by": [metadata.get("updateVroidVersionMajor"), metadata.get("updateVroidVersionMinor"), metadata.get("updateVroidVersionPatch")]}
    (ROOT / "output/avatar-samples-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
