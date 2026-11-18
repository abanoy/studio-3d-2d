"""ROOT later: literal B metadata publication; exact parent and tested raw1029."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json
import subprocess
ROOT = Path(__file__).resolve().parents[1]
PARENT = 'dcbeb9dddb4326d80ad1f24ae135fd7bda7be152'
PUBLIC = 'experiments/native_B_ownership_publication_20261118/MANIFEST.json'
SELF = 'experiments/prepare_native_B_ownership_publication_20261118.py'
DERIVATION = 'experiments/native_B_ownership_publication_selector_20261118/SOURCE_DERIVATION.json'
PACKETS = {
    'native_B_resource_ownership_runtime_20261118': '505da02ceed7dfb705dfb9d22d3b054053c4c32279053fd8d9743336be33f99f',
    'native_runtime_stamp_probe_source_20261118': 'a166b92ff19d48c2e4cb594d45e5beab40b339b1218732c953b6ae27b5b46563',
    'native_runtime_stamp_probe_source_v2_20261118': 'b34a10387208b1d14d9586c0e1a0d5b2698abf1ec5554ac6553b3eb56ed86053',
    'native_B_resource_ownership_actual_20261118': 'd30ddacc37620a7ee72f0d553cd1c33b3cad5ee09114af59ffc94b0c286fe876',
}
FILE_PINS = {
    'LLM.md': 'd07b72920984eef7034c5d3a43a686b1aa734964675a8b0e78e41feffdf95db2',
    'docs/progress_memo.md': '2b60a72fd9df5b8b708d6d28d30edaccf8c8212a578b10cc6af768e900757e69',
    'docs/RESUME_MASTER_PLAN.md': 'cecc816f5ea07cdfcb4452923772636f05b0f8ff11163e6b43ca4f705507a6e7',
    'docs/completion_checklist.json': '5fdf08ba76e01adfdac1e6e197257c2e4bbe56a38a311b88a744b396c6aaf1e5',
    'docs/benchmarks/neon_review_2026-11-17.json': '45dcca6058c800082c28637a60aa3fec1b6a9b503f9cb284d363f2e5680551ba',
    'experiments/native_B_ownership_root_classification_20261118/RESULT.json': '3481821aef0643fdaf75cbfef79d624e1671a5a4243ce9459b5921f9ad1a3dd0',
    'experiments/native_B_ownership_cache_preservation_20261118/RESULT.json': '84b46e70f3cb473c68c6879c5a993215c5d23bc0ea932e063f1b21a8069b3e7f',
}
CACHE_MOVE = 'experiments/native_B_ownership_cache_preservation_20261118/RESULT.json'
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


assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == PARENT
assert Path(__file__).resolve() == checked_path(ROOT, SELF).resolve()
for name, pin in FILE_PINS.items():
    assert sha(checked_path(ROOT, name).read_bytes()) == pin, name
names = [*FILE_PINS, SELF, DERIVATION]
indexes = []
for folder_name, pin in PACKETS.items():
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
    assert path.suffix in ('.py', '.json', '.md')
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

actual = json.loads(checked_path(ROOT, 'experiments/native_B_resource_ownership_actual_20261118/RESULT.json').read_bytes())
classification = json.loads(checked_path(ROOT, 'experiments/native_B_ownership_root_classification_20261118/RESULT.json').read_bytes())
assert actual['native_metadata_diagnostic']['diagnostic_completed'] is True
assert actual['native_metadata_diagnostic']['ownership_metadata_collected'] is True
assert actual['resource_decision']['status'] == 'RESOURCE_PROFILE_REFUSED' and actual['resource_decision']['profile_issues'] == 6
assert actual['resource_decision']['export_branch'] == 'UNKNOWN'
assert all(value is False for value in actual['claims'].values())
assert all(value is False for value in actual['additional_qualifications'].values())
assert classification['actual_native_observed'] is True and classification['original_issue_rows_retained'] == 6
assert classification['resource_decision_changed'] is False and classification['model_repair_normal_fidelity_export_or_adoption_claimed'] is False
assert classification['private_payload_sha256'] == actual['private_metadata_hashes_from_public_bindings_only']['ownership']['sha256']
cache_move = json.loads(checked_path(ROOT, CACHE_MOVE).read_bytes())
assert cache_move['status'] == 'PASSED' and cache_move['file_count'] == 9 and cache_move['bytes'] == 76119
assert cache_move['original_source_INDEX_sha256'] == PACKETS['native_B_resource_ownership_runtime_20261118']
assert all(cache_move[key] is True for key in ('all_archived_file_hashes_exact', 'native_lease_closed_before_move', 'source_absent'))
assert all(cache_move[key] is False for key in ('deletion_performed', 'binary_payloads_included', 'source_members_modified'))
manifest = {
    'format': 'has_public_native_B_ownership_publication_manifest_1',
    'metadata_parent_HEAD_at_preparation': PARENT, 'files': rows, 'source_indexes': indexes,
    'main_functional_matches_qualified_candidate': 1029,
    'qualified_functional_source_commit': baseline['commit'],
    'qualified_functional_raw_map_sha256': source_map_sha,
    'public_functional_guard': {'path': baseline_relative, 'sha256': sha(baseline_raw)},
    'actual_native_B_metadata_diagnostic_completed': True, 'ownership_metadata_collected': True,
    'resource_status': 'RESOURCE_PROFILE_REFUSED', 'resource_profile_issues': 6, 'export_branch': 'UNKNOWN',
    'Root_attested_private_classification_included_as_sanitized_metadata': True,
    'actual_cache_move_public_metadata': CACHE_MOVE, 'generated_cache_files_preserved_privately': 9,
    'generated_cache_bytes_preserved_privately': 76119, 'generated_cache_deletion_performed': False,
    'native_normal_fidelity': 'FAILED_UNQUALIFIED', 'strict31_normal_repair_export_or_adoption_qualified': False,
    'owner_copy_changed_by_this_publication': False, 'cold187_changed_by_this_publication': False,
    'human_acceptance': 'DEFERRED',
    'raw_private_model_resource_ownership_bodies_logs_arrays_receipts_pyc_excluded': True,
}
raw = (json.dumps(manifest, indent=2) + '\n').encode()
target = ROOT / 'output/native-B-ownership-publication-20261118-manifest.json'
public = ROOT / PUBLIC
path_list = ROOT / 'output/native-B-ownership-publication-20261118-paths.nul'
assert not target.exists() and not public.parent.exists() and not path_list.exists()
with target.open('xb') as stream: stream.write(raw)
public.parent.mkdir(exist_ok=False)
with public.open('xb') as stream: stream.write(raw)
paths = [row['path'] for row in rows] + [PUBLIC]
with path_list.open('xb') as stream: stream.write(b''.join(name.encode() + b'\0' for name in paths))
print(json.dumps({'selected_files': len(paths), 'working_bytes': sum(row['bytes'] for row in rows) + len(raw),
                  'manifest_sha256': sha(raw), 'path_list_sha256': sha(path_list.read_bytes()),
                  'source_functional_files_unchanged': 1029}))
