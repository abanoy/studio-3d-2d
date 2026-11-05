"""Original minimal PMX hinge fixture, not a product model-export feature."""
import importlib.util
import math
from pathlib import Path


def create(path,inherited=False):
    source=Path.home()/"AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default/mmd_tools/core/pmx/__init__.py"
    spec=importlib.util.spec_from_file_location("has_ik_pmx_fixture",source)
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    model=p.Model();model.name="HAS original hinge fixture";model.name_e=model.name
    for name,parent,point in [("Root",-1,[0,2,0]),("Hinge",0,[0,1,.02]),("Tip",1,[0,0,0]),("Foot target",-1,[0,0,0])]:
        bone=p.Bone();bone.name=name;bone.name_e=name;bone.parent=parent;bone.location=point;model.bones.append(bone)
    model.bones[0].displayConnection=1;model.bones[1].displayConnection=2
    target=model.bones[3];target.isIK=True;target.target=2;target.loopCount=40;target.rotationConstraint=2.
    for index in (1,0):
        link=p.IKLink();link.target=index
        if index==1:link.minimumAngle=[-math.pi,0,0];link.maximumAngle=[-.005,0,0]
        target.ik_links.append(link)
    if inherited:
        inherited_source=1
        if inherited=="descendant":
            source_bone=p.Bone();source_bone.name="Inherited source child";source_bone.parent=1;source_bone.location=[0,.5,.01]
            inherited_source=len(model.bones);model.bones.append(source_bone)
        extra=p.Bone();extra.name="Inherited deform";extra.parent=0;extra.location=[0,1,.02];extra.hasAdditionalRotate=True;extra.additionalTransform=(inherited_source,1.)
        model.bones.append(extra)
    for index,y in enumerate((2,1,0)):
        for x in (-.06,.06):
            vertex=p.Vertex();vertex.co=[x,y,0];vertex.normal=[0,0,-1];vertex.weight=p.BoneWeight();vertex.weight.bones=[index];vertex.weight.weights=[1.];model.vertices.append(vertex)
    model.faces=[[0,2,1],[1,2,3],[2,4,3],[3,4,5]]
    material=p.Material();material.name="Original hinge surface";material.diffuse=[.6,.7,.8,1.];material.specular=[0,0,0];material.ambient=[.3,.3,.3];material.edge_color=[0,0,0,1];material.vertex_count=12;model.materials=[material]
    p.save(str(path),model)
