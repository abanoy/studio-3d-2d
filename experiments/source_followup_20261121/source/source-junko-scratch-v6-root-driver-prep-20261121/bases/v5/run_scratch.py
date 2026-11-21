"""Root-only Body/Dress export-identity component; no app, Full or simulation claim."""
from pathlib import Path,PurePosixPath
import argparse,ast,hashlib,json,math,os,re,stat,struct,subprocess,sys,time,types,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CANDIDATE=ROOT/'output/source-junko-scratch-rest-representation-prep-20261121'
CANDIDATE_SHA='9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015'
BASELINE_SHA='23ea7fe6c4e92c8184f421ce9425173d25c409c49d24dd150e5cafd3966685b2'
TREES=('src','tools','tests','data','examples')
FILES=('project.godot','main.tscn','run.py','launch.pyw','dependencies.json','experiments/reference_body_20261120/run_full.py','experiments/reference_body_20261120/stage_legacy_inputs.py','experiments/reference_body_20261120/verify_units.py','experiments/reference_body_20261120/run_scoped.py','experiments/reference_body_20261120/receipt_provenance.py','experiments/reference_body_20261120/test_receipt_provenance.py')
def need(ok,code):
    if not ok:raise RuntimeError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def rel(name):
    need(type(name)is str and name and '\\' not in name and ':' not in name,'RELATIVE_PATH')
    p=PurePosixPath(name);need(not p.is_absolute() and p.as_posix()==name and all(x not in ('.','..') and x.rstrip(' .')==x for x in p.parts),'CONTAINED_PATH');return Path(*p.parts)
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,getattr(s,'st_file_attributes',0))
def safe(path,missing=False):
    path=Path(os.path.abspath(path))
    for p in (path,*path.parents):
        if missing and not os.path.lexists(p):continue
        s=p.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'ALIAS_REFUSED')
    return path
class Guard:
    def __init__(self):self.rows={}
    def read(self,path,limit=512*1024*1024):
        p=safe(path);s=p.stat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit,'BOUNDED_REGULAR_FILE')
        raw=p.read_bytes();need(signature(s)==signature(p.stat()),'READ_DRIFT')
        row={'identity':list(signature(s)),'bytes':len(raw),'sha256':sha(raw)};key=str(p)
        need(key not in self.rows or self.rows[key]==row,'ADMITTED_INPUT_DRIFT');self.rows[key]=row;return raw
    def preserve(self):
        failures=[]
        for p in list(self.rows):
            try:self.read(Path(p))
            except BaseException as e:failures.append({'path':p,'error_type':type(e).__name__,'error':str(e)})
        return failures
def fresh(path,raw):
    safe(path,missing=True);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:need(f.write(raw)==len(raw),'SHORT_WRITE');f.flush();os.fsync(f.fileno())
def write(path,obj):fresh(path,(json.dumps(obj,indent=2,allow_nan=False)+'\n').encode())
def parse(raw):
    def pairs(rows):
        result={}
        for k,v in rows:need(k not in result,'DUPLICATE_JSON_KEY');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(RuntimeError('NONFINITE_JSON')))
def tree(folder,filtered=False):
    result=[]
    def fail(e):raise e
    for base,dirs,files in os.walk(folder,followlinks=False,onerror=fail):
        for name in list(dirs):
            safe(Path(base)/name)
            if filtered and name in ('.git','__pycache__'):dirs.remove(name)
        for name in files:
            p=Path(base)/name;safe(p)
            if not filtered or p.suffix!='.pyc':result.append(p.relative_to(folder).as_posix())
    need(len(result)==len({n.casefold() for n in result}),'CASE_ALIAS');return set(result)
def domain():
    names=set(FILES)
    for part in TREES:
        names.update(part+'/'+n for n in tree(ROOT/part) if Path(n).suffix!='.pyc' and '__pycache__' not in Path(n).parts)
    return names
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW).strip()
def current_main(G,baseline,revision):
    need(git('rev-parse','HEAD')==revision and domain()==set(baseline) and len(baseline)==1109,'MAIN_REVISION_DOMAIN')
    for name,row in baseline.items():
        path=ROOT/rel(name);raw=G.read(path)
        need(len(raw)==row['bytes'] and sha(raw)==row['sha256'] and path.stat().st_mtime_ns==row['mtime_ns'],'MAIN_SOURCE_PIN')
