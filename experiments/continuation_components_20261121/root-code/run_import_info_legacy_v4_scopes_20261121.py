"""Root-owned harmless import lifecycle53 and optional native texture recovery."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,time,types
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';KIT=OUT/'source-import-capability-headless163-c315-v2-prep-20261121'
INFO=OUT/'source-import-capability-canonical-c315-v2-prep-20261121';LEGACY=OUT/'source-import-info-legacy-tests-v2-prep-20261121'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name,path,digest=None):
 raw=path.read_bytes();assert digest is None or sha(raw)==digest
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);return m
H=load('_legacy_info_helpers',KIT/'qualified_helpers.py','990c37ddca7b1301613f5efc5a7e5a30ce2723369112ef274ee78d2d4dc34087')
R=load('_legacy_info_runner',KIT/'run_root105.py','436e704ea893f1029852ec667bb0c4618a2e095ec339591f99fd5c03339300ad')
J=load('_legacy_info_job',KIT/'root_native_job.py','fe9a9da0b545fbc1c2b21d09e93dd931b52c5a9e4681c5f0d106c3e43d67f34b')
L=load('_legacy_info_layout',KIT/'approved_job_layout.py','c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61')
F=load('_legacy_info_source',ROOT/'experiments/reference_body_20261120/run_full.py')
assert F.git('rev-parse','HEAD')=='c31576d0c1d84030d51ec886f2f3976a60a70c7b';before=F.snapshot();assert len(before)==1103
for prep,digest in [(INFO,'0cc2240218def0037cfe0377d22a0c22f772805dc07f967c5144b0d0dce66977'),(LEGACY,'879849943eda7f6fb036dd126db81020f49dea162a6f41889148b9ecc760187c')]:
 value=H.parse(H.read(prep/'SOURCE_PINS.json',digest=digest))
 for row in value['files']:H.read(prep/H.rel(row['path']),row['bytes'],row['sha256'])
lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));used=[]
for key in ('godot','python'):
 p=lock['runtime_paths'][key];row=lock['runtime_executables'][p];H.read(p,row['bytes'],row['sha256']);used.append({**row,'path':p.replace('\\','/') if key=='python' else p})
assert Path(sys.executable).resolve()==Path(lock['runtime_paths']['python']).resolve()
stage=ROOT.parent/('has-import-info-legacy-v4-scopes-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio'
B=load('_legacy_info_builder',ROOT/'tools/build_owner_review_snapshot.py');rev,base=B.freeze_source(ROOT,studio,F.git('rev-parse','HEAD'),runtime_scope=True);assert len(base)==1106
for prep in (INFO,LEGACY):
 for row in H.parse(H.read(prep/'TARGETS.json'))['targets']:
  if prep==INFO and not row['path'].startswith('src/'):continue
  target=studio/row['path'];raw=H.read(prep/'payload'/row['path'],row['bytes'],row['sha256'])
  if row['operation']=='replace':assert sha(target.read_bytes())==row['base_sha256']
  else:assert not target.exists()
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
MMD=OUT/'source-import-info-missing-texture-v3-prep-20261121'
value=H.parse(H.read(MMD/'SOURCE_PINS.json',digest='57db4f1a5d8ee9951f51716deba0de1cdd2130cd6a3345de0697ef3c3afabcf3'))
for row in value['files']:H.read(MMD/H.rel(row['path']),row['bytes'],row['sha256'])
target=studio/'tests/mmd_missing_texture_smoke.gd';assert sha(target.read_bytes())=='aaaa50b191f7aff04501dafbbfc9f0bcaf2253b007e90e3964c521898d3e2626'
target.write_bytes(H.read(MMD/'payload/tests/mmd_missing_texture_smoke.gd',4015,'72d80b683017d90277d4cecb8d161581b27d4eda9c376918ba37018b9d2dfe6d'))
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS legacy import isolated '+str(time.time_ns())+'"\n')
runtime={p:p.read_bytes() for p in studio.rglob('*') if p.is_file()};assert len(runtime)==1109
env={}
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 p=stage/'User'/leaf;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
env.update(HYBRID_PYTHON=Path(sys.executable).as_posix(),HYBRID_GODOT=lock['runtime_paths']['godot'],PYTHONDONTWRITEBYTECODE='1')
worker=H.read(KIT/'gated_headless_worker.py',6656,'4955af943d021ba0023d6617f981ece106dfd897bb561a50144377cab0181b69').decode()
anchor="('res://tests/import_capability_summary_unit.gd','res://tests/import_capability_app_headless.gd')";assert worker.count(anchor)==1
(stage/'gated_headless_worker.py').write_text(worker.replace(anchor,"('res://tests/source_import_owner_unit.gd',)"));R.HERE=stage
class Logs:
 MAX_LOG=8*1024*1024
 @staticmethod
 def validate_logs(h,job,record):
  stdout=h.read(record/'godot-stdout.log').decode();alltext=stdout+h.read(record/'godot-stderr.log').decode()+h.read(stage/'owner.engine.log').decode()
  assert not re.search(r'ERROR:|WARNING:|FAIL |leaked|orphan',alltext)
  rows=[json.loads(x.removeprefix('SOURCE_IMPORT_OWNER ')) for x in stdout.splitlines() if x.startswith('SOURCE_IMPORT_OWNER ')];assert len(rows)==1
  value=rows[0];assert value['checks']==53 and value['failures']==0 and len(value['cases'])==6 and sum(x.startswith('PASS ') for x in stdout.splitlines())==53
  return value
parent=dict(os.environ);result={'format':'has_import_info_legacy_v4_scopes_1','status':'FAIL','checks':0,'jobs':[],'native_texture_wrapper_passed':False,'graphics_executed':False,'Full_claimed':False,'application_adopted':False,'stage':str(stage)};error=None
try:
 args=[lock['runtime_paths']['godot'],'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(stage/'owner.engine.log'),'--script','res://tests/source_import_owner_unit.gd']
 job={'name':'unit','args':args,'cwd':str(studio),'studio':str(studio),'timeout_seconds':60,'expected_checks':53,'environment_overrides':env}
 value=R.run_case(H,Logs,J,L,job,stage,used,result);result['checks']=value['checks'];print('PASS owner53',flush=True)
 # Gate the ordinary native wrapper before assigning its entire descendant tree.
 native=J.RootJob(L);process=None;closed=False;token=str(time.time_ns());record={'name':'optional_native_missing_texture','status':'FAIL'};result['native_job']=record
 gate="import sys,runpy; token=sys.stdin.readline().strip(); assert token==sys.argv[1]; sys.argv=[sys.argv[2]]; runpy.run_path(sys.argv[0],run_name='__main__')"
 childenv=R.clean_env(job)
 try:
  with (stage/'mmd-stdout.log').open('xb') as out,(stage/'mmd-stderr.log').open('xb') as err:
   process=subprocess.Popen([sys.executable,'-I','-S','-B','-u','-c',gate,token,str(studio/'tests/verify_mmd_missing_texture.py')],cwd=studio,env=childenv,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
   record['owner']=native.identity(process);native.assign(process);record['assigned_before_start']=True;process.stdin.write((token+'\n').encode());process.stdin.close();record['exit']=process.wait(timeout=360)
 finally:
  native.terminate()
  if process is not None:
   if process.poll() is None:process.kill()
   process.wait(timeout=10);record['reaped']=process.poll() is not None;process._handle.Close();record['handle_closed']=True
  record['accounting']=native.accounting();record['active_zero']=record['accounting']['active']==0;native.close();record['job_closed']=native.closed
  closed=record.get('reaped') and record.get('handle_closed') and record['active_zero'] and record['job_closed']
 trace=(stage/'mmd-stdout.log').read_text()+(stage/'mmd-stderr.log').read_text()
 assert closed and record['exit']==0 and record['accounting']['terminated_by_limit']==0 and not re.search(r'ERROR:|WARNING:|Traceback|FAIL |leaked|SKIP ',trace)
 assert 'PASS street PMX warning and cold reopen of relocated packed mesh with missing-texture metadata' in trace
 result['native_wrapper_validated_both_engine_log_markers']=True
 result['native_marker_source']='Unchanged tests/verify_mmd_missing_texture.py assertions read both engine logs before ordinary temporary cleanup; raw windowed-engine stdout is not inherited on Windows.'
 record['status']='PASS';result['native_texture_wrapper_passed']=True;result['status']='PASS'
except BaseException as exc:error=exc;result['error_type']=type(exc).__name__;result['error']=str(exc)
finally:
 result['all_jobs_closed']=all(r.get('wrapper_reaped') and r.get('wrapper_handle_closed') and r.get('active_zero_before_close') and r.get('job_closed') for r in result['jobs']) and (not result.get('native_job') or all(result['native_job'].get(k) for k in ('reaped','handle_closed','active_zero','job_closed')))
 result['Main_runtime_inputs_environment_preserved']=F.snapshot()==before and dict(os.environ)==parent and all(H.read(p)==raw for p,raw in runtime.items()) and not H.preserve()
 if not result['all_jobs_closed'] or not result['Main_runtime_inputs_environment_preserved']:result['status']='FAIL'
 (stage/'ROOT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='PASS' and error is None else 1)
