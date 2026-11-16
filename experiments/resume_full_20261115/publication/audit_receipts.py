from pathlib import Path
import json,hashlib,re,datetime,collections,shutil,sys,argparse
import publication_gates as Gates
sys.stdout.reconfigure(encoding='utf-8')
TASK=Path(__file__).resolve().parent; ROOT=TASK.parents[1]
CONTEXT=json.loads((TASK/'RUN_EXPECTATIONS.json').read_bytes())
ROOT=Path(CONTEXT['workspace_root'])
REGISTRY=Gates.registry(TASK,CONTEXT)
parser=argparse.ArgumentParser(description='Terminal-only immutable canonical receipt audit; no process/runtime actions')
parser.add_argument('--terminal-permission',action='store_true',required=True)
parser.add_argument('--host-proof-sha256',required=True)
parser.add_argument('--host-raw-sha256',required=True)
parser.add_argument('--output',type=Path,default=TASK/'receipt-audit')
OPTIONS=parser.parse_args()
assert all(re.fullmatch(r'[0-9a-f]{64}',value) for value in [OPTIONS.host_proof_sha256,OPTIONS.host_raw_sha256])
RUN=ROOT/'output'/CONTEXT['run_name']; EXPECT=CONTEXT['source_commit']; OUT=OPTIONS.output.resolve()
assert OUT.parent==TASK and not OUT.exists()

def load(p): return Gates.load(Path(p))
def sha(p): return hashlib.sha256(Gates.read(Path(p))).hexdigest()
def meta(p):
 p=Path(p).absolute();raw=Gates.read(p);s=p.stat();return {'path':str(p),'bytes':len(raw),'mtime_ns':s.st_mtime_ns,'sha256':hashlib.sha256(raw).hexdigest()}
def utc_ns(s):
 m=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)',s)
 if not m: raise ValueError(s)
 d=datetime.datetime.fromisoformat(m[1]+('+00:00' if m[3]=='Z' else m[3]))
 return int(d.timestamp())*10**9+int((m[2]or'').ljust(9,'0')[:9])
def write(name,x): (OUT/name).write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def absolute(s):
 return isinstance(s,str) and re.match(r'^[A-Za-z]:[\\/]',s) is not None
state=load(RUN/'state.json')
if state.get('status')!='passed' or state.get('suite_exit')!=0 or state.get('source_unchanged') is not True or not state.get('finished_utc'):
 raise RuntimeError('Root-confirmed terminal PASS required before any audit output or final report read')
assert state['source_commit']==EXPECT and state['pid']==CONTEXT['coordinator_pid'] and state['process_started']==CONTEXT['coordinator_creation_utc']
assert sha(RUN/'source-before.json')==CONTEXT['source_before_sha256'] and sha(RUN/'launch.json')==CONTEXT['launch_sha256'] and sha(RUN/'coordinator-children-observed.json')==CONTEXT['children_observation_sha256']
a=utc_ns(state['started_utc']);b=utc_ns(state['finished_utc'])
host=load(RUN/'authoritative-host-termination.json')
host_raw=RUN/'authoritative-host-terminal.json'
host_bound=(sha(RUN/'authoritative-host-termination.json')==OPTIONS.host_proof_sha256 and sha(host_raw)==OPTIONS.host_raw_sha256 and host['raw_observation_sha256']==sha(host_raw) and host['source_commit']==EXPECT and host['coordinator_pid']==CONTEXT['coordinator_pid'] and host['python_pid']==CONTEXT['python_pid'] and host['expected_creation_utc']==CONTEXT['coordinator_creation_utc'] and host['expected_python_creation_utc']==CONTEXT['python_creation_utc'] and host['coordinator_absent'] is True and host['python_absent'] is True and host['owned_runtime_command_matches_absent'] is True and host['no_process_killed'] is True and not host['coordinator_matches'] and not host['owned_runtime_matches'])
before=load(RUN/'source-before.json'); after=load(RUN/'source-after.json')
source_equal=len(before['source_sha256'])==CONTEXT['functional_source_entries'] and before==after and before['commit']==EXPECT and state['source_commit']==EXPECT and state['pid']==CONTEXT['coordinator_pid'] and state['process_started']==CONTEXT['coordinator_creation_utc']
assert source_equal and host_bound, 'Exact terminal/source/host proof required before final report read or audit output'
Gates.validate_raw_host(RUN,CONTEXT,state,host)
assert before['source_sha256'][REGISTRY['verifier_relative_path']]==REGISTRY['verifier_sha256']
resultpath=ROOT/'output/verification.json'
assert a<=resultpath.stat().st_mtime_ns<=b, 'Final canonical verification is stale/outside this run'
result=load(resultpath);Gates.validate_result(result,CONTEXT,REGISTRY)
OUT.mkdir(exist_ok=False)
failures=[]
if not(source_equal and host_bound and a<=resultpath.stat().st_mtime_ns<=b and state['status']=='passed' and state['suite_exit']==0 and state['source_unchanged']): failures.append({'kind':'canonical_state_or_source'})
refs=collections.defaultdict(set); inline=[]; docs={}; queue=[(resultpath,'full_result')]; seen=set(); missing=[]; ignored_named=[]
def add_ref(p,ref):
 p=Path(p).absolute()
 assert '..' not in p.parts and p.is_relative_to(ROOT/'output'), 'Receipt reference escaped owned output metadata'
 if p.is_file(): refs[p].add(ref)
 else: missing.append({'path':str(p),'reference':ref})
