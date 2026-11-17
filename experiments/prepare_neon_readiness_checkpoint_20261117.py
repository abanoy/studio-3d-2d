"""UNRUN readiness source selector; Root must freeze the final public records first.

Derived from the camera selector. This selects exact literal files and closed
INDEX payloads, checks retained qualified52 Main1019, and creates one new manifest.
It never imports selected source or discovers a directory recursively.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_696_checkpoint_privacy_peer_20261117
neon_camera_source_checkpoint_remote_20261117
neon_source52_to_696_delta_draft_20261117
neon_source52_to_696_root_review_20261117
neon_696_postpass_copy_readiness_20261117
successful_full_public_projection_certificate_696_20261117
pmx_physics_archive_prototype_20261117
neon_696_color_failure_20261117
'''.split()
FOLDER_INDEX_SHA256 = {
    'neon_696_checkpoint_privacy_peer_20261117': 'dab5b50b7a1288e8362301531b7033b196e32759bf18b43ec69a5e4fc1a900da',
    'neon_source52_to_696_delta_draft_20261117': '0ba355b396b69669789ae08b56449aa53b6b7d16704a8b50e650d8cffa386052',
    'neon_source52_to_696_root_review_20261117': 'fb1e75534468a71f524fd2c481e45c4a36d5a701de4f762045a612e2a9e3a65d',
    'neon_696_postpass_copy_readiness_20261117': 'd90b594b3a3cb32c5b42167bda4ee9c77ba7151340a660b966897d122dbe8b7a',
    'successful_full_public_projection_certificate_696_20261117': 'c7c465f176df125a520064c4095faa0001273fce84fcc36ed1847a0ae47ad719',
    'pmx_physics_archive_prototype_20261117': '97e7c5a6085de7e0eb67b87584a49d7401a9f42553373f85ddf81108873346d1',
    'neon_696_color_failure_20261117': 'f66c93a5f9180e36838ae76fd20421434a86bc4464192cdee667cb3ccb0160ab',
}
# The closed remote proof has no INDEX: this is its sole exact named exception.
UNSEALED = {
    'neon_camera_source_checkpoint_remote_20261117': ('COMPLETE_READBACK.json',),
}
FILE_PINS = {
    'experiments/neon_camera_source_checkpoint_remote_20261117/COMPLETE_READBACK.json':
        (431613, '65cff50f448decae4421c79a9ccad2bd8f4152592352ea30a0a14935c0cbbf8f'),
}
# PMX is closed, independently source-reviewed, and selected only via its INDEX.
FILES = '''
LLM.md
docs/progress_memo.md
docs/RESUME_MASTER_PLAN.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/benchmarks/neon_review_2026-11-17.json
docs/completion_checklist.json
experiments/prepare_neon_readiness_checkpoint_20261117.py
experiments/verify_neon_camera_source_checkpoint_remote_20261117.py
experiments/review_neon_696_source_delta_20261117.py
experiments/record_neon_696_color_failure_20261117.py
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
        assert not cursor.is_symlink(), str(cursor)
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
            relative = path.relative_to(ROOT).as_posix()
            raw = path.read_bytes()
            assert path.suffix == '.json' and (len(raw), sha(raw)) == FILE_PINS[relative], relative
    else:
        index_path = checked_path(folder, 'INDEX.json')
        index_raw = index_path.read_bytes()
        assert sha(index_raw) == FOLDER_INDEX_SHA256[name], name
        doc = json.loads(index_raw)
        keys = [key for key in ('files', 'artifacts', 'payloads') if key in doc]
        assert len(keys) == 1, (name, keys)
        entries = doc[keys[0]]
        entries = [dict(path=path, **row) for path, row in entries.items()] if isinstance(entries, dict) else entries
        entries = entries + doc.get('objects', [])
        names = [row['path'] for row in entries]
        assert len(names) == len(set(names)) and 'INDEX.json' not in names, name
        for row in entries:
            path = checked_path(folder, row['path'])
            raw = path.read_bytes()
            assert type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
            if 'decoded_sha256' in row:
                decoded = gzip.decompress(raw)
                assert len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256'], str(path)
        paths = [index_path] + [checked_path(folder, row['path']) for row in entries]
        indexes.append({'packet': name, 'index_sha256': sha(index_raw), 'checked_payloads': len(entries)})
    FILES.extend(path.relative_to(ROOT).as_posix() for path in paths)

rows = []
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.cfg'}
for name in sorted(set(FILES)):
    path = checked_path(ROOT, name)
    parts = [part.casefold() for part in PurePosixPath(name).parts]
    assert parts[0] != 'output' and '__pycache__' not in parts, name
    assert not any(part.startswith('private') or part in ('terminal-audit', 'canonical', 'receipt-logs') for part in parts), name
    assert path.suffix in allowed, name
    raw = path.read_bytes()
    content = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in content, name
    content.decode('utf-8-sig')
    if path.suffix == '.json':
        json.loads(content)
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

manifest = ROOT / 'output/neon-readiness-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_readiness_source_checkpoint_catalogue_1',
        'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'main_functional_source_commit': state['source_commit'],
        'full_result_claimed': False, 'redesign_merged': False,
        'source_delta_review_is_not_full_or_merge_activation': True,
        'postpass_copy_and_projection_are_source_CPU_readiness_only': True,
        'projection_binding_has_no_actual_report_or_archive_activation': True,
        'PMX_archive_prototype_and_retained_failure_are_authored_synthetic_CPU_only': True,
        'closed696_failure_is_selected_scalar_metadata_only': True,
        'native_fidelity_material_acceptance_or_simulation_claimed': False,
        'raw_full_reports_logs_phase_receipt_arrays_excluded': True,
        'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'sealed_indexes': len(indexes), 'manifest_sha256': sha(manifest.read_bytes()),
    'manifest': str(manifest)}))
