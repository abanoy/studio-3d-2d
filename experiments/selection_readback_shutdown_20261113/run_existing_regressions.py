from pathlib import Path
import json,subprocess,sys,time,hashlib
root=Path.cwd();sys.path.insert(0,str(root));from run import command
out=root/'output'/('pick-fix-regressions-'+str(time.time_ns()));out.mkdir()
source=root/'src/world_selection.gd';frozen=hashlib.sha256(source.read_bytes()).hexdigest()
results=[]
for label,script,marker in [('world_selection','tests/world_selection_smoke.gd','WORLD_SELECTION_SMOKE '),('world_edit','tests/world_edit_smoke.gd','WORLD_EDIT_SMOKE ')]:
 args=command(script,extra=[]);p=subprocess.run(args,cwd=root,capture_output=True,encoding='utf-8',errors='replace',timeout=300);log=p.stdout+p.stderr;(out/(label+'.log')).write_text(log,encoding='utf-8')
 receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());item={'name':label,'command':args,'exit':p.returncode,'receipt':r,'log_sha256':hashlib.sha256(log.encode()).hexdigest()};results.append(item)
 (out/'progress.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 assert p.returncode==0 and marker in log and not any(s in log for s in ['SCRIPT ERROR','ERROR:','FAIL ','ObjectDB instances leaked','unclaimed string names','Pages in use exist']),log[-5000:]
 result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;item['result']=result
 assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
 assert hashlib.sha256(source.read_bytes()).hexdigest()==frozen
p=subprocess.run([sys.executable,'-u','tests/verify_scene_view.py'],cwd=root,capture_output=True,encoding='utf-8',errors='replace',timeout=500)
(out/'scene_view.log').write_text(p.stdout+p.stderr,encoding='utf-8');results.append({'name':'scene_view','exit':p.returncode});assert p.returncode==0,(p.stdout+p.stderr)[-5000:]
assert hashlib.sha256(source.read_bytes()).hexdigest()==frozen
(out/'result.json').write_text(json.dumps({'source_sha256':frozen,'results':results},indent=2),encoding='utf-8');print(out)
