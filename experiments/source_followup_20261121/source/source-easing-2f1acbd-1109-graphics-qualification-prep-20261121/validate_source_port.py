"""Read-only AST/byte/source-anchor verification; no candidate imports."""
from pathlib import Path
import ast,hashlib,json
p=Path(__file__).resolve().parent
old=ast.parse((p/'bases/c315/run_easing_graphics.py').read_text(encoding='utf-8'))
new=ast.parse((p/'run_easing_graphics.py').read_text(encoding='utf-8'))
old_funcs={n.name:n for n in old.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name!='main'}
new_funcs={n.name:n for n in new.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name!='main'}
assert set(old_funcs)==set(new_funcs)
for n in old_funcs:assert ast.dump(old_funcs[n],include_attributes=False)==ast.dump(new_funcs[n],include_attributes=False)
old_inputs=json.loads((p/'bases/c315/INPUT_PINS.json').read_bytes());inputs=json.loads((p/'INPUT_PINS.json').read_bytes())
assert inputs['targets']==old_inputs['targets'] and len(inputs['targets'])==7
for row in inputs['targets']:
 a=(p/'candidate/payload'/row['path']).read_bytes();b=(p/'bases/c315/candidate/payload'/row['path']).read_bytes()
 assert a==b and len(a)==row['bytes'] and hashlib.sha256(a).hexdigest()==row['sha256']
for n in ['source1109.py','full183_validation.py','run_easing_graphics.py']:ast.parse((p/n).read_text(encoding='utf-8'))
base=json.loads((p/'candidate/BASE_FUNCTIONAL_SOURCE.json').read_bytes())
patches=json.loads((p/'candidate/PATCHES.json').read_bytes())['patches']
for n in ['src/app.gd','src/renderer.gd']:
 data=(p.parents[1]/n).read_bytes();assert len(data)==base[n]['bytes'] and hashlib.sha256(data).hexdigest()==base[n]['sha256']
 text=data.decode('utf-8')
 for row in patches:
  if row['path']==n:assert text.count(row['before'])==1;text=text.replace(row['before'],row['after'])
 assert text.encode()==(p/'candidate/payload'/n).read_bytes()
print(json.dumps({'status':'SOURCE_STRUCTURE_PASS','unchanged_nonmain_host_functions':len(old_funcs),'unchanged_GDS_payloads':7,'current_base_anchor_replays':2,'candidate_programs_executed':False,'AST_only_files':3}))
