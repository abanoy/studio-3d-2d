"""Sample a bounded VMD range into the existing MMD-to-HAS pose adapter."""
from pathlib import Path
import json
import math
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from mmd_motion import read_motion,Sampler
from blender_mmd_pose import convert_pose
from secondary_helpers import GLB


def convert(request):
    count=request.get("count")
    if type(count) is not int or not 1<=count<=241:raise ValueError("Choose between 1 and 241 destination frames")
    source_start=request.get("source_start",0)
    if isinstance(source_start,bool) or not isinstance(source_start,(int,float)) or not math.isfinite(source_start) or not 0<=source_start<=1000000:
        raise ValueError("Invalid VMD source start frame")
    motion=read_motion(request["motion"])
    if not motion["bones"] and not motion["morphs"]:
        raise ValueError("This file contains no model motion. Camera and lighting motion are not imported here.")
    sampler=Sampler(motion);asset=GLB(request["source"])
    bases=request.get("base_frames",[])
    if not isinstance(bases,list) or bases and len(bases)!=count:raise ValueError("Motion base poses do not match the selected range")
    samples=[]
    for offset in range(count):
        pose=sampler.sample_project_frame(offset,request["fps_num"],request.get("fps_den",1),source_start)
        sample=convert_pose(asset,pose,request["scale"],bases[offset] if bases else [])
        sample.update(project_offset=offset,sample_interpolation="linear")
        samples.append(sample)
    return dict(format="studio_mmd_motion_conversion_1",source_sha256=motion["source_sha256"],source_file=Path(request["motion"]).name,model_sha256=asset.sha,
                source_start=source_start,source_last_frame=motion["last_frame"],source_fps=30,
                fps_num=request["fps_num"],fps_den=request.get("fps_den",1),samples=samples,
                other_sections=motion["other_sections"])


if __name__=="__main__":
    request=json.loads(Path(sys.argv[sys.argv.index("--")+1]).read_bytes())
    result=convert(request)
    encoded=json.dumps(result,ensure_ascii=False)
    if len(encoded.encode("utf-8"))>8*1024*1024:raise ValueError("Converted motion exceeds its 8 MiB staging limit")
    Path(request["output"]).write_text(encoded,encoding="utf-8")
    print("VMD_CONVERTED",len(result["samples"]))
