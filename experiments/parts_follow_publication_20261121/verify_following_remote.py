"""Read independently fetched Git blobs and verify the whole published increment."""
from pathlib import Path
import hashlib,json,subprocess
root=Path(__file__).resolve().parents[1]
fresh=root.parent/'has-feature-retrieved-20261121-243e6a1e'
revision='edffb651181825517dc6bc5d9c536027c11b6e14'
def git(where,*args):return subprocess.check_output(['git','-C',str(where),*args])
assert git(fresh,'rev-parse','origin/main').decode().strip()==revision
assert git(root,'rev-parse',revision+'^{tree}')==git(fresh,'rev-parse',revision+'^{tree}')
names=[n for n in git(root,'diff-tree','-r','--no-commit-id','--name-only','-z',revision).decode().split('\0') if n]
raw=git(root,'ls-tree','-r','-z',revision,'--',*names)
objects=[]
for line in raw.split(b'\0'):
    if not line:continue
    fields,path=line.split(b'\t',1);mode,kind,sha=fields.split()
    assert mode==b'100644' and kind==b'blob'
    objects.append((path.decode(),sha.decode()))
assert len(names)==len(objects)==81
process=subprocess.run(['git','-C',str(fresh),'cat-file','--batch'],input=('\n'.join(sha for _,sha in objects)+'\n').encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
blob=process.stdout;offset=0;rows=[]
for name,sha in objects:
    newline=blob.index(b'\n',offset);header=blob[offset:newline].split();assert header[:2]==[sha.encode(),b'blob']
    size=int(header[2]);data=blob[newline+1:newline+1+size];offset=newline+size+2
    assert blob[offset-1:offset]==b'\n' and data==(root/name).read_bytes(),name
    assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+data).hexdigest()==sha
    rows.append({'path':name,'bytes':size,'sha256':hashlib.sha256(data).hexdigest(),'git_blob':sha})
assert offset==len(blob)
report={'format':'has_following_remote_verification_1','status':'PASS','revision':revision,'retrieved_parent':'c0618407539ac51a66cb7cb8c5fe44d5acee5e0d','fresh_retrieval':str(fresh),'tree':git(fresh,'rev-parse',revision+'^{tree}').decode().strip(),'files':rows,'exact_files':len(rows),'exact_bytes':sum(r['bytes'] for r in rows),'remote_tracking_main_matches':True,'private_art_uploaded':False,'cleanup_authorized_only_for_disposable_verified_outputs':True}
(root/'output/FOLLOWER_REMOTE_VERIFIED_20261121.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
print(json.dumps({key:report[key] for key in ['status','revision','exact_files','exact_bytes','tree']}))
