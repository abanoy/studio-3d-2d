"""Completed native-state source/metadata archive only. Never reads native assets."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PASS = ROOT / 'output/source-native-state-20261116T020227823185'
FAILED = ROOT / 'output/source-native-state-20261116T020159138961'
PREFLIGHT = ROOT / 'output/source-native-state-20261116T020126056307'
SCRIPT = 'tests/source_native_state_unit.gd'
CORRECTED = '008e694dfc3947e9ca3054e6dff14b64e22ee0d1dea3aaf8147df6c9ec0e74fc'
ORIGINAL = '46436bab631d12efdbc40474012234d82b2427a1af51676f5c6deab34dc36140'
SOURCES = ['src/source_secondary.gd', 'src/source_jiggle_math.gd', 'src/secondary_live.gd',
           'src/source_bone_bindings.gd', 'src/model.gd', 'project.godot', SCRIPT]
SAFE = ['SOURCE.json', 'job.json', 'verification.json',
        'before-inventory-process.json', 'before-inventory-stderr.log', 'before-inventory-stdout.log',
        'before-runtime-closure.json', 'after-inventory-process.json', 'after-inventory-stderr.log',
        'after-inventory-stdout.log', 'after-runtime-closure.json',
        'parse-command.json', 'parse-process.json', 'parse-engine.log', 'parse-stderr.log', 'parse-stdout.log']
ALIASES = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def copy(source, relative):
    assert source.suffix in ('.gd', '.py', '.godot', '.json', '.log')
    raw = source.read_bytes()
    target = HERE / relative
    assert target.is_relative_to(HERE) and '..' not in Path(relative).parts and not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    assert target.read_bytes() == raw
    row = {'source': str(source), 'stored': relative, 'bytes': len(raw), 'sha256': sha(raw)}
    ALIASES.append(row)
    return row


def main():
    verification = load(PASS / 'verification.json')
    result = load(PASS / 'result.json')
    assert verification['passed'] and verification['actual_result_valid']
    assert verification['checks_observed'] == result['checks'] == len(result['named_checks']) == 180
    assert result['failures'] == verification['failures_observed'] == 0
    assert result['complete_assertion_set'] and all(result['named_checks'].values())
    assert all(verification['preservation'].values()) and verification['runtime_lease_released']
    assert verification['test_result_sha256'] == sha((PASS / 'result.json').read_bytes())
    assert result['test_script_sha256'] == CORRECTED
    assert result['job_sha256'] == sha((PASS / 'job.json').read_bytes())
    assert result['source_manifest_sha256'] == sha((PASS / 'SOURCE.json').read_bytes())
    assert result['metrics']['actors_loaded'] == 3 and result['metrics']['completed_native_steps'] == 506
    assert result['metrics']['negative_case_count'] == 23 and result['metrics']['planned_assertions'] == 180
    assert result['cleanup']['owned_copy_hashes_restored'] and result['cleanup']['passed_input_hashes_preserved']
    assert result['scope']['private_arrays_serialized'] is False and result['scope']['GPU_or_GUI'] is False
    assert result['scope']['actual_single_physical_body_only_adversarial_refusal'] is True
    assert result['scope']['same_actor_complete_ragdoll_or_borrowed_primary'] == 'UNQUALIFIED_PARTIAL_SOURCE_RIG'
    excluded = 'OUTSIDE_CONTINUOUS_CRYPTOGRAPHIC_GUARANTEE_NOT_TESTED_OR_CLAIMED'
    assert result['scope']['unchanged_header_size_mtime_body_edit_detection'] == excluded
    categories = {prefix: sum(name.startswith(prefix + '.') for name in result['named_checks'])
                  for prefix in ('load', 'instances', 'negative', 'file', 'wrapper', 'cleanup')}
    assert categories == {'load': 15, 'instances': 7, 'negative': 125, 'file': 17, 'wrapper': 12, 'cleanup': 4}
    assert sum(categories.values()) == 180
    assert result['metrics']['file_header'] == {'attempts': 1, 'isolated': True, 'length_unchanged': True, 'mtime_unchanged': True}
    assert result['metrics']['file_length'] == {'attempts': 1, 'isolated': True, 'length_unchanged': False, 'mtime_unchanged': True}
    assert result['metrics']['file_mtime'] == {'attempts': 1, 'isolated': True, 'length_unchanged': True, 'mtime_unchanged': False}
    for folder, label, script_sha, phases in [(PASS, 'passed', CORRECTED, ('parse', 'state')),
                                               (FAILED, 'parse-failure', ORIGINAL, ('parse',))]:
        source = load(folder / 'SOURCE.json')
        job = load(folder / 'job.json')
        assert len(source['files']) == 204
        assert job['expected_script_sha256'] == script_sha and job['source_manifest_sha256'] == sha((folder / 'SOURCE.json').read_bytes())
        assert job['root_closed_all'] is True and job['format'] == 'has_source_native_state_job_1'
        assert sha((folder / 'Studio' / SCRIPT).read_bytes()) == script_sha
        assert len(job) == 10  # Exact safe lease metadata; no parser/native arrays.
        for filename in SAFE:
            copy(folder / filename, label + '/' + filename)
        if label == 'passed':
            for filename in ['state-command.json', 'state-process.json', 'state-engine.log',
                             'state-stderr.log', 'state-stdout.log', 'result.json']:
                copy(folder / filename, label + '/' + filename)
        for phase in phases:
            process = load(folder / (phase + '-process.json'))
            command = load(folder / (phase + '-command.json'))
            assert process['retained_Popen_reaped'] and not process['timed_out']
            assert not process['owned_child_terminated'] and not process['owned_child_forced_kill']
            assert '--headless' in command and command[command.index('--script') + 1] == 'res://' + SCRIPT
            assert Path(command[command.index('--path') + 1]) == folder / 'Studio'
            assert Path(command[-1]) == folder / 'job.json'
            assert ('--check-only' in command) is (phase == 'parse')
            if label == 'passed':
                assert process['passed'] and process['exit'] == 0 and not process['error_markers']
            else:
                assert process['passed'] is False and process['exit'] == 1 and process['error_markers']
        for when in ('before', 'after'):
            assert load(folder / (when + '-runtime-closure.json'))['owned_count'] == 0
            assert load(folder / (when + '-inventory-process.json'))['retained_Popen_reaped']
            assert load(folder / (when + '-inventory-process.json'))['exit'] == 0
    failed_verification = load(FAILED / 'verification.json')
    assert failed_verification['passed'] is False and failed_verification['actual_result_valid'] is False
    assert failed_verification['checks_observed'] == 0 and failed_verification['test_result_sha256'] is None
    assert len(failed_verification['phases']) == 1 and not (FAILED / 'result.json').exists()
    source_map = {row['path']: row for row in load(PASS / 'SOURCE.json')['files']}
    source_rows = []
    for name in SOURCES:
        path = PASS / 'Studio' / name
        raw = path.read_bytes()
        assert sha(raw) == source_map[name]['sha256'] and len(raw) == source_map[name]['bytes']
        row = copy(path, 'source/passed/' + name)
        row['functional_path'] = name
        source_rows.append(row)
    failed_source = copy(FAILED / 'Studio' / SCRIPT, 'source/parse-failure/' + SCRIPT)
    original = (FAILED / 'Studio' / SCRIPT).read_text()
    corrected = (PASS / 'Studio' / SCRIPT).read_text()
    assert original.replace('var complete := sims[0].latest.size()', 'var complete: bool = sims[0].latest.size()') == corrected
    patch = ''.join(difflib.unified_diff(original.splitlines(True), corrected.splitlines(True),
                                       fromfile='parse-failure/source_native_state_unit.gd',
                                       tofile='passed/source_native_state_unit.gd'))
    with (HERE / 'test-declaration-fix.patch').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(patch)
    driver = ROOT / 'experiments/native_source_live_port_20261115/run_state_owned.py'
    driver_row = copy(driver, 'source/run_state_owned.py')
    driver_text = driver.read_text()
    assert "SCRIPT_SHA = '" + CORRECTED + "'" in driver_text
    assert "actual.get('checks') == 180" in driver_text and "actual.get('metrics', {}).get('actors_loaded') == 3" in driver_text
    assert "actual.get('job_sha256') == sha(folder / 'job.json')" in driver_text
    assert "actual.get('source_manifest_sha256') == sha(folder / 'SOURCE.json')" in driver_text
    assert "all(actual.get('named_checks', {}).values())" in driver_text
    refusal = load(PREFLIGHT / 'PRECHECK_REFUSAL.json')
    assert refusal['format'] == 'has_native_state_preflight_refusal_1'
    assert refusal['status'] == 'REFUSED_BEFORE_ENGINE_LAUNCH' and refusal['engine_launched'] is False
    assert refusal['raw_child_inventory_output_retained'] is False and refusal['not_an_automatic_approval_rejection'] is True
    refusal_row = copy(PREFLIGHT / 'PRECHECK_REFUSAL.json', 'preflight/PRECHECK_REFUSAL.json')
    preflight_observation = {
        'path': str(PREFLIGHT), 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'exists': PREFLIGHT.is_dir(), 'entries_observed': sorted(path.name for path in PREFLIGHT.iterdir()),
        'parent_reported_initial_cause': 'Before-engine read-only CIM inventory access denied; no engine launched.',
        'independent_scope': 'Only current directory membership and the exact subsequent root-authored cause receipt inspected. Raw initial child inventory output was not retained and is not reconstructed.',
        'authoritative_cause_metadata': refusal_row}
    save('PREFLIGHT_NOTE.json', preflight_observation)
    benchmark = {
        'format': 'has_native8_state_actual_benchmark_1', 'passed': True,
        'actual_run': str(PASS), 'source_HEAD': load(PASS / 'SOURCE.json')['source_HEAD'],
        'checks': 180, 'failures': 0, 'actual_Model_actors': 3, 'source_files': 204,
        'completed_native_steps': 506, 'count_derivation': '240 independent-runner steps +23 negative seeds +3 file-isolation seeds +240 wrapper/replay steps',
        'assertion_categories': categories, 'negative_cases': 23,
        'file_isolation': {name: result['metrics'][name] for name in ('file_header', 'file_length', 'file_mtime')},
        'wrapper_scope': ['independent actor state, exact reset/replay', 'complete69-channel authored poses/keys/raw reports unchanged',
                          '68 unselected world bones exact', 'invalid dt, seek, reverse and skipped Record time refuse before state commit',
                          'Off/disposal restores all three actual models exactly'],
        'continuous_guard': 'Cached complete69-bone binding/report stamp plus source existence,12-byte GLB header, statmtime and length. Full source cryptographic authentication on create/reload.',
        'excluded_same_header_size_mtime_body_edits': excluded,
        'physical_body_scope': 'One actual simulating PhysicalBone3D only as an adversarial create/step refusal context; not a complete ragdoll or borrowed primary.',
        'same_actor_complete_ragdoll_or_borrowed_primary': 'UNQUALIFIED_PARTIAL_SOURCE_RIG',
        'native_rules_solved': 1, 'native_rules_retained': 49, 'native_conversion_GPU_GUI': False,
        'preservation': verification['preservation'], 'runtime_lease_released': True,
        'closed_observed_utc': verification['observed_utc'],
        'parse_then_state_seconds': [row['seconds'] for row in verification['phases']],
        'retained_parse_failure': {'passed': False, 'script_sha256': ORIGINAL, 'checks_executed': 0,
                                   'error': 'Cannot infer type of complete; fixed only by explicit bool declaration.',
                                   'state_phase_launched': False, 'runtime_lease_released': failed_verification['runtime_lease_released']},
        'earlier_preflight': preflight_observation,
        'raw_native_assets_or_buffers_in_public_packet': False}
    save('BENCHMARK.json', benchmark)
    save('SOURCE_PROOF.json', {
        'format': 'has_native8_state_actual_source_proof_1', 'passed_frozen_sources': source_rows,
        'failed_frozen_script': failed_source, 'successful_driver_source_review': driver_row,
        'driver_binding': 'Corrected script hash,180 exact assertion count, job/source hash bindings,3 actual actors, restored owned inputs, all preservation and runtime closure are checked by the copied driver and actual reports.',
        'failed_driver_original_bytes': 'Not captured independently. Failed job/commands/frozen46436 script and parse errors are preserved; current008e driver is not presented as the exact earlier driver bytes.',
        'prior96_product_header_guard_relationship': 'This state run uses frozen backend d2c04165587ca3bb0f7b9f474b23dc81902cc78c1aa174d593534f0198f689c0 with12-byte continuous header guard, qualifying later state/guard work separately from the earlier96-check frozen UI run.'})
    save('PAYLOAD_INDEX.json', {'format': 'has_native8_state_actual_alias_index_1', 'sources': ALIASES})
    note = '''# Native state and source-guard result

Passed180 checks with three actual Model actors and506 successful native steps. All source/read-only-input/runtime preservation gates passed; both headless parse and state processes exited0, were reaped and required no termination. Recorded before/after owned-runtime inventories are empty.

Coverage includes independent state/reset, all69 authored channels/keys/raw reports,68 unaffected world bones, atomic refusal of23 invalid contexts, complete wrapper pose preservation, Off/reset/replay, and isolated GLB header/length/mtime changes on new owned copies. A single actual simulating PhysicalBone3D is an adversarial refusal case only. Complete same-actor ragdoll/borrowed-primary coupling remains unqualified.

The continuous file guard checks source existence,12 header bytes, length, statmtime and a complete cached binding/report stamp. A body edit preserving header, size and mtime remains outside the continuous cryptographic guarantee. Creation/reload performs full authentication. This limitation is explicit in the original result and is not waived by this packet.

The earlier parse failure remains failed with0 executed state assertions. Its exact frozen script differs only by an explicit bool declaration. The still-earlier preflight refusal is recorded by the exact subsequent Root cause JSON: inventory access was denied before engine launch. It explicitly states that raw child inventory output was not retained; no raw logs or approval-review rejection are invented.

Included data is source, commands, safe lease JSON, source hashes, scalar/count result metadata, logs, process receipts and closure observations only. No GLB/HAS/PNG/native-rest matrices, weighted point arrays, decoded PCM or artwork is copied. The three state-owned native copies remain private and retained outside this packet. `verify_public_packet.py` checks all source aliases, hashes, count bindings and exclusions independently without launching any runtime.
'''
    with (HERE / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(note)
    print(json.dumps({'prepared': True, 'aliases': len(ALIASES), 'BENCHMARK_sha256': sha((HERE / 'BENCHMARK.json').read_bytes())}))


if __name__ == '__main__':
    main()
