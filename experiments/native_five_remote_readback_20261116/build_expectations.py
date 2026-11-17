"""Catalogue exact committed blobs for connected-service raw readback."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
COMMIT='52f63c944ded7a651da871524d23a345b606424d'
paths=subprocess.check_output(['git','diff','--name-only','-z',COMMIT+'^',COMMIT],cwd=ROOT).decode().split('\0')[:-1]
oids=[subprocess.check_output(['git','rev-parse',COMMIT+':'+n],cwd=ROOT).decode().strip() for n in paths]
batch=subprocess.check_output(['git','cat-file','--batch'],input=''.join(x+'\n' for x in oids).encode(),cwd=ROOT)
rows=[];offset=0
for name,oid in zip(paths,oids):
    end=batch.index(b'\n',offset);actual,kind,size=batch[offset:end].decode().split();assert actual==oid and kind=='blob'
    start=end+1;stop=start+int(size);body=batch[start:stop];assert batch[stop:stop+1]==b'\n';offset=stop+1
    working=(ROOT/name).read_bytes();recipe='exact' if body==working else 'git_blob_LF_to_CRLF' if body.replace(b'\n',b'\r\n')==working else 'working_differs_from_commit'
    functional=name.split('/')[0] in ('src','tests','tools','data','examples') or name in ('main.tscn','project.godot','run.py','launch.pyw')
    assert not functional or recipe!='working_differs_from_commit'
    rows.append({'ordinal':len(rows),'path':name,'git_blob_sha1':oid,'git_blob_bytes':len(body),'git_blob_sha256':hashlib.sha256(body).hexdigest(),
        'working_recipe':recipe,'working_sha256':hashlib.sha256(working).hexdigest(),'working_bytes':len(working),'functional':functional})
assert offset==len(batch) and len(rows)==757
folder=ROOT/'output/native-five-52f63c9-remote-readback';folder.mkdir()
with (folder/'LOCAL_EXPECTATIONS.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'format':'has_native_five_local_blob_expectations_1','commit':COMMIT,'repository':'abanoy/studio-3d-2d','files':rows},f,indent=2);f.write('\n')
print(json.dumps({'files':len(rows),'bytes':sum(x['git_blob_bytes'] for x in rows),'functional':sum(x['functional'] for x in rows),'expected':str(folder/'LOCAL_EXPECTATIONS.json')}))
