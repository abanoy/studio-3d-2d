"""Verify a separately fetched bare remote store without touching a live Full."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time

p=argparse.ArgumentParser();p.add_argument('--git-dir',type=Path,required=True);p.add_argument('--revision',required=True);p.add_argument('--base',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];remote=a.git_dir.resolve(strict=True)
assert remote.parent==root.parent and remote.name.startswith('has-voxel-integration-remote-20261121')
assert not (remote/'objects/info/alternates').exists()
def local(*args):return subprocess.check_output(['git',*args],cwd=root)
def fetched(*args):return subprocess.check_output(['git','--git-dir',str(remote),*args],cwd=root)
assert local('rev-parse','HEAD').decode().strip()==a.revision
assert fetched('rev-parse','FETCH_HEAD').decode().strip()==a.revision
assert fetched('remote','get-url','origin').strip()==b'https://github.com/abanoy/studio-3d-2d.git'
def tree(raw):
 result={}
 for row in raw.split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t',1);mode,kind,oid=meta.split();assert kind==b'blob';result[name.decode()]={'mode':mode.decode(),'blob':oid.decode()}
 return result
ours=tree(local('ls-tree','-r','-z',a.revision));theirs=tree(fetched('ls-tree','-r','-z',a.revision));assert ours==theirs
changed={s.decode() for s in local('diff','--name-only','-z',a.base,a.revision).split(b'\0') if s}
functional={n for n in ours if (n.split('/')[0] in {'src','tools','tests','data','examples'} or n in {'run.py','launch.pyw','project.godot','main.tscn','dependencies.json'}) and '__pycache__' not in n.split('/') and not n.endswith('.pyc')}
names=sorted(changed|functional)
requests=b''.join(theirs[n]['blob'].encode()+b'\n' for n in names)
process=subprocess.Popen(['git','--git-dir',str(remote),'cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
raw,errors=process.communicate(requests);assert process.returncode==0 and not errors
at=0;rows={}
for n in names:
 end=raw.index(b'\n',at);oid,kind,size=raw[at:end].split();assert oid.decode()==theirs[n]['blob'] and kind==b'blob'
 size=int(size);at=end+1;data=raw[at:at+size];at+=size;assert raw[at:at+1]==b'\n';at+=1
 assert (root/n).read_bytes()==data,n
 assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+data).hexdigest()==oid.decode(),n
 rows[n]={**theirs[n],'sha256':hashlib.sha256(data).hexdigest(),'bytes':size}
assert at==len(raw)
out=root/'output'/('voxel-branch-remote-verified-'+str(time.time_ns()));out.mkdir()
inventory=(json.dumps(rows,indent=2,ensure_ascii=True)+'\n').encode();(out/'files.json').write_bytes(inventory)
result={'format':'has_independent_bare_remote_verification_1','status':'PASS','revision':a.revision,'base':a.base,'independent_remote_git_store':str(remote),'alternates_used':False,'all_tree_blob_ids_and_modes_match':True,'tree':fetched('rev-parse',a.revision+'^{tree}').decode().strip(),'verified_raw_files':len(rows),'verified_raw_bytes':sum(r['bytes'] for r in rows.values()),'changed_files':len(changed),'inventory_sha256':hashlib.sha256(inventory).hexdigest()}
(out/'verification.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({'folder':str(out),**result},indent=2))
