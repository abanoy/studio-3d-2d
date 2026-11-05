"""Real retained Miku declarations and constrained reach, on a disposable GLB."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import bpy
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(Path.home()/"AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default"))
import mmd_tools
mmd_tools.register()
from mmd_tools.core.vmd.importer import BoneConverter
from mmd_ik import capture,EXTRA
from standard_ik import Solver,local_matrix
from secondary_helpers import GLB
from blender_mmd_pose import convert_pose

folder=Path(sys.argv[sys.argv.index("--")+1]);folder.mkdir(exist_ok=True,parents=True)
bundle=Path(json.loads((ROOT/"output/native-import-verification.json").read_bytes())["bundles"][0])
source=bundle/"scene.glb";native=bundle/"native/Miku_Hatsune.pmd";blend=bundle/"editable.blend"
original={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,native,blend)}
bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False,use_scripts=False)
rig,=[obj for obj in bpy.data.objects if obj.type=="ARMATURE"]
asset=GLB(source)
descriptor=capture(native,[rig],asset.doc)
assert len(descriptor["chains"])==7 and not descriptor["skipped"]
asset.doc.setdefault("asset",{}).setdefault("extras",{})[EXTRA]=descriptor
text=json.dumps(asset.doc,ensure_ascii=True,separators=(",",":")).encode();text+=b" "*(-len(text)%4)
tail=asset.raw[20+struct.unpack_from("<I",asset.raw,12)[0]:]
prepared=folder/"scene.glb"
prepared.write_bytes(struct.pack("<4sIIII",b"glTF",2,20+len(text)+len(tail),len(text),0x4e4f534a)+text+tail)
assert prepared.read_bytes()[20+len(text):]==tail
parameters=json.loads((bundle/"parameters.json").read_bytes());parameters["ik_constraints"]=descriptor
(folder/"parameters.json").write_text(json.dumps(parameters,ensure_ascii=True),encoding="utf-8")
asset=GLB(prepared);solver=Solver(asset)
pose=dict(source_sha256="test",bones=[dict(name="左足ＩＫ",position=[0,1,0],rotation_xyzw=[0,0,0,1])],morphs=[])
converted=convert_pose(asset,pose,.08)
solved=dict(bones=converted["bones"],**converted["ik_report"])
assert {row["name"] for row in solved["chains"]}=={"左足ＩＫ","左つま先ＩＫ"}
report={"descriptor":descriptor,"solve":solved,"original_sha256":original,"binary_tail_sha256":hashlib.sha256(tail).hexdigest()}
print("STANDARD_IK_RESIDUALS",[(row["name"],row["residual"],row["steps"]) for row in solved["chains"]])
(folder/"experiment.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
control=rig.pose.bones["左足ＩＫ"]
control.location=BoneConverter(control,.08).convert_location([0,1,0])
bpy.context.view_layer.update()
evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
reference=(evaluated.pose.bones["左足首"].matrix.translation-evaluated.pose.bones["左足ＩＫ"].matrix.translation).length
report["blender_reference_foot_residual"]=reference
report["blender_reference_toe_residual"]=(evaluated.pose.bones["左つま先"].matrix.translation-evaluated.pose.bones["左つま先ＩＫ"].matrix.translation).length
print("TOE_REACH",report["blender_reference_toe_residual"],[(row["name"],row["minimum_residual"]) for row in solved["chains"]])
report["blender_ik_constraints"]=[dict(bone=bone.name,name=c.name,mute=c.mute,valid=c.is_valid,influence=c.influence) for bone in rig.pose.bones for c in bone.constraints if c.type=="IK"]
(folder/"experiment.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
foot=next(row for row in solved["chains"] if row["name"]=="左足ＩＫ")
toe=next(row for row in solved["chains"] if row["name"]=="左つま先ＩＫ")
assert foot["residual"]<.001
assert abs(toe["residual"]-toe["minimum_residual"])<1e-5
assert abs(toe["residual"]-report["blender_reference_toe_residual"])<.001
assert reference<.001,reference
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in original.items())
(folder/"experiment.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("MMD_IK_REFERENCE native7 chains, limited foot and toe reach, Blender residual",reference,"originals unchanged")
