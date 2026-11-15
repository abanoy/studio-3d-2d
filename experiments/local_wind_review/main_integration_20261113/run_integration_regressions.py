from pathlib import Path
import ast,json,hashlib,subprocess,sys,time,os
ROOT=Path(__file__).resolve().parents[1]
def manifest():
 paths=[p for n in ['src','tests','tools','data','examples'] for p in (ROOT/n).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]+[ROOT/n for n in ['project.godot','main.tscn','run.py','launch.pyw','dependencies.json']]
 return {'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':{p.relative_to(ROOT).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in sorted(paths)}}
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 p=__import__('argparse').ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--folder',type=Path);args=p.parse_args()
 targets=['tests/verify_native_readback_lifecycle.py','tests/verify_world_selection_teardown.py','tests/verify_secondary_helpers.py','tests/verify_secondary_picking.py','tests/verify_secondary_batch.py','tests/verify_scene_view.py','tests/verify_contact_physics.py']
 tree=ast.parse((ROOT/'tests/verify.py').read_text(encoding='utf-8'));deadlines={}
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run' and node.args and isinstance(node.args[0],ast.List):
   parts=node.args[0].elts
   if len(parts)>=3 and isinstance(parts[2],ast.Constant) and parts[2].value in targets:deadlines[parts[2].value]=next((ast.literal_eval(k.value) for k in node.keywords if k.arg=='timeout'),120)
 # Contact suites are registered dynamically in the canonical runner.
 deadlines['tests/verify_contact_physics.py']=500
 assert set(targets)<=set(deadlines),deadlines
 rows=[{'script':name,'extra':[],'timeout':deadlines[name]} for name in targets]
 rows.append({'script':'tests/verify_contact_physics.py','extra':['--components'],'timeout':500})
 if not args.run:print(json.dumps(rows,indent=2));return
 folder=args.folder.absolute();assert folder.parent==ROOT/'output' and folder.name.startswith('wind-main-regressions-') and not folder.exists();folder.mkdir();before=manifest();save(folder/'source-before.json',before);save(folder/'schedule.json',rows)
 state={'format':'has_wind_main_integration_regressions_1','status':'running','source_revision':before['revision'],'source_files':len(before['files']),'pid':os.getpid(),'started_ns':time.time_ns(),'results':[],'all_requested_passed':False,'source_unchanged':False};save(folder/'state.json',state)
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['HYBRID_HECATIA_KRA']=str(ROOT/'output/owner-fixtures/hecatia.kra');env['HYBRID_NATIVE_INPUTS']=r'C:\a\dump';env['HYBRID_FFMPEG']=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe';env.pop('HYBRID_FAN_PROJECT',None)
 try:
  for i,row in enumerate(rows):
   name=Path(row['script']).stem.removeprefix('verify_')+('-components' if row['extra'] else '');case=folder/(str(i+1).zfill(2)+'-'+name);case.mkdir();command=[sys.executable,'-B','-u',row['script'],*row['extra']];save(case/'command.json',command);start=time.time_ns();run=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=row['timeout'],creationflags=subprocess.CREATE_NO_WINDOW);(case/'process.log').write_text(run.stdout+run.stderr,encoding='utf-8');item={**row,'case':str(case.relative_to(ROOT)),'exit':run.returncode,'elapsed_seconds':(time.time_ns()-start)/1e9,'passed':run.returncode==0};state['results'].append(item);save(folder/'state.json',state);assert item['passed'],name;print('PASS '+name,flush=True)
  state['status']='passed_scopes_only';state['all_requested_passed']=True
 except BaseException as error:state['status']='failed';state['error']=type(error).__name__+': '+str(error);raise
 finally:
  after=manifest();save(folder/'source-after.json',after);state['source_unchanged']=before==after;state['finished_ns']=time.time_ns()
  if before!=after:state['status']='source_changed';state['all_requested_passed']=False
  save(folder/'state.json',state)
 assert state['all_requested_passed'] and state['source_unchanged'],state
if __name__=='__main__':main()
