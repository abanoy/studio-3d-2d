from pathlib import Path
import ctypes,ctypes.wintypes as W,gzip,hashlib,json,os,stat,subprocess,time
from collections import Counter
ROOT=Path.cwd().resolve(); OUT=ROOT/'output/source-choices-native-independent-cleanup-audit-20261114'
PLAN=json.loads((ROOT/'output/source-choices-native-cleanup-plan-20261114/PLAN.json').read_bytes())
SHA=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):
 p=OUT/n;p.write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf-8');return {'path':str(p),'bytes':p.stat().st_size,'sha256':SHA(p.read_bytes())}
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
HEAD=git('rev-parse','HEAD').decode().strip()
class Info(ctypes.Structure):
 _fields_=[('attrs',W.DWORD),('ctime',W.FILETIME),('atime',W.FILETIME),('mtime',W.FILETIME),('volume',W.DWORD),('sizehi',W.DWORD),('sizelo',W.DWORD),('links',W.DWORD),('indexhi',W.DWORD),('indexlo',W.DWORD)]
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetFileInformationByHandle.argtypes=[W.HANDLE,ctypes.POINTER(Info)];k.GetFileInformationByHandle.restype=W.BOOL
import msvcrt
errors=[]
def stamped(p,handle_info=False):
 before=p.stat(follow_symlinks=False)
 if before.st_file_attributes & 0x400:raise ValueError('Reparse refused: '+str(p))
 with p.open('rb') as stream:
  opened=os.fstat(stream.fileno());i=Info()
  if not k.GetFileInformationByHandle(msvcrt.get_osfhandle(stream.fileno()),ctypes.byref(i)):raise ctypes.WinError(ctypes.get_last_error())
  digest=hashlib.file_digest(stream,'sha256').hexdigest();after=os.fstat(stream.fileno())
 final=p.stat(follow_symlinks=False)
 if any((x.st_size,x.st_mtime_ns,x.st_ino,x.st_dev)!=(before.st_size,before.st_mtime_ns,before.st_ino,before.st_dev) for x in (opened,after,final)):raise ValueError('Changed while read: '+str(p))
 row={'bytes':before.st_size,'mtime_ns':before.st_mtime_ns,'sha256':digest}
 if handle_info:row.update(hardlinks=int(i.links),device=int(i.volume),file_index=int(i.indexhi)<<32|int(i.indexlo))
 return row

def inventory(base):
 files=[];dirs=[];reparse=[];pending=[base]
 while pending:
  directory=pending.pop()
  if directory.stat(follow_symlinks=False).st_file_attributes & 0x400:reparse.append(str(directory));continue
  with os.scandir(directory) as entries:
   for entry in entries:
    p=Path(entry.path);info=entry.stat(follow_symlinks=False)
    if info.st_file_attributes & 0x400:reparse.append(str(p));continue
    rel=p.relative_to(base).as_posix()
    if stat.S_ISDIR(info.st_mode):dirs.append(rel);pending.append(p)
    elif stat.S_ISREG(info.st_mode):files.append({'path':rel,**stamped(p,True)})
    else:errors.append('Unsupported file kind '+str(p))
 return {'absolute_root':str(base),'files':sorted(files,key=lambda r:r['path']),'directories':sorted(dirs),'reparse_points':reparse}

