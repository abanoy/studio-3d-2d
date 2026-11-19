"""Pure Root authority, background receipt and bounded observation checks."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

HEAD = '795a0af905bfbe49b99ab7335594cd6666ef91e5'
QUALIFICATIONS = ('native_storage_rule_qualified', 'universal_group_or_F32_domain_qualified',
                  'actual_source_rows_or_saved_scene_qualified', 'native_fidelity_export_repair_adoption_qualified')


def need(ok, message):
    if not ok: raise ValueError(message)


def same(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def utc(value):
    need(type(value) is str, 'Explicit UTC timestamp required')
    result = datetime.fromisoformat(value)
    need(result.tzinfo is not None and result.utcoffset() == timedelta(0), 'UTC timestamp required')
    return result


def zero_scope(value):
    need(type(value) is dict and all(type(value.get(k)) is int and value[k] == 0
         for k in ('owned_count', 'main_count', 'review_count')), 'Actual zero Main/Review lane counts required')


def authority(value, root, runtime_sha, probe_sha, now, *, initial=True):
    fields = {'format', 'phase', 'metadata_head', 'run_id', 'issued_utc', 'expires_utc', 'output_root',
              'runtime_packet_sha256', 'probe_packet_sha256', 'root_execution_authorized', 'root_lane'}
    need(type(value) is dict and set(value) == fields, 'Exact fresh Root authority schema required')
    need(value['format'] == 'has_root_synthetic_weight_storage_execution_authority_1'
         and value['phase'] == 'ROOT_APPROVED_FRESH_SYNTHETIC_ONLY'
         and value['metadata_head'] == HEAD and value['root_execution_authorized'] is True, 'Root authority/head differs')
    need(sha(runtime_sha) and sha(probe_sha) and value['runtime_packet_sha256'] == runtime_sha
         and value['probe_packet_sha256'] == probe_sha, 'Exact reviewed packet authorities required')
    need(type(value['run_id']) is str and re.fullmatch('[0-9a-f]{32}', value['run_id']), 'Fresh run ID required')
    issued, expires = utc(value['issued_utc']), utc(value['expires_utc'])
    need(issued <= now < expires <= issued + timedelta(minutes=15)
         and (not initial or now - issued <= timedelta(minutes=2)), 'Fresh bounded Root authority required')
    need(type(value['output_root']) is str, 'Literal owned output path required')
    stage = Path(value['output_root'])
    need(stage.is_absolute()
         and stage == root / 'output' / ('weight-storage-probe-20261118-' + value['run_id']), 'Exact fresh direct Root/output stage required')
    lane = value['root_lane']
    need(type(lane) is dict and set(lane) == {'format', 'observed_utc', 'owned_count', 'main_count', 'review_count', 'termination_issued'}
         and lane['format'] == 'has_root_synthetic_weight_storage_closed_lane_1'
         and lane['termination_issued'] is False, 'Fresh read-only Root lane authority required')
    zero_scope(lane)
    need(issued - timedelta(minutes=2) <= utc(lane['observed_utc']) <= issued, 'Fresh observed closed lane required')
    return stage


def receipt(value, process_exit, contract):
    need(type(value) is dict and value.get('format') == 'studio_private_desktop_1', 'Wrapper receipt format differs')
    required = {'child_desktop_confirmed': True, 'foreground_child_observed': False,
                'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True,
                'job_memory_limit_bytes': 2048 * 1024 * 1024}
    need(all(same(value.get(k), v) for k, v in required.items()), 'Actual private desktop/job receipt refused')
    need(type(process_exit) is int and type(value.get('exit')) is int and value['exit'] == process_exit
         and type(value.get('child_pid')) is int and value['child_pid'] > 0
         and type(value.get('private_window_seen')) is bool, 'Actual child exit/PID/window fields required')
    need(not any(k in value for k in ('error', 'monitor_error', 'desktop_enumeration_error', 'timed_out', 'cancelled')), 'Wrapper/monitor failure recorded')
    if process_exit == 0:
        contract.qualify_background_receipt(value)  # Exact sealed public validator.
    return {'background_private_desktop_confirmed': True, 'private_window_seen': value['private_window_seen'],
            'child_exit': process_exit, 'visible_window_required': False}


def observation(report, plan, request_sha, contract):
    """Preserve a complete finite mismatch as NOT_PASS, never turn it into a match."""
    need(type(report) is dict and report.get('status') in ('BOUNDED_SYNTHETIC_STORAGE_MATCH', 'BOUNDED_SYNTHETIC_STORAGE_MISMATCH'), 'Complete finite observation required')
    common = {'format': 'has_synthetic_blender_weight_storage_observation_1', 'run_id': plan['run_id'],
              'request_sha256': request_sha, 'copied_script_identities': plan['scripts'],
              'Root_expected_runtime_identity': plan['runtime'], 'case_count': contract.CASE_COUNT,
              'group_count': contract.GROUP_COUNT, 'group_alphabet': list(contract.GROUP_IDS),
              'weight_word_alphabet': [f'{x:08x}' for x in contract.WEIGHT_WORDS],
              'sourceio_importer_rule_sha256': contract.SOURCEIO_IMPORTER_SHA256,
              'expected_positive_add_calls': contract.POSITIVE_WRITE_COUNT, 'positive_add_calls': contract.POSITIVE_WRITE_COUNT,
              'owned_object_mesh_cleanup_exact': True, 'cleanup_error_types': [], 'synthetic_group_indices_exact': True,
              'runtime_binary_hash_verified_by_probe': False, 'native_API_execution_observed_by_this_script': True,
              'factory_background_no_model_file': True, 'scene_or_native_model_files_opened': False,
              'files_exported_or_blend_saved': False, 'window_or_desktop_API_called_by_probe': False,
              'runtime_version': [5, 1, 2], **{name: False for name in QUALIFICATIONS}}
    need(all(same(report.get(k), v) for k, v in common.items()), 'Observation/source/request/runtime/qualification binding differs')
    need('error_type' not in report and type(report.get('mesh_validate_reported_change')) is bool
         and type(report.get('immediate_vs_after_validate_exact')) is bool, 'Probe failed or incomplete validate observation')
    need(all(type(report.get(k)) is str and 0 < len(report[k]) <= 128 for k in ('runtime_version_string', 'runtime_build_hash')), 'Bounded runtime strings required')
    catalogue = contract.cases()
    need(report.get('case_catalogue_sha256') == contract.case_digest(catalogue), 'Finite case catalogue differs')
    expected_hash = contract.row_digest(tuple(contract.expected_row(case) for case in catalogue))
    expected_hist = {str(k): v for k, v in contract.EXPECTED_GROUP_HISTOGRAM.items()}
    phases = {}
    for name in ('immediate', 'after_validate'):
        phase = report.get(name)
        fields = {'observed_rows', 'expected_rows', 'mismatch_cases', 'extra_observed_rows', 'mismatch_counts', 'bounded_examples',
                  'expected_ordered_rows_sha256', 'observed_ordered_rows_sha256', 'expected_group_count_histogram', 'all_cases_match'}
        need(type(phase) is dict and set(phase) == fields, 'Complete bounded phase schema required')
        for key, limit in (('observed_rows', contract.CASE_COUNT + 1), ('mismatch_cases', contract.CASE_COUNT), ('extra_observed_rows', 1)):
            need(type(phase[key]) is int and 0 <= phase[key] <= limit, 'Phase count outside finite bound')
        need(type(phase['expected_rows']) is int and phase['expected_rows'] == contract.CASE_COUNT
             and phase['extra_observed_rows'] == max(0, phase['observed_rows'] - contract.CASE_COUNT)
             and phase['expected_ordered_rows_sha256'] == expected_hash and sha(phase['observed_ordered_rows_sha256'])
             and same(phase['expected_group_count_histogram'], expected_hist), 'Finite phase identity/count binding differs')
        counts = phase['mismatch_counts']
        need(type(counts) is dict and set(counts) == {'row_missing', 'ordered_group_relation', 'weight_word'}
             and all(type(v) is int and 0 <= v <= phase['mismatch_cases'] for v in counts.values())
             and counts['row_missing'] == max(0, contract.CASE_COUNT - phase['observed_rows'])
             and phase['mismatch_cases'] <= sum(counts.values()) <= 2 * phase['mismatch_cases'], 'Mismatch counts inconsistent')
        matched = phase['mismatch_cases'] == 0 and phase['extra_observed_rows'] == 0
        need(type(phase['all_cases_match']) is bool and phase['all_cases_match'] is matched
             and (not matched or phase['observed_ordered_rows_sha256'] == expected_hash), 'Phase match claim inconsistent')
        examples = phase['bounded_examples']
        need(type(examples) is list and len(examples) == min(contract.MAX_EXAMPLES, phase['mismatch_cases']), 'Bounded mismatch examples required')
        previous = -1
        for example in examples:
            need(type(example) is dict and set(example) == {'case_index', 'slot_groups', 'slot_weight_words', 'expected', 'observed', 'reasons'}, 'Exact synthetic example schema required')
            index = example['case_index']; need(type(index) is int and previous < index < contract.CASE_COUNT, 'Ordered bounded example indices required'); previous = index
            case = catalogue[index]
            need(same(example['slot_groups'], [group for group, _ in case]) and same(example['slot_weight_words'], [f'{word:08x}' for _, word in case])
                 and same(example['expected'], [[group, f'{word:08x}'] for group, word in contract.expected_row(case)]), 'Synthetic example source binding differs')
            actual = example['observed']
            need(actual is None or type(actual) is list and len(actual) <= contract.GROUP_COUNT
                 and all(type(pair) is list and len(pair) == 2 and type(pair[0]) is int and 0 <= pair[0] < contract.GROUP_COUNT
                         and type(pair[1]) is str and re.fullmatch('[0-9a-f]{8}', pair[1]) for pair in actual), 'Bounded observed synthetic example required')
            need(type(example['reasons']) is list and 1 <= len(example['reasons']) <= 2
                 and len(set(example['reasons'])) == len(example['reasons'])
                 and all(reason in counts for reason in example['reasons']), 'Example mismatch reasons differ')
        phases[name] = {k: phase[k] for k in ('mismatch_cases', 'extra_observed_rows', 'mismatch_counts', 'expected_ordered_rows_sha256', 'observed_ordered_rows_sha256', 'all_cases_match')}
    need(report['immediate_vs_after_validate_exact'] is
         (report['immediate']['observed_ordered_rows_sha256'] == report['after_validate']['observed_ordered_rows_sha256']),
         'Immediate/after-validate exactness contradicts ordered row hashes')
    both = all(report[name]['all_cases_match'] for name in phases) and report['immediate_vs_after_validate_exact']
    need((report['status'] == 'BOUNDED_SYNTHETIC_STORAGE_MATCH') is both, 'Observation status contradicts phase evidence')
    if both:
        contract.validate_matching_public_report(report, expected_request_sha256=request_sha, expected_run_id=plan['run_id'],
                                                  expected_scripts=plan['scripts'], expected_runtime=plan['runtime'])
    return {'observation_status': report['status'], 'finite_cases': contract.CASE_COUNT, 'phases': phases,
            'immediate_vs_after_validate_exact': report['immediate_vs_after_validate_exact'],
            'native_storage_rule_qualified': False, 'universal_or_actual_source_policy_qualified': False,
            'native_fidelity_export_repair_adoption_qualified': False}


def completed(process, receipt_summary, observation_summary, preserved, before, after):
    return (preserved is True and before is True and after is True and process.get('retained_Popen_reaped') is True
            and process.get('timed_out') is False and type(process.get('exit')) is int and process['exit'] == 0
            and type(receipt_summary.get('child_exit')) is int and receipt_summary['child_exit'] == 0
            and receipt_summary.get('background_private_desktop_confirmed') is True
            and observation_summary.get('observation_status') == 'BOUNDED_SYNTHETIC_STORAGE_MATCH')
