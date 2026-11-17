"""AST and pure-result-fixture tests only; never import or run the root driver."""
from pathlib import Path
import ast
from copy import deepcopy
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=(HERE/'run_owned.py').read_text(encoding='utf-8')
tree=ast.parse(source)
checks={}


def mark(name,ok):
    assert name not in checks
    checks[name]=bool(ok)
    assert ok,name


def main():
    compile(tree,str(HERE/'run_owned.py'),'exec')
    mark('python_parse_and_compile_only',True)
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    mark('all_execution_in_main',all(not isinstance(n,(ast.For,ast.While,ast.Try,ast.With)) and
        (not isinstance(n,ast.Expr) or isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)) for n in tree.body))
    mark('main_guard_only',len([n for n in tree.body if isinstance(n,ast.If)])==1 and source.rstrip().endswith('raise SystemExit(main())'))
    env={}
    pure=ast.Module(body=[functions['result_passes']],type_ignores=[])
    exec(compile(ast.fix_missing_locations(pure),'<pure result checker>','exec'),env)
    checker=env['result_passes']
    job={'script_sha256':'script','corpus_sha256':'corpus'}
    raw={f'corpus.fixture_{i}':True for i in range(427)}
    raw.update({'corpus.schema_encode_'+str(i):False for i in range(7)})
    domain={'format':'has_six_foot_gd_domain_result_1','checks':480,'expected_checks':480,'failures':0,
        'complete_assertion_set':True,'named_checks':{'check'+str(i):True for i in range(480)},
        'classification_run':False,'application_import_activation':False,'synthetic_only':True,
        'native_assets_read':False,'job_script_sha256':'script','corpus_sha256':'corpus',
        'comparison_contract':'exact_json_numbers_bounded_cross_type_1','encoder_unchanged':True,
        'raw_corpus_named_checks':raw,'strict_encode_differences':{str(i):[{}] for i in range(7)}}
    mark('accept_correct480_domain_contract',checker(domain,'domain',480,job))
    for field,value in [('format','has_six_foot_domain_result_1'),('checks',444),('expected_checks',444),
            ('failures',1),('complete_assertion_set',False),('classification_run',True),
            ('application_import_activation',True),('synthetic_only',False),('native_assets_read',True),
            ('job_script_sha256','changed'),('corpus_sha256','changed'),('comparison_contract','other'),('encoder_unchanged',False)]:
        mutated=deepcopy(domain);mutated[field]=value
        mark('reject_domain_bad_'+field,not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['named_checks'].pop('check0')
    mark('reject_missing_named_check',not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['named_checks']['check0']=False
    mark('reject_failed_named_check',not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['named_checks']['check0']=1
    mark('reject_truthy_nonboolean_named_check',not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['raw_corpus_named_checks']['corpus.fixture_0']=False
    mark('reject_additional_raw_failure',not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['raw_corpus_named_checks']['corpus.schema_encode_0']=True
    mark('reject_missing_historical_raw_failure',not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['raw_corpus_named_checks']['corpus.fixture_0']=1
    mark('reject_nonboolean_raw_check',not checker(mutated,'domain',480,job))
    mutated=deepcopy(domain);mutated['strict_encode_differences'].pop('0')
    mark('reject_missing_diagnostic_case',not checker(mutated,'domain',480,job))
    boundary={'format':'has_six_foot_boundary_result_1','checks':21,'expected_checks':21,'failures':0,
        'complete_assertion_set':True,'named_checks':{'check'+str(i):True for i in range(21)},
        'classification_run':False,'application_import_activation':False,'owner_native_assets_read':False}
    mark('accept_correct21_boundary_contract',checker(boundary,'boundary',21,job))
    mutated=deepcopy(boundary);mutated['format']='has_six_foot_gd_boundary_result_1'
    mark('reject_wrong_boundary_format',not checker(mutated,'boundary',21,job))
    mutated=deepcopy(boundary);mutated['owner_native_assets_read']=True
    mark('reject_boundary_native_read',not checker(mutated,'boundary',21,job))
    old=ROOT/'experiments/six_foot_domain_actual_20261116/run_owned.py'
    old_sha=hashlib.sha256(old.read_bytes()).hexdigest()
    mark('old_root_runner_preserved',old_sha=='3339fdee26df687cab46d22a95275691dbc26ae35f420f441ce61df65cf86de9')
    packet=ROOT/'experiments/six_foot_domain_json_transport_20261116'
    mark('successor_packet_seal_pinned',hashlib.sha256((packet/'INDEX.json').read_bytes()).hexdigest()=='efa55eb23cd69ee7410059c9e01da8414b1b50a454db7bc6ba40a40984120147')
    mark('successor_script_format_verified','"format":"has_six_foot_gd_domain_result_1"' in (packet/'basis_domain_unit.gd').read_text(encoding='utf-8'))
    boundary_packet=ROOT/'experiments/six_foot_import_basis_gd_candidate_20261116'
    mark('original_boundary_packet_seal_pinned',hashlib.sha256((boundary_packet/'INDEX.json').read_bytes()).hexdigest()=='921579101eb9e97feeb62e8f7b0f22a392fe6536fa8fa9006ecb58650ead7125')
    old_snapshot=json.loads((ROOT/'output/six-foot-domain-20261116-attempt1/SOURCE.json').read_bytes())
    runtime={n:h for n,h in old_snapshot['source_sha256'].items() if not n.startswith('experiments/')}
    digest=hashlib.sha256(json.dumps(runtime,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    mark('exact_original1029_runtime_closure_pin',len(runtime)==1029 and digest=='e13bb105840c76c6114763087746e81281a3e315fd3de2d7f8d94dfc078875c6')
    mark('fresh_attempt2_not_existing',not (ROOT/'output/six-foot-domain-20261116-attempt2').exists())
    mark('domain480_boundary21_fixed',"('domain',PACKET,'basis_domain_unit.gd',480),('boundary',BOUNDARY_PACKET,'basis_boundary_unit.gd',21)" in source)
    mark('sequential_parse_run_fixed',"[('parse',['--check-only']),('run',[])]" in source)
    mark('unchanged_root_job_controls',all(s in source for s in ["'root_closed_all':True","'expires_unix':time.time()+600","'script_sha256':sha(studio/relative)","'corpus_sha256'","runtime_scope=True"]))
    mark('original_and_staged_sources_checked',all(s in source for s in ["SOURCE-BEFORE.json","SOURCE-AFTER.json","source_before==source_after","all(sha(studio/name)==digest for name,digest in sources.items())"]))
    mark('after_closure_in_finally',"finally:" in source and "after=observer.closure(FOLDER,'after')" in source)
    result={'format':'has_six_foot_json_root_source_audit_1','passed':all(checks.values()),'checks':len(checks),
        'named_checks':checks,'driver_sha256':hashlib.sha256((HERE/'run_owned.py').read_bytes()).hexdigest(),
        'actual_engine_execution':False,'actual_cim_inventory':False,'actual_git_call':False,'main_source_edits':False}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'driver_sha256':result['driver_sha256']}))


if __name__=='__main__':main()
