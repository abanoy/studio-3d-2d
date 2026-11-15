"""CPU-only inspection against checksum-bound six native files. No extraction/runtime."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode=True
import native_reader as N

TASK=Path(__file__).absolute().parents[1]
ROOT=TASK.parents[1]
PRIOR=ROOT/'output/sfm-next-cases-20261112'
STAGE=PRIOR/'stage'
RECEIPT=PRIOR/'runs/execute-1794542752822327800/verification.json'
PLAN=PRIOR/'plan.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def no_link(path):
    for item in (Path(path),*Path(path).parents):
        if item.exists():
            st=item.lstat()
            N.require(not stat.S_ISLNK(st.st_mode) and not getattr(st,'st_file_attributes',0)&0x400,'Link/reparse path')


def stamp(path):
    path=Path(path).absolute();no_link(path);st=path.stat()
    return {'path':str(path),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(path)}


def write(path,value):
    path=Path(path);N.require(path.resolve().is_relative_to(TASK.resolve()),'Owned output path')
    no_link(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def protect():
    receipts=[stamp(RECEIPT),stamp(PLAN)]
    r=json.loads(RECEIPT.read_bytes());plan=json.loads(PLAN.read_bytes())
    N.require(r['mode']=='execute' and len(r['staged'])==296 and sum(x['bytes'] for x in r['staged'])==181460484,'Exact reviewed resource scope')
    expected=set()
    for item in r['staged']:
        path=Path(item['path']);N.require(path.resolve().is_relative_to(STAGE.resolve()),'Stage member escapes owned original stage')
        actual=stamp(path)
        N.require(all(actual[k]==item[k] for k in ['bytes','mtime_ns','sha256']),'Reviewed staged resource changed')
        receipts.append(actual);expected.add(path.resolve())
    actual_files=set()
    for item in STAGE.rglob('*'):
        no_link(item)
        if item.is_file():actual_files.add(item.resolve())
    N.require(expected==actual_files,'Stage membership changed')
    for case in plan['cases']:
        archive=case['archive'];actual=stamp(archive['path'])
        N.require(all(actual[k]==archive[k] for k in ['bytes','mtime_ns','sha256']),'Original archive changed')
        receipts.append(actual)
    return r,receipts


def inspect(receipt):
    results=[]
    for key in ['multi_skin_glove','keiki_tools_chisels']:
        records=[r for r in receipt['staged'] if r['case']==key]
        chosen={}
        for extension in ['.mdl','.vvd','.dx90.vtx']:
            matches=[r for r in records if r['member'].lower().endswith(extension)]
            N.require(len(matches)==1,'Ambiguous exact native '+extension)
            chosen[extension]=matches[0]
        row={'case':key,'native_inputs':{k:{n:r[n] for n in ['path','bytes','sha256']} for k,r in chosen.items()},'mdl':'UNRUN','vvd':'UNRUN','vtx':'UNRUN'}
        try:
            m=N.mdl(Path(chosen['.mdl']['path']).read_bytes());row['mdl']='PARSED'
            row['native_metadata']={'checksum':m['checksum'],'bones':m['bones'],'materials':m['materials'],'skins':m['skins'],'groups':m['groups']}
            v=N.vvd(Path(chosen['.vvd']['path']).read_bytes(),m['checksum'],len(m['bones']));row['vvd']='PARSED'
            row['vvd_metadata']={k:v[k] for k in ['version','checksum','lod_count','lod_vertex_counts','fixups']}
            lengths=[r['normal_length_squared'] for r in v['lod0']]
            row['vvd_metadata']['normal_observations']={'nonunit_count':sum(abs(x-1)>.02 for x in lengths),'zero_count':sum(x==0 for x in lengths),'length_squared_min':min(lengths),'length_squared_max':max(lengths),'scope':'Finite raw authored values; no normalization fitted into native oracle'}
            t=N.vtx(Path(chosen['.dx90.vtx']['path']).read_bytes(),m,v);row['vtx']='PARSED'
            row['vtx_metadata']={k:t[k] for k in ['version','checksum','layout','hardware_palette_render_equivalence']}
            row['native_meshes']=[{k:x[k] for k in ['group_index','group_name','model_index','model_name','mesh_index','material_column','stripgroups']}|{'triangles':len(x['triangles']),'compiled_vertex_records':len(x['compiled_vertex_records']),'distinct_vvd_rows':len(set(x['compiled_vertex_records'].values()))} for x in t['meshes']]
        except Exception as error:
            row['error_type']=type(error).__name__;row['error']=str(error)
            row['status']='PARTIAL_READER_NO_GUESSED_FORMAT_FALLBACK'
        results.append(row)
    return results


def main():
    folder=TASK/'runs'/str(time.time_ns());folder.mkdir(parents=True,exist_ok=False)
    command=[sys.executable,'-B','-m','unittest','discover','-s',str(TASK/'source'),'-p','test_native_reader.py','-v']
    cpu=subprocess.run(command,capture_output=True,text=True,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    (folder/'cpu.log').write_text(cpu.stdout+cpu.stderr,encoding='utf-8')
    write(folder/'cpu.json',{'command':command,'exit':cpu.returncode,'scope':'Synthetic hand-computed fixtures only, before native geometry read'})
    N.require(cpu.returncode==0 and 'Ran 24 tests' in cpu.stdout+cpu.stderr,'Synthetic CPU gate failed')
    source={p.name:stamp(p) for p in (TASK/'source').glob('*.py')}
    started=time.monotonic();receipt,protected=protect()
    result={'format':'has_independent_native_geometry_inspection_1','status':'STARTED','synthetic_cpu_tests':24,'source':source,'protected_before':protected,'native_runtime_gpu_converter_or_sourceio_imported':False}
    try:
        result['cases']=inspect(receipt)
        result['status']='NATIVE_BASE_FORMAT_PARSE_COMPLETE' if all(r['vtx']=='PARSED' for r in result['cases']) else 'PARTIAL_NATIVE_READER'
    finally:
        result['protected_after']=[]
        for p in protected:
            try:result['protected_after'].append(stamp(p['path']))
            except (OSError,ValueError) as error:result['protected_after'].append({'path':p['path'],'preservation_error':str(error)})
        result['all_original_archive_stage_hashes_stamps_preserved']=protected==result['protected_after']
        result['source_unchanged']=source=={p.name:stamp(p) for p in (TASK/'source').glob('*.py')}
        result['elapsed_seconds']=time.monotonic()-started
        valid_preservation=result['all_original_archive_stage_hashes_stamps_preserved'] and result['source_unchanged']
        if not valid_preservation:result['status']='FAILED_PRESERVATION_RETAIN_ALL'
        write(folder/'inspection.json',result)
        N.require(valid_preservation,'Preservation failed; retained inspection is not accepted')
    print(json.dumps({'folder':str(folder),'status':result['status'],'preserved':result['all_original_archive_stage_hashes_stamps_preserved'],'seconds':result['elapsed_seconds'],'cases':[{k:r.get(k) for k in ['case','mdl','vvd','vtx','error']} for r in result['cases']]}))


if __name__=='__main__':main()
