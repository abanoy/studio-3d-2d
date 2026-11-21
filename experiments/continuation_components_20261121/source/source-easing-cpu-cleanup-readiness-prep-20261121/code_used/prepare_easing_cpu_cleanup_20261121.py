"""Read-only seven-stage survey and source/text evidence collector. Never deletes,
moves, inspects processes, imports candidates or runs native/graphical tools.
"""
from pathlib import Path
import ast,hashlib,json,os,re,stat
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';PARENT=ROOT.parent
DEST=OUT/'source-easing-cpu-cleanup-readiness-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
NAMES=('has-easing-headless-1795254145851799500','has-easing435-app-cpu-1795254384845561100',
 'has-easing435-app-cpu-1795254695259497400','has-easing435-app-cpu-1795254761995523000',
 'has-easing-headless-1795254831934151300','has-easing435-graphics-parse-1795258322734840400',
 'has-easing-c315-graphics-parse-1795260866931895900')
ARCHIVES=('source_additions_preparation_20261121','source_post_e087_evidence_20261121',
 'editor_camera_iteration_20261121','continuation_sources_20261121')
SOURCE_EXT={'.gd','.py','.gdshader','.godot','.tscn','.cfg','.md','.json','.ps1','.mjs','.uid'}
PRIVATE_KEYS={'raw_bones','raw_skin','raw_source_weights','normalized_source_weights','imported_weights',
 'inverse_bind_matrices','vertex_positions','skin_vertices','bone_matrices','joint_indices','raw_samples',
 'calibration_failure','influence_failure'}
def need(ok,why):
 if not ok:raise RuntimeError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def identity(s):return tuple(str(v) for v in (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0)))
def safe(p):
 p=Path(os.path.abspath(p))
 for x in reversed((p,*p.parents)):
  s=x.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'PATH_ALIAS '+str(x))
 return p
def raw(p,limit=8*1024*1024):
 p=safe(p);before=p.lstat();need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'PLAIN_BOUNDED_FILE '+str(p))
 b=p.read_bytes();need(len(b)==before.st_size and identity(before)==identity(p.lstat()),'READ_CHANGED '+str(p));return b
def pin(p):
 p=safe(p);s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'REGULAR_SINGLE_LINK '+str(p))
 h=hashlib.sha256()
 with p.open('rb') as f:
  need(identity(os.fstat(f.fileno()))==identity(s),'OPEN_CHANGED')
  while True:
   b=f.read(1024*1024)
   if not b:break
   h.update(b)
  need(identity(os.fstat(f.fileno()))==identity(s),'HASH_CHANGED')
 need(identity(p.lstat())==identity(s),'PATH_CHANGED')
 return {'bytes':s.st_size,'sha256':h.hexdigest(),'identity_native64_rawmode':identity(s)}
def walk(base):
 base=safe(base);rows=[];dirs=[];seen=set();issues=[]
 def error(e):raise e
 for folder,children,names in os.walk(base,followlinks=False,onerror=error):
  folder=Path(folder);s=folder.lstat();dirs.append({'path':folder.relative_to(base).as_posix(),'identity':identity(s)})
  for n in children+names:
   p=folder/n;relative=p.relative_to(base).as_posix();s=p.lstat();k=relative.casefold()
   need(k not in seen,'CASE_ALIAS '+str(p));seen.add(k)
   if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:
    issues.append({'path':relative,'kind':'reparse_or_link'});continue
   need(n==n.rstrip(' .') and ':' not in n,'WINDOWS_PATH_ALIAS '+str(p))
   if n in names:
    need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'SPECIAL_OR_HARDLINK '+str(p))
    row={'path':relative,**pin(p)};rows.append(row)
  children[:]=[n for n in children if not (folder/n).is_symlink() and not getattr((folder/n).lstat(),'st_file_attributes',0)&0x400]
 return {'files':rows,'directories':dirs,'aliases':issues}
def privacy(b):
 text=b.decode('utf-8-sig');need('\0' not in text,'NUL_BINARY')
 need(not re.search(r'data:[^\s\"\']{0,90};base64,[A-Za-z0-9+/=]{256,}',text),'EMBEDDED_BINARY')
 return text
