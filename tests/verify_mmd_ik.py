from pathlib import Path
import hashlib
import json
import os
import struct
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
from mmd_ik_fixture import create

def run(args,log):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=180,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
    text=result.stdout+result.stderr;log.write_text(text,encoding="utf-8")
    assert result.returncode==0 and not any(s in text for s in ("SCRIPT ERROR","SHADER ERROR","ObjectDB instances leaked")),text
    return text


if __name__=="__main__":
    folder=ROOT/"output/mmd-ik"/str(time.time_ns());folder.mkdir(parents=True)
    source=Path(r"C:\a\tools\mmd64\UserFile\Model\Miku_Hatsune.pmd")
    original=hashlib.sha256(source.read_bytes()).hexdigest()
    pmx=folder/"Original hinge.pmx";create(pmx);pmx_original=hashlib.sha256(pmx.read_bytes()).hexdigest()
    run([sys.executable,"tools/prepare_mmd.py",str(pmx),"--output",str(folder/"pmx")],folder/"pmx-preparation.log")
    pmx_parameters=json.loads((folder/"pmx/parameters.json").read_bytes())
    assert len(pmx_parameters["ik_constraints"]["chains"])==1 and not pmx_parameters["ik_constraints"]["skipped"]
    inherited=folder/"Inherited hinge.pmx";create(inherited,inherited=True)
    run([sys.executable,"tools/prepare_mmd.py",str(inherited),"--output",str(folder/"inherited")],folder/"inherited-preparation.log")
    unsupported=json.loads((folder/"inherited/parameters.json").read_bytes())["ik_constraints"]
    assert not unsupported["chains"] and len(unsupported["skipped"])==1 and "inherited" in unsupported["skipped"][0]["reason"]
    inherited_child=folder/"Inherited descendant hinge.pmx";create(inherited_child,inherited="descendant")
    run([sys.executable,"tools/prepare_mmd.py",str(inherited_child),"--output",str(folder/"inherited-child")],folder/"inherited-child-preparation.log")
    unsupported_child=json.loads((folder/"inherited-child/parameters.json").read_bytes())["ik_constraints"]
    assert not unsupported_child["chains"] and len(unsupported_child["skipped"])==1 and "inherited" in unsupported_child["skipped"][0]["reason"]
    (folder/"hinge.vpd").write_bytes(b"Vocaloid Pose Data file\nHinge.pmx;\n1;\nBone0{Foot target\n0,0.5,0;\n0,0,0,1;\n}\n")
    run([sys.executable,"tools/prepare_mmd.py",str(source),"--output",str(folder/"native")],folder/"preparation.log")
    parameters=json.loads((folder/"native/parameters.json").read_bytes())
    assert len(parameters["ik_constraints"]["chains"])==7 and not parameters["ik_constraints"]["skipped"]
    raw=(folder/"native/scene.glb").read_bytes();size=struct.unpack_from("<I",raw,12)[0]
    document=json.loads(raw[20:20+size]);tail=raw[20+size:]
    assert document["asset"]["extras"]["studio_ik_constraints"]==parameters["ik_constraints"]
    assert hashlib.sha256(tail).hexdigest()==parameters["ik_geometry_tail_sha256"]
    (folder/"foot.vpd").write_bytes("Vocaloid Pose Data file\nMiku.pmd;\n1;\nBone0{左足ＩＫ\n0,1,0;\n0,0,0,1;\n}\n".encode("cp932"))
    data=b"Vocaloid Motion Data 0002".ljust(30,b"\0")+b"Miku".ljust(20,b"\0")+struct.pack("<I",2)
    interpolation=bytearray(64)
    for base in (0,16,32,48):
        for at,value in zip((0,4,8,12),(20,20,107,107)):interpolation[base+at]=value
    for frame,height in ((0,0),(30,1)):
        data+="左足ＩＫ".encode("cp932").ljust(15,b"\0")+struct.pack("<I7f",frame,0,height,0,0,0,0,1)+interpolation
    data+=struct.pack("<5I",0,0,0,0,3)
    for frame,state in ((0,1),(15,0),(24,1)):
        data+=struct.pack("<IBI",frame,1,2)
        for name in ("左足ＩＫ","左つま先ＩＫ"):data+=name.encode("cp932").ljust(20,b"\0")+bytes([state])
    (folder/"foot.vmd").write_bytes(data)
    args=command("tests/mmd_ik_smoke.gd",extra=["--",str(folder)])
    text=run(args,folder/"app.log");assert "MMD_IK_SMOKE " in text
    receipt=Path(args[args.index("--receipt")+1]);desktop=json.loads(receipt.read_bytes())
    assert desktop["exit"]==0 and desktop["child_desktop_confirmed"] and not desktop["foreground_child_observed"] and desktop["job_closed"] and desktop["desktop_closed"]
    report=json.loads((folder/"app-result.json").read_bytes())
    assert report["foot_reach"]<.001 and report["switches_baked"] and report["pixels_exact"]
    probe=str(Path(os.environ.get("HYBRID_FFMPEG",r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")).with_name("ffprobe.exe"))
    metadata=json.loads(run([probe,"-v","error","-count_frames","-show_streams","-show_format","-of","json",report["movie"]],folder/"ffprobe.json"))
    video=next(s for s in metadata["streams"] if s["codec_type"]=="video")
    assert (video["codec_name"],video["width"],video["height"],video["nb_read_frames"],video["r_frame_rate"])==("h264",1920,1080,"48","24/1")
    assert abs(float(metadata["format"]["duration"])-2)<.01 and hashlib.sha256(source.read_bytes()).hexdigest()==original and hashlib.sha256(pmx.read_bytes()).hexdigest()==pmx_original
    report.update(folder=str(folder),private_receipt=str(receipt),original_input_unchanged=True,geometry_tail_verified=True,
                  inherited_direct_skipped=True,inherited_descendant_skipped=True)
    (ROOT/"output/mmd-ik-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("PASS fresh PMD IK declarations, VPD reach/sparse FK, VMD on/off/reset, Undo, packed HAS and movie")
