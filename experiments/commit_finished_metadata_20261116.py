"""Root checkpoint: validate and stage only the reviewed completed metadata list."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'output/metadata-checkpoint-20261116-manifest.json').read_bytes())
rows=manifest['files']
assert len(rows)==699
existing=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().strip('\0').split('\0'))-{''}
assert existing.issubset({r['path'] for r in rows})
for row in rows:
    p=ROOT/row['path']
    assert p.resolve().is_relative_to(ROOT) and not p.is_symlink()
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'] and p.stat().st_size==row['bytes']
    assert not row['path'].startswith('output/') and '__pycache__' not in p.parts
names=[r['path'] for r in rows]
subprocess.run(['git','add','-f','--pathspec-from-file=-','--pathspec-file-nul'],cwd=ROOT,input=b'\0'.join(n.encode() for n in names)+b'\0',check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
actual=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
actual={n for n in actual if n}
assert actual.issubset(set(names))
assert len(actual)>650 and all(not n.startswith('output/') and '__pycache__' not in Path(n).parts for n in actual)
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-q','-m','Record complete Windows native-hair verification and import diagnostics'],cwd=ROOT,check=True)
print(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'staged_changed_files':len(actual),'reviewed_catalogue_files':len(rows),'private_outputs_staged':False}))
