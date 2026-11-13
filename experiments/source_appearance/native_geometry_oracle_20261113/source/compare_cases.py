"""Independent native base attributes vs twelve accepted GLBs; CPU/metadata only."""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode=True
import native_reader as N
import glb_reference as G
import compare_mesh as C
import inspect_cases as I

TASK,ROOT,PRIOR=I.TASK,I.ROOT,I.PRIOR
RESULTS=PRIOR/'BACKGROUND3-ACTUAL-RESULTS.json'
RESULTS_SHA='8bfa2071c9cc6846c9972d53ce93ce433fd8b46293b9155409fcef00f8f97478'


def preservation_ok(proof):
    return (proof.get('all_archives_stage_bundles_and_reports_preserved') is True
            and proof.get('source_unchanged') is True and proof.get('root_head_before')==proof.get('root_head_after')
            and bool(proof.get('root_head_before')))


def native_mesh_records(m,v,group,model,mesh):
    start=model['vvd_lod0_origin']+mesh['vertex_start']
    N.require(start+mesh['vertex_count']<=len(v['lod0']),'MDL/VVD native mesh range')
    result={}
    for i in range(start,start+mesh['vertex_count']):
        row=v['lod0'][i]
        result[i]={'position':N.source_to_gltf(row['position']), 'normal':N.normal_to_gltf(row['normal']),
                   'uv':row['uv'],'weights':{m['bones'][j]['name']:w for j,w in row['weights'].items()}}
    return result


def derived_meshes(glb):
    references=glb.positions();globals_=glb.globals();result=[]
    for (ni,pi,p),reference in zip(glb.primitives(),references):
        node=glb.data['nodes'][ni];mesh=glb.data['meshes'][node['mesh']]
        N.require(all(w==0 for w in node.get('weights',mesh.get('weights',[]))), 'Base comparison requires actual neutral morph weights')
        skin=glb.data['skins'][node['skin']]
        joints=skin['joints'];binds=glb.accessor(skin['inverseBindMatrices'])
        matrices=[G.mul(globals_[joint],tuple(bind[c*4+r] for r in range(4) for c in range(4))) for joint,bind in zip(joints,binds)]
        normals=glb.accessor(p['attributes']['NORMAL']);uvs=glb.accessor(p['attributes']['TEXCOORD_0'])
        joint_rows=glb.accessor(p['attributes']['JOINTS_0']);weight_rows=glb.accessor(p['attributes']['WEIGHTS_0'])
        indices=[x[0] for x in glb.accessor(p['indices'])]
        N.require(len(indices)%3==0,'GLB triangle index count')
        used=sorted(set(indices));rows={}
        N.require(len(used)==len(reference['positions']),'Independent GLB reference order/count')
        for vertex,position in zip(used,reference['positions']):
            weights={};normal=[0.,0.,0.]
            for slot,w in zip(joint_rows[vertex],weight_rows[vertex]):
                if w==0:continue
                name=glb.data['nodes'][joints[slot]]['name'];weights[name]=weights.get(name,0.)+w
                for r in range(3):normal[r]+=w*sum(matrices[slot][r*4+c]*normals[vertex][c] for c in range(3))
            length=math.sqrt(sum(x*x for x in normal))
            normal=tuple(x/length for x in normal) if length else tuple(normal)
            rows[vertex]={'position':tuple(position),'normal':normal,'uv':uvs[vertex],'weights':weights}
        result.append({'source_node':ni,'source_name':node.get('name',''),'primitive':pi,
                       'material':glb.data['materials'][p['material']].get('name',''),
                       'vertices':rows,'triangles':[tuple(indices[i:i+3]) for i in range(0,len(indices),3)]})
    return result


