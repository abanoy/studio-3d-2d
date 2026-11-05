from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"tests"))
from run import command
from test_mmd_motion import fixture,camera_fixture


def run(args,log):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=130,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    log.write_text(result.stdout+result.stderr,encoding="utf-8")
    assert result.returncode==0,log.read_text(encoding="utf-8")
    assert not any(s in log.read_text(encoding="utf-8") for s in ("SCRIPT ERROR","SHADER ERROR","ObjectDB instances leaked"))
    return result.stdout+result.stderr


if __name__=="__main__":
    folder=ROOT/"output/mmd-motion"/str(time.time_ns());folder.mkdir(parents=True)
    manifest=json.loads((ROOT/"output/native-import-verification.json").read_bytes())
    source=Path(manifest["bundles"][0])/"scene.glb"
    original=hashlib.sha256(source.read_bytes()).hexdigest()
    motion=folder/"original.vmd";motion.write_bytes(fixture())
    (folder/"camera-only.vmd").write_bytes(camera_fixture())
    request=dict(source=str(source),motion=str(motion),scale=.08,count=25,fps_num=24,fps_den=1,source_start=0,output=str(folder/"converted.json"))
    (folder/"request.json").write_text(json.dumps(request),encoding="utf-8")
    blender=os.environ.get("HYBRID_BLENDER",r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
    run([blender,"--background","--factory-startup","--disable-autoexec","--offline-mode","--python-exit-code","1","--python",str(ROOT/"tests/mmd_motion_reference.py"),"--",str(folder)],folder/"independent.log")
    comparison=json.loads((folder/"independent-comparison.json").read_bytes());assert len(comparison)==25
    args=command("tests/mmd_motion_smoke.gd",extra=["--",str(folder)])
    text=run(args,folder/"app.log");assert "MMD_MOTION_SMOKE " in text
    receipt=Path(args[args.index("--receipt")+1]);desktop=json.loads(receipt.read_bytes())
    assert desktop["exit"]==0 and desktop["child_desktop_confirmed"] and not desktop["foreground_child_observed"] and desktop["job_closed"] and desktop["desktop_closed"]
    report=json.loads((folder/"app-result.json").read_bytes())
    ffprobe=str(Path(os.environ.get("HYBRID_FFMPEG",r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")).with_name("ffprobe.exe"))
    metadata=json.loads(run([ffprobe,"-v","error","-count_frames","-show_streams","-show_format","-of","json",report["movie"]],folder/"ffprobe.json"))
    video=next(s for s in metadata["streams"] if s["codec_type"]=="video")
    assert (video["codec_name"],video["nb_read_frames"],video["width"],video["height"],video["r_frame_rate"])==("h264","48",1920,1080,"24/1")
    assert abs(float(metadata["format"]["duration"])-2)<.01
    assert hashlib.sha256(source.read_bytes()).hexdigest()==original and motion.read_bytes()==fixture()
    report.update(folder=str(folder),private_receipt=str(receipt),original_inputs_unchanged=True,max_position_error=max(r["position_error"] for r in comparison),max_quaternion_error=max(r["quaternion_error"] for r in comparison))
    (ROOT/"output/mmd-motion-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("PASS bounded VMD source sampling, independent native MMD curves/basis, standard keys, Undo, HAS and movie")
