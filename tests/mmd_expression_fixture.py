"""Original tiny native PMX test data, using the installed MMD Tools file API.

This is a test fixture writer, not an application format-export feature.
"""
import importlib.util
from pathlib import Path
def create(path):
    module=Path.home()/'AppData/Roaming/Blender Foundation/Blender/5.1/extensions/user_default/mmd_tools/core/pmx/__init__.py'
    spec=importlib.util.spec_from_file_location('has_original_pmx_fixture',module);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    model=p.Model();model.name='HAS original expression fixture';model.name_e=model.name
    for point in [(-1,0,0),(1,0,0),(1,2,0),(-1,2,0)]:
        v=p.Vertex();v.co=list(point);v.normal=[0,0,-1];v.weight=p.BoneWeight();v.weight.bones=[0];v.weight.weights=[1.];model.vertices.append(v)
    model.faces=[[0,1,2],[0,2,3]]
    bone=p.Bone();bone.name='頭';bone.name_e='Head';bone.location=[0,0,0];model.bones=[bone]
    material=p.Material();material.name='Original warm face';material.diffuse=[.8,.6,.4,1.];material.specular=[0,0,0];material.ambient=[.4,.4,.4];material.edge_color=[0,0,0,1];material.vertex_count=6;model.materials=[material]
    for name,index,offset in [('Eye',2,[.6,.2,0]),('Mouth',3,[-.4,-.3,0])]:
        morph=p.VertexMorph(name,name,4);value=p.VertexMorphOffset();value.index=index;value.offset=offset;morph.offsets=[value];model.morphs.append(morph)
    uv=p.UVMorph('UV effect','UV effect',4,type_index=3);model.morphs.append(uv)
    for name,english,refs in [('笑い','Friendly',[(0,.6),(1,.4)]),('入れ子','Nested',[(3,.5),(0,.2)]),('逆','Reverse',[(0,-.5),(1,.3)]),('UV group','UV group',[(0,1.),(2,1.)])]:
        morph=p.GroupMorph(name,english,4)
        for index,weight in refs:
            value=p.GroupMorphOffset();value.morph=index;value.factor=weight;morph.offsets.append(value)
        model.morphs.append(morph)
    p.save(str(path),model)
