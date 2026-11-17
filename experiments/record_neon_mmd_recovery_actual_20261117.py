"""Scalar public projection of Root's actual closed/incomplete run and MMD recovery."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
OLD = REVIEW / 'output/windows-neon-3a3701a-20261117T185401541257'
NEW = REVIEW / 'output/windows-neon-3a3701a-mmd-20261117T200622956559'
load = lambda path: json.loads(path.read_bytes())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def descriptor(path):
    before = path.stat()
    digest = sha(path)
    assert (path.stat().st_size, path.stat().st_mtime_ns) == (before.st_size, before.st_mtime_ns)
    return {'bytes': before.st_size, 'sha256': digest}


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    inventory_path = OLD / 'terminal-audit-unqualified-mmd-attempt1/receipt-inventory.json'
    assert sha(inventory_path) == 'c3eb67c3e0e07d16e21325905773c28233a10a0d4bddc2c34c889bdaa88f28de'
    inventory = load(inventory_path)
    release = load(OLD / 'graphics-lease-unqualified-closed.json')
    assert inventory['qualification'] == release['qualification'] == 'UNQUALIFIED_MMD_POSED_FIXTURE_MISSING'
    assert inventory['full_suite_passed'] is False and release['full_suite_passed'] is False
    assert release['released'] is True and release['physical_jobs'] == 196
    assert inventory['normal_exit0'] == 195 and inventory['registered_cancel_exit2'] == 1
    assert len(inventory['inline_receipts']) > 0
    prior = load(OLD / 'state.json')
    assert prior['status'] == 'passed' and prior['suite_exit'] == 0 and prior['source_unchanged'] is True
    assert load(OLD / 'source-before.json') == load(OLD / 'source-after.json')
    assert inventory['result_groups'] == 157 and inventory['movie_groups'] == 20
    focused_folder = REVIEW / 'output/neon-mmd-pose-3a-attempt1'
    focused = load(focused_folder / 'verification.json')
    row, = focused['rows']
    assert focused['passed'] is True and focused['host_scopes_closed'] is True
    assert focused['all_functional_source_unchanged'] is True and focused['functional_source_files'] == 1029
    assert row['exit'] == 0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False
    assert row['report']['checks'] == 45 and row['report']['failures'] == 0
    assert row['report']['actual_mmd_tested'] is True and len(row['report']['movies']) == 2
    stage_path = ROOT / 'output/PRIVATE-neon-mmd-pose-fixture-stage-20261117/PROVENANCE.json'
    stage = load(stage_path)
    assert stage['files'] == 18 and stage['bytes'] == 2648542
    assert stage['all_originals_preserved'] is True and stage['all_copies_equal'] is True
    b = ROOT / 'output/native-normal-B-known-factory-20261117T200016977593'
    b_result = load(b / 'ROOT_RESULT.json')
    b_process = load(b / 'process.json')
    b_receipt = load(b / 'private-receipt.json')
    assert b_result['diagnostic_completed'] is False and b_result['input_source_tool_context_preserved'] is True
    assert b_result['root_fresh_scopes_closed'] is True and not any(b_result['claims'].values())
    assert b_process['exit'] == 1 and b_process['retained_Popen_reaped'] is True and b_process['timed_out'] is False
    assert b_receipt['exit'] == 1 and all(b_receipt[key] is True for key in ('job_closed', 'desktop_closed', 'child_desktop_confirmed', 'private_window_seen'))
    b_error = (b / 'PRIVATE_STDERR.log').read_text(encoding='utf-8')
    assert "AttributeError: module 'bpy' has no attribute 'blend_paths'" in b_error
    assert (b / 'PRIVATE_HANDLERS_AFTER_LOAD.json').is_file()
    pmx = ROOT / 'output/PRIVATE-pmx-observation-counts-20261117-attempt1'
    counts = load(pmx / 'PRIVATE_BATCH.json')['public_scalars']
    assert counts['completed_cases'] == counts['preserved_cases'] == counts['started_cases'] == 4
    assert counts['timed_out_cases'] == counts['unconfirmed_closure_cases'] == 0
    assert counts['all_original_copy_and_source_preserved'] is True
    diagnostics = [load(pmx / f'case-{i}/PRIVATE_COUNTS.json') for i in range(4)]
    assert [[item['table'] for item in value['observed_tables'] if not item['within_count_budget']]
            for value in diagnostics] == [['joint'], ['joint'], ['joint'], []]
    assert all(value['candidate_imported_or_run'] is False and value['original_limits_and_traversal_preserved'] is True for value in diagnostics)
    state = load(NEW / 'state.json')
    assert state['status'] == 'running' and state['source_commit'] == prior['source_commit']
    launch = load(NEW / 'launch.json')
    birth = load(NEW / 'root-birth-observation.json')
    api = load(NEW / 'root-birth-api-detail.json')
    assert launch['coordinator_pid'] == birth['coordinator']['pid'] == 21536
    assert birth['python']['pid'] == api['python_pid'] == 2976
    assert api['python_get_process_birth'] == '2026-11-17T20:07:59.1058242Z'
    assert api['python_CIM_birth'] == '2026-11-17T20:07:59.1058240Z'
    output = ROOT / 'experiments/neon_mmd_fixture_recovery_actual_20261117'
    output.mkdir(exist_ok=False)
    record = {'format': 'has_root_neon_mmd_fixture_recovery_public_1',
        'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'candidate_commit': state['source_commit'], 'functional_files': 1029,
        'prior_full': {'software_exit': 0, 'qualification': inventory['qualification'],
            'result_groups': 157, 'core_groups': 36, 'movie_groups': 20,
            'missing_key': 'posed_model_video_1', 'actual_mmd_tested': False, 'pose_checks': 37,
            'neon_checks': 12504, 'physical_jobs': 196, 'normal_exit0': 195, 'registered_Krita_cancel_exit2': 1,
            'all_owned_jobs_desktops_closed': True, 'all_functional_source_unchanged': True,
            'full_suite_passed': False, 'raw_inventory': descriptor(inventory_path)},
        'fixture_stage': {'files': 18, 'bytes': 2648542, 'originals_preserved': True,
            'copies_equal': True, 'private_provenance': descriptor(stage_path)},
        'focused_pose': {'checks': 45, 'failures': 0, 'actual_mmd_tested': True,
            'independently_probed_48_frame_movies': 2, 'seconds': row['seconds'],
            'retained_child_reaped': True, 'source_unchanged': True, 'scopes_closed': True,
            'raw_verification': descriptor(focused_folder / 'verification.json')},
        'preflight_first_refusal_preserved': 'canonical pose regenerated exactly two owned project metadata outputs; all36 Root originals and other34 Review copies remained exact',
        'preflight_second': 'passed; precisely those two generated outputs declared and preserved privately with dated canonical source provenance',
        'source_B_attempt': {'model_load_reached': True, 'after_load_factory_handler_gate_passed': True,
            'resource_diagnostic_completed': False, 'failure': 'collector used bpy.blend_paths; installed API is bpy.utils.blend_paths',
            'process_exit': 1, 'retained_process_reaped': True, 'private_job_desktop_closed': True,
            'inputs_sources_tools_preserved': True, 'scopes_closed': True, 'native_normal_fidelity': False,
            'raw_result': descriptor(b / 'ROOT_RESULT.json'), 'raw_process': descriptor(b / 'process.json'),
            'raw_stderr': descriptor(b / 'PRIVATE_STDERR.log')},
        'PMX_passive_count_diagnostic': {**counts, 'refused_joint_table_cases': 3,
            'complete_original_oracle_traversals': 1, 'numeric_counts_remain_private': True,
            'unchanged_limits_and_traversal': True, 'prefix_correctness_not_proved': True,
            'candidate_comparison_archive_simulation_or_production_adoption': False,
            'raw_batch': descriptor(pmx / 'PRIVATE_BATCH.json')},
        'fresh_full': {'run': NEW.name, 'status_at_observation': 'RUNNING',
            'coordinator_pid': 21536, 'python_pid': 2976, 'expected_result_groups': 158,
            'expected_core_groups': 36, 'expected_movie_groups': 21,
            'restored_native_pose_precondition_passed': True, 'pass_claimed': False},
        'main_merge_owner_copy_cold187_or_human_acceptance_claimed': False,
        'raw_full_native_models_counts_callbacks_and_logs_uploaded': False}
    save(output / 'RESULT.json', record)
    for name, path in (('PRIOR_SOFTWARE_STATE.json', OLD / 'state.json'),
                       ('PRIOR_UNQUALIFIED_RELEASE.json', OLD / 'graphics-lease-unqualified-closed.json'),
                       ('NEW_LAUNCH.json', NEW / 'launch.json'),
                       ('NEW_BIRTH.json', NEW / 'root-birth-observation.json'),
                       ('NEW_API_DETAIL.json', NEW / 'root-birth-api-detail.json')):
        with (output / name).open('xb') as stream: stream.write(path.read_bytes())
    rows = [{'path': path.name, **descriptor(path)} for path in sorted(output.iterdir())]
    save(output / 'INDEX.json', {'format': 'has_root_neon_mmd_recovery_public_index_1',
         'files': rows, 'full_suite_pass_claimed': False})
    print(json.dumps({'files': len(rows), 'INDEX_sha256': sha(output / 'INDEX.json'),
                     'fresh_full_status': 'RUNNING', 'full_PASS_or_merge_claimed': False}))


if __name__ == '__main__': main()
