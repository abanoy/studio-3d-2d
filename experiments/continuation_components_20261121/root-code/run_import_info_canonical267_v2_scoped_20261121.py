"""Qualify the new ordinary component verifier, not a whole Full or native asset."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
PREP=OUT/'source-import-capability-canonical-c315-v2-prep-20261121';OLD=OUT/'source-import-capability-c315-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
F=module('_info_component_source_snapshot',ROOT/'experiments/reference_body_20261120/run_full.py')
assert F.git('rev-parse','HEAD')==REV
before=F.snapshot();assert len(before)==1103
pins_raw=(PREP/'SOURCE_PINS.json').read_bytes();assert sha(pins_raw)=='0cc2240218def0037cfe0377d22a0c22f772805dc07f967c5144b0d0dce66977'
protected={PREP/'SOURCE_PINS.json':pins_raw}
for row in json.loads(pins_raw)['files']:
 path=PREP/row['path'];raw=path.read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];protected[path]=raw
targets=json.loads((PREP/'TARGETS.json').read_bytes())['targets'];assert len(targets)==10
production=[r for r in targets if r['path'].startswith('src/')];assert len(production)==5
for row in production:assert (PREP/'payload'/row['path']).read_bytes()==(OLD/'payload'/row['path']).read_bytes()
stage=ROOT.parent/('has-import-info-canonical267-v2-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio'
builder=module('_info_component_git_builder',ROOT/'tools/build_owner_review_snapshot.py')
revision,base=builder.freeze_source(ROOT,studio,REV,runtime_scope=True);assert revision==REV and len(base)==1106
for row in targets:
 target=studio/row['path'];raw=protected[PREP/'payload'/row['path']]
 if row['operation']=='replace':
  previous=target.read_bytes();assert len(previous)==row['base_bytes'] and sha(previous)==row['base_sha256']
 else:assert row['operation']=='new' and not target.exists()
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS Import info qualification '+str(time.time_ns())+'"\n')
runtime={p:p.read_bytes() for p in studio.rglob('*') if p.is_file()};assert len(runtime)==1113
parent=dict(os.environ);env=dict(parent)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 p=stage/'User'/leaf;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,HYBRID_GODOT='C:/a/tools/Godot/Godot_v4.6-stable_win64.exe',HYBRID_FFMPEG='C:/Program Files/ffmpeg/bin/ffmpeg.exe')
report_dir=studio/'output/component267';start=time.time_ns()
argv=[sys.executable,'-B','-u','tests/verify_import_capability.py','--scope','all','--output',str(report_dir)]
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
 child=subprocess.Popen(argv,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 (stage/'launch.json').write_text(json.dumps({'pid':child.pid,'started_ns':start,'argv':argv,'source_manifest_sha256':sha(pins_raw),'scope':'ordinary component all267, no Full'},indent=2)+'\n')
 print(json.dumps({'stage':str(stage),'pid':child.pid,'scope':'public verifier267'}),flush=True)
 try:code=child.wait(timeout=4200)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=10)
report_path=report_dir/'verification.json';value=json.loads(report_path.read_bytes()) if report_path.exists() else {}
preserved=F.snapshot()==before and F.git('rev-parse','HEAD')==REV and dict(os.environ)==parent
preserved=preserved and all(p.read_bytes()==raw for p,raw in {**protected,**runtime}.items())
flags=('all_admitted_sources_unchanged','all_runtime_sources_unchanged','parent_environment_preserved','all_private_jobs_and_desktops_closed','all_writer_trees_restored')
passed=code==0 and preserved and value.get('status')=='PASS' and value.get('checks')==267 and all(value.get(k) is True for k in flags)
passed=passed and len(value.get('cases',[]))==21 and len(value.get('pairs',[]))==8 and report_path.stat().st_mtime_ns>=start
result={'format':'has_import_info_canonical267_root_v2_1','status':'PASS' if passed else 'FAIL','component_checks':value.get('checks',0),
 'pid':child.pid,'exit':code,'reaped':child.poll() is not None,'Main_source_proposed_runtime_and_environment_preserved':preserved,
 'baseline_revision':REV,'source_manifest_sha256':sha(pins_raw),'runtime_input_files':1113,
 'public_verifier_integration':True,'CPU_and_GUI_single_component_batch':True,'whole_Full_claimed':False,
 'native_or_owner_assets_read':False,'adopted':False,'stage':str(stage),'case_count':len(value.get('cases',[])),
 'pair_count':len(value.get('pairs',[])),'component_flags':{k:value.get(k) for k in flags},
 'report_sha256':sha(report_path.read_bytes()) if report_path.exists() else None,'seconds':(time.time_ns()-start)/1e9}
(stage/'ROOT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(0 if passed else 1)
