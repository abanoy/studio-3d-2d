"""Output-only one-line ownership amendment plus owned negative-exit fixture."""
from pathlib import Path
import ast,difflib,hashlib,json,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
OLD=ROOT/'output/source-import-owner-candidate-20261114'
REVIEW=ROOT/'output/source-import-owner-negative-exit-review-20261114'
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
expected={'old_candidate':(OLD,'f7374de647d6029b02b0d1054fdaeb53f9eb5b3a6120f82c1b9d91eece0414b0'),'sentinel_review':(REVIEW,'6998441afb2f16eee43b93fa5dd9dcf8a482eade92192a16f3ad5509ef92510d')}
for label,(folder,digest) in expected.items():
 assert stamp(folder/'INDEX.json')['sha256']==digest
 index=json.loads((folder/'INDEX.json').read_bytes())
 assert all(stamp(folder/row['path'])=={'bytes':row['bytes'],'sha256':row['sha256']} for row in index['files'])
(BASE/'source').mkdir(exist_ok=False)
shutil.copytree(OLD/'source',BASE/'source',dirs_exist_ok=True)
shutil.copytree(OLD/'source',BASE/'old-context')
path=BASE/'source/src/source_import.gd';original=path.read_bytes()
line=b'\tif OS.get_process_exit_code(owned) == -1: return'
needle=line+b'\r\n' if line+b'\r\n' in original else line+b'\n'
assert original.count(needle)==1
path.write_bytes(original.replace(needle,b''))
assert path.read_bytes()==(BASE/'old-context/src/source_import.gd').read_bytes().replace(needle,b'')

def update(path,edits):
 data=path.read_bytes();newline='\r\n' if b'\r\n' in data else '\n'
 text=data.decode('utf-8').replace('\r\n','\n')
 for old,new in edits:
  assert text.count(old)==1,(old,text.count(old))
  text=text.replace(old,new)
 path.write_bytes(text.replace('\n',newline).encode('utf-8'))
update(BASE/'source/tests/source_import_owner_worker.py',[
 ("choices=('normal','refusal','cancel')","choices=('normal','refusal','cancel','exit_minus_one')"),
 ("code=0 if args.mode=='normal' else 1","code=0 if args.mode=='normal' else (-1 if args.mode=='exit_minus_one' else 1)"),
])
update(BASE/'source/tests/source_import_owner_unit.gd',[
 ('var expected_exit:=0 if mode=="normal" else (2 if mode=="cancel" else 1)',
  'var expected_exit: int={"normal":0,"refusal":1,"cancel":2,"exit_minus_one":-1}[mode]'),
 ('"completed exit remains cached before owner release: "+mode',
  '("controlled negative exit reports the ambiguous -1 sentinel: " if expected_exit==-1 else "completed exit remains cached before owner release: ")+mode'),
 ('check(external_audit.release_calls==1 and external_audit.cached_exit_at_release==[expected_exit] and OS.get_process_exit_code(owned)==-1,"terminal polling releases mapped HANDLE entry before dropping PID: "+mode)',
  'check(external_audit.release_calls==1 and external_audit.cached_exit_at_release==[expected_exit] and external_audit.release_returns.size()==1 and external_audit.release_returns[0] in [OK,FAILED] and OS.get_process_exit_code(owned)==-1,("negative-exit reservation takes the real mapped release once; getter alone is ambiguous: " if expected_exit==-1 else "terminal polling removes the observed cached map entry: ")+mode)'),
 ('"expected_exit":expected_exit,"bypass_base_creator"',
  '"expected_exit":expected_exit,"getter_proves_map_disappearance":expected_exit!=-1 and not bypass,"bypass_base_creator"'),
 ('for mode in ["normal","refusal","cancel"]:await completed_case(mode)',
  'for mode in ["normal","refusal","cancel","exit_minus_one"]:await completed_case(mode)'),
 ('"authored_single_process_Python_only":true,"native_converter_or_GPU":false',
  '"authored_single_process_Python_only":true,"native_converter_or_GPU":false,"negative_exit_getter_limitation":"-1 before and after does not independently prove map disappearance; sole creator/reservation/real release and pinned implementation are required"'),
])
parts=[]
for relative in ('src/source_import.gd','tests/source_import_owner_unit.gd','tests/source_import_owner_worker.py'):
 old=(BASE/'old-context'/relative).read_text(encoding='utf-8').splitlines(keepends=True)
 new=(BASE/'source'/relative).read_text(encoding='utf-8').splitlines(keepends=True)
 parts+=difflib.unified_diff(old,new,fromfile='old-context/'+relative,tofile='source/'+relative)
(BASE/'candidate.patch').write_text(''.join(parts),encoding='utf-8')
for path in BASE.rglob('*.py'):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
production=ROOT/'src/source_import.gd'
prior=json.loads((OLD/'BASELINE.json').read_bytes())
assert stamp(production)['sha256']==prior['production_before_sha256']==prior['production_after_sha256']
value={'format':'has_source_import_owner_negative_exit_amendment_unrun_1','prior_packets':{label:{'path':str(folder),'index_sha256':digest,'verified_unchanged':True} for label,(folder,digest) in expected.items()},'production_unchanged':True,'production_sha256':stamp(production)['sha256'],'product_overlay_change':'Exactly one complete sentinel-guard line removed byte-for-byte; no other SourceImport bytes changed from previous draft','source':{p.relative_to(BASE/'source').as_posix():stamp(p) for p in sorted((BASE/'source').rglob('*')) if p.is_file()},'planned_checks_not_actual':53,'prior_planned_checks':44,'new_owned_exit_minus_one_case_checks':9,'actual_checks':None,'Python_AST':'PASS','Godot_parse':'UNRUN','headless_or_worker_execution':'UNRUN_until_canonical_lease_ends','native_converter_or_GPU':False,'main_docs_HEAD_or_runtime_mutation':False,'negative_exit_proof_limit':'Cached getter -1 is ambiguous; do not claim absence from that value alone.0/1/2 controls establish query transition; exact known-map source and sole reservation support one handle release.'}
(BASE/'SUMMARY.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'source':value['source'],'planned_checks_not_actual':53,'runtime':'UNRUN'},indent=2))
