"""Publish completed source-only preparations and the current review handoff."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
packets={
 'normal_setter_boundary_probe_20261116':'d6c4520ae2a78bc779cb227bb028c5cf2a3b166706da154bc85a1343736e0350',
 'six_foot_domain_json_actual_20261116':'106a087930b62f365a7ae3609123608b3f492af7e892a763ce20666f3da91668',
 'six_foot_domain_json_transport_20261116':'efa55eb23cd69ee7410059c9e01da8414b1b50a454db7bc6ba40a40984120147'}
files=['LLM.md','docs/progress_memo.md','docs/NEXT_SESSION_PLAN_2026-11-16.md','docs/completion_checklist.json','docs/completion_checklist.md',
 'experiments/prepare_neon_windows_20261116.py','experiments/record_neon_review_start_20261116.py','experiments/verify_metadata_remote_20261116.py','experiments/save_review_preparation_20261116.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in packets.items():
    folder=ROOT/'experiments'/name;index=folder/'INDEX.json'
    assert sha(index)==digest
    rows=json.loads(index.read_bytes())['files']
    if isinstance(rows,dict):rows=[{'path':n,**r} for n,r in rows.items()]
    for row in rows:
        p=folder/row['path'];assert p.resolve().is_relative_to(folder) and not p.is_symlink()
        assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    files.extend((folder/row['path']).relative_to(ROOT).as_posix() for row in rows)
    files.append(index.relative_to(ROOT).as_posix())
for name in ('metadata_2ca4b66_remote_20261116','neon_windows_original_20261116'):
    folder=ROOT/'experiments'/name
    files.extend(p.relative_to(ROOT).as_posix() for p in folder.rglob('*') if p.is_file())
assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)==b''
for name in files:
    p=ROOT/name;assert p.suffix in ('.md','.json','.py','.ps1','.gd','.txt','.patch','.log') and '__pycache__' not in p.parts
    assert not name.startswith('output/') and b'\0' not in p.read_bytes();p.read_bytes().decode('utf-8-sig')
subprocess.run(['git','add','--pathspec-from-file=-','--pathspec-file-nul'],cwd=ROOT,input=b'\0'.join(n.encode() for n in sorted(set(files)))+b'\0',check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
changed=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
assert changed.issubset(set(files))
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-q','-m','Prepare isolated Neon Pro Windows review and exact import probes'],cwd=ROOT,check=True)
print(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':len(changed),'branch_application_source_changed':False}))
