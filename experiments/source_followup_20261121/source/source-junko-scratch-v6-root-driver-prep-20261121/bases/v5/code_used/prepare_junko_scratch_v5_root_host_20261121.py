"""Freeze minimal scratch-only Root launcher; author executes no Blender/tests/Main."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-factory-boundary-v4-root-driver-prep-20261121'
C=R/'output/source-junko-scratch-rest-representation-prep-20261121'
D=R/'output/source-junko-scratch-v5-root-driver-prep-20261121'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert pin((S/'SOURCE_PINS.json').read_bytes())['sha256']=='20f2dcfd7d95127ab3b139b3cc87a99c74e00aa869a21c672027c40c163a1bcc'
assert pin((C/'SOURCE_PINS.json').read_bytes())['sha256']=='9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015'
assert not D.exists();D.mkdir()
for name in ('root_native_job.py','approved_job_layout.py','BASELINE_SOURCE1109.json'):(D/name).write_bytes((S/name).read_bytes())
for name in ('SOURCE_PINS.json','ROOT_PROTOCOL.md'):(D/('CANDIDATE_'+name)).write_bytes((C/name).read_bytes())
worker=(S/'gated_converter_worker.py').read_text()
start=worker.index("    need(job['name'] in (");end=worker.index("    receipt={'format':",start)
worker=worker[:start]+'''    need(job['name'] in ('unit12','scratch') and type(cmd)is list and all(type(x)is str for x in cmd),'EXACT_TWO_SCRATCH_JOBS')
    need(Path(sys.executable).resolve()==Path(pin['path']).resolve() and job['cwd']==str(studio),'ROOT_PYTHON_AND_OWNED_CWD')
    expected_exit=0
    need(type(job.get('expected_child_exit'))is int and job['expected_child_exit']==0,'SCRATCH_ZERO_EXIT_ONLY')
    child_pin=job['child_pin'];need(cmd[0]==child_pin['path'],'CHILD_EXECUTABLE_IDENTITY')
    if job['name']=='unit12':
        need(cmd==[pin['path'],'-I','-S','-B',str(studio/'tests/test_junko_scratch_rest.py')] and child_pin==pin and job['timeout_seconds']==90,'EXACT_PURE12')
        scripts=('tests/test_junko_scratch_rest.py','tools/junko_scratch_rest.py')
    else:
        need(child_pin.get('role')=='blender' and cmd[:9]==[child_pin['path'],'--background','--factory-startup','--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(studio/'tools/junko_scratch_rest.py')] and job['timeout_seconds']==180,'EXACT_BACKGROUND_SCRATCH_BLENDER')
        capture=job['capture_pin'];b=regular(capture['path'],65536)
        need(len(b)==capture['bytes'] and sha(b)==capture['sha256'],'OWNED_CAPTURE_PIN')
        need(cmd[9:]==['--','--private-input',capture['path'],'--reference-close',str(studio/'tools/source_jiggle_crosswalk.py'),'--reference-close-sha256',job['script_pins']['tools/source_jiggle_crosswalk.py']['sha256'],'--output',job['output_dir']],'EXACT_SCRATCH_ARGUMENTS')
        scripts=('tools/junko_scratch_rest.py','tools/source_jiggle_crosswalk.py')
    for executable in (pin,child_pin):
        b=regular(executable['path'],512*1024*1024);need(len(b)==executable['bytes'] and sha(b)==executable['sha256'],'EXECUTABLE_PIN')
    need(set(job['script_pins'])==set(scripts),'EXACT_SCRIPT_PIN_MEMBERSHIP')
    script_bytes={}
    for name in scripts:
        script=regular(studio/name,1024*1024);expected=job['script_pins'][name]
        need(len(script)==expected['bytes'] and sha(script)==expected['sha256'],'OWNED_SCRIPT_PIN');script_bytes[name]=script
''' +worker[end:]
ast.parse(worker);(D/'gated_converter_worker.py').write_text(worker,encoding='utf-8')
source=(S/'run_stage_a.py').read_text();source=source[:source.index('def glb_json(')]
source=source.replace('source-junko-factory-boundary-diagnostic-prep-20261121','source-junko-scratch-rest-representation-prep-20261121').replace('5a07872ec538d18835c01f1f11b83ea24ae69858a9ead03fa0f31c9dd1640974','9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015')
source+='''def scratch_results(G,stage,reference_raw,reference_sha,capture_raw,record):
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
    need(len(markers)==1 and markers[0]==public and not re.search(r'Traceback|Python: Error|Error: script failed',stdout+'\\n'+stderr),'EXACT_SCRATCH_MARKER_NO_SCRIPT_FAILURE')
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
        text=(G.read(record/'child-stdout.log')+G.read(record/'child-stderr.log')).decode('utf-8','replace').replace('\\r\\n','\\n')
        need(re.search(r'Ran 12 tests? in [0-9.]+s\\s+OK\\s*$',text) and len(re.findall(r'^test_.* \\.\\.\\. ok$',text,re.M))==12 and not re.search(r'FAILED|ERROR|Traceback',text),'PURE12_EXACT');result['checks']=12
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
'''
ast.parse(source);(D/'run_scratch.py').write_text(source,encoding='utf-8')
(D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'README.md').write_text('''# Root scratch-only v5 measurement host

SOURCE ONLY UNRUN. Candidate9557dff and Main2f1/1109 baseline23ea7f are exact.
Existing RootJob16process4GiB,START nonce/retainedPID+birth,kill-on-close/no-breakaway,
log/timeouts,child/wrapper handle closure/active0-before-advance remain from v4.
Two jobs only: Python-I-S-B pure12 (90s), then approved background/factory/offline/
disable-autoexec Blender scratch script (180s). No SourceIO, SDK copy, MDL, model
conversion, app, Godot, GPU/render or ownerproject is loaded. Runtime is exactly3
files: helper,test,pinned original C.close module used by AST only, never imported.

Root must source-review before running existing pinned Python-I-S-B run_scratch.py
--self-sha256 <driverSHA> --source-manifest-sha256 <thisSOURCE_PINSSHA> --revision
2f1acbd7867087d9f18cfbc1122cc0c883c5f788 --root-cpu-component-confirmed.

Exact a929 private capture is copied only into new local PRIVATE_INPUTS. Installed
twoAPI source references,Python/Blender executables,original capture/currentMain1109
and copied3 sources are full native64 identity/ns/bytes/hash checked before/after.
Reference C.close source is pinned and only its originalAST function executes.
Root independently reconciles public marker/report and all22 method/length rows,
finite private matrices and every reported error/close flag. Original baseline
must match captured immediategetter+OBJECT bit-exact and original closefalse;
scratch cleanup/context flag is mandatory. Allcandidatefalse outcomes remain valid
measurements; no minimum success is assumed, no originalmodel repair is claimed.

Only scalar case metadata/hashes/counts/Job closure are public. Original capture,
all matrix/name/word data, private results and identities staylocal. No original
bone/SDK/installation/Main edits, native export/Godot54/follow/physics/fidelity or
Full pass is inferred. Existing failed/expected-refusal preparations remain intact.
''',encoding='utf-8')
(D/'CHECK_PLAN.json').write_text(json.dumps({'format':'has_scratch_v5_root_plan_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','pure_controls':12,'Root_jobs':2,'scratch_measurement_cases':22,'scratch_cases_are_not_22_additional_unit_tests':True,'runtime_source_files':3,'Python_timeout':90,'Blender_timeout':180,'max_processes':16,'Job_bytes':4294967296,'Main_sources':1109,'candidate_source_pins':'9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015','SDK_or_native_model_or_app_or_Godot_loaded':False,'Main_or_original_bones_or_tools_written':False,'tolerance_changed':False,'model_repairs':0},indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file() and p!=D/'SOURCE_PINS.json']
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_scratch_v5_root_source_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':rows},indent=2)+'\n',encoding='utf-8')
assert {r['path'] for r in rows}|{'SOURCE_PINS.json'}=={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}
for row in rows:assert pin((D/row['path']).read_bytes())=={'bytes':row['bytes'],'sha256':row['sha256']}
print(json.dumps({'files':len(rows)+1,'payload_bytes':sum(r['bytes'] for r in rows),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'host':pin((D/'run_scratch.py').read_bytes()),'worker':pin((D/'gated_converter_worker.py').read_bytes()),'AST_changed_sources_only':2,'CPU_exact_source_closure':'PASS'},indent=2))
