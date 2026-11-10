"""Private actual Bikini Reimu missing-chain setup, fan, Record and packed replay.

Supply the converted player scene.glb with its parameters.json sibling. No game
installation or redistributed model is required. Linux requires an explicitly
provisioned isolated X display; Windows uses run.command's hidden desktop.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run


def identity(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-source", type=Path, required=True)
    parser.add_argument("--isolated-display")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    if sys.platform == "linux":
        if not options.isolated_display:
            parser.error("Linux graphical tests require --isolated-display :N")
        run.configure_private_display(options.isolated_display)
    source = options.prepared_source.resolve(strict=True)
    parameters = source.with_name("parameters.json")
    if not parameters.is_file():
        parser.error("The actual converted native model requires its parameters.json sibling")
    originals = {str(path): identity(path) for path in (source, parameters)}
    folder = (options.output or ROOT / "output/reimu-helpers" / str(time.time_ns())).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    staged = folder / "input"; staged.mkdir()
    for path in (source, parameters):
        shutil.copy2(path, staged / path.name)
    prepared = staged / source.name

    def invoke(mode):
        args = ["--audio-driver", "Dummy", "--log-file", str(folder / (mode + "-engine.log")),
                "--", str(folder), str(prepared)]
        if mode == "reader": args.append("--read")
        with (folder / (mode + ".log")).open("w", encoding="utf-8") as log:
            result = subprocess.run(run.command("tests/reimu_helpers_smoke.gd", extra=args),
                                    cwd=ROOT, stdout=log, stderr=log, timeout=250)
        text = (folder / (mode + ".log")).read_text(encoding="utf-8", errors="replace")
        if result.returncode or any(marker in text for marker in
                                   ("SCRIPT ERROR", "SHADER ERROR", "FAIL ", "ERROR:", "ObjectDB instances leaked")):
            raise RuntimeError(f"{mode} failed; see {folder / (mode + '.log')}")
        report = json.loads((folder / (mode + "-result.json")).read_text(encoding="utf-8"))
        assert report["failures"] == 0
        return report

    writer = invoke("writer")
    expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(folder / "Reimu helpers.has") as archive:
        manifest = json.loads(archive.read("project.json"))
    actor = next(row for row in manifest["world"]["objects"] if row["id"] == expected["actor_id"])
    # Compare the original full-precision writer oracle to actual stored numbers.
    # This is independent of Godot's numeric types and its JSON parser rounding.
    assert actor["animation_clips"][0]["keys"] == expected["keys"]
    assert actor["metadata"]["generated_helpers"] == expected["report"]
    assert actor["sha256"] == expected["derived_sha256"]
    offline = folder / "input.offline"; staged.rename(offline)
    try:
        reader = invoke("reader")
    finally:
        offline.rename(staged)
    encoder = os.environ.get("HYBRID_FFMPEG", "")
    sibling = Path(encoder).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe") if encoder else None
    ffprobe = str(sibling) if sibling and sibling.is_file() else shutil.which("ffprobe") or "ffprobe"
    probe = subprocess.run([ffprobe, "-v", "error", "-count_frames",
                            "-show_streams", "-of", "json", writer["movie"]],
                           capture_output=True, text=True, check=True)
    video = next(row for row in json.loads(probe.stdout)["streams"] if row["codec_type"] == "video")
    assert (video["codec_name"], video["width"], video["height"], video["nb_read_frames"],
            video["r_frame_rate"], float(video["duration"])) == ("h264",1920,1080,"24","24/1",1.0)
    assert all(identity(Path(path)) == before for path, before in originals.items())
    report = {"writer": writer, "reader": reader, "originals": originals,
              "packed_keys_exact": True, "private_source_offline_for_reader": True,
              "video": {key: video[key] for key in ("codec_name","width","height","nb_read_frames","r_frame_rate","duration")}}
    (folder / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
