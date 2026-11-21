"""Adopt exact scoped-qualified Import info sources; no Full/artist claim."""
from pathlib import Path
import argparse,hashlib,json,importlib.util,time,os,re,stat,uuid
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
ALLOWED={'src/pose_editor.gd','src/world_selection.gd','src/source_import.gd','src/import_capability_summary.gd','src/import_capability_editor.gd','tests/import_capability_summary_unit.gd','tests/import_capability_app_headless.gd','tests/import_capability_gui_smoke.gd','tests/verify_import_capability.py','tests/verify.py','experiments/reference_body_20261120/run_full.py','experiments/reference_body_20261120/test_receipt_provenance.py','tests/source_import_owner_unit.gd','tests/mmd_missing_texture_smoke.gd','tests/contact_transform_smoke.gd','tests/verify_contact_transform.py'}
NEW={'src/import_capability_summary.gd','src/import_capability_editor.gd','tests/import_capability_summary_unit.gd','tests/import_capability_app_headless.gd','tests/import_capability_gui_smoke.gd','tests/verify_import_capability.py'}
FLAGS=('all_admitted_sources_unchanged','all_runtime_sources_unchanged','parent_environment_preserved','all_private_jobs_and_desktops_closed','all_writer_trees_restored')

def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(value,message):
 if not value:raise RuntimeError(message)
def rel(value):
 need(type(value) is str and value and chr(92) not in value and ':' not in value,'Relative POSIX path required')
 p=Path(value);need(not p.is_absolute() and '..' not in p.parts and p.as_posix()==value,'Contained relative path required');return p
def safe(path,missing=False):
 path=Path(os.path.abspath(path))
 for part in reversed((path,*path.parents)):
  if missing and not os.path.lexists(part):continue
  s=part.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Alias refused')
 return path
def read(path,limit=4*1024*1024):
 path=safe(path);s=path.stat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit,'Bounded single-link file required')
 raw=path.read_bytes();t=path.stat();need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_nlink,t.st_mode),'Read drift');return raw
def durable(path,raw):
 safe(path,missing=True)
 with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def atomic(path,raw):
 tmp=path.with_name('.'+path.name+'.adoption-'+uuid.uuid4().hex);created=False
 safe(tmp,missing=True)
 try:
  with tmp.open('xb') as f:
   created=True;f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if created and tmp.exists():tmp.unlink()
def packet(folder,digest):
 raw=read(folder/'SOURCE_PINS.json');need(sha(raw)==digest,'Packet manifest changed');value=json.loads(raw);names=[]
 for row in value['files']:
  name=row['path'];rel(name);names.append(name);data=read(folder/name,8*1024*1024);need(len(data)==row['bytes'] and sha(data)==row['sha256'],'Packet bytes changed')
 need(len(names)==len(set(names))==len({n.casefold() for n in names}),'Packet duplicates')
 found=set()
 for here,dirs,files in os.walk(folder,followlinks=False):
  for name in dirs+files:safe(Path(here)/name)
  found.update((Path(here)/n).relative_to(folder).as_posix() for n in files)
 need(found=={'SOURCE_PINS.json'}|set(names),'Packet membership changed');return value

