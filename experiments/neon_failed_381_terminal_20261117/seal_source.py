"""Source-only parse and protocol checks; do not import the terminal/CIM helper."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    source=(HERE/'close_failed.py').read_text(encoding='utf-8')
    compile(ast.parse(source),str(HERE/'close_failed.py'),'exec')
    context=json.loads((HERE/'CONTEXT.json').read_bytes())
    checks={
        'source_parse_and_compile_only':True,
        'exact_381_commit':context['commit']=='381d5a974d34eb4dc10208a44c1a54d178c72fbb',
        'root_observed_terminal_before_preparation':context['terminal_observed_by_root_before_preparation'] is True,
        'source1028_before_process_query':'len(before[\'source_sha256\'])==1028' in source and source.index('state,before,failed_report=terminal()')<source.index('observed=observe()'),
        'actual_nested_birth_schema':'has_root_neon_corrected_birth_observation_1' in source and "birth['python']['parent_pid']==6012" in source,
        'PID_reuse_compares_creation_not_number_only':'[DateTimeOffset]::Parse($now) -ne [DateTimeOffset]::Parse($pin.birth)' in source,
        'no_termination_API':all(text not in source for text in ['.kill(','.terminate(','Stop-Process','taskkill']),
        'two_runtime_scopes_checked':'has-neon-review-20261116-c2d52ff' in source and 'has-acceptance-session-20261111' in source,
        'fresh_root_and_nested_references_not_recursive_art_tree':"(OUTPUT/'private-desktop').glob('*.json')" in source and "('file'" not in source and "for pattern in ('*-verification.json','*-result.json')" in source,
        'known_Krita_source_cancellation_join':"cancelled_receipt" in source and "registered_Krita_cancel_exit2" in source,
        'failed_animated_assertion_join':"registered_animated_assertion_exit1" in source and "report['checks']==47 and report['failures']==1" in source,
        'stale_full_report_not_used':"load(OUTPUT/'verification.json')" not in source and "'final_full_report_used':False" in source,
        'full_PASS_never_inferred':"'full_suite_passed':False" in source,
        'second_observation_before_release':"second=observe()" in source and source.index('second=observe()')<source.index("save(RUN/'graphics-lease-closed-after-failure.json'"),
        'fresh_outputs_only':"out.mkdir(exist_ok=False)" in source and "path.open('x'" in source,
    }
    assert all(checks.values()),[name for name,ok in checks.items() if not ok]
    audit={'format':'has_neon_failed_381_terminal_source_audit_1','passed':True,'checks':len(checks),'named_checks':checks,
        'helper_imported_or_executed':False,'CIM_engine_or_Git_executed':False,'driver_sha256':sha(HERE/'close_failed.py')}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    files=[{'path':path.name,'bytes':path.stat().st_size,'sha256':sha(path)} for path in sorted(HERE.iterdir()) if path.is_file()]
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':files,'file_count':len(files),'bytes':sum(row['bytes'] for row in files),
        'excludes':['INDEX.json'],'actual_closure_or_release_performed':False,'no_native_arrays_or_artwork_included':True}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'helper_sha256':sha(HERE/'close_failed.py'),'context_sha256':sha(HERE/'CONTEXT.json'),'source_checks':len(checks),'executed':False}))


if __name__=='__main__':main()
