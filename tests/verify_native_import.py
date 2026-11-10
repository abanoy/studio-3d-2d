"""Actual PMD/PMX/VRM picker/worker/shared-model/save/render integration, optional private files."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from run import command
from asset_audit import inspect


def private_vrm(name):
    """Use an original or an exact retained import input, never a renamed GLB."""
    supplied = Path(os.environ['HYBRID_NATIVE_INPUTS']) / name if os.environ.get('HYBRID_NATIVE_INPUTS') else None
    if supplied is not None and supplied.is_file(): return supplied
    desktop = Path.home() / 'Desktop' / name
    if desktop.is_file(): return desktop
    for base in [ROOT / 'output', Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output')]:
        manifest = base / 'native-import-verification.json'
        if not manifest.is_file(): continue
        for folder in json.loads(manifest.read_text(encoding='utf-8')).get('bundles', []):
            bundle = Path(folder); parameters = bundle / 'parameters.json'; candidate = bundle / 'native' / name
            if not parameters.is_file() or not candidate.is_file(): continue
            report = json.loads(parameters.read_text(encoding='utf-8'))
            if report.get('kind') == 'vrm_preparation' and report.get('source_file') == name and hashlib.sha256(candidate.read_bytes()).hexdigest() == report.get('source_sha256'):
                return candidate
    return desktop


def main():
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_vrm_import.py"], cwd=ROOT, check=True)
    assets = [
        {"path": r"C:\a\tools\mmd64\UserFile\Model\Miku_Hatsune.pmd", "actor": True, "name": "Miku", "arm": "左腕"},
        {"path": r"C:\a\tools\mmd64\UserFile\Model\environments pack 03 (FFA)\street01_android\street01_android.pmx", "actor": False, "name": "Street"},
        {"path": str(private_vrm('AvatarSample_A.vrm')), "actor": True, "name": "VRM1", "arm": "J_Bip_L_UpperArm"},
        {"path": str(private_vrm('AvatarSample_Avrm0.vrm')), "actor": True, "name": "VRM0", "arm": "J_Bip_L_UpperArm"},
    ]
    if not all(Path(row["path"]).is_file() for row in assets):
        print("SKIP optional owner PMD/PMX/VRM native samples absent")
        return
    originals = {}
    for row in assets:
        path = Path(row["path"])
        row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        originals[path] = (row["sha256"], path.stat().st_mtime_ns)
        if path.suffix.lower() in ("pmd", "pmx"):
            for item in inspect(path)["texture_dependencies"]:
                assert item.get("present") and not item.get("unsafe")
                dependency = path.parent / item["name"].replace("\\", "/")
                originals[dependency] = (hashlib.sha256(dependency.read_bytes()).hexdigest(), dependency.stat().st_mtime_ns)
    (ROOT / "output").mkdir(exist_ok=True)
    (ROOT / "output/native-import-request.json").write_text(json.dumps({"assets": assets}), encoding="utf-8")
    result = subprocess.run(command("tests/native_import_smoke.gd"), cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=210)
    log = result.stdout + result.stderr
    (ROOT / "output/native-import-verification.log").write_text(log, encoding="utf-8")
    if result.returncode or '"failures":0' not in log or any(error in log for error in ("SCRIPT ERROR", "SHADER ERROR", "FAIL ", "ObjectDB instances leaked", "another exclusive child")):
        raise RuntimeError(log)
    report = json.loads((ROOT / "output/native-import-result.json").read_text(encoding="utf-8"))
    for path, before in originals.items():
        assert before == (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns), path
    result = subprocess.run([r"C:\Program Files\ffmpeg\bin\ffprobe.exe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", report["movie"]], capture_output=True, text=True, check=True)
    probe = json.loads(result.stdout)
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    assert (video["codec_name"], video["width"], video["height"], video["r_frame_rate"], video["nb_read_frames"]) == ("h264", 1920, 1080, "24/1", "48")
    assert abs(float(probe["format"]["duration"]) - 2) < .001
    report["original_inputs_unchanged"] = True
    report['input_paths'] = [row['path'] for row in assets]
    report["video"] = {"codec": "h264", "size": [1920, 1080], "fps": "24/1", "frames": 48, "duration": "2.000000"}
    (ROOT / "output/native-import-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
