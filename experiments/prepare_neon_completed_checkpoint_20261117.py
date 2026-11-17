"""Catalogue explicit completed public source/evidence; never stage generated media."""
from pathlib import Path
import gzip, hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_redesign_review_20261116
neon_redesign_geometry_review_20261116
neon_redesign_geometry_successor_20261116
neon_redesign_refresh_fixture_20261116
neon_redesign_refresh_boundary_v3_20261116
neon_workspace_suite_integration_20261117
neon_timeline_fixture_audit_20261117
neon_timeline_fixture_followup_20261117
neon_movement_fixture_managed_raster_20261117
neon_waveform_palette_successor_20261117
neon_waveform_diagnostic_20261117
neon_waveform_aa_successor_20261117
normal_setter_boundary_sentinel_20261117
normal_setter_actual_driver_20261117
native_normal_carrier_strategy_20261117
neon_actual_review_archive_recipe_20261116
neon_actual_review_archive_recipe_v2_20261116
neon_actual_review_packet_20261117
neon_review_root_archive_audit_20261117
neon_failed_381_terminal_20261117
setter_and_failed381_archive_recipes_20261117
normal_setter_actual_packet_20261117
neon_failed_381_actual_packet_20261117
setter_failed381_root_archive_audit_20261117
neon_checkpoint_remote_readback_20261117
neon_windows_candidate_20261117
neon_windows_f387d0e_20261117
six_foot_domain_host_actual_20261116
'''.split()
OPERATIONS = '''
apply_neon_review_fixes_20261116.py
audit_neon_original_closed_20261116.py
commit_finished_metadata_20261116.py
commit_neon_fixture_followup_20261117.py
prepare_neon_behavior_candidate_20261116.py
prepare_neon_candidate_commit_20261116.py
prepare_neon_channel_fixture_20261117.py
prepare_neon_f387_full_20261117.py
prepare_neon_f387_full_actual_20261117.py
prepare_neon_full_candidate_20261117.py
prepare_neon_refresh_drivers_20261116.py
prepare_neon_refresh_v3_driver_20261116.py
prepare_neon_timeline_runner_v2_20261117.py
prepare_neon_waveform_aa_runner_20261117.py
prepare_six_foot_host_attempt_20261116.py
record_neon_checkpoint_20261117.py
record_neon_f387_active_20261117.py
record_neon_second_failure_and_setter_20261117.py
run_neon_auxiliary_original_20261117.py
run_neon_behavior_boundary_v3_20261116.py
run_neon_behavior_candidate_20261116.py
run_neon_behavior_diagnostic_20261116.py
run_neon_behavior_fixture_20261116.py
run_neon_behavior_original_20261116.py
run_neon_geometry_20261116.py
run_neon_timeline_successors_20261117.py
run_neon_timeline_successors_v2_20261117.py
run_neon_ui_review_20261116.py
run_neon_waveform_aa_profiles_20261117.py
run_neon_waveform_classic_reveal_20261117.py
run_neon_waveform_diagnostic_20261117.py
run_neon_waveform_palette_profiles_20261117.py
stage_neon_native_fixtures_20261116.py
verify_neon_checkpoint_remote_20261117.py
verify_neon_review_archive_20261117.py
verify_setter_and_failed_archives_20261117.py
prepare_neon_completed_checkpoint_20261117.py
'''.split()
FILES = '''
LLM.md
docs/progress_memo.md
docs/NEXT_SESSION_PLAN_2026-11-16.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/completion_checklist.json
docs/completion_checklist.md
docs/benchmarks/neon_review_2026-11-17.json
docs/benchmarks/six_foot_domain_transport_2026-11-17.json
docs/benchmarks/source_normal_setter_2026-11-17.json
experiments/neon_windows_original_20261116/run_canonical_owned.ps1
experiments/neon_windows_original_20261116/NATIVE_FIXTURE_STAGE.json
'''.split()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

indexes = []
for name in FOLDERS:
    folder = ROOT / 'experiments' / name
    assert folder.is_dir(), name
    selected = [p for p in folder.rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
    index = folder / 'INDEX.json'
    if index.is_file():
        document = json.loads(index.read_bytes())
        entries = document['files']
        entries = [dict(path=name, **row) for name, row in entries.items()] if isinstance(entries, dict) else entries
        for row in entries:
            path = folder / row['path']
            assert path.resolve().is_relative_to(folder) and not path.is_symlink()
            assert sha(path.read_bytes()) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)
        indexes.append({'packet': name, 'index_sha256': sha(index.read_bytes()), 'checked_payloads': len(entries)})
    FILES.extend(p.relative_to(ROOT).as_posix() for p in selected)
FILES.extend('experiments/' + name for name in OPERATIONS)
rows = []
allowed = {'.json', '.md', '.py', '.ps1', '.gd', '.log', '.txt', '.gz', '.patch', '.proposed'}
for name in sorted(set(FILES)):
    path = ROOT / name
    assert path.resolve().is_relative_to(ROOT) and not path.is_symlink()
    assert not name.startswith('output/') and '__pycache__' not in path.parts and path.suffix.lower() in allowed
    raw = path.read_bytes()
    text = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in text
    text.decode('utf-8-sig')
    if path.suffix == '.json':
        json.loads(text)
    assert 'PRIVATE_SETTER' not in path.name
    rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
original = json.loads((ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json').read_bytes())
assert len(original['source_sha256']) == 1019
assert all(sha((ROOT / name).read_bytes()) == pin for name, pin in original['source_sha256'].items())
manifest = ROOT / 'output/neon-completed-checkpoint-20261117-manifest-v2.json'
record = {'format': 'has_completed_public_checkpoint_catalogue_1', 'files': rows, 'validated_source_indexes': indexes,
          'main_functional_source_unchanged': 1019, 'full_candidate_stays_separate': True,
          'active_terminal_helpers_excluded': True, 'private_art_arrays_media_excluded': True}
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
                  'validated_indexes': len(indexes), 'manifest': str(manifest), 'sha256': sha(manifest.read_bytes())}))
