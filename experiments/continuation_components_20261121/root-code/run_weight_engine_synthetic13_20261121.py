"""Separate synthetic ArrayMesh API check. No native inputs or Full admission."""
from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'output/source-miku-contact-c315-1103-successor-prep-20261121'
ENGINE=Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
manifest=PREP/'SOURCE_PINS.json';manifest_raw=manifest.read_bytes()
assert hashlib.sha256(manifest_raw).hexdigest()=='7a7fa46b26ff626d6f3a157679523c92192bdc48af39649239eca770e95bc60b'
pins=json.loads(manifest_raw)['files'];selected=('payload/src/godot_skin_weight_conversion.gd','payload/tests/godot_skin_weight_engine_conformance.gd')
sources={manifest:manifest_raw}
for name in selected:
 row=next(r for r in pins if r['path']==name);raw=(PREP/name).read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];sources[PREP/name]=raw
assert hashlib.sha256(ENGINE.read_bytes()).hexdigest()=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
stage=ROOT.parent/('has-weight-engine-synthetic13-'+str(time.time_ns()));stage.mkdir();studio=stage/'Studio';studio.mkdir()
for path,raw in sources.items():
 if path.is_relative_to(PREP/'payload'):
  target=studio/path.relative_to(PREP/'payload');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(studio/'project.godot').write_text('[application]\nconfig/name="Synthetic weight API check"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
(studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS synthetic weights '+str(time.time_ns())+'"\n')
runtime={p:p.read_bytes() for p in studio.rglob('*') if p.is_file()};assert len(runtime)==4
parent=dict(os.environ);env=dict(parent)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 p=stage/'User'/leaf;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
env['PYTHONDONTWRITEBYTECODE']='1'
argv=[str(ENGINE),'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(stage/'engine.log'),'--script','res://tests/godot_skin_weight_engine_conformance.gd']
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
 child=subprocess.Popen(argv,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=child.wait(timeout=35)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=5)
stdout=(stage/'stdout.log').read_text();logs=stdout+(stage/'stderr.log').read_text()+(stage/'engine.log').read_text()
marker='GODOT_SKIN_WEIGHT_ENGINE_CONFORMANCE '
lines=[line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)];value=json.loads(lines[0]) if len(lines)==1 else {}
preserved=all(p.read_bytes()==raw for p,raw in {**sources,**runtime}.items()) and dict(os.environ)==parent
passed=code==0 and preserved and value.get('checks')==13 and value.get('failures')==0
passed=passed and len([line for line in stdout.splitlines() if line.startswith('PASS ')])==13 and not any(bad in logs for bad in ('ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked'))
result={'format':'has_synthetic_weight_engine13_root_1','status':'PASS' if passed else 'FAIL','checks':value.get('checks',0),
 'pid':child.pid,'exit':code,'reaped':child.poll() is not None,'source_runtime_and_environment_preserved':preserved,
 'synthetic_only':True,'native_inputs_read':False,'graphics_executed':False,'native_slot_conversion_qualified':False,
 'shader_equivalence_qualified':False,'capsule_contact_qualified':False,'application_adopted':False,'Full_admission_claimed':False,
 'separate_from_frozen_Miku_host':True,'stage':str(stage),'source_manifest_sha256':hashlib.sha256(manifest_raw).hexdigest()}
(stage/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(0 if passed else 1)