def main():
    folder=TASK/'comparisons'/str(time.time_ns());folder.mkdir(parents=True,exist_ok=False)
    cpu_command=[sys.executable,'-B','-m','unittest','discover','-s',str(TASK/'source'),'-p','test_*.py','-v']
    cpu=subprocess.run(cpu_command,cwd=ROOT,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    (folder/'cpu.log').write_text(cpu.stdout+cpu.stderr,encoding='utf-8')
    I.write(folder/'cpu.json',{'command':cpu_command,'exit':cpu.returncode,'scope':'30 synthetic CPU checks before actual comparison inputs'})
    N.require(cpu.returncode==0 and 'Ran 30 tests' in cpu.stdout+cpu.stderr,'Synthetic comparison gate failed')
    before_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code={p.name:I.stamp(p) for p in (TASK/'source').glob('*.py')}
    started=time.monotonic();receipt,protected=I.protect()
    N.require(I.sha(RESULTS)==RESULTS_SHA,'Actual accepted fourteen-case evidence differs')
    protected.append(I.stamp(RESULTS));accepted=json.loads(RESULTS.read_bytes())
    native={};native_limits=[]
    for key in ['multi_skin_glove','keiki_tools_chisels']:
        chosen={}
        for extension in ['.mdl','.vvd','.dx90.vtx']:
            matches=[r for r in receipt['staged'] if r['case']==key and r['member'].lower().endswith(extension)]
            N.require(len(matches)==1,'Exact native file scope')
            chosen[extension]=Path(matches[0]['path'])
        m=N.mdl(chosen['.mdl'].read_bytes());v=N.vvd(chosen['.vvd'].read_bytes(),m['checksum'],len(m['bones']))
        try:t=N.vtx(chosen['.dx90.vtx'].read_bytes(),m,v)
        except N.FormatError as error:t=None;native_limits.append({'case':key,'vtx':'UNSUPPORTED_BY_FIRST_LEGACY_READER','reason':str(error)})
        native[key]=(m,v,t,I.sha(chosen['.mdl']))
    results=[]
    proof={'format':'has_independent_native_base_comparison_1','status':'STARTED','root_head_before':before_head,'source':code,
           'synthetic_cpu_checks':30,'protected_before':protected,'native_limits':native_limits,'cases':results,
           'adapter_contract':{'position':'(Source.x, Source.z, -Source.y) * .01905; no fitted transform',
                               'uv':'Source UV unchanged after documented importer/exporter double V flip',
                               'triangle':'Reverse each native VTX triple, preserve cyclic rotation and multiplicity; no orientation fitting',
                               'weights':'Native VVD global bone indices joined by exact MDL names/parents to actual GLB palette',
                               'normals':'Raw native directions recorded separately; no normal equivalence is implied by position/UV/weight match'},
           'runtime_gpu_converter_or_sourceio_imported':False,'decoded_geometry_payloads_written':False,
           'native_flex_shader_jiggle':'UNTESTED'}
    try:
        for accepted_case in accepted['cases']:
            if not accepted_case['expected_success']:continue
            verification=ROOT/accepted_case['verification']['path']
            N.require(I.sha(verification)==accepted_case['verification']['sha256'],'Accepted per-case verification differs')
            prior=json.loads(verification.read_bytes());bundle=verification.parent/'bundle'
            glb_path=bundle/'scene.glb';parameter_path=bundle/'parameters.json'
            N.require(I.sha(glb_path)==accepted_case['glb']['sha256'] and I.sha(parameter_path)==prior['parameters']['sha256'],'Accepted GLB/report differs')
            protected.extend([I.stamp(verification),I.stamp(glb_path),I.stamp(parameter_path)])
            parameters=json.loads(parameter_path.read_bytes());N.require(parameters['scale']==.01905 and parameters['axes']=='Source Z-up to glTF Y-up via Blender exporter','Adapter scale/axes differ from explicit contract')
            m,v,t,mdl_sha=native[accepted_case['case']]
            N.require(parameters['source_sha256']==mdl_sha,'Accepted bundle native MDL binding differs from actual staged input')
            glb=G.GLB(glb_path.read_bytes())
            join=glb.native_bindings(m['bones']);derived=derived_meshes(glb)
            skin=int(accepted_case['selected_skin'] or 0)
            selected=accepted_case['selected_named_bodygroups']
            expected=[]
            for group in m['groups']:
                choice=int(selected.get(group['name'],0));model=group['models'][choice]
                for mesh in model['meshes']:
                    material=m['materials'][m['skins'][skin][mesh['material_column']]]
                    matches=[r for r in derived if r['source_name']==model['name'] and r['material']==material]
                    N.require(len(matches)==1,'Ambiguous native-model/material-to-GLB primitive join')
                    row=matches[0]
                    native_triangles=None;compiled_records=None
                    if t is not None:
                        matching=[r for r in t['meshes'] if (r['group_index'],r['model_index'],r['mesh_index'])==(group['index'],choice,mesh['index'])]
                        N.require(len(matching)==1,'Native VTX/MDL mesh join')
                        native_triangles=matching[0]['triangles'];compiled_records=len(matching[0]['compiled_vertex_records'])
                    records=native_mesh_records(m,v,group,model,mesh)
                    observed=C.compare(records,native_triangles,row['vertices'],row['triangles'])
                    observed.update({'native_group':group['index'],'native_choice':choice,'native_mesh':mesh['index'],
                                     'native_model':model['name'],'native_material_column':mesh['material_column'],
                                     'native_selected_material_table_index':m['skins'][skin][mesh['material_column']],
                                     'actual_material_name':material,'glb_source_node':row['source_node'],'glb_primitive':row['primitive'],
                                     'native_compiled_vertex_records':compiled_records,
                                     'native_zero_normals':sum(sum(x*x for x in r['normal'])==0 for r in records.values())})
                    expected.append(observed)
            N.require(len(expected)==len(derived),'Unexpected active GLB primitive')
            results.append({'case':accepted_case['case'],'variant':accepted_case['variant'],'glb_sha256':I.sha(glb_path),
                            'native_mdl_sha256':parameters['source_sha256'],'selected_skin':skin,'selected_groups':selected,
                            'native_to_glb_join':join,'meshes':expected,
                            'all_base_position_uv_vvd_named_weights_match':all(r['position_uv_vvd_named_weights_match'] for r in expected),
                            'all_supported_attributed_triangles_match':all(r['triangles']=='ATTRIBUTED_ORIENTED_MULTIPLICITY_MATCH' for r in expected) if t is not None else None})
        proof['status']='BOUNDED_COMPARISON_COMPLETE_WITH_EXPLICIT_LIMITS'
    except Exception as error:
        proof['status']='PARTIAL_COMPARISON_FAILED_CLOSED';proof['error_type']=type(error).__name__;proof['error']=str(error)
        raise
    finally:
        proof['protected_after']=[]
        for p in protected:
            try:proof['protected_after'].append(I.stamp(p['path']))
            except (OSError,ValueError) as error:proof['protected_after'].append({'path':p['path'],'preservation_error':str(error)})
        proof['all_archives_stage_bundles_and_reports_preserved']=protected==proof['protected_after']
        proof['source_unchanged']=code=={p.name:I.stamp(p) for p in (TASK/'source').glob('*.py')}
        proof['root_head_after']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        proof['elapsed_seconds']=time.monotonic()-started
        valid_preservation=preservation_ok(proof)
        if not valid_preservation:proof['status']='FAILED_PRESERVATION_RETAIN_ALL'
        I.write(folder/'comparison.json',proof)
        N.require(valid_preservation,'Preservation check failed; retained comparison is not accepted')
    print(json.dumps({'folder':str(folder),'status':proof['status'],'cases':len(results),'base_matches':sum(r['all_base_position_uv_vvd_named_weights_match'] for r in results),'supported_triangle_matches':sum(r['all_supported_attributed_triangles_match'] is True for r in results),'native_limits':native_limits,'preserved':proof['all_archives_stage_bundles_and_reports_preserved'],'seconds':proof['elapsed_seconds']}))


if __name__=='__main__':main()
