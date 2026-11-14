"""Main-owned helper preview checks; defaults contain no native/cache dependency.

Every Godot invocation uses an exact main-source snapshot with no overlay and a
unique profile. The report distinguishes committed from uncommitted main bytes;
this is not literal res://main or a prototype-source acceptance claim.
"""
from pathlib import Path, PureWindowsPath
import argparse, hashlib, importlib.util, json, os, shutil, stat, subprocess, sys, time, uuid
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PYTHONW=PYTHON.with_name('pythonw.exe')
GODOT=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
RUNTIMES={str(PYTHON):'03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9',str(PYTHONW):'2bea4fc941b7d9436afa1be8cb46551c0694deed23b3fec87b969054238be099',str(GODOT):'63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'}
TREES=('src','tests','tools','data','examples')
TOP=('project.godot','main.tscn','run.py','launch.pyw','dependencies.json')
RUNTIME_FILES=['src/'+n+'.gd'for n in ['app','physics_editor','pose_editor','secondary_helper_editor','source_bone_bindings','wind_review','pending_helper_preview','pending_helper_wind_player','wind_helper_bridge','wind_helper_runtime','wind_helper_candidate']]+['tools/'+n+'.py'for n in ['wind_helper_preview','wind_preview_controller','wind_preview_owned','wind_preview_worker']]
TEST_FILES=['tests/'+n for n in ['helper_preview_gpu_common.gd','helper_preview_gpu.gd','helper_preview_gpu_peers.gd','helper_preview_gpu_native.gd','helper_preview_integration_cpu.gd','wind_helper_candidate_cpu.gd','helper_preview_fixtures.py','helper_preview_transport_cpu.py','verify_helper_preview.py','test_helper_preview_driver.py']]
GPU=[('focused','tests/helper_preview_gpu.gd',221),('peers','tests/helper_preview_gpu_peers.gd',45)]
BAD=('ERROR:','WARNING:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','resources still in use','Orphan StringName:','unclaimed string names','Pages in use exist at exit')
CONTEXTS=('main_source_snapshot','main_working_source_snapshot')

