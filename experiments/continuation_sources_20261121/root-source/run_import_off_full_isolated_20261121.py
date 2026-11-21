"""Own the unchanged full verifier coordinator with fresh per-run user folders."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--checkout',type=Path,required=True);p.add_argument('--revision',required=True);a=p.parse_args()
root=a.checkout.resolve(strict=True)
assert root.parent==Path('C:/a/Programming/cloudflare') and root.name.startswith('has-import-off-full-20261121-')
assert os.name=='nt' and sys.flags.optimize==0
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=root).decode().strip()
assert git('rev-parse','HEAD')==a.revision
parent=dict(os.environ);folder=root/'output'/('root-full-launch-'+str(time.time_ns()));folder.mkdir()
env=dict(parent)
for key in tuple(env):
 if key.startswith('HYBRID_'):env.pop(key)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
 path=folder/'User'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
env['PYTHONDONTWRITEBYTECODE']='1'
script=root/'experiments/reference_body_20261120/run_full.py'
script_before=hashlib.sha256(script.read_bytes()).hexdigest()
args=[sys.executable,'-B','-u',str(script),'--revision',a.revision,
 '--fixture-root','C:/a/Programming/cloudflare/has-acceptance-session-20261111/output',
 '--sourceio','C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff/output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647']
start=time.time_ns()
with (folder/'coordinator-stdout.log').open('xb') as out,(folder/'coordinator-stderr.log').open('xb') as err:
 child=subprocess.Popen(args,cwd=root,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 launch={'format':'has_import_off_full_outer_launch_1','revision':a.revision,'checkout':str(root),'pid':child.pid,'started_ns':start,
 'coordinator_sha256':script_before,'child_environment':{k:env[k] for k in ('APPDATA','LOCALAPPDATA','TEMP','TMP','PYTHONDONTWRITEBYTECODE')},
 'parent_environment_changed':False,'hidden_console':True,'graphical_tests_must_use_private_desktops':True}
 (folder/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
 print(json.dumps({'folder':str(folder),'coordinator_pid':child.pid,'revision':a.revision}),flush=True)
 code=child.wait()
result={'format':'has_import_off_full_outer_completion_1','exit':code,'pid':child.pid,'child_reaped':child.poll() is not None,
 'parent_environment_unchanged':dict(os.environ)==parent,'coordinator_source_unchanged':hashlib.sha256(script.read_bytes()).hexdigest()==script_before,
 'revision_unchanged':git('rev-parse','HEAD')==a.revision,'seconds':(time.time_ns()-start)/1e9,'launch':launch}
(folder/'completion.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
raise SystemExit(code if all(result[k] for k in ('child_reaped','parent_environment_unchanged','coordinator_source_unchanged','revision_unchanged')) else 1)
