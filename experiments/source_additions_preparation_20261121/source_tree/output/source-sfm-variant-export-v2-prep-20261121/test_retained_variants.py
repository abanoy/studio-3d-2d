"""Authored CPU controls, unrun. All objects and flat glTF values are fakes.
The real existing pure GLB/graph serializer is used; the BIN is deliberately not
renderable geometry. These controls prove reference/planning behavior only, not
actual SourceIO/Blender hooks, resources, native geometry or renderer fidelity.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_jiggle_crosswalk as C
import variant_plan as V
import retained_variants as R


class Material:
    def __init__(self, name): self.name=name; self.original=self; self.library=None
class Mesh:
    def __init__(self, material):
        self.original=self; self.library=None; self.materials=[material]
        self.vertices=[None]*12; self.loops=[None]*12
        self.polygons=[NS(material_index=0) for _ in range(4)]
class FastMesh(Mesh): pass
class Object:
    def __init__(self, kind, data=None):
        self.type=kind; self.data=data; self.original=self; self.library=None
        self.parent=None; self.name='same duplicate display name'; self._selected=False; self._hidden=True; self.hide_render=True
        self.material_slots=[] if kind!='MESH' else [NS(material=m) for m in data.materials]
    def select_get(self): return self._selected
    def select_set(self, value): self._selected=value
    def hide_get(self): return self._hidden
    def hide_set(self, value): self._hidden=value
    def as_pointer(self): return id(self)
class Mdl: pass
class ModelContainer: pass
class GMaterial: pass
class GNode:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)
class GPrimitive:
    def __init__(self, material): self.material=material; self.mode=4; self.extensions=None
    def to_dict(self): return {'attributes':{'POSITION':0,'JOINTS_0':1,'WEIGHTS_0':2},'material':self.material,'mode':4,'extensions':self.extensions}
class GMesh:
    def __init__(self, material): self.primitives=[GPrimitive(material)]
    def to_dict(self): return {'primitives':[p.to_dict() for p in self.primitives]}
class GSkin:
    def __init__(self, joints): self.joints=joints; self.inverse_bind_matrices=0
    def to_dict(self): return {'joints':self.joints,'inverseBindMatrices':0}
class GGltf: pass
class Extension:
    def __init__(self, name, extension, required): self.name=name; self.extension=extension; self.required=required
class ChildOfRootExtension(Extension):
    def __init__(self, path, **kw): super().__init__(**kw); self.path=path
class Proof:
    def __init__(self, cap, poses):
        self.armature=cap.armature; self.mdl=cap.mdl; self.native_sha256=cap.catalogue['native_mdl_sha256']
        self.bindings=[NS(native_index=i,data_pointer=id(p.bone),pose_pointer=id(p)) for i,p in enumerate(poses)]
        self.valid=True
    def recheck(self):
        if not self.valid: raise R.Refusal('synthetic_bone_drift')
    def evidence(self): return {'bones':[{'native_index':i,'native_parent_index':i-1} for i in range(len(self.bindings))]}
class Pointer:
    def as_pointer(self): return id(self)


def signed(catalogue):
    result=copy.deepcopy(catalogue); result.pop('catalogue_sha256',None)
    catalogue['catalogue_sha256']=hashlib.sha256(R.canonical(result)).hexdigest()
    return catalogue


def fixture(keiki=False):
    native=next(k for k,v in R.PROFILES.items() if v[1]==(1 if keiki else 3))
    bones, skins, counts=R.PROFILES[native]
    materials=[Material('material'+str(i)) for i in range(3)]
    native_materials=[NS(name='native'+str(i),bpy_material=m) for i,m in enumerate(materials)]
    indices=[[0,1,2]] if keiki else [[0,1,2],[1,1,2],[2,1,2]]
    parts=[]; groups=[]; objects=[]; choices={}
    armature=Object('ARMATURE',NS(bones=[None]*bones))
    for group in range(len(counts)):
        name=['tools','box','flame'][group] if keiki else 'glove'
        models=[NS(name='part'+str(group),vertex_count=12),NS(name='',vertex_count=0)]
        part=NS(name=name,models=models); parts.append(part)
        mesh=Mesh(materials[group if keiki else 0]); obj=Object('MESH',mesh); obj.parent=armature
        objects.append(obj); choices[name]=[obj,None]
        groups.append({'index':group,'name':name,'choices':[{'index':i,'name':m.name,'vertex_count':m.vertex_count,'true_blank':m.vertex_count==0} for i,m in enumerate(models)]})
    mdl=Mdl(); mdl.header=NS(version=49); mdl.body_parts=parts; mdl.materials=native_materials
    mdl.skin_groups=[[native_materials[i] for i in row] for row in indices]
    container=ModelContainer(); container.mdl=mdl; container.objects=objects; container.bodygroups=choices
    container.armature=armature; container.attachments=[]; container.physics_objects=[]
    catalogue=signed({'format':'studio_source_mdl_choices_1','native_version':49,'native_mdl_sha256':native,
        'original_source_sha256':'a'*64,'skin_reference_count':3,
        'materials':[{'index':i,'name':m.name} for i,m in enumerate(native_materials)],
        'skins':[{'index':i,'material_indices':row} for i,row in enumerate(indices)],'bodygroups':groups})
    guard_state=[b'g'*32]
    request={'retain_variants':True,'sourceio_revision':R.REVISION,'sha256':'a'*64,'appearance':None}
    types=NS(Object=Object,Mesh=Mesh,FastMesh=FastMesh,Material=Material,Mdl=Mdl,ModelContainer=ModelContainer)
    cap=R.prepare(request,catalogue,container,types=types,geometry_guard=lambda:guard_state[0])
    poses=[]
    for i in range(bones):
        p=Pointer(); p.bone=Pointer(); p.id_data=armature; poses.append(p)
    proof=Proof(cap,poses)
    contract=NS(**{key:getattr(C,key) for key in ['pointer','emitted_json','scene_dict','node_dict','mesh_dict','scene_graph','compact','final_glb_json']},NativeProof=Proof)
    gt=NS(Material=GMaterial,Mesh=GMesh,MeshPrimitive=GPrimitive,Node=GNode,Skin=GSkin,Gltf=GGltf,Extension=Extension,ChildOfRootExtension=ChildOfRootExtension)
    settings={'gltf_apply':False,'gltf_extras':False,'gltf_skins':True,'gltf_yup':True,'gltf_animations':False,'gltf_current_frame':True,'gltf_morph':True,
        'gltf_rest_position_armature':True,'gltf_def_bones':False,'gltf_leaf_bone':False,
        'gltf_unused_images':False,'gltf_unused_textures':False,
        'gltf_armature_object_remove':False,'gltf_flatten_bones_hierarchy':False,'gltf_flatten_obj_hierarchy':False,
        'gltf_gpu_instances':False,'gltf_use_gltfpack':False,'gltf_draco_mesh_compression':False,
        'pre_export_callbacks':[],'post_export_callbacks':[]}
    ready={id(m) for m in cap.required_materials}; emitted={}; resolver_calls=[]; holder=[]
    def resolve(mat, mesh, actual_settings):
        resolver_calls.append(mat)
        if id(mat) not in emitted:
            emitted[id(mat)]=GMaterial(); holder[0].gather_material_hook(emitted[id(mat)],mat,actual_settings)
        return emitted[id(mat)]
    collector=R.Collector(cap,gltf_types=gt,material_resolver=resolve,resource_guard=lambda m:id(m) in ready,final_resource_guard=lambda document,bindings:True,
                          contract=contract,planner=V,bone_proof=proof)
    holder.append(collector); settings['gltf_user_extensions']=[collector]
    return NS(cap=cap,request=request,catalogue=catalogue,container=container,types=types,guard=guard_state,
        collector=collector,settings=settings,ready=ready,emitted=emitted,resolve=resolve,proof=proof,poses=poses,
        materials=materials,resolver_calls=resolver_calls)


def glb(document):
    encoded=json.dumps(document,separators=(',',':')).encode(); encoded+=b' '*((-len(encoded))%4)
    body=struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',4,0x004e4942)+bytes(4)
    return struct.pack('<III',0x46546c67,2,len(body)+12)+body


def observed(f):
    o=f.collector; s=f.settings; o.pre_export_hook(s)
    joints=[GNode(name='joint'+str(i),children=[] if i+1==len(f.poses) else [i+1]) for i in range(len(f.poses))]
    for node,pose in zip(joints,f.poses): o.gather_joint_hook(node,pose,s)
    skin=GSkin(list(joints)); o.gather_skin_hook(skin,f.cap.armature,s)
    mesh_nodes=[]; meshes=[]
    for obj in f.cap.objects:
        source=tuple(slot.material for slot in obj.material_slots)
        mesh=GMesh(f.resolve(source[0],obj.data,s))
        o.gather_mesh_hook(mesh,obj.data,obj,None,None,source,s)
        if o.failure is not None: return None
        node=GNode(name='same',mesh=mesh,skin=skin); o.gather_node_hook(node,obj,s)
        meshes.append(mesh); mesh_nodes.append(node)
    # Synthetic ordinary-export traversal. This is not an actual SDK invocation.
    materials=list(f.emitted.values()); materials.reverse()
    for mesh in meshes:
        for p in mesh.primitives:
            p.material=R.unique_index(materials,p.material)
            payload=p.extensions[R.EXT].extension
            p.extensions={R.EXT:{'mappings':[{'material':R.unique_index(materials,row['material']),
                'variants':[R.unique_index(o.variant_refs,v) for v in row['variants']]} for row in payload['mappings']]}}
    for index,node in enumerate(mesh_nodes): node.mesh=index; node.skin=0
    skin.joints=list(range(len(joints)))
    arm=GNode(name='armature',children=[0,*range(len(joints),len(joints)+len(mesh_nodes))])
    flat=GGltf(); flat.nodes=[*joints,*mesh_nodes,arm]; flat.meshes=meshes; flat.materials=materials
    flat.skins=[skin]; flat.scene=0; flat.scenes=[NS(nodes=[len(flat.nodes)-1],extras=None)]
    flat.extensions={R.EXT:{'variants':copy.deepcopy(o.variant_values)}}
    return flat


def document(f, flat):
    o=f.collector
    return {**copy.deepcopy(o.final['snapshot']),'asset':{'version':'2.0'},
        'materials':[{} for _ in flat.materials], 'extensions':copy.deepcopy(flat.extensions),
        'extensionsUsed':[R.EXT]}


class CaptureTests(unittest.TestCase):
    def test_default_static_route_does_not_inspect_inputs(self):
        class Bomb:
            def __getattribute__(self,key): raise AssertionError('unexpected inspection')
        for request in [{},{'retain_variants':False}]:
            self.assertIsNone(R.prepare(request,Bomb(),Bomb(),types=Bomb(),geometry_guard=Bomb()))

    def test_explicit_malformed_flag_refuses(self):
        with self.assertRaisesRegex(R.Refusal,'^retain_variants_boolean$'):
            R.prepare({'retain_variants':1},None,None,types=None,geometry_guard=None)

    def test_nitori_has_three_required_actual_material_refs_and_true_blank(self):
        f=fixture(); self.assertEqual(len(f.cap.required_materials),3)
        self.assertIs(f.cap.rows[1][2],None); self.assertIs(f.cap.objects[0],f.container.objects[0])
        self.assertEqual(f.cap.profile,(66,3,(2,)))

    def test_keiki_has_three_independent_object_choices(self):
        f=fixture(True); self.assertEqual(len(f.cap.objects),3)
        self.assertEqual([(r[0],r[1]) for r in f.cap.rows],[(0,0),(0,1),(1,0),(1,1),(2,0),(2,1)])

    def test_catalogue_mutation_refuses(self):
        f=fixture(); f.catalogue['bodygroups'][0]['name']='foreign'
        with self.assertRaisesRegex(R.Refusal,'^native_catalogue_changed$'): f.cap.recheck()

    def test_native_material_or_skin_refs_cannot_be_replaced(self):
        for mutate in [lambda f:setattr(f.container.mdl.materials[0],'bpy_material',Material('same')),
                       lambda f:f.container.mdl.skin_groups[1].__setitem__(0,f.container.mdl.materials[2])]:
            f=fixture(); mutate(f)
            with self.assertRaises(R.Refusal): f.cap.recheck()

    def test_geometry_fingerprint_drift_refuses(self):
        f=fixture(); f.guard[0]=b'x'*32
        with self.assertRaisesRegex(R.Refusal,'^source_geometry_or_inventory_changed$'): f.cap.recheck()

    def test_native_choice_and_mesh_reference_drift_refuses(self):
        for mutate in [lambda f:setattr(f.container.mdl.body_parts[0].models[0],'vertex_count',99),
                       lambda f:setattr(f.cap.objects[0],'data',Mesh(f.materials[0]))]:
            f=fixture(); mutate(f)
            with self.assertRaises(R.Refusal): f.cap.recheck()

    def test_temporary_selection_visibility_restores_on_primary_error(self):
        f=fixture(); other=Object('EMPTY'); other._selected=True
        all_objects=[*f.cap.objects,f.cap.armature,other]
        bpy=NS(context=NS(scene=NS(objects=all_objects),view_layer=NS(objects=NS(active=other))))
        before=[(v.select_get(),v.hide_get(),v.hide_render) for v in all_objects]
        error=RuntimeError('primary')
        with self.assertRaises(RuntimeError) as result:
            with f.cap.visible_export(bpy):
                self.assertTrue(all(v.select_get() and not v.hide_get() and not v.hide_render for v in (*f.cap.objects,f.cap.armature)))
                self.assertFalse(other.select_get()); raise error
        self.assertIs(result.exception,error)
        self.assertEqual(before,[(v.select_get(),v.hide_get(),v.hide_render) for v in all_objects])
        self.assertIs(bpy.context.view_layer.objects.active,other)


class CollectorTests(unittest.TestCase):
    def test_complete_synthetic_export_binds_actual_refs_and_permuted_material_indices(self):
        f=fixture(); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        self.assertIsNone(f.collector.failure)
        raw=glb(document(f,flat)); result=f.collector.finish(raw)
        self.assertEqual(result['manifest']['asset_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['manifest']['surfaces'][0]['materials'],[2,1,0])
        self.assertEqual(result['manifest']['groups'][0]['choices'][0]['nodes'],[66])
        self.assertTrue(result['manifest']['groups'][0]['choices'][1]['blank'])
        self.assertEqual(result['summary']['actual_same_native_bone_count'],66)

    def test_keiki_blank_choices_and_same_skeleton_export(self):
        f=fixture(True); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        result=f.collector.finish(glb(document(f,flat)))
        self.assertEqual([r['choices'][0]['nodes'] for r in result['manifest']['groups']],[[31],[32],[33]])
        self.assertEqual(result['summary']['actual_same_native_bone_count'],31)
        self.assertEqual(result['selection']['groups'],{'0':0,'1':0,'2':0})

    def test_unprepared_alternate_material_is_refused_before_resolver(self):
        f=fixture(); f.ready.remove(id(f.materials[2])); observed(f)
        self.assertIsNotNone(f.collector.failure)
        self.assertFalse(any(m is f.materials[2] for m in f.resolver_calls))

    def test_foreign_equal_named_material_hook_cannot_bind(self):
        f=fixture(); o=f.collector; o.pre_export_hook(f.settings)
        o.gather_material_hook(GMaterial(),Material(f.materials[0].name),f.settings)
        self.assertEqual(o.failure,('material','foreign_material_hook'))

    def test_foreign_extension_or_export_setting_refuses(self):
        for update in [{'gltf_apply':True},{'gltf_user_extensions':[object()]}]:
            f=fixture(); f.settings.update(update); f.collector.pre_export_hook(f.settings)
            self.assertIsNotNone(f.collector.failure)

    def test_same_display_name_objects_are_joined_by_identity(self):
        f=fixture(True); self.assertEqual(len({v.name for v in f.cap.objects}),1)
        flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        self.assertIsNone(f.collector.failure); self.assertEqual(len(f.collector.nodes),3)

    def test_foreign_resolver_result_is_not_admitted_by_value(self):
        f=fixture(); f.collector.resolve=lambda *args:GMaterial(); observed(f)
        self.assertIsNotNone(f.collector.failure)

    def test_missing_or_duplicate_exported_node_identity_refuses(self):
        for duplicate in [False,True]:
            f=fixture(); flat=observed(f)
            if duplicate: flat.nodes.append(f.collector.nodes[id(f.cap.objects[0])])
            else: flat.nodes[66]=GNode(name='same',mesh=0,skin=0)
            f.collector.gather_gltf_extensions_hook(flat,f.settings)
            self.assertIsNotNone(f.collector.failure)

    def test_native_joint_or_skin_substitution_refuses(self):
        for mutate in [lambda f,g:g.skins[0].joints.__setitem__(1,0),
                       lambda f,g:setattr(g.nodes[66],'skin',99),
                       lambda f,g:f.proof.__setattr__('valid',False)]:
            f=fixture(); flat=observed(f); mutate(f,flat)
            f.collector.gather_gltf_extensions_hook(flat,f.settings)
            self.assertIsNotNone(f.collector.failure)

    def test_native_joint_parent_change_refuses(self):
        f=fixture(); flat=observed(f); flat.nodes[0].children=[]
        flat.nodes[-1].children.append(1)
        f.collector.gather_gltf_extensions_hook(flat,f.settings)
        self.assertIsNotNone(f.collector.failure)

    def test_active_scene_must_include_all_variant_meshes(self):
        f=fixture(); flat=observed(f); flat.nodes[-1].children.remove(66)
        f.collector.gather_gltf_extensions_hook(flat,f.settings)
        self.assertIsNotNone(f.collector.failure)

    def test_final_mesh_skin_or_scene_mutations_refuse(self):
        for key in ['meshes','skins','scenes']:
            f=fixture(); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
            value=document(f,flat); value[key]=[]
            with self.subTest(key=key),self.assertRaises(R.Refusal): f.collector.finish(glb(value))

    def test_lost_alt_material_or_variant_mapping_refuses(self):
        for mutate in [lambda d:d['materials'].pop(),
                       lambda d:d['meshes'][0]['primitives'][0]['extensions'][R.EXT]['mappings'][1].update(material=0)]:
            f=fixture(); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
            value=document(f,flat); mutate(value)
            with self.assertRaises(R.Refusal): f.collector.finish(glb(value))

    def test_final_variants_must_remain_optional(self):
        f=fixture(); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        value=document(f,flat); value['extensionsRequired']=[R.EXT]
        with self.assertRaisesRegex(R.Refusal,'^optional_variant_declaration$'): f.collector.finish(glb(value))

    def test_final_resource_guard_must_reconcile_actual_reference_rows(self):
        f=fixture(); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        seen=[]
        def reject(document,bindings):
            seen.extend(bindings)
            return False
        f.collector.final_resource_guard=reject
        with self.assertRaisesRegex(R.Refusal,'^final_resource_reconciliation_required$'):
            f.collector.finish(glb(document(f,flat)))
        self.assertTrue(R.same([row[0] for row in seen],f.cap.required_materials))
        self.assertEqual([row[2] for row in seen],[2,1,0])

    def test_final_resource_consumer_cannot_change_expected_document(self):
        f=fixture(); flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        def mutate(document,bindings):
            document['materials'][0]['foreign']=True
            return True
        f.collector.final_resource_guard=mutate
        with self.assertRaisesRegex(R.Refusal,'^final_resource_consumer_mutated_document$'):
            f.collector.finish(glb(document(f,flat)))

    def test_source_material_assignments_remain_unchanged(self):
        f=fixture(); before=tuple(f.cap.objects[0].data.materials)
        flat=observed(f); f.collector.gather_gltf_extensions_hook(flat,f.settings)
        f.collector.finish(glb(document(f,flat)))
        self.assertTrue(R.same(before,tuple(f.cap.objects[0].data.materials)))
        self.assertTrue(R.same(before,tuple(s.material for s in f.cap.objects[0].material_slots)))


if __name__=='__main__': unittest.main()