def walk(v,loc,origin):
 if isinstance(v,dict):
  if v.get('format')=='studio_private_desktop_1': inline.append({'origin':str(origin),'location':loc,'receipt':v})
  if v.get('format')=='has_helper_preview_main_verification_1' and v.get('mode')=='graphical':
   for row in v.get('results',[]):
    if 'private_receipt' in row:
     add_ref(Path(v['actual_res_root'])/'output/helper-preview-qa'/row['label']/'private-receipt.json',str(origin)+loc+'.derived_helper_'+row['label'])
  for k,x in v.items():
   where=loc+'.'+k
   if isinstance(x,str) and absolute(x):
    p=Path(x)
    if p.suffix.lower()=='.json' and ('receipt' in k.lower() or 'private-desktop' in x.lower() or 'private-receipt' in x.lower()): add_ref(p,str(origin)+where)
    if k=='folder' and p.is_dir():
     q=p/'verification.json'
     if q.is_file() and q.absolute().is_relative_to(ROOT/'output'): queue.append((q,str(origin)+where))
   walk(x,where,origin)
 elif isinstance(v,list):
  for i,x in enumerate(v):
   if absolute(x) and Path(x).suffix.lower()=='.json' and ('receipt' in loc.lower() or 'private-desktop' in x.lower() or 'private-receipt' in x.lower()): add_ref(x,str(origin)+loc+'['+str(i)+']')
   walk(x,loc+'['+str(i)+']',origin)
while queue:
 assert len(seen)<1024 and len(refs)<4096 and len(inline)<10000, 'Receipt metadata catalogue exceeds bound'
 p,ref=queue.pop(0);p=p.absolute()
 if p in seen: continue
 seen.add(p);v=load(p);docs[p]={'file':meta(p),'reference':ref};walk(v,'$',p)
rootdir=ROOT/'output/private-desktop'; fresh=[]
for p in rootdir.glob('*.json'):
 if a<=p.stat().st_mtime_ns<=b:
  fresh.append(p.resolve());refs[p.resolve()].add('fresh_root_exact_aware_UTC_interval')
expected_cancel=Path(result['krita_import']['cancelled_receipt']).absolute()
assertion=ROOT/'tests/verify_krita_import.py'; text=assertion.read_text(encoding='utf-8')
assertion_support="assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']" in text and sha(assertion)==before["source_sha256"]["tests/verify_krita_import.py"]
rows=[]; bydesktop=collections.defaultdict(list)
for p in sorted(refs,key=lambda x:str(x).lower()):
 r=load(p)
 if not isinstance(r,dict) or r.get('format')!='studio_private_desktop_1':
  ignored_named.append({'file':meta(p),'references':sorted(refs[p]),'actual_format':r.get('format') if isinstance(r,dict) else type(r).__name__});continue
 iso=all(r.get(k) is True for k in ['private_window_seen','child_desktop_confirmed','job_closed','desktop_closed']) and all(r.get(k) is False for k in ['desktop_switch_requested','foreground_child_observed'])
 expected=p==expected_cancel and r.get('exit')==2 and r.get('cancelled') is True and r.get('error')=='Owned converter cancelled' and assertion_support
 classification='success_exit_0' if r.get('exit')==0 else 'expected_krita_cancel_exit_2' if expected else 'unexpected_exit'
 within=a<=p.stat().st_mtime_ns<=b
 row={'file':meta(p),'references':sorted(refs[p]),'fresh_root':p in fresh,'within_run_interval':within,'classification':classification,'isolation_and_closure_passed':iso,'receipt':r}
 rows.append(row);bydesktop[r.get('desktop')].append(row)
 if not iso or classification=='unexpected_exit' or not within or r.get('monitor_error') or (r.get('error') and not expected): failures.append({'kind':'receipt','path':str(p),'isolation_ok':iso,'classification':classification,'within_run_interval':within})
 if p in fresh and r.get('exit')!=0: failures.append({'kind':'fresh_root_exit','path':str(p)})
if not fresh: failures.append({'kind':'no_fresh_root_receipts'})
for row in rows:
 p=Path(row['file']['path']); bucket='root' if row['fresh_root'] else 'nested'
 target=OUT/'physical-receipts'/bucket/(hashlib.sha256(str(p).encode()).hexdigest()[:12]+'-'+p.name)
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 if sha(target)!=row['file']['sha256']: failures.append({'kind':'raw_copy_mismatch','path':str(p)})
 row['preserved_raw_copy']=meta(target)
