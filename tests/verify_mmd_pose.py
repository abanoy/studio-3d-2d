"""Actual desktop pose import, using the owner's retained local Miku preparation."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command


def run(args):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,
                          encoding="utf-8",errors="replace",timeout=120)
    log=result.stdout+result.stderr
    assert result.returncode==0 and not any(s in log for s in
          ("SCRIPT ERROR","SHADER ERROR","ObjectDB instances leaked")),log
    return log


if __name__=="__main__":
    fixture=ROOT/"output/native-import-verification.json"
    assert fixture.is_file(),"Retained real Miku preparation is required; run the native import verification first."
    folder=ROOT/"output/mmd-pose-tests"
    folder.mkdir(exist_ok=True)
    text="""Vocaloid Pose Data file
Miku_Hatsune.pmd;
2;
Bone0{左腕
0,0,0;
0,0,0.382683432365,0.923879532511;
}
Bone1{センター
1,2,3;
0,0,0,1;
}
Morph0{まばたき
0.75;
}
Morph1{not a real shape
1;
}
"""
    pose=folder/"generated.vpd"
    pose.write_bytes(text.encode("cp932"))
    (folder/"shapes-only.vpd").write_bytes("Vocaloid Pose Data file\nMiku_Hatsune.pmd;\n0;\nMorph0{まばたき\n0;\n}\n".encode("cp932"))
    original=hashlib.sha256(pose.read_bytes()).hexdigest()
    args=command("tests/mmd_pose_import_smoke.gd")
    log=run(args)
    (folder/"workflow.log").write_text(log,encoding="utf-8")
    assert "VPD_APP_ROUNDTRIP " in log
    report=json.loads((ROOT/"output/mmd-pose-result.json").read_bytes())
    for key in ("cancellation_preserved","missing_pose_preserved","stale_review_rejected","undo_restored","pixels_exact","shapes_keyed","shape_only_preserved_body","shape_pixels_changed"):
        assert report[key] is True,key
    assert report["keys"]==2 and hashlib.sha256(pose.read_bytes()).hexdigest()==original
    receipt=Path(args[args.index("--receipt")+1])
    desktop=json.loads(receipt.read_bytes())
    assert desktop["exit"]==0 and desktop["child_desktop_confirmed"] and not desktop["foreground_child_observed"]
    assert desktop["job_closed"] and desktop["desktop_closed"]
    probe=str(Path(os.environ.get("HYBRID_FFMPEG",r"C:\Program Files\ffmpeg\bin\ffmpeg.exe")).with_name("ffprobe.exe"))
    metadata=json.loads(run([probe,"-v","error","-count_frames","-show_streams","-show_format","-of","json",report["movie"]]))
    video=next(s for s in metadata["streams"] if s["codec_type"]=="video")
    assert (video["codec_name"],video["width"],video["height"],video["nb_read_frames"],video["r_frame_rate"])==("h264",1920,1080,"48","24/1")
    assert abs(float(metadata["format"]["duration"])-2)<.01
    report.update(private_receipt=str(receipt),video=video,source_pose_sha256=original)
    (ROOT/"output/mmd-pose-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("PASS MMD pose picker, cancel/retry, stale review, standard body keys, Undo, packed HAS and 1080p movie")
