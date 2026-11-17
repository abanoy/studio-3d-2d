"""Catalogue completed public packets plus an explicitly dated active observation."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_4ed3_terminal_20261117
neon_4ed3_terminal_peer_20261117
neon_4ed_candidate_remote_20261117
neon_followup_checkpoint_remote_20261117
neon_scene_mask_diagnostic_20261117
neon_scene_view106_actual_20261117
neon_scene_view_mask_fixture_20261117
neon_windows_4ed3a63_20261117
pmx_physics_native_reader_prototype_20261117
neon_scene106_actual_packet_20261117
neon_scene106_archive_recipe_20261117
neon_failed_4ed_actual_packet_20261117
pmx_native_read_qualification_protocol_20261117
neon_helper_preview_manifest_20261117
neon_helper_manifest_independent_peer_20261117
neon_failed_4ed_independent_audit_20261117
neon_375_candidate_reconstruction_20261117
neon_375_candidate_reconstruction_peer_20261117
neon_windows_375ec05_20261117
native_normal_resource_survey_20261117
neon_375_terminal_20261117
neon_375_terminal_final_peer_20261117
neon_375_terminal_independent_peer_20261117
neon_helper375_actual_packet_20261117
neon_helper375_archive_recipe_20261117
'''.split()
FILES = '''
LLM.md
docs/progress_memo.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
experiments/prepare_neon_4ed3a63_full_actual_20261117.py
experiments/run_neon_scene_followup_20261117.py
experiments/verify_neon_followup_remote_20261117.py
experiments/verify_neon_4ed_remote_20261117.py
experiments/record_neon_4ed_active_20261117.py
experiments/prepare_neon_4ed_checkpoint_20261117.py
experiments/archive_neon_4ed_failure_20261117.py
experiments/record_neon_4ed_failed_20261117.py
experiments/run_neon_helper_followup_20261117.py
experiments/apply_neon_helper_manifest_20261117.py
experiments/neon_helper_manifest_root_application_20261117.json
experiments/backup_neon_375_candidate_20261117.py
experiments/prepare_neon_375ec05_full_actual_20261117.py
experiments/record_neon_375_active_20261117.py
experiments/record_main_publication_authority_20261117.py
experiments/neon_main_publication_scope_20261117.json
'''.split()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
indexes = []
for name in FOLDERS:
    folder = ROOT / 'experiments' / name
    assert folder.is_dir(), name
    paths = [p for p in folder.rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
    index_path = folder / 'INDEX.json'
    if index_path.is_file():
        index = json.loads(index_path.read_bytes())
        keys = [key for key in ('files', 'artifacts', 'payloads') if key in index]
        assert len(keys) == 1, (name, keys)
        entries = index[keys[0]]
        entries = [dict(path=path, **row) for path, row in entries.items()] if isinstance(entries, dict) else entries
        entries = entries + index.get('objects', [])
        for row in entries:
            path = folder / row['path']
            assert path.resolve().is_relative_to(folder) and not path.is_symlink()
            raw = path.read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
            if 'decoded_sha256' in row:
                decoded = gzip.decompress(raw)
                assert len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256']
        indexes.append({'packet': name, 'index_sha256': sha(index_path.read_bytes()), 'checked_payloads': len(entries)})
        # Publish declared payloads only; retain unlisted local CPU scratch.
        paths = [index_path] + [folder / row['path'] for row in entries]
    FILES.extend(path.relative_to(ROOT).as_posix() for path in paths)
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
manifest = ROOT / 'output/neon-4ed-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_4ed_checkpoint_catalogue_1', 'files': rows,
               'source_indexes': indexes, 'main_functional_unchanged': 1019,
               'historical_running_observation_included_not_a_pass': True,
               'preceding_4ed_full_failed_helper_review_manifest': True,
               'latest375_full_running_at_dated_observation_not_a_pass': True,
               'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows), 'sealed_indexes': len(indexes),
                  'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
