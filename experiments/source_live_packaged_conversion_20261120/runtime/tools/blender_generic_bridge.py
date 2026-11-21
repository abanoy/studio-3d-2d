"""Isolated built-in Blender import; original files are read-only, no source scripts run."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
sys.dont_write_bytecode=True
import bpy
bpy.context.preferences.filepaths.file_preview_type='NONE'
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).parent))
from generic_assets import digest,MAX_TOTAL,IMAGE_EXT

req=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
out=Path(req['output']);source=Path(req['source']);native=out/'native';original=Path(req['asset_root'])
dependencies={i['path']:i for i in req['dependencies']};warnings=[]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

# FBX's built-in image loader can receive author-machine absolute paths. Confine
# it to the declared asset folder and staged copies; embedded data packs afterward.
if source.suffix.lower()=='.fbx':
    from bpy_extras import image_utils
    original_loader=image_utils.load_image
    def image_loader(filepath,*args,**kwargs):
        text=str(filepath).replace('\\','/');value=Path(text)
        candidate=None
        if text.startswith('//') or '://' in text:pass
        elif value.is_absolute():
            resolved=value.resolve()
            if resolved.is_relative_to(native):candidate=original/resolved.relative_to(native)
            elif resolved.is_relative_to(original):candidate=resolved
        else:candidate=Path(req['original_source']).parent/value
        if candidate is None or not candidate.resolve().is_relative_to(original) or not candidate.is_file():
            candidate=Path(req['original_source']).parent/value.name
        staged=native/'_missing'/value.name
        if candidate.is_file() and candidate.resolve().is_relative_to(original):
            candidate=candidate.resolve()
            if candidate.suffix.lower() not in IMAGE_EXT or candidate.stat().st_size>64*1024*1024:raise ValueError('Unsupported or oversized FBX texture')
            relative=candidate.relative_to(original);staged=native/relative;staged.parent.mkdir(parents=True,exist_ok=True)
            before=digest(candidate)
            if not staged.exists():shutil.copyfile(candidate,staged)
            if digest(staged)!=before or digest(candidate)!=before:raise ValueError('FBX texture changed while staging')
            dependencies[str(candidate)]={'path':str(candidate),'relative':relative.as_posix(),'sha256':before,'bytes':candidate.stat().st_size}
            if len(dependencies)>2048 or sum(i['bytes'] for i in dependencies.values())>MAX_TOTAL:raise ValueError('FBX dependency budget exceeded')
        kwargs['dirname']=str(native);kwargs['recursive']=False
        return original_loader(str(staged),**kwargs)
    image_utils.load_image=image_loader
    try:bpy.ops.import_scene.fbx(filepath=str(source),use_image_search=False,use_anim=True,use_custom_props=True)
    finally:image_utils.load_image=original_loader
elif source.suffix.lower()=='.obj':
    bpy.ops.wm.obj_import(filepath=str(source),forward_axis='NEGATIVE_Z' if req['obj_up']=='Y' else 'Y',up_axis=req['obj_up'])
else:bpy.ops.import_scene.gltf(filepath=str(source))

objects=list(bpy.context.scene.objects);rigs=[o for o in objects if o.type=='ARMATURE']
# Blender's glTF importer creates custom bone-display meshes (e.g. Icosphere).
# They belong in the editable rig, but are not imported asset geometry.
helpers={bone.custom_shape for rig in rigs for bone in rig.pose.bones if bone.custom_shape}
meshes=[o for o in objects if o.type=='MESH' and o not in helpers]
if not any(len(o.data.polygons) for o in meshes):raise ValueError('No renderable mesh imported')
if sum(len(r.data.bones) for r in rigs)>512:raise ValueError('Model exceeds studio512bone limit')
pixels=0
for image in bpy.data.images:
    if image.source not in ('FILE','GENERATED'):continue
    if image.source=='FILE' and not image.packed_file:
        path=Path(bpy.path.abspath(image.filepath)).resolve()
        if not path.is_relative_to(native) or not path.is_file():raise ValueError('Missing or outside-folder texture: '+image.filepath)
    if image.size[0]*image.size[1]>16*1024*1024:raise ValueError('Image exceeds16million pixels')
    pixels+=image.size[0]*image.size[1]
    if pixels>64*1024*1024:raise ValueError('Images exceed64million total pixels')
    if image.source=='FILE' and not image.has_data:raise ValueError('Texture could not be decoded: '+image.filepath)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'editable.blend'),check_existing=False,compress=True)
report={'adapter':'studio_generic_1','standard':'studio_model_1','source_file':Path(req['original_source']).name,
        'source_sha256':req['source_sha256'],'format':source.suffix.lower()[1:],'scale':req['scale'],'obj_up':req['obj_up'],
        'tools':{'blender':bpy.app.version_string},'dependencies':list(dependencies.values()),'warnings':warnings,
        'counts':{'meshes':len(meshes),'bones':sum(len(r.data.bones) for r in rigs),'textures':sum(i.source=='FILE' or bool(i.packed_file) for i in bpy.data.images)},
        'native_parameters':{'rigs':[{'name':r.name,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None} for b in r.data.bones]} for r in rigs],
                             'objects':[{'name':o.name,'type':o.type} for o in objects],
                             'materials':[{'name':m.name,'diffuse':list(m.diffuse_color),'metallic':m.metallic,'roughness':m.roughness} for m in bpy.data.materials if m.users],
                             'animation_actions':[a.name for a in bpy.data.actions]},
        'editor_helpers_excluded':[o.name for o in helpers],
        'limits':['Static geometry and skinned bind pose; imported actions stay in editable.blend, not the Studio timeline',
                  'PBR material approximation; no native constraints, physics, shader graphs or lossless roundtrip',
                  'Unit/axis handling follows importer metadata (FBX/glTF) or chosen OBJ up axis; adjustable uniform scale']}
for obj in objects:
    obj.animation_data_clear()
    if obj.type=='ARMATURE':obj.data.pose_position='REST'
    if obj.type=='MESH' and obj.data.shape_keys:obj.data.shape_keys.animation_data_clear()
    if obj.parent is None:obj.matrix_world=Matrix.Scale(req['scale'],4)@obj.matrix_world
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(False)
for obj in objects:
    if obj not in helpers and obj.type in ('MESH','ARMATURE','EMPTY'):obj.hide_set(False);obj.hide_render=False;obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'scene.glb'),export_format='GLB',use_selection=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=False,export_yup=True,export_image_format='AUTO')
serialized=json.dumps(report,ensure_ascii=True,indent=2)
if len(serialized.encode())>256*1024:raise ValueError('Native report exceeds studio256KiB limit')
(out/'parameters.json').write_text(serialized,encoding='utf-8')
print('STUDIO_GENERIC_READY',json.dumps(report['counts']))
