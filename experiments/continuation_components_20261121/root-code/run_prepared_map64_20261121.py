"""Root-owned headless editor completion replay; no conversion or graphics."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys,time,types
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
PREP=OUT/'source-prepared-map-editor-prep-20261121'
KIT=OUT/'source-import-capability-headless163-c315-v2-prep-20261121'
BASE='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name,path,digest):
 raw=path.read_bytes();assert sha(raw)==digest
 module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
 exec(compile(raw,str(path),'exec'),module.__dict__);return module
H=load('_map64_helpers',KIT/'qualified_helpers.py','990c37ddca7b1301613f5efc5a7e5a30ce2723369112ef274ee78d2d4dc34087')
R=load('_map64_runner',KIT/'run_root105.py','436e704ea893f1029852ec667bb0c4618a2e095ec339591f99fd5c03339300ad')
J=load('_map64_job',KIT/'root_native_job.py','fe9a9da0b545fbc1c2b21d09e93dd931b52c5a9e4681c5f0d106c3e43d67f34b')
L=load('_map64_layout',KIT/'approved_job_layout.py','c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61')
F=load('_map64_domain',ROOT/'experiments/reference_body_20261120/run_full.py',sha((ROOT/'experiments/reference_body_20261120/run_full.py').read_bytes()))
assert os.name=='nt' and sys.version_info[:2]==(3,13) and F.git('rev-parse','HEAD')==BASE
before=F.snapshot();assert len(before)==1103
manifest_raw=H.read(PREP/'SOURCE_PINS.json',digest='66a091596faa2c4531a2e27c4ba95c6ca7118f62bddaf1fb6753ffe1a44cb804')
manifest=H.parse(manifest_raw)
for row in manifest['files']:H.read(PREP/H.rel(row['path']),row['bytes'],row['sha256'])
assert {p.relative_to(PREP).as_posix() for p in PREP.rglob('*') if p.is_file()}=={'SOURCE_PINS.json'}|{r['path'] for r in manifest['files']}
pre=H.parse(H.read(PREP/'PRECONDITIONS.json'));used=[]
for row in pre['executables']:
 H.read(row['path'],row['bytes'],row['sha256']);used.append(row)
engine=pre['executables'][0]['path'];assert Path(sys.executable).resolve()==Path(pre['executables'][1]['path']).resolve()
reference=pre['actual_read_only_prepared_input_manifest']
private=H.parse(H.read(reference['path'],reference['bytes'],reference['sha256']))
for row in [private['conversion_result']]+[v for m in private['maps'] for v in m['files'].values()]:H.read(row['path'],row['bytes'],row['sha256'])
closure=H.parse(H.read(PREP/'RUNTIME_SOURCE_CLOSURE.json'));assert len(closure['files'])==327
payload={}
for row in closure['files']:
 source=(ROOT if row['source_domain']=='current_readonly_source' else PREP)/H.rel(row['source'])
 payload[H.rel(row['path'])]=H.read(source,row['bytes'],row['sha256'])
assert len(payload)==327
stage=ROOT.parent/('has-prepared-map-editor64-'+str(time.time_ns()));stage.mkdir();(stage/'jobs').mkdir()
worker=H.read(KIT/'gated_headless_worker.py',6656,'4955af943d021ba0023d6617f981ece106dfd897bb561a50144377cab0181b69').decode()
old="('res://tests/import_capability_summary_unit.gd','res://tests/import_capability_app_headless.gd')"
assert worker.count(old)==1 and worker.count('<=180')==1
worker=worker.replace(old,"('res://tests/prepared_map_editor_smoke.gd',)").replace('<=180','<=240')
(stage/'gated_headless_worker.py').write_text(worker)
R.HERE=stage
parent=dict(os.environ);runtime={};result={'format':'has_prepared_map64_root_1','status':'FAIL','checks':0,'jobs':[],
 'baseline_revision':BASE,'source_manifest_sha256':sha(manifest_raw),'conversion_rerun':False,'graphics_executed':False,
 'Full_claimed':False,'appearance_qualified':False,'application_adopted':False,'stage':str(stage)}
class Logs:
 MAX_LOG=8*1024*1024
 @staticmethod
 def validate_logs(h,job,record):
  stdout=h.read(record/'godot-stdout.log',limit=Logs.MAX_LOG).decode('utf-8','replace')
  logs=stdout+h.read(record/'godot-stderr.log',limit=Logs.MAX_LOG).decode('utf-8','replace')+h.read(Path(job['args'][job['args'].index('--log-file')+1]),limit=Logs.MAX_LOG).decode('utf-8','replace')
  assert not re.search(r'ERROR:|SCRIPT ERROR|FAIL |leaked|orphan|WARNING:',logs)
  if job['expected_checks']==0:
   assert not any(x.startswith(('PASS ','PREPARED_MAP_EDITOR ')) for x in stdout.splitlines());return {'checks':0,'failures':0}
  rows=[json.loads(x.removeprefix('PREPARED_MAP_EDITOR ')) for x in stdout.splitlines() if x.startswith('PREPARED_MAP_EDITOR ')]
  assert len(rows)==1;value=rows[0];assert value['checks']==32 and value['failures']==0
  assert sum(x.startswith('PASS ') for x in stdout.splitlines())==32
  assert value['actual_current_app_and_SourceImport_completion'] is True and value['actual_Model_API_used'] is True
  assert all(value[k] is False for k in ('conversion_rerun','graphics_executed','artist_appearance_qualified','Full_qualification_claimed','application_source_modified'))
  case=H.parse(H.read(Path(job['args'][-2])/'result.json'));assert case==value
  return value
error=None
try:
 for maprow in private['maps']:
  name=maprow['name'];studio=stage/name/'Studio';studio.mkdir(parents=True)
  for rel,raw in payload.items():
   target=studio/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  asset=studio/'Assets/map';asset.mkdir(parents=True);files={}
  for key,leaf in [('scene','scene.glb'),('parameters','parameters.json'),('entities','entities.json')]:
   row=maprow['files'][key];p=asset/leaf;p.write_bytes(H.read(row['path'],row['bytes'],row['sha256']));files[key]={**row,'path':p.as_posix()}
  config=asset/'config.json';config.write_text(json.dumps({'name':name,'files':files,'expected':maprow['expected']},indent=2)+'\n')
  profile='HAS prepared map '+name+' '+str(time.time_ns())
  (studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n')
  owned={p:p.read_bytes() for p in studio.rglob('*') if p.is_file()};assert len(owned)==332;runtime.update(owned)
  env={}
  for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
   p=stage/name/'User'/leaf;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
  env['HYBRID_PYTHON']=Path(sys.executable).as_posix()
  for parse in (True,False):
   label=name+('-parse' if parse else '-actual')
   args=[engine,'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(stage/name/(label+'.engine.log'))]
   if parse:args+=['--check-only']
   args+=['--script','res://tests/prepared_map_editor_smoke.gd']
   if not parse:args+=['--',str(config),str(studio/'output/case'),profile]
   # Existing trusted worker has three retained logical lane names only.
   lane=stage/label;lane.mkdir()
   job={'name':'unit','args':args,'cwd':str(studio),'studio':str(studio),'timeout_seconds':240,'expected_checks':0 if parse else 32,'environment_overrides':env}
   value=R.run_case(H,Logs,J,L,job,lane,used,result);result['checks']+=value['checks'];result['jobs'][-1]['map']=name;result['jobs'][-1]['parse_only']=parse
   print(json.dumps({'case':label,'checks':value['checks'],'status':'PASS'}),flush=True)
 assert result['checks']==64 and len(result['jobs'])==4;result['status']='PASS'
except BaseException as exc:error=exc;result['error_type']=type(exc).__name__;result['error']=str(exc)
finally:
 result['all_jobs_closed']=all(x.get('wrapper_reaped') and x.get('wrapper_handle_closed') and x.get('active_zero_before_close') and x.get('job_closed') for x in result['jobs'])
 result['source_and_environment_preserved']=F.snapshot()==before and F.git('rev-parse','HEAD')==BASE and dict(os.environ)==parent
 result['runtime_preserved']=all(H.read(p)==raw for p,raw in runtime.items())
 result['input_preservation_failures']=H.preserve()
 if not result['all_jobs_closed'] or not result['source_and_environment_preserved'] or not result['runtime_preserved'] or result['input_preservation_failures']:result['status']='FAIL'
 (stage/'ROOT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='PASS' and error is None else 1)
