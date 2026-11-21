"""Root read-only exact7 preflight; does not delete or move anything."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,time,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';BASE=ROOT.parent
REMOTE=BASE/'has-import-info-full-20261121-2f1acbd';PREP=OUT/'source-easing-cpu-cleanup-readiness-prep-20261121'
PUBLISHED=REMOTE/'experiments/continuation_components_20261121/source/source-easing-cpu-cleanup-readiness-prep-20261121'
NAMES=['has-easing-headless-1795254145851799500','has-easing435-app-cpu-1795254384845561100','has-easing435-app-cpu-1795254695259497400','has-easing435-app-cpu-1795254761995523000','has-easing-headless-1795254831934151300','has-easing435-graphics-parse-1795258322734840400','has-easing-c315-graphics-parse-1795260866931895900']
def sha(data):return hashlib.sha256(data).hexdigest()
def stamp(s):return [str(v) for v in (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))]
def safe(path):
 assert path.is_absolute() and path.is_relative_to(BASE)
 for p in (path,*path.parents):
  s=p.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
  if p==BASE:break
 return path
def read(path):
 safe(path);s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 raw=path.read_bytes();assert stamp(s)==stamp(path.lstat());return raw
remote=json.loads(read(OUT/'IMPORT_INFO_REMOTE_VERIFIED_20261121.json'));assert remote['status']=='PASS' and remote['revision']=='2f1acbd7867087d9f18cfbc1122cc0c883c5f788'
manifest=read(PREP/'SOURCE_PINS.json');assert sha(manifest)=='66e6b911c56f61b5adcc95ef1978e95578e74e74b2365eb4a9b204847d17ad29' and read(PUBLISHED/'SOURCE_PINS.json')==manifest
for row in json.loads(manifest)['files']:
 blob=read(PREP/row['path']);assert len(blob)==row['bytes'] and sha(blob)==row['sha256'] and read(PUBLISHED/row['path'])==blob
inventories=[json.loads(read(PREP/'stage-inventories'/f'{n}.json')) for n in NAMES]
assert sum(x['file_count'] for x in inventories)==5640 and sum(x['logical_bytes'] for x in inventories)==47366153
objects={};targets=[];source_files=0
for inv in inventories:
 root=safe(BASE/inv['name']);assert inv['name'] in NAMES and root.parent==BASE and root.resolve()==root and str(root)==inv['absolute_boundary']==inv['resolved_boundary']
 actual_files=set();actual_dirs={'.'}
 for here,dirs,files in os.walk(root,followlinks=False):
  for leaf in dirs:
   p=safe(Path(here)/leaf);actual_dirs.add(p.relative_to(root).as_posix())
  actual_files.update((Path(here)/x).relative_to(root).as_posix() for x in files)
 assert actual_files=={x['path'] for x in inv['files']} and actual_dirs=={x['path'] for x in inv['directories']}
 for row in inv['directories']:assert stamp(safe(root/row['path']).lstat())==row['identity']
 for row in inv['files']:
  p=root/row['path'];raw=read(p);assert stamp(p.lstat())==row['identity_native64_rawmode'] and len(raw)==row['bytes'] and sha(raw)==row['sha256']
  if 'new_recovery' in row:recovery=read(PUBLISHED/row['new_recovery']['path']);assert recovery==raw
  elif row.get('prior_recovery',{}).get('kind')=='prior_published_source_archive_file':assert read(REMOTE/row['prior_recovery']['path'])==raw
  elif row.get('prior_recovery',{}).get('kind')=='c315_functional_git_blob':
   ref=row['prior_recovery'];assert ref['revision']=='c31576d0c1d84030d51ec886f2f3976a60a70c7b';objects.setdefault(ref['git_sha1'],(row['bytes'],row['sha256']));assert objects[ref['git_sha1']]==(row['bytes'],row['sha256'])
  else:
   assert row['path']=='Studio/web/studio.svg' and row['bytes']==720 and row['sha256']=='fd9ec2eff6157f02d93e51f1f9e9e2040fe407aa13f5922ac7e2967c76b1d450';assert read(REMOTE/'web/studio.svg')==raw
  source_files+=1
 targets.append({'path':str(root),'name':inv['name'],'files':inv['file_count'],'logical_bytes':inv['logical_bytes'],'root_identity':stamp(root.lstat())})
ordered=sorted(objects)
process=subprocess.run(['git','cat-file','--batch'],cwd=REMOTE,input=('\n'.join(ordered)+'\n').encode(),capture_output=True,check=True)
offset=0
for oid in ordered:
 end=process.stdout.index(b'\n',offset);header=process.stdout[offset:end].decode().split();assert header[0]==oid and header[1]=='blob';length=int(header[2]);offset=end+1;data=process.stdout[offset:offset+length];offset+=length;assert process.stdout[offset:offset+1]==b'\n';offset+=1;assert (len(data),sha(data))==objects[oid]
assert offset==len(process.stdout) and not process.stderr
value={'format':'has_easing_cleanup_preflight_1','status':'PASS','remote_revision':remote['revision'],'targets':targets,'files':source_files,'logical_bytes':47366153,'exact_native64_identities_and_membership_preserved':True,'all_source_evidence_recovery_bytes_verified':True,'unique_c315_blobs_verified':len(objects),'process_check_still_required':True,'removed':False,'recorded_ns':time.time_ns()}
if '--verify-only' not in sys.argv:
 path=OUT/'EASING_CLEANUP_EXACT_PREFLIGHT_20261121.json';assert not path.exists();path.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='targets'}))
