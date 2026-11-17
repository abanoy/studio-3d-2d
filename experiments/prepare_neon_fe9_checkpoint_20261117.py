"""Select only sealed public increments and explicit dated run observations."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_checkpoint_privacy_peer_20261117
neon_375_checkpoint_remote_20261117
neon_failed_375_actual_packet_20261117
neon_source_binding_b64_fixture_20261117
neon_fe9_candidate_reconstruction_20261117
neon_fe9_candidate_reconstruction_peer_20261117
neon_fe9_preflight_refusal_20261117
neon_fe9_terminal_20261117
neon_fe9_terminal_peer_20261117
neon_foundation_fe9_actual_packet_20261117
neon_foundation_fe9_archive_recipe_20261117
neon_foundation_fe9_v2_independent_peer_20261117
neon_historical52_working_witness_20261117
neon_owner_review_after_qualified_merge_20261117
neon_owner_admission_independent_peer_20261117
neon_owner_executor_primitive_audit_20261117
neon_owner_review_executor_20261117
neon_owner_qualified_inputs_peer_20261117
neon_owner_qualified_inputs_final_peer_20261117
neon_shape_catalog_fixture_root_20261117
neon_shape_catalog_fixture_actual_inputs_20261117
neon_failed_fe9_actual_packet_20261117
neon_failed_fe9_archive_recipe_20261117
neon_failed_fe9_archive_peer_20261117
neon_00bf_candidate_reconstruction_20261117
neon_00bf_candidate_reconstruction_peer_20261117
neon_windows_00bf0f9_20261117
neon_00bf_terminal_20261117
neon_00bf_terminal_peer_20261117
neon_windows_fe9aace_20261117
remote_download_cache_cleanup_preparation_20261117
remote_download_cache_cleanup_v2_20261117
remote_download_cache_cleanup_v2_source_fix_20261117
public_cache_cleanup_actual_20261117
'''.split()
UNSEALED = {'neon_375_checkpoint_remote_20261117', 'neon_fe9_preflight_refusal_20261117', 'neon_windows_fe9aace_20261117', 'neon_shape_catalog_fixture_actual_inputs_20261117', 'neon_windows_00bf0f9_20261117'}
FILES = '''
LLM.md
docs/progress_memo.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
docs/benchmarks/public_cache_cleanup_2026-11-17.json
experiments/verify_neon_375_checkpoint_remote_20261117.py
experiments/archive_neon_375_failure_20261117.py
experiments/record_neon_375_failed_20261117.py
experiments/apply_neon_binding_fixture_20261117.py
experiments/neon_binding_fixture_root_application_20261117.json
experiments/run_neon_source_foundation_followup_20261117.py
experiments/prepare_fe9_reconstruction_20261117.py
experiments/backup_neon_fe9_candidate_20261117.py
experiments/prepare_neon_fe9_full_actual_20261117.py
experiments/record_neon_fe9_active_20261117.py
experiments/archive_public_cache_cleanup_20261117.py
experiments/record_public_cache_cleanup_20261117.py
experiments/prepare_neon_fe9_checkpoint_20261117.py
experiments/record_neon_fe9_failed_20261117.py
experiments/apply_neon_fixture_selectors_20261117.py
experiments/neon_fixture_selectors_root_application_20261117.json
experiments/run_neon_catalogue_followup_20261117.py
experiments/prepare_00bf_reconstruction_20261117.py
experiments/backup_neon_00bf_candidate_20261117.py
experiments/prepare_neon_00bf_full_actual_20261117.py
experiments/record_neon_00bf_active_20261117.py
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
    assert not name.startswith('output/') and '__pycache__' not in path.parts and path.suffix in allowed, name
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
manifest = ROOT / 'output/neon-fe9-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_fe9_checkpoint_catalogue_1', 'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'historical_running_observation_not_a_full_pass': True,
        'fe9_closed_failed_stale_Mima_descriptor': True,
        'latest00bf_dated_full_observation_not_a_pass': True,
        'closed_375_failure_preserved': True, 'exact71_public_cache_cleanup_completed': True,
        'redesign_merged': False, 'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows), 'sealed_indexes': len(indexes),
    'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
