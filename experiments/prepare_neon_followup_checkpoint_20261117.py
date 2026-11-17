"""Catalogue only completed public follow-up packets; exclude active drafts/art."""
from pathlib import Path
import gzip, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
carrier_semantic_preservation_20261117
carrier_semantic_qualification_boundary_20261117
compact_followup_archive_recipe_20261117
neon_completed_checkpoint_remote_20261117
neon_f387_terminal_20261117
neon_ffcf_terminal_20261117
neon_failed_f387_actual_packet_20261117
neon_failed_ffcf_actual_packet_20261117
neon_fix_sequence_archive_recipe_20261117
neon_workspace_fix_sequence_actual_packet_20261117
neon_focused_followup_actual_packet_20261117
neon_focused_root_archive_audit_20261117
neon_fix_sequence_root_audit_20261117
neon_lifecycle32_append_recipe_20261117
neon_world_lifecycle32_actual_packet_20261117
neon_lifecycle32_root_audit_20261117
neon_matcher_source_correction_20261117
neon_windows_ffcf4c5_20261117
neon_workspace_font_diagnosis_20261117
neon_world_font_cache_20261117
neon_world_lifecycle_integration_20261117
neon_world_lifecycle_typing_20261117
neon_world_rail_transaction_20261117
neon_world_rail_transaction_32_20261117
neon_world_teardown_actual_20261117
neon_world_teardown_fix_20261117
pmx_physics_source_gap_20261117
pmx_physics_capture_prototype_20261117
pmx_physics_capture_peer_review_20261117
pmx20_binary_layout_review_20261117
neon_archive_independent_audit_20261117
neon_ffcf_candidate_remote_20261117
native_normal_carrier_probe_20261117
'''.split()
FILES = '''
LLM.md
docs/progress_memo.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/completion_checklist.json
docs/completion_checklist.md
docs/benchmarks/neon_review_2026-11-17.json
experiments/neon_windows_original_20261116/APPLIED_SUCCESSOR.json
experiments/neon_windows_original_20261116/CANDIDATE_COMMIT.json
experiments/apply_neon_teardown_candidate_20261117.py
experiments/archive_neon_f387_failure_20261117.py
experiments/archive_neon_ffcf_failure_20261117.py
experiments/prepare_neon_ffcf4c5_full_actual_20261117.py
experiments/run_neon_workspace_followup_20261117.py
experiments/run_neon_world_lifecycle_20261117.py
experiments/run_neon_world_lifecycle_typed_20261117.py
experiments/run_neon_world_transaction32_20261117.py
experiments/verify_neon_complete_remote_20261117.py
experiments/verify_neon_focused_archive_20261117.py
experiments/audit_neon_fix_archive_root_20261117.py
experiments/audit_neon_lifecycle32_archive_root_20261117.py
experiments/record_ffcf_failed_and_fixes_20261117.py
experiments/prepare_neon_followup_checkpoint_20261117.py
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
        entries = index['files'] if 'files' in index else index['artifacts']
        entries = [dict(path=path, **row) for path, row in entries.items()] if isinstance(entries, dict) else entries
        for row in entries:
            path = folder / row['path']
            assert path.resolve().is_relative_to(folder) and not path.is_symlink()
            assert path.stat().st_size == row['bytes'] and sha(path.read_bytes()) == row['sha256'], str(path)
        indexes.append({'packet': name, 'index_sha256': sha(index_path.read_bytes()), 'checked_payloads': len(entries)})
    FILES.extend(path.relative_to(ROOT).as_posix() for path in paths)
rows = []
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.hex', '.cfg'}
for name in sorted(set(FILES)):
    path = ROOT / name
    assert path.resolve().is_relative_to(ROOT) and not path.is_symlink()
    assert not name.startswith('output/') and '__pycache__' not in path.parts and path.suffix in allowed, name
    raw = path.read_bytes()
    text = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in text
    text.decode('utf-8-sig')
    if path.suffix == '.json':
        json.loads(text)
    assert not path.name.startswith('PRIVATE_')
    rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
before = json.loads((ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json').read_bytes())
assert len(before['source_sha256']) == 1019
assert all(sha((ROOT / name).read_bytes()) == pin for name, pin in before['source_sha256'].items())
manifest = ROOT / 'output/neon-followup-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_completed_public_neon_followup_catalogue_1', 'files': rows,
               'source_indexes': indexes, 'main_functional_unchanged': 1019,
               'active_scene_and_native_reader_drafts_excluded': True,
               'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows), 'sealed_indexes': len(indexes),
                  'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
