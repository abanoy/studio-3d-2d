from pathlib import Path
import hashlib,json,subprocess,time
root=Path(__file__).resolve().parents[1]
feature=root.parent/'has-backhair-reconstruction-20261121'
bare=root.parent/'has-voxel-integration-remote-20261121.git'
revision='7f1d85d7ea57a3bafd16e5be085e18609830c304'
base='43dbdecc759e971a80f0d1e468e1e7d1e3b9ed2b'
def local(*args):return subprocess.check_output(['git','-C',str(feature),*args])
def fetched(*args):return subprocess.check_output(['git','--git-dir',str(bare),*args])
assert local('rev-parse','HEAD').decode().strip()==revision
assert fetched('rev-parse','FETCH_HEAD').decode().strip()==revision
assert not (bare/'objects/info/alternates').exists()
assert fetched('remote','get-url','origin').strip()==b'https://github.com/abanoy/studio-3d-2d.git'
def tree(data):
    result={}
    for row in data.split(b'\0'):
        if not row:continue
        meta,name=row.split(b'\t',1);mode,kind,oid=meta.split();assert kind==b'blob'
        result[name.decode()]={'mode':mode.decode(),'blob':oid.decode()}
    return result
ours=tree(local('ls-tree','-r','-z',revision));theirs=tree(fetched('ls-tree','-r','-z',revision));assert ours==theirs
changed={n.decode() for n in local('diff','--name-only','-z',base,revision).split(b'\0') if n}
functional={n for n in ours if (n.split('/')[0] in {'src','tools','tests','data','examples'} or n in {'run.py','launch.pyw','project.godot','main.tscn','dependencies.json'}) and '__pycache__' not in n.split('/') and not n.endswith('.pyc')}
names=sorted(changed|functional)
process=subprocess.Popen(['git','--git-dir',str(bare),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
raw,errors=process.communicate(b''.join(theirs[n]['blob'].encode()+b'\n' for n in names));assert process.returncode==0 and not errors
at=0;rows={};normalized=[]
for name in names:
    end=raw.index(b'\n',at);oid,kind,size=raw[at:end].split();size=int(size);at=end+1;data=raw[at:at+size];at+=size
    assert raw[at:at+1]==b'\n';at+=1;assert kind==b'blob' and oid.decode()==theirs[name]['blob']
    assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+data).hexdigest()==oid.decode()
    working=(feature/name).read_bytes();exact=working==data
    if not exact:
        assert working.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n'),name
        normalized.append(name)
    rows[name]={**theirs[name],'remote_bytes':size,'remote_sha256':hashlib.sha256(data).hexdigest(),
                'working_raw_sha256':hashlib.sha256(working).hexdigest(),'working_raw_exact':exact}
assert at==len(raw)
out=root/'output'/('reconstruction-branch-readback-'+str(time.time_ns()));out.mkdir()
inventory=(json.dumps(rows,indent=2)+'\n').encode();(out/'files.json').write_bytes(inventory)
result={'status':'PASS_REMOTE_BLOBS_AND_DECLARED_WORKING_NEWLINE_EQUIVALENCE','revision':revision,
        'base':base,'all_tree_blob_ids_modes_match':True,'independent_fetch_without_alternates':True,
        'raw_remote_blobs_verified':len(rows),'remote_bytes':sum(r['remote_bytes'] for r in rows.values()),
        'working_files_with_newline_only_differences':normalized,'working_raw_identity_claimed_for_all':not normalized,
        'inventory_sha256':hashlib.sha256(inventory).hexdigest(),
        'known_status':'Experimental; GUI18/19 fails exact rest pixels, whole back hair unqualified; not merged to main.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(out),**result},indent=2))
