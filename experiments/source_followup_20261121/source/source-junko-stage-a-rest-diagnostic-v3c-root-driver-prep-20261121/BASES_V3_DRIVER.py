"""Root-only Body/Dress export-identity component; no app, Full or simulation claim."""
from pathlib import Path,PurePosixPath
import argparse,ast,hashlib,json,math,os,re,stat,struct,subprocess,sys,time,types,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CANDIDATE=ROOT/'output/source-junko-body-dress-rest-diagnostic-prep-20261121'
CANDIDATE_SHA='8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3'
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
def glb_json(raw):
    need(len(raw)>=20 and raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw)),'GLB_HEADER')
    length,kind=struct.unpack_from('<II',raw,12);need(kind==0x4e4f534a and length%4==0 and 20+length<=len(raw),'GLB_JSON_CHUNK')
    return parse(raw[20:20+length].rstrip(b' \0'))
def diagnostic_result(G,stage,facts):
    folder=stage/'Bundles/body';status=parse(G.read(stage/'body-status.json'))
    need(status.get('ok') is False and 'Conversion failed' in str(status.get('error','')),'EXPECTED_ORDINARY_REFUSAL_STATUS')
    need(not (folder/'scene.glb').exists() and not (folder/'PRIVATE_part_export_binding.json').exists(),'NO_EXPORT_OR_BINDING_ACCEPTED')
    raw=G.read(folder/'PRIVATE_first_rest_refusal.json',65536);private=parse(raw)
    need(private.get('format')=='has_private_first_native_rest_refusal_1' and private.get('private_do_not_publish') is True and private.get('native_mdl_sha256')==facts['sha256'] and private.get('original_error_code')=='native_Blender_rest_matrix_mismatch','EXACT_FIRST_REFUSAL_PROFILE')
    need(private.get('diagnostic_reads_only') is True and all(private.get(k) is False for k in ('rest_tolerance_changed','model_repaired','export_binding_qualified','native_runtime_binding_qualified')),'NO_REPAIR_OR_PROMOTION')
    index=private.get('native_index');need(type(index)is int and 0<=index<145,'NATIVE_INDEX')
    scalar=private.get('scalar_errors');need(type(scalar)is dict and set(scalar)=={'first_native_index','global_max_error','global_translation_error','global_basis_error','global_normalized_error','parent_global_error','current_parent_native_local_error','current_parent_mathutils_local_error','mathutils_vs_native_local_error','native_quaternion_unit_error'},'EXACT_PUBLIC_SCALAR_FIELDS')
    need(type(scalar['first_native_index'])is int and scalar['first_native_index']==index and all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in scalar.values()),'FINITE_TYPED_SCALARS')
    vectors={}
    for key in ('actual_global_rest','independent_native_global_rest','actual_parent_global_rest','independent_parent_global_rest','independent_native_local_rest','current_parent_times_native_local','mathutils_local_rest','current_parent_times_mathutils_local','actual_pose_matrix'):
        value=private.get(key);need(type(value)is list and len(value)==16 and all(type(v) in (int,float) and math.isfinite(v) and abs(v)<=1e9 for v in value),'FINITE_PRIVATE_MATRIX');vectors[key]=value
    # Compile ONLY the exact existing pinned close() AST; no module/native hooks.
    helper=G.read(stage/'Studio/tools/source_jiggle_crosswalk.py');nodes=[n for n in ast.parse(helper).body if isinstance(n,ast.FunctionDef) and n.name=='close'];need(len(nodes)==1,'PINNED_CLOSE_FUNCTION')
    namespace={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'pinned-source-close-only','exec'),namespace)
    need(namespace['close'](vectors['actual_global_rest'],vectors['independent_native_global_rest']) is False,'ORIGINAL_REST_REFUSAL_MUST_REMAIN_FALSE')
    mdl=G.read(stage/'NativeJunko'/rel(facts['source_relative']));need(sha(mdl)==facts['sha256'] and mdl[:4]==b'IDST' and struct.unpack_from('<i',mdl,4)[0]==49,'EXACT_NATIVE_MDL49')
    count,base=struct.unpack_from('<II',mdl,156);need(count==145 and base>=408 and base+count*216<=len(mdl),'NATIVE_TABLE')
    at=base+index*216;name_offset,parent=struct.unpack_from('<ii',mdl,at);values=struct.unpack_from('<7f',mdl,at+32);words=struct.unpack_from('<7I',mdl,at+32)
    name_at=at+name_offset;end=mdl.find(b'\0',name_at,min(len(mdl),name_at+63));need(base+count*216<=name_at<end<len(mdl),'NATIVE_NAME_DOMAIN')
    need(private.get('native_name')==mdl[name_at:end].decode('ascii') and private.get('native_parent_index')==parent and private.get('native_rest_words_uint32')==list(words),'FIRST_NATIVE_ROW_IDENTITY')
    position=private.get('native_position');quat=private.get('native_quaternion')
    need(type(position)is list and len(position)==3 and type(quat)is list and len(quat)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in position+quat),'NATIVE_ROW_NUMBERS')
    need(struct.pack('<7f',*position,*quat)==struct.pack('<7I',*words),'EXACT_NATIVE_REST_WORDS')
    for key in ('actual_data_bone_pointer','actual_pose_bone_pointer','actual_armature_pointer'):need(type(private.get(key))is int and private[key]>0,'OBSERVED_POINTERS_PRIVATE')
    def maximum(a,b,indices=range(16)):return max(abs(a[i]-b[i]) for i in indices)
    actual=vectors['actual_global_rest'];expected=vectors['independent_native_global_rest']
    recomputed={'first_native_index':index,'global_max_error':maximum(actual,expected),'global_translation_error':maximum(actual,expected,(3,7,11)),'global_basis_error':maximum(actual,expected,(0,1,2,4,5,6,8,9,10)),'global_normalized_error':max(abs(a-b)/max(1.,abs(b)) for a,b in zip(actual,expected)),'parent_global_error':maximum(vectors['actual_parent_global_rest'],vectors['independent_parent_global_rest']),'current_parent_native_local_error':maximum(actual,vectors['current_parent_times_native_local']),'current_parent_mathutils_local_error':maximum(actual,vectors['current_parent_times_mathutils_local']),'mathutils_vs_native_local_error':maximum(vectors['mathutils_local_rest'],vectors['independent_native_local_rest']),'native_quaternion_unit_error':abs(math.sqrt(sum(v*v for v in quat))-1.)}
    need(recomputed==scalar,'EXACT_SCALAR_RECALCULATION')
    log=G.read(folder/'conversion.log',64*1024*1024).decode('utf-8','replace');prefix='JUNKO_PART_REST_DIAGNOSTIC '
    markers=[parse(line[len(prefix):]) for line in log.splitlines() if line.startswith(prefix)]
    need(len(markers)==1 and markers[0]==scalar and 'JUNKO_PART_REST_DIAGNOSTIC_CAPTURE_FAILED' not in log,'ONE_COMPLETE_DIAGNOSTIC')
    need(log.count('Traceback (most recent call last):')==1 and 'source_jiggle_crosswalk.CrosswalkError: native_Blender_rest_matrix_mismatch' in log and 'JUNKO_PART_EXPORT_IDENTITY ' not in log,'UNCHANGED_ORIGINAL_NATIVE_REFUSAL')
    return {'status':'EXPECTED_REFUSAL_WITH_DIAGNOSTIC','scalar_errors':scalar,'private_diagnostic_sha256':sha(raw),'conversion_log_sha256':sha(log.encode('utf-8')),'original_close_predicate_still_false':True,'source_rest_tolerance_changed':False,'diagnosed_cause_claimed':False,'reference_pose_or_later_factory_writes_ruled_out':False,'export_binding_qualified':False,'Godot_binding_qualified':False,'native_simulation_qualified':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-sha256',required=True);p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--revision',required=True);p.add_argument('--root-cpu-component-confirmed',action='store_true',required=True);a=p.parse_args()
    need(os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize and re.fullmatch('[0-9a-f]{40}',a.revision),'ROOT_WINDOWS313_REVISION')
    G=Guard();need(sha(G.read(Path(__file__)))==a.self_sha256,'EXTERNAL_DRIVER_PIN');packet(G,HERE,a.source_manifest_sha256);packet(G,CANDIDATE,CANDIDATE_SHA)
    baseline_raw=G.read(HERE/'BASELINE_SOURCE1109.json');need(sha(baseline_raw)==BASELINE_SHA,'SOURCE1109_BASELINE');baseline=parse(baseline_raw);current_main(G,baseline,a.revision)
    python_rows=parse(G.read(CANDIDATE/'RUNTIME_EXECUTABLES.json'))['files'];executables={r['role']:r for r in python_rows};need(set(executables)=={'python','blender','godot'},'EXECUTABLE_PROFILE')
    for row in python_rows:
        b=G.read(row['path']);need(len(b)==row['bytes'] and sha(b)==row['sha256'],'EXE_PIN')
    python=executables['python'];need(Path(sys.executable).resolve()==Path(python['path']).resolve(),'APPROVED_ROOT_PYTHON')
    sdk=parse(G.read(CANDIDATE/'SDK_CATALOGUE.json'));inputs_ref=parse(G.read(CANDIDATE/'PRIVATE_INPUT_REFERENCE.json'));inputs_raw=G.read(inputs_ref['path']);need(len(inputs_raw)==inputs_ref['bytes'] and sha(inputs_raw)==inputs_ref['sha256'],'PRIVATE_INPUT_REFERENCE')
    inputs=parse(inputs_raw);native_root=Path(inputs_ref['source_root']);need(inputs.get('root_input')==str(native_root).replace('\\','/') and len(inputs['files'])==99,'ORIGINAL99_PROFILE')
    observed_roots={};copy_groups=[]
    for tag,folder,rows in [('SDK',Path(sdk['source_root']),sdk['sourceio_files']),('Exporter',Path(sdk['exporter_root']),sdk['exporter_files']),('NativeJunko',native_root,inputs['files'])]:
        need(len(rows)=={'SDK':574,'Exporter':120,'NativeJunko':99}[tag],'EXACT_SOURCE_COUNTS');names={r['path'] for r in rows}
        need(len(names)==len(rows) and len({n.casefold() for n in names})==len(rows) and tree(folder,filtered=tag!='NativeJunko')==names,'ORIGINAL_MEMBERSHIP')
        # Preserve ALL existing files, including unconsumed caches/Git metadata,
        # separately from the exact source-only114/574/120 profile.
        observed_roots[str(folder)]=tree(folder)
        for name in observed_roots[str(folder)]:G.read(folder/rel(name))
        for row in rows:
            b=G.read(folder/rel(row['path']));need(len(b)==row['bytes'] and sha(b)==row['sha256'],'ORIGINAL_INPUT_PIN')
            if tag=='NativeJunko':need((folder/rel(row['path'])).stat().st_mtime_ns==int(row['mtime_ns']),'ORIGINAL_NATIVE_NSMTIME')
        copy_groups.append((tag,folder,rows))
    J=load(G,'_junko_stage_a_job',HERE/'root_native_job.py');L=load(G,'_junko_stage_a_layout',HERE/'approved_job_layout.py')
    closure=parse(G.read(CANDIDATE/'RUNTIME_SOURCE_CLOSURE.json'));need(closure['file_count']==116 and len(closure['files'])==116,'TOOLS116_CLOSURE')
    runtime={}
    for row in closure['files']:
        name=row['path'];rel(name);need(name not in runtime,'TOOLS_DUPLICATE');source=(ROOT if row['source_domain']=='current_readonly_source' else CANDIDATE)/rel(row['source']);b=G.read(source);need(len(b)==row['bytes'] and sha(b)==row['sha256'],'TOOLS_SOURCE_PIN');runtime[name]=b
    stage=ROOT.parent/('has-junko-native-rest-diagnostic-v3-'+str(time.time_ns()));safe(stage,missing=True);stage.mkdir();studio=stage/'Studio'
    parent=dict(os.environ);result={'format':'has_junko_body_rest_diagnostic_v3_1','status':'FAIL','revision':a.revision,'checks':0,'jobs':{},'conversions':{},'diagnostic':{},'dress_started':False,'graphics_executed':False,'Full_claimed':False,'native_simulation_qualified':False,'Godot_binding_qualified':False,'application_modified':False,'private_arrays_published':False};primary=None
    lane=ROOT/'output/junko-native-rest-diagnostic-v3.lock';fd=None;lock_id=None;token=uuid.uuid4().hex.encode();owned_copies={}
    try:
        fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR);need(os.write(fd,token)==len(token),'LOCK_SHORT_WRITE');os.fsync(fd);lock_id=signature(os.fstat(fd))
        for name,b in runtime.items():fresh(studio/rel(name),b);G.read(studio/rel(name))
        for tag,folder,rows in copy_groups:
            dest=stage/('SourceIO' if tag=='SDK' else 'ExporterReference' if tag=='Exporter' else tag)
            for row in rows:fresh(dest/rel(row['path']),G.read(folder/rel(row['path'])));G.read(dest/rel(row['path']))
            owned_copies[str(dest)]={r['path'] for r in rows}
        write(stage/'PRIVATE_ORIGINAL_IDENTITIES_BEFORE.json',G.rows)
        facts=parse(G.read(CANDIDATE/'NATIVE_FACTS.json'));need(facts['scale']==.01905 and {r['role'] for r in facts['models']}=={'body','dress'},'TWO_NATIVE_PROFILES')
        mount=stage/'mount-plan.json';write(mount,[str(stage/'NativeJunko').replace('\\','/')]);G.read(mount)
        def job(name,cmd,timeout,scripts,expected_exit):return {'name':name,'command':cmd,'studio':str(studio),'cwd':str(studio),'timeout_seconds':timeout,'environment_overrides':profile_env(stage/'Profiles'/name),'expected_child_exit':expected_exit,'script_pins':{s:{'bytes':len(runtime[s]),'sha256':sha(runtime[s])} for s in scripts}}
        tests=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py')
        unit=job('unit25',[python['path'],'-I','-S','-B','-m','unittest','discover','-s',str(studio/'tests'),'-p','test_junko_part*.py','-v'],90,tests,0);record=run_job(G,J,L,stage,unit,python,result)
        text=(G.read(record/'child-stdout.log')+G.read(record/'child-stderr.log')).decode('utf-8','replace').replace('\r\n','\n')
        need(re.search(r'Ran 25 tests? in [0-9.]+s\s+OK\s*$',text) is not None and len(re.findall(r'^test_.* \.\.\. ok$',text,re.M))==25 and not re.search(r'FAILED|ERROR|Traceback',text),'PURE25_EXACT');result['checks']=25
        model=next(row for row in facts['models'] if row['role']=='body');source=stage/'NativeJunko'/rel(model['source_relative']);need(sha(G.read(source))==model['sha256'],'SELECTED_OWNED_BODY')
        target=stage/'Bundles/body';need(not target.exists(),'FRESH_DIAGNOSTIC_OUTPUT');target.parent.mkdir(exist_ok=True)
        cmd=[python['path'],'-I','-S','-B',str(studio/'tools/prepare_junko_part_probe.py'),str(source),'--output',str(target),'--sourceio',str(stage/'SourceIO'),'--blender',executables['blender']['path'],'--gmod',str(stage/'AbsentGame'),'--workshop',str(stage/'AbsentWorkshop'),'--mount-plan',str(mount),'--scale','0.01905','--status-file',str(stage/'body-status.json'),'--cancel-file',str(stage/'body-cancel')]
        spec=job('body',cmd,720,('tools/prepare_junko_part_probe.py',),1);spec['conversion_log']=str(target/'conversion.log');run_job(G,J,L,stage,spec,python,result)
        result['diagnostic']=diagnostic_result(G,stage,model)
        need(len(result['jobs'])==2 and set(result['jobs'])=={'unit25','body'} and result['conversions']=={} and result['dress_started'] is False,'ONLY_BODY_DIAGNOSTIC_COMPLETE')
        result['status']='EXPECTED_REFUSAL_WITH_DIAGNOSTIC'

    except BaseException as e:primary=e;result.update(error_type=type(e).__name__,private_error=str(e))
    finally:
        result['all_jobs_closed']=all(all(row.get(k) is True for k in ('wrapper_reaped','wrapper_handle_closed','active_zero_before_close','job_closed')) for row in result['jobs'].values())
        failures=G.preserve();result['preservation_failures']=failures
        try:
            current_main(G,baseline,a.revision)
            need(all(tree(Path(p))==names for p,names in observed_roots.items()),'ORIGINAL_TREE_CHANGED')
            need(all(tree(Path(p),filtered=True)==names for p,names in owned_copies.items()) and tree(studio,filtered=True)==set(runtime),'OWNED_RUNTIME_DOMAIN')
            result['all_memberships_and_Main_preserved']=True
        except BaseException as e:result.update(all_memberships_and_Main_preserved=False,membership_error_type=type(e).__name__)
        result['parent_environment_preserved']=dict(os.environ)==parent;result['all_admitted_inputs_preserved']=not failures
        result['lock_removed']=False
        if fd is not None:
            try:
                need(result['all_jobs_closed'] and signature(os.fstat(fd))==lock_id and signature(lane.lstat())==lock_id,'RETAINED_OWNED_LOCK');os.lseek(fd,0,0);need(os.read(fd,128)==token,'LOCK_TOKEN');os.close(fd);fd=None;lane.unlink();result['lock_removed']=True
            except BaseException as e:result['lock_error_type']=type(e).__name__
            finally:
                if fd is not None:os.close(fd)
        if not all(result[k] for k in ('all_jobs_closed','all_memberships_and_Main_preserved','parent_environment_preserved','all_admitted_inputs_preserved','lock_removed')):result['status']='FAIL'
        write(stage/'PRIVATE_ORIGINAL_IDENTITIES_AFTER.json',G.rows);write(stage/'PRIVATE_RESULT.json',result)
        public={k:v for k,v in result.items() if k not in ('private_error','preservation_failures')};public['preservation_failure_count']=len(failures);public['source_input_file_count']=len(G.rows)
        write(stage/'PUBLIC_RESULT.json',public);print(json.dumps({'status':public['status'],'pure_checks':result['checks'],'conversion_count':0,'diagnostic_captured':bool(result['diagnostic']),'public_result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if primary is None and result['status']=='EXPECTED_REFUSAL_WITH_DIAGNOSTIC' else 1
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:print(json.dumps({'status':'PREFLIGHT_REFUSED','error_type':type(e).__name__}),flush=True);raise SystemExit(2)
