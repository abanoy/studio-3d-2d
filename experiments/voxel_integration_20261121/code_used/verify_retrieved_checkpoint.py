"""Compare a fresh remote checkout with the published primary raw source."""
from pathlib import Path
import argparse, hashlib, json, subprocess, time

p = argparse.ArgumentParser()
p.add_argument('--checkout', type=Path, required=True)
p.add_argument('--revision', required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
fresh = a.checkout.resolve(strict=True)
assert fresh.parent == root.parent and fresh.name.startswith('has-import-info-full-20261121-')
assert (fresh/'.git').is_dir() and not (fresh/'.git/objects/info/alternates').exists()
def git(where, *args):
    return subprocess.check_output(['git', '-c', 'core.autocrlf=false', *args], cwd=where)
assert git(fresh,'remote','get-url','origin').strip() == b'https://github.com/abanoy/studio-3d-2d.git'
assert git(root,'rev-parse','HEAD').decode().strip() == a.revision
assert git(fresh,'rev-parse','HEAD').decode().strip() == a.revision
assert git(fresh,'rev-parse','origin/main').decode().strip() == a.revision
tree = git(root,'rev-parse','HEAD^{tree}').strip()
assert git(fresh,'rev-parse','HEAD^{tree}').strip() == tree
def inventory(where):
    result = {}
    for row in git(where,'ls-tree','-r','-z','HEAD').split(b'\0'):
        if not row: continue
        meta, name = row.split(b'\t',1)
        mode, kind, oid = meta.split()
        assert kind == b'blob'
        result[name.decode()] = {'mode':mode.decode(), 'blob':oid.decode()}
    return result
local, remote = inventory(root), inventory(fresh)
assert local == remote
base = 'cdc86f3b85491709774b1d88eca470869ef09482'
changed = {s.decode() for s in git(root,'diff','--name-only','-z',base,'HEAD').split(b'\0') if s}
trees = {'src','tools','tests','data','examples'}
tops = {'project.godot','main.tscn','run.py','launch.pyw','dependencies.json'}
functional = {n for n in local if (n.split('/')[0] in trees or n in tops) and not n.endswith('.pyc') and '__pycache__' not in n.split('/')}
rows = {}
for name in sorted(changed | functional):
    assert name in local, ('Deletion needs explicit verification', name)
    before, after = (root/name).read_bytes(), (fresh/name).read_bytes()
    assert before == after, name
    blob = hashlib.sha1(b'blob '+str(len(after)).encode()+b'\0'+after).hexdigest()
    assert blob == remote[name]['blob'], name
    rows[name] = {**remote[name], 'sha256':hashlib.sha256(after).hexdigest(), 'bytes':len(after)}
folder=root/'output'/('integrated-remote-verification-'+str(time.time_ns()))
folder.mkdir()
raw=(json.dumps(rows,indent=2,ensure_ascii=True)+'\n').encode()
(folder/'files.json').write_bytes(raw)
receipt={'format':'has_integrated_independent_remote_verification_1','status':'PASS',
    'revision':a.revision,'tree':tree.decode(),'base':base,'fresh_remote_checkout':str(fresh),
    'independent_git_store':True,'alternates_used':False,'all_tree_blob_ids_and_modes_match':True,
    'tree_files':len(local),'changed_files':len(changed),'functional_paths':len(functional),
    'verified_raw_files':len(rows),'verified_raw_bytes':sum(x['bytes'] for x in rows.values()),
    'inventory_sha256':hashlib.sha256(raw).hexdigest()}
(folder/'verification.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps({'folder':str(folder),**receipt},indent=2))
