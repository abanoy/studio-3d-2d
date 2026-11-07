"""Original geometry and entity records; exercises the exact Source light emitter."""
import json,sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_lights import plan,create
folder=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(location=(0,0,1));obj=bpy.context.object;obj.name='Original test panel';obj.scale=(1,.1,1)
mat=bpy.data.materials.new('Original diffuse');mat.diffuse_color=(.35,.4,.5,1);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.35,.4,.5,1);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8;obj.data.materials.append(mat)
entities=[{'classname':'light','targetname':'Point','origin':'0 -3 2','_light':'255 180 128 100'}, {'classname':'light_spot','targetname':'Spot','origin':'0 -3 2','angles':'0 90 0','pitch':'-18','_light':'128 180 255 100','_cone':'35','_inner_cone':'20'}, {'classname':'light_environment','targetname':'Sun','angles':'0 90 0','pitch':'-45','_light':'255 255 255 200'}]
prepared=plan(entities,1);create(bpy,prepared);(folder/'entities.json').write_text(json.dumps(entities));(folder/'lights.json').write_text(json.dumps(prepared,indent=2))
bpy.ops.export_scene.gltf(filepath=str(folder/'scene.glb'),export_format='GLB',export_yup=True,export_lights=True,export_cameras=False,export_animations=False)
print('SOURCE_LIGHTS_BLENDER_READY',flush=True)
