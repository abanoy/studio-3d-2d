"""Optional private-asset Source integration: staging, real UI conversion/render, MP4 metadata."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command


def run(args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    if result.returncode:
        raise RuntimeError(f"Exit {result.returncode}: {args}\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def main():
    for pattern in ("test_source_archive.py", "test_source_paths.py"):
        print(run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern]))
    output = run(command("tests/source_render_smoke.gd"))
    (ROOT / "output/source-verification.log").write_text(output, encoding="utf-8")
    report = json.loads((ROOT / "output/source-smoke/result.json").read_text(encoding="utf-8"))
    if "SOURCE_SMOKE " not in output or report["failures"] or any(s in output for s in ("SCRIPT ERROR", "FAIL ", "ObjectDB instances leaked")):
        raise RuntimeError("Source UI integration failed; see output/source-verification.log")
    ffprobe = Path(os.environ.get("HYBRID_FFMPEG", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")).with_name("ffprobe.exe")
    report["videos"] = {}
    for label in ("movie", "map_movie"):
        metadata = json.loads(run([str(ffprobe), "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", report[label]]))
        video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
        assert (video["codec_name"], video["width"], video["height"], video["r_frame_rate"], int(video["nb_read_frames"])) == ("h264", 1920, 1080, "24/1", 48)
        assert abs(float(metadata["format"]["duration"]) - 2) < 0.001
        report["videos"][label] = {"codec": "h264", "width": 1920, "height": 1080, "fps": "24/1", "frames": 48, "seconds": 2}
    (ROOT / "output/source-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
