"""Optional real installed SFM asset checks, with explicit skips when unavailable."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from run import command
from source_content import discover, assets
from source_paths import DEFAULT_GMOD, DEFAULT_WORKSHOP


def main():
    discovery = discover(DEFAULT_GMOD, DEFAULT_WORKSHOP)
    installed = discovery["games"][-1]["locations"]
    if not installed:
        print("SKIP: real SFM is not installed; fixture coverage remains in test_source_content.py")
        return
    sfm = Path(installed[0]) / "game"
    model = sfm / "tf_movies/models/player/hwm/scout.mdl"
    map_file = sfm / "tf_movies/maps/box.bsp"
    if not model.is_file() or not map_file.is_file():
        print("SKIP: installed SFM lacks the specific Scout/box fixtures")
        return
    originals = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (model, map_file, sfm / "usermod/gameinfo.txt")}
    inventory = []
    for provider in discovery["providers"]:
        if not provider["origin"].startswith("sfm"): continue
        rows = assets(provider)["assets"] if provider["present"] else []
        inventory.append({**provider, "models": sum(a["kind"] == "model" for a in rows), "maps": sum(a["kind"] == "map" for a in rows)})
    output = ROOT / "output"; output.mkdir(exist_ok=True)
    (output / "sfm-verification-input.json").write_text(json.dumps({"model": str(model), "map": str(map_file)}), encoding="utf-8")
    process = subprocess.run(command("tests/sfm_render_smoke.gd"), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=210)
    log = process.stdout + process.stderr
    (output / "sfm-verification.log").write_text(log, encoding="utf-8")
    if process.returncode or '"failures":0' not in log or any(s in log for s in ("SCRIPT ERROR", "FAIL ", "ObjectDB instances leaked", "another exclusive child")):
        raise RuntimeError(log)
    result = json.loads((output / "sfm-smoke/result.json").read_text(encoding="utf-8"))
    deps = json.loads((Path(result["model_bundle"]) / "dependencies.json").read_text(encoding="utf-8"))
    providers = {Path(d["provider"]).resolve() for d in deps["resolved"] if d["path"].lower().endswith((".vmt", ".vtf"))}
    assert (sfm/"tf").resolve() in providers and (sfm/"tf_movies").resolve() in providers
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == sha for p, sha in originals.items())
    probe = subprocess.run([r"C:\Program Files\ffmpeg\bin\ffprobe.exe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", result["movie"]], capture_output=True, text=True, check=True)
    video = next(s for s in json.loads(probe.stdout)["streams"] if s["codec_type"] == "video")
    assert (video["codec_name"], video["width"], video["height"], video["r_frame_rate"], video["nb_read_frames"]) == ("h264", 1920, 1080, "24/1", "48")
    result.update(inventory=inventory, discovery_warnings=discovery["warnings"], video=video, native_inputs_unchanged=True, cross_mod_textures=True)
    (output / "sfm-verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k,v in result.items() if k not in {"inventory", "video"}}, indent=2))


if __name__ == "__main__": main()
