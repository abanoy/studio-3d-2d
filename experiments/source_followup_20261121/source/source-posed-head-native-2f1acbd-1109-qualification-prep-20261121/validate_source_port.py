from pathlib import Path
import ast,hashlib,json
p=Path(__file__).resolve().parent
original=ast.parse((p/'POSTFLIGHT_SOURCE_REFERENCE.py').read_text(encoding='utf-8'))
ported=ast.parse((p/'full183_validation.py').read_text(encoding='utf-8'))
validate=next(n for n in ported.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
def assigns(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
start=next(i for i,n in enumerate(original.body) if assigns(n,'completion'))
end=next(i for i,n in enumerate(original.body) if assigns(n,'target'))
body=original.body[start:end]
portstart=next(i for i,n in enumerate(validate.body) if assigns(n,'completion'))
actual=validate.body[portstart:portstart+len(body)]
assert ast.dump(ast.Module(body=body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=actual,type_ignores=[]),include_attributes=False)
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('write_text','write_bytes','open','mkdir','unlink','remove','replace') for n in ast.walk(validate))
for name in ('source1109.py','run_posed_head_controls.py','full183_validation.py'):ast.parse((p/name).read_text(encoding='utf-8'))
base=json.loads((p/'BASELINE_SOURCE1109.json').read_bytes());catalogue=json.loads((p/'IMPORT_INFO_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').read_bytes())
assert len(base['files'])==len(catalogue)==1109
for n,row in base['files'].items():
 assert row['main_mtime_ns']==catalogue[n]['mtime_ns'] and type(row['main_mtime_ns']) is int
 assert all(row[k]==catalogue[n][k] for k in ('bytes','sha256','git_sha1'))
for n,row in base['files'].items():
 raw=(p.parents[1]/n).read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_sha1']
 assert (p.parents[1]/n).stat().st_mtime_ns==row['main_mtime_ns']
print(json.dumps({'status':'SOURCE_STRUCTURE_PASS','postflight_body_AST_statements_preserved':len(body),'baseline_integer_ns_rows_preserved':1109,'ported_files_AST_parsed':3,'candidate_programs_executed':False}))
