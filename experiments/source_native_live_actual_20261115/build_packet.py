"""Archive completed native8 actual-run code/metadata only; no runtime or art."""
from pathlib import Path
import ast
import collections
import datetime
import gzip
import hashlib
import io
import json
import re

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUNS = {1: ROOT / 'output/source-native-live-20261115-attempt1',
        2: ROOT / 'output/source-native-live-20261115-attempt2'}
PRODUCTION = ['src/source_secondary.gd', 'src/source_jiggle_math.gd',
              'src/secondary_live.gd', 'src/physics_editor.gd', 'src/fan_editor.gd']
TESTS = ['tests/source_native_live_ui.gd', 'tests/verify_source_native_live.py',
         'tests/source_native_live_capture.gd']
PHASE_FILES = ['command.json', 'engine.log', 'private-receipt.json',
               'process-verification.json', 'result.json', 'stderr.log', 'stdout.log']
ALIASES = []
STORED = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def store(source, relative, compress=False):
    assert source.suffix in ('.json', '.log', '.gd', '.py', '.cfg')
    raw = source.read_bytes()
    if compress:
        buffer = io.BytesIO()
        with gzip.GzipFile(filename='', mode='wb', fileobj=buffer, mtime=0, compresslevel=9) as stream:
            stream.write(raw)
        encoded = buffer.getvalue()
        assert gzip.decompress(encoded) == raw
    else:
        encoded = raw
    path = HERE / relative
    assert path.is_relative_to(HERE) and '..' not in Path(relative).parts
    if relative in STORED:
        assert path.read_bytes() == encoded
    else:
        assert not path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(encoded)
        STORED[relative] = {'path': relative, 'bytes': len(encoded), 'sha256': sha(encoded)}
    ALIASES.append({'source': str(source), 'source_bytes': len(raw), 'source_sha256': sha(raw),
                    'stored': relative, 'compression': 'gzip' if compress else 'none',
                    'stored_bytes': len(encoded), 'stored_sha256': sha(encoded)})
    return {'path': str(source), 'bytes': len(raw), 'sha256': sha(raw), 'stored': relative}


