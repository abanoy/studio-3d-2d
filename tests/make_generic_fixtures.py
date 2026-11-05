"""Run in isolated Blender; creates original textured geometry and a two-bone rig."""
from pathlib import Path
import json
import shutil
import sys
import bpy
from mathutils import Vector

out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
image=bpy.data.images.new('surface color',width=16,height=16)
pixels=[]
for y in range(16):
    for x in range(16):pixels.extend((1,.15,.05,1) if (x//4+y//4)%2 else (.05,.3,1,1))
image.pixels[:]=pixels;image.filepath_raw=str(out/'surface color.png');image.file_format='PNG';image.save()
mat=bpy.data.materials.new('Original checker');mat.use_nodes=True
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,1));mesh=bpy.context.object;mesh.name='Textured skinned box';mesh.scale=(.6,.6,2)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);mesh.data.materials.append(mat)
arm=bpy.data.armatures.new('Native two bones');rig=bpy.data.objects.new('Original rig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);mesh.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
root=arm.edit_bones.new('Root');root.head=(0,0,0);root.tail=(0,0,1)
tip=arm.edit_bones.new('Tip');tip.head=(0,0,1);tip.tail=(0,0,2);tip.parent=root
bpy.ops.object.mode_set(mode='OBJECT')
groups={name:mesh.vertex_groups.new(name=name) for name in ('Root','Tip')}
for v in mesh.data.vertices:groups['Root' if v.co.z<1 else 'Tip'].add([v.index],1,'REPLACE')
mod=mesh.modifiers.new('Skin','ARMATURE');mod.object=rig;mesh.parent=rig
bone=rig.pose.bones['Tip'];bone.rotation_mode='XYZ';bone.keyframe_insert('rotation_euler',frame=1);bone.rotation_euler.z=.6;bone.keyframe_insert('rotation_euler',frame=12)
bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(out/'rig-linked.fbx'),use_selection=True,add_leaf_bones=False,path_mode='RELATIVE',embed_textures=False,bake_anim=True)
bpy.ops.export_scene.fbx(filepath=str(out/'rig-embedded.fbx'),use_selection=True,add_leaf_bones=False,path_mode='COPY',embed_textures=True,bake_anim=True)
(out/'embedded-only').mkdir(exist_ok=True);shutil.copyfile(out/'rig-embedded.fbx',out/'embedded-only/rig.fbx')
bpy.ops.export_scene.gltf(filepath=str(out/'rig.gltf'),export_format='GLTF_SEPARATE',export_texture_dir='textures',export_animations=True)
rig.select_set(False);mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.wm.obj_export(filepath=str(out/'textured.obj'),export_selected_objects=True,export_materials=True,path_mode='RELATIVE',forward_axis='NEGATIVE_Z',up_axis='Y')
print('GENERIC_FIXTURES_READY')
