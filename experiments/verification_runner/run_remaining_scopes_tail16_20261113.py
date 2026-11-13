"""Run the previously unrun canonical suffix as SCOPED checks, never a full aggregate."""
from pathlib import Path
import argparse,ast,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
if ROOT.name=='output': ROOT=ROOT.parent
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
def require(ok,why):
 if not ok:raise RuntimeError(why)
def source():
 files=[p for d in ['src','tests','tools','data','examples'] for p in (ROOT/d).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
 files += [ROOT/n for n in ['project.godot','main.tscn','run.py','launch.pyw']]
 return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
def schedule():
 tree=ast.parse((ROOT/'tests/verify.py').read_text(encoding='utf-8'));main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main');out=[];tail=False;motions=None
 for node in main.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='contact_suites' for t in node.targets):
   rows=ast.literal_eval(node.value);names=[n for n,_ in rows];index=names.index('physics')+1
   out += [{'name':'contact_'+n,'script':'tests/verify_contact_'+n+'.py','report':'contact-'+n+'-verification.json','timeout':deadline} for n,deadline in rows[index:]];tail=True;continue
  if not tail:continue
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='motion_suites' for t in node.targets):
   motions=ast.literal_eval(node.value);out += [{'name':'motion_'+n,'script':script,'report':report,'timeout':deadline} for n,script,report,deadline in motions];continue
  if not isinstance(node,ast.Assign) or not isinstance(node.value,ast.Call) or not isinstance(node.value.func,ast.Name) or node.value.func.id!='run':continue
  call=node.value
  if not call.args or not isinstance(call.args[0],ast.List):continue
  args=call.args[0].elts
  if len(args)!=3 or not isinstance(args[1],ast.Constant) or args[1].value!='-u' or not isinstance(args[2],ast.Constant):continue
  script=args[2].value
  require(script.startswith('tests/verify_') and script.endswith('.py'),'Unexpected suffix command')
  following=main.body[main.body.index(node)+1:main.body.index(node)+4];reports=[x.right.value for stmt in following for x in ast.walk(stmt) if isinstance(x,ast.BinOp) and isinstance(x.op,ast.Div) and isinstance(x.left,ast.Name) and x.left.id=='output' and isinstance(x.right,ast.Constant) and isinstance(x.right.value,str) and x.right.value.endswith('-verification.json')]
  require(len(set(reports))==1,'Ambiguous report for '+script);deadline=next((ast.literal_eval(k.value) for k in call.keywords if k.arg=='timeout'),120)
  out.append({'name':Path(script).stem.removeprefix('verify_'),'script':script,'report':reports[0],'timeout':deadline})
 require(len(out)==36 and len({x['script'] for x in out})==len(out),'Unexpected canonical suffix membership')
 return out
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-scopes',action='store_true');p.add_argument('--expected-revision');p.add_argument('--folder',type=Path);p.add_argument('--start-after');a=p.parse_args();rows=schedule()
 if a.start_after:
  names=[row['name'] for row in rows];require(a.start_after in names,'Unknown explicit scope boundary');rows=rows[names.index(a.start_after)+1:]
 if not a.run_scopes:
  print(json.dumps({'count':len(rows),'scopes':rows,'graphics_started':False,'full_aggregate':False},indent=2));return
 require(a.expected_revision is not None and len(a.expected_revision)==40 and a.folder is not None,'Explicit frozen source and fresh folder required')
 folder=a.folder.absolute();require(folder.parent==ROOT/'output' and folder.name.startswith('remaining-scopes-') and not folder.exists(),'Fresh direct owned output folder required');folder.mkdir();before=source();require(before['commit']==a.expected_revision,'HEAD differs from expected revision');save(folder/'source-before.json',before);save(folder/'schedule.json',rows)
 state={'format':'has_canonical_suffix_scopes_1','full_aggregate':False,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'status':'running','pid':os.getpid(),'started_ns':time.time_ns(),'source_commit':before['commit'],'source_files':len(before['files']),'original_scope_count':36,'selected_after':a.start_after,'requested_scopes':len(rows),'results':[],'all_requested_scopes_passed':False,'source_unchanged':False}
 save(folder/'state.json',state)
 env=os.environ.copy();env.update(HYBRID_HECATIA_KRA=str(ROOT/'output/owner-fixtures/hecatia.kra'),HYBRID_NATIVE_INPUTS=r'C:\a\dump',HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',PYTHONDONTWRITEBYTECODE='1');env.pop('HYBRID_FAN_PROJECT',None)
 try:
  for i,row in enumerate(rows):
   case=folder/(f'{i+1:02d}-'+row['name']);case.mkdir();started=time.time_ns();args=[str(PYTHON),'-u',row['script']];save(case/'command.json',args);result=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=row['timeout'],creationflags=subprocess.CREATE_NO_WINDOW);(case/'process.log').write_text(result.stdout+result.stderr,encoding='utf-8');item={**row,'exit':result.returncode,'elapsed_s':(time.time_ns()-started)/1e9,'case':str(case.relative_to(ROOT)),'passed':False};state['results'].append(item)
   require(result.returncode==0,'Wrapper failed: '+row['name'])
   report=ROOT/'output'/row['report'];require(report.is_file() and report.stat().st_mtime_ns>=started,'Fresh report absent: '+row['name']);data=report.read_bytes();(case/'report.json').write_bytes(data);v=json.loads(data);item['report_sha256']=hashlib.sha256(data).hexdigest()
   if 'failures' in v:require(v['failures']==0,'Reported failures: '+row['name'])
   if row['name']=='contact_persistence':require(v['writer']['failures']==0 and all(x['failures']==0 for x in v['readers'].values()),'Contact reader/writer failure')
   if row['name'] in ['contact_viewport','motion_editor']:require(v['reader']['failures']==0,'Fresh reader failure')
   if row['name']=='project_duration':require(v['failures']==0 and len(v['fresh_readers'])==4,'Project duration readers incomplete')
   item['passed']=True;save(case/'verification.json',item);save(folder/'state.json',state);print('PASS '+row['name'],flush=True)
  state['all_requested_scopes_passed']=True;state['status']='passed_scopes_only'
 except BaseException as e:
  state['status']='failed';state['error']=type(e).__name__+': '+str(e);raise
 finally:
  after=source();save(folder/'source-after.json',after);state['source_unchanged']=before==after;state['finished_ns']=time.time_ns();state['full_aggregate']=False
  if not state['source_unchanged']:state['status']='source_changed';state['all_requested_scopes_passed']=False
  save(folder/'state.json',state)
 require(state['all_requested_scopes_passed'] and state['source_unchanged'],'Scoped suffix incomplete')
if __name__=='__main__':main()