inline_unique={}
for x in inline:
 r=x['receipt'];candidates=bydesktop.get(r.get('desktop'),[]);exact=[row for row in candidates if row['receipt']==r]
 x['physical_exact_matches']=[row['file']['path'] for row in exact];x['strict_identity_closure_match']=bool(exact)
 inline_unique.setdefault(r.get('desktop'),[]).append(x)
 if not exact: failures.append({'kind':'unmatched_inline','desktop':r.get('desktop'),'location':x['location'],'origin':x['origin']})
for desktop,items in bydesktop.items():
 if len({json.dumps(x['receipt'],sort_keys=True) for x in items})!=1: failures.append({'kind':'conflicting_duplicate_desktop','desktop':desktop})
if len(bydesktop)!=len(rows): failures.append({'kind':'duplicate_physical_desktop_receipt'})
if sum(row['classification']=='expected_krita_cancel_exit_2' for row in rows)!=1: failures.append({'kind':'registered_Krita_cancel_count_not_one'})
for x in missing: failures.append({'kind':'missing_referenced_receipt',**x})
root_rows=[r for r in rows if r['fresh_root']]; nested=[r for r in rows if not Path(r['file']['path']).parent==rootdir]
summary={'format':'has_canonical_metadata_receipt_audit_1','source_commit':EXPECT,'run_directory':str(RUN),'state':state,'interval_start_ns':a,'interval_end_ns':b,'elapsed_seconds':(b-a)/10**9,'source_before_after_equal':source_equal,'functional_source_entries':len(before['source_sha256']),'full_result_top_level_entries':len(result),'fresh_root_receipt_files':len(root_rows),'fresh_root_all_exit_0':all(r['receipt']['exit']==0 for r in root_rows),'fresh_root_all_private_closed':all(r['isolation_and_closure_passed'] for r in root_rows),'unique_receipt_files':len(rows),'unique_desktops':len(bydesktop),'nested_receipt_files_outside_root':len(nested),'success_exit_0_files':sum(r['classification']=='success_exit_0' for r in rows),'expected_krita_cancel_exit_2_files':sum(r['classification']=='expected_krita_cancel_exit_2' for r in rows),'all_receipts_private_closed':all(r['isolation_and_closure_passed'] for r in rows),'all_receipts_fresh_for_run':all(r['within_run_interval'] for r in rows),'inline_occurrences':len(inline),'inline_unique_desktops':len(inline_unique),'all_inline_exact_physical_matches':all(x['strict_identity_closure_match'] for x in inline),'actual_report_documents_read':len(docs),'non_receipt_filename_matches':len(ignored_named),'missing_referenced_receipts':len(missing),'unexpected_failures':failures,'passed':not failures,'release_file_created':False,'authoritative_host_context_bound':host_bound,'coordinator_pid':CONTEXT['coordinator_pid'],'suite_python_pid':CONTEXT['python_pid']}
write('receipt-inventory.json',{'summary':summary,'receipts':rows,'inline_receipts':inline,'non_receipt_filename_matches':ignored_named,'missing_references':missing,'report_documents':list(docs.values()),'expected_cancellation_support':{'file':meta(assertion),'explicit_exit2_assertion_found':assertion_support,'source_line':next(i for i,line in enumerate(text.splitlines(),1) if "assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']" in line),'full_result_binding':'$.krita_import.cancelled_receipt','receipt_path':str(expected_cancel)}})
write('receipt-ready-final.json',summary)
for p in [resultpath,RUN/'state.json',RUN/'source-before.json',RUN/'source-after.json',RUN/'authoritative-host-termination.json',RUN/'authoritative-host-terminal.json',RUN/'coordinator-children-observed.json',RUN/'desktop-enumeration.json']:
 if p.is_file():shutil.copyfile(p,OUT/('full-verification.json' if p==resultpath else p.name))
write('input-hashes.json',[meta(p) for p in [resultpath,RUN/'state.json',RUN/'source-before.json',RUN/'source-after.json',RUN/'authoritative-host-termination.json',RUN/'authoritative-host-terminal.json',RUN/'coordinator-children-observed.json',RUN/'desktop-enumeration.json',assertion] if p.is_file()])
shutil.copy2(Path(__file__),OUT/'audit_receipts.py')
shutil.copy2(TASK/'RUN_EXPECTATIONS.json',OUT/'RUN_EXPECTATIONS.json')
shutil.copy2(TASK/'RESULT_REGISTRY.json',OUT/'RESULT_REGISTRY.json')
shutil.copy2(TASK/'publication_gates.py',OUT/'publication_gates.py')
(OUT/'README.md').write_text('Terminal-only metadata audit. Receipt counts are observed for this exact run; no prior-run totals are reused. Raw receipts and report/source/host contexts are retained without native/media/runtime payloads. Release is supplied separately by root.\n',encoding='utf-8')
assert not failures, 'Receipt audit failed; retained incomplete evidence for review'
print(json.dumps(summary,ensure_ascii=True))
