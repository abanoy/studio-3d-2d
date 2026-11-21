"""Focused generated hair CPU checks;no desktop creation or graphics launch.
Uses the approved Windows Job ABI and a start-gated hidden headless descendant.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,importlib.util,json,os,re,subprocess,sys,time,uuid
from ctypes import wintypes as W
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))


def need(ok,message):
    if not ok:raise RuntimeError(message)


def stamp(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_mode,s.st_nlink,getattr(s,'st_file_attributes',0))


def read(path):
    before=path.stat();raw=path.read_bytes();need(stamp(path.stat())==stamp(before),'Input changed while read');return raw


def sha(raw):return hashlib.sha256(raw).hexdigest()


def process_identity(handle,pid):
    kernel=C.WinDLL('kernel32',use_last_error=True);getid=kernel.GetProcessId;getid.restype=W.DWORD;getid.argtypes=[W.HANDLE]
    times=kernel.GetProcessTimes;times.restype=W.BOOL;times.argtypes=[W.HANDLE,*([C.POINTER(W.FILETIME)]*4)]
    values=[W.FILETIME() for _ in range(4)]
    need(getid(handle)==pid and times(handle,*(C.byref(v) for v in values)),'Retained process identity required')
    return {'pid':pid,'created_100ns':str((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime)}


def child(request_path,digest):
    raw=read(request_path);need(sha(raw)==digest,'Owned request bytes changed');request=json.loads(raw)
    gate=json.loads(sys.stdin.buffer.readline(4097));need(sys.stdin.buffer.read(1)==b'','One start gate and EOF required')
    need(gate=={'sha256':digest,'nonce':request['nonce'],'owner':process_identity(W.HANDLE(-1),os.getpid())},'Assigned child start gate differs')
    command=request['command'];boundary=command.index('--') if '--' in command else len(command)
    need(command[:boundary].count('--headless')==1 and '--script' in command[:boundary]
         and '--editor' not in command[:boundary] and '--import' not in command[:boundary],'Headless script only')
    folder=request_path.parent;process=None;receipt={'status':'FAIL','headless':True,'desktop_created':False}
    try:
        with (folder/'engine-stdout.log').open('xb') as out,(folder/'engine-stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=request['cwd'],env=request['environment'],stdin=subprocess.DEVNULL,
                 stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['engine_identity']=process_identity(process._handle,process.pid);deadline=time.monotonic()+150
            while process.poll() is None:
                need(time.monotonic()<deadline,'Headless CPU timeout')
                need(os.fstat(out.fileno()).st_size<=8*1024*1024 and os.fstat(err.fileno()).st_size<=8*1024*1024,'Bounded engine logs')
                time.sleep(.02)
            receipt['exit']=process.wait(timeout=1);need(receipt['exit']==0,'Headless engine failed');receipt['status']='PASS'
    finally:
        if process is not None:
            if process.poll() is None:process.kill();process.wait(timeout=5)
            receipt['exit']=process.returncode;receipt['engine_reaped']=process.returncode is not None
            process._handle.Close();receipt['engine_handle_closed']=True
        (folder/'child-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return 0 if receipt['status']=='PASS' else 1


def case(folder,name,script,marker,count,extra,attempts):
    from owned_headless_job import OwnedHeadlessJob
    from run import command
    from verify_import_capability import read as guarded_read
    path=ROOT/'tools/private_desktop.py';spec=importlib.util.spec_from_file_location('_settling_job_layout',path)
    layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
    output=folder/name;output.mkdir();data=output/'Data';data.mkdir();env=dict(os.environ)
    for key in tuple(env):
        if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(key,None)
    for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
        target=output/'User'/leaf;target.mkdir(parents=True,exist_ok=True);env[key]=str(target)
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',HYBRID_PYTHON=sys.executable)
    args=command(script,headless=True,extra=['--audio-driver','Dummy','--log-file',str(output/'engine.log'),'--',str(data),*extra])
    need('--receipt' not in args,'No private desktop launcher in CPU lane')
    request={'nonce':uuid.uuid4().hex,'command':args,'cwd':str(ROOT),'environment':env}
    raw=json.dumps(request).encode();request_path=output/'request.json';request_path.write_bytes(raw);digest=sha(raw)
    native=OwnedHeadlessJob(layout);process=None;proof={'name':name,'status':'FAIL','checks':0,'desktop_created':False};primary=None
    attempts.append(proof)
    try:
        with (output/'worker-stdout.log').open('xb') as out,(output/'worker-stderr.log').open('xb') as err:
            process=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--child',str(request_path),'--digest',digest],
                   cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            native.assign(process);owner=native.identity(process)
            process.stdin.write((json.dumps({'sha256':digest,'nonce':request['nonce'],'owner':owner})+'\n').encode());process.stdin.close()
            deadline=time.monotonic()+175
            while process.poll() is None:
                need(time.monotonic()<deadline,'Owned headless worker timeout');time.sleep(.02)
            proof['worker_exit']=process.wait(timeout=1);need(proof['worker_exit']==0,'Headless worker failed')
    except BaseException as error:primary=error;proof['error']=str(error)
    finally:
        if process is not None:
            if process.poll() is None:native.terminate();process.wait(timeout=10)
            proof['worker_reaped']=process.returncode is not None;process._handle.Close();proof['worker_handle_closed']=True
        deadline=time.monotonic()+5
        while native.accounting()['active'] and time.monotonic()<deadline:time.sleep(.02)
        proof['accounting']=native.accounting()
        if proof['accounting']['active']:
            native.terminate();primary=primary or RuntimeError('Headless descendants did not exit')
            deadline=time.monotonic()+5
            while native.accounting()['active'] and time.monotonic()<deadline:time.sleep(.02)
            proof['accounting_after_termination']=native.accounting()
        native.close();proof['job_closed']=True
    try:
        if primary is not None:raise primary
        text='\n'.join(guarded_read(output/name).decode('utf-8','replace') for name in ('engine.log','engine-stdout.log','engine-stderr.log'))
        need(not re.search(r'SCRIPT ERROR|SHADER ERROR|FAIL |ObjectDB instances leaked|^ERROR:',text,re.M),'Engine/assertion error')
        rows=[line[len(marker):] for line in guarded_read(output/'engine-stdout.log').decode().splitlines() if line.startswith(marker)]
        need(len(rows)==1,'One actual result marker required');report=json.loads(rows[0])
        need(type(report.get('checks')) is int and report['checks']==count and report.get('failures')==0,'Exact CPU control count required')
        need(Path(report['user_profile']).is_relative_to(output/'User/Roaming'),'Unique case user profile required')
        proof.update(status='PASS',checks=count,report=report)
    except BaseException as error:primary=error;proof['error']=str(error)
    (output/'result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    if primary is not None:raise primary
    return proof


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--child',type=Path);p.add_argument('--digest');p.add_argument('--output',type=Path);p.add_argument('--existing-source',type=Path);p.add_argument('--region',type=int,nargs=3,metavar=('NODE','PRIMITIVE','COMPONENT'));o=p.parse_args()
    need(os.name=='nt','Owned Windows CPU runner required')
    if o.child:return child(o.child,o.digest)
    from verify_camera_interactions import source_inputs,sources_unchanged
    need(bool(o.existing_source)==bool(o.region),'Existing source and region are required together')
    protected=None
    if o.existing_source:
        o.existing_source=o.existing_source.resolve();protected=(stamp(o.existing_source.stat()),sha(read(o.existing_source)))
    folder=(o.output or ROOT/'output'/('generated-settling-'+str(time.time_ns()))).resolve()
    need(folder.is_relative_to(ROOT/'output') and not folder.exists(),'New owned output folder required');folder.mkdir(parents=True)
    frozen=source_inputs();environment=dict(os.environ);result={'status':'FAIL','cases':[],'graphics_used':False,'desktop_created':False};primary=None
    try:
        case(folder,'unit','tests/generated_secondary_motion_unit.gd','GENERATED_SECONDARY_MOTION_UNIT ',22,[],result['cases'])
        case(folder,'geometry','tests/generated_secondary_settling_smoke.gd','GENERATED_SECONDARY_SETTLING ',11,[],result['cases'])
        case(folder,'preview','tests/generated_secondary_preview_unit.gd','GENERATED_SECONDARY_PREVIEW ',18,[],result['cases'])
        case(folder,'editor','tests/generated_secondary_editor_smoke.gd','GENERATED_SECONDARY_EDITOR ',18,[],result['cases'])
        handoff=folder/'Handoff';handoff.mkdir()
        handoff_pins={}
        for name in ('settled.has','expected.json'):
            raw=read(folder/'editor/Data'/name);(handoff/name).write_bytes(raw);handoff_pins[name]=sha(raw)
        case(folder,'reader','tests/generated_secondary_reader_smoke.gd','GENERATED_SECONDARY_READER ',4,[str(handoff/'settled.has'),str(handoff/'expected.json')],result['cases'])
        need(all(sha(read(handoff/name))==digest for name,digest in handoff_pins.items()),'Cold handoff bytes changed')
        if o.existing_source:case(folder,'existing','tests/generated_secondary_existing_smoke.gd','GENERATED_SECONDARY_EXISTING ',14,[str(o.existing_source),*[str(v) for v in o.region]],result['cases'])
        result['status']='PASS'
    except BaseException as error:primary=error;result['error']=str(error)
    finally:
        result['source_preservation_failures']=sources_unchanged(frozen);result['parent_environment_preserved']=dict(os.environ)==environment
        result['protected_source_preserved']=protected is None or protected==(stamp(o.existing_source.stat()),sha(read(o.existing_source)))
        result['checks']=sum(row.get('checks',0) for row in result['cases'])
        if result['source_preservation_failures'] or not result['parent_environment_preserved'] or not result['protected_source_preserved']:result['status']='FAIL'
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}))
    if primary is not None:raise primary
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
