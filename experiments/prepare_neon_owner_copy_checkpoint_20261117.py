"""Exact public owner-copy source/scalar checkpoint; no target imports.

The predecessor's safe-path, closed INDEX and raw tested1029 checks are retained.
Only explicit source packets, public scalar projections and Root's documents are
selected. No private/native/runtime output is read and no Git state is mutated.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER_INDEX_SHA256 = {
    'neon_owner_admission_shell_eol_index_compat_20261117': 'f8da4f783958b918a35b53116fa6182fcddc9cd3cf485959f8bb088ce8147ee5',
    'neon_owner_executor_index_api_20261117': 'ced9e3943f24263b2399d14e77cc943e39371edacf7716e5fdbb9d336dcc447c',
    'neon_owner_cold187_index_api_20261117': '1d622b70d155441f4f07edf38be962d4ffc7ed0ecaf61ab6af13cf575ac1baac',
    'neon_owner_activation_index_api_20261117': '36fe7f94d9e519050ffac503a5c69be831563ce5ca8da8ac2bfec2d5216e7e4b',
    'neon_owner_executor_preparation_index_api_20261117': 'ebccd7264e2cd89d83d7ac61adc9f66fa872bcdb3ace5da7cb7720a94f0baef3',
    'neon_owner_validator_preparation_index_api_20261117': '72b5ea3df6eaa98442b10a228ee15def0be9158c2c285a82b0a9e0e47d6146ad',
    'neon_owner_executor_active_973039e_index_20261117': '61978b62ac92f6471d5b1dcbcc8cb485caccb3d2b7adb5d7edaa643e2252a066',
    'neon_owner_validator_active_973039e_index_20261117': '303b96a094d3ee61e8c1ec618db61adb0aa306811094347220b4b70436fafe38',
    'neon_owner_failed_activation_source_history_20261117': 'd8c729cfb9c915781a7c84eb729dd6e6caf9aa4c84b29103f0090038170a1f45',
    'neon_owner_973039e_closed_attempts_projection_20261118': '4bcfc1f4819e7369cbac63be2b08ec45d904c7fa7a22eb6745e8ed9a03c09e27',
}
UNSEALED = {
    'neon_qualified_merge_source_checkpoint_remote_20261117': ('COMPLETE_READBACK.json',),
    'neon_qualified_merge_remote_verifier_preparation_20261117': ('SOURCE_DERIVATION.json',),
}
FILE_PINS = {
    'experiments/neon_qualified_merge_source_checkpoint_remote_20261117/COMPLETE_READBACK.json': (557192, 'bf2400bc8b230d1cf785a8bbb5a619b86703fe216b5487f892f8e698cfe3750c'),
    'experiments/neon_qualified_merge_remote_verifier_preparation_20261117/SOURCE_DERIVATION.json': (4363, '7b2aeba7cf9080d9ce5a581c412928cf1ecb853f975d65653a9622bf4b0a3eed'),
}
FOLDERS = list(FOLDER_INDEX_SHA256) + list(UNSEALED)
FILES = '''
LLM.md
docs/progress_memo.md
docs/RESUME_MASTER_PLAN.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
experiments/update_neon_owner_copy_docs_20261117.py
experiments/prepare_neon_owner_copy_checkpoint_20261117.py
experiments/prepare_neon_failed_activation_source_history_20261117.py
experiments/verify_neon_qualified_merge_source_checkpoint_remote_20261117.py
experiments/verify_neon_owner_copy_source_checkpoint_remote_20261117.py
experiments/neon_owner_copy_checkpoint_selector_preparation_20261117/SOURCE_DERIVATION.json
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
        assert not cursor.is_symlink() and not getattr(cursor.lstat(), 'st_file_attributes', 0) & 0x400, str(cursor)
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
            relative = path.relative_to(ROOT).as_posix(); raw = path.read_bytes()
            assert path.suffix in ('.json', '.py') and (len(raw), sha(raw)) == FILE_PINS[relative], relative
    else:
        index_path = checked_path(folder, 'INDEX.json'); index_raw = index_path.read_bytes()
        assert sha(index_raw) == FOLDER_INDEX_SHA256[name], name
        doc = json.loads(index_raw)
        keys = [key for key in ('files', 'artifacts', 'payloads') if key in doc]
        assert len(keys) == 1, (name, keys)
        entries = doc[keys[0]]
        entries = [dict(path=path, **row) for path, row in entries.items()] if isinstance(entries, dict) else entries
        entries = entries + doc.get('objects', [])
        names = [row['path'] for row in entries]
        assert len(names) == len(set(names)) and 'INDEX.json' not in names, name
        # These explicitly named packets are flat and closed; no recursion.
        assert all('/' not in item for item in names), name
        assert {item.name for item in folder.iterdir()} == {'INDEX.json', *names}, name
        for row in entries:
            path = checked_path(folder, row['path']); raw = path.read_bytes()
            assert type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
            if 'decoded_sha256' in row:
                decoded = gzip.decompress(raw)
                assert len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256'], str(path)
        paths = [index_path] + [checked_path(folder, row['path']) for row in entries]
        indexes.append({'packet': name, 'index_sha256': sha(index_raw), 'checked_payloads': len(entries)})
    FILES.extend(path.relative_to(ROOT).as_posix() for path in paths)
assert len(FILES) == len(set(FILES)), 'Overlapping literal/indexed selection'

rows = []
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.cfg'}
for name in sorted(FILES):
    path = checked_path(ROOT, name)
    parts = [part.casefold() for part in PurePosixPath(name).parts]
    assert parts[0] != 'output' and '__pycache__' not in parts, name
    assert not any(part.startswith('private') or part in ('terminal-audit', 'canonical', 'receipt-logs') for part in parts), name
    assert path.suffix in allowed, name
    raw = path.read_bytes(); content = gzip.decompress(raw) if path.suffix == '.gz' else raw
    assert b'\0' not in content, name
    content.decode('utf-8-sig')
    if path.suffix == '.json': json.loads(content)
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

actual = json.loads(checked_path(ROOT, 'experiments/neon_3a_mmd_full_pass_actual_20261117/RESULT.json').read_bytes())
assert actual['full_suite_passed'] is True and actual['functional_files_unchanged'] == 1029
assert (actual['result_groups'], actual['core_groups'], actual['movie_groups']) == (158, 36, 21)
assert actual['actual_mmd_tested'] is True and actual['all_failures'] == 0
assert actual['receipt_inventory_sha256'] == 'a4b47b3bd0582e62f9466648cce07a25e8828656a9458262eac1d6e4eac84a23'
assert actual['owner_copy_and_cold187'] == 'UNRUN' and actual['prior157_group_run_remains_UNQUALIFIED'] is True
assert actual['Source_B_metadata_diagnostic']['resource_status'] == 'RESOURCE_PROFILE_REFUSED'
assert actual['Source_B_metadata_diagnostic']['export_branch'] == 'UNKNOWN'
assert actual['raw_native_arrays_art_callback_metadata_and_logs_included'] is False
review = json.loads(checked_path(ROOT, 'experiments/neon_3a_shell_eol_root_review_20261117/REVIEWED52_TO_CANDIDATE_DELTA.json').read_bytes())
assert review['review_status'] == 'ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA' and len(review['rows']) == 39
assert review['sealed_admission_core_sha256'] == 'c6ebc4b6e3999fbdecf13697a2ccb0ca9f0cafe3368beaf9767bd5f247247f76'

# These checks distinguish the current result from the historical full-pass snapshot.
projection = json.loads(checked_path(ROOT, 'experiments/neon_owner_973039e_closed_attempts_projection_20261118/RESULT.json').read_bytes())
assert projection['copied_merged_commit'] == '973039e40622ac20600e6d297d712de419877eda'
assert projection['qualified_functional_candidate'] == baseline['commit']
assert projection['overall_cold187_qualification'] is False
assert projection['portable_or_artist_acceptance_claimed'] is False and projection['third_native_attempt_launched'] is False
copy = projection['copy_at_BUILD']
assert copy['passed'] is True and copy['graphics_launched'] is False
assert (copy['functional_source_files'], copy['committed_support_files'], copy['native_source_files'],
        copy['SourceIO_files'], copy['exporter_sources_preserved'], copy['previous_reviews_preserved']) == (1029, 9790, 495, 574, 120, 4)
assert copy['preservation_assertions_passed_at_copy'] is True
assert copy['raw_private_BUILD'] == {'sha256': '23131d6ef73cc57146b514436755cdfb62447ccc02bfecb944c7389b91981c9e', 'bytes': 4333220}
archive = projection['attempt1_generated_output_archive']
assert (archive['status'], archive['files'], archive['logical_bytes'], archive['subdirectories']) == ('PASS', 10, 215197, 5)
assert archive['source_absent_at_archive_completion'] is True and archive['archive_current_file_identities_exact'] is True
assert archive['validator_launched_by_archiver'] is False
assert len(projection['cold_attempts']) == 2
for attempt in projection['cold_attempts']:
    assert attempt['overall_status'] == 'INCOMPLETE_NOT_PASS'
    assert (attempt['case_count'], attempt['observed_case_checks'], attempt['expected_case_checks'],
            attempt['physical_private_receipts_passed']) == (4, 187, 187, 4)
    assert attempt['original_terminal_exit'] is None and attempt['final_runtime_verification_present'] is False
    assert attempt['final_runtime_preservation_status'] == 'NOT_RECORDED'
    closure = attempt['recovery_scope']
    assert all(type(closure[key]) is int and closure[key] == 0 for key in ('owned_count', 'main_count', 'neon_count'))
    assert closure['observer_retained_Popen_reaped'] is True
history = json.loads(checked_path(ROOT, 'experiments/neon_owner_failed_activation_source_history_20261117/SOURCE_MAP.json').read_bytes())
assert history['all_23_failed_payloads_recoverable_exact'] is True and len(history['payloads']) == 23
for row in history['payloads']:
    body = checked_path(ROOT, row['recoverable_source']).read_bytes()
    assert (len(body), sha(body)) == (row['bytes'], row['sha256']) and row['source_bytes_exact'] is True

manifest = ROOT / 'output/neon-owner-copy-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_owner_copy_source_checkpoint_catalogue_1',
        'files': rows, 'source_indexes': indexes,
        'main_functional_matches_qualified_candidate': 1029,
        'qualified_functional_source_commit': baseline['commit'],
        'qualified_functional_raw_map_sha256': source_map_sha,
        'public_functional_guard': {'path': baseline_relative, 'sha256': sha(baseline_raw)},
        'metadata_parent_HEAD_at_preparation_Root_reported': '973039e40622ac20600e6d297d712de419877eda',
        'Git_state_observed_by_selector': False,
        'actual_full_PASS_public_scalar_projection_previously_published': True,
        'full_PASS_result_groups': 158, 'full_PASS_core_groups': 36, 'full_PASS_movie_groups': 21,
        'prior157_group_run_remains_unqualified': True,
        'actual_owner_copy_passed': True,
        'cold_attempts_overall': ['INCOMPLETE_NOT_PASS', 'INCOMPLETE_NOT_PASS'],
        'cold_case_checks_per_attempt': 187, 'physical_private_receipts_passed_per_attempt': 4,
        'recovery_scopes_closed_per_attempt': True, 'original_coordinator_terminal_records_absent': True,
        'exact_external_cause': 'UNOBSERVED', 'third_native_attempt_launched': False,
        'attempt1_generated_output_archive': 'TEN_FILES_215197_BYTES_PRESERVED_EXACT',
        'attempt2_generated_output': 'RETAINED_PRIVATE',
        'failed_activation_exact_source_history_included_without_duplicate_catalogues': True,
        'human_acceptance': 'DEFERRED', 'native_normal_fidelity': 'FAILED_UNQUALIFIED',
        'raw_full_reports_logs_receipts_native_counts_and_callbacks_excluded': True,
        'private_native_art_arrays_media_excluded': True,
        'native_normal_repair_adoption_or_simulation_claimed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'sealed_indexes': len(indexes), 'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
