"""Select only sealed public increments and explicit dated run observations."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_fe9_checkpoint_remote_20261117
neon_fe9_checkpoint_privacy_peer_20261117
neon_catalogue_00bf_actual_packet_20261117
neon_catalogue_00bf_archive_recipe_20261117
neon_catalogue_00bf_archive_peer_20261117
neon_catalogue_00bf_root_join_20261117
neon_owner_cold187_after_qualified_copy_20261117
pmx_import_metadata_integration_map_20261117
pmx_import_metadata_helper_boundary_20261117

successful_full_public_projection_20261117
successful_full_public_projection_certificate_20261117
neon_00bf_OS_interruptions_20261117
neon_00bf_interruption_preparation_20261117
neon_replay2_runtime_refusal_20261117
neon_replay2_runtime_identity_diagnostics_20261117
neon_windows_00bf0f9_replay2_20261117-20261117T155709412051
neon_00bf_replay2_terminal_20261117
'''.split()
UNSEALED = {'neon_catalogue_00bf_root_join_20261117', 'neon_replay2_runtime_identity_diagnostics_20261117', 'neon_00bf_OS_interruptions_20261117', 'neon_fe9_checkpoint_remote_20261117', 'neon_00bf_interruption_preparation_20261117', 'neon_windows_00bf0f9_replay2_20261117-20261117T155709412051', 'neon_replay2_runtime_refusal_20261117'}
FILES = '''
.gitignore
LLM.md
docs/progress_memo.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/RESUME_MASTER_PLAN.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
experiments/verify_neon_fe9_checkpoint_remote_20261117.py
experiments/record_neon_fe9_checkpoint_readback_20261117.py
experiments/record_neon_followup_preparation_20261117.py
experiments/prepare_neon_restart_source_checkpoint_20261117.py

experiments/observe_neon_00bf_interruption_20261117.py
experiments/record_neon_00bf_restart_authority_20261117.py
experiments/record_neon_00bf_interrupted_pickup_20261117.py
experiments/prepare_neon_00bf_full_replay2_actual_20261117.py
experiments/check_neon_00bf_full_replay2_source_20261117.py
experiments/freeze_neon_00bf_interrupted_20261117.py
experiments/test_neon_00bf_interrupted_freeze_20261117.py
experiments/neon_00bf_interrupted_freeze_20261117_summary.json
experiments/neon_00bf_interrupted_freeze_20261117_INDEX.json
experiments/capture_neon_00bf_replay2_active_20261117.py
'''.split()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
indexes = []
for name in FOLDERS:
    folder = ROOT / 'experiments' / name
    assert folder.is_dir(), name
    index_path = folder / 'INDEX.json'
    if index_path.is_file():
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
    else:
        assert name in UNSEALED, 'Unfinished source packet refused: ' + name
        paths = [p for p in folder.rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
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
manifest = ROOT / 'output/neon-restart-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_restart_source_checkpoint_catalogue_1', 'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'full_result_claimed': False,
        'preceding00bf_interrupted_by_OS_restarts': True, 'active_replay2_metadata_not_result': True,
        'strict_host_preflight_passed_without_guard_change': True,
        'closed_focused_archive_only': True, 'cold187_adapter_source_CPU_only': True,
        'PMX_integration_map_source_only': True, 'redesign_merged': False,
        'raw_successful_full_report_log_terminal_directory_excluded': True,
        'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows), 'sealed_indexes': len(indexes),
    'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
