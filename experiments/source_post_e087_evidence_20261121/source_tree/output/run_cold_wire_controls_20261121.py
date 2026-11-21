"""Root-only hidden pure cold-wire controls; copied e087 source, no app instantiated."""
from pathlib import Path
import importlib.util,hashlib,json,os,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'output/source-headless-component-coordinator-v3-prep-20261121/run_components.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='7b146fd5ad8aabb80f4b3542dd02ce6416d26ab36d209c1ca754a926d954c8ad'
s=importlib.util.spec_from_file_location('_cold_oracle_job_helpers',p);H=importlib.util.module_from_spec(s);sys.modules[s.name]=H;s.loader.exec_module(H)
assert H.head()==H.REVISION and H.ROOT==ROOT
B=H.load_builder();_full,catalogue,_proof=B.validate_full(H.FULL,H.FULL_REVISION,H.FULL_SHA)
frozen=B.source_blobs(H.REVISION,catalogue);assert len(frozen)==1087
lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));runtime=lock['runtime_paths']
assert Path(sys.executable).resolve()==Path(runtime['python']).resolve()
for path,pin in lock['runtime_executables'].items():H.read(path,pin['bytes'],pin['sha256'])
smoke=H.read(ROOT/'output/import-physics-default-off-cold-wire-v3-prep-20261121/import_physics_smoke.gd',21848,'9104065d55830781b07e47c358ddaa8c039d038b53780dcbeeafaad52c0d9be1')
stage=ROOT/'output'/('cold-wire-controls-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio';studio.mkdir()
for name,raw in frozen.items():
 target=studio/name;target.parent.mkdir(parents=True,exist_ok=True);H.new(target,raw)
H.replace_owned(studio/'tests/import_physics_smoke.gd',smoke)
for name in ['Roaming','Local','Temp']:(stage/name).mkdir()
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',APPDATA=str(stage/'Roaming'),LOCALAPPDATA=str(stage/'Local'),TEMP=str(stage/'Temp'),TMP=str(stage/'Temp'))
result={'format':'has_cold_wire_oracle_root_1','status':'FAIL','stage':str(stage),'jobs':[],'application_adopted':False,'actual_model_import_or_gpu_started':False,'complements_actual_54_gpu_checks':True};primary=None
try:
 H.job(studio,stage,'import',['--editor','--import','--quit'],runtime,env,result['jobs'])
 stdout=H.job(studio,stage,'controls',['--log-file',str(stage/'engine.log'),'--script','res://tests/import_physics_smoke.gd','--','--cold-oracle-only'],runtime,env,result['jobs'])
 marker='IMPORT_OFF_COLD_ORACLE_CONTROLS ';rows=[line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
 H.need(len(rows)==1,'ONE_ORACLE_MARKER');value=H.parse(rows[0]);H.need(value.get('checks')==20 and value.get('failures')==0 and value.get('failed_labels')==[] and value.get('actual_native_asset_tested') is False and value.get('application_adopted') is False,'EXACT_ORACLE_COUNTS_SCOPE')
 H.need(not any(line.startswith('PASS ') or line.startswith('IMPORT_PHYSICS ') for line in stdout.splitlines()),'APP_SMOKE_MUST_NOT_RUN')
 result.update(status='PASS',oracle_checks=20,oracle_failures=0,scope_marker=value)
except BaseException as error:primary=error;result.update(error_type=type(error).__name__,error=str(error)[:200])
finally:
 for process,row in H.OWNED:row['reaped']=H.reap(process)
 result['all_owned_launchers_reaped']=all(row['reaped'] for _p,row in H.OWNED);result['all_private_jobs_closed']=all(row['private_job_closed'] and row['desktop_closed'] for _p,row in H.OWNED)
 failures=H.preserve();result['all_admitted_inputs_preserved']=not failures;result['preservation_failures']=failures;result['head_unchanged']=H.head()==H.REVISION
 if primary is not None or failures or not result['all_owned_launchers_reaped'] or not result['all_private_jobs_closed'] or not result['head_unchanged']:result['status']='FAIL'
 H.json_new(stage/'PUBLIC_RESULT.json',result);print(json.dumps(result),flush=True)
sys.exit(0 if result['status']=='PASS' else 1)
