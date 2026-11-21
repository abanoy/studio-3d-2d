"""Root-only historical Junko105 runner. SOURCE ONLY, UNRUN; no Desktop/GPU."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,stat,subprocess,sys,time,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
PINS={"qualified_helpers.py":[26455,"990c37ddca7b1301613f5efc5a7e5a30ce2723369112ef274ee78d2d4dc34087"],"root_native_job.py":[5018,"fe9a9da0b545fbc1c2b21d09e93dd931b52c5a9e4681c5f0d106c3e43d67f34b"],"protocol_checks.py":[10181,"536016ff2bebe36081d72f694bf1af64783802aa52b56c9d5bd66081b6168472"],"gated_headless_worker.py":[6684,"8bbb3f7d8a983a9c8d4837ebb3705ca8a365a863a85c9717ea7a9d324c6e5ed6"],"approved_job_layout.py":[12692,"c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61"]}
KIT=HERE.parents[1]/'output/source-character-parts-headless-protocol-prep-20261121'

def load(name,path,pin):
    for part in reversed((path,*path.parents)):
        s=part.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise RuntimeError('BOOTSTRAP_ALIAS')
    before=path.stat();raw=path.read_bytes();after=path.stat()
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or identity(before)!=identity(after) or len(raw)!=pin[0] or hashlib.sha256(raw).hexdigest()!=pin[1]:raise RuntimeError('BOOTSTRAP_PIN')
    spec=importlib.util.spec_from_loader(name,loader=None);module=importlib.util.module_from_spec(spec)
    module.__file__=str(path);sys.modules[name]=module;exec(compile(raw,str(path),'exec'),module.__dict__);return module

def clean_env(job):
    env=dict(os.environ)
    for key in tuple(env):
        if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(key,None)
    env.update(job['environment_overrides']);env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    return env

def run_case(H,V,J,layout,job,runroot,used,result):
    record=runroot/'jobs'/job['name'];record.mkdir(parents=True,exist_ok=False)
    request={'format':'has_root_junko_gated_request_1','nonce':uuid.uuid4().hex,'record_dir':str(record),
             'job':job,'godot_pin':next(row for row in used if row['path']==job['args'][0])}
    request_path=record/'request.json';H.json_new(request_path,request);request_sha=H.sha(H.read(request_path))
    python=next(row['path'] for row in used if row['path'].lower().endswith('/python.exe'))
    command=[python,'-I','-S','-B','-u',str(HERE/'gated_headless_worker.py'),'--request',str(request_path),'--request-sha256',request_sha]
    row={'name':job['name'],'status':'FAIL','expected_checks':job['expected_checks'],'graphical':False,
         'wrapper_created':False,'job_created':False,'wrapper_reaped':False,'wrapper_handle_closed':False,
         'job_assigned_before_START':False,'START_released':False,'active_zero_before_close':False,'job_closed':False}
    result['jobs'].append(row);process=None;native=None;primary=None;closed=False
    try:
        native=J.RootJob(layout);row['job_created']=True
        with (record/'wrapper-stdout.log').open('xb') as out,(record/'wrapper-stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=record,env=clean_env(job),stdin=subprocess.PIPE,stdout=out,stderr=err,
                                     close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
            row['wrapper_created']=True;row['owner']=native.identity(process)
            native.assign(process);row['job_assigned_before_START']=True
            gate={'format':'has_root_junko_START_1','nonce':request['nonce'],'request_sha256':request_sha,'owner':row['owner']}
            process.stdin.write((json.dumps(gate)+'\n').encode());process.stdin.flush();process.stdin.close();row['START_released']=True
            H.json_new(record/'launch.json',{'command':command,'wrapper_identity':row['owner'],'request_sha256':request_sha,
                       'job_assigned_before_START':True,'kill_on_close':True,'active_process_limit':16,'job_memory_bytes':4294967296,
                       'no_desktop':True,'headless_only':True,'start_ns':time.time_ns()})
            deadline=time.monotonic()+job['timeout_seconds']+20
            while process.poll() is None:
                H.need(time.monotonic()<deadline,'OUTER_HEADLESS_TIMEOUT')
                for path,limit in ((record/'wrapper-stdout.log',262144),(record/'wrapper-stderr.log',262144),
                    (record/'godot-stdout.log',V.MAX_LOG),(record/'godot-stderr.log',V.MAX_LOG),
                    (Path(job['args'][job['args'].index('--log-file')+1]),V.MAX_LOG)):
                    if path.exists():H.need(path.stat().st_size<=limit,'OWNED_LOG_BUDGET')
                time.sleep(.05)
            row['wrapper_exit']=process.wait(timeout=1);row['wrapper_reaped']=True
    except BaseException as error:primary=error;row['error_type']=type(error).__name__;row['error']=str(error)
    finally:
        if process is not None and process.stdin and not process.stdin.closed:
            try:process.stdin.close()
            except BaseException:pass
        if native is not None:
            try:row['pre_termination_accounting']=native.accounting();native.terminate();row['terminate_owned_job_called']=True
            except BaseException as error:row['termination_error']=str(error);primary=primary or error
        if process is not None:
            try:
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
                row['wrapper_exit']=process.returncode;row['wrapper_reaped']=process.returncode is not None
                if row['wrapper_reaped']:process._handle.Close();row['wrapper_handle_closed']=True
            except BaseException as error:row['reap_error']=str(error);primary=primary or error
        if native is not None:
            try:
                deadline=time.monotonic()+10
                while True:
                    state=native.accounting();row['final_accounting']=state
                    if state['active']==0:row['active_zero_before_close']=True;break
                    H.need(time.monotonic()<deadline,'ROOT_JOB_ACTIVE_DESCENDANTS_REMAIN');time.sleep(.05)
            except BaseException as error:row['accounting_error']=str(error);primary=primary or error
            finally:
                try:native.close();row['job_closed']=native.closed
                except BaseException as error:row['job_close_error']=str(error);primary=primary or error
        closed=row['wrapper_reaped'] and row['wrapper_handle_closed'] and row['active_zero_before_close'] and row['job_closed']
        H.json_new(record/'OWNERSHIP.json',{'format':'has_root_headless_ownership_1','closure_proven':closed,
            'phase':'CLOSED_BEFORE_ASSERTION_CHECKS' if closed else 'CLOSURE_UNPROVEN',
            'ownership':{key:value for key,value in row.items() if key!='status'}})
    H.need(closed,'OWNED_HEADLESS_TREE_CLOSURE_UNPROVEN_STOP')
    if primary is not None:raise primary
    H.need(row.get('wrapper_exit')==0 and row['job_assigned_before_START'] and row['START_released'],'GATED_WRAPPER_FAILED')
    receipt=H.parse(H.read(record/'wrapper-receipt.json',limit=65536))
    H.need(receipt.get('format')=='has_root_gated_headless_receipt_1' and receipt.get('status')=='PASS'
           and receipt.get('request_sha256')==request_sha and receipt.get('wrapper_identity')==row['owner']
           and receipt.get('gate_accepted') is True and receipt.get('godot_launched') is True
           and type(receipt.get('godot_exit')) is int and receipt['godot_exit']==0
           and receipt.get('godot_reaped') is True and receipt.get('godot_handle_closed') is True,'EXACT_RETAINED_GODOT_RECEIPT')
    H.need(row['final_accounting']['total']>=2 and row['final_accounting']['terminated_by_limit']==0,'ROOT_JOB_TREE_AND_LIMITS')
    H.need(not H.read(record/'wrapper-stderr.log',limit=262144),'WRAPPER_STDERR')
    value=V.validate_logs(H,job,record)
    row['status']='PASS';row['checks']=value['checks'];row['godot_identity']=receipt['godot_identity']
    H.json_new(record/'CASE_RESULT.json',{'status':'PASS','value':value,'wrapper_receipt_sha256':H.sha(H.read(record/'wrapper-receipt.json'))})
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256',required=True);parser.add_argument('--source-manifest-sha256',required=True)
    parser.add_argument('--root-headless-protocol-confirmed',action='store_true',required=True)
    args=parser.parse_args()
    if os.name!='nt' or sys.version_info[:2]!=(3,13) or sys.flags.optimize or not args.root_headless_protocol_confirmed:raise RuntimeError('ROOT_WINDOWS313_HEADLESS_SCOPE')
    H=load('_root_junko_preservation',HERE/'qualified_helpers.py',PINS['qualified_helpers.py'])
    V=load('_root_junko_protocol_checks',HERE/'protocol_checks.py',PINS['protocol_checks.py'])
    J=load('_root_junko_native_job',HERE/'root_native_job.py',PINS['root_native_job.py'])
    layout=load('_root_junko_approved_layout',HERE/'approved_job_layout.py',PINS['approved_job_layout.py'])
    for value in (args.self_sha256,args.source_manifest_sha256):H.need(re.fullmatch('[0-9a-f]{64}',value) is not None,'EXPLICIT_SOURCE_SHA256')
    H.read(Path(__file__),digest=args.self_sha256);V.source_manifest(H,HERE,(None,args.source_manifest_sha256))
    for name,pin in PINS.items():H.read(HERE/name,*pin)
    protocol,baseline,expected,runtimes,used=V.admit(H,KIT)
    python=next(row for row in used if row['path'].lower().endswith('/python.exe'))
    H.need(Path(sys.executable).resolve()==Path(python['path']).resolve(),'APPROVED_ROOT_PYTHON')
    stage=H.safe(Path(protocol['stage']));runroot=stage/('RootRun-'+str(time.time_ns()));H.safe(runroot,missing=True)
    lane=stage/'root-headless105.lock';token=uuid.uuid4().hex.encode();fd=None;lane_identity=None;owned=False;primary=None
    parent_env=dict(os.environ);reader_inputs=None
    result={'format':'has_root_character_parts105_1','status':'FAIL','historical_revision':'435dc02426a7cdd313e43fe674c9008520845428',
            'protocol_sha256':V.PROTOCOL_PIN[1],'expected_checks':105,'jobs':[],'checks':0,'execution_owner':'Root approved host',
            'source_files_per_studio':1108,'source_input_files':3327,'current_Main_revision_unchanged_claimed':False,
            'Full_qualification_claimed':False,'native_alignment_qualified':False,'bone_following_qualified':False,
            'graphical_or_physical_input_qualified':False,'application_adopted':False,'private_arrays_published':False}
    try:
        H.safe(lane,missing=True);fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(fd,token)==len(token),'OWNED_LOCK_SHORT_WRITE');os.fsync(fd);lane_identity=H.stamp(os.fstat(fd))
        runroot.mkdir(exist_ok=False);owned=True
        for job in protocol['jobs']:
            if job['name']=='reader':reader_inputs=V.copy_reader(H,protocol,runroot)
            value=run_case(H,V,J,layout,job,runroot,used,result);result['checks']+=value['checks']
            H.need(all(row.get('status')=='PASS' and row.get('active_zero_before_close') is True and row.get('job_closed') is True for row in result['jobs']),'PRIOR_CASE_CLOSED_BEFORE_ADVANCE')
        H.need(result['checks']==105 and len(result['jobs'])==3,'EXACT105_SUCCESS')
        result['status']='PASS'
    except BaseException as error:primary=error;result['error_type']=type(error).__name__;result['error']=str(error)
    finally:
        result['all_attempted_jobs_closed']=all(row.get('wrapper_reaped') is True and row.get('wrapper_handle_closed') is True
            and row.get('active_zero_before_close') is True and row.get('job_closed') is True for row in result['jobs'])
        result['parent_environment_unchanged']=dict(os.environ)==parent_env
        try:
            V.preserve_runtime_membership(H,protocol,expected)
            if reader_inputs is not None:H.need(set(V.tree(H,reader_inputs[0]))==reader_inputs[1]|{'reader-result.json'},'READER_INPUT_MEMBERSHIP_CHANGED')
            result['runtime_source_membership_preserved']=True
        except BaseException as error:result['runtime_source_membership_preserved']=False;result['membership_error']=str(error)
        result['preservation_failures']=H.preserve();result['all_admitted_inputs_preserved']=not result['preservation_failures']
        result['owned_lock_removed']=False
        if fd is not None:
            try:
                H.need(result['all_attempted_jobs_closed'] and H.stamp(os.fstat(fd))==lane_identity and H.stamp(lane.lstat())==lane_identity,'OWNED_LOCK_RETAINED')
                os.lseek(fd,0,os.SEEK_SET);H.need(os.read(fd,128)==token,'OWNED_LOCK_TOKEN_CHANGED')
                os.close(fd);fd=None;H.need(H.stamp(lane.lstat())==lane_identity,'OWNED_LOCK_PATH_CHANGED');lane.unlink();result['owned_lock_removed']=True
            except BaseException as error:result['lock_error']=str(error)
            finally:
                if fd is not None:os.close(fd)
        result['owned_lock_retained']=lane_identity is not None and not result['owned_lock_removed']
        if not (result['all_attempted_jobs_closed'] and result['parent_environment_unchanged'] and result['runtime_source_membership_preserved']
                and result['all_admitted_inputs_preserved'] and result['owned_lock_removed']):result['status']='FAIL'
        if owned:
            H.json_new(runroot/'PRIVATE_RESULT.json',result)
            public={key:value for key,value in result.items() if key!='preservation_failures'}
            public['preservation_failure_count']=len(result['preservation_failures']);H.json_new(runroot/'PUBLIC_RESULT.json',public)
            print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(runroot/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if primary is None and result['status']=='PASS' else 1
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status':'PREFLIGHT_REFUSED','error_type':type(error).__name__,'error':str(error)}),flush=True);raise SystemExit(2)
