"""Fresh exact-commit app subset + output-only overlay; CPU/headless only."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,uuid,importlib.util
ROOT=Path(__file__).resolve().parents[4]
TASK=ROOT/'output/helper-preview-integration-20261113/display-v2'
PIN='9897f86019dfb8499d0ee30f6560580fac7bb8da'
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
GODOT=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def write(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def safe(p,boundary):
 p=Path(p).absolute();assert p.is_relative_to(boundary.absolute()) and p!=boundary
 for part in (p,*p.parents):
  if part.exists():assert not part.is_symlink() and not (getattr(part.lstat(),'st_file_attributes',0)&0x400),part
 return p

def main():
 assert sys.executable.lower()==str(PYTHON).lower()
 assert git('rev-parse','HEAD').decode().strip()==PIN
 assert sha(GODOT)=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
 assert sha(PYTHON)=='03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
 mainpaths=[x for x in git('ls-files','src','tests','tools','project.godot','main.tscn').decode().splitlines()if(ROOT/x).is_file()]
 protected=[stamp(ROOT/x) for x in mainpaths]+[stamp(PYTHON),stamp(GODOT)]
 overlays=sorted(p for p in (TASK/'overlay').rglob('*')if p.is_file())
 for p in overlays:safe(p,TASK)
 overlay_before=[stamp(p)for p in overlays]
 harness_before=[stamp(p)for p in (TASK/'source').glob('*.py')]
 folder=TASK/'integration-runs'/(str(time.time_ns())+'-'+uuid.uuid4().hex[:8]);safe(folder,TASK);folder.mkdir(parents=True,exist_ok=False)
 studio=folder/'Studio';studio.mkdir()
 exact=git('ls-tree','-r','--name-only',PIN,'src','data','project.godot','main.tscn').decode().splitlines()
 exact+=['tools/secondary_helpers.py','tools/secondary_helpers_batch.py','tools/secondary_helper_worker.py','tools/private_desktop.py','tests/test_secondary_helpers.py']
 copies=[]
 for name in exact:
  raw=git('show',f'{PIN}:{name}');dst=studio/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);copies.append(dict(path=name,git_blob_sha256=hashlib.sha256(raw).hexdigest()))
 for src in overlays:
  dst=studio/src.relative_to(TASK/'overlay');dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
 (studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS-helper-preview-'+folder.name+'"\n',encoding='utf-8')
 spec=importlib.util.spec_from_file_location('helper_fixture',studio/'tests/test_secondary_helpers.py');factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
 source=folder/'two-panel-v1.glb';factory.two_panel_fixture(source,'v1');fixture=stamp(source)
 config=dict(folder=str(folder),source=str(source),python=str(PYTHON),code_root=str(studio),headless=True,gpu=False,profile='HAS-helper-preview-'+folder.name)
 write(folder/'config.json',config);write(folder/'source-copy.json',dict(pin=PIN,exact=copies,overlay=overlay_before))
 runtime=[stamp(p)for p in studio.rglob('*')if p.is_file()]
 write(folder/'preservation-before.json',dict(main=protected,overlay=overlay_before,harness=harness_before,runtime=runtime,fixture=fixture))
 script='res://src/app.gd' if '--check-only' in sys.argv else 'res://tests/helper_preview_integration_cpu.gd'
 cmd=[str(GODOT),'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(folder/'engine.log'),'--script',script]
 if '--check-only' in sys.argv:cmd+=['--check-only']
 else:cmd+=['--',str(folder/'config.json')]
 write(folder/'command.json',cmd)
 env=os.environ.copy();env['HYBRID_PYTHON']=str(PYTHON);env['PYTHONDONTWRITEBYTECODE']='1'
 process=subprocess.Popen(cmd,cwd=studio,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
 write(folder/'launch.json',dict(pid=process.pid,started_ns=time.time_ns(),headless=True,gpu=False))
 timedout=False
 try:out,err=process.communicate(timeout=90 if '--check-only' in sys.argv else 150)
 except subprocess.TimeoutExpired:timedout=True;process.kill();out,err=process.communicate()
 (folder/'stdout.log').write_text(out,encoding='utf-8');(folder/'stderr.log').write_text(err,encoding='utf-8')
 result=json.loads((folder/'result.json').read_bytes())if(folder/'result.json').is_file()else None
 preservation={label:all(Path(r['path']).is_file()and stamp(r['path'])==r for r in records)for label,records in [('main',protected),('overlay',overlay_before),('harness',harness_before),('runtime',runtime),('fixture',[fixture])]}
 preservation['head']=git('rev-parse','HEAD').decode().strip()==PIN
 forbidden=[x for x in ['SCRIPT ERROR','ERROR:','WARNING:','ObjectDB instances leaked','resources still in use','Orphan StringName:']if x in out+err]
 passed=not timedout and process.returncode==0 and not forbidden and all(preservation.values())and(('--check-only'in sys.argv)or(result is not None and not result['failures']))
 receipt=dict(passed=passed,exit=process.returncode,timed_out=timedout,retained_Popen_reaped=process.poll()is not None,forbidden=forbidden,preservation=preservation,checks=len(result['checks'])if result else None,headless=True,gpu=False)
 write(folder/'execution.json',receipt);print(json.dumps(dict(folder=str(folder),**receipt)),flush=True);print((out+err)[-6000:],flush=True)
 return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
