"""Output-only static candidate inventory; no runtime/worker execution."""
from pathlib import Path
import ast,difflib,hashlib,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
baseline=json.loads((BASE/'BASELINE.json').read_bytes())
current=stamp(ROOT/'src/source_import.gd')['sha256']
assert current==baseline['production_before_sha256']==baseline['production_after_sha256']==stamp(BASE/'old-context/source_import.gd')['sha256']
baseline['candidate_sha256']=stamp(BASE/'source/src/source_import.gd')['sha256']
(BASE/'BASELINE.json').write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8')
old=(BASE/'old-context/source_import.gd').read_text(encoding='utf-8').splitlines(keepends=True)
new=(BASE/'source/src/source_import.gd').read_text(encoding='utf-8').splitlines(keepends=True)
(BASE/'candidate.patch').write_text(''.join(difflib.unified_diff(old,new,fromfile='old-context/src/source_import.gd',tofile='source/src/source_import.gd')),encoding='utf-8')
for file in BASE.rglob('*.py'):ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
summary={'format':'has_source_import_owner_unrun_candidate_ready_1','production_source_unchanged':True,'production_sha256':current,'scope':'Routine completion/cancelled completion only; completed-only teardown; live preparers untouched','candidate_source':{p.relative_to(BASE/'source').as_posix():stamp(p) for p in sorted((BASE/'source').rglob('*')) if p.is_file()},'Godot_parse':'UNRUN','headless_process_fixture':'UNRUN_until_canonical_lease_ends','worker_execution':'UNRUN','Python_AST_only':'PASS','planned_fixture_checks_not_actual':44,'actual_fixture_checks':None,'production_docs_HEAD_or_runtime_mutation':False,'native_converter_or_GPU':False,'primary_ownership_reference':'https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/platform/windows/os_windows.cpp#L1449-L1566'}
(BASE/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(BASE).as_posix(),**stamp(p)} for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='INDEX.json']}
assert not any('__pycache__' in p['path'] or p['path'].endswith('.pyc') for p in index['files'])
(BASE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'files':len(index['files']),'bytes':sum(x['bytes'] for x in index['files']),'index_sha256':stamp(BASE/'INDEX.json')['sha256'],'candidate_source':summary['candidate_source'],'execution':'UNRUN'},indent=2))