def privacy_json(b):
 def pairs(rows):
  value={}
  for k,v in rows:need(k not in value,'DUPLICATE_JSON_KEY');value[k]=v
  return value
 v=json.loads(privacy(b),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(RuntimeError('NONFINITE_JSON')))
 def check(x):
  if type(x) is dict:
   for k,y in x.items():
    need(not(k in PRIVATE_KEYS and type(y) in (dict,list) and y),'PRIVATE_NATIVE_ARRAY '+k);check(y)
  elif type(x) is list:
   need(not(len(x)>512 and all(type(y) in (int,float) for y in x)),'LARGE_NUMERIC_ARRAY')
   for y in x:check(y)
 check(v);return v
def put(name,b):
 p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():need(raw(p,32*1024*1024)==b,'EXISTING_PREP_DIFFERS '+name)
 else:
  with p.open('xb') as f:need(f.write(b)==len(b),'SHORT_COPY')
 need(raw(p,32*1024*1024)==b,'COPY_READBACK')
def js(name,v):put(name,(json.dumps(v,indent=2)+'\n').encode())
need(not (DEST/'SOURCE_PINS.json').exists(),'FROZEN_PACKET')
remote=json.loads(raw(OUT/'IMPORT_OFF_REMOTE_VERIFIED_20261121.json'))
need(remote.get('status')=='PASS' and remote.get('revision')==REV,'PRIOR_REMOTE_CHECKPOINT_PIN')
catalogue=json.loads(raw(OUT/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json'));need(len(catalogue)==1103,'SOURCE1103')
recovery={};reference_sources=[]
for name,row in catalogue.items():
 p=ROOT/name;current=pin(p);need(current['bytes']==row['bytes'] and current['sha256']==row['sha256'],'CURRENT_SOURCE_DRIFT '+name)
 recovery.setdefault((row['bytes'],row['sha256']),{'kind':'c315_functional_git_blob','revision':REV,'path':name,'git_sha1':row['git_sha1']})
for name in ARCHIVES:
 base=ROOT/'experiments'/name;need(base.is_dir() and not (base/'BUILDING.json').exists(),'PRIOR_ARCHIVE_NOT_FINAL')
 count=0;total=0
 for row in walk(base)['files']:
  recovery.setdefault((row['bytes'],row['sha256']),{'kind':'prior_published_source_archive_file','path':(base/row['path']).relative_to(ROOT).as_posix()})
  count+=1;total+=row['bytes']
 reference_sources.append({'path':base.relative_to(ROOT).as_posix(),'files_hashed':count,'logical_bytes':total})
js('PRIOR_RECOVERY_INDEX_SCOPE.json',{'revision':REV,'remote_verification':remote,'reference_archives':reference_sources,
 'functional_source_rows':len(catalogue),'unique_bytes_hash_pairs':len(recovery),'read_only_hash_inventory':True,
 'not_a_new_remote_verification':True})
stages=[];copied=[];deferred=[];runtime_sources=[];reports=[]
for name in NAMES:
 base=safe(PARENT/name);need(base.parent==PARENT and base.name==name and base.resolve()==base,'EXACT_OWNED_BOUNDARY')
 tree=walk(base);need(not tree['aliases'],'ALIAS_STAGE_RETAIN_REQUIRED')
 counts={};copy_count=0;copy_bytes=0;matched=0;unknown_binary=[]
 for row in tree['files']:
  relative=row['path'];p=base/relative;suffix=p.suffix.lower();counts[suffix or '<none>']=counts.get(suffix or '<none>',0)+1
  ref=recovery.get((row['bytes'],row['sha256']))
  if ref:row['prior_recovery']=ref;matched+=1
  is_log=suffix=='.log' or p.name.lower() in ('stdout.txt','stderr.txt','stdout','stderr')
  in_cache=any(part in ('User','UserData','.godot','__pycache__') for part in Path(relative).parts)
  text_candidate=is_log or (suffix in SOURCE_EXT and not in_cache)
  # Already-backed exact source/result bytes need no duplicate copy. Every
  # unbacked actual log, source fixture and safe source catalogue is retained.
  if text_candidate and not ref:
   b=raw(p,32*1024*1024)
   try:
    value=privacy_json(b) if suffix=='.json' else None;privacy(b)
   except (ValueError,RuntimeError,UnicodeError) as error:
    row['not_copied_reason']='PRIVACY_OR_TEXT_SCREEN_REFUSAL';deferred.append({'stage':name,'path':relative,'reason':str(error)});continue
   target='preserved/'+name+'/'+relative;put(target,b)
   row['new_recovery']={'path':target,'bytes':len(b),'sha256':sha(b)}
   copied.append({'path':target,'origin':str(p),'bytes':len(b),'sha256':sha(b)});copy_count+=1;copy_bytes+=len(b)
  elif not ref:
   reason='regenerable_runtime_cache_not_copied' if in_cache else 'binary_or_unclassified_not_copied'
   row['not_copied_reason']=reason
   if not in_cache:unknown_binary.append({'path':relative,'bytes':row['bytes'],'sha256':row['sha256']})
  if suffix in SOURCE_EXT and not in_cache:
   runtime_sources.append({'stage':name,'path':relative,'bytes':row['bytes'],'sha256':row['sha256'],
       'recovery':row.get('prior_recovery',row.get('new_recovery'))})
  if p.name in ('PUBLIC_RESULT.json','RESULT.json') and len(Path(relative).parts)==1:
   v=json.loads(raw(p));reports.append({'stage':name,'result_path':relative,'bytes':row['bytes'],'sha256':row['sha256'],
      'status':v.get('status'),'checks':v.get('checks'),'case_summaries':[{k:c[k] for k in ('name','exit','child_reaped','result') if k in c} for c in v.get('cases',[])],
      'graphics_or_native_started':v.get('graphics_or_native_jobs_started',v.get('graphics_or_native_jobs_started',False)),
      'application_adopted':v.get('application_adopted',False)})
 summary={'name':name,'absolute_boundary':str(base),'resolved_boundary':str(base.resolve()),'file_count':len(tree['files']),
  'directory_count':len(tree['directories']),'logical_bytes':sum(r['bytes'] for r in tree['files']),'aliases':tree['aliases'],
  'regular_single_link_files':True,'prior_hash_recoverable_files':matched,'new_preserved_files':copy_count,'new_preserved_bytes':copy_bytes,
  'extensions':counts,'unbacked_noncache_binary_or_unknown':unknown_binary}
 stages.append(summary);js('stage-inventories/'+name+'.json',{'format':'has_owned_cpu_stage_readonly_inventory_1',**summary,
  'directories':tree['directories'],'files':tree['files'],'process_check_performed':False,'cleanup_executed':False})
js('PRESERVED_ORIGINS.json',{'format':'has_easing_cpu_missing_artifacts_1','files':copied,'count':len(copied),'bytes':sum(r['bytes'] for r in copied)})
js('SOURCE_RECOVERY_CHECKS.json',{'format':'has_easing_cpu_source_hash_recovery_1','files':runtime_sources,
 'unrecoverable_source_rows':[r for r in runtime_sources if not r['recovery']],'revision_of_prior_checkpoint':REV})
js('STAGE_RESULTS.json',{'format':'has_easing_cpu_retained_result_scopes_1','reports':reports,
 'failed_and_partial_result_statuses_not_rewritten':True,'parse_only_zero_assertions_not_graphical_qualification':True,
 'current_process_closure_not_inferred_from_old_results':True})
js('AUDIT_SUMMARY.json',{'format':'has_easing_cpu_cleanup_readiness_1','status':'PREPARATION_ONLY_NOT_DELETE_AUTHORIZATION',
 'stages':stages,'stage_count':len(stages),'total_files':sum(r['file_count'] for r in stages),
 'total_directories':sum(r['directory_count'] for r in stages),'total_logical_bytes':sum(r['logical_bytes'] for r in stages),
 'new_preserved_files':len(copied),'new_preserved_bytes':sum(r['bytes'] for r in copied),'deferred_privacy_files':deferred,
 'unbacked_noncache_binary_files':sum(len(r['unbacked_noncache_binary_or_unknown']) for r in stages),
 'process_or_CIM_checks_performed':False,'delete_move_or_graphics_performed':False,
 'requires_next_packet_remote_verification_and_fresh_Root_process_check':True})
print(json.dumps({'stage_count':len(stages),'total_files':sum(r['file_count'] for r in stages),
 'logical_bytes':sum(r['logical_bytes'] for r in stages),'new_preserved_files':len(copied),
 'new_preserved_bytes':sum(r['bytes'] for r in copied),'deferred_privacy_files':len(deferred),
 'unbacked_noncache_binary_files':sum(len(r['unbacked_noncache_binary_or_unknown']) for r in stages)}))