def qualification(key,value,packets):
 need(value.get('status')=='PASS','Qualification not PASS: '+key)
 if key=='component267':
  need(value.get('format')=='has_import_info_canonical267_root_v2_1' and type(value.get('component_checks')) is int and value['component_checks']==267 and value.get('case_count')==21 and value.get('pair_count')==8,'Component267 scope')
  need(value.get('exit')==0 and value.get('reaped') is True and value.get('Main_source_proposed_runtime_and_environment_preserved') is True and all(value.get('component_flags',{}).get(k) is True for k in FLAGS),'Component267 closure')
  need(value.get('baseline_revision')==REV and value.get('source_manifest_sha256')==packets['source-import-capability-canonical-c315-v2-prep-20261121'],'Component267 source')
 elif key=='contact129':
  need(value.get('format')=='has_contact_rotation_scoped_root_1' and type(value.get('checks')) is int and value['checks']==129 and value.get('native_contexts')==5,'Contact129 scope')
  need(all(value.get(k) is True for k in ('all_owned_launchers_reaped','all_private_jobs_closed_isolated','parent_environment_unchanged','main_source_and_head_unchanged','all_admitted_inputs_preserved')) and value.get('preservation_failure_count')==0,'Contact129 closure')
  need(value.get('baseline_revision')==REV and value.get('source_manifest_sha256')==packets['source-contact-rotation-gesture-v2-prep-20261121'],'Contact129 source')
 elif key=='map_info64':
  need(value.get('format')=='has_prepared_map_info64_root_1' and type(value.get('checks')) is int and value['checks']==64 and value.get('baseline_revision')==REV,'Map64 scope')
  need(all(value.get(k) is True for k in ('all_jobs_closed','source_and_environment_preserved','runtime_preserved')) and value.get('input_preservation_failures')==[],'Map64 closure')
  need(value.get('source_manifest_sha256')=='c7937e9febd4938425328144d986cbe47f3a9e71b0e23195d6d96f4c1d2e37a6' and all(value.get(k) is False for k in ('conversion_rerun','graphics_executed','Full_claimed','appearance_qualified','application_adopted')),'Map64 source/scope')
 elif key=='owner53':
  need(value.get('format') in ('has_import_info_legacy_v3_scopes_1','has_import_info_legacy_v4_scopes_1') and type(value.get('checks')) is int and value['checks']==53 and value.get('native_texture_wrapper_passed') is True,'Owner53 plus missing-texture scope')
  need(value.get('all_jobs_closed') is True and value.get('Main_runtime_inputs_environment_preserved') is True and all(value.get(k) is False for k in ('graphics_executed','Full_claimed','application_adopted')),'Owner53 closure')
  stage=Path(value['stage']);need(stage.is_relative_to(ROOT.parent) and stage!=ROOT,'Owned legacy stage')
  for name in ('source_import_owner_unit.gd','mmd_missing_texture_smoke.gd'):
   need(read(stage/'Studio/tests'/name)==PAYLOAD['tests/'+name],'Legacy qualified test version differs')
 elif key=='coordinator_policy':
  need(value.get('format')=='has_import_info_coordinator_policy47_1' and type(value.get('checks')) is int and value['checks']==47 and value.get('exit')==0 and value.get('new_negative_controls')==30 and value.get('prior_provenance_controls')==17 and value.get('Full_claimed') is False,'Policy47 scope/exit')
  need(value.get('source_manifest_sha256')==packets['source-import-info-full-receipts-prep-20261121'],'Policy47 source')
 elif key=='coordinator_cpu163':
  need(value.get('format')=='has_import_info_metadata163_root_v3_1' and type(value.get('component_checks')) is int and value['component_checks']==163 and value.get('case_count')==5 and value.get('pair_count')==0,'Metadata163 scope')
  need(value.get('exit')==0 and value.get('reaped') is True and value.get('Main_source_proposed_runtime_and_environment_preserved') is True and all(value.get('component_flags',{}).get(k) is True for k in FLAGS),'Metadata163 closure')
  need(value.get('baseline_revision')==REV and value.get('source_manifest_sha256')==packets['source-import-capability-canonical-c315-v2-prep-20261121'] and value.get('metadata_manifest_sha256')==packets['source-import-info-full-receipts-prep-20261121'] and value.get('policy47_passed') is True and value.get('actual_headless_receipts_independently_admitted')==5,'Metadata163 source/physical receipt audit')
 else:raise RuntimeError('Unknown qualification')

p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True);a=p.parse_args()
plan_raw=read(a.plan);need(re.fullmatch('[0-9a-f]{64}',a.plan_sha256) and sha(plan_raw)==a.plan_sha256,'Exact external plan pin required')
plan=json.loads(plan_raw);need(plan.get('format')=='has_import_info_adoption_plan_1' and plan.get('status')=='READY_FOR_ROOT_ADOPTION' and plan.get('ready_for_execution') is True and plan.get('revision')==REV,'Draft/unapproved plan refused')
need(plan.get('functional_sources_before')==1103 and plan.get('functional_sources_after')==1109,'Exact functional source counts')
spec=importlib.util.spec_from_file_location('_adoption_snapshot',ROOT/'experiments/reference_body_20261120/run_full.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
need(F.git('rev-parse','HEAD')==REV,'Revision changed');before=F.snapshot();need(len(before)==1103 and {n:r['git_sha1'] for n,r in before.items()}==F.committed_sources(REV),'Exact c315 committed source domain/bytes required')
for source_name in before:
 s=safe(ROOT/source_name).stat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'Source alias or hardlink refused')
packets={}
for row in plan['packets']:
 name=row['folder'];rel(name);need(len(Path(name).parts)==1 and name not in packets,'Unique owned packet required');packet(OUT/name,row['sha256']);packets[name]=row['sha256']
