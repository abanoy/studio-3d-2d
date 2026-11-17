"""UNRUN source selector for root review; execute only when root approves a freeze."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
# Next increment only. Reconstruction peer is closed and remains INDEX-only.
FOLDERS = '''
neon_restart_source_checkpoint_remote_20261117
neon_00bf_source_checkpoint_privacy_peer_20261117
neon_owner_activation_successor_source_20261117
neon_source52_to_00bf_delta_draft_20261117
neon_source52_to_00bf_root_review_20261117
neon_camera_details_visibility_proposal_20261117
neon_696_candidate_reconstruction_20261117
neon_696_candidate_reconstruction_peer_20261117
neon_696_terminal_20261117
neon_696_full_preflight_source_20261117
neon_windows_696ca7f_20261117
neon_replay2_camera_failure_20261117
native_normal_resource_diagnostic_20261117
native_normal_resource_diagnostic_failed_full_20261117
native_normal_resource_diagnostic_import_fix_20261117
native_normal_factory_handler_capture_20261117
native_normal_factory_handler_baseline_20261117
'''.split()
# Dated public scalar/snapshot exceptions are literal files, never recursive discovery.
UNSEALED = {
    'neon_restart_source_checkpoint_remote_20261117': ('ROOT_OBSERVATION.json', 'COMPLETE_READBACK.json'),
    'neon_windows_696ca7f_20261117': (
        'PREPARATION.json', 'active-observation/OBSERVATION.json',
        'active-observation/launch.json', 'active-observation/root-birth-observation.json',
        'active-observation/root-birth-api-detail.json', 'active-observation/source-before.json',
        'active-observation/preflight-source.json', 'active-observation/state.json'),
    'neon_replay2_camera_failure_20261117': ('OBSERVATION.json',),
}
# This flat source seal names only these two scripts. It cannot nominate arbitrary files.
FLAT_SEALS = {'neon_696_full_preflight_source_20261117': (
    'experiments/prepare_neon_696_full_actual_20261117.py',
    'experiments/check_neon_696_full_source_20261117.py')}
FILES = '''
.gitignore
LLM.md
docs/progress_memo.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/RESUME_MASTER_PLAN.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
experiments/prepare_neon_camera_checkpoint_20261117.py
experiments/apply_neon_camera_visibility_20261117.py
experiments/backup_neon_696_candidate_20261117.py
experiments/check_neon_696_full_source_20261117.py
experiments/prepare_neon_696_full_actual_20261117.py
experiments/run_neon_camera_visibility_followup_20261117.py
experiments/record_neon_696_active_20261117.py
experiments/record_neon_replay2_camera_failure_20261117.py
experiments/record_neon_restart_source_checkpoint_readback_20261117.py
experiments/verify_neon_restart_source_checkpoint_remote_20261117.py
experiments/run_B_resource_diagnostic_root_20261117.py
experiments/prepare_B_resource_diagnostic_root_attempt2_20261117.py
experiments/prepare_B_resource_diagnostic_root_attempt3_20261117.py
experiments/prepare_B_factory_handler_capture_attempt4_20261117.py
experiments/neon_camera_visibility_root_application_20261117.json
experiments/native_B_diagnostic_actual_scalars_20261117/OBSERVATIONS.json
'''.split()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
indexes = []
for name in FOLDERS:
    folder = ROOT / 'experiments' / name
    assert folder.is_dir(), name
    index_path = folder / 'INDEX.json'
    if name in UNSEALED:
        paths = [folder / item for item in UNSEALED[name]]
        assert all(path.is_file() and path.suffix == '.json' for path in paths)
    elif name in FLAT_SEALS:
        seal_path = folder / 'SOURCE_SEAL.json'
        seal = json.loads(seal_path.read_bytes())
        assert seal['format'] == 'has_neon696_full_preflight_source_seal_1'
        entries = seal['source_files']
        assert len(entries) == len(FLAT_SEALS[name]) and {row['ROOT_relative_path'] for row in entries} == set(FLAT_SEALS[name])
        for row in entries:
            path = ROOT / row['ROOT_relative_path']
            assert path.resolve().is_relative_to(ROOT / 'experiments') and not path.is_symlink()
            raw = path.read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
        paths = [seal_path] + [ROOT / item for item in FLAT_SEALS[name]]
    else:
        assert index_path.is_file(), 'Unfinished source packet refused: ' + name
        doc = json.loads(index_path.read_bytes())
        keys = [key for key in ('files', 'artifacts', 'payloads') if key in doc]
        assert len(keys) == 1, (name, keys)
        entries = doc[keys[0]]
        entries = [dict(path=path, **row) for path, row in entries.items()] if isinstance(entries, dict) else entries
        entries = entries + doc.get('objects', [])
        for row in entries:
            path = folder / row['path']
            assert path.resolve().is_relative_to(folder) and not path.is_symlink()
            raw = path.read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
            if 'decoded_sha256' in row:
                decoded = gzip.decompress(raw)
                assert len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256']
        paths = [index_path] + [folder / row['path'] for row in entries]
        indexes.append({'packet': name, 'index_sha256': sha(index_path.read_bytes()), 'checked_payloads': len(entries)})
    FILES.extend(p.relative_to(ROOT).as_posix() for p in paths)
rows = []
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.hex', '.cfg'}
for name in sorted(set(FILES)):
    path = ROOT / name
    assert path.resolve().is_relative_to(ROOT) and not path.is_symlink()
    assert not name.startswith('output/') and '__pycache__' not in path.parts and (path.suffix in allowed or name == '.gitignore'), name
    raw = path.read_bytes()
    content = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in content
    content.decode('utf-8-sig')
    if path.suffix == '.json':
        json.loads(content)
    assert not path.name.startswith('PRIVATE_')
    rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
before = json.loads((ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json').read_bytes())
assert len(before['source_sha256']) == 1019
assert all(sha((ROOT / name).read_bytes()) == pin for name, pin in before['source_sha256'].items())
manifest = ROOT / 'output/neon-camera-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_camera_source_checkpoint_catalogue_1', 'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'full_result_claimed': False,
        'preceding00bf_replay2_closed_failed_camera': True, 'active696_metadata_not_result': True,
        'camera_visibility_focused_actual_passed': True,
        'actual_focused_checks': {'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48},
        'native_fidelity_or_material_acceptance_claimed': False,
        'native_diagnostic_source_and_scalar_metadata_only': True,
        'owner_activation_renderer_source_CPU_only': True, 'source_delta_review_is_not_full_or_merge_activation': True,
        'redesign_merged': False, 'raw_full_reports_logs_phase_receipt_arrays_excluded': True,
        'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows), 'sealed_indexes': len(indexes),
    'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
