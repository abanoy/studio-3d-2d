"""Verify connected GitHub raw responses against immutable local blob expectations."""
from pathlib import Path
import base64, datetime, hashlib, json

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/native_source_live_port_20261115/remote_dbf0bc1'
RAW=ROOT/'output/github-readback-dbf0bc1'
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
expect=load(PACKET/'LOCAL_EXPECTATIONS.json')
by_name={x['path']:x for x in expect['files']}
old=[x for p in sorted(PACKET.glob('batch-*.json')) for x in load(p)['files']]
assert len(old)==54 and len({x['path'] for x in old})==54 and all(x['passed'] for x in old)
new=[]
for p in sorted(RAW.glob('*.json')):
    r=load(p);x=by_name[r['path']];s=r['response']
    assert r['repository']==expect['repository'] and r['commit']==expect['commit'] and s['encoding']=='base64'
    data=base64.b64decode(''.join(s['content'].split()),validate=True)
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    sha=hashlib.sha256(data).hexdigest()
    assert blob==s['sha']==x['git_blob_sha1'] and sha==x['git_blob_sha256'] and len(data)==x['git_blob_bytes'],x['path']
    recipe=x['working_recipe']
    restored=data.replace(b'\n',b'\r\n') if recipe=='git_blob_LF_to_CRLF' else data
    reconstruct=not x['functional'] or (hashlib.sha256(restored).hexdigest()==x['working_sha256'] and len(restored)==x['working_bytes'])
    assert reconstruct,x['path']
    new.append({'path':x['path'],'change':x['change'],'remote_ref':r['commit'],
        'remote_git_blob_sha1':blob,'service_git_blob_sha1':s['sha'],'local_git_blob_sha1':x['git_blob_sha1'],
        'remote_bytes':len(data),'remote_sha256':sha,'local_git_blob_sha256':x['git_blob_sha256'],
        'remote_equals_exact_local_git_blob':True,'working_recipe':recipe,'working_sha256':x['working_sha256'],
        'functional':x['functional'],'functional_working_bytes_reconstruct':reconstruct,
        'display_url':s['display_url'],'fetch_attempts':1,'passed':True,'observed_utc':r['observed_utc']})
assert len(new)==151
all_rows=old+new
assert len(all_rows)==205 and len({x['path'] for x in all_rows})==205 and {x['path'] for x in all_rows}==set(by_name)
for n,start in enumerate(range(0,len(new),6),9):
    save(PACKET/f'batch-{n:03d}.json',{'format':'has_exact_commit_connected_GitHub_readback_batch_1','repository':expect['repository'],
        'commit':expect['commit'],'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'batch':n,'files':new[start:start+6]})
summary={'format':'has_complete_exact_commit_connected_github_readback_1','repository':expect['repository'],'commit':expect['commit'],
    'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':205,'exact_bytes_and_git_sha1_and_sha256':205,
    'functional_files':sum(x['functional'] for x in all_rows),'functional_working_bytes_reconstruct':True,
    'current_working_tree_equals_old_commit_claimed':False,'all_raw_changed_files_read_back':True,'cleanup_performed':False,
    'scope':'Old immutable dbf commit only; later working changes require their own checkpoint/readback. No raw base64 is published.'}
save(PACKET/'COMPLETE.json',summary)
print(json.dumps(summary))