rows=[];all_paths=[];original_rows={};protected_kept=[ROOT/'output/sfm-bone-bindings-native-launch-20261114T033026205/run',ROOT/'output/sfm-extra-native-launch-20261114T013526736/run']
for old in PLAN['candidates']:
 base=Path(old['absolute_path']);assert base.parent==ROOT/'output/source-choices-native';assert base.resolve(strict=True)==base
 for ancestor in [base,*base.parents]:
  if ancestor==ROOT.parent:break
  assert not ancestor.stat(follow_symlinks=False).st_file_attributes & 0x400
 print('AUDIT_BEGIN '+old['phase'],flush=True)
 inv=inventory(base);byname={r['path']:r for r in inv['files']};all_paths.extend(str(base/r['path']) for r in inv['files'])
 prior=json.loads(Path(old['inventory']['path']).read_bytes());prior_map={r['path']:r for r in prior['files']}
 differences=[]
 for name in sorted(set(byname)|set(prior_map)):
  if name not in byname or name not in prior_map or any(byname[name][q]!=prior_map[name][q] for q in ['bytes','mtime_ns','sha256']):differences.append(name)
 proofs=save(old['phase']+'-fresh-inventory.json',inv)
 original_proof=json.loads((base/'originals-before.json').read_bytes());source_signatures=set();orig_status=[]
 for path,expected in original_proof.items():
  retained=Path(path);assert not retained.is_relative_to(base);fresh={r['path']:{q:r[q] for q in ['bytes','mtime_ns','sha256']} for r in inventory(retained)['files']}
  mismatch=[n for n in sorted(set(fresh)|set(expected)) if fresh.get(n)!=expected.get(n)]
  source_signatures.update((r['bytes'],r['sha256']) for r in fresh.values())
  original_rows[path]=fresh;orig_status.append({'root':path,'files':len(fresh),'bytes':sum(r['bytes'] for r in fresh.values()),'differences':mismatch})
 inputs=[r for r in inv['files'] if r['path'].startswith('inputs/')];unbacked=[r['path'] for r in inputs if (r['bytes'],r['sha256']) not in source_signatures]
 packages=json.loads((base/'packages-before-readers.json').read_bytes());actual_has=[r['path'] for r in inv['files'] if r['path'].lower().endswith('.has')]
 unknown_has=[p for p in actual_has if str(base/p) not in packages and p not in ['Studio/examples/tutorials/first-movie.has','Studio/examples/tutorials/practice.has']]
 unexpected_recovery=[p for p in inv['directories'] if 'recovery' in Path(p).parts]
 verify=json.loads((base/'verification.json').read_bytes());revision=verify['source_before']['revision']
 tree=git('ls-tree','-rz',revision);oids={}
 for record in tree.split(b'\0'):
  if not record:continue
  meta,name=record.split(b'\t',1);mode,kind,oid=meta.split();oids[name.decode()]=oid.decode()
 code= [r for r in inv['files'] if r['path'].startswith('Studio/') and (r['path'].split('/')[1] in ['src','tools','tests','data','examples'] or r['path'] in ['Studio/run.py','Studio/project.godot','Studio/main.tscn']) and not any(part in ['__pycache__','.godot','output'] for part in Path(r['path']).parts) and not r['path'].endswith('.pyc')]
 code_missing=[];code_mismatch=[]
 for r in code:
  name=r['path'][7:]
  if name not in oids:code_missing.append(name)
  elif SHA(git('cat-file','blob',oids[name]))!=r['sha256']:code_mismatch.append(name)
 prefix='experiments/source_appearance/main_native_app_actual_20261113/'+old['phase']+'/actual/'
 meta_rows=[]
 for r in inv['files']:
  name=r['path']
  if name.startswith('cases/') and (name.endswith('/expected.json') or name.endswith('/conversion-metadata/parameters.json')):
   blob=prefix+name
   try:data=git('show',HEAD+':'+blob)
   except subprocess.CalledProcessError:errors.append('Missing Git metadata '+blob);continue
   meta_rows.append({'candidate':name,'git_path':blob,'equal':SHA(data)==r['sha256'],'sha256':r['sha256']})
 recovered=gzip.decompress(git('show',HEAD+':'+prefix+'root/verification.json.gz'))
 joined=SHA(recovered)==byname['verification.json']['sha256']
 row={'phase':old['phase'],'root':str(base),'files':len(inv['files']),'directories':len(inv['directories']),'bytes':sum(r['bytes'] for r in inv['files']),'prior_inventory_differences':differences,'reparse_points':inv['reparse_points'],'hardlinked_files':[r['path'] for r in inv['files'] if r['hardlinks']!=1],'fresh_inventory':proofs,'original_families':orig_status,'owned_inputs':len(inputs),'owned_inputs_without_matching_retained_original':unbacked,'HAS_count':len(actual_has),'case_packages':len(packages),'unclassified_HAS':unknown_has,'actual_recovery_directories':unexpected_recovery,'snapshot_code_revision':revision,'snapshot_code_files_checked':len(code),'snapshot_code_absent_from_revision':code_missing,'snapshot_code_mismatch':code_mismatch,'git_metadata_exact':all(r['equal'] for r in meta_rows),'git_metadata_joins':meta_rows,'git_verification_exact':joined,'historical_test_passed':verify['passed'],'historical_all_preservation':all(verify['preservation'].values())}
 rows.append(row);print('AUDIT_END '+old['phase']+' '+str(row['files'])+'files',flush=True)

