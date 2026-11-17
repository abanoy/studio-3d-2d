"""Completed cleanup85/source checkpoint selector; Root must freeze the final public records first.

Derived from the sealed readiness selector. This selects exact literal files and closed
INDEX payloads, checks retained qualified52 Main1019, and creates one new manifest.
It never imports selected source or discovers a directory recursively.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_source52_to_3a_root_review_20261117
neon_3a_postpass_copy_readiness_20261117
public_remote_cache_candidates_20261117
public_remote_cache_cleanup85_source_20261117
public_remote_cache_cleanup85_actual_20261117
neon_3a_source_checkpoint_remote_20261117
'''.split()
FOLDER_INDEX_SHA256 = {'neon_source52_to_3a_root_review_20261117': 'a91e9f9656238c2df60492dfa024ebcca7f46b7380da643b9a30b0f48d9fee15', 'neon_3a_postpass_copy_readiness_20261117': '617e6badf4682303f3555b201d97a85f222d87923e2f7538e2e59fa6f15c872e', 'public_remote_cache_candidates_20261117': 'f9be18b1accd813d18f941c20978f3d0e9828394160d87fe561cc333796f340f', 'public_remote_cache_cleanup85_source_20261117': 'bd2cdddf549f7da6840bbc85ca7724b79e3c07ff69910ffb6d7f48f7a6741aa8', 'public_remote_cache_cleanup85_actual_20261117': '5d17a897370cdc2226d35c1ecb19974e2bbcde3a1cbf2e99cc5179cf8de55cc1'}
# The closed remote proof has no INDEX: this is its sole exact named exception.
UNSEALED = {'neon_3a_source_checkpoint_remote_20261117': ('COMPLETE_READBACK.json',)}
FILE_PINS = {'experiments/neon_3a_source_checkpoint_remote_20261117/COMPLETE_READBACK.json': (436207, 'a8ad5426a5aaba5532b33dccfa17c22d42283c8b8960a89a2a17127a913a5ab0')}
# The only admitted JSONL is the sealed public 85-cache receipt.
JOURNAL_PAYLOADS = ('experiments/public_remote_cache_cleanup85_actual_20261117/JOURNAL.jsonl',)
# All five completed packets are closed; the remote proof is one exact literal exception.
FILES = '''
LLM.md
docs/progress_memo.md
docs/RESUME_MASTER_PLAN.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/benchmarks/neon_review_2026-11-17.json
docs/completion_checklist.json
experiments/prepare_neon_cleanup85_checkpoint_20261117.py
experiments/review_neon_3a_source_delta_20261117.py
experiments/verify_neon_3a_source_checkpoint_remote_20261117.py
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
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.cfg', '.jsonl'}
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
    if path.suffix == '.jsonl':
        assert name in JOURNAL_PAYLOADS
        journal_rows = [json.loads(line) for line in content.splitlines()]
        assert len(journal_rows) == 173 and all(type(row) is dict for row in journal_rows)
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

manifest = ROOT / 'output/neon-cleanup85-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_cleanup85_source_checkpoint_catalogue_1',
        'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'main_functional_source_commit': state['source_commit'],
        'full_result_claimed': False, 'redesign_merged': False,
        'root39_source_review_is_not_full_or_merge_activation': True,
        'postpass_copy_notes_have_not_activated_builder_or_cold187': True,
        'actual_public_cache_cleanup_deleted_files': 85,
        'actual_public_cache_cleanup_deleted_logical_bytes': 33228774,
        'current86df_cache_files_retained': 10,
        'free_space_change_measured_or_claimed': False,
        'preceding_public_metadata_checkpoint': '86dfd40609d814c4d8e4cde64f17f1f642258a35',
        'full3a_status_reference': 'ROOT_REPORTED_RUNNING_NOT_OBSERVED_HERE',
        'cleanup_journal_is_public_paths_scalar_identities_and_hashes_only': True,
        'native_fidelity_material_acceptance_or_simulation_claimed': False,
        'raw_full_reports_logs_phase_receipt_arrays_excluded': True,
        'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'sealed_indexes': len(indexes), 'manifest_sha256': sha(manifest.read_bytes()),
    'manifest': str(manifest)}))
