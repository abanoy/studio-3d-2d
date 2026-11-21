"""Run only the reviewed synthetic transform mathematics, with no native assets."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'output/source-character-pose-follow-prep-20261121'
ENGINE=Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
manifest=PREP/'SOURCE_PINS.json';data=manifest.read_bytes()
assert hashlib.sha256(data).hexdigest()=='9070c635a32b7379adbece0236e5cfa4b76532d3c5b30f95b031c17b977f4232'
inputs={manifest:data,ENGINE:ENGINE.read_bytes()};assert hashlib.sha256(inputs[ENGINE]).hexdigest()=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
for row in json.loads(data)['files']:
 path=PREP/row['path'];raw=path.read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];inputs[path]=raw
stage=ROOT.parent/('has-part-follow-math21-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio';studio.mkdir()
for path,raw in inputs.items():
 if path.is_relative_to(PREP/'payload'):
  target=studio/path.relative_to(PREP/'payload');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS synthetic follow '+str(time.time_ns())+'"\n')
runtime={path:path.read_bytes() for path in studio.rglob('*') if path.is_file()};assert len(runtime)==4
parent=dict(os.environ);env=dict(parent)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 path=stage/'User'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
env['PYTHONDONTWRITEBYTECODE']='1'
argv=[str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(stage/'engine.log'),'--script','res://tests/part_pose_follow_unit.gd']
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
 child=subprocess.Popen(argv,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=child.wait(timeout=40)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=5)
stdout=(stage/'stdout.log').read_text();logs=stdout+(stage/'stderr.log').read_text()+(stage/'engine.log').read_text()
lines=[line.removeprefix('PART_POSE_FOLLOW_MATH ') for line in stdout.splitlines() if line.startswith('PART_POSE_FOLLOW_MATH ')]
value=json.loads(lines[0]) if len(lines)==1 else {}
preserved=all(p.read_bytes()==raw for p,raw in {**inputs,**runtime}.items()) and dict(os.environ)==parent
passed=code==0 and preserved and len([line for line in stdout.splitlines() if line.startswith('PASS ')])==21
passed=passed and value.get('checks')==21 and value.get('failures')==0 and value.get('synthetic_only') is True
passed=passed and all(value.get(key) is False for key in ('actual_native_alignment_qualified','actual_pose_following_qualified','application_adopted'))
passed=passed and not any(bad in logs for bad in ('ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked'))
result={'format':'has_part_pose_follow_math21_root_1','status':'PASS' if passed else 'FAIL','checks':value.get('checks',0),
 'pid':child.pid,'exit':code,'reaped':child.poll() is not None,'source_runtime_and_environment_preserved':preserved,
 'synthetic_only':True,'native_inputs_read':False,'graphics_executed':False,'actual_native_alignment_qualified':False,
 'actual_pose_following_qualified':False,'application_adopted':False,'Full_admission_claimed':False,'stage':str(stage),
 'source_manifest_sha256':hashlib.sha256(data).hexdigest()}
(stage/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(0 if passed else 1)
