"""Verify every selected raw byte and functional source in a fresh remote clone."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--checkout',type=Path,required=True);p.add_argument('--revision',required=True);a=p.parse_args()
CONTROL=Path(__file__).resolve().parent;root=a.checkout.resolve(strict=True)
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.longpaths=true',*args],cwd=root)
def remote():return git('ls-remote','origin','refs/heads/main').decode().split()[0]
selection=json.loads((CONTROL/'IMPORT_OFF_PUBLICATION_SELECTION_20261121.json').read_bytes())
assert remote()==a.revision==git('rev-parse','HEAD').decode().strip()
assert git('rev-parse','HEAD^').decode().strip()==selection['base']
assert git('config','--local','core.autocrlf').decode().strip()=='false'
assert git('config','--local','core.longpaths').decode().strip()=='true'
changed=set(git('diff-tree','--no-commit-id','--name-only','-r','-z','HEAD').decode().rstrip('\0').split('\0'))
rows=selection['paths'];assert changed=={r['path'] for r in rows}
tree={}
for raw in git('ls-tree','-rz','HEAD').split(b'\0'):
 if not raw:continue
 meta,name=raw.split(b'\t',1);mode,kind,oid=meta.decode().split();tree[name.decode()]={'mode':mode,'kind':kind,'oid':oid}
def check(name,row,mode=False):
 raw=(root/name).read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],name
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_sha1']==tree[name]['oid'],name
 assert tree[name]['kind']=='blob'
 if mode:assert row['mode']==tree[name]['mode']
for row in rows:check(row['path'],row,True)
sources=json.loads((CONTROL/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').read_bytes());assert len(sources)==1103
spec=importlib.util.spec_from_file_location('fresh_full_snapshot',root/'experiments/reference_body_20261120/run_full.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
actual=module.snapshot();assert set(actual)==set(sources)
for name,row in sources.items():check(name,row)
assert not git('status','--porcelain')
assert remote()==a.revision
record={'format':'has_import_off_remote_verification_1','status':'PASS','revision':a.revision,'parent':selection['base'],
 'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'fresh_checkout':str(root),'selected_count':len(rows),
 'selected_bytes':sum(r['bytes'] for r in rows),'functional_source_count':1103,
 'all_selected_raw_sha256_git_blobs_modes_exact':True,'functional_raw_bytes_and_membership_exact':True,
 'remote_main_before_after':a.revision,'clean_before_fixtures':True,'verified_ns':time.time_ns()}
(CONTROL/'IMPORT_OFF_REMOTE_VERIFIED_20261121.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
