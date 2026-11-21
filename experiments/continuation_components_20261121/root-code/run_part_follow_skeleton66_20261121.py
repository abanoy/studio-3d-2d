"""Execute only the isolated actual-Model synthetic Skeleton controller fixture."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,stat,subprocess,time
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'output/source-character-pose-follow-controller-prep-20261121'
ENGINE=Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
def safe_relative(name):
 p=PurePosixPath(name);assert not p.is_absolute() and all(x not in ('.','..') and ':' not in x for x in p.parts);return Path(*p.parts)
def read(path):
 s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 raw=path.read_bytes();after=path.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns);return raw
manifest=PREP/'SOURCE_PINS.json';manifest_raw=read(manifest);assert hashlib.sha256(manifest_raw).hexdigest()=='98e123065b42cdccd38e8e5348b27ac6fcc6db50517789786bbf3a7ea0a94963'
inputs={manifest:manifest_raw}
for row in json.loads(manifest_raw)['files']:
 p=PREP/safe_relative(row['path']);raw=read(p);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];inputs[p]=raw
closure=json.loads(inputs[PREP/'RUNTIME_SOURCE_CLOSURE.json']);assert closure['file_count']==46 and len(closure['files'])==46
payload={}
for row in closure['files']:
 assert row['source_domain'] in ('candidate','current_readonly_source')
 source=(PREP if row['source_domain']=='candidate' else ROOT)/safe_relative(row['source'])
 raw=read(source);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];inputs[source]=raw
 assert row['path'] not in payload;payload[row['path']]=raw
assert hashlib.sha256(ENGINE.read_bytes()).hexdigest()=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
stage=ROOT.parent/('has-part-follow-skeleton66-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio';studio.mkdir()
for name,raw in payload.items():
 p=studio/safe_relative(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
(studio/'project.godot').write_bytes(inputs[PREP/'payload/project.godot'])
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS Skeleton follow synthetic '+str(time.time_ns())+'"\n')
runtime={p:p.read_bytes() for p in studio.rglob('*') if p.is_file()};assert len(runtime)==48
parent=dict(os.environ);env=dict(parent)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 p=stage/'User'/leaf;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
env['PYTHONDONTWRITEBYTECODE']='1'
argv=[str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(stage/'engine.log'),'--script','res://tests/part_pose_follow_controller_unit.gd']
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
 child=subprocess.Popen(argv,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=child.wait(timeout=60)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=5)
stdout=(stage/'stdout.log').read_text();logs=stdout+(stage/'stderr.log').read_text()+(stage/'engine.log').read_text()
prefix='PART_POSE_FOLLOW_CONTROLLER ';rows=[x[len(prefix):] for x in stdout.splitlines() if x.startswith(prefix)]
value=json.loads(rows[0]) if len(rows)==1 else {}
preserved=all(read(p)==raw for p,raw in {**inputs,**runtime}.items()) and dict(os.environ)==parent
passed=code==0 and preserved and value.get('checks')==66 and value.get('failures')==0 and sum(x.startswith('PASS ') for x in stdout.splitlines())==66
passed=passed and all(value.get(k) is True for k in ('synthetic_only','actual_Model_API_used','actual_Skeleton3D_used'))
passed=passed and all(value.get(k) is False for k in ('actual_native_bindings_qualified','actual_native_alignment_qualified','application_adopted','SecondaryLive_integration_qualified'))
passed=passed and not any(x in logs for x in ('ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked'))
result={'format':'has_part_follow_skeleton66_root_1','status':'PASS' if passed else 'FAIL','checks':value.get('checks',0),'failures':value.get('failures'),
 'pid':child.pid,'exit':code,'reaped':child.poll() is not None,'runtime_files':48,'all_source_runtime_and_environment_preserved':preserved,
 'synthetic_only':True,'native_inputs_read':False,'graphics_executed':False,'actual_Model_API_used':value.get('actual_Model_API_used',False),
 'actual_Skeleton3D_used':value.get('actual_Skeleton3D_used',False),'native_binding_or_appearance_qualified':False,'application_adopted':False,
 'Full_qualification_claimed':False,'stage':str(stage),'source_manifest_sha256':hashlib.sha256(manifest_raw).hexdigest()}
(stage/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(0 if passed else 1)
