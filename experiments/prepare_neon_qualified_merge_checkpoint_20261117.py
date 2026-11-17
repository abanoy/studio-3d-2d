"""Exact public qualified-merge source/scalar checkpoint; no target imports.

Main is guarded against already-public tested3a raw1029, never historical52.
Root reports HEADf21b/MERGE_HEAD3a at preparation; this selector performs no Git
query or mutation and reads no private/full/native output. Selection is literal
files plus fifteen closed pinned source packets, without recursive discovery.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = '''
neon_3a_mmd_full_pass_actual_20261117
neon_owner_executor_preparation_glue_20261117
neon_owner_validator_preparation_glue_20261117
pmx_classification_followup_proposal_20261117
native_normal_carrier_adapter_readiness_20261117
native_B_resource_refusal_followup_20261117
neon_owner_admission_shell_eol_20261117
neon_3a_shell_eol_delta_proposal_20261117
neon_3a_shell_eol_root_review_20261117
neon_owner_executor_shell_eol_20261117
neon_owner_cold187_shell_eol_20261117
neon_owner_activation_shell_eol_20261117
neon_owner_executor_preparation_shell_eol_20261117
neon_owner_validator_preparation_shell_eol_20261117
neon_qualified_merge_preparation_actual_20261117
neon_mmd_source_checkpoint_remote_20261117
neon_mmd_remote_verifier_preparation_20261117
'''.split()
FOLDER_INDEX_SHA256 = {'neon_3a_mmd_full_pass_actual_20261117': '941e9aeab6d788fd7e92603a0a8f9e7c2fde0f48e2f5c9193b37c8a931dc851a', 'neon_owner_executor_preparation_glue_20261117': '607c890490f8b69f30b098ec765ebd19b432da37597309c81e8d9d7a840611c6', 'neon_owner_validator_preparation_glue_20261117': '8fc4c53bc0920b9912a66e4a94de018495ae598fee9feaacf2e022c4d4b08a7a', 'pmx_classification_followup_proposal_20261117': 'e7171e6833d7c45f27d24fed39ad84919262230550b31d38e90b6c25d9493061', 'native_normal_carrier_adapter_readiness_20261117': 'dabd9d3af832ae59dce03fb5783b7ae8df3cd8cd88ef61279dc5d9875900238e', 'native_B_resource_refusal_followup_20261117': 'b2dffa81b4d9f0b04a066001d6131131a0c5a3195af122976d76d5e6dee64bb6', 'neon_owner_admission_shell_eol_20261117': '8ab1c8eb9f576a9c8a315ebf4df433fc4e4b8b4767ac44cdf64a2403467a2d42', 'neon_3a_shell_eol_delta_proposal_20261117': '36b5c4c6ccee9a3f783864b7648a2dba708f6d91189ee996228748392125ffd8', 'neon_3a_shell_eol_root_review_20261117': 'c3cac0b610b632d6bd519700e6066c87852d2447fff56c39b6bfc22f3a24834c', 'neon_owner_executor_shell_eol_20261117': '3ea125a3c043688c2bf5f2dbe5ce4c41501ea41b7f831575eefbe5bdfffbdcf4', 'neon_owner_cold187_shell_eol_20261117': 'a38e4866df7f8810d73e616b05b728b4e088dd4c84015b2ff65c6a8f1cbb3e64', 'neon_owner_activation_shell_eol_20261117': '1f42a221ad7de5094675d29888c51e5ddc60cb52a44e3ceecaa6b1866e57a367', 'neon_owner_executor_preparation_shell_eol_20261117': '21980dfe510f8ad4edafd1a97101e9251a81ca526365cb8177fc32255c30d883', 'neon_owner_validator_preparation_shell_eol_20261117': 'efd83e68fc08fcb98175f23b9618135c84699d472ef8672036cf33a4e697c623', 'neon_qualified_merge_preparation_actual_20261117': '3caf3ef76eac87c9cdacda0f5037506b1ee3e5b9b278cfafb7e066cf3a3ec68b'}
UNSEALED = {'neon_mmd_source_checkpoint_remote_20261117': ('COMPLETE_READBACK.json',), 'neon_mmd_remote_verifier_preparation_20261117': ('prepare_verifier.py', 'SOURCE_DERIVATION.json', 'FIRST_READBACK_REFUSAL.json', 'READBACK_HISTORY.json')}
FILE_PINS = {'experiments/neon_mmd_source_checkpoint_remote_20261117/COMPLETE_READBACK.json': (400912, 'ca28ba8c8d9cf121f854c18d627c0975e474aca7ed5babcd628218cc497e57ec'), 'experiments/neon_mmd_remote_verifier_preparation_20261117/prepare_verifier.py': (3709, '734a51c16ab15b6829d92449dc9f9793fd7baf64243011652b646eb10fd09f9a'), 'experiments/neon_mmd_remote_verifier_preparation_20261117/SOURCE_DERIVATION.json': (1867, '39528f80a179603a020da8cfa0f322797ae6b069eead320e59a3e11e105b84be'), 'experiments/neon_mmd_remote_verifier_preparation_20261117/FIRST_READBACK_REFUSAL.json': (1105, 'fe16cd149dc89c8cd00e7b7e5b3c844055ebf2e9cc6420b5781aacf9693586ea'), 'experiments/neon_mmd_remote_verifier_preparation_20261117/READBACK_HISTORY.json': (2257, '834e1506e12e3d15679e53816552c9a60ddf02f4a036b72413993efc9eac51de')}
FILES = '''
LLM.md
docs/progress_memo.md
docs/RESUME_MASTER_PLAN.md
docs/completion_checklist.json
docs/benchmarks/neon_review_2026-11-17.json
experiments/prepare_neon_qualified_merge_checkpoint_20261117.py
experiments/verify_neon_mmd_source_checkpoint_remote_20261117.py
experiments/record_neon_3a_mmd_full_pass_20261117.py
experiments/update_neon_qualified_merge_docs_20261117.py
experiments/restore_qualified_neon_merge_raw_20261117.py
experiments/review_neon_shell_eol_delta_20261117.py
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
        # These fifteen explicitly named packets are flat and closed; no recursion.
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

manifest = ROOT / 'output/neon-qualified-merge-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_qualified_merge_source_checkpoint_catalogue_1',
        'files': rows, 'source_indexes': indexes,
        'main_functional_matches_qualified_candidate': 1029,
        'qualified_functional_source_commit': baseline['commit'],
        'qualified_functional_raw_map_sha256': source_map_sha,
        'public_functional_guard': {'path': baseline_relative, 'sha256': sha(baseline_raw)},
        'prior_Main1019_guard_replaced_for_actual_tested1029': True,
        'metadata_HEAD_at_preparation_Root_reported': 'f21b9ec85ae63006d036ca7a21c5c82e53fda019',
        'MERGE_HEAD_at_preparation_Root_reported': baseline['commit'],
        'merge_commit_created_at_preparation': False, 'Git_state_observed_by_selector': False,
        'actual_full_PASS_public_scalar_projection_included': True,
        'full_PASS_result_groups': 158, 'full_PASS_core_groups': 36, 'full_PASS_movie_groups': 21,
        'actual_MMD_and_strict_terminal_closure_projected_by_Root': True,
        'prior157_group_run_remains_unqualified': True,
        'Root_reviewed_exact39_delta_and_three_shell_EOL_policy_included': True,
        'owner_copy_builder_or_cold187_activated': False,
        'human_acceptance': 'DEFERRED', 'native_normal_fidelity': 'FAILED_UNQUALIFIED',
        'B_metadata_completed_with_six_issue_profile_refusal_and_UNKNOWN_export': True,
        'old_source_CPU_and_preparation_status_records_are_historical': True,
        'raw_full_reports_logs_receipts_native_counts_and_callbacks_excluded': True,
        'private_native_art_arrays_media_excluded': True,
        'native_normal_repair_adoption_or_simulation_claimed': False}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'sealed_indexes': len(indexes), 'manifest_sha256': sha(manifest.read_bytes()), 'manifest': str(manifest)}))