def packet(G,folder,pin):
    raw=G.read(folder/'SOURCE_PINS.json');need(sha(raw)==pin,'PACKET_PIN');value=parse(raw);names={'SOURCE_PINS.json'}
    for row in value['files']:
        p=rel(row['path']);need(row['path'] not in names,'PACKET_DUPLICATE');names.add(row['path']);b=G.read(folder/p)
        need(len(b)==row['bytes'] and sha(b)==row['sha256'],'PACKET_PAYLOAD')
    need(tree(folder)==names,'PACKET_CLOSURE');return value
def load(G,name,path):
    raw=G.read(path);m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);return m
def profile_env(root):
    env={}
    for k,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp'),('BLENDER_USER_CONFIG','BlenderConfig'),('BLENDER_USER_DATAFILES','BlenderData'),('BLENDER_USER_SCRIPTS','BlenderScripts')]:
        p=root/leaf;p.mkdir(parents=True,exist_ok=True);env[k]=str(p)
    return {**env,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','NO_BPY':'1'}
def clean_env(overrides):
    env=dict(os.environ)
    for k in tuple(env):
        if k.startswith('HYBRID_') or k in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(k,None)
    env.update(overrides);return env
def run_job(G,J,L,stage,job,python,result):
    record=stage/'jobs'/job['name'];record.mkdir(parents=True,exist_ok=False)
    request={'format':'has_junko_stage_a_gated_request_1','record_dir':str(record),'nonce':uuid.uuid4().hex,'python_pin':python,'job':job}
    write(record/'request.json',request);request_sha=sha(G.read(record/'request.json'))
    cmd=[python['path'],'-I','-S','-B','-u',str(HERE/'gated_converter_worker.py'),'--request',str(record/'request.json'),'--request-sha256',request_sha]
    row={'status':'FAIL','wrapper_reaped':False,'wrapper_handle_closed':False,'job_closed':False,'active_zero_before_close':False,'assigned_before_START':False};result['jobs'][job['name']]=row
    child=None;native=None;primary=None
    try:
        native=J.RootJob(L)
        with (record/'wrapper-stdout.log').open('xb') as out,(record/'wrapper-stderr.log').open('xb') as err:
            child=subprocess.Popen(cmd,cwd=record,env=clean_env(job['environment_overrides']),stdin=subprocess.PIPE,stdout=out,stderr=err,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
            row['owner']=native.identity(child);native.assign(child);row['assigned_before_START']=True
            gate={'format':'has_junko_stage_a_START_1','request_sha256':request_sha,'nonce':request['nonce'],'owner':row['owner']}
            child.stdin.write((json.dumps(gate)+'\n').encode());child.stdin.flush();child.stdin.close()
            write(record/'launch.json',{'command':cmd,'request_sha256':request_sha,'assigned_before_START':True,'kill_on_close':True,'active_process_limit':16,'job_memory_bytes':4294967296,'no_Desktop_API':True})
            until=time.monotonic()+job['timeout_seconds']+30
            while child.poll() is None:
                need(time.monotonic()<until,'OUTER_COMPONENT_TIMEOUT')
                for leaf,limit in [('wrapper-stdout.log',262144),('wrapper-stderr.log',262144),('child-stdout.log',16*1024*1024),('child-stderr.log',16*1024*1024)]:
                    p=record/leaf
                    if p.exists():need(p.stat().st_size<=limit,'OWNED_LOG_BUDGET')
                log=Path(job.get('conversion_log',record/'not-a-conversion.log'))
                if log.exists():need(log.stat().st_size<=64*1024*1024,'CONVERSION_LOG_BUDGET')
                time.sleep(.05)
            row['wrapper_exit']=child.wait(timeout=1)
    except BaseException as e:primary=e;row['error_type']=type(e).__name__
    finally:
        if child is not None and child.stdin and not child.stdin.closed:child.stdin.close()
        if native is not None:
            try:row['pre_termination_accounting']=native.accounting();native.terminate()
            except BaseException as e:primary=primary or e;row['termination_error_type']=type(e).__name__
        if child is not None:
            try:
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:child.kill();child.wait(timeout=10)
                row.update(wrapper_exit=child.returncode,wrapper_reaped=child.returncode is not None)
                if row['wrapper_reaped']:child._handle.Close();row['wrapper_handle_closed']=True
            except BaseException as e:primary=primary or e;row['reap_error_type']=type(e).__name__
        if native is not None:
            try:
                until=time.monotonic()+10
                while True:
                    row['accounting']=native.accounting()
                    if row['accounting']['active']==0:row['active_zero_before_close']=True;break
                    need(time.monotonic()<until,'ACTIVE_DESCENDANTS');time.sleep(.05)
            except BaseException as e:primary=primary or e;row['accounting_error_type']=type(e).__name__
            finally:
                try:native.close();row['job_closed']=native.closed
                except BaseException as e:primary=primary or e;row['job_close_error_type']=type(e).__name__
        closed=all(row[k] is True for k in ('wrapper_reaped','wrapper_handle_closed','active_zero_before_close','job_closed'))
        write(record/'OWNERSHIP.json',{'format':'has_junko_stage_a_ownership_1','closure_proven':closed,'phase':'CLOSED_BEFORE_ASSERTION_CHECKS' if closed else 'CLOSURE_UNPROVEN','ownership':row})
    need(closed,'UNPROVEN_CLOSURE_STOP')
    if primary is not None:raise primary
    proof=parse(G.read(record/'worker-receipt.json'))
    need(row['wrapper_exit']==0 and row['assigned_before_START'] is True and proof.get('format')=='has_junko_stage_a_worker_1' and proof.get('status')==('EXPECTED_CHILD_REFUSAL' if job['expected_child_exit']==1 else 'PASS') and proof.get('request_sha256')==request_sha and proof.get('wrapper_identity')==row['owner'],'WORKER_RECEIPT')
    need(all(proof.get(k) is True for k in ('gate_accepted','child_launched','child_reaped','child_handle_closed')) and type(proof.get('child_exit'))is int and proof['child_exit']==job['expected_child_exit'] and proof.get('expected_child_exit')==job['expected_child_exit'],'CHILD_LIFECYCLE')
    need(row['accounting']['total']>=2 and row['accounting']['terminated_by_limit']==0 and not G.read(record/'wrapper-stderr.log'),'JOB_LIMIT_OR_WRAPPER_ERROR')
    row.update(status='EXPECTED_CHILD_REFUSAL' if job['expected_child_exit']==1 else 'PASS',worker_receipt_sha256=sha(G.read(record/'worker-receipt.json')))
    return record
def scratch_results(G,stage,reference_raw,reference_sha,capture_raw,record):
    out=stage/'PRIVATE_OUTPUT';public_raw=G.read(out/'PUBLIC_RESULT.json',262144);public=parse(public_raw);private_raw=G.read(out/'PRIVATE_scratch_rest.json',262144);private=parse(private_raw)
    need(public.get('format')=='has_scratch_rest_measurements_1' and public.get('status')=='MEASURED_SCRATCH_REPRESENTATIONS' and public.get('case_count')==22 and public.get('baseline_reproduced_exactly') is True and public.get('all_scratch_deleted_original_context_preserved') is True,'SCRATCH_COMPLETE_BASELINE_AND_CLEANUP')
    need(public.get('source_capture_sha256')==sha(capture_raw) and type(public.get('actual_model_repairs'))is int and public['actual_model_repairs']==0 and all(public.get(k) is False for k in ('native_export_qualified','tolerance_changed','SDK_written')),'NO_ORIGINAL_REPAIR_OR_QUALIFICATION')
    need(private.get('format')=='has_private_scratch_rest_representations_1' and private.get('private_do_not_publish') is True,'PRIVATE_MATRICES_REQUIRED')
    capture=parse(capture_raw);boundary=capture['factory_boundaries']
    def matrix(v):
        need(type(v)is list and len(v)==16 and all(type(x)in(int,float) and math.isfinite(x) for x in v),'FINITE_PRIVATE_MAT4');return v
    assigned=matrix(private.get('assignment'));native=matrix(private.get('native_reference'))
    need(assigned==boundary['assigned_matrix'] and native==capture['independent_native_global_rest'],'EXACT_PRIVATE_ASSIGNMENT_REFERENCE')
    nodes=[n for n in ast.parse(reference_raw).body if isinstance(n,ast.FunctionDef) and n.name=='close'];need(len(nodes)==1 and sha(reference_raw)==reference_sha,'PINNED_UNCHANGED_CLOSE_AST')
    namespace={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'pinned-close-only','exec'),namespace);close=namespace['close']
    schedule=[('original_baseline',None)]+[(m,n) for m in ('setter','setter_align','gltf_axes') for n in (.01905,.05,.1,.25,.5,1.,2.)]
    rows=public.get('cases');rawrows=private.get('rows');need(type(rows)is list and type(rawrows)is list and len(rows)==len(rawrows)==22,'EXACT22_MEASUREMENTS')
    def gap(a,b):return max(abs(x-y) for x,y in zip(a,b))
    expected_keys={'method','requested_length','getter_to_assignment_error','rest_to_assignment_error','rest_to_native_reference_error','getter_to_rest_error','original_close_rest_assignment','original_close_rest_native'}
    for i,(method,length) in enumerate(schedule):
        row=rows[i];raw=rawrows[i];need(type(row)is dict and set(row)==expected_keys and type(raw)is dict and set(raw)=={'method','requested_length','getter','rest'},'EXACT_SCALAR_PRIVATE_ROW_FIELDS')
        need(row['method']==raw['method']==method and row['requested_length']==raw['requested_length']==length,'EXACT_CASE_SCHEDULE')
        getter=matrix(raw['getter']);rest=matrix(raw['rest'])
        expected={'getter_to_assignment_error':gap(getter,assigned),'rest_to_assignment_error':gap(rest,assigned),'rest_to_native_reference_error':gap(rest,native),'getter_to_rest_error':gap(getter,rest),'original_close_rest_assignment':bool(close(rest,assigned)),'original_close_rest_native':bool(close(rest,native))}
        need(all(type(row[k])is bool for k in ('original_close_rest_assignment','original_close_rest_native')) and all(type(row[k])in(int,float) and math.isfinite(row[k]) and row[k]>=0 for k in expected if k.endswith('_error')),'TYPED_FINITE_SCALARS')
        need(all(row[k]==v for k,v in expected.items()),'EXACT_INDEPENDENT_ERROR_AND_CLOSE_RECALCULATION')
    need(rawrows[0]['getter']==boundary['immediate_edit_getter']['matrix'] and rawrows[0]['rest']==boundary['object_return_matrix'] and close(rawrows[0]['rest'],native) is False,'BIT_EXACT_ORIGINAL_FAILED_BASELINE')
    stdout=G.read(record/'child-stdout.log').decode('utf-8','replace');stderr=G.read(record/'child-stderr.log').decode('utf-8','replace');prefix='JUNKO_SCRATCH_REST '
    markers=[parse(s[len(prefix):]) for s in stdout.splitlines() if s.startswith(prefix)]
    need(len(markers)==1 and markers[0]==public and not re.search(r'Traceback|Python: Error|Error: script failed',stdout+'\n'+stderr),'EXACT_SCRATCH_MARKER_NO_SCRIPT_FAILURE')
    return {'public_report':public,'public_report_sha256':sha(public_raw),'private_matrix_sha256':sha(private_raw),'all22_error_and_close_rows_recomputed':True,'baseline_native_close_still_false':True,'original_model_or_SDK_loaded':False,'actual_model_repairs':0,'native_export_qualified':False,'cause_claimed':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--self-sha256',required=True);p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--revision',required=True);p.add_argument('--root-cpu-component-confirmed',action='store_true',required=True);a=p.parse_args()
    need(os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize and re.fullmatch('[0-9a-f]{40}',a.revision),'ROOT_WINDOWS313')
    G=Guard();need(sha(G.read(Path(__file__)))==a.self_sha256,'DRIVER_PIN');packet(G,HERE,a.source_manifest_sha256);packet(G,CANDIDATE,CANDIDATE_SHA)
    baseline_raw=G.read(HERE/'BASELINE_SOURCE1109.json');need(sha(baseline_raw)==BASELINE_SHA,'BASELINE1109_PIN');baseline=parse(baseline_raw);current_main(G,baseline,a.revision)
    exe_rows=parse(G.read(CANDIDATE/'RUNTIME_EXECUTABLES.json'))['files'];executables={r['role']:r for r in exe_rows};need(set(executables)=={'python','blender'},'EXACT_TWO_USED_EXECUTABLES')
    for row in exe_rows:
        b=G.read(row['path']);need(len(b)==row['bytes'] and sha(b)==row['sha256'],'EXE_PIN')
    python=executables['python'];need(Path(sys.executable).resolve()==Path(python['path']).resolve(),'ROOT_PYTHON_PIN')
    capture_pin=parse(G.read(CANDIDATE/'PRIVATE_INPUT_REFERENCE.json'))['input'];capture_raw=G.read(capture_pin['path'],65536);need(len(capture_raw)==capture_pin['bytes'] and sha(capture_raw)==capture_pin['sha256']=='a929dcc301d6d85f51a66ad9ca6ffc691958fd80393a8ae0360c593633a8f4cd','EXACT_PRIVATE_CAPTURE')
    reference=parse(G.read(CANDIDATE/'REFERENCE_CLOSE_SOURCE.json'));reference_raw=G.read(reference['path']);need(len(reference_raw)==reference['bytes'] and sha(reference_raw)==reference['sha256'],'REFERENCE_CLOSE_SOURCE')
    for row in parse(G.read(CANDIDATE/'INSTALLED_API_REFERENCES.json'))['files']:
        b=G.read(row['path']);need(len(b)==row['bytes'] and sha(b)==row['sha256'],'INSTALLED_API_SOURCE_PIN')
    closure=parse(G.read(CANDIDATE/'RUNTIME_SOURCE_CLOSURE.json'));need(closure['file_count']==3 and len(closure['files'])==3,'EXACT3_SOURCE_CLOSURE')
    runtime={}
    for row in closure['files']:
        rel(row['path']);need(row['path'] not in runtime,'SOURCE_DUPLICATE');origin=(ROOT if row['source_domain']=='current_readonly_source' else CANDIDATE)/rel(row['source']);b=G.read(origin);need(len(b)==row['bytes'] and sha(b)==row['sha256'],'SOURCE_PIN');runtime[row['path']]=b
    need(set(runtime)=={'tools/junko_scratch_rest.py','tools/source_jiggle_crosswalk.py','tests/test_junko_scratch_rest.py'},'EXACT_SCRATCH_RUNTIME')
    J=load(G,'_scratch_root_job',HERE/'root_native_job.py');L=load(G,'_scratch_root_layout',HERE/'approved_job_layout.py')
    stage=ROOT.parent/('has-junko-scratch-rest-v5-'+str(time.time_ns()));safe(stage,missing=True);stage.mkdir();studio=stage/'Studio'
    parent=dict(os.environ);result={'format':'has_junko_scratch_rest_v5_root_1','status':'FAIL','revision':a.revision,'checks':0,'jobs':{},'measurement':{},'scratch_cases':0,'SDK_or_native_models_loaded':False,'original_model_repairs':0,'native_export_qualified':False,'tolerance_changed':False,'Full_claimed':False,'graphics_executed':False,'application_modified':False,'private_matrices_published':False};primary=None
    lane=ROOT/'output/junko-scratch-rest-v5.lock';fd=None;lock_id=None;token=uuid.uuid4().hex.encode()
    try:
        fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR);need(os.write(fd,token)==len(token),'LOCK_WRITE');os.fsync(fd);lock_id=signature(os.fstat(fd))
        for name,b in runtime.items():fresh(studio/rel(name),b);G.read(studio/rel(name))
        private=stage/'PRIVATE_INPUTS/capture.json';fresh(private,capture_raw);G.read(private);out=stage/'PRIVATE_OUTPUT';out.mkdir()
        write(stage/'PRIVATE_ORIGINAL_IDENTITIES_BEFORE.json',G.rows)
        def job(name,cmd,timeout,scripts,exe):return {'name':name,'command':cmd,'studio':str(studio),'cwd':str(studio),'timeout_seconds':timeout,'expected_child_exit':0,'child_pin':exe,'environment_overrides':profile_env(stage/'Profiles'/name),'script_pins':{n:{'bytes':len(runtime[n]),'sha256':sha(runtime[n])} for n in scripts}}
        unit=job('unit12',[python['path'],'-I','-S','-B',str(studio/'tests/test_junko_scratch_rest.py')],90,('tests/test_junko_scratch_rest.py','tools/junko_scratch_rest.py'),python);record=run_job(G,J,L,stage,unit,python,result)
        text=(G.read(record/'child-stdout.log')+G.read(record/'child-stderr.log')).decode('utf-8','replace').replace('\r\n','\n')
        need(re.search(r'Ran 12 tests? in [0-9.]+s\s+OK\s*$',text) and len(re.findall(r'^test_.* \.\.\. ok$',text,re.M))==12 and not re.search(r'FAILED|ERROR|Traceback',text),'PURE12_EXACT');result['checks']=12
        blender=executables['blender'];cmd=[blender['path'],'--background','--factory-startup','--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(studio/'tools/junko_scratch_rest.py'),'--','--private-input',str(private),'--reference-close',str(studio/'tools/source_jiggle_crosswalk.py'),'--reference-close-sha256',reference['sha256'],'--output',str(out)]
        scratch=job('scratch',cmd,180,('tools/junko_scratch_rest.py','tools/source_jiggle_crosswalk.py'),blender);scratch.update(capture_pin={'path':str(private),'bytes':len(capture_raw),'sha256':sha(capture_raw)},output_dir=str(out));record=run_job(G,J,L,stage,scratch,python,result)
        result['measurement']=scratch_results(G,stage,reference_raw,reference['sha256'],capture_raw,record);result['scratch_cases']=22
        need(set(result['jobs'])=={'unit12','scratch'} and len(result['jobs'])==2,'EXACT_TWO_JOBS');result['status']='MEASURED_SCRATCH_REPRESENTATIONS'
    except BaseException as e:primary=e;result.update(error_type=type(e).__name__,private_error=str(e))
    finally:
        result['all_jobs_closed']=all(all(row.get(k) is True for k in ('wrapper_reaped','wrapper_handle_closed','active_zero_before_close','job_closed')) for row in result['jobs'].values())
        failures=G.preserve();result['preservation_failures']=failures;result['all_admitted_inputs_preserved']=not failures
        try:current_main(G,baseline,a.revision);need(tree(studio,filtered=True)==set(runtime),'OWNED3_RUNTIME_MEMBERSHIP');result['Main_and_runtime_preserved']=True
        except BaseException as e:result.update(Main_and_runtime_preserved=False,membership_error_type=type(e).__name__)
        result['parent_environment_preserved']=dict(os.environ)==parent;result['lock_removed']=False
        if fd is not None:
            try:
                need(result['all_jobs_closed'] and signature(os.fstat(fd))==lock_id and signature(lane.lstat())==lock_id,'OWNED_LOCK_IDENTITY');os.lseek(fd,0,0);need(os.read(fd,128)==token,'LOCK_TOKEN');os.close(fd);fd=None;lane.unlink();result['lock_removed']=True
            except BaseException as e:result['lock_error_type']=type(e).__name__
            finally:
                if fd is not None:os.close(fd)
        if not all(result[k] for k in ('all_jobs_closed','all_admitted_inputs_preserved','Main_and_runtime_preserved','parent_environment_preserved','lock_removed')):result['status']='FAIL'
        write(stage/'PRIVATE_ORIGINAL_IDENTITIES_AFTER.json',G.rows);write(stage/'PRIVATE_ROOT_RESULT.json',result)
        public={k:v for k,v in result.items() if k not in ('private_error','preservation_failures')};public['preservation_failure_count']=len(failures);public['source_input_file_count']=len(G.rows);write(stage/'PUBLIC_RESULT.json',public)
        print(json.dumps({'status':result['status'],'pure_checks':result['checks'],'scratch_measurements':result['scratch_cases'],'public_result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if primary is None and result['status']=='MEASURED_SCRATCH_REPRESENTATIONS' else 1
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:print(json.dumps({'status':'PREFLIGHT_REFUSED','error_type':type(e).__name__}),flush=True);raise SystemExit(2)