def main():
    run2 = RUNS[2]
    verification = load(run2 / 'verification.json')
    closure = load(run2 / 'authoritative-closure.json')
    assert verification['passed'] and verification['checks_expected'] == verification['checks_observed'] == 96
    assert verification['phase_expected'] == {'writer': 77, 'reader-packed': 11, 'reader-linked': 8}
    assert len(verification['results']) == 3 and all(verification['preservation'].values())
    assert closure['validation_passed'] and closure['owned_private_jobs_closed'] == 3
    assert closure['owned_runtime_commands_absent'] and closure['runtime_lease_released'] and closure['no_process_killed']
    assert closure['verification_sha256'] == sha((run2 / 'verification.json').read_bytes())
    phases = []
    names = []
    for phase, expected_count in [('writer', 77), ('reader-packed', 11), ('reader-linked', 8)]:
        folder = run2 / phase
        result = load(folder / 'result.json')
        process = load(folder / 'process-verification.json')
        receipt = load(folder / 'private-receipt.json')
        declared = next(row for row in closure['actual_phases'] if row['name'] == phase)
        assert process['passed'] and process['result_binding'] and process['domain_checks_passed']
        assert process['domain_failure_count'] == process['exit'] == result['failures'] == 0
        assert process['retained_Popen_reaped'] and process['private_receipt_passed']
        assert not process['timed_out'] and not process['error_markers'] and not process['metadata_errors']
        assert result['checks'] == len(result['named_checks']) == expected_count and all(result['named_checks'].values())
        assert result['complete_assertion_set'] and result['private_native_arrays_serialized'] is False
        assert result['native_rules_solved'] == 1 and result['retained_rules'] == 49
        assert result['same_actor_reverse_body_qualification'] == 'UNQUALIFIED_PARTIAL_SOURCE_RIG'
        assert receipt['exit'] == 0 and receipt['job_closed'] and receipt['desktop_closed'] and receipt['child_desktop_confirmed']
        assert not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested']
        assert declared['checks'] == expected_count and declared['failures'] == 0 and declared['exit'] == 0
        assert declared['result_sha256'] == process['result_sha256'] == sha((folder / 'result.json').read_bytes())
        for filename in PHASE_FILES:
            store(folder / filename, 'actual2/' + phase + '/' + filename)
        names.extend(phase + '/' + name for name in result['named_checks'])
        phases.append({'phase': phase, 'checks': expected_count, 'failures': 0,
                       'exit': 0, 'private_job_and_desktop_closed': True, 'seconds': process['seconds'],
                       'exact_names': list(result['named_checks'])})
    assert len(names) == len(set(names)) == 96
    for number in (1, 2):
        run = RUNS[number]
        before = (run / 'source-before.json').read_bytes()
        assert before == (run / 'source-after.json').read_bytes()
        assert len(json.loads(before)) == 1013
        store(run / 'source-before.json', 'actual' + str(number) + '/source-before-and-after.json.gz', True)
        store(run / 'source-after.json', 'actual' + str(number) + '/source-before-and-after.json.gz', True)
        store(run / 'verification.json', 'actual' + str(number) + '/verification.json')
        store(run / 'authoritative-closure.json', 'actual' + str(number) + '/authoritative-closure.json')
    store(run2 / 'offline-plan.json', 'actual2/offline-plan.json')
    source_map = load(run2 / 'source-before.json')
    source_rows = []
    for name in PRODUCTION + TESTS:
        path = run2 / 'Studio' / name
        raw = path.read_bytes()
        assert sha(raw) == source_map[name]['sha256'] and len(raw) == source_map[name]['bytes']
        row = store(path, 'source/attempt2/' + name)
        row['functional_path'] = name
        source_rows.append(row)
    # First attempt uses the same five product files; only its test assumption
    # and driver's failed-phase reporting differ. Preserve both old test sources.
    first_source_rows = []
    for name in PRODUCTION:
        assert (RUNS[1] / 'Studio' / name).read_bytes() == (run2 / 'Studio' / name).read_bytes()
    for name in TESTS[:2]:
        first_source_rows.append(store(RUNS[1] / 'Studio' / name, 'source/attempt1/' + name))
    first = load(RUNS[1] / 'writer/result.json')
    first_verification = load(RUNS[1] / 'verification.json')
    first_closure = load(RUNS[1] / 'authoritative-closure.json')
    first_receipt = load(RUNS[1] / 'writer/private-receipt.json')
    assert first['checks'] == 74 and first['failures'] == 2
    assert [name for name, value in first['named_checks'].items() if not value] == [
        'body.actual_primary_started', 'body.native_refusal_preserves_primary']
    assert first_verification['passed'] is False and first_verification['checks_observed'] == 0
    assert first_closure['validation_passed'] is False and first_closure['owned_private_jobs_closed'] == 1
    assert first_closure['owned_runtime_commands_absent'] and first_closure['runtime_lease_released']
    assert first_receipt['exit'] == 1 and first_receipt['job_closed'] and first_receipt['desktop_closed']
    for name in PHASE_FILES:
        store(RUNS[1] / 'writer' / name, 'actual1/writer/' + name)
    driver_raw = (run2 / 'Studio/tests/verify_source_native_live.py').read_bytes()
    tree = ast.parse(driver_raw)
    execute = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'execute')
    assert isinstance(execute.body[-1], ast.Return) and execute.body[-1].value.id == 'proof'
    assert not any(isinstance(node, ast.Assert) for node in execute.body[-2:])
    driver_text = driver_raw.decode('utf-8')
    assert "assert results[-1]['passed']" in driver_text
    assert "'checks_observed': sum(row['checks'] for row in results)" in driver_text
    writer = load(run2 / 'writer/result.json')
    observations = writer['metrics']
    assert set(observations) == {'disabled', 'zero', 'miss', 'speed3', 'speed12', 'speed50', 'opposite'}
    assert all(row['tick_count'] == 180 and row['native_Z_tip_error_max'] <= .00002 for row in observations.values())
    assert observations['disabled']['points_sha256'] == observations['zero']['points_sha256'] == observations['miss']['points_sha256']
    metrics = {name: {'relative_fan_speed': int(name[5:]) if name.startswith('speed') else 12,
                      'weighted_displacement_vs_disabled_m': row.get('affected_max_vs_disabled'),
                      'last_60_ticks_tip_span_m': row['last_second_tip_span'],
                      'native_Z_tip_error_max_m': row['native_Z_tip_error_max']}
               for name, row in observations.items()}
    metrics['zero']['relative_fan_speed'] = 0
    benchmark = {
        'format': 'has_native8_first_product_actual_benchmark_1', 'passed': True,
        'actual_run': str(run2), 'root_closed_utc': closure['observed_utc'],
        'checks': 96, 'writer_checks': 77, 'packed_reader_checks': 11, 'linked_reader_checks': 8,
        'closed_private_jobs': 3, 'preservation_gates': verification['preservation'],
        'functional_source_files': 1013, 'native_rules_solved': 1, 'native_rules_retained': 49,
        'profile': 'Original qualified Junko FrontHair1 native8/parent7/0x31 only; no generic chains',
        'actual_controlled_fan_profiles': 7, 'ticks_per_profile': 180, 'physics_Hz': 120,
        'controlled_profile_ticks_total': 1260, 'weighted_vertices': 152, 'shared_weight_vertices': 144,
        'unaffected_vertices_exact': 9509, 'total_vertices': 9661, 'other_world_bones_exact': 68,
        'fan_metrics': metrics,
        'historical_metric_name_note': 'Raw last_second_tip_span is the maximum displacement from the final tip among the last60 fixed ticks, i.e.0.5seconds at120Hz; the raw report is preserved unchanged.',
        'ordinary_editor_acceptance': [
            'actual Add fan/Aim/relative speeds0/3/12/50/disabled/missed/opposite fields',
            'native desired-state versus actual native-Z tip and exact weighted Off at keyed12/24',
            'seek and unrecorded Save restore authored data without a draft',
            'partial-rig ragdoll refusal; existing independent fan rigid-body identity/RID preserved on native On/Off',
            'connected Local Record Stop/Escape/Undo/Redo, ordinary FK, immutable49-rule metadata',
            'packed+linked cold no-autoactivation, FK/final-frame0/24 agreement and packed PNG-export agreement',
            'existing generic declared-chain backend and Off'],
        'native_fan_policy': 'Explicit HAS world acceleration: existing deterministic fan field divided by0.03, bounded by field cap. Relative fan speed is not SDK wind parity or a calibrated real fan.',
        'same_actor_reverse_body_qualification': 'UNQUALIFIED_PARTIAL_SOURCE_RIG',
        'not_claimed': ['all49 native rules simulated', 'full Source SDK/client parity', 'same-actor active ragdoll/native coexistence',
                        'native parent-chain product integration', 'a new native converter run',
                        'later header-guard followup changes qualified by this96-check run'],
        'first_attempt': {'passed': False, 'actual_writer_checks': 74, 'actual_failures': 2,
                          'old_aggregate_observed_checks_preserved': 0,
                          'reason': 'Hair-only partial skeleton correctly rejects automatic ragdoll; two test expectations were invalid.',
                          'count_reporting_correction': 'Old execute raised before returning phase proof. New driver appends each returned proof before its strict pass assertion; actual attempt2 records77+11+8.',
                          'original_failed_phase_exit': 1, 'original_private_job_closed': True},
        'source_context': 'Exact frozen attempt2 working-functional snapshot, not the later edited checkout.',
        'raw_native_points_PCM_artwork_in_packet': False}
    save(HERE / 'BENCHMARK.json', benchmark)
    save(HERE / 'SOURCE_PROOF.json', {
        'format': 'has_native8_actual_frozen_source_proof_1',
        'actual2_sources': source_rows, 'actual1_test_sources': first_source_rows,
        'actual1_product_sources_equal_actual2_five': True,
        'header_followup': 'Parent reported later header-guard edit after96-check closure. This packet copies frozen attempt2 product code only and does not claim the later guard was tested here.',
        'driver_failed_phase_accounting_source_review': {'return_failed_proof': True, 'append_before_pass_assert': True,
                                                        'context_binding_separate_from_domain_pass': 'result_binding/domain_checks_passed',
                                                        'actual_recorded_results': [77, 11, 8]},
        'baseline_converter_evidence_reference_only': verification['baseline_conversion']})
    save(HERE / 'PAYLOAD_INDEX.json', {'format': 'has_native8_actual_source_alias_index_1', 'sources': ALIASES,
                                     'stored_payloads': list(STORED.values())})
    note = '''# First native spring product result

Passed96 actual editor checks:77writer,11packed cold reader and8linked cold reader. All three private jobs/desktops closed, all four preservation gates passed, and the root lease closed2026-11-16T01:48:47.8599896Z.

The exact original Junko profile now exercises one imported FrontHair1 joint through real Hair & clothes/fan/Local Record controls. Seven180-tick profiles cover disabled/zero/missed/3/12/50/opposite airflow. At relative speed50, the measured weighted displacement from disabled was0.014946725m; maximum observed native-Z tip error across profiles was below1.77e-6m. Off, seek and unrecorded Save restore authored poses; Record remains ordinary editable FK. Packed and linked cold readers retain the49-rule report, keep simulation off and match final frames0/24; packed PNG export matches too.

The original74-check attempt remains failed with its two incorrect ragdoll expectations. Its partial hair rig has no validated arms/legs. The successor tests that refusal and uses a real separate fan rigid body to verify independent body ownership survives native On/Off. Same-actor active-ragdoll/native combination and48other native rules remain unqualified.

Sources are copied from the frozen successful Studio: five product files plus the three public test files. The later header-guard followup is separate work. Exact functional before/after maps and actual commands/logs/results/receipts/closures are included; identical before/after maps share one lossless payload with both source aliases recorded. No expected files, PNG/HAS/GLB/sidecars, decoded PCM, model buffers or weighted point arrays are included.

`verify_public_packet.py` independently checks every outer hash, each stored/decompressed/source alias, actual counts/closures/source-map joins and private-payload exclusions. The numerical values describe this restricted HAS profile and explicit HAS fan policy; they are not a claim of full Source SDK parity.
'''
    with (HERE / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(note)
    print(json.dumps({'prepared': True, 'stored_actual_payloads': len(STORED),
                      'source_aliases': len(ALIASES), 'benchmark_sha256': sha((HERE / 'BENCHMARK.json').read_bytes())}))


if __name__ == '__main__':
    main()
