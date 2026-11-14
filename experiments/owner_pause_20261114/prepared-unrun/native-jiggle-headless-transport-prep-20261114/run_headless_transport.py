"""UNRUN locked headless driver. Root must grant a fresh post-full runtime lease.
Default invocation cannot start an engine. Never imports app/model parsers; only
frozen run.py constructs the headless command after all explicit launch gates.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,stat,subprocess,sys,time
sys.dont_write_bytecode=True
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]
QUALIFIED='f380729cb170682068017b0d4c29b5f8425cdd14'
BAD=('ERROR:','WARNING:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked','unclaimed string names','Pages in use exist at exit','resources still in use')
def need(ok,detail):
 if not ok:raise RuntimeError(detail)
def no_links(path):
 for p in[path,*path.parents]:
  try:s=p.lstat()
  except FileNotFoundError:continue
  need(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400,'Link/reparse path refused')
def identity(p):
 no_links(p);p=p.resolve(strict=True);s=p.stat();need(p.is_file(),'Regular input required')
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 t=p.stat();need((s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)==(t.st_size,t.st_mtime_ns,t.st_ino,t.st_dev),'Input changed while hashing');return {'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':h}
def load(p):
 need(p.stat().st_size<=16*1024*1024,'JSON exceeds16MiB');return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=10).strip()
def check_inputs(lock):
 need(lock['format']=='has_private_headless_transport_input_lock_1'and Path(lock['root']).resolve()==ROOT,'Input-lock scope');need(lock['qualified_full_revision']==QUALIFIED,'Obsolete c4d or undeclared full context');need(head()==lock['HEAD'],'HEAD changed; regenerate the CPU-only oracle/input lock before launch')
 for row in lock['files']:need(identity(Path(row['path']))==row,'Pinned source/runtime/private input changed: '+row['path'])
def gate(lock,lease):
 need(lease.get('format')=='has_root_headless_native_transport_lease_1'and lease.get('status')=='granted'and lease.get('headless_only')is True and lease.get('no_other_runtime_lease')is True,'Fresh explicit root headless lease required')
 need(lease.get('source_commit')==lock['HEAD']and lease.get('qualified_full_revision')==QUALIFIED,'Lease source context differs')
 full=Path(lock['qualified_full_run']).resolve(strict=True);need(full==ROOT/'output/windows-canonical-bone-binding-20261114T040946652'and Path(lease['canonical_run']).resolve()==full,'Wrong full run')
 state=load(full/'state.json');need(state.get('source_commit')==QUALIFIED and state.get('status')=='passed'and state.get('suite_exit')==0 and state.get('source_unchanged')is True,'Exact fresh f380 full must terminalPASS before any engine/parse launch')
 host_path=Path(lease['canonical_host_proof']).resolve(strict=True);no_links(host_path);host=load(host_path);need(host_path.is_relative_to(full),'Host proof escaped full run')
 need(host.get('format')=='has_canonical_authoritative_host_termination_1'and host.get('source_commit')==QUALIFIED and host.get('canonical_run')==full.name and host.get('coordinator_pid')==state['pid']and host.get('expected_creation_utc')==state['process_started'],'Exact full host identity required')
 need(all(host.get(k)is True for k in['coordinator_absent','python_absent','owned_runtime_command_matches_absent','no_process_killed'])and host.get('coordinator_matches')==[]and host.get('owned_runtime_matches')==[],'Full runtime lease has not closed')
 raw=full/'authoritative-host-terminal.json';need(identity(raw)['sha256']==host['raw_observation_sha256'],'Host raw proof changed');before=load(full/'source-before.json');after=load(full/'source-after.json');need(before==after and before['commit']==QUALIFIED,'Full source freeze differs')
 for row in lock['files']:
  p=Path(row['path'])
  if not p.is_relative_to(ROOT):continue
  n=p.relative_to(ROOT).as_posix()
  if n.split('/',1)[0]=='src'or n in['run.py','project.godot','main.tscn']:
   need(before['source_sha256'].get(n)==row['sha256'],'Probe app source differs from passed full')
 return {str(p):identity(p)for p in[full/'state.json',host_path,raw,full/'source-before.json',full/'source-after.json']}
def phase(args,folder,label,timeout):
 save(folder/(label+'-command.json'),args);started=time.monotonic();process=None;error=None;timed=False;terminated=False;killed=False;out=b'';err=b''
 try:
  process=subprocess.Popen(args,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt'else 0)
  try:out,err=process.communicate(timeout=timeout)
  except subprocess.TimeoutExpired as exc:
   timed=True;error={'type':type(exc).__name__,'detail':'Owned headless probe timeout'};process.terminate();terminated=True
   try:out,err=process.communicate(timeout=10)
   except subprocess.TimeoutExpired:process.kill();killed=True;out,err=process.communicate(timeout=10)
 except BaseException as exc:
  error={'type':type(exc).__name__,'detail':str(exc)}
  if process is not None:
   try:
    if process.poll()is None:process.terminate();terminated=True
    try:out,err=process.communicate(timeout=10)
    except subprocess.TimeoutExpired:process.kill();killed=True;out,err=process.communicate(timeout=10)
   except BaseException as closing:error['closure']={'type':type(closing).__name__,'detail':str(closing)}
 (folder/(label+'-stdout.log')).write_bytes(out);(folder/(label+'-stderr.log')).write_bytes(err);logpath=folder/(label+'-engine.log');engine=logpath.read_text(encoding='utf-8',errors='replace')if logpath.is_file()else'';texts=[out.decode('utf-8','replace'),err.decode('utf-8','replace'),engine];markers=[line for text in texts for line in text.splitlines()if any(k in line for k in BAD)];reaped=process is not None and process.poll()is not None;code=process.returncode if process else None
 proof={'phase':label,'exit':code,'retained_Popen_reaped':reaped,'timed_out':timed,'terminated_owned_child':terminated,'killed_owned_child':killed,'error':error,'error_markers':markers,'seconds':time.monotonic()-started,'passed':error is None and reaped and code==0 and not markers};save(folder/(label+'-process.json'),proof);return proof

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input-lock',type=Path,required=True);ap.add_argument('--root-lease',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--execute-headless-after-full',action='store_true',required=True);opt=ap.parse_args();need(os.name=='nt','Approved Windows headless runtime required')
 lock_path=opt.input_lock.resolve(strict=True);lease_path=opt.root_lease.resolve(strict=True);no_links(lock_path);no_links(lease_path);lock=load(lock_path);lease=load(lease_path);check_inputs(lock);need(Path(sys.executable).resolve()==Path(r'C:\Program Files\Python313\python.exe').resolve(),'Use approved Python313 -B');need(lease.get('input_lock_sha256')==identity(lock_path)['sha256'],'Root lease is not bound to this exact reviewed input lock');full_gate=gate(lock,lease)
 oracle=Path(lock['private_oracle']).resolve(strict=True);need(oracle.is_relative_to(CODE)and lock_path.parent==oracle.parent,'Private oracle/lock boundary');fixture=load(oracle);expected_configurations=len(fixture['cases']);expected_checks=8+expected_configurations*(69+69+49+2);need(fixture.get('format')=='has_private_native_transport_oracle_1'and fixture.get('expected_bindings')==69 and fixture.get('expected_rule_count')==49 and fixture.get('source_conversion_scale')==.01905 and expected_configurations==220,'Exact locked private oracle domain required')
 folder=opt.output.absolute();no_links(folder);need(folder.resolve().is_relative_to(CODE)and folder.resolve()!=CODE and not folder.exists(),'Fresh owned probe output required');folder.mkdir(exist_ok=False);before={str(p):identity(p)for p in[lock_path,lease_path]};save(folder/'locked-launch-context.json',{'HEAD':lock['HEAD'],'qualified_full_revision':QUALIFIED,'private_oracle_sha256':identity(oracle)['sha256'],'input_lock_sha256':identity(lock_path)['sha256'],'actual_root_uniform_scales':[1.,2.],'source_conversion_scale':.01905,'headless_only':True})
 phases=[];errors=[];result={};preserved=False
 try:
  # run.command itself performs only its approved Godot version query here,
  # after full-terminal and root-lease gates. It is never called by preparation.
  os.environ['HYBRID_GODOT']=str(Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe'))
  spec=importlib.util.spec_from_file_location('frozen_transport_run_command',ROOT/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
  script=(CODE/'headless_transport.gd').relative_to(ROOT).as_posix();target=folder/'result.json'
  for label,flags,timeout in[('parse',['--check-only'],30),('run',[],150)]:
   args=runner.command(script,headless=True,extra=['--audio-driver','Dummy',*flags,'--',str(oracle),str(target)]);args[args.index('--log-file')+1]=str(folder/(label+'-engine.log'));boundary=args.index('--');need('--headless'in args[:boundary]and args[args.index('--script')+1]==script and Path(args[0]).resolve()==Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe').resolve(),'Only exact approved headless script route admitted');proof=phase(args,folder,label,timeout);phases.append(proof)
   need(proof['passed'],'Headless '+label+' phase failed; preserve all outputs')
  result=load(target);need(result.get('format')=='has_actual_standard_model_transport_probe_1'and result.get('status')=='PASSED'and result.get('failures')==0 and result.get('configurations')==expected_configurations and result.get('checks')==expected_checks and result.get('authored_source_reset_preserved')is True,'Exact headless result/count/reset contract failed')
 except BaseException as exc:errors.append({'type':type(exc).__name__,'detail':str(exc)})
 finally:
  try:check_inputs(lock);need(before=={str(p):identity(p)for p in[lock_path,lease_path]},'Lock/lease changed');need(full_gate=={p:identity(Path(p))for p in full_gate},'Passed full-run gate changed');preserved=True
  except BaseException as exc:errors.append({'phase':'preservation','type':type(exc).__name__,'detail':str(exc)})
  report={'format':'has_owned_headless_native_transport_verification_1','HEAD':lock['HEAD'],'qualified_full_revision':QUALIFIED,'passed':not errors and len(phases)==2 and all(p['passed']for p in phases)and preserved,'headless_only':True,'phases':phases,'errors':errors,'result':result,'source_runtime_inputs_preserved':preserved,'private_oracle_not_published':True,'dynamics_added':False};save(folder/'verification.json',report)
 need(report['passed'],'Retain failed headless transport evidence: '+str(folder));print(json.dumps({'passed':True,'verification':str(folder/'verification.json'),'configurations':expected_configurations}))
if __name__=='__main__':main()
