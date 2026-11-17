"""Verify three independently fetched published progress files by raw bytes."""
from pathlib import Path
import base64,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
paths=['docs/benchmarks/native_five_full_2026-11-16.json','docs/benchmarks/native_five_owner_review_2026-11-16.json','docs/NEXT_SESSION_PLAN_2026-11-16.md']
rows=[]
for i,path in enumerate(paths):
    value=json.loads((ROOT/f'output/metadata-checkpoint-2ca4b66-remote-{i}.json').read_bytes())
    raw=base64.b64decode(value['content']);local=(ROOT/path).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert raw==local and blob==value['sha']
    rows.append({'path':path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'remote_git_blob':blob,'exact_remote_bytes':True})
folder=ROOT/'experiments/metadata_2ca4b66_remote_20261116';folder.mkdir(exist_ok=False)
record={'format':'has_published_metadata_remote_readback_1','commit':'2ca4b663edf17eb7837c7166a8f3db602df58ec6','source_functional_commit':'52f63c944ded7a651da871524d23a345b606424d','files':rows,'cleanup_performed':False}
(folder/'REMOTE_READBACK.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
