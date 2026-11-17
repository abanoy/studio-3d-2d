from pathlib import Path
import base64,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
groups=[('592fe4f82ec0284adaa328228da83feb9abc7814','metadata-checkpoint-592fe4f',['docs/NEXT_SESSION_PLAN_2026-11-16.md','experiments/neon_windows_original_20261116/PREPARATION.json','experiments/normal_setter_boundary_probe_20261116/INDEX.json']),('381d5a974d34eb4dc10208a44c1a54d178c72fbb','neon-candidate-381d5a9',['src/app.gd','src/workspace_layout.gd','tests/verify_neon_workspace.py','tests/verify.py'])]
rows=[]
for commit,prefix,paths in groups:
    for i,path in enumerate(paths):
        response=json.loads((ROOT/f'output/{prefix}-remote-{i}.json').read_bytes())
        raw=base64.b64decode(response['content'])
        expected=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert raw==expected and blob==response['sha']
        rows.append({'commit':commit,'path':path,'remote_git_blob':blob,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'exact_independent_remote_bytes':True})
folder=ROOT/'experiments/neon_checkpoint_remote_readback_20261117';folder.mkdir(exist_ok=False)
record={'format':'has_neon_checkpoint_independent_remote_readback_1','files':rows,'main_redesign_merge_claimed':False,'cleanup_performed':False}
(folder/'REMOTE_READBACK.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'all_remote_bytes_and_blobs_exact':True,'candidate_remains_separate':True}))
