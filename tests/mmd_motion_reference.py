"""Independent installed MMD curve reader/bone conversion comparison in Blender."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
from mathutils import Quaternion,Vector,Matrix

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from mmd_motion import read_motion,Sampler
from blender_mmd_motion import convert
from secondary_helpers import GLB

addon=Path.home()/"AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default"
sys.path.insert(0,str(addon))
import mmd_tools
mmd_tools.register()
from mmd_tools.core import vmd
from mmd_tools.core.vmd.importer import _FnBezier,BoneConverter

folder=Path(sys.argv[sys.argv.index("--")+1])
request=json.loads((folder/"request.json").read_bytes())
original=Path(request["source"]).with_name("editable.blend")
digest=hashlib.sha256(original.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(original),load_ui=False,use_scripts=False)
rig,=[obj for obj in bpy.data.objects if obj.type=="ARMATURE"]
reference=vmd.File();reference.load(filepath=request["motion"])
converted=convert(request)
asset=GLB(request["source"])
(folder/"converted.json").write_text(json.dumps(converted,ensure_ascii=False),encoding="utf-8")
sampler=Sampler(read_motion(request["motion"]))
rows=[]
for offset in range(request["count"]):
    source_frame=offset*30*request["fps_den"]/request["fps_num"]
    sample=sampler.sample(source_frame)
    for record in sample["bones"]:
        first,last=sorted(reference.boneAnimation[record["name"]],key=lambda key:key.frame_number)
        fraction=source_frame/30
        factors=[]
        for base in (0,16,32,48):
            x1,y1,x2,y2=[last.interp[base+i]/127 for i in (0,4,8,12)]
            curve=_FnBezier(Vector((0,0)),Vector((x1,y1)),Vector((x2,y2)),Vector((1,1)))
            factors.append(fraction if fraction in (0,1) else curve.evaluate_by_x(fraction).y)
        position=[a+(b-a)*t for a,b,t in zip(first.location,last.location,factors)]
        a=Quaternion((first.rotation[3],*first.rotation[:3])).normalized()
        b=Quaternion((last.rotation[3],*last.rotation[:3])).normalized()
        rotation=a.slerp(b,factors[3])
        converter=BoneConverter(rig.pose.bones[record["name"]],request["scale"])
        expected_position=converter.convert_location(position)
        expected_rotation=converter.convert_rotation([rotation.x,rotation.y,rotation.z,rotation.w])
        actual=next(row for row in converted["samples"][offset]["bones"] if row["name"]==record["name"])
        error=(Vector(actual["translation"])-expected_position).length
        x,y,z,w=actual["rotation_xyzw"];q=Quaternion((w,x,y,z))
        rotation_error=min((q-expected_rotation).magnitude,(q+expected_rotation).magnitude)
        if error>=1e-5:
            skin=asset.doc["skins"][0]
            node=next(i for i,n in enumerate(asset.doc["nodes"]) if n.get("name")==record["name"])
            values=asset.accessor(skin["inverseBindMatrices"],"MAT4")[skin["joints"].index(node)]
            standard=Matrix([values[c::4] for c in range(4)]).inverted().to_3x3().normalized()
            conversion=standard.transposed()@Matrix(((1,0,0),(0,1,0),(0,0,-1)))
            alternate=(conversion@Vector(position))*request["scale"]
            print("BIND_PRECISION",offset,"node chain",error,"inverse bind",(alternate-expected_position).length)
            raw=Matrix([values[c::4] for c in range(4)]).inverted().to_3x3()
            raw_position=(raw.transposed()@Matrix(((1,0,0),(0,1,0),(0,0,-1)))@Vector(position))*request["scale"]
            original_basis=rig.pose.bones[record["name"]].bone.matrix_local.to_3x3()
            print("BIND_PRECISION raw",(raw_position-expected_position).length,"native column lengths",[column.length for column in original_basis.col],"bind column lengths",[column.length for column in raw.col])
        assert error<1e-5 and rotation_error<2e-6,(offset,error,rotation_error)
        rows.append(dict(project_offset=offset,source_frame=source_frame,position_error=error,quaternion_error=rotation_error))
assert hashlib.sha256(original.read_bytes()).hexdigest()==digest
(folder/"independent-comparison.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
print("VMD_REFERENCE",len(rows),"native MMD curves, shortest-path slerp and real Miku BoneConverter; original unchanged")
