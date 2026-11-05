"""Offline Blender eye binding/UV staging, including transformed helpers and refusal."""
from pathlib import Path
import bpy,json,sys
from mathutils import Matrix,Vector,Euler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_eyes import plan
folder=Path(sys.argv[sys.argv.index('--')+1]);folder.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
eye=bpy.data.objects.new('authored_eye',None);bpy.context.collection.objects.link(eye)
eye.matrix_world=Matrix.Translation((10,20,30))@Euler((.2,.3,.4)).to_matrix().to_4x4()@Matrix.Diagonal(Vector((.03,.03,.03,1)))
mesh=bpy.data.meshes.new('authored_mesh');obj=bpy.data.objects.new('authored_model',mesh);bpy.context.collection.objects.link(obj)
obj.matrix_world=Matrix.Translation((1,-2,3))@Euler((.1,.2,.3)).to_matrix().to_4x4()
native=[(-1,0,0),(1,0,0),(0,0,1)]
vertices=[tuple(obj.matrix_world.inverted()@eye.matrix_world@Vector(p))for p in native]+[(0,0,0),(1,0,0),(0,1,0)]
mesh.from_pydata(vertices,[],[(0,1,2),(3,4,5)]);mesh.update();uv=mesh.uv_layers.new()
for point in uv.data:point.uv=(.13,.27)
material=bpy.data.materials.new('native_iris');body=bpy.data.materials.new('body');mesh.materials.append(material);mesh.materials.append(body);mesh.polygons[1].material_index=1
material['eye_source']=eye;obj['authored_eye_iris_scale']=1.;obj['authored_eye_z_offset']=0.;bpy.context.view_layer.update()
before=[tuple(p.uv)for p in uv.data];prepared=plan(material,[obj]);assert before==[tuple(p.uv)for p in uv.data]
assert len(prepared['changes'])==3
for (_,actual),expected in zip(prepared['changes'],[(0,.5),(1,.5),(.5,1)]):assert max(abs(a-b)for a,b in zip(actual,expected))<.0001,(actual,expected)
for index,value in prepared['changes']:uv.data[index].uv=value
assert [tuple(p.uv)for p in uv.data][3:]==before[3:]
copy=obj.copy();bpy.context.collection.objects.link(copy)
try:plan(material,[obj,copy])
except ValueError:pass
else:raise AssertionError('Ambiguous shared eye material accepted')
after=[tuple(p.uv)for p in uv.data];del obj['authored_eye_iris_scale']
try:plan(material,[obj])
except ValueError:pass
else:raise AssertionError('Missing native helper parameters accepted')
assert after==[tuple(p.uv)for p in uv.data]
result={'transformed_projection':True,'staged_before_mutation':True,'non_eye_uvs_preserved':True,'ambiguous_binding_refused':True,'missing_parameters_refused_without_mutation':True}
(folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('SOURCE_EYES_PROBE '+json.dumps(result))