PAYLOAD={};BACKUPS={}
for row in plan['targets']:
 name=row['path'];rel(name);need(name in ALLOWED and name not in PAYLOAD,'Unreviewed/duplicate target');destination=safe(ROOT/name,missing=True);need(destination.is_relative_to(ROOT),'Target outside Root')
 rel(row['payload']);need(row['packet'] in packets and row['payload']=='payload/'+name,'Exact admitted payload path')
 data=read(OUT/row['packet']/row['payload']);need(len(data)==row['bytes'] and sha(data)==row['sha256'],'Payload changed');PAYLOAD[name]=data
 if name in NEW:need(row['operation']=='new' and row.get('base_absent') is True and not os.path.lexists(destination),'New target must remain absent')
 else:
  need(row['operation']=='replace','Existing target must replace');raw=read(destination);need(len(raw)==row['base_bytes'] and sha(raw)==row['base_sha256'],'Base changed');BACKUPS[name]=raw
need(set(PAYLOAD)==ALLOWED and len(PAYLOAD)==len({n.casefold() for n in PAYLOAD})==16,'Exact16 target membership required')
need(set(plan['required_qualification'])=={'component267','contact129','owner53','map_info64','coordinator_policy','coordinator_cpu163'},'Exact six qualification gates')
for key,row in plan['required_qualification'].items():
 need(row.get('status')=='PINNED_PASS' and type(row.get('path')) is str,'Pending qualification refused');raw=read(row['path']);need(sha(raw)==row['sha256'],'Qualification bytes changed');qualification(key,json.loads(raw),packets)
need(F.snapshot()==before and F.git('rev-parse','HEAD')==REV,'Concurrent source changed before backup')
backup=OUT/('import-info-adoption-backup-'+str(time.time_ns())+'-'+uuid.uuid4().hex);safe(backup,missing=True);need(backup.is_relative_to(OUT) and backup!=OUT,'Owned backup required');backup.mkdir()
for name,raw in BACKUPS.items():
 path=backup/name;path.parent.mkdir(parents=True,exist_ok=True);durable(path,raw)
durable(backup/'PLAN.json',plan_raw);durable(backup/'BEFORE.json',(json.dumps(before,indent=2)+'\n').encode())
written=[]
try:
 for name,data in PAYLOAD.items():
  path=ROOT/name
  if name in NEW:need(not os.path.lexists(path),'Concurrent new target created')
  else:need(read(path)==BACKUPS[name],'Concurrent target changed')
  path.parent.mkdir(parents=True,exist_ok=True);atomic(path,data);written.append(name)
 after=F.snapshot();added=set(after)-set(before);changed={n for n in before if before[n]!=after[n]}
 need(not set(before)-set(after) and changed|added==ALLOWED and len(after)==1109 and added==NEW,'Adoption domain mismatch')
 need(all(before[n]==after[n] for n in set(before)-ALLOWED) and all(read(ROOT/n)==data for n,data in PAYLOAD.items()),'Final bytes/unrelated source changed')
except BaseException as error:
 rollback_errors=[]
 for name in reversed(written):
  path=ROOT/name
  try:
   need(read(path)==PAYLOAD[name],'Concurrent target edit; refuse rollback overwrite')
   if name in NEW:path.unlink()
   else:
    atomic(path,BACKUPS[name]);os.utime(path,ns=(path.stat().st_atime_ns,before[name]['mtime_ns']))
  except BaseException as rollback_error:rollback_errors.append({'path':name,'error':str(rollback_error)})
 durable(backup/'ROLLBACK.json',(json.dumps({'status':'ROLLED_BACK' if not rollback_errors else 'ROLLBACK_REQUIRES_REVIEW','error':str(error),'rollback_errors':rollback_errors},indent=2)+'\n').encode());raise
record={'format':'has_import_info_scoped_adoption_1','status':'PASS','base_revision':REV,'functional_sources_before':1103,'functional_sources_after':1109,'modified':sorted(changed),'added':sorted(added),'all_unrelated_functional_files_preserved':True,'ordinary_component267_pass':True,'final_metadata_version267_pass_claimed':False,'whole_Full_pass_claimed':False,'source_plan_sha256':sha(plan_raw),'durable_backup':str(backup),'recorded_ns':time.time_ns()}
atomic(OUT/'IMPORT_INFO_ADOPTION_20261121.json',(json.dumps(record,indent=2)+'\n').encode());atomic(OUT/'IMPORT_INFO_FINAL_FUNCTIONAL_CATALOGUE_20261121.json',(json.dumps(after,indent=2)+'\n').encode());print(json.dumps(record))
