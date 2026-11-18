"""Freeze an explicit metadata-only followup; preserve the tested raw1029 guard."""
from pathlib import Path, PurePosixPath
import argparse
import gzip
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'ddc24d786228c8a66a38a21d4db61e939ca6dee8'
PUBLIC = 'experiments/neon_post_copy_source_checkpoint_catalogue_20261118/PUBLIC_MANIFEST.json'
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


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--selection', required=True)
parser.add_argument('--selection-sha256', required=True)
args = parser.parse_args()
selection_path = checked_path(ROOT, args.selection)
selection_raw = selection_path.read_bytes()
assert sha(selection_raw) == args.selection_sha256
selection = json.loads(selection_raw)
assert selection['parent'] == PARENT
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == PARENT
names = list(selection['files'])
assert args.selection in names and len(names) == len(set(names))
indexes = []
for folder_name, pin in selection['packets'].items():
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
assert len(names) == len(set(names)) and PUBLIC not in names
rows = []
for name in sorted(names):
    parts = PurePosixPath(name).parts
    assert parts[0] in ('experiments', 'docs') or name == 'LLM.md'
    assert not any(p.casefold() in ('output', '.git', '.godot', '__pycache__', 'terminal-audit', 'receipt-logs')
                   or p.casefold().startswith('private') or 'remote-batch' in p.casefold() for p in parts)
    path = checked_path(ROOT, name)
    assert path.suffix in ('.py', '.json', '.md', '.log', '.gz', '.ps1', '.txt')
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

proof = checked_path(ROOT, 'experiments/neon_owner_copy_source_checkpoint_remote_20261117/COMPLETE_READBACK.json').read_bytes()
assert sha(proof) == '7d3a345fb459b9396173906b00955cda5fe433d7447c1af9884e73636b4d3581'
proof_value = json.loads(proof)
assert proof_value['commit'] == PARENT and proof_value['file_count'] == proof_value['changed_file_count'] == 151
assert proof_value['owner_copy_passed'] is True and proof_value['cold_attempts_overall'] == ['INCOMPLETE_NOT_PASS'] * 2
assert all(row['independent_remote_bytes_exact'] is True for row in proof_value['files'])
manifest = {
    'format': 'has_public_neon_owner_copy_source_checkpoint_catalogue_1',
    'metadata_parent_HEAD_at_preparation_Root_reported': PARENT,
    'files': rows, 'source_indexes': indexes,
    'main_functional_matches_qualified_candidate': 1029,
    'qualified_functional_source_commit': baseline['commit'],
    'qualified_functional_raw_map_sha256': source_map_sha,
    'public_functional_guard': {'path': baseline_relative, 'sha256': sha(baseline_raw)},
    'actual_owner_copy_passed': True,
    'cold_attempts_overall': ['INCOMPLETE_NOT_PASS', 'INCOMPLETE_NOT_PASS'],
    'native_ownership_collector_execution': 'UNRUN',
    'native_normal_fidelity': 'FAILED_UNQUALIFIED',
    'human_acceptance': 'DEFERRED', 'cleanup_performed': False,
    'raw_private_native_reports_logs_receipts_arrays_media_excluded': True,
}
raw = (json.dumps(manifest, indent=2) + '\n').encode()
target = ROOT / 'output/neon-post-copy-source-checkpoint-20261118-manifest.json'
with target.open('xb') as stream:
    stream.write(raw)
public = ROOT / PUBLIC
public.parent.mkdir(exist_ok=False)
with public.open('xb') as stream:
    stream.write(raw)
path_list = ROOT / 'output/neon-post-copy-source-checkpoint-20261118-paths.nul'
paths = [row['path'] for row in rows] + [PUBLIC]
with path_list.open('xb') as stream:
    stream.write(b''.join(name.encode() + b'\0' for name in paths))
print(json.dumps({'selected_files': len(paths), 'working_bytes': sum(row['bytes'] for row in rows) + len(raw),
                  'manifest_sha256': sha(raw), 'path_list_sha256': sha(path_list.read_bytes()),
                  'source_functional_files_unchanged': 1029}))
