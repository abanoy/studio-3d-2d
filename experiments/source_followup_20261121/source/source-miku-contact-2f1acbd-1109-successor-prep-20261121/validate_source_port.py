"""Read-only Miku port source/AST proof. No candidate imports or native assets."""
from pathlib import Path
import ast,hashlib,json
p=Path(__file__).resolve().parent
old=ast.parse((p/'bases/c315/run_miku_contact_qualification.py').read_text(encoding='utf-8'))
new=ast.parse((p/'run_miku_contact_qualification.py').read_text(encoding='utf-8'))
a={n.name:n for n in old.body if isinstance(n,ast.FunctionDef) and n.name!='main'}
b={n.name:n for n in new.body if isinstance(n,ast.FunctionDef) and n.name!='main'}
assert set(a)==set(b)
for n in a:assert ast.dump(a[n],include_attributes=False)==ast.dump(b[n],include_attributes=False)
old_input=json.loads((p/'bases/c315/INPUT_PINS.json').read_bytes());new_input=json.loads((p/'INPUT_PINS.json').read_bytes())
assert new_input['targets']==old_input['targets'] and len(new_input['targets'])==13
for row in new_input['targets']:
 raw=(p/'payload'/row['path']).read_bytes()
 assert raw==(p/'bases/c315/payload'/row['path']).read_bytes() and len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 assert not (p.parents[1]/row['path']).exists()
base=json.loads((p/'BASELINE_SOURCE1109.json').read_bytes())['files'];assert len(base)==1109
for name,row in base.items():
 root=p.parents[1]/name;data=root.read_bytes()
 assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1']
 assert root.stat().st_mtime_ns==row['main_mtime_ns']
refs=json.loads((p/'LITERAL_ROOT_SOURCE_CLOSURE.json').read_bytes());assert refs['root_dependency_count']==218 and refs['unresolved']==[]
for row in refs['files']:
 assert row['scope']=='current_Main1109' and row['sha256']==base[row['path']]['sha256']
for name in ['source1109.py','full183_validation.py','run_miku_contact_qualification.py']:ast.parse((p/name).read_text(encoding='utf-8'))
print(json.dumps({'status':'SOURCE_STRUCTURE_PASS','unchanged_nonmain_host_functions':len(a),'unchanged_candidate_payloads':13,'literal_current_Main_dependencies':218,'current_Main_rows_raw_Gitblob_ns':1109,'source_AST_files':3,'candidate_programs_executed':False}))
