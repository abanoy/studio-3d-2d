"""Convert a bounded VPD against an MMD-prepared standard GLB. Run in Blender Python."""
from pathlib import Path
import json
import math
import sys
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from mmd_pose import read_pose, binding_plan
from secondary_helpers import GLB


def convert(source, pose_path, scale,base_bones=()):
    return convert_pose(GLB(source),read_pose(pose_path),scale,base_bones)


def convert_pose(asset, pose, scale,base_bones=()):
    if not isinstance(scale,(int,float)) or not math.isfinite(scale) or not 0.0001<=scale<=100:
        raise ValueError("Invalid MMD import scale")
    nodes=asset.doc["nodes"]
    parents={}
    for i,node in enumerate(nodes):
        for child in node.get("children",[]):
            if type(child) is not int or not 0<=child<len(nodes) or child in parents:
                raise ValueError("Invalid joint hierarchy")
            parents[child]=i
    matrices={}
    active=set()
    def global_matrix(index):
        if index in matrices:return matrices[index]
        if index in active or len(active)>256:raise ValueError("Cyclic or excessive joint hierarchy")
        active.add(index)
        node=nodes[index]
        if "matrix" in node:
            values=node["matrix"]
            if len(values)!=16:raise ValueError("Invalid joint matrix")
            local=Matrix([values[c::4] for c in range(4)])
        else:
            x,y,z,w=node.get("rotation",[0,0,0,1])
            local=Matrix.LocRotScale(Vector(node.get("translation",[0,0,0])),
                                    Quaternion((w,x,y,z)),Vector(node.get("scale",[1,1,1])))
        if not all(math.isfinite(v) for row in local for v in row):
            raise ValueError("Nonfinite joint transform")
        matrices[index]=global_matrix(parents[index])@local if index in parents else local
        active.remove(index)
        return matrices[index]
    joints={i for skin in asset.doc.get("skins",[]) for i in skin.get("joints",[])}
    if any(type(i) is not int or not 0<=i<len(nodes) for i in joints):
        raise ValueError("Invalid skin joint")
    bones=[dict(id=str(i),name=nodes[i].get("name","")) for i in sorted(joints)]
    plan=binding_plan(pose,bones)
    if plan["ambiguous"]:raise ValueError("Pose contains ambiguous bone names")
    if not plan["matched"] and not pose["morphs"] and not pose.get("ik_enabled"):raise ValueError("Pose has no matching bones or shape controls")
    reflection=Matrix(((1,0,0),(0,1,0),(0,0,-1)))
    records=[]
    for match in plan["matched"]:
        index=int(match["bone_id"])
        # Blender's native edit-bone basis can retain tiny length deviations.
        # Preserve them for translation, as MMD Tools' BoneConverter does.
        basis=global_matrix(index).to_3x3()
        unit=basis.normalized()
        if any(abs(column.length-1)>0.001 for column in basis.col) or abs(abs(unit.determinant())-1)>0.0001:
            raise ValueError("Pose import requires an orthogonal unit joint basis")
        conversion=basis.transposed()@reflection
        record=match["control"]
        position=(conversion@Vector(record["position"]))*scale
        x,y,z,w=record["rotation_xyzw"]
        q=Quaternion((w,x,y,z)).normalized()
        rotation=conversion.to_quaternion()
        rotation=(rotation@q@rotation.conjugated()).normalized()
        records.append(dict(name=record["name"],translation=list(position),
                            rotation_xyzw=[rotation.x,rotation.y,rotation.z,rotation.w]))
    from standard_ik import Solver
    solved=Solver(asset).apply(records,base_bones,pose.get("ik_enabled",{}))
    if not solved["bones"] and not pose["morphs"]:raise ValueError("This model has no retained IK declarations for those switches. Import the original MMD model again.")
    return dict(format="studio_mmd_pose_conversion_1",model_sha256=asset.sha,
                pose_sha256=pose["source_sha256"],bones=solved["bones"],
                unmatched_bones=plan["unmatched"],morphs=pose["morphs"],
                ik_report={key:value for key,value in solved.items() if key!="bones"})


if __name__=="__main__":
    request_path=Path(sys.argv[sys.argv.index("--")+1])
    request=json.loads(request_path.read_bytes())
    result=convert(request["source"],request["pose"],request["scale"],request.get("base_bones",[]))
    Path(request["output"]).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("VPD_CONVERTED",len(result["bones"]))
