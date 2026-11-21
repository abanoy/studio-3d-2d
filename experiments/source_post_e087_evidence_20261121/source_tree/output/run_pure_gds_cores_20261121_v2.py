"""Root-owned pure GDS easing/contact-math checks; no app, asset or rendering claim."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'output/source-headless-component-coordinator-v3-prep-20261121/run_components.py'
raw=HELPER.read_bytes()
assert len(raw)==21619 and hashlib.sha256(raw).hexdigest()=='7b146fd5ad8aabb80f4b3542dd02ce6416d26ab36d209c1ca754a926d954c8ad'
spec=importlib.util.spec_from_file_location('_qualified_headless_jobs',HELPER)
H=importlib.util.module_from_spec(spec);sys.modules[spec.name]=H;spec.loader.exec_module(H)
assert H.ROOT==ROOT and os.name=='nt' and sys.version_info[:2]==(3,13)
H.read(HELPER,21619,'7b146fd5ad8aabb80f4b3542dd02ce6416d26ab36d209c1ca754a926d954c8ad')
assert H.head()=='e0879c7df74bc3704902bfdaf4ff74eee40c3aea'
lock=H.parse(H.read(ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json',digest='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'))
runtime=lock['runtime_paths']
assert Path(sys.executable).resolve()==Path(runtime['python']).resolve()
for p,pin in lock['runtime_executables'].items():
 H.read(p,pin['bytes'],pin['sha256']);assert Path(p).stat().st_mtime_ns==pin['mtime_ns']
H.read(ROOT/'tools/private_desktop.py',digest='c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61')
cases=[{'id':'easing','unit':'tests/keyframe_easing_math_unit.gd','count':24,'marker':'KEYFRAME_EASING_MATH_UNIT ','flag':'native_or_gpu_started','files':[
 ('output/source-keyframe-easing-prep-20261121/payload/src/keyframe_easing.gd','src/keyframe_easing.gd',7179,'08aacb9df9317ce2dd8329e5d9f6de35d771e8b3b07e1cabf58bf621891a65b7'),
 ('output/source-keyframe-easing-prep-20261121/payload/tests/keyframe_easing_math_unit.gd','tests/keyframe_easing_math_unit.gd',6289,'f329ea9d29f7eb346b43e0f804d9ca72421e6dc93fd598dd5c1772ed16d04b55'),
 ('output/source-keyframe-easing-prep-20261121/bases/timeline.gd','src/timeline.gd',2878,'2cd69b4ae0b2fe546064bd318301fc1c7cd6ac8f7c9cadf91730a473ee36f835')]},
 {'id':'contact_math','unit':'tests/secondary_collision_geometry_unit.gd','count':26,'marker':'COLLISION_GEOMETRY_UNIT ','flag':'native_asset_tested','files':[
 ('output/source-miku-collision-geometry-v2-prep-20261121/secondary_collision_geometry.gd','src/secondary_collision_geometry.gd',5190,'63f75e7cae189fad1dab190302c7218f94ae3d4910b3eb9319e4f0a1b54e6cc2'),
 ('output/source-miku-collision-geometry-v2-prep-20261121/secondary_collision_geometry_unit.gd','tests/secondary_collision_geometry_unit.gd',4542,'6f23d6bf84beba91c6eb4237eeaa62ef71e86e0ec1f9dd4c072f8a54ad5f16de')]}]
blobs={}
for case in cases:
 for src,_target,n,digest in case['files']:blobs[src]=H.read(ROOT/src,n,digest)
stage=ROOT/'output'/('pure-gds-core-'+str(time.time_ns()));stage.mkdir()
result={'format':'has_pure_gds_core_root_1','status':'FAIL','stage':str(stage),'suites':[],'application_adopted':False,'native_assets_tested':False,'gui_render_or_actual_contact_qualified':False}
primary=None
try:
 for case in cases:
  folder=stage/case['id'];folder.mkdir();studio=folder/'Project';studio.mkdir()
  for src,target,n,digest in case['files']:
   path=studio/target;path.parent.mkdir(parents=True,exist_ok=True);H.new(path,blobs[src])
  private_source=studio/'tools/private_desktop.py';private_source.parent.mkdir(parents=True,exist_ok=True)
  H.new(private_source,H.read(ROOT/'tools/private_desktop.py',digest='c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61'))
  H.new(studio/'project.godot',b'config_version=5\n[application]\nconfig/name="HAS pure core qualification"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
  for item in ['Roaming','Local','Temp']:(folder/item).mkdir()
  env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',APPDATA=str(folder/'Roaming'),LOCALAPPDATA=str(folder/'Local'),TEMP=str(folder/'Temp'),TMP=str(folder/'Temp'))
  row={'id':case['id'],'status':'FAIL','jobs':[]};result['suites'].append(row)
  stdout=H.job(studio,folder,'unit',['--log-file',str(folder/'engine.log'),'--script','res://'+case['unit']],runtime,env,row['jobs'])
  matches=[line[len(case['marker']):] for line in stdout.splitlines() if line.startswith(case['marker'])]
  H.need(len(matches)==1,'EXACT_COMPLETE_MARKER_REQUIRED');value=H.parse(matches[0])
  H.need(type(value.get('checks')) is int and value['checks']==case['count'] and type(value.get('failures')) is int and value['failures']==0 and value.get('application_adopted') is False and value.get(case['flag']) is False,'COMPLETE_SCOPE_COUNTS_REQUIRED')
  H.need(sum(line.startswith('PASS ') for line in stdout.splitlines())==case['count'],'NAMED_ASSERTION_COUNT')
  H.need('ObjectDB instances leaked' not in stdout,'ENGINE_OBJECT_LEAK')
  row.update(status='PASS',checks=case['count']);result['status']='PASS'
except BaseException as error:
 primary=error;result.update(status='FAIL',error_type=type(error).__name__,error=str(error)[:200])
finally:
 for process,row in H.OWNED:row['reaped']=H.reap(process)
 result['all_owned_launchers_reaped']=all(row['reaped'] for _p,row in H.OWNED)
 result['all_private_jobs_closed']=all(row['private_job_closed'] and row['desktop_closed'] for _p,row in H.OWNED)
 failures=H.preserve();result['preservation_failures']=failures;result['all_admitted_inputs_preserved']=not failures
 result['head_unchanged']=H.head()=='e0879c7df74bc3704902bfdaf4ff74eee40c3aea'
 if primary is not None or len(result['suites'])!=2 or any(row['status']!='PASS' for row in result['suites']) or failures or not result['head_unchanged'] or not result['all_owned_launchers_reaped'] or not result['all_private_jobs_closed']:result['status']='FAIL'
 result['checks']=sum(row.get('checks',0) for row in result['suites'])
 H.json_new(stage/'PUBLIC_RESULT.json',result);print(json.dumps(result),flush=True)
sys.exit(0 if result['status']=='PASS' else 1)
