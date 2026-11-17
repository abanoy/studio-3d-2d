"""UNRUN3a source selector; Root must freeze the final public records first.

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
neon_3a3701a_candidate_reconstruction_20261117
neon_3a3701a_candidate_reconstruction_peer_20261117
neon_color_sampler_conjunction_diagnostic_20261117
neon_color_sampler_pixel_center_proposal_20261117
neon_color_center_actual_20261117
neon_late_stage_cases_source_20261117
pmx_physics_independent_oracle_20261117
native_normal_known_factory_resource_successor_20261117
neon_readiness_source_checkpoint_remote_20261117
neon_3a3701a_full_preflight_source_20261117
pmx_physics_native_observation_harness_20261117
neon_late_3a_actual_20261117
pmx_oracle_native_observation_actual_20261117
native_normal_known_factory_binding_source_20261117
native_normal_known_factory_binding_git_tool_20261117
neon_3a_terminal_20261117
pmx_physics_oracle_count_diagnostic_20261117
neon_windows_3a3701a_20261117
neon_source52_to_3a_delta_draft_20261117
'''.split()
FOLDER_INDEX_SHA256 = {'neon_3a3701a_candidate_reconstruction_20261117': '69d8f2eef22aa3ad1c0d2576cf4bba04977a4320fed9ff1dcec9afe81f8bcc28', 'neon_3a3701a_candidate_reconstruction_peer_20261117': '269fee199f729d2cd27cd1e51f12410222d4a641b42078a26ebcb824e88f3da6', 'neon_color_sampler_conjunction_diagnostic_20261117': '63f14095d1baab762a0c8254d31b447e08c672e42dabdb1a1f18b21c4b255ef8', 'neon_color_sampler_pixel_center_proposal_20261117': '46d8ac7d77f5af550cef292e52d01f6d2bfa4ad69a62e556492a406c659a58e6', 'neon_color_center_actual_20261117': '0d99bc3c60bcb7b7f85289682861b00c3fd0ff4e5f84d0294baa49a55282c48b', 'neon_late_stage_cases_source_20261117': '790277ef5e25f78e63d46350dba0304dce6c083c84ad5e010ac478fcea865ea3', 'pmx_physics_independent_oracle_20261117': 'd27d9873bc08ec2bc37f8939ae09f9b071f9f4e6fda8b112a2626fef7fabbb45', 'native_normal_known_factory_resource_successor_20261117': '1eeca1e85d93c834c52c1208ed68d18aaa2b00bc1b62987cf0b89d5561ab6f90', 'neon_3a3701a_full_preflight_source_20261117': '8e60d6cad288ff7b40100e0b8828dcf13e1cc3c7f0caca9e7a9c1ed4847e93c0', 'pmx_physics_native_observation_harness_20261117': '4258db09011aab285d00889cda1ada279f511f4553828cb69b6b07975bdaf8ec', 'neon_late_3a_actual_20261117': '8b1b7813da72735ff170aa6c46eb887cf0d1b6e352fd7d2ad69cee204597467b', 'pmx_oracle_native_observation_actual_20261117': '955f93dc384f4e243e6aad843219fc254a007793d3964406cf24091258201982', 'native_normal_known_factory_binding_source_20261117': '097e93267f9c438358cc6a0519615a20b4d6dcede2473c7480ca9514a3c00891', 'native_normal_known_factory_binding_git_tool_20261117': '3917792c091fe776cdd49b7f3e015b5655b104798c8a605e340967e870801235', 'neon_3a_terminal_20261117': '7ed937daaf6b2b1c39b6c0d877243f2e6fdec0215bb86a34bfbf897baaf0fd62', 'pmx_physics_oracle_count_diagnostic_20261117': 'c21bac607f5772817455dc50f7db95580601545009fb8ba4b944a1ccd4b2b7d8', 'neon_source52_to_3a_delta_draft_20261117': 'b0ce3924dcab5d34bacd661753f24431b552b1e7ebaf056712fe2450aade20aa'}
ROOT_SOURCE_SEALS = {'neon_3a3701a_full_preflight_source_20261117': ('experiments/prepare_neon_3a3701a_full_actual_20261117.py', 'experiments/check_neon_3a3701a_full_source_20261117.py')}
# The closed remote proof has no INDEX: this is its sole exact named exception.
UNSEALED = {'neon_readiness_source_checkpoint_remote_20261117': ('COMPLETE_READBACK.json',), 'neon_windows_3a3701a_20261117': ('PREPARATION.json', 'active-observation/OBSERVATION.json', 'active-observation/launch.json', 'active-observation/root-birth-observation.json', 'active-observation/root-birth-api-detail.json', 'active-observation/source-before.json', 'active-observation/preflight-source.json', 'active-observation/prelaunch-owned-scope.json', 'active-observation/state.json')}
FILE_PINS = {'experiments/neon_readiness_source_checkpoint_remote_20261117/COMPLETE_READBACK.json': (377331, '1b109da39a709b895117b56bbea04a28226f6b486ec2a2e3d99e85aa18191b24'), 'experiments/neon_windows_3a3701a_20261117/PREPARATION.json': (3696, '4ff40a8e5c4a585e51446aec39fb73755d7162ddb4bc8a84363b5f7f949dcbb0'), 'experiments/neon_windows_3a3701a_20261117/active-observation/OBSERVATION.json': (2689, '70783e66ba82c2fdb5d13fca581b95cf688a957b5f809b0d880974b29d18a4a4'), 'experiments/neon_windows_3a3701a_20261117/active-observation/launch.json': (1187, 'a35a4d10130116ccfadb294851bc4c45faf0931392fc93440c3aa0d9cb4ce409'), 'experiments/neon_windows_3a3701a_20261117/active-observation/root-birth-observation.json': (365, '1ba1fb9eae97c0e247570a81e0abb7d43e9fbafee9bf75a7802e60e0e3cf8fd6'), 'experiments/neon_windows_3a3701a_20261117/active-observation/root-birth-api-detail.json': (301, 'e38a1d27a7cc30eb59176b4c9366a3cf346394f84a5903e185fe3aeb60c00209'), 'experiments/neon_windows_3a3701a_20261117/active-observation/source-before.json': (108131, '3ef2e7d8bed6e063afef59c8caccba914663752998761350c882fd4efbc78e9d'), 'experiments/neon_windows_3a3701a_20261117/active-observation/preflight-source.json': (104958, '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'), 'experiments/neon_windows_3a3701a_20261117/active-observation/prelaunch-owned-scope.json': (188, 'bde0a0783ba77451a468d724f562624ac74c8a5753e351e6d005ac805dfcaf9b'), 'experiments/neon_windows_3a3701a_20261117/active-observation/state.json': (724, '3987c60012d80846b04caff116fc89e5dc817dd4a907c4fcc7cb2cedfee69829')}
# Only these exact public Git-tree metadata encodings are admitted as hex.
HEX_PAYLOADS = ('experiments/neon_3a3701a_candidate_reconstruction_20261117/tree-objects/00.hex', 'experiments/neon_3a3701a_candidate_reconstruction_20261117/tree-objects/01.hex', 'experiments/neon_3a3701a_candidate_reconstruction_20261117/tree-objects/02.hex')
# Completed packets only. Add3a preflight/harness only after their final seals; never private data.
FILES = '''
LLM.md
docs/progress_memo.md
docs/RESUME_MASTER_PLAN.md
docs/NEXT_SESSION_PLAN_2026-11-17.md
docs/benchmarks/neon_review_2026-11-17.json
docs/completion_checklist.json
experiments/prepare_neon_3a_checkpoint_20261117.py
experiments/apply_neon_color_center_20261117.py
experiments/neon_color_center_root_application_20261117.json
experiments/run_neon_color_diagnostic_20261117.py
experiments/run_neon_color_center_diagnostic_20261117.py
experiments/run_neon_color_center_followup_20261117.py
experiments/run_neon_late_stage_3a_20261117.py
experiments/record_neon_color_center_actual_20261117.py
experiments/stage_pmx_oracle_inputs_20261117.py
experiments/verify_neon_readiness_source_checkpoint_remote_20261117.py
experiments/prepare_neon_3a3701a_full_actual_20261117.py
experiments/check_neon_3a3701a_full_source_20261117.py
experiments/record_neon_late_3a_actual_20261117.py
experiments/record_pmx_oracle_observation_20261117.py
experiments/launch_neon_3a_full_20261117.ps1
experiments/record_neon_3a_active_20261117.py
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
        if name in ROOT_SOURCE_SEALS:
            seal = json.loads(checked_path(folder, 'SOURCE_SEAL.json').read_bytes())
            assert seal['format'] == 'has_neon3a_full_preflight_source_seal_1'
            source_rows = seal['source_files']
            assert len(source_rows) == len(ROOT_SOURCE_SEALS[name]) and {row['ROOT_relative_path'] for row in source_rows} == set(ROOT_SOURCE_SEALS[name])
            assert set(ROOT_SOURCE_SEALS[name]) <= set(FILES)
            for row in source_rows:
                source_path = checked_path(ROOT, row['ROOT_relative_path'])
                source_raw = source_path.read_bytes()
                assert source_path.is_relative_to(ROOT / 'experiments') and len(source_raw) == row['bytes'] and sha(source_raw) == row['sha256']
        paths = [index_path] + [checked_path(folder, row['path']) for row in entries]
        indexes.append({'packet': name, 'index_sha256': sha(index_raw), 'checked_payloads': len(entries)})
    FILES.extend(path.relative_to(ROOT).as_posix() for path in paths)

rows = []
allowed = {'.json', '.md', '.py', '.gd', '.ps1', '.patch', '.proposed', '.original', '.log', '.txt', '.gz', '.cfg', '.hex'}
for name in sorted(set(FILES)):
    path = checked_path(ROOT, name)
    parts = [part.casefold() for part in PurePosixPath(name).parts]
    assert parts[0] != 'output' and '__pycache__' not in parts, name
    assert not any(part.startswith('private') or part in ('terminal-audit', 'canonical', 'receipt-logs') for part in parts), name
    assert path.suffix in allowed, name
    raw = path.read_bytes()
    if path.suffix == '.hex':
        assert name in HEX_PAYLOADS
        decoded_tree = bytes.fromhex(raw.decode('ascii').rstrip('\n'))
        assert len(decoded_tree) <= 65536 and raw == (decoded_tree.hex() + '\n').encode('ascii')
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

manifest = ROOT / 'output/neon-3a-source-checkpoint-20261117-manifest.json'
with manifest.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'format': 'has_public_neon_3a_source_checkpoint_catalogue_1',
        'files': rows, 'source_indexes': indexes,
        'main_functional_unchanged': 1019, 'main_functional_source_commit': state['source_commit'],
        'full_result_claimed': False, 'redesign_merged': False,
        'completed_source_and_selected_scalar_evidence_only': True,
        'source52_to_3a_delta_is_DRAFT_not_Root_review_or_activation': True,
        'color_center_focus_selected_scalar_metadata_only': True,
        'targeted_or_CPU_checks_do_not_claim_complete_full_PASS': True,
        'preflight_source_qualification_does_not_claim_full_PASS': True,
        'PMX_independent_oracle_is_authored_source_synthetic_unqualified': True,
        'known_factory_resource_successor_is_source_only_inactive': True,
        'private_callback_payload_and_native_capsules_excluded': True,
        '3a_active_boot_metadata_is_dated_running_snapshot_not_result': True,
        'actual_tail44_scalar_packet_is_not_complete_full_PASS': True,
        'partial_native_oracle1_of4_scalar_packet_does_not_qualify_candidate_or_archive': True,
        'native_fidelity_material_acceptance_or_simulation_claimed': False,
        'raw_full_reports_logs_phase_receipt_arrays_excluded': True,
        'private_native_art_arrays_media_excluded': True}, stream, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'sealed_indexes': len(indexes), 'manifest_sha256': sha(manifest.read_bytes()),
    'manifest': str(manifest)}))
