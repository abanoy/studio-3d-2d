from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
index=json.loads((root/'INDEX.json').read_bytes())
rows=index['files']
assert len({r['path'] for r in rows})==len(rows)
assert {r['path'] for r in rows}=={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='INDEX.json'}
for row in rows:
 p=root/row['path'];b=p.read_bytes()
 assert p.resolve().is_relative_to(root.resolve()) and len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
print('PASS375 source/context packet files='+str(len(rows)))