def require(value,message):
    if not value:raise RuntimeError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded(value):return(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def relative(name):
    require(isinstance(name,str)and name and '\\'not in name,'Canonical relative source path required')
    p=Path(name);w=PureWindowsPath(name)
    require(not p.is_absolute()and not w.drive and all(x not in ('','.','..')and ':'not in x for x in name.split('/')),'Unsafe relative source path: '+name)
    return p

def owned(path,boundary,allow_equal=False):
    path=Path(path).absolute();boundary=Path(boundary).absolute()
    require(all(':'not in part for part in path.parts if part!=path.anchor),'Alternate data stream path refused')
    require((allow_equal or path!=boundary)and '..'not in path.parts and path.resolve().is_relative_to(boundary.resolve()),'Path escapes owned boundary: '+str(path))
    for item in(path,*path.parents):
        if item.exists():
            s=item.lstat();require(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400,'Link/reparse path refused: '+str(item))
        if item==boundary:break
    return path

def identity(path):
    p=Path(path);s=p.stat();return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def records_unchanged(records):
    try:return all(Path(p).is_file()and identity(p)==value for p,value in records.items())
    except (OSError,ValueError):return False
def source_manifest(root):
    root=Path(root).absolute();result={}
    for tree in TREES:
        base=root/tree
        if not base.exists():continue
        for p in sorted(base.rglob('*')):
            owned(p,root)
            if p.is_file()and p.suffix!='.pyc'and '__pycache__'not in p.parts:result[p.relative_to(root).as_posix()]=identity(p)
    for name in TOP:
        p=root/name
        if p.is_file():owned(p,root);result[name]=identity(p)
    return result

def validate_port(root,allow_eol=False):
    root=Path(root);p=owned(root/'tests/helper_preview_port_files.json',root)
    require(p.is_file(),'Reviewed helper preview port manifest is not installed')
    doc=json.loads(p.read_bytes());require(doc.get('format')=='has_helper_preview_main_port_files_1'and isinstance(doc.get('files'),list),'Invalid reviewed helper port manifest')
    seen=set();proof={}
    for row in doc['files']:
        name=row.get('path');relative(name);require(name not in seen,'Repeated reviewed port source: '+name);seen.add(name)
        file=owned(root/name,root);require(file.is_file(),'Missing reviewed helper main source: '+name)
        raw=file.read_bytes();actual=hashlib.sha256(raw).hexdigest();exact=actual==row.get('sha256')
        normalized=bool(allow_eol and file.suffix in('.gd','.py','.tscn','.godot','.json')and hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()==row.get('lf_sha256'))
        require(exact or normalized,'Unreviewed helper main bytes: '+name)
        proof[name]=dict(actual_sha256=actual,reviewed_sha256=row['sha256'],reconstruction='exact bytes'if exact else'explicit --allow-checkout-eol; CRLF-to-LF only')
    require(set(RUNTIME_FILES+TEST_FILES).issubset(seen),'Reviewed helper port manifest omits required main runtime/test source')
    return proof

def copy_snapshot(root,project,before):
    root=Path(root).absolute();project=owned(project,root/'output');require(not project.exists(),'Snapshot destination must be fresh')
    project.mkdir(parents=True,exist_ok=False)
    for name,value in before.items():
        src=owned(root/relative(name),root);dst=owned(project/relative(name),project);require(identity(src)==value,'Source changed before snapshot copy: '+name)
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        require(identity(dst)==value,'Snapshot bytes/size/mtime differ: '+name)
    require(source_manifest(root)==before,'Main source set changed during snapshot')
    copied=source_manifest(project);require(copied==before,'Snapshot source set differs from exact main input')
    return copied

def write(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def functional_status(raw):
    chunks=raw.split(b'\0');kept=[];ignored=[];index=0
    def generated(name):return Path(name).suffix=='.pyc'or '__pycache__'in Path(name).parts
    while index<len(chunks):
        part=chunks[index];index+=1
        if not part:continue
        require(len(part)>=4 and part[2:3]==b' ','Malformed Git porcelain source status')
        state=part[:2].decode('ascii');names=[part[3:].decode('utf-8','surrogateescape')]
        if 'R'in state or 'C'in state:
            require(index<len(chunks)and chunks[index],'Missing Git renamed source path')
            names.append(chunks[index].decode('utf-8','surrogateescape'));index+=1
        row=dict(status=state,paths=names)
        (ignored if all(generated(name)for name in names)else kept).append(row)
    return kept,ignored

def source_state(root,allow_working):
    revision=git(root,'rev-parse','HEAD')
    raw=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all','--',*TREES,*TOP],cwd=root)
    status,ignored=functional_status(raw)
    require(not status or allow_working,'Functional working tree is uncommitted; use explicit --allow-working-source for a labeled working-source check')
    require(not(Path(root)/'override.cfg').exists()and not(Path(root)/'project.binary').exists(),'Main startup override/binary settings need explicit separate review; will not silently replace them')
    return dict(revision=revision,working_status=status,ignored_generated_status=ignored,source_context='main_working_source_snapshot'if status else'main_source_snapshot')

def invoke(args,project,target,timeout,graphical=False):
    target.mkdir(parents=True,exist_ok=False);write(target/'command.json',args)
    env=os.environ.copy();env.update(HYBRID_PYTHON=str(PYTHON),HYBRID_GODOT=str(GODOT),PYTHONDONTWRITEBYTECODE='1')
    process=subprocess.Popen(args,cwd=project,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
    write(target/'launch.json',dict(pid=process.pid,started_ns=time.time_ns(),graphical=graphical,retained_Popen=True))
    timed_out=False
    try:out,err=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:timed_out=True;process.kill();out,err=process.communicate()
    (target/'stdout.log').write_text(out,encoding='utf-8');(target/'stderr.log').write_text(err,encoding='utf-8')
    engines=sorted(target.rglob('engine.log'));combined=out+err+''.join('\n'+log.read_text(encoding='utf-8',errors='replace')for log in engines)
    errors=[x for x in BAD if x in combined]
    return dict(exit=process.returncode,timed_out=timed_out,retained_Popen_reaped=process.poll()is not None,error_markers=errors)

def command(project,script,target,arguments,graphical=False):
    project=Path(project).absolute();path=project/'run.py'
    run=load_module(path,'helper_preview_snapshot_run_'+uuid.uuid4().hex)
    require(Path(run.ROOT).resolve()==project.resolve()and Path(run.__file__).resolve()==path.resolve(),'Runner differs from the exact staged main source')
    prior=os.environ.get('HYBRID_GODOT')
    try:
        os.environ['HYBRID_GODOT']=str(GODOT)
        args=run.command(script,headless=not graphical,extra=['--audio-driver','Dummy','--log-file',str(target/'engine.log'),'--',*map(str,arguments)])
    finally:
        if prior is None:os.environ.pop('HYBRID_GODOT',None)
        else:os.environ['HYBRID_GODOT']=prior
    require(args.count('--path')==1 and Path(args[args.index('--path')+1]).resolve()==project.resolve(),'Actual command path differs from main snapshot')
    if graphical:
        require(args.count('--receipt')==1 and Path(args[0]).resolve()==PYTHONW.resolve()and Path(args[1]).resolve()==(project/'tools/private_desktop.py').resolve(),'Approved private Windows runner required; no fallback')
        boundary=args.index('--')
        require(Path(args[boundary+1]).resolve()==GODOT.resolve(),'Private runner selected a different engine')
        args[args.index('--receipt')+1]=str(target/'private-receipt.json')
    else:require(Path(args[0]).resolve()==GODOT.resolve()and '--headless'in args,'Approved headless engine required')
    return args

def result_binding(result,expected,label,graphical=False):
    if not isinstance(result,dict)or result.get('mode')!=label:return False
    actual=result.get('metrics')if graphical else result
    if not isinstance(actual,dict):return False
    for key in('source_context','source_manifest_sha256','main_revision'):
        if actual.get(key)!=expected.get(key):return False
    for key in('main_root','project_root'):
        value=actual.get(key,'')
        if not isinstance(value,str)or not Path(value).is_absolute()or Path(value).resolve()!=Path(expected[key]).resolve():return False
    return True

def run_job(project,label,script,args,count,expected,graphical=False,timeout=180):
    target=owned(project/'output/helper-preview-qa'/label,project/'output');cmd=command(project,script,target,args,graphical)
    row=invoke(cmd,project,target,timeout,graphical)
    result_path=target/'result.json';result=json.loads(result_path.read_bytes())if result_path.is_file()else None
    actual_count=len(result['checks'])if result and isinstance(result.get('checks'),list)else result.get('checks')if result else None
    failures=result.get('failures')if result else None
    clean=True;receipt=None
    if graphical:
        receipt_path=target/'private-receipt.json';receipt=json.loads(receipt_path.read_bytes())if receipt_path.is_file()else{}
        clean=receipt.get('exit')==0 and receipt.get('job_closed')is True and receipt.get('desktop_closed')is True and receipt.get('child_desktop_confirmed')is True and receipt.get('private_window_seen')is True and receipt.get('foreground_child_observed')is False and receipt.get('desktop_switch_requested')is False
    bound=result_binding(result,expected,label,graphical)
    passed=bound and row['exit']==0 and not row['timed_out']and row['retained_Popen_reaped']and not row['error_markers']and clean and actual_count==count and failures in(0,[])
    row.update(label=label,script=script,checks=actual_count,expected_checks=count,failures=failures,private_receipt=receipt,clean_private_receipt=clean if graphical else None,result_source_context_bound=bound,passed=passed)
    write(target/'verification.json',row);return row

def native_plan(root,manifest=None):
    path=owned(root/'tests/native_fixture_plans.py',root);resolver=load_module(path,'helper_preview_native_resolver')
    require(Path(resolver.ROOT).resolve()==Path(root).resolve(),'Native resolver has another main root')
    return resolver.wind_review_native_plans(manifest)

def stage_native(project,plan):
    row=plan['inputs']['backhair'];folder=owned(project/'output/helper-preview-native/backhair',project/'output');folder.mkdir(parents=True,exist_ok=False)
    staged={}
    for key in('source','parameters'):
        src=Path(row[key]);require(identity(src)==row[key+'_identity'],'Native original changed before copy: '+key)
        dst=folder/('scene.glb'if key=='source'else'parameters.json');shutil.copy2(src,dst)
        require(identity(dst)==row[key+'_identity'],'Native copy lost exact hash/size/mtime: '+key)
        staged[key]=str(dst);staged[key+'_identity']=identity(dst)
    return staged

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['prepare','cpu','graphical'],required=True);parser.add_argument('--native',action='store_true');parser.add_argument('--inputs-manifest',type=Path);parser.add_argument('--lease-confirmed',action='store_true');parser.add_argument('--allow-working-source',action='store_true');parser.add_argument('--allow-checkout-eol',action='store_true');opt=parser.parse_args(argv)
    require(os.name=='nt'and Path(sys.executable).resolve()==PYTHON.resolve(),'Approved Windows Python executable required')
    require((ROOT/'project.godot').is_file(),'Install this reviewed driver in the actual main tests directory')
    require(opt.mode!='graphical'or opt.lease_confirmed,'Graphical mode needs the coordinator exclusive-lease assertion')
    family=owned(ROOT/'output/helper-preview',ROOT/'output');family.mkdir(parents=True,exist_ok=True);folder=owned(family/(opt.mode+'-'+str(time.time_ns())+'-'+uuid.uuid4().hex[:8]),family);folder.mkdir(exist_ok=False)
    before=None;runtimes={};state=None;project=None;runtime_before=None;native=None;originals={};rows=[];error=None;passed=False;gpu_attempted=False;fixtures={};gates={};extras={};fixture_proof={};requests={};staged_records={}
    try:
        before=source_manifest(ROOT);runtimes={p:identity(p)for p,expected in RUNTIMES.items()}
        require(all(value['sha256']==RUNTIMES[p]for p,value in runtimes.items()),'Approved runtime fingerprint differs')
        state=source_state(ROOT,opt.allow_working_source);bindings=validate_port(ROOT,opt.allow_checkout_eol);source_sha=digest(before)
        write(folder/'main-source-before.json',before);write(folder/'source-state-before.json',state);write(folder/'reviewed-main-bindings.json',bindings)
        project=folder/'Studio';copy_snapshot(ROOT,project,before)
        profile='HAS Main Helper Preview '+folder.name
        write(project/'helper-preview-source-context.json',dict(**state,main_revision=state['revision'],main_root=str(ROOT),project_root=str(project),source_manifest_sha256=source_sha,overlay_files=0))
        extras[str(project/'helper-preview-source-context.json')]=identity(project/'helper-preview-source-context.json')
        (project/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
        extras[str(project/'override.cfg')]=identity(project/'override.cfg')
        config_base=dict(**state,main_revision=state['revision'],main_root=str(ROOT),source_manifest_sha256=source_sha,project_root=str(project),code_root=str(project),python=str(PYTHON),profile=profile)
        if opt.native:
            native=native_plan(ROOT,opt.inputs_manifest);originals={native['manifest']:native['manifest_identity']}
            for item in native['inputs'].values():
                for key in('source','parameters'):originals[item[key]]=item[key+'_identity']
            staged=stage_native(project,native);staged_records={staged[key]:identity(staged[key])for key in('source','parameters')}
        else:staged=None
        sys.path.insert(0,str(project/'tests'))
        factory=load_module(project/'tests/helper_preview_fixtures.py','helper_preview_owned_fixtures')
        fixtures=factory.build(project,project/'output/helper-preview-fixtures',{name:value['sha256']for name,value in before.items()},staged)
        plan_path=Path(fixtures['plan_path']);plan=json.loads(plan_path.read_bytes());plan.update(config_base)
        plan_path.write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        fixture_proof={str(p):identity(p)for p in (project/'output/helper-preview-fixtures').rglob('*')if p.is_file()}
        runtime_before=source_manifest(project);require(runtime_before==before,'Preparation changed functional main snapshot bytes before execution')
        write(folder/'snapshot-source-before.json',runtime_before);write(folder/'fixture-identities.json',fixture_proof)
        if opt.mode=='prepare':
            for script in['src/app.gd',*['tests/'+n for n in ['helper_preview_gpu.gd','helper_preview_gpu_peers.gd','helper_preview_gpu_native.gd','wind_helper_candidate_cpu.gd','helper_preview_integration_cpu.gd']]]:
                target=project/'output/helper-preview-qa'/(Path(script).stem+'-parse');cmd=[str(GODOT),'--headless','--audio-driver','Dummy','--path',str(project),'--log-file',str(target/'engine.log'),'--script',script,'--check-only'];row=invoke(cmd,project,target,45);row['passed']=row['exit']==0 and not row['timed_out']and row['retained_Popen_reaped']and not row['error_markers'];rows.append(row);write(target/'verification.json',row);require(row['passed'],'Main snapshot parse failed: '+script)
        elif opt.mode=='cpu':
            target=project/'output/helper-preview-qa/transport';cmd=[str(PYTHON),'-I','-B',str(project/'tests/helper_preview_transport_cpu.py'),str(target)]
            row=invoke(cmd,project,target,30);value=json.loads((target/'result.json').read_bytes())if(target/'result.json').is_file()else{};row.update(label='transport',script='tests/helper_preview_transport_cpu.py',expected_checks=11,failures=value.get('failures'));row['checks']=len(value.get('checks',[]));row['result_source_context_bound']=result_binding(value,config_base,'transport');row['passed']=row['exit']==0 and not row['timed_out']and row['retained_Popen_reaped']and not row['error_markers']and row['result_source_context_bound']and row['checks']==11 and value.get('failures')==[];rows.append(row);write(target/'verification.json',row);require(row['passed'],'Main transport root controls failed')
            result=project/'output/helper-preview-qa/adapter/result.json';row=run_job(project,'adapter','res://tests/wind_helper_candidate_cpu.gd',[plan_path,result],fixtures['expected_adapter_checks'],config_base);rows.append(row);require(row['passed'],'Main imported-binding adapter failed')
            target=project/'output/helper-preview-qa/host';request_path=project/'output/helper-preview-host-request.json';write(request_path,dict(**config_base,folder=str(target),source=fixtures['host_source'],mode='host',headless=True,gpu=False));requests[str(request_path)]=identity(request_path);row=run_job(project,'host','res://tests/helper_preview_integration_cpu.gd',[request_path],69,config_base);rows.append(row);require(row['passed'],'Main helper editor CPU hosting failed')
        else:
            jobs=list(GPU)+([('native','tests/helper_preview_gpu_native.gd',39)]if staged else[])
            for label,script,count in jobs:
                target=project/'output/helper-preview-qa'/label;data=dict(**config_base,folder=str(target),source=fixtures['host_source'],mode=label)
                if label=='native':data.update(source=staged['source'],parameters=staged['parameters'],native_case='backhair-existing-chain',expected_native_sha256=staged['source_identity']['sha256'],expected_native_bytes=staged['source_identity']['bytes'])
                req=project/('output/helper-preview-'+label+'-request.json');write(req,data);requests[str(req)]=identity(req);gpu_attempted=True;row=run_job(project,label,'res://'+script,[req],count,config_base,True,480);rows.append(row);require(row['passed'],'Main graphical helper check failed: '+label)
        passed=True
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    finally:
        gate_errors={}
        def probe(name,call):
            try:gates[name]=bool(call())
            except Exception as exc:gates[name]=False;gate_errors[name]=type(exc).__name__+': '+str(exc)
        try:after=source_manifest(ROOT)
        except Exception as exc:after={'enumeration_error':type(exc).__name__+': '+str(exc)}
        gates['main_sources']=before is not None and before==after
        gates['runtimes']=bool(runtimes)and records_unchanged(runtimes)
        probe('head',lambda:state is not None and git(ROOT,'rev-parse','HEAD')==state['revision'])
        gates['native_originals']=records_unchanged(originals);gates['staged_native_inputs']=records_unchanged(staged_records);gates['published_requests']=records_unchanged(requests)
        if runtime_before is not None:
            probe('snapshot_sources',lambda:source_manifest(project)==runtime_before)
            gates['snapshot_extras']=len(extras)==2 and records_unchanged(extras);gates['fixtures']=bool(fixture_proof)and records_unchanged(fixture_proof)
        if gate_errors:error=(error+'; 'if error else'')+'Preservation probe failed: '+json.dumps(gate_errors)
        passed=passed and all(gates.values());report=dict(format='has_helper_preview_main_verification_1',source_context=state['source_context']if state else'unadmitted',source_state=state,main_root=str(ROOT),actual_res_root=str(project)if project else None,overlay_files=0,mode=opt.mode,native_requested=opt.native,native_inputs_checked=native is not None,native_fidelity=False,graphical_process_attempted=gpu_attempted,gpu_used=True if gpu_attempted and any(r.get('private_receipt',{}).get('private_window_seen')is True and r.get('private_receipt',{}).get('child_desktop_confirmed')is True for r in rows if isinstance(r.get('private_receipt'),dict))else None if gpu_attempted else False,checks=sum(r.get('checks',0)or 0 for r in rows),results=rows,error=error,preservation=gates,passed=passed)
        write(folder/'main-source-after.json',after);write(folder/'verification.json',report)
    print('HELPER_PREVIEW_MAIN '+json.dumps(dict(folder=str(folder),verification=str(folder/'verification.json'),passed=passed,source_context=report['source_context'],mode=opt.mode,native_requested=opt.native,checks=report['checks'])),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
