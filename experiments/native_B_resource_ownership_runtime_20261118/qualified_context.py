"""Fixed source/public qualification metadata; never opens native output or art."""
from pathlib import Path
import json
import diagnostic_support as S

SOURCE = S.ROOT / 'experiments/neon_windows_3a3701a_20261117/active-observation/source-before.json'
SOURCE_SHA = '3ef2e7d8bed6e063afef59c8caccba914663752998761350c882fd4efbc78e9d'
FULL = S.ROOT / 'experiments/neon_3a_mmd_full_pass_actual_20261117'
FULL_SHA = '941e9aeab6d788fd7e92603a0a8f9e7c2fde0f48e2f5c9193b37c8a931dc851a'
REVIEWED = S.ROOT / 'experiments/neon_3a_shell_eol_root_review_20261117/REVIEWED52_TO_CANDIDATE_DELTA.json'
REVIEWED_SHA = '129beeac3bf394774d26c603063b63813ebc84070444987cce51dacd361affdb'
TESTED = '3a3701ab6edfa81dc883759403c170b8555aab07'
STRICT = 'f223587f75cb56281b961679fecb399672025216c1b0f23f5cebee20cdc38d6b'


def validate_qualification(snapshot, result, release, state, protected, reviewed):
    """Pure metadata joins. This is historical qualification, never fresh closure."""
    S.need(type(snapshot) is dict and set(snapshot) == {'commit', 'source_sha256'}
           and snapshot['commit'] == TESTED and type(snapshot['source_sha256']) is dict
           and len(snapshot['source_sha256']) == 1029, 'Exact immutable qualified1029 source map required')
    expected = {'format': 'has_root_actual_neon_full_pass_scalars_1', 'candidate_commit': TESTED,
                'suite_exit': 0, 'full_suite_passed': True, 'functional_files_unchanged': 1029,
                'result_groups': 158, 'core_groups': 36, 'movie_groups': 21, 'actual_mmd_tested': True,
                'all_failures': 0, 'physical_jobs': 196, 'normal_exit0': 195,
                'registered_Krita_cancel_exit2': 1, 'all_physical_jobs_and_desktops_closed': True,
                'inline_receipts_exactly_match_owned_physical_receipts': True,
                'strict_terminal_INDEX_sha256': STRICT}
    S.need(all(type(result.get(k)) is type(v) and result[k] == v for k, v in expected.items()),
           'Exact qualified full158/36/21/f223 and196 closed jobs required')
    expected_release = {'format': 'has_root_neon_ffcf_graphics_lease_release_1', 'released': True,
                        'release_kind': 'closed_passed_full_run', 'source_commit': TESTED,
                        'full_suite_passed': True, 'suite_exit': 0, 'functional_sources': 1029,
                        'physical_jobs': 196, 'physical_receipt_files': 196,
                        'all_collected_jobs_desktops_closed_private': True,
                        'all_inline_exact_physical_matches': True, 'root_observer_issued_no_termination': True}
    S.need(all(type(release.get(k)) is type(v) and release[k] == v for k, v in expected_release.items())
           and result['run'] == release['canonical_run']
           and result['receipt_inventory_sha256'] == release['receipt_inventory_sha256'],
           'Qualified full release/inventory join differs')
    S.need(state.get('format') == 'has_owned_canonical_run_1' and state.get('status') == 'passed'
           and state.get('source_commit') == TESTED and type(state.get('suite_exit')) is int
           and state['suite_exit'] == 0 and state.get('source_unchanged') is True,
           'Qualified full terminal source state differs')
    S.need(protected == result['post_run_protected_inputs'] and protected.get('all_unchanged') is True,
           'Qualified full protected-input recheck differs')
    S.need(reviewed.get('format') == 'has_reviewed52_to_qualified_Neon_delta_1'
           and reviewed.get('review_status') == 'ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA'
           and reviewed.get('reasons_status') == 'ROOT_REVIEWED_ALL39_REASONS_PRESERVED'
           and reviewed.get('candidate_manifest_commit') == TESTED
           and reviewed.get('candidate_immutable_before_sha256') == SOURCE_SHA
           and type(reviewed.get('rows')) is list and len(reviewed['rows']) == 39,
           'Exact reviewed39 source provenance required')
    return snapshot


def check_qualified_context():
    S.packet(FULL, FULL_SHA)
    raw = S.safe(SOURCE).read_bytes(); reviewed = S.safe(REVIEWED).read_bytes()
    S.need(len(raw) <= 256 * 1024 and S.digest(raw) == SOURCE_SHA
           and len(reviewed) <= 128 * 1024 and S.digest(reviewed) == REVIEWED_SHA,
           'Immutable candidate and reviewed39 metadata pins changed')
    return validate_qualification(json.loads(raw), S.read_json(FULL / 'RESULT.json'),
        S.read_json(FULL / 'RELEASE.json'), S.read_json(FULL / 'STATE.json'),
        S.read_json(FULL / 'PROTECTED_INPUTS_AFTER.json'), json.loads(reviewed))
