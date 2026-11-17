"""Root actual full-PASS projection: public scalars/hashes, no native payloads."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-3a3701a-mmd-20261117T200622956559'
load = lambda path: json.loads(path.read_bytes())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    state = load(RUN / 'state.json')
    release = load(RUN / 'graphics-lease-closed.json')
    audit = RUN / 'terminal-audit-attempt1'
    inventory = load(audit / 'receipt-inventory.json')
    assert sha(audit / 'receipt-inventory.json') == 'a4b47b3bd0582e62f9466648cce07a25e8828656a9458262eac1d6e4eac84a23'
    result = load(audit / 'full-verification.json')
    assert state['status'] == 'passed' and state['suite_exit'] == 0 and state['source_unchanged'] is True
    assert release['released'] is True and release['full_suite_passed'] is True
    assert release['release_kind'] == 'closed_passed_full_run'
    assert inventory['full_suite_passed'] is True and inventory['result_groups'] == len(result) == 158
    assert inventory['core_groups'] == 36 and inventory['movie_groups'] == 21
    assert inventory['unique_physical_jobs'] == inventory['physical_receipt_files'] == 196
    assert inventory['normal_exit0'] == 195 and inventory['registered_cancel_exit2'] == 1
    assert result['actual_mmd_tested'] is True and result['pose_checks'] == 45
    assert result['neon_workspace']['checks'] == 12504 and result['neon_workspace']['failures'] == 0
    assert result['camera_range']['checks'] == 60 and result['camera_range']['failures'] == 0
    assert result['color_sampler']['checks'] == 44 and result['color_sampler']['failures'] == 0
    preserved = load(RUN / 'ROOT_PROTECTED_INPUTS_AFTER.json')
    assert preserved['all_unchanged'] is True
    b = ROOT / 'output/native-normal-B-known-factory-20261117T210226296393'
    b_result = load(b / 'ROOT_RESULT.json')
    b_public = load(b / 'PUBLIC_RESOURCES.json')
    assert b_result['diagnostic_completed'] is True and b_result['resource_status'] == 'RESOURCE_PROFILE_REFUSED'
    assert b_result['root_fresh_scopes_closed'] is True and b_result['input_source_tool_context_preserved'] is True
    assert b_result['process']['exit'] == 0 and b_result['process']['retained_Popen_reaped'] is True
    assert not b_result['process']['timed_out'] and not any(b_result['claims'].values())
    output = ROOT / 'experiments/neon_3a_mmd_full_pass_actual_20261117'
    output.mkdir(exist_ok=False)
    record = {'format': 'has_root_actual_neon_full_pass_scalars_1',
        'candidate_commit': state['source_commit'], 'run': RUN.name,
        'started_utc': state['started_utc'], 'finished_utc': state['finished_utc'],
        'suite_exit': 0, 'full_suite_passed': True, 'functional_files_unchanged': 1029,
        'result_groups': 158, 'core_groups': 36, 'movie_groups': 21,
        'actual_mmd_tested': True, 'pose_checks': 45, 'neon_checks': 12504,
        'camera_checks': 60, 'color_checks': 44, 'all_failures': 0,
        'physical_jobs': 196, 'normal_exit0': 195, 'registered_Krita_cancel_exit2': 1,
        'all_physical_jobs_and_desktops_closed': True,
        'inline_receipts_exactly_match_owned_physical_receipts': True,
        'strict_terminal_INDEX_sha256': 'f223587f75cb56281b961679fecb399672025216c1b0f23f5cebee20cdc38d6b',
        'receipt_inventory_sha256': sha(audit / 'receipt-inventory.json'),
        'raw_private_full_report_sha256': sha(audit / 'full-verification.json'),
        'raw_private_canonical_log_sha256': sha(RUN / 'canonical.log'),
        'release_sha256': sha(RUN / 'graphics-lease-closed.json'),
        'post_run_protected_inputs': preserved,
        'Source_B_metadata_diagnostic': {'completed': True, 'process_exit': 0,
            'resource_status': 'RESOURCE_PROFILE_REFUSED', 'profile_issues': 6,
            'export_branch': 'UNKNOWN', 'process_reaped': True, 'scopes_closed': True,
            'inputs_source_tools_preserved': True, 'raw_result_sha256': sha(b / 'ROOT_RESULT.json'),
            'resource_summary_sha256': sha(b / 'PUBLIC_RESOURCES.json'),
            'unused_internal_viewer_images': 2, 'viewer_material_references': 0,
            'unclassified_repeated_reference_count': 1,
            'reference_datablock_owner_type_and_content_remain_unobserved': True,
            'strict31_normal_repair_fidelity_or_adoption_claimed': False},
        'prior157_group_run_remains_UNQUALIFIED': True,
        'preparation_main_metadata_label_correction': {
            'inherited_ancestor_label': '855d67fe44868793a29d6c6c75c61c0ba86236d2',
            'meaning': 'retained parent-preparer checkpoint label, not actual current Main HEAD',
            'actual_main_parent_for_qualified_merge': 'f21b9ec85ae63006d036ca7a21c5c82e53fda019',
            'functional52_invariant_in_preparation_was_correct': True},
        'merge_state_at_recording': 'QUALIFIED_MERGE_IN_PROGRESS',
        'owner_copy_and_cold187': 'UNRUN', 'human_acceptance': 'DEFERRED',
        'native_normal_fidelity': 'FAILED_UNQUALIFIED',
        'raw_native_arrays_art_callback_metadata_and_logs_included': False}
    save(output / 'RESULT.json', record)
    for name, path in (('STATE.json', RUN / 'state.json'),
                       ('RELEASE.json', RUN / 'graphics-lease-closed.json'),
                       ('PROTECTED_INPUTS_AFTER.json', RUN / 'ROOT_PROTECTED_INPUTS_AFTER.json')):
        with (output / name).open('xb') as stream: stream.write(path.read_bytes())
    rows = [{'path': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(output.iterdir())]
    save(output / 'INDEX.json', {'format': 'has_root_actual_neon_full_pass_public_index_1',
                               'files': rows, 'raw_private_payloads_included': False})
    print(json.dumps({'full_suite_passed': True, 'result_groups': 158,
                     'public_INDEX_sha256': sha(output / 'INDEX.json'), 'owner_copy_or187_claimed': False}))


if __name__ == '__main__': main()
