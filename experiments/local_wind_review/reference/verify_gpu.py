"""Prepare/parse the private Wind Review GPU harness; run only with a released lease.

Default mode never starts graphics, extracts models, converts assets or runs the
new smoke bodies. --run-gpu additionally requires --lease-confirmed.
"""
from pathlib import Path
import argparse
import array
import hashlib
import importlib.util
import json
import math
import os
import shutil
import stat
import subprocess
import sys
import time
import wave

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
STUDIO=BASE/'Studio'
SCRIPTS=['tests/wind_review_gpu_common.gd','tests/wind_review_gpu_motion.gd','tests/wind_review_gpu_lifecycle.gd','tests/wind_review_gpu_primary.gd']
SOURCES={
    'vrm1':('output/compatibility/source-1794448091-467-21644406/scene.glb','a0b095f399e0f7f95c88b91d12e74f8d1816052c1552b9d2dd758ceed8a6b062'),
    'vrm0':('output/compatibility/source-1794448093-218-23395070/scene.glb','3caa50b76d0f481bb7ee66daeb6ebe7485aefb966140321b599ca60d9d464b56'),
    'backhair':('output/back-hair-composition/1794516017604605200/input/scene.glb','4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5'),
}

def require(ok,message):
    if not ok:raise RuntimeError(message)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def guard(path,boundary):
    path=Path(path).absolute();boundary=Path(boundary).resolve()
    require(path.resolve().is_relative_to(boundary),f'Path escaped owned boundary: {path}')
    for candidate in [path,*path.parents]:
        if candidate.exists():
            value=candidate.lstat()
            require(not stat.S_ISLNK(value.st_mode) and not getattr(value,'st_file_attributes',0)&0x400,f'Reparse path refused: {candidate}')
        if candidate.resolve()==boundary:break
    return path

def identity(path):
    path=Path(path);value=path.stat()
    return {'sha256':sha(path),'bytes':value.st_size,'mtime_ns':value.st_mtime_ns}