# Restart Manager registers exact file paths read-only, reports known applications
# using these resources; never requests shutdown, restart or process termination.
class RM_UNIQUE_PROCESS(ctypes.Structure):_fields_=[('pid',W.DWORD),('start',W.FILETIME)]
class RM_PROCESS_INFO(ctypes.Structure):_fields_=[('process',RM_UNIQUE_PROCESS),('app',W.WCHAR*256),('service',W.WCHAR*64),('type',ctypes.c_int),('status',W.ULONG),('session',W.DWORD),('restartable',W.BOOL)]
rmproof={'format':'has_readonly_restart_manager_resource_audit_1','files_registered':0,'applications':[],'status':'unavailable','limitations':'Point-in-time Windows Restart Manager resource report; it does not prove no arbitrary shared readers or transient future use.'}
try:
 rm=ctypes.WinDLL('rstrtmgr');session=W.DWORD();key=ctypes.create_unicode_buffer(33)
 rm.RmStartSession.argtypes=[ctypes.POINTER(W.DWORD),W.DWORD,W.LPWSTR];rm.RmRegisterResources.argtypes=[W.DWORD,W.UINT,ctypes.POINTER(W.LPCWSTR),W.UINT,ctypes.c_void_p,W.UINT,ctypes.c_void_p];rm.RmGetList.argtypes=[W.DWORD,ctypes.POINTER(W.UINT),ctypes.POINTER(W.UINT),ctypes.POINTER(RM_PROCESS_INFO),ctypes.POINTER(W.DWORD)]
 result=rm.RmStartSession(ctypes.byref(session),0,key);rmproof['start_result']=result
 if result:raise OSError('RmStartSession='+str(result))
 try:
  for offset in range(0,len(all_paths),500):
   chunk=all_paths[offset:offset+500];values=(W.LPCWSTR*len(chunk))(*chunk);result=rm.RmRegisterResources(session,len(chunk),values,0,None,0,None)
   if result:raise OSError('RmRegisterResources='+str(result))
   rmproof['files_registered']+=len(chunk)
  need=W.UINT();count=W.UINT();reasons=W.DWORD();result=rm.RmGetList(session,ctypes.byref(need),ctypes.byref(count),None,ctypes.byref(reasons))
  if result==234:
   count=W.UINT(need.value);items=(RM_PROCESS_INFO*count.value)();result=rm.RmGetList(session,ctypes.byref(need),ctypes.byref(count),items,ctypes.byref(reasons))
   if result:raise OSError('RmGetList='+str(result))
   rmproof['applications']=[{'pid':p.process.pid,'name':p.app,'service':p.service,'session':p.session,'type':p.type} for p in items[:count.value]]
  elif result:raise OSError('RmGetList='+str(result))
  rmproof.update(status='observed',get_list_result=result,reboot_reason=reasons.value)
 finally:rm.RmEndSession(session)
except Exception as e:rmproof['error']=str(e)
rm_record=save('restart-manager-proof.json',rmproof)
protected=[{'path':str(p),'exists':p.is_dir(),'candidate_overlap':any(p.is_relative_to(Path(r['root'])) or Path(r['root']).is_relative_to(p) for r in rows)} for p in protected_kept]
original_record=save('retained-originals-fresh-proof.json',original_rows)
summary={'format':'has_independent_two_old_native_cleanup_audit_1','checked_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'HEAD':HEAD,'local_origin_main':git('rev-parse','refs/remotes/origin/main').decode().strip(),'source_main_edits':False,'deletion_performed':False,'candidates':rows,'retained_original_proof':original_record,'protected_current_useful_runs':protected,'restart_manager':rm_record,'errors':errors,'execution_gate':'FULL suite is running. This is output-only inventory evidence. Root must obtain terminalPASS, publish and verify remote, then establish fresh current nonuse and deletion access. Missing process identities remain unresolved until root final audit.'}
record=save('AUDIT.json',summary);print(json.dumps({'audit':record,'candidate_files':sum(r['files'] for r in rows),'bytes':sum(r['bytes'] for r in rows),'errors':errors,'rm_status':rmproof['status'],'rm_applications':rmproof['applications']}),flush=True)
