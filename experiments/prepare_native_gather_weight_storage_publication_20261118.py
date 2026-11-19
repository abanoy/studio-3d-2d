"""ROOT later: literal gather/weight-storage followup publication.

FINAL SOURCE ONLY. Root supplied the exact document, packet, preparer and actual
scalar projection pins. The first NOT_PASS remains retained alongside the
observed finite synthetic match; no broad qualification follows.
This author does not execute this selector.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json
import subprocess
ROOT = Path(__file__).resolve().parents[1]
PARENT = '795a0af905bfbe49b99ab7335594cd6666ef91e5'
PUBLIC = 'experiments/native_gather_weight_storage_publication_20261118/MANIFEST.json'
SELF = 'experiments/prepare_native_gather_weight_storage_publication_20261118.py'
DERIVATION = 'experiments/native_gather_weight_storage_publication_selector_20261118/SOURCE_DERIVATION.json'
READY = True
ACTUAL_SCHEMA_APPROVED = True
ACTUAL_PROJECTION = 'experiments/blender_weight_storage_probe_actual_20261118/RESULT.json'
SUCCESSOR_PREPARER = 'experiments/prepare_weight_hidden_authority_20261118.py'
EXPECTED_SELECTED_FILES = 59
ACTUAL_STATUS = 'FINITE_SYNTHETIC_MATCH_WITH_PRIOR_NOT_PASS_RETAINED'
PACKETS = {
    'native_carrier_gather_binding_20261118': 'ce4e3247c920485cc3a41af8b1aed1057f5eecd3f5095e76602be102f41e82e7',
    'blender_weight_storage_probe_20261118': '31f4a7275e11883a9936b033148d3bae5638d2017fa5147b305ea6a945289adb',
    'native_point_checkpoint_remote_20261118': '8b529193a7c052db4403a784f15d9652e23a52afe59074e35a09c466b3a833ae',
    'blender_weight_storage_probe_runtime_20261118': 'e17561614cd2ec4fe5b9210b0d1062371d8c34649184752c088ecfb4ce8a70ab',
    'native_B_export_resource_plan_20261118': '3fa5c7dc3311c7173b5dffd6c30e9feb172768233ed8d9d1199012fc51166bf9',
    'blender_weight_storage_hidden_runtime_20261118': 'f8dd89c823215b8bba7e1d74ad2fa119e61aeef2d3f954b0535b57aea5623a34',
}
REQUIRED_FILES = (
    'LLM.md', 'docs/progress_memo.md', 'docs/RESUME_MASTER_PLAN.md',
    'docs/completion_checklist.json', 'docs/benchmarks/neon_review_2026-11-17.json',
    'experiments/native_B_issue_attribution_20261118/RESULT.json',
    'experiments/prepare_weight_authority_20261118.py',
)
FILE_PINS = {
    'LLM.md': '8f7866fb0c21c0142ff9937defffd5795b762fee1c5912b3cf4ea19e3959877d',
    'docs/progress_memo.md': '4c8bf937330af53891184e6e43866e866c1eb99bf6306900c38182bd933f8293',
    'docs/RESUME_MASTER_PLAN.md': 'd9a3292d2210e3f04da50cdcd6f0486f9045d7f124596106d40d64370ccf90a0',
    'docs/completion_checklist.json': 'fca01d3c84048213e8de83d9e04ea9765bd2864d14515dbdc6f78d3327f7743f',
    'docs/benchmarks/neon_review_2026-11-17.json': '151e84f3d30eb49c4b2142c9cf4f2b051d6f8c8588d070dc0017c9332894bdc6',
    'experiments/native_B_issue_attribution_20261118/RESULT.json': 'b81aa1eba8092eee603edc342a2ce4eee5686d4a85c3c72f2a97b646f930870b',
    'experiments/blender_weight_storage_probe_actual_20261118/RESULT.json': 'e33d8d240035673336cca77b51d2a501311cb477185bd6abbf0365197c286df7',
    'experiments/prepare_weight_authority_20261118.py': '7b0abaf896610003bab138cf4c8f11fcca73d16507ca880b8d5111c1d250aead',
    'experiments/prepare_weight_hidden_authority_20261118.py': '4c0425467ba7c6b3fd6c0b4ee8cd86bd4c9661d8f2237d44284d17fb2ae7dc73',
}
HISTORICAL_EOL_RECIPES = {
    'LLM.md': {'LF_newlines': 6792, 'CRLF_newline_runs': [[0, 6792]]},
    'docs/RESUME_MASTER_PLAN.md': {'LF_newlines': 1918, 'CRLF_newline_runs': [[0, 1918]]},
    'docs/progress_memo.md': {'LF_newlines': 16368, 'CRLF_newline_runs':
        [[0, 14821], [15100, 2], [15154, 43], [15292, 1], [15868, 13], [16276, 92]]},
}
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def checked_path(base, name):
    assert type(name) is str and name and '\\' not in name and ':' not in name
    relative = PurePosixPath(name)
    assert not relative.is_absolute() and all(p not in ('', '.', '..') for p in relative.parts)
    path = base / name
    assert path.resolve().is_relative_to(base.resolve()) and path.is_file(), name
    cursor = path
    while cursor != base:
        assert not cursor.is_symlink() and not getattr(cursor.lstat(), 'st_file_attributes', 0) & 0x400
        cursor = cursor.parent
    return path


assert READY is True and ACTUAL_SCHEMA_APPROVED is True, 'Root documents/runtime/actual scalar schema and literal pins are not final'
assert set(FILE_PINS) == set(REQUIRED_FILES) | {ACTUAL_PROJECTION, SUCCESSOR_PREPARER}
assert FILE_PINS['experiments/prepare_weight_authority_20261118.py'] == '7b0abaf896610003bab138cf4c8f11fcca73d16507ca880b8d5111c1d250aead'
assert SUCCESSOR_PREPARER.startswith('experiments/') and SUCCESSOR_PREPARER.endswith('.py')
assert type(EXPECTED_SELECTED_FILES) is int and EXPECTED_SELECTED_FILES > 0
assert ACTUAL_PROJECTION.startswith('experiments/') and ACTUAL_PROJECTION.endswith('/RESULT.json')
assert ACTUAL_STATUS != 'PENDING_ROOT_EXACT_OBSERVED_STATUS'
assert all(type(pin) is str and len(pin) == 64 and all(c in '0123456789abcdef' for c in pin)
           for pin in (*PACKETS.values(), *FILE_PINS.values()))
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == PARENT
assert Path(__file__).resolve() == checked_path(ROOT, SELF).resolve()
for name, pin in FILE_PINS.items():
    assert sha(checked_path(ROOT, name).read_bytes()) == pin, name
names = [*FILE_PINS, SELF, DERIVATION]
indexes = []
for folder_name, pin in PACKETS.items():
    assert '/' not in folder_name and '\\' not in folder_name and not folder_name.lower().startswith('private')
    folder = ROOT / 'experiments' / folder_name
    index = checked_path(ROOT, f'experiments/{folder_name}/INDEX.json')
    raw = index.read_bytes()
    assert sha(raw) == pin
    value = json.loads(raw)
    keys = [key for key in ('files', 'payloads', 'artifacts') if key in value]
    assert len(keys) == 1
    entries = value[keys[0]]
    entries = [dict(path=name, **row) for name, row in entries.items()] if type(entries) is dict else entries
    entries = entries + value.get('objects', [])
    members = [row['path'] for row in entries]
    assert len(members) == len(set(members)) and 'INDEX.json' not in members
    assert all('/' not in name and '\\' not in name for name in members)
    assert {p.name for p in folder.iterdir()} == {'INDEX.json', *members}
    for row in entries:
        data = checked_path(folder, row['path']).read_bytes()
        assert type(row['bytes']) is int and len(data) == row['bytes'] and sha(data) == row['sha256']
        if 'decoded_sha256' in row:
            decoded = gzip.decompress(data)
            assert len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256']
    names.extend(f'experiments/{folder_name}/{name}' for name in ('INDEX.json', *members))
    indexes.append({'packet': folder_name, 'index_sha256': pin, 'checked_payloads': len(entries)})
assert len(names) == len(set(names)) == EXPECTED_SELECTED_FILES - 1 and PUBLIC not in names
rows = []
for name in sorted(names):
    parts = PurePosixPath(name).parts
    assert parts[0] in ('experiments', 'docs') or name == 'LLM.md'
    assert not any(p.casefold() in ('output', '.git', '.godot', '__pycache__', 'terminal-audit', 'receipt-logs')
                   or p.casefold().startswith('private') or 'remote-batch' in p.casefold() for p in parts)
    path = checked_path(ROOT, name)
    assert path.suffix in ('.py', '.json', '.md')
    raw = path.read_bytes()
    decoded = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in decoded
    decoded.decode('utf-8-sig')
    if path.suffix == '.json':
        json.loads(decoded)
    rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})

# Raw functional guard: only the already-public immutable3a source-before map.
baseline_relative = 'experiments/neon_windows_3a3701a_20261117/active-observation/source-before.json'
baseline_raw = checked_path(ROOT, baseline_relative).read_bytes()
assert sha(baseline_raw) == '3ef2e7d8bed6e063afef59c8caccba914663752998761350c882fd4efbc78e9d'
baseline = json.loads(baseline_raw)
assert baseline['commit'] == '3a3701ab6edfa81dc883759403c170b8555aab07'
source_map = baseline['source_sha256']; assert type(source_map) is dict and len(source_map) == 1029
scope_names = {p.relative_to(ROOT).as_posix() for folder in ('src', 'tests', 'tools', 'data', 'examples')
               for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts}
scope_names.update(('project.godot', 'main.tscn', 'run.py', 'launch.pyw'))
assert scope_names == set(source_map), 'Main functional membership differs from tested1029'
assert all(type(pin) is str and len(pin) == 64 and sha(checked_path(ROOT, name).read_bytes()) == pin
           for name, pin in source_map.items()), 'Main raw bytes differ from qualified candidate'
source_map_sha = sha(json.dumps(source_map, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode())

# Preserve the exact independently retrieved57-file checkpoint as one closed
# three-file proof packet; do not reselect/repack its old57 source members.
remote = json.loads(checked_path(ROOT, 'experiments/native_point_checkpoint_remote_20261118/COMPLETE_READBACK.json').read_bytes())
assert remote['commit'] == remote['main_reference_verified_commit'] == PARENT
assert remote['parent'] == 'c9a4489d1998b19f14c7d0c54e018b6cbfd4db51'
assert len(remote['files']) == remote['actual_remote_files'] == 57
assert remote['git_bytes'] == 2859111 and remote['working_bytes'] == 2882793
assert remote['temporary_response_data_removed'] is True and remote['raw_private_assets_included'] is False
assert len({row['path'] for row in remote['files']}) == 57
assert all(row['remote_sha256'] == row['sha256'] for row in remote['files'])
assert {row['path']: row['EOL_recipe'] for row in remote['files'] if 'EOL_recipe' in row} == HISTORICAL_EOL_RECIPES
issue = json.loads(checked_path(ROOT, 'experiments/native_B_issue_attribution_20261118/RESULT.json').read_bytes())
assert issue['original_resource_status'] == 'RESOURCE_PROFILE_REFUSED' and issue['original_total_issues'] == 6
assert issue['non_image_issue_rows'] == 2 and len(issue['image_issue_rows']) == 4
assert issue['original_private_body_unchanged'] is True
assert all(issue[key] is False for key in ('original_six_issues_or_resource_decision_changed', 'new_native_process_or_export',
    'resource_exclusion_or_acceptance_qualified', 'raw_private_paths_names_pointers_images_arrays_included',
    'normal_fidelity_export_repair_or_adoption_qualified'))
actual = json.loads(checked_path(ROOT, ACTUAL_PROJECTION).read_bytes())
assert actual['format'] == 'has_actual_finite_weight_probe_attempts_projection_1'
assert actual['metadata_head'] == PARENT and actual['overall_status'] == ACTUAL_STATUS
assert actual['attempt_count'] == len(actual['attempts']) == 2 and actual['prior_not_pass_attempts_retained'] == 1
assert actual['first_attempt_projection_sha256'] == '740439b9e14bba7567773176abf453507938341981268edcfb227b55ba2db2bf'
assert actual['hidden_preparer_source_sha256'] == FILE_PINS[SUCCESSOR_PREPARER]
assert actual['original_probe_and_runtime_packets_preserved'] is True
assert actual['native_model_files_opened_or_SourceIO_import_or_export'] is False
assert actual['normal_repair_native_source_policy_fidelity_or_adoption_qualified'] is False
first, second = actual['attempts']
assert first['overall_status'] == first['root_result']['status'] == 'NOT_PASS'
assert first['reason'] == 'BACKGROUND_PRIVATE_DESKTOP_PLACEMENT_UNCONFIRMED'
assert first['root_result']['runtime_packet_sha256'] == PACKETS['blender_weight_storage_probe_runtime_20261118']
assert first['root_result']['process']['exit'] == first['receipt_observation']['exit'] == 2
assert first['receipt_observation']['private_window_seen'] is False and first['receipt_observation']['child_desktop_confirmed'] is False
assert first['root_result']['background_receipt'] == {} and first['root_result']['error_type'] == 'ValueError'
assert first['finite_case_report_independently_validated_readonly'] is True
assert second['overall_status'] == second['root_result']['status'] == 'FINITE_SYNTHETIC_MATCH'
assert second['root_result']['runtime_packet_sha256'] == PACKETS['blender_weight_storage_hidden_runtime_20261118']
assert second['finite_case_report_and_receipt_independently_validated_readonly'] is True
for attempt in (first, second):
    result = attempt['root_result']; observation = result['observation']; process = result['process']; receipt = attempt['receipt_observation']
    assert result['metadata_head'] == PARENT and result['probe_packet_sha256'] == PACKETS['blender_weight_storage_probe_20261118']
    assert result['report_sha256'] == attempt['native_public_report_sha256']
    assert result['source_tool_authority_preserved'] is True
    assert result['main_review_scopes_zero_before'] is True and result['main_review_scopes_zero_after'] is True
    assert process['retained_Popen_reaped'] is True and process['timed_out'] is False and process['streams_within_acceptance_cap'] is True
    assert receipt['foreground_child_observed'] is False and receipt['desktop_switch_requested'] is False
    assert receipt['job_closed'] is True and receipt['desktop_closed'] is True
    assert observation['observation_status'] == 'BOUNDED_SYNTHETIC_STORAGE_MATCH' and observation['finite_cases'] == 21952
    assert set(observation['phases']) == {'immediate', 'after_validate'} and observation['immediate_vs_after_validate_exact'] is True
    for phase in observation['phases'].values():
        assert phase['mismatch_cases'] == phase['extra_observed_rows'] == 0 and phase['all_cases_match'] is True
        assert phase['mismatch_counts'] == {'row_missing': 0, 'ordered_group_relation': 0, 'weight_word': 0}
        assert phase['expected_ordered_rows_sha256'] == phase['observed_ordered_rows_sha256'] == 'bc2fddb6944b1cb6fd4ab3933901fe7eb0bcedf840fbed8cf4e62c10609af0ca'
    assert all(observation[key] is False for key in ('native_storage_rule_qualified', 'universal_or_actual_source_policy_qualified', 'native_fidelity_export_repair_adoption_qualified'))
    assert all(result[key] is False for key in ('model_or_native_asset_inputs', 'SourceIO_import_or_export', 'native_storage_rule_qualified',
        'universal_group_or_F32_domain_qualified', 'actual_source_rows_or_saved_scene_qualified', 'native_fidelity_export_repair_adoption_qualified'))
result = second['root_result']; receipt = second['receipt_observation']; background = result['background_receipt']; host = result['host_placement']
assert result['process']['exit'] == receipt['exit'] == background['child_exit'] == 0 and result['error_type'] is None
assert receipt['private_window_seen'] is True and receipt['child_desktop_confirmed'] is True
assert background['background_private_desktop_confirmed'] is True and background['private_window_seen'] is True
assert background['visible_window_required'] is False and background['hidden_owned_window_required'] is True
assert host['hidden_host_placement_complete'] is True and host['probe_return_code'] == 0
assert host['host_hidden_window_API_called'] is True and host['unchanged_probe_window_or_desktop_API_called'] is False
assert host['native_storage_rule_qualified'] is False
placement = host['placement']
assert placement['format'] == 'has_hidden_background_desktop_placement_sentinel_1'
assert placement['class'] == 'STATIC' and placement['requested_size_pixels'] == [0, 0]
assert all(placement[key] is True for key in ('disabled', 'noactivate_style', 'toolwindow_style', 'owned_pid_and_thread_verified', 'destroyed_in_finally'))
assert all(placement[key] is False for key in ('visible_at_creation', 'visible_before_destruction', 'show_or_activation_calls', 'thread_desktop_switch_calls'))
assert host['host_source_identities'] == {
    'weight_storage_host.py': {'bytes': 11375, 'sha256': 'c384f0210e1dfeb8196714e4381df8b2e8bcc5199d45c691a9e6d8addf4ba421'},
    'placement_sentinel.py': {'bytes': 4387, 'sha256': 'e42fa44efa599851396c517fa0b4bc90a692efb1f911517fa3d748879d1462c2'}}
manifest = {
    'format': 'has_public_gather_weight_storage_followup_manifest_1',
    'metadata_parent_HEAD_at_preparation': PARENT, 'files': rows, 'source_indexes': indexes,
    'main_functional_matches_qualified_candidate': 1029,
    'qualified_functional_source_commit': baseline['commit'],
    'qualified_functional_raw_map_sha256': source_map_sha,
    'public_functional_guard': {'path': baseline_relative, 'sha256': sha(baseline_raw)},
    'previous_checkpoint_independent_readback_files': 57,
    'previous_checkpoint_reversible_document_EOL_recipes': 3,
    'old57_source_files_repacked': False,
    'original_resource_status': 'RESOURCE_PROFILE_REFUSED', 'original_resource_issues': 6,
    'synthetic_native_scalar_observation_status': actual['overall_status'],
    'actual_synthetic_status_assumed_to_pass': False,
    'prior_NOT_PASS_attempts_retained': 1,
    'finite_synthetic_cases_per_phase': 21952,
    'finite_synthetic_phases': ['immediate', 'after_validate'],
    'second_attempt_hidden_background_placement_confirmed': True,
    'hidden_placement_is_not_a_Blender_GUI_or_render_claim': True,
    'B_export_resource_plan_is_conditional_source_only': True,
    'native_fixture_expected_adapter_weight_order_normal_fidelity_export_or_adoption_qualified': False,
    'owner_copy_or_cold187_changed_by_this_publication': False,
    'human_acceptance': 'DEFERRED',
    'raw_private_models_native_outputs_arrays_receipts_logs_caches_old57_source_files_excluded': True,
}
raw = (json.dumps(manifest, indent=2) + '\n').encode()
target = ROOT / 'output/native-gather-weight-storage-publication-20261118-manifest.json'
public = ROOT / PUBLIC
path_list = ROOT / 'output/native-gather-weight-storage-publication-20261118-paths.nul'
assert not target.exists() and not public.parent.exists() and not path_list.exists()
with target.open('xb') as stream: stream.write(raw)
public.parent.mkdir(exist_ok=False)
with public.open('xb') as stream: stream.write(raw)
paths = [row['path'] for row in rows] + [PUBLIC]
assert len(paths) == EXPECTED_SELECTED_FILES
with path_list.open('xb') as stream: stream.write(b''.join(name.encode() + b'\0' for name in paths))
print(json.dumps({'selected_files': len(paths), 'working_bytes': sum(row['bytes'] for row in rows) + len(raw),
                  'manifest_sha256': sha(raw), 'path_list_sha256': sha(path_list.read_bytes()),
                  'source_functional_files_unchanged': 1029}))
