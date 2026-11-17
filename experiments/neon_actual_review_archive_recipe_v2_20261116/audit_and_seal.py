"""Audit the recipe and known inputs without importing/running its builder."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    plan=json.loads((HERE/'INPUTS.json').read_bytes())
    checks={}
    def mark(name,ok):
        assert name not in checks
        checks[name]=bool(ok)
        assert ok,name
    source=(HERE/'build_archive.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    compile(tree,str(HERE/'build_archive.py'),'exec')
    mark('builder_parsed_compiled_without_execution',True)
    imports={alias.name for node in tree.body if isinstance(node,ast.Import) for alias in node.names}
    mark('no_process_network_or_Git_modules',imports=={'argparse','gzip','hashlib','json'})
    mark('builder_guarded_main',source.rstrip().endswith('if __name__==\'__main__\':main()'))
    mark('exact217_known_files',len(plan['files'])==217)
    mark('all_destinations_unique',len({row['archive_path'] for row in plan['files']})==217)
    for row in plan['files']:
        path=Path(plan['roots'][row['root']])/row['path']
        mark('exact_input.'+row['archive_path'],path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'])
    selected=[row['path'] for row in plan['files']]
    mark('all_selected_inputs_text_scalar_only',all(Path(path).suffix in {'.json','.log','.gd','.py','.ps1','.md','.patch'} for path in selected))
    mark('all24_original_receipts_selected',sum(row['archive_path'].startswith('original-full/receipts/') for row in plan['files'])==24)
    mark('original28_2_raw_report_preserved',any(row['archive_path']=='original-full/object-timing-original-result.json' and row['sha256']=='df40715344819ab69260e7909c8189010e636d8db1447903ffe0b6dc7bb5ec0a' for row in plan['files']))
    mark('v3_actual_no_longer_pending',plan['v3_pending'] is False and plan['v3_focused_checks']==32 and plan['v3_focused_failures']==0)
    mark('corrected_full_explicit_pending',plan['corrected_full_suite_pending'] is True and 'PENDING_SEPARATE_EXECUTION' in source)
    mark('old_failures_separate_from_later_success',all(name in {case['name'] for case in plan['cases']} for name in ['original-full','original-behavior','candidate-v1','diagnostic-only','fixture-v2','boundary-v3']))
    mark('gzip_preserves_exact_originals','gzip.decompress(body)==raw' in source and "assert sha(raw)==row['sha256']" in source)
    mark('never_reuses_output','not output.exists()' in source and 'output.mkdir(exist_ok=False)' in source)
    mark('complete_recipe_index_validated_and_copied',"for row in recipe_index['files']:" in source and "for name,data in recipe_payloads:" in source and source.index('recipe_index=json.loads')<source.index('output.mkdir(exist_ok=False)'))
    result={'format':'has_neon_actual_archive_recipe_source_audit_1','passed':all(checks.values()),'checks':len(checks),
        'named_checks':checks,'builder_executed':False,'archive_created':False,'engine_CIM_or_Git_executed':False}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    rows=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert path.suffix in {'.json','.py','.md'} and '__pycache__' not in path.parts
        rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':rows,'file_count':len(rows),'bytes':sum(row['bytes'] for row in rows),
        'excludes':['INDEX.json'],'builder_execution_claimed':False,'actual_archive_created':False,'owner_art_or_native_arrays_included':False}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'builder_sha256':sha(HERE/'build_archive.py'),
        'inputs_sha256':sha(HERE/'INPUTS.json'),'source_checks':len(checks),'files':len(rows),'bytes':index['bytes'],'builder_executed':False}))


if __name__=='__main__':main()
