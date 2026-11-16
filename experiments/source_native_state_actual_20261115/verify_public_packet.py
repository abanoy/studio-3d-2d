"""Independent CPU-only public metadata/source packet verifier; never launches tools."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
SAFE_SUFFIXES = {'.py', '.gd', '.godot', '.json', '.log', '.md', '.patch'}
FORBIDDEN_KEYS = {'pcm', 'vertices', 'positions', 'normals', 'uvs', 'weights', 'joints',
                  'transforms', 'bone_rests', 'rest_matrices', 'bind_matrices',
                  'native_parameters', 'native_jiggle', 'raw_jiggle', 'base64',
                  'buffer', 'buffers', 'points', 'world_points', 'local_points'}
CORRECTED = '008e694dfc3947e9ca3054e6dff14b64e22ee0d1dea3aaf8147df6c9ec0e74fc'
ORIGINAL = '46436bab631d12efdbc40474012234d82b2427a1af51676f5c6deab34dc36140'
DRIVER = '30302f2658183cc9fbca09e8518339dea22accbe064d1d9966fa3233e1392ade'
BACKEND = 'd2c04165587ca3bb0f7b9f474b23dc81902cc78c1aa174d593534f0198f689c0'
RESULT = 'a42cc5de39e6cbaadc5adbdf3811739ef979bc0f37c56c72e369e1f159d3d1e6'
REFUSAL = '8d753bd1248ec61cb92f97891387113eb1aca9d8f6aff9dc0910471ce4ff302a'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(relative):
    return json.loads((HERE / relative).read_bytes())


def privacy(value, location='$'):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key.lower() not in FORBIDDEN_KEYS, (location, key)
            privacy(child, location + '.' + key)
    elif isinstance(value, list):
        # Source file metadata, commands and names are allowed; native numeric
        # vectors, matrices, decoded samples and nested model arrays are not.
        assert not (len(value) >= 3 and all(type(x) in (int, float) for x in value)), location
        for index, child in enumerate(value):
            privacy(child, location + '[' + str(index) + ']')
    elif isinstance(value, str):
        assert len(value) <= 2048, location
        assert not re.search(r'(?:Vector[234]|Transform3D|Packed(?:Float|Vector|Byte))\s*\(', value), location
        assert not value.startswith('data:'), location
    else:
        assert value is None or type(value) in (int, float, bool), location


def iso(value):
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-audit', action='store_true')
    args = parser.parse_args()
    paths = sorted(path for path in HERE.rglob('*') if path.is_file())
    assert all(path.suffix in SAFE_SUFFIXES for path in paths)
    assert all(not path.is_symlink() for path in paths)
    assert not any(part in {'.godot', 'read-only-inputs', 'state-owned-inputs', '.assets'}
                   for path in paths for part in path.relative_to(HERE).parts)
    json_count = 0
    for path in paths:
        if path.suffix == '.json':
            privacy(json.loads(path.read_bytes()), path.relative_to(HERE).as_posix())
            json_count += 1
    aliases = load('PAYLOAD_INDEX.json')['sources']
    assert len(aliases) == len({row['stored'] for row in aliases}) == 48
    for row in aliases:
        relative = Path(row['stored'])
        assert not relative.is_absolute() and '..' not in relative.parts
        stored = HERE / relative
        origin = Path(row['source'])
        # Exact bounded alias paths only; assets cannot be read via this verifier.
        assert stored.suffix in {'.gd', '.py', '.godot', '.json', '.log'}
        assert origin.suffix == stored.suffix
        assert ('/output/source-native-state-' in origin.as_posix() or
                origin.as_posix().endswith('/experiments/native_source_live_port_20261115/run_state_owned.py'))
        assert not any(part in {'read-only-inputs', 'state-owned-inputs', '.assets'} for part in origin.parts)
        raw = stored.read_bytes()
        assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
        assert origin.read_bytes() == raw, row['stored']
    result = load('passed/result.json')
    verification = load('passed/verification.json')
    failed = load('parse-failure/verification.json')
    benchmark = load('BENCHMARK.json')
    assert digest((HERE / 'passed/result.json').read_bytes()) == RESULT == verification['test_result_sha256']
    assert result['checks'] == len(result['named_checks']) == verification['checks_observed'] == benchmark['checks'] == 180
    assert result['failures'] == verification['failures_observed'] == benchmark['failures'] == 0
    assert result['complete_assertion_set'] is True and all(value is True for value in result['named_checks'].values())
    assert verification['passed'] and verification['actual_result_valid']
    assert result['metrics']['actors_loaded'] == benchmark['actual_Model_actors'] == 3
    assert result['metrics']['completed_native_steps'] == benchmark['completed_native_steps'] == 240 + 23 + 3 + 240
    assert result['metrics']['negative_case_count'] == benchmark['negative_cases'] == 23
    assert benchmark['assertion_categories'] == {'load': 15, 'instances': 7, 'negative': 125, 'file': 17, 'wrapper': 12, 'cleanup': 4}
    for category, count in benchmark['assertion_categories'].items():
        assert sum(name.startswith(category + '.') for name in result['named_checks']) == count
    assert result['scope']['private_arrays_serialized'] is False
    assert result['scope']['actual_single_physical_body_only_adversarial_refusal'] is True
    assert result['scope']['same_actor_complete_ragdoll_or_borrowed_primary'] == 'UNQUALIFIED_PARTIAL_SOURCE_RIG'
    assert result['scope']['unchanged_header_size_mtime_body_edit_detection'] == benchmark['excluded_same_header_size_mtime_body_edits'] == 'OUTSIDE_CONTINUOUS_CRYPTOGRAPHIC_GUARANTEE_NOT_TESTED_OR_CLAIMED'
    assert result['scope']['native_rule_index_selected'] == 8 and result['scope']['retained_rules'] == 49
    assert benchmark['native_rules_solved'] == 1
    for field in ('file_header', 'file_length', 'file_mtime'):
        assert benchmark['file_isolation'][field] == result['metrics'][field]
        assert result['metrics'][field]['isolated'] is True and result['metrics'][field]['attempts'] == 1
    assert all(result['cleanup'][name] is True for name in ('owned_copy_hashes_restored', 'passed_input_hashes_preserved'))
    for label, expected_sha, phases in [('passed', CORRECTED, ('parse', 'state')),
                                        ('parse-failure', ORIGINAL, ('parse',))]:
        source = load(label + '/SOURCE.json')
        job = load(label + '/job.json')
        ver = load(label + '/verification.json')
        assert len(source['files']) == len({row['path'] for row in source['files']}) == 204
        assert set(job) == {'format', 'phase', 'folder', 'glb', 'report', 'engine_sha256', 'expected_script_sha256', 'source_manifest_sha256', 'root_closed_all', 'expires_unix'}
        assert job['root_closed_all'] is True
        assert job['expected_script_sha256'] == expected_sha
        assert job['source_manifest_sha256'] == digest((HERE / label / 'SOURCE.json').read_bytes())
        assert all(ver['preservation'].values()) and ver['runtime_lease_released'] is True
        assert [phase['phase'] for phase in ver['phases']] == list(phases)
        for phase in phases:
            process = load(label + '/' + phase + '-process.json')
            command = load(label + '/' + phase + '-command.json')
            assert process['retained_Popen_reaped'] is True and process['timed_out'] is False
            assert process['owned_child_terminated'] is False and process['owned_child_forced_kill'] is False
            assert process['exit'] == (0 if label == 'passed' else 1)
            assert process['passed'] is (label == 'passed')
            assert '--headless' in command and ('--check-only' in command) is (phase == 'parse')
            assert command[command.index('--script') + 1] == 'res://tests/source_native_state_unit.gd'
            assert command[-1] == str(Path(job['folder']) / 'job.json')
        before = load(label + '/before-runtime-closure.json')
        after = load(label + '/after-runtime-closure.json')
        assert before['owned_count'] == after['owned_count'] == 0
        assert iso(before['observed_utc']) <= iso(after['observed_utc']) <= iso(ver['observed_utc'])
        for when in ('before', 'after'):
            process = load(label + '/' + when + '-inventory-process.json')
            assert process['exit'] == 0 and process['retained_Popen_reaped'] is True
            assert json.loads((HERE / label / (when + '-inventory-stdout.log')).read_bytes()) == load(label + '/' + when + '-runtime-closure.json')
    assert failed['passed'] is False and failed['actual_result_valid'] is False
    assert failed['checks_observed'] == 0 and failed['test_result_sha256'] is None
    assert not (HERE / 'parse-failure/result.json').exists()
    assert result['job_sha256'] == digest((HERE / 'passed/job.json').read_bytes())
    assert result['source_manifest_sha256'] == digest((HERE / 'passed/SOURCE.json').read_bytes())
    assert result['test_script_sha256'] == CORRECTED
    source_proof = load('SOURCE_PROOF.json')
    for row in source_proof['passed_frozen_sources']:
        source_map = {x['path']: x for x in load('passed/SOURCE.json')['files']}
        assert row['sha256'] == source_map[row['functional_path']]['sha256']
        assert row['bytes'] == source_map[row['functional_path']]['bytes']
    assert digest((HERE / 'source/passed/src/source_secondary.gd').read_bytes()) == BACKEND
    assert digest((HERE / 'source/run_state_owned.py').read_bytes()) == DRIVER
    original = (HERE / 'source/parse-failure/tests/source_native_state_unit.gd').read_text()
    corrected = (HERE / 'source/passed/tests/source_native_state_unit.gd').read_text()
    assert original.replace('var complete := sims[0].latest.size()', 'var complete: bool = sims[0].latest.size()') == corrected
    refusal = load('preflight/PRECHECK_REFUSAL.json')
    assert digest((HERE / 'preflight/PRECHECK_REFUSAL.json').read_bytes()) == REFUSAL
    assert refusal['engine_launched'] is False and refusal['raw_child_inventory_output_retained'] is False
    assert refusal['not_an_automatic_approval_rejection'] is True
    assert refusal['status'] == 'REFUSED_BEFORE_ENGINE_LAUNCH'
    allowed_error = ('SCRIPT ERROR: Parse Error: Cannot infer the type of "complete" variable because the value doesn\'t have a set type.',
                     '   at: GDScript::reload (res://tests/source_native_state_unit.gd:341)',
                     'ERROR: Failed to load script "res://tests/source_native_state_unit.gd" with error "Parse error".',
                     '   at: load (modules/gdscript/gdscript.cpp:2907)')
    log_count = 0
    for path in paths:
        if path.suffix != '.log':
            continue
        lines = path.read_text().splitlines()
        for line in lines:
            if not line or line.startswith('Godot Engine v4.6.stable.official.89cea1439 - https://godotengine.org'):
                continue
            if line.startswith('PASS source_native_state.'):
                assert line.removeprefix('PASS source_native_state.') in result['named_checks']
            elif line.startswith('SOURCE_NATIVE_STATE '):
                assert json.loads(line.removeprefix('SOURCE_NATIVE_STATE ')) == {'checks': 180, 'complete_assertion_set': True, 'failures': 0}
            elif line.startswith('{'):
                assert set(json.loads(line)) == {'observed_utc', 'owned_count'} and json.loads(line)['owned_count'] == 0
            else:
                assert 'parse-failure' in path.parts and line in allowed_error, (str(path), line[:100])
        if path.name in {'state-engine.log', 'state-stdout.log'}:
            assert len([x for x in lines if x.startswith('PASS source_native_state.')]) == 180
            assert len(set(x for x in lines if x.startswith('PASS source_native_state.'))) == 180
        log_count += 1
    if (HERE / 'INDEX.json').exists():
        index = load('INDEX.json')
        expected = {path.relative_to(HERE).as_posix() for path in paths if path.name != 'INDEX.json'}
        assert set(row['path'] for row in index['files']) == expected
        assert index['files_count'] == len(index['files']) == len(expected)
        assert index['bytes'] == sum(row['bytes'] for row in index['files'])
        for row in index['files']:
            raw = (HERE / row['path']).read_bytes()
            assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
    else:
        assert args.write_audit, 'Final INDEX.json required.'
    audit = {'format': 'has_native8_state_public_packet_audit_1', 'passed': True,
             'source_aliases_exact': len(aliases), 'json_files_privacy_checked': json_count,
             'log_files_line_whitelist_checked': log_count,
             'actual_checks': 180, 'actual_Model_actors': 3, 'native_steps': 506,
             'failed_parse_retained_as_failed': True, 'preflight_exact_root_receipt': True,
             'sensitive_model_media_payloads_copied': False,
             'source_files_manifest': 204, 'all_three_preservation_gates': True,
             'runtime_or_process_queries_executed_by_this_audit': False,
             'continuous_crypto_exclusion_explicit': True, 'same_actor_body_coupling_claimed': False,
             'result_sha256': RESULT, 'preflight_receipt_sha256': REFUSAL,
             'verifier_sha256': digest(Path(__file__).read_bytes())}
    if args.write_audit:
        with (HERE / 'INDEPENDENT_AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(audit, stream, indent=2); stream.write('\n')
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
