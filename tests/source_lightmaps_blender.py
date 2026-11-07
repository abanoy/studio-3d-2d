"""Original brush records through the exact capture/bake boundary and real Blender."""
from pathlib import Path
from types import SimpleNamespace as N
import json,sys
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_lightmaps import capture,bake,tag_glb
folder=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
vertices=np.array([[-1,0,0],[1,0,0],[1,0,2],[-1,0,2],[3,0,0],[5,0,0],[5,0,2],[3,0,2]],dtype=np.float32)
mesh=bpy.data.meshes.new('Original brush');mesh.from_pydata(vertices,[],[(0,1,2,3),(4,5,6,7)]);obj=bpy.data.objects.new('Original lit wall',mesh);bpy.context.collection.objects.link(obj);uv=mesh.uv_layers.new(name='UVMap')
for polygon in mesh.polygons:
 for loop,point in zip(polygon.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop].uv=point
material=bpy.data.materials.new('Original stone');material.use_nodes=True;material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.4,.4,.4,1);mesh.materials.append(material)
base=bpy.data.images.new('Original striped stone',width=1024,height=4,alpha=True);pixels=np.ones((4,1024,4),dtype=np.float32);pixels[:,:512,:3]=.25;pixels[:,512:,:3]=.6;base.pixels.foreach_set(pixels.ravel());base.pack();node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=base;material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
lighting=np.array([[64,64,255,0],[64,255,64,0],[255,64,64,0],[255,255,255,2]],dtype=np.uint8)
face=lambda start,styles:N(first_edge=start,edge_count=4,disp_info_id=-1,lightmap_width=1,lightmap_height=1,light_offset=0,styles=styles,lightmap_texture_mins_in_luxels=(0,0),tex_info_id=0)
edges=np.array([[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4]],dtype=np.int32)
lumps={'LUMP_LIGHTING':N(lightmap_data=lighting),'LUMP_MODELS':N(models=[N(first_face=0,face_count=2)]),'LUMP_VERTICES':N(vertices=vertices),'LUMP_EDGES':N(edges=edges),'LUMP_SURFEDGES':N(surf_edges=np.arange(8,dtype=np.int32)),'LUMP_FACES':N(faces=[face(0,(0,-1,-1,-1)),face(4,(0,1,-1,-1))]),'LUMP_TEXINFO':N(texture_info=[N(lightmap_vectors=((.5,0,0,.5),(0,0,-.5,1)))])}
(folder/'original-lighting.bin').write_bytes(lighting.tobytes())
handler=N(_bsp=N(get_lump=lambda name:lumps[name]),scale=1.)
lumps['LUMP_FACES'].faces.append(face(0,(0,-1,-1,-1)));lumps['LUMP_MODELS'].models[0].face_count=3;duplicate=capture(handler,0,obj,{});ambiguous=bake(bpy,[duplicate],32*1024*1024);assert ambiguous['faces']==0 and ambiguous['skipped']['duplicate brush face identity']==1
lumps['LUMP_FACES'].faces.pop();lumps['LUMP_MODELS'].models[0].face_count=2;job=capture(handler,0,obj,{})
limited=bake(bpy,[job],0);assert limited['faces']==0 and limited['skipped']['decoded texture budget']==1
report=bake(bpy,[job],32*1024*1024);assert report['faces']==1 and report['atlases']==1 and report['downsampled_faces']==1 and report['skipped']['styled lightmap']==1 and mesh.polygons[0].material_index!=mesh.polygons[1].material_index
uv1=mesh.uv_layers.get('lightmap');assert uv1 and all(0<=v<=1 for row in uv1.data for v in row.uv)
assert report['objects'][0]['emission_strength']>1
(folder/'parameters.json').write_text(json.dumps({'kind':'original_decoded_brush_fixture','static_brush_lightmaps':report},indent=2));(folder/'lightmaps.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'original-lightmap.blend'))
bpy.ops.export_scene.gltf(filepath=str(folder/'scene.glb'),export_format='GLB',export_yup=True,export_lights=False,export_cameras=False,export_animations=False)
tag_glb(folder/'scene.glb',report['materials'])
print('SOURCE_LIGHTMAPS_BLENDER_READY',flush=True)
