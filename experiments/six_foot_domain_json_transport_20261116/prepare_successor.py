"""Prepare an isolated harness-only successor. Never invoke Godot or alter main."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'experiments/six_foot_import_basis_gd_candidate_20261116'
FAILED = ROOT / 'output/six-foot-domain-20261116-attempt1'
OLD_INDEX = '921579101eb9e97feeb62e8f7b0f22a392fe6536fa8fa9006ecb58650ead7125'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def put(name, text):
    (HERE/name).write_text(text, encoding='utf-8', newline='\n')


def main():
    assert sha(OLD/'INDEX.json') == OLD_INDEX
    original = json.loads((OLD/'INDEX.json').read_text(encoding='utf-8'))
    for row in original['files']:
        assert sha(OLD/row['path']) == row['sha256'], row['path']
    for name in ['import_basis_domain.gd', 'PARITY_CORPUS_v3.json']:
        target = HERE/name
        if target.exists():
            assert target.read_bytes() == (OLD/name).read_bytes()
        else:
            shutil.copyfile(OLD/name, target)
    source = (OLD/'basis_domain_unit.gd').read_text(encoding='utf-8')
    source = source.replace('# UNPARSED/UNRUN. Future root-owned headless domain probe; no native assets.',
        '# SUCCESSOR UNPARSED/UNRUN. Exact JSON-number comparison; no native assets.')
    source = source.replace('six_foot_import_basis_gd_candidate_20261116/', HERE.name+'/')
    source = source.replace('var failures := 0', 'var failures := 0\nvar raw_named: Dictionary = {}\nvar strict_encode_differences: Dictionary = {}')
    anchor = 'func checked_job() -> Dictionary:'
    assert source.count(anchor) == 1
    source = source.replace(anchor, (HERE/'comparison_functions.gd.txt').read_text(encoding='utf-8')+'\n'+anchor)
    old = '''\t\tvar ok: bool = actual.has("error") if row.expected.get("error",false) else not actual.has("error")
\t\tif ok and not row.expected.get("error",false):
\t\t\tfor field in row.expected:
\t\t\t\tif actual.get(field) != row.expected[field]: ok = false
\t\tmark("corpus."+row.name,ok)'''
    new = '''\t\tvar raw_ok: bool = actual.has("error") if row.expected.get("error",false) else not actual.has("error")
\t\tvar ok: bool = raw_ok
\t\tif ok and not row.expected.get("error",false):
\t\t\tfor field in row.expected:
\t\t\t\tvar raw_equal: bool = actual.get(field) == row.expected[field]
\t\t\t\tif not raw_equal: raw_ok = false
\t\t\t\tif row.operation == "encode" and field == "document":
\t\t\t\t\tif not json_differences(actual.get(field),row.expected[field],"$.document").is_empty(): ok = false
\t\t\t\t\tif not raw_equal: strict_encode_differences[row.name] = json_differences(actual.get(field),row.expected[field],"$.document",0,false)
\t\t\t\telif not raw_equal: ok = false
\t\traw_named["corpus."+row.name] = raw_ok
\t\tmark("corpus."+row.name,ok)
\trun_comparator_contracts()
\tvar expected_raw_failures: Array = []
\tfor index in range(7):
\t\tvar case_name := "schema_encode_"+str(index)
\t\texpected_raw_failures.append("corpus."+case_name)
\t\tvar differences: Array = strict_encode_differences.get(case_name,[])
\t\tvar proves_numeric_type_only := differences.size() == 1
\t\tif proves_numeric_type_only:
\t\t\tvar delta: Dictionary = differences[0]
\t\t\tproves_numeric_type_only = delta.get("path") == "$.document.schema_version" and delta.get("actual_type") == "int" and delta.get("expected_type") == "float" and delta.get("reason") == "number_representation" and delta.get("exact_numeric_equal") == true and delta.get("actual_number") == 9 and delta.get("expected_number") == 9
\t\tmark("transport.actual_type_only_"+case_name,proves_numeric_type_only)
\tvar raw_failures: Array = []
\tfor name in raw_named:
\t\tif not raw_named[name]: raw_failures.append(name)
\traw_failures.sort(); expected_raw_failures.sort()
\tmark("transport.raw_failure_set_preserved",raw_named.size() == 434 and raw_failures == expected_raw_failures and strict_encode_differences.size() == 7)'''
    assert source.count(old) == 1
    source = source.replace(old, new)
    source = source.replace('"expected_checks":444', '"expected_checks":480')
    source = source.replace('named.size()==444', 'named.size()==480')
    source = source.replace('"named_checks":named,', '"named_checks":named,"raw_corpus_named_checks":raw_named,"strict_encode_differences":strict_encode_differences,"comparison_contract":"exact_json_numbers_bounded_cross_type_1","encoder_unchanged":true,')
    put('basis_domain_unit.gd', source)
    # Keep the original failing evidence intact; copies are exact and synthetic.
    target = HERE/'failed_predecessor'
    target.mkdir(exist_ok=True)
    for name in ['verification.json','domain-run-process.json','domain-run-stdout.log','domain-run-stderr.log','domain-parse-process.json']:
        shutil.copyfile(FAILED/name, target/name)
    shutil.copyfile(FAILED/'Studio/output/domain/result.json', target/'result.json')
    failure = json.loads((target/'result.json').read_text(encoding='utf-8'))
    assert failure['checks'] == 444 and failure['failures'] == 7
    assert sorted(k for k,v in failure['named_checks'].items() if not v) == ['corpus.schema_encode_'+str(i) for i in range(7)]
    pins = {
        'format':'has_six_foot_transport_successor_pins_1',
        'predecessor_packet':str(OLD.relative_to(ROOT)).replace('\\','/'),
        'predecessor_index_sha256':OLD_INDEX,
        'original_failed_root_run':str(FAILED.relative_to(ROOT)).replace('\\','/'),
        'original_failed_result_sha256':sha(target/'result.json'),
        'original_probe_sha256':sha(OLD/'basis_domain_unit.gd'),
        'successor_probe_sha256':sha(HERE/'basis_domain_unit.gd'),
        'domain_sha256':sha(HERE/'import_basis_domain.gd'),
        'corpus_sha256':sha(HERE/'PARITY_CORPUS_v3.json'),
        'domain_bytes_unchanged':(HERE/'import_basis_domain.gd').read_bytes()==(OLD/'import_basis_domain.gd').read_bytes(),
        'corpus_bytes_unchanged':(HERE/'PARITY_CORPUS_v3.json').read_bytes()==(OLD/'PARITY_CORPUS_v3.json').read_bytes(),
        'expected_checks':480,'original_domain_checks_retained':444,
        'comparator_contract_checks':28,'typed_actual_diagnosis_checks':8,
        'godot_successor_parsed':False,'godot_successor_executed':False,
        'main_source_edited':False,'boundary_probe_executed':False,
    }
    put('SOURCE_PINS.json',json.dumps(pins,indent=2)+'\n')
    print(json.dumps(pins,indent=2))


if __name__ == '__main__':
    main()
