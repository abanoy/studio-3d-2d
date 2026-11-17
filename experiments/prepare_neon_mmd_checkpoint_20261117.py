"""Exact public MMD-recovery/source checkpoint; no selected source is executed.

The qualified52 Main1019 guard is retained from cleanup85 selector f1832e77.
Only literal files and closed pinned INDEX members are selected. Active run state,
logs, reports, native inputs, private callbacks and raw PMX counts are excluded.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_3a_unqualified_mmd_terminal_20261117
neon_3a_mmd_terminal_20261117
native_normal_blender51_resource_api_fix_20261117
pmx_count_root_driver_20261117
neon_3a_postpass_commands_20261117
neon_mmd_fixture_recovery_actual_20261117
native_normal_known_factory_blender51_resource_20261117
native_normal_known_factory_blender51_binding_20261117
neon_cleanup85_source_checkpoint_remote_20261117
neon_windows_3a3701a_mmd_20261117
'''.split()
FOLDER_INDEX_SHA256 = {
    'neon_3a_unqualified_mmd_terminal_20261117': 'dcc4e096b1c6bb387529a7e6fe54e13d22c32aa3c15533103583ae0c210fa4cd',
    'neon_3a_mmd_terminal_20261117': 'f223587f75cb56281b961679fecb399672025216c1b0f23f5cebee20cdc38d6b',
    'native_normal_blender51_resource_api_fix_20261117': '9f8e24d0053d920dcdb7a5f5560a37ee0b493aa63351dc95e478435e95685369',
    'pmx_count_root_driver_20261117': '6bcf8cb52f7763689cc69bc9256e4287afe8cdb94b68c095f20de848a93048dd',
    'neon_3a_postpass_commands_20261117': '2db8aec2082a9f2aa58a0a35966b3b5b4d14e4babb0945d67614898ff44cf9f2',
    'neon_mmd_fixture_recovery_actual_20261117': 'e9fc98b5a55e8ec7bf170d513919e8d4498e7aa616b633cd9f2f486c7408c78b',
    'native_normal_known_factory_blender51_resource_20261117': '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0',
    'native_normal_known_factory_blender51_binding_20261117': 'eacc7b33245e33fd7e4826f17dda6cd95917bb7034537d1145c88a4320a7bfa4',
}
UNSEALED = {
    'neon_cleanup85_source_checkpoint_remote_20261117': ('COMPLETE_READBACK.json', 'COMMIT_STATE_ACCOUNTING.json'),
    'neon_windows_3a3701a_mmd_20261117': ('PREPARATION.json', 'LAUNCHER_SOURCE_DERIVATION.json'),
}
FILE_PINS = {
    'experiments/neon_cleanup85_source_checkpoint_remote_20261117/COMPLETE_READBACK.json': (356988, 'e7518d5de22fb7555a0834cea98a68940cb518d68eb593b5451ca12740c6ac02'),
    'experiments/neon_cleanup85_source_checkpoint_remote_20261117/COMMIT_STATE_ACCOUNTING.json': (1574, '6d0b114a12887223379202c2f437cfefe2a6a0be42d168a957a0ecacd99f36d2'),
    'experiments/neon_windows_3a3701a_mmd_20261117/PREPARATION.json': (14553, '7f0ce5605b7a03d9faba2315e718b7357d1972d1020861c360c3e985f13e4574'),
    'experiments/neon_windows_3a3701a_mmd_20261117/LAUNCHER_SOURCE_DERIVATION.json': (452, 'ba7e99c22dc849ba6972d306fbb1ec7990ed73a67b82a58025c7ce0f72626243'),
}
FILES = '''
LLM.md
docs/progress_memo.md
docs/RESUME_MASTER_PLAN.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
experiments/prepare_neon_mmd_checkpoint_20261117.py
experiments/verify_neon_cleanup85_source_checkpoint_remote_20261117.py
experiments/stage_neon_mmd_pose_fixture_20261117.py
experiments/neon_mmd_pose_check_20261117.py
experiments/run_neon_mmd_pose_20261117.py
experiments/prepare_neon_3a_mmd_full_20261117.py
experiments/launch_neon_3a_mmd_full_20261117.ps1
experiments/record_neon_mmd_recovery_actual_20261117.py
experiments/update_neon_mmd_checkpoint_docs_20261117.py
'''.split()
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def checked_path(base, name):
    assert type(name) is str and name and '\\' not in name, name
    relative = PurePosixPath(name)
    assert not relative.is_absolute() and all(part not in ('', '.', '..') for part in relative.parts), name
    path = base / name
    assert path.resolve().is_relative_to(base.resolve()) and path.is_file(), name
    cursor = path
    while cursor != base:
        assert not cursor.is_symlink() and not getattr(cursor.lstat(), 'st_file_attributes', 0) & 0x400, str(cursor)
        cursor = cursor.parent
    return path


assert len(FOLDERS) == len(set(FOLDERS)) and len(FILES) == len(set(FILES))
assert set(FOLDERS) == set(FOLDER_INDEX_SHA256) | set(UNSEALED)
assert not set(FOLDER_INDEX_SHA256) & set(UNSEALED)
indexes = []
for name in FOLDERS:
    folder = ROOT / 'experiments' / name
    assert folder.is_dir() and not folder.is_symlink(), name
    if name in UNSEALED:
        paths = [checked_path(folder, item) for item in UNSEALED[name]]
        for path in paths:
            relative = path.relative_to(ROOT).as_posix(); raw = path.read_bytes()
            assert path.suffix == '.json' and (len(raw), sha(raw)) == FILE_PINS[relative], relative
    else:
        index_path = checked_path(folder, 'INDEX.json'); index_raw = index_path.read_bytes()
        assert sha(index_raw) == FOLDER_INDEX_SHA256[name], name
        doc = json.loads(index_raw)
        keys = [key for key in ('files', 'artifacts', 'payloads') if key in doc]
        assert len(keys) == 1, (name, keys)
        entries = doc[keys[0]]
        entries = [dict(path=path, **row) for path, row in entries.items()] if isinstance(entries, dict) else entries
        entries = entries + doc.get('objects', [])
        names = [row['path'] for row in entries]
        assert len(names) == len(set(names)) and 'INDEX.json' not in names, name
        # These eight explicitly named packets are flat and closed; no recursion.
        assert all('/' not in item for item in names), name
        assert {item.name for item in folder.iterdir()} == {'INDEX.json', *names}, name
        for row in entries:
            path = checked_path(folder, row['path']); raw = path.read_bytes()
            assert type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
            if 'decoded_sha256' in row:
                decoded = gzip.decompress(raw)
                assert len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256'], str(path)
        paths = [index_path] + [checked_path(folder, row['path']) for row in entries]
        indexes.append({'packet': name, 'index_sha256': sha(index_raw), 'checked_payloads': len(entries)})
    FILES.extend(path.relative_to(ROOT).as_posix() for path in paths)
assert len(FILES) == len(set(FILES)), 'Overlapping literal/indexed selection'

rows = []
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.cfg'}
for name in sorted(FILES):
    path = checked_path(ROOT, name)
    parts = [part.casefold() for part in PurePosixPath(name).parts]
    assert parts[0] != 'output' and '__pycache__' not in parts, name
    assert not any(part.startswith('private') or part in ('terminal-audit', 'canonical', 'receipt-logs') for part in parts), name
    assert path.suffix in allowed, name
    raw = path.read_bytes(); content = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in content, name
    content.decode('utf-8-sig')
    if path.suffix == '.json': json.loads(content)
    rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})

# Main source identity comes only from the already-public qualified52 archive.
baseline_folder = ROOT / 'experiments/native_five_full_actual_20261116'
baseline_index_raw = checked_path(baseline_folder, 'INDEX.json').read_bytes()
assert sha(baseline_index_raw) == '757146330ae801d5a2bd11d2f9b594babd665c64291f61f33b0115f048cedd1e'
baseline_index = json.loads(baseline_index_raw)
baseline_path = 'run/source-before.json.gz'
baseline_row = next(row for row in baseline_index['files'] if row['path'] == baseline_path)
baseline_raw = checked_path(baseline_folder, baseline_path).read_bytes()
assert len(baseline_raw) == baseline_row['bytes'] and sha(baseline_raw) == baseline_row['sha256'] == '0ff288cd27a5aaf6230a4cec798c2555371506e072864e8545492a291d5c2512'
state_row = next(row for row in baseline_index['files'] if row['path'] == 'run/state.json')
state_raw = checked_path(baseline_folder, state_row['path']).read_bytes()
assert len(state_raw) == state_row['bytes'] and sha(state_raw) == state_row['sha256']
state = json.loads(state_raw)
assert state['source_commit'] == '52f63c944ded7a651da871524d23a345b606424d'
assert state['status'] == 'passed' and state['source_unchanged'] is True
assert type(state['suite_exit']) is int and state['suite_exit'] == 0
source_map = json.loads(gzip.decompress(baseline_raw))['source_sha256']
assert len(source_map) == 1019
assert all(sha(checked_path(ROOT, name).read_bytes()) == pin for name, pin in source_map.items())

actual = json.loads(checked_path(ROOT, 'experiments/neon_mmd_fixture_recovery_actual_20261117/RESULT.json').read_bytes())
assert actual['prior_full']['full_suite_passed'] is False
assert actual['prior_full']['qualification'] == 'UNQUALIFIED_MMD_POSED_FIXTURE_MISSING'
assert actual['prior_full']['missing_key'] == 'posed_model_video_1' and actual['prior_full']['actual_mmd_tested'] is False
assert actual['fresh_full']['status_at_observation'] == 'RUNNING' and actual['fresh_full']['pass_claimed'] is False
assert actual['main_merge_owner_copy_cold187_or_human_acceptance_claimed'] is False
assert actual['raw_full_native_models_counts_callbacks_and_logs_uploaded'] is False
assert actual['PMX_passive_count_diagnostic']['numeric_counts_remain_private'] is True

manifest = ROOT / 'output/neon-mmd-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_mmd_source_checkpoint_catalogue_1',
        'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'main_functional_source_commit': state['source_commit'],
        'preceding_public_metadata_checkpoint': '265d3030b848b37f01036dd356840269fca9475b',
        'review_source_commit': '3a3701ab6edfa81dc883759403c170b8555aab07',
        'full_result_claimed': False, 'redesign_merged': False,
        'owner_copy_builder_or_cold187_activated': False,
        'prior157_group_run_closed_unqualified': True,
        'restored_pose_focus_is_not_full_qualification': True,
        'current_full_status_reference': 'ROOT_REPORTED_RUNNING_NOT_OBSERVED_BY_SELECTOR',
        'strict158_registry_and_actual_MMD_gates_unchanged': True,
        'expected_counts_are_not_actual_results': True,
        'new_Blender51_resource_API_runtime_and_binder_source_only': True,
        'raw_full_reports_logs_receipts_native_counts_and_callbacks_excluded': True,
        'private_native_art_arrays_media_excluded': True,
        'native_fidelity_material_acceptance_or_simulation_claimed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'sealed_indexes': len(indexes), 'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
