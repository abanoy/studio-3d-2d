"""Freeze amended source and exact authored CPU evidence only."""
from pathlib import Path
import difflib,hashlib,json
BASE=Path(__file__).resolve().parent
baseline=json.loads((BASE/'BASELINE.json').read_bytes())
OLD=Path(baseline['old_candidate'])
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
after={name:stamp(OLD/name)['sha256'] for name in baseline['old_context_sha256']}
copies={name:stamp(BASE/'old-context'/name)['sha256'] for name in baseline['old_context_sha256']}
assert after==copies==baseline['old_context_sha256']
for name in ('source_jiggle_values.py','authored_fixture.py'):
 assert stamp(BASE/'source'/name)==stamp(OLD/name)
pieces=[]
for name in ('source_jiggle_metadata.py','test_source_jiggle_metadata.py'):
 pieces += difflib.unified_diff((BASE/'old-context'/name).read_text(encoding='utf-8').splitlines(keepends=True),(BASE/'source'/name).read_text(encoding='utf-8').splitlines(keepends=True),fromfile='old-context/'+name,tofile='source/'+name)
(BASE/'candidate.patch').write_text(''.join(pieces),encoding='utf-8')
reports=sorted(BASE.glob('cpu-launch-*/verification.json'))
assert len(reports)==1
actual=json.loads(reports[0].read_bytes());assert actual['passed'] and actual['report']['checks']==25 and actual['report']['failures']==actual['report']['errors']==0
summary={'format':'has_jiggle_minimal_three_refusal_amendment_ready_1','production_or_Git_mutation':False,'source_context':'output-only amendment to historical saved minimal plan','new_signature':'plan_report(base_report, inspection, newline="\\n", *, expected_native_mdl_sha256=None)','bridge_seam4':'plan_report(report, inspection, newline=os.linesep, expected_native_mdl_sha256=frozen_native_sha)','expected_context_source':'Independently frozen staged selected-MDL bytes/SHA/size/nsmtime from before SourceIO, rechecked before publication; never copied from metadata','old_context_before':baseline['old_context_sha256'],'old_context_after':after,'new_source':{p.name:stamp(p) for p in sorted((BASE/'source').glob('*.py'))},'CPU_report':str(reports[0].relative_to(BASE)),'checks':25,'original_tests_API_updated':22,'new_refusal_test_methods':3,'failures':0,'errors':0,'source_unchanged_during_CPU':True,'runtime_import_or_launch':False,'native_Junko_full_report_fit_adoption_save':'UNRUN','no_rule_BSP_bytes_and_128KiB_256KiB_1MiB_contracts':'unchanged'}
(BASE/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(BASE).as_posix(),**stamp(p)} for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='INDEX.json']}
assert not any('__pycache__' in p['path'] or p['path'].endswith('.pyc') for p in index['files'])
(BASE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'files':len(index['files']),'bytes':sum(p['bytes'] for p in index['files']),'index_sha256':stamp(BASE/'INDEX.json')['sha256'],'new_source':summary['new_source']},indent=2))
