from pathlib import Path
import gzip,hashlib,json,subprocess
R=Path.cwd();O=R/'output/source-choices-native-independent-cleanup-audit-20261114';sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,**kw):return subprocess.check_output(['git',*a],cwd=R,**kw)
def tree(revision,prefix=''):
 rows={}
 for r in git('ls-tree','-rz',revision,*([prefix] if prefix else [])).split(b'\0'):
  if r:
   m,p=r.split(b'\t',1);_,kind,oid=m.split()
   if kind==b'blob':rows[p.decode()]=oid.decode()
 return rows
HEAD=git('rev-parse','HEAD').decode().strip();prefix='experiments/source_appearance/main_native_app_actual_20261113/';entries=tree(HEAD,prefix)
def bodies(oids):
 wanted=list(dict.fromkeys(oids));raw=git('cat-file','--batch',input=b''.join(x.encode()+b'\n' for x in wanted));out={};offset=0
 for oid in wanted:
  end=raw.index(b'\n',offset);actual,kind,size=raw[offset:end].split();start=end+1;finish=start+int(size)
  assert actual.decode()==oid and kind==b'blob' and raw[finish:finish+1]==b'\n';out[oid]=raw[start:finish];offset=finish+1
 assert offset==len(raw);return out
payloads=bodies(entries.values());index=json.loads(payloads[entries[prefix+'INDEX.json']]);index_bad=[]
for row in index['files']:
 data=payloads[entries[prefix+row['path']]]
 if len(data)!=row['bytes'] or sha(data)!=row['sha256']:index_bad.append(row['path'])
results=[];code_total=0;code_bad=[];code_missing=[]
for phase in ['core14','wider11']:
 inv=json.loads((O/(phase+'-fresh-inventory.json')).read_bytes());base=Path(inv['absolute_root']);byname={r['path']:r for r in inv['files']};verified=json.loads((base/'verification.json').read_bytes());rev=verified['source_before']['revision'];old=tree(rev);code=[]
 for row in inv['files']:
  name=row['path']
  if name.startswith('Studio/') and (name.split('/')[1] in ['src','tools','tests','data','examples'] or name in ['Studio/run.py','Studio/project.godot','Studio/main.tscn']) and not any(p in ['output','.godot','__pycache__'] for p in Path(name).parts) and not name.endswith('.pyc'):code.append(row)
 missing=[r['path'] for r in code if r['path'][7:] not in old];code_missing.extend(missing);oldpayloads=bodies([old[r['path'][7:]] for r in code if r['path'][7:] in old]);recovery=[];bad=[]
 for r in code:
  name=r['path'][7:]
  if name not in old:continue
  blob=oldpayloads[old[name]];actual=(base/r['path']).read_bytes()
  mode='exact_git_blob' if actual==blob else ('git_blob_LF_to_CRLF' if actual==blob.replace(b'\n',b'\r\n') else ('git_blob_selected_LF_to_CRLF' if actual.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n') else 'unrecovered'))
  recipe={'path':r['path'],'git_blob_oid':old[name],'original_sha256':r['sha256'],'recovery':mode}
  if mode=='git_blob_selected_LF_to_CRLF':
   chunks=actual.split(b'\n');ordinals=[i for i,chunk in enumerate(chunks[:-1]) if chunk.endswith(b'\r')];recipe['crlf_newline_ordinals']=ordinals
   normalized=blob.replace(b'\r\n',b'\n').split(b'\n');rebuilt=b''.join(chunk+(b'\r\n' if i in ordinals else b'\n') for i,chunk in enumerate(normalized[:-1]))+normalized[-1];assert rebuilt==actual
  recovery.append(recipe)
  if mode=='unrecovered':bad.append(r['path'])
 code_bad.extend(bad);code_total+=len(code)
 joins=[]
 for row in inv['files']:
  name=row['path']
  if name.startswith('cases/') and (name.endswith('/expected.json') or name.endswith('/conversion-metadata/parameters.json')):
   target=prefix+phase+'/actual/'+name;compressed=target not in entries;target=target+'.gz' if compressed else target;data=payloads[entries[target]];data=gzip.decompress(data) if compressed else data;joins.append({'candidate':name,'git_path':target,'git_blob_oid':entries[target],'gzip_recovered':compressed,'equal':sha(data)==row['sha256'],'sha256':row['sha256']})
 raw=gzip.decompress(payloads[entries[prefix+phase+'/actual/root/verification.json.gz']])
 results.append({'phase':phase,'code_revision':rev,'code_files_checked':len(code),'code_missing':missing,'code_mismatches':bad,'code_recovery':recovery,'code_exact_git_blob':sum(r['recovery']=='exact_git_blob' for r in recovery),'code_exact_from_git_LF_to_CRLF':sum(r['recovery']=='git_blob_LF_to_CRLF' for r in recovery),'code_exact_from_git_selected_LF_to_CRLF':sum(r['recovery']=='git_blob_selected_LF_to_CRLF' for r in recovery),'metadata_joins':joins,'verification_exact':sha(raw)==byname['verification.json']['sha256']})
proof={'format':'has_independent_git_recovery_batch_proof_1','HEAD':HEAD,'same_as_local_origin_main':HEAD==git('rev-parse','refs/remotes/origin/main').decode().strip(),'network_verification_performed':False,'compact_tree_blobs_read':len(entries),'unique_compact_objects_read':len(payloads),'indexed_payloads_verified':len(index['files']),'index_mismatches':index_bad,'snapshot_code_files_checked':code_total,'snapshot_code_missing':code_missing,'snapshot_code_mismatches':code_bad,'candidate_joins':results,'all_checks_passed':not(index_bad or code_bad or code_missing) and all(x['verification_exact'] and all(j['equal'] for j in x['metadata_joins']) for x in results),'prior_attempt_note':'First audit git show REV:path hit Windows long-path argument disambiguation for two parameters paths. This supplemental independent batch uses ls-tree OIDs and cat-file batch, resolving those checks without filenames-as-revs. Prior errors remain recorded honestly.','not_recoverable_from_Git':'Discarded test GLB/HAS/PNG/audio/movie/import-cache binaries are not represented as recoverable. Retained originals and newer useful actual runs remain outside removal scope.'}
p=O/'GIT_RECOVERY_BATCH_PROOF.json';p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'proof':str(p),'passed':proof['all_checks_passed'],'indexed':len(index['files']),'code_files':code_total,'joins':sum(len(r['metadata_joins']) for r in results),'missing':code_missing,'mismatch_count':len(code_bad)}))