def write_json(path,value):
    guard(path,BASE);Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def runner():
    spec=importlib.util.spec_from_file_location('wind_review_private_run',STUDIO/'run.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    require(result.ROOT.resolve()==STUDIO.resolve(),'Runner did not bind this isolated prototype')
    return result

def runtime_hashes():
    proof=json.loads((BASE/'runtime-review-reviewfixed.json').read_bytes())
    result={name:sha(STUDIO/name) for name in proof['runtime_files']}
    require(all(result[name]==record['prototype_sha256'] for name,record in proof['runtime_files'].items()),'Frozen runtime changed since headless review fixes')
    return result

def source_manifest():
    names=[p for part in ['src','tests','tools','data','examples'] for p in (STUDIO/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
    names.extend(STUDIO/name for name in ['run.py','project.godot','main.tscn','launch.pyw'])
    return {path.relative_to(STUDIO).as_posix():identity(path) for path in sorted(names)}

def originals():
    result={}
    for label,(name,expected) in SOURCES.items():
        path=guard(ROOT/name,ROOT/'output');parameters=guard(path.with_name('parameters.json'),ROOT/'output')
        require(path.is_file() and sha(path)==expected,f'Wrong/missing checksum-bound native source: {label}')
        require(parameters.is_file(),f'Native source needs parameters.json: {label}')
        result[label]={'source':str(path),'parameters':str(parameters),'source_identity':identity(path),'parameters_identity':identity(parameters)}
    return result

def verify_originals(before):
    return all(identity(item['source'])==item['source_identity'] and identity(item['parameters'])==item['parameters_identity'] for item in before.values())

def parse_checks(folder,run):
    records=[]
    for script in SCRIPTS:
        args=run.command(script,headless=True,extra=['--check-only','--log-file',str(folder/(Path(script).stem+'-parse-engine.log'))])
        process=subprocess.run(args,cwd=STUDIO,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=40)
        text=process.stdout+process.stderr
        path=folder/(Path(script).stem+'-parse.log');path.write_text(text,encoding='utf-8')
        ok=process.returncode==0 and not any(word in text for word in ['ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked'])
        records.append({'script':script,'exit':process.returncode,'passed':ok,'log':str(path),'command':args,'gpu':False})
    return records

def audio(path):
    samples=array.array('h',(int(8000*math.sin(2*math.pi*1000*n/48000)) if 48000<=n<57600 else 0 for n in range(96000)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(path),'wb') as stream:
        stream.setparams((1,2,48000,0,'NONE','not compressed'));stream.writeframes(samples.tobytes())

def stage_native(folder,inputs):
    staged={}
    for label,item in inputs.items():
        target=folder/'inputs'/label;target.mkdir(parents=True)
        source=target/'scene.glb';parameters=target/'parameters.json'
        shutil.copy2(item['source'],source);shutil.copy2(item['parameters'],parameters)
        require(identity(source)==item['source_identity'] and identity(parameters)==item['parameters_identity'],'Native stage failed exact hash/size/mtime copy')
        staged[label]={'source':str(source).replace('\\','/'),'parameters':str(parameters).replace('\\','/')}
    # The retained input has one configured ribbon; add the existing Back hair
    # chain with the unchanged production helper builder, inside this owned run.
    sys.path.insert(0,str(STUDIO/'tools'))
    import secondary_helpers as helpers
    source=Path(staged['backhair']['source']);before=helpers.GLB(source)
    request={'source_sha256':SOURCES['backhair'][1],'node':80,'primitive':1,'component':5,'review_only':True,'use_existing_joints':True,'reviewed':True}
    preview=helpers.preview(source,request)
    require(len(before.springs())==1 and preview['existing_chain']['joint_nodes']==[11,10,9] and len(preview['affected_regions'])==3 and preview['affected_vertices']==1369,'Native ribbon/Back hair identity or shared scope changed')
    result=helpers.build(source,folder/'inputs/backhair-configured',request)
    after=helpers.GLB(result['glb'])
    require(len(after.springs())==2 and after.binary==before.binary and all(after.doc.get(name)==before.doc.get(name) for name in ['meshes','skins','materials','animations','accessors','bufferViews']),'Native preparation changed existing geometry/skin/materials')
    require(result['report']['changed_vertices']==0 and result['report']['source_skin_preserved'],'Back hair preparation did not retain existing weights')
    staged['backhair']['source']=result['glb'].replace('\\','/')
    staged['backhair']['shared_regions']=len(preview['affected_regions']);staged['backhair']['shared_weighted_vertices']=preview['affected_vertices']
    write_json(folder/'native-helper-request.json',request)
    write_json(folder/'native-helper-report.json',result['report'])
    write_json(folder/'staged-native.json',{name:{**row,'identity':identity(row['source'])} for name,row in staged.items()})
    return staged

def execute_gpu(folder,run,inputs):
    staged=stage_native(folder,inputs);tone=folder/'known-tone.wav';audio(tone)
    jobs=[('procedural','tests/wind_review_gpu_motion.gd',{}),('vrm0','tests/wind_review_gpu_motion.gd',staged['vrm0']),('vrm1','tests/wind_review_gpu_motion.gd',staged['vrm1']),('backhair','tests/wind_review_gpu_motion.gd',staged['backhair']),('lifecycle','tests/wind_review_gpu_lifecycle.gd',{}),('primary','tests/wind_review_gpu_primary.gd',{**staged['vrm1'],'raise_y':2.5})]
    records=[]
    for name,script,data in jobs:
        target=folder/name;target.mkdir()
        request={'mode':name,'folder':str(target).replace('\\','/'),'audio':str(tone).replace('\\','/'),**data}
        request_path=target/'request.json';write_json(request_path,request)
        args=run.command(script,extra=['--audio-driver','Dummy','--log-file',str(target/'engine.log'),'--',str(request_path)])
        require('--receipt' in args and 'private_desktop.py' in args[1],'No private Windows desktop; visible fallback refused')
        receipt_path=target/'private-receipt.json';args[args.index('--receipt')+1]=str(receipt_path)
        write_json(target/'command.json',args)
        process=subprocess.run(args,cwd=STUDIO,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=330)
        text=process.stdout+process.stderr;(target/'process.log').write_text(text,encoding='utf-8')
        result=json.loads((target/'result.json').read_bytes()) if (target/'result.json').is_file() else {}
        receipt=json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else {}
        errors=[word for word in ['ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked','unclaimed string names','Object was freed while a signal is being emitted','_set_transient_exclusive_child'] if word in text]
        clean=receipt.get('exit')==0 and receipt.get('child_desktop_confirmed') and not receipt.get('foreground_child_observed',True) and receipt.get('job_closed') and receipt.get('desktop_closed')
        ok=process.returncode==0 and result.get('failures',1)==0 and clean and not errors
        row={'mode':name,'script':script,'exit':process.returncode,'checks':result.get('checks'),'failures':result.get('failures'),'private_receipt':str(receipt_path),'clean_isolation':bool(clean),'error_markers':errors,'passed':bool(ok)}
        write_json(target/'verification.json',row);records.append(row);write_json(folder/'execution-progress.json',records);print(('PASS ' if ok else 'FAIL ')+name)
        if not ok:break
    return records

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-gpu',action='store_true');parser.add_argument('--lease-confirmed',action='store_true');options=parser.parse_args()
    require(not options.run_gpu or options.lease_confirmed,'Do not run graphics before root releases the canonical/review GPU lease')
    require(os.name=='nt','This harness is prepared for the approved Windows private-desktop runtime')
    guard(BASE,ROOT/'output');folder=BASE/('gpu-verification' if options.run_gpu else 'gpu-preparation')/str(time.time_ns());folder.mkdir(parents=True,exist_ok=False)
    before_runtime=runtime_hashes();before_sources=source_manifest();before_inputs=originals();run=runner()
    historical_root=json.loads((BASE/'active-root-raw-sha256.json').read_bytes())
    root_before={name:sha(ROOT/name) for name in historical_root}
    write_json(folder/'source-before.json',before_sources);write_json(folder/'native-originals-before.json',before_inputs)
    parse=parse_checks(folder,run);write_json(folder/'parse-verification.json',parse)
    require(all(row['passed'] for row in parse),f'Harness parse failed; inspect {folder}')
    results=[]
    try:
        if options.run_gpu:results=execute_gpu(folder,run,before_inputs)
    finally:
        if not results and (folder/'execution-progress.json').is_file():results=json.loads((folder/'execution-progress.json').read_bytes())
        after_runtime=runtime_hashes();after_sources=source_manifest();unchanged=verify_originals(before_inputs)
        root_after={name:sha(ROOT/name) for name in root_before}
        root_changes=[name for name in root_before if root_before[name]!=root_after[name]]
        historical_changes=[name for name in root_before if historical_root[name]!=root_before[name]]
        write_json(folder/'active-root-context.json',{'fresh_before':root_before,'fresh_after':root_after,'changes_during_check':root_changes,'different_from_original924_baseline':historical_changes,'note':'Parent-authorized source/test work can advance independently. Historical differences are reported separately; this agent writes only the isolated prototype/harness.'})
        report={'format':'has_wind_review_private_gpu_1','mode':'graphical' if options.run_gpu else 'parse-only','runtime_source_sha256':before_runtime,'test_sha256':{name:sha(STUDIO/name) for name in SCRIPTS},'parse':parse,'results':results,'runtime_unchanged':before_runtime==after_runtime,'all_prototype_sources_hash_size_mtime_unchanged':before_sources==after_sources,'native_originals_unchanged':unchanged,'active_root_functional_changes_during_check':root_changes,'historical_root_baseline_differences':historical_changes,'gpu_used':options.run_gpu,'private_art_uploaded':False,'scope':'Session-only declared-chain local preview. Pending helper-setup preview, permanent group authoring, native jiggle equivalence, owner/device acceptance and all original regression suites remain separate. No movie renders; lifecycle uses real PNG export only.'}
        report['passed']=all(row['passed'] for row in parse) and before_runtime==after_runtime and before_sources==after_sources and unchanged and not root_changes and (not options.run_gpu or len(results)==6 and all(row['passed'] for row in results))
        write_json(folder/'verification.json',report)
        write_json(folder/'source-after.json',after_sources)
    print(json.dumps({'folder':str(folder),'mode':report['mode'],'passed':report['passed'],'gpu_used':report['gpu_used']},indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
