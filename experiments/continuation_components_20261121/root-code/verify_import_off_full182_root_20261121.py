"""Independent postflight; run only after retained Root exec1322 has completed."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,stat,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--root-exec-reaped-confirmed',action='store_true',required=True);args=p.parse_args()
CONTROL=Path(__file__).resolve().parent;MAIN=CONTROL.parent
ROOT=MAIN.parent/'has-import-off-full-20261121-c31576d'
RUN=ROOT/'output/windows-reference-body-1795260488673286600'
OUTER=ROOT/'output/root-full-launch-1795260488526602700'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def raw(path):
 for part in (path,*path.parents):
  s=part.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Alias evidence path')
 a=path.lstat();need(stat.S_ISREG(a.st_mode) and a.st_nlink==1,'Evidence must be single-link regular')
 data=path.read_bytes();b=path.lstat()
 need((a.st_dev,a.st_ino,a.st_mode,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_mode,b.st_size,b.st_mtime_ns),'Changing evidence')
 return data
def read(path):
 data=raw(path);return json.loads(data),{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def git(*v):return subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.longpaths=true',*v],cwd=ROOT).decode().strip()
S_PATH=CONTROL/'source-miku-contact-c315-1103-successor-prep-20261121/source1103.py'
need(hashlib.sha256(raw(S_PATH)).hexdigest()=='e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3','Reviewed source-admission module changed')
spec=importlib.util.spec_from_file_location('_root_full_contracts',S_PATH);S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
audit,apin=read(CONTROL/'FULL182_REGISTRATION_AUDIT_20261121.json')
completion,cpin=read(RUN/'completion.json');report,rpin=read(ROOT/'output/verification.json')
before,bpin=read(RUN/'source-before.json');after,afterpin=read(RUN/'source-after.json')
launch,lpin=read(RUN/'launch.json');outer,opin=read(OUTER/'launch.json');outer_done,odpin=read(OUTER/'completion.json')
expected,epin=read(CONTROL/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json')
remote,remotepin=read(CONTROL/'IMPORT_OFF_REMOTE_VERIFIED_20261121.json')
classification,ppin=read(RUN/'receipt-provenance.json')
need(completion['revision']==launch['revision']==outer['revision']==git('rev-parse','HEAD')==REV,'Revision mismatch')
need(remote['status']=='PASS' and remote['revision']==REV and remote['functional_source_count']==1103,'Fresh remote source verification missing')
S.completion_contract(completion);S.report_contract(report);S.source_contract(expected,before)
need(before==after and bpin==afterpin and len(before)==1103,'Source snapshots changed')
need(set(report)==set(audit['expected_group_keys']) and len(report)==182,'Exact182 group keys differ')
need(sum(r['checks'] for name,r in report.items() if name in S.NEW_GROUPS)==626,'New UI/camera count differs')
groups,gpin=read(S_PATH.parent/'FULL182_GROUP_CONTRACT.json')
need((gpin['bytes'],gpin['sha256'])==S.GROUP_PIN,'Reviewed group contract changed')
S.exact_group_contract(completion,report,groups)
need(outer['started_ns']<=launch['started_ns']<=(ROOT/'output/verification.json').stat().st_mtime_ns
     <=(RUN/'completion.json').stat().st_mtime_ns<=(OUTER/'completion.json').stat().st_mtime_ns,'Full report outside exact nested completion window')
coordinator_sha=hashlib.sha256(raw(ROOT/'experiments/reference_body_20261120/run_full.py')).hexdigest()
S.outer_contract(outer,outer_done,ROOT,OUTER,coordinator_sha)
need(outer_done['pid']==outer['pid']==launch['coordinator_pid']==22996 and launch['pid']==23816,'Retained process identities differ')
need(outer_done['parent_environment_unchanged'] is True and outer_done['child_reaped'] is True,'Outer process/environment proof failed')
S.receipt_contract(completion,classification)
for row in classification['current']:
 path=ROOT/row['path'];need(path.resolve(strict=True).is_relative_to(ROOT),'Receipt escaped clone')
 data=raw(path);need(hashlib.sha256(data).hexdigest()==row['sha256'] and json.loads(data)==row['value'],'Persisted current receipt differs')
S.physical_receipt_contract(completion['nonzero_private_jobs'][0]['value'])
tree={}
for row in subprocess.check_output(['git','ls-tree','-r','-z',REV],cwd=ROOT).split(b'\0'):
 if not row:continue
 meta,name=row.split(b'\t',1);mode,kind,oid=meta.decode().split();tree[name.decode()]=(kind,oid)
actual_domain=set(S.ROOT_FILES)|set(S.EXPERIMENTS)
for prefix in ('src','tests','tools','examples','data'):
 for path in (ROOT/prefix).rglob('*'):
  info=path.lstat()
  need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'Alias in current functional tree')
  if stat.S_ISDIR(info.st_mode):continue
  need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'Special current functional path')
  if path.suffix=='.pyc' or '__pycache__' in path.parts:continue
  actual_domain.add(path.relative_to(ROOT).as_posix())
need(actual_domain==set(before) and len({name.casefold() for name in actual_domain})==1103,'Current functional membership differs from completed Full')
for name,row in before.items():
 data=raw(ROOT/name);need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'Source no longer matches Full')
 need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1']==tree[name][1] and tree[name][0]=='blob','Source commit blob differs')
need(git('rev-parse','HEAD')==REV,'Revision changed during postflight')
result={'format':'has_import_off_full182_root_postflight_1','status':'PASS','revision':REV,'functional_sources':1103,
 'exact_group_count':182,'new_editor_camera_checks':626,'movie_groups':completion['movie_groups'],
 'current_private_jobs':completion['unique_current_private_jobs'],'all_private_jobs_isolated_closed':True,
 'source_raw_before_after_identical':True,'source_exact_published_commit':True,'outer_process_reaped_and_environment_preserved':True,
 'persisted_current_receipts_verified':True,'only_nonzero_job_expected_converter_cancellation':True,
 'seconds':completion['seconds'],'root_exec_session':1322,'root_exec_reaped_confirmed':True,
 'scenario_d_scope':'Separate qualified28wire+30writer+4cold/49frames; not an additional Full182 group.',
 'human_device_acceptance_claimed':False,'formal_acceptance_score':'55/62','timestamp_ns':time.time_ns(),
 'pins':{'completion':cpin,'report':rpin,'source_before':bpin,'source_after':afterpin,'launch':lpin,'outer_launch':opin,
         'outer_completion':odpin,'registration_audit':apin,'group_contract':gpin,'expected_source':epin,'remote':remotepin,'provenance':ppin}}
target=CONTROL/'IMPORT_OFF_FULL182_ROOT_POSTFLIGHT_20261121.json';need(not target.exists(),'Do not overwrite prior postflight')
target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
