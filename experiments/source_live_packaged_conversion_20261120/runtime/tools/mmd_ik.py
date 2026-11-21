"""Normalize separately installed MMD declarations into source-independent IK data."""
from pathlib import Path
import math

EXTRA="studio_ik_constraints"
FORMAT="studio_ik_constraints_1"


def capture(source,rigs,document):
    from mmd_tools.core import pmx
    from mmd_tools.core.pmd.importer import import_pmd_to_pmx
    from mmd_tools.core.pmx.importer import PMXImporter
    result=dict(format=FORMAT,chains=[],skipped=[])
    if len(rigs)!=1:
        result["skipped"].append(dict(name="MMD rig",reason="Multiple armatures have ambiguous native constraints."))
        return result
    model=import_pmd_to_pmx(str(source)) if Path(source).suffix.lower()==".pmd" else pmx.load(str(source))
    joints={i for skin in document.get("skins",[]) for i in skin.get("joints",[])}
    names={}
    for i in joints:names.setdefault(document["nodes"][i].get("name",""),[]).append(i)
    def node(index):
        if type(index) is not int or not 0<=index<len(model.bones):raise ValueError("Invalid native IK bone reference.")
        native=model.bones[index].name
        if len(names.get(native,[]))!=1:raise ValueError("Native IK bone has no unique standard binding: "+native)
        return names[native][0]
    rig=rigs[0];work=0
    inherited=[(i,bone) for i,bone in enumerate(model.bones) if bone.hasAdditionalRotate or bone.hasAdditionalLocation]
    def native_ancestor(parent,child):
        seen=set()
        while 0<=child<len(model.bones):
            if child==parent:return True
            if child in seen:raise ValueError("Cyclic native bone parents.")
            seen.add(child);child=model.bones[child].parent
        return False
    parents={child:i for i,parent in enumerate(document.get("nodes",[])) for child in parent.get("children",[])}
    def ancestor(parent,child):
        seen=set()
        while True:
            if parent==child:return True
            if child not in parents:return False
            if child in seen or len(seen)>256:raise ValueError("Cyclic native IK hierarchy.")
            seen.add(child);child=parents[child]
    for i,bone in sorted(enumerate(model.bones),key=lambda pair:(pair[1].transform_order,pair[0])):
        if not bone.isIK:continue
        if len(result["chains"])+len(result["skipped"])>=64:raise ValueError("Native IK exceeds 64 declarations.")
        try:
            if type(bone.loopCount) is not int or not 1<=bone.loopCount<=256 or not math.isfinite(bone.rotationConstraint) or not 0<bone.rotationConstraint<=math.tau:
                raise ValueError("Native IK iteration/angle settings exceed the supported bounds.")
            if not 1<=len(bone.ik_links)<=32:raise ValueError("Native IK chain length exceeds the supported bounds.")
            involved={i,bone.target,*[link.target for link in bone.ik_links]}
            for inherited_index,inherited_bone in inherited:
                inherited_source=inherited_bone.additionalTransform[0]
                if any(native_ancestor(joint,inherited_source) or native_ancestor(inherited_index,joint) for joint in involved):
                    raise ValueError("Native inherited bone transforms affect this chain and are not baked yet.")
            row=dict(name=bone.name,controller=node(i),effector=node(bone.target),iterations=bone.loopCount,angle_limit=float(bone.rotationConstraint),links=[])
            for link in bone.ik_links:
                entry=dict(node=node(link.target))
                if link.minimumAngle is not None or link.maximumAngle is not None:
                    if link.minimumAngle is None or link.maximumAngle is None:raise ValueError("Incomplete native IK limits.")
                    pose_bone=rig.pose.bones.get(model.bones[link.target].name)
                    if pose_bone is None:raise ValueError("Missing native constraint basis.")
                    minimum,maximum=PMXImporter.convertIKLimitAngles(link.minimumAngle,link.maximumAngle,pose_bone.bone.matrix_local)
                    if any(not math.isfinite(v) or abs(v)>math.tau*2 for v in (*minimum,*maximum)) or any(a>b for a,b in zip(minimum,maximum)):
                        raise ValueError("Invalid native IK angle limits.")
                    entry.update(minimum=list(minimum),maximum=list(maximum))
                row["links"].append(entry)
            prior=row["effector"];seen=set()
            for link in row["links"]:
                if link["node"] in seen or prior==link["node"] or not ancestor(link["node"],prior):raise ValueError("Native IK links do not form a supported ancestor chain.")
                if ancestor(link["node"],row["controller"]):raise ValueError("Native IK target depends on a solved link.")
                prior=link["node"];seen.add(prior)
            cost=row["iterations"]*len(row["links"])
            if work+cost>32768:raise ValueError("Native joint chains exceed the preparation work budget.")
            work+=cost;result["chains"].append(row)
        except (ValueError,IndexError,KeyError) as error:
            result["skipped"].append(dict(name=bone.name,reason=str(error)))
    return result
