"""Run the unchanged final media function left unrun by the failed aggregate."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
CONTROL=Path(__file__).resolve().parent;ROOT=CONTROL.parent.parent/'has-import-off-full-20261121-c31576d'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
F=load('_final_media_source_snapshot',ROOT/'experiments/reference_body_20261120/run_full.py')
V=load('_canonical_final_media',ROOT/'tests/verify.py')
assert V.ROOT==ROOT and F.git('rev-parse','HEAD')==REV
spike=ROOT/'output/canonical-spikes/1795260532525033100';assert spike.is_dir() and not (spike/'tone').exists()
assert len(list(spike.glob('frame_*.png')))==48
before=F.snapshot();assert len(before)==1103
prior={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'output/private-desktop').glob('*.json')}
parent=dict(os.environ);folder=ROOT/'output'/('final-media-scope-'+str(time.time_ns()));folder.mkdir()
env=dict(parent)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 p=folder/'User'/leaf;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,HYBRID_GODOT='C:/a/tools/Godot/Godot_v4.6-stable_win64.exe',HYBRID_FFMPEG='C:/Program Files/ffmpeg/bin/ffmpeg.exe')
ordinary_run=V.run
def hidden_run(args,timeout=120,**kwargs):
 assert 'env' not in kwargs and 'creationflags' not in kwargs
 return ordinary_run(args,timeout=timeout,env=env,creationflags=subprocess.CREATE_NO_WINDOW,**kwargs)
V.run=hidden_run
result={'format':'has_c315_final_media_scope_1','status':'FAIL','revision':REV,'results':{},'canonical_function_source_unchanged':True,
 'launch_context_only':'Caller supplies fresh child user folders and CREATE_NO_WINDOW; assertions/function source unchanged.',
 'failed_Full_reclassified':False,'whole_verifier_pass_claimed':False,'human_device_acceptance_claimed':False,'folder':str(folder)}
error=None
try:
 V.verify_media(ROOT/'output',spike,result['results'])
 movies=[k for k in result['results'] if k.endswith('_video') or k.startswith('posed_model_video_')]
 assert len(movies)==21
 result['status']='SCOPED_MEDIA21_PASS_NOT_FULL';result['movie_groups']=movies
except BaseException as exc:error=repr(exc);result['error']=error
finally:
 rows=[]
 for p in (ROOT/'output/private-desktop').glob('*.json'):
  raw=p.read_bytes()
  if p.name in prior:assert hashlib.sha256(raw).hexdigest()==prior[p.name]
  else:rows.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'value':json.loads(raw)})
 closed=all(all(r['value'].get(k) is True for k in ('job_closed','desktop_closed','child_desktop_confirmed','private_window_seen'))
  and r['value'].get('foreground_child_observed') is False and r['value'].get('desktop_switch_requested') is False and r['value'].get('exit')==0 for r in rows)
 result.update(source_and_head_unchanged=F.snapshot()==before and F.git('rev-parse','HEAD')==REV,parent_environment_preserved=dict(os.environ)==parent,
  private_jobs=rows,all_private_jobs_isolated_closed=closed,private_job_count=len(rows))
 if error or not closed or not result['source_and_head_unchanged'] or not result['parent_environment_preserved'] or len(rows)!=1:result['status']='FAIL'
 (folder/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('results','private_jobs')}),flush=True)
raise SystemExit(0 if result['status']=='SCOPED_MEDIA21_PASS_NOT_FULL' else 1)
