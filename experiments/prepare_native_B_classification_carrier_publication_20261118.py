"""ROOT later: literal saved-B/classifier/carrier/native-reader publication.

FINAL SOURCE ONLY. Root supplied the exact documents, three reader observations
and literal pins. This author does not execute the selector.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json
import subprocess
ROOT = Path(__file__).resolve().parents[1]
PARENT = 'c9a4489d1998b19f14c7d0c54e018b6cbfd4db51'
PUBLIC = 'experiments/native_B_classification_carrier_publication_20261118/MANIFEST.json'
SELF = 'experiments/prepare_native_B_classification_carrier_publication_20261118.py'
DERIVATION = 'experiments/native_B_classification_carrier_publication_selector_20261118/SOURCE_DERIVATION.json'
READY = True
SECOND_POINT_ACTUAL = 'experiments/native_point_expectation_blank_actual_20261118/RESULT.json'
THIRD_POINT_ACTUAL = 'experiments/native_point_expectation_bone_state_actual_20261118/RESULT.json'
PACKETS = {
    'native_B_resource_classification_rules_20261118': 'c2cc5476eb03bfc687102c1364ff753e4d941ae5ab90e6b92b78bd86314525ec',
    'native_B_resource_classification_actual_20261118': 'e8e321e473dbd4166d16b015ccc2c014f85f09c65fb8f44e07a4e28c9cc7d0dc',
    'carrier_input_domain_20261118': 'e7ae7f7011cf5e063f4513c75bf21e704d1c2de18604945e06dda763025a960a',
    'native_point_expectation_20261118': '482f888349c19617bc540df723ed76104d3d6056cab085ecf6b99a56f42040f6',
    'native_point_expectation_blank_model_fix_20261118': 'b7e12bb9655d794fa142ae20ff2175519a860d1aafc6e7be7e5699d6835b9326',
    'native_point_expectation_bone_state_fix_20261118': '4afdadb1fbbbf44216b9c3c0d7736efc293c7717eb8908e7eb219b7af094c7c8',
}
# Root supplies exactly nine current file pins only after documents and
# all three actual reader observations are ready. No pin is inferred from a directory.
REQUIRED_FILES = (
    'LLM.md', 'docs/progress_memo.md', 'docs/RESUME_MASTER_PLAN.md',
    'docs/completion_checklist.json', 'docs/benchmarks/neon_review_2026-11-17.json',
    'experiments/carrier_input_domain_actual_20261118/RESULT.json',
    'experiments/native_point_expectation_actual_20261118/RESULT.json',
)
FILE_PINS = {
    'LLM.md': '3a5b423c48ef6273a777b55f88b2477c4da9621b739b5791f024c9b3169faff6',
    'docs/progress_memo.md': 'c361453bdbd59e888541b86566eb457269a3becc31d823607e52212c22d6ec86',
    'docs/RESUME_MASTER_PLAN.md': '5b80ec1173de9983d2fc32b7997d294f9a346a5e9ea97b707b5fd4ccc9b467e4',
    'docs/completion_checklist.json': '2b26c8514710a5708c0a5ba3187bb0c977e410cd989bfdd47f8ef7463d2400a4',
    'docs/benchmarks/neon_review_2026-11-17.json': '82bf965c7d3cc0f529456012da2b7a1d74bde9b0baddd2bd9fc662930e29729a',
    'experiments/carrier_input_domain_actual_20261118/RESULT.json': 'f037bc175ffb48b9135bdd5ad57e78909f78c209bc72813845f724c0f0f8d75d',
    'experiments/native_point_expectation_actual_20261118/RESULT.json': '828db2b896d268a7db057f8b1e00f362059a7d80a2a47dabc005207169da91f6',
    'experiments/native_point_expectation_blank_actual_20261118/RESULT.json': '0d0ff866792097a7901005d5fa990c3181559746afb947f8b7d164dd3b6a7d8b',
    'experiments/native_point_expectation_bone_state_actual_20261118/RESULT.json': '36dac1dbc6a9218c0cf291cb38c05342d49f01e46c606961d0218544b63e9612',
}
CPU_LOG = 'experiments/native_B_resource_classification_rules_20261118/CPU_TESTS.log'
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


assert READY is True, 'Root documents, third actual and literal pins are not finalized'
assert set(FILE_PINS) == set(REQUIRED_FILES) | {SECOND_POINT_ACTUAL, THIRD_POINT_ACTUAL}
assert SECOND_POINT_ACTUAL.startswith('experiments/') and SECOND_POINT_ACTUAL.endswith('/RESULT.json')
assert THIRD_POINT_ACTUAL.startswith('experiments/') and THIRD_POINT_ACTUAL.endswith('/RESULT.json')
assert all(type(pin) is str and len(pin) == 64 and all(c in '0123456789abcdef' for c in pin)
           for pin in (*PACKETS.values(), *FILE_PINS.values()))
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
assert len(names) == len(set(names)) == 56 and PUBLIC not in names
rows = []
for name in sorted(names):
    parts = PurePosixPath(name).parts
    assert parts[0] in ('experiments', 'docs') or name == 'LLM.md'
    assert not any(p.casefold() in ('output', '.git', '.godot', '__pycache__', 'terminal-audit', 'receipt-logs')
                   or p.casefold().startswith('private') or 'remote-batch' in p.casefold() for p in parts)
    path = checked_path(ROOT, name)
    assert path.suffix in ('.py', '.json', '.md') or name == CPU_LOG
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

classification = json.loads(checked_path(ROOT, 'experiments/native_B_resource_classification_actual_20261118/PUBLIC_CLASSIFICATION.json').read_bytes())
assert classification['classification_rows'] == 6 and classification['original_issue_rows_retained'] == 6
assert classification['status'] == 'RESOURCE_PROFILE_REFUSED' and classification['profile_issues'] == 6
assert classification['counts'] == {'REQUIRED_EXTERNAL_REFERENCE': 0, 'LOCAL_APPENDED_ASSET_PROVENANCE': 2,
                                    'INTERNAL_VIEWER_EDITOR_OBSERVATION': 2, 'UNRESOLVED': 2}
assert all(classification[key] is False for key in ('resource_profile_decision_changed', 'resources_excluded_or_accepted',
    'external_content_identity_or_existence_observed', 'strict31_normal_fidelity_export_repair_carrier_or_adoption_qualified',
    'actual_native_execution_by_classifier'))
domain = json.loads(checked_path(ROOT, 'experiments/carrier_input_domain_actual_20261118/RESULT.json').read_bytes())
assert domain['status'] == 'CLOSED_INPUT_DOMAIN_PASSED' and domain['domain']['passed'] is True
assert domain['original_unchanged'] is True
assert all(domain[key] is False for key in ('new_native_process_or_export', 'raw_native_arrays_included'))
assert all(domain['domain'][key] is False for key in ('full_gltf_conformance_qualified', 'native_correspondence_qualified',
                                                    'normal_fidelity_or_adoption_qualified'))
first = json.loads(checked_path(ROOT, 'experiments/native_point_expectation_actual_20261118/RESULT.json').read_bytes())
second = json.loads(checked_path(ROOT, SECOND_POINT_ACTUAL).read_bytes())
third = json.loads(checked_path(ROOT, THIRD_POINT_ACTUAL).read_bytes())
assert first['status'] == 'CLOSED_NATIVE_FAMILY_PROFILE_REFUSED'
assert first['source_sha256'] == '2631269a552a5dcbeb7091f8b1c903ff4f35cbd1713beba7b622a62b3aa1a283'
assert first['reason'] == 'Bounded ASCII model name required' and first['originals_unchanged'] is True
assert second['status'] == 'CLOSED_NATIVE_FAMILY_PROFILE_REFUSED'
assert second['reason'] == 'Closed trilist/no-bone-state-change strip required'
assert second['source_sha256'] == '0527c86cd36fc886cc7f4bde5c9363fa6226da4345382df7100e171a5b2401cf'
assert second['originals_unchanged'] is True
for point in (first, second, third):
    assert all(point[key] is False for key in ('new_native_process_or_export', 'raw_native_arrays_included',
                                             'normal_fidelity_or_adoption_qualified'))
assert third['format'] == 'has_readonly_native_family_reader_observation_1'
assert third['status'] == 'CLOSED_NATIVE_SOURCE_ROWS_DERIVED'
assert third['source_sha256'] == 'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d'
assert third['packet_INDEX_sha256'] == PACKETS['native_point_expectation_bone_state_fix_20261118']
assert third['source_facts_format'] == 'has_private_native_point_source_rows_1'
assert third['originals_unchanged'] is True and first['inputs'] == second['inputs'] == third['inputs']
assert third['native_lod0_rows'] == third['native_raw_rows'] == third['derived_model_point_rows'] == 9661
assert third['renderable_logical_models'] == 2 and third['bone_groups'] == 69 and third['derived_corner_rows'] == 42702
assert third['point_rows_by_distinct_positive_weight_groups'] == {'1': 4090, '2': 3191, '3': 2380}
assert sum(third['point_rows_by_distinct_positive_weight_groups'].values()) == third['derived_model_point_rows']
assert all(third[key] is False for key in ('Blender_stored_weight_order_qualified', 'actual_setter_or_exporter_binding_observed',
    'palette_or_render_equivalence_qualified', 'native_expected_adapter_independently_qualified'))
manifest = {
    'format': 'has_public_B_classification_carrier_reader_publication_manifest_1',
    'metadata_parent_HEAD_at_preparation': PARENT, 'files': rows, 'source_indexes': indexes,
    'main_functional_matches_qualified_candidate': 1029,
    'qualified_functional_source_commit': baseline['commit'],
    'qualified_functional_raw_map_sha256': source_map_sha,
    'public_functional_guard': {'path': baseline_relative, 'sha256': sha(baseline_raw)},
    'saved_actual_resource_classification_rows': 6,
    'resource_status': 'RESOURCE_PROFILE_REFUSED', 'resource_profile_issues': 6,
    'export_branch': 'UNKNOWN_UNCHANGED_NOT_RECOMPUTED',
    'classification_counts': classification['counts'],
    'retained_GLB_closed_input_domain_passed': True,
    'native_point_first_actual_status': first['status'],
    'native_point_blank_model_actual_status': second['status'],
    'native_point_strip_state_actual_status': third['status'],
    'native_source_point_rows_derived': third['derived_model_point_rows'],
    'native_source_corner_rows_derived': third['derived_corner_rows'],
    'native_source_rows_are_not_a_qualified_expected_adapter': True,
    'normal_fidelity_repair_carrier_correspondence_export_or_adoption_qualified': False,
    'owner_copy_changed_by_this_publication': False, 'cold187_changed_by_this_publication': False,
    'human_acceptance': 'DEFERRED',
    'raw_private_model_resource_ownership_classification_bodies_logs_arrays_receipts_pyc_caches_excluded': True,
}
raw = (json.dumps(manifest, indent=2) + '\n').encode()
target = ROOT / 'output/native-B-classification-carrier-publication-20261118-manifest.json'
public = ROOT / PUBLIC
path_list = ROOT / 'output/native-B-classification-carrier-publication-20261118-paths.nul'
assert not target.exists() and not public.parent.exists() and not path_list.exists()
with target.open('xb') as stream: stream.write(raw)
public.parent.mkdir(exist_ok=False)
with public.open('xb') as stream: stream.write(raw)
paths = [row['path'] for row in rows] + [PUBLIC]
assert len(paths) == 57
with path_list.open('xb') as stream: stream.write(b''.join(name.encode() + b'\0' for name in paths))
print(json.dumps({'selected_files': len(paths), 'working_bytes': sum(row['bytes'] for row in rows) + len(raw),
                  'manifest_sha256': sha(raw), 'path_list_sha256': sha(path_list.read_bytes()),
                  'source_functional_files_unchanged': 1029}))
