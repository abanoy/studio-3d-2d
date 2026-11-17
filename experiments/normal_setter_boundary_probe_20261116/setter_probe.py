"""UNRUN Blender source-only next probe. Native arrays remain private; no export/save."""
from pathlib import Path
import argparse,hashlib,importlib,importlib.util,json,os,sys,traceback
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
from setter_support import check_lease,sha,require
from instrumentation import observed_import_function,scalar_stats
from vvd_normals import decode_lod0_normals
import bpy
import numpy as np

EXPECTED={'hair.smd':(8011,34332),'Hat.smd':(1650,8370)}
def array_hash(value):return sha(np.asarray(value).tobytes())
def mesh_arrays(mesh):
    co=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',co)
    ids=np.empty(len(mesh.loops),np.int32);mesh.loops.foreach_get('vertex_index',ids)
    return co.reshape((-1,3)),ids
def corner_array(mesh):
    result=np.empty(len(mesh.loops)*3,np.float32);mesh.corner_normals.foreach_get('vector',result);return result.reshape((-1,3))
def distances(left,right):return np.linalg.norm(np.asarray(left,dtype=np.float64)-np.asarray(right,dtype=np.float64),axis=1)
def write(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,allow_nan=False,separators=(',',':'));f.write('\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--lease',type=Path,required=True)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);lease,files=check_lease(args.lease,__file__)
    require(Path(bpy.app.binary_path).resolve()==files['blender_exe'],'Actual Blender binary differs')
    require(not bpy.data.filepath and bpy.context.preferences.filepaths.use_scripts_auto_execute is False and bpy.app.online_access is False,'Factory/no-file/offline/disabled-autoexec context required')
    target=Path(lease['private_output']);require(not target.exists() and target.parent.is_dir(),'Fresh private destination required')
    saved=json.loads(files['saved_capture'].read_bytes());require(saved['format']=='has_private_blender_normal_intermediates_2','Saved capture format differs')
    saved_by_name={o['name']:o for o in saved['objects']};require(set(saved_by_name)==set(EXPECTED),'Exact two saved logical models required')
    os.environ['NO_BPY']='1';sourceio=Path(lease['sourceio_root'])
    spec=importlib.util.spec_from_file_location('SourceIO',sourceio/'__init__.py',submodule_search_locations=[str(sourceio)])
    package=importlib.util.module_from_spec(spec);sys.modules['SourceIO']=package;spec.loader.exec_module(package)
    from SourceIO.library.utils import MemoryBuffer
    from SourceIO.library.models.mdl.v49 import MdlV49
    from SourceIO.library.models.vvd import Vvd
    from SourceIO.library.models.vtx import open_vtx
    from SourceIO.blender_bindings.operators.import_settings_base import ModelOptions
    from SourceIO.blender_bindings.models.common import merge_meshes
    module=importlib.import_module('SourceIO.blender_bindings.models.mdl49.import_mdl')
    require(Path(module.__file__).resolve()==files['importer'],'Actual importer module differs')
    factory,ast_proof=observed_import_function(files['importer'].read_text(encoding='utf-8'))
    native_bytes=files['vvd'].read_bytes();mdl_bytes=files['mdl'].read_bytes();vtx_bytes=files['vtx'].read_bytes()
    independent=decode_lod0_normals(native_bytes,expected_checksum=int.from_bytes(mdl_bytes[8:12],'little'))
    raw_normals=np.asarray(independent['normals'],dtype=np.float32)
    class VTXBuffer(MemoryBuffer):
        def seek(self,*a):
            import struct
            try:return super().seek(*a)
            except BufferError as e:raise struct.error(str(e)) from e
    class NoMaterialIO:
        def check(self,path):return False
    def inputs():
        mdl=MdlV49.from_buffer(MemoryBuffer(mdl_bytes));vvd=Vvd.from_buffer(MemoryBuffer(native_bytes));vtx=open_vtx(VTXBuffer(vtx_bytes))
        require(vtx is not None and mdl.header.checksum==vvd.header.checksum==vtx.header.checksum,'Native family checksums differ')
        models=[m for b in mdl.body_parts for m in b.models if m.vertex_count]
        require({m.name for m in models}==set(EXPECTED) and len(models)==2 and all(not m.has_flexes and not m.has_eyeballs for m in models),'Exact no-morph/no-eyeball model profile required')
        require(not vvd.extra_data,'Exact UV0 profile required')
        require(np.asarray(vvd.lod_data[0]['normal'],dtype=np.float32).tobytes()==raw_normals.tobytes(),'SourceIO VVD decoded normal words differ from independent raw parser')
        options=ModelOptions.default();options.scale=.01905
        for key in ('import_textures','create_flex_drivers','bodygroup_vis_switches','bodygroup_grouping','generate_wrinkle_map_node_group','import_physics','import_animations','import_include_animations','load_refpose'):setattr(options,key,False)
        return mdl,vvd,vtx,options
    # Factory-created default objects only; no blend or owner scene was loaded.
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    records={};summaries={};original_refs={};error=None
    def payload(model,mesh,vertices,mapping):
        name=model.name;require(name in EXPECTED,'Unexpected logical model')
        ids=int(model.vertex_offset)+np.asarray(mapping,dtype=np.int64)
        require(len(ids)==len(mesh.vertices) and ids.min()>=0 and ids.max()<len(raw_normals),'Exact bounded native vertex identity required')
        normals=np.asarray(vertices['normal'],dtype=np.float32).copy();expected=raw_normals[ids]
        require(normals.tobytes()==expected.tobytes(),'Setter input differs from independent native normal words')
        co,loops=mesh_arrays(mesh);require((len(co),len(loops))==EXPECTED[name],'Expected mesh cardinality differs')
        require(np.array_equal(co,np.asarray(vertices['vertex']*.01905,dtype=np.float32)),'SourceIO point mapping differs')
        return ids,normals,co,loops
    def observe(phase,model,obj,mesh,vertices,mapping):
        name=model.name
        if phase=='before_setter':
            ids,normals,co,loops=payload(model,mesh,vertices,mapping)
            require(name not in records,'Logical model repeated')
            records[name]={'source_lod0_vertex_indices':ids.tolist(),'source_raw_vertex_indices':[independent['raw_vertex_indices'][int(i)] for i in ids],'setter_payload':normals.tolist(),'initial_vertices':co.tolist(),'initial_corner_indices':loops.tolist(),'stages':{}}
            original_refs[name]=(normals,co,loops)
            summaries[name]={'setter_input_word_exact':True,'vertices':len(co),'corners':len(loops),'stages':{}}
            return
        normals,initial_co,initial_loops=original_refs[name];co,loops=mesh_arrays(mesh)
        stable=np.array_equal(co,initial_co) and np.array_equal(loops,initial_loops)
        current=corner_array(mesh)
        info={'topology_and_positions_exact':bool(stable),'corner_normals_sha256':array_hash(current),'has_custom_normals':getattr(mesh,'has_custom_normals',None)}
        if stable:info['setter_payload_to_corner_readback']=scalar_stats(distances(normals[loops],current).tolist())
        records[name]['stages'][phase]={'vertices':co.tolist(),'corner_vertex_indices':loops.tolist(),'corner_normals':current.tolist()}
        summaries[name]['stages'][phase]=info
    namespace=dict(module.__dict__);namespace['_HAS_NORMAL_OBSERVER']=observe
    exec(compile(factory,str(files['importer'])+'[HAS observer]','exec'),namespace)
    try:
        mdl,vvd,vtx,options=inputs();observed=namespace['import_model'](NoMaterialIO(),mdl,vtx,vvd,options)
        require(set(records)==set(EXPECTED) and all(set(r['stages'])=={'after_setter','before_validate','after_validate'} for r in records.values()),'Complete observer boundaries required')
        # Replay the original function without intermediate normal-property reads.
        mdl2,vvd2,vtx2,options2=inputs();control=module.import_model(NoMaterialIO(),mdl2,vtx2,vvd2,options2)
        logical=[m for b in mdl2.body_parts for m in b.models if m.vertex_count]
        require(len(control.objects)==len(observed.objects)==len(logical)==2,'Control object count differs')
        for model,obj in zip(logical,control.objects):
            name=model.name;co,loops=mesh_arrays(obj.data);current=corner_array(obj.data)
            after=records[name]['stages']['after_validate'];stable=np.array_equal(co,np.asarray(after['vertices'],np.float32)) and np.array_equal(loops,np.asarray(after['corner_vertex_indices'],np.int32))
            neutral=stable and current.tobytes()==np.asarray(after['corner_normals'],np.float32).tobytes()
            old=saved_by_name[name];saved_geometry=np.array_equal(co,np.asarray(old['vertices'],np.float32)) and np.array_equal(loops,np.asarray(old['corner_vertex_indices'],np.int32))
            summaries[name]['observer_control_geometry_exact']=bool(stable);summaries[name]['observer_control_normals_word_exact']=bool(neutral)
            summaries[name]['saved_geometry_exact']=bool(saved_geometry)
            if saved_geometry:summaries[name]['control_vs_saved_corner_readback']=scalar_stats(distances(current,np.asarray(old['corner_normals_stored_snapshot'],np.float32)).tolist())
            records[name]['unobserved_control']={'vertices':co.tolist(),'corner_vertex_indices':loops.tolist(),'corner_normals':current.tolist()}
        require(all(v['observer_control_normals_word_exact'] and v['saved_geometry_exact'] for v in summaries.values()),'Observation/control/saved topology join refused')
    except BaseException as e:
        error={'type':type(e).__name__,'reason':str(e)};failure_trace=traceback.format_exc()
    check_lease(args.lease,__file__)
    target.mkdir()
    private={'format':'has_private_sourceio_setter_probe_1','models':records,'error':error,'ast_proof':ast_proof}
    raw=(json.dumps(private,allow_nan=False,separators=(',',':'))+'\n').encode();require(len(raw)<=96*1024*1024,'Private probe over budget')
    (target/'PRIVATE_SETTER.json').write_bytes(raw)
    if error:(target/'PRIVATE_FAILURE.log').write_text(failure_trace,encoding='utf-8')
    status='SETTER_BOUNDARIES_MEASURED' if error is None else 'SETTER_IMPORT_REPLAY_FAILED'
    public={'format':'has_sourceio_setter_boundary_probe_1','status':status,'coordinate_space':'SourceIO/Blender mesh-local, before armature/object/Y-up transport','models':summaries,'private_sha256':sha(raw),'private_bytes':len(raw),'ast_observer_inverse':ast_proof,'error_type':error['type'] if error else None,'files_unchanged':True,'SourceIO_import_executed':True,'original_importer_patched_on_disk':False,'GLB_exported':False,'blend_saved':False,'material_resources_read':False,'normal_fidelity':'FAILED_UNQUALIFIED; this observer does not repair original rawGLB2e-5 failure','causal_limit':'Actual source input, immediate API read-back, later validate read-back and unobserved replay control are separate. This does not prove a particular Blender encoder implementation caused a difference.'}
    write(target/'PUBLIC_SETTER.json',public);print('HAS_SETTER_PROBE '+json.dumps(public));return 0 if error is None else 1
if __name__=='__main__':raise SystemExit(main())
