"""Verify actual connected-service raw file bytes; never infer full product acceptance."""
from pathlib import Path
import base64,datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'output/native-five-52f63c9-remote-readback'
def load(p):return json.loads(p.read_bytes())
expect=load(FOLDER/'LOCAL_EXPECTATIONS.json');rows=[]
for x in expect['files']:
    p=FOLDER/'raw'/f"{x['ordinal']:03d}.json";r=load(p);s=r['response']
    assert r['path']==x['path'] and r['commit']==expect['commit'] and s['sha']==x['git_blob_sha1']
    assert r['service_file_metadata_confirmed'] is True
    if s['encoding']=='base64':body=base64.b64decode(''.join(s['content'].split()),validate=True)
    else:assert s['encoding']=='utf-8';body=s['content'].encode('utf-8')
    digest=hashlib.sha256(body).hexdigest();blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    assert digest==x['git_blob_sha256'] and blob==x['git_blob_sha1'] and len(body)==x['git_blob_bytes'],x['path']
    restored=body.replace(b'\n',b'\r\n') if x['working_recipe']=='git_blob_LF_to_CRLF' else body
    reconstruct=hashlib.sha256(restored).hexdigest()==x['working_sha256'] and len(restored)==x['working_bytes']
    assert not x['functional'] or reconstruct,x['path']
    rows.append({'path':x['path'],'git_blob_sha1':blob,'sha256':digest,'bytes':len(body),'remote_ref':expect['commit'],
        'display_url':s['display_url'],'functional':x['functional'],'working_recipe':x['working_recipe'],
        'functional_working_bytes_reconstruct':not x['functional'] or reconstruct,'fetch_attempts':r['fetch_attempts'],
        'large_text_blob_fallback':r.get('large_text_blob_fallback',False),'observed_utc':r['observed_utc'],'passed':True})
assert len(rows)==757 and len({x['path'] for x in rows})==757
packet=ROOT/'experiments/native_five_remote_readback_20261116'
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
for i,start in enumerate(range(0,len(rows),12)):
    save(packet/f'batch-{i:03d}.json',{'format':'has_native_five_exact_remote_batch_1','repository':expect['repository'],'commit':expect['commit'],'files':rows[start:start+12]})
summary={'format':'has_native_five_complete_remote_readback_1','repository':expect['repository'],'commit':expect['commit'],
    'passed':True,'files':757,'exact_raw_bytes_git_sha1_sha256':757,'raw_bytes':sum(x['bytes'] for x in rows),
    'functional_files':sum(x['functional'] for x in rows),'functional_working_bytes_reconstruct':True,
    'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'product_full_test_pass_claimed':False,
    'cleanup_performed':False,'scope':'Exact immutable checkpoint. Uncommitted future work is separate; no private source assets were uploaded.'}
save(packet/'COMPLETE.json',summary)
save(packet/'LOCAL_EXPECTATIONS.json',expect)
print(json.dumps(summary))
