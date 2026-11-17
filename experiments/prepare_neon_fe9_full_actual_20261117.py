"""Fresh full reservation after actual Source foundation and closed375 run."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
REV = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == REV
focused = REVIEW / 'output/neon-foundation-fe9aace-20261117-attempt1'
check = load(focused / 'verification.json')
assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
foundation = load(focused / 'source-choices/verification.json')
assert foundation['passed'] is True and foundation['checks'] == 167 and foundation['separate_checks'] == {'crosswalk_cpu': 77, 'bone_bindings_headless': 96}
assert foundation['source_unchanged'] is True
helper_folder = REVIEW / 'output/neon-helper-375ec05-20261117-attempt1'
helper = load(helper_folder / 'verification.json')
assert helper['passed'] is True and [(row['mode'], row['report']['checks']) for row in helper['rows']] == [('cpu', 208), ('graphical', 266)]
assert all(row['root_exact_suite_assertions_passed'] is True for row in helper['rows'])
prior_run = REVIEW / 'output/windows-neon-375ec05-20261117T033037'
release = load(prior_run / 'graphics-lease-closed.json')
assert release['released'] is True and release['physical_jobs'] == 51
files = [p for d in ('src', 'tests', 'tools', 'data', 'examples') for p in (REVIEW / d).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
files += [REVIEW / n for n in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
assert len(files) == 1029
assert subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=REVIEW) == b''
sources = {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(files)}
assert sources == load(focused / 'source-before.json') == load(focused / 'source-after.json')
old = load(prior_run / 'source-before.json')['source_sha256']
assert old == load(helper_folder / 'source-before.json') == load(helper_folder / 'source-after.json')
assert set(old) == set(sources) and [name for name in sources if sources[name] != old[name]] == ['tests/source_bone_bindings_unit.gd']
assert sources['tests/source_bone_bindings_unit.gd'] == '80764dea7982a11f1d42a9bcbfb36b74c44edb6e620ddb585fa37dc1c8ab1e09'
assert sources['tests/helper_preview_port_files.json'] == '2c9e483649108b9760aeb96e20c8ac95025a4b595fa0cfbb730308247fb7a8f0'
lock = load(ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json')
reader = ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
spec = importlib.util.spec_from_file_location('neon_fe9_approved_input_reader', reader)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
for name, expected in lock['runtime_executables'].items():
    assert audit.identity(Path(name)) == expected, name
sourceio = ROOT / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
assert audit.metadata_map(sourceio) == lock['sourceio_files']
assert audit.metadata_map(REVIEW / 'output/dependencies' / sourceio.name) == lock['sourceio_files']
assert audit.metadata_map(Path(lock['exporter_root']), 'exporter') == lock['exporter_noncache_sources']
stage = load(ROOT / 'experiments/neon_windows_original_20261116/NATIVE_FIXTURE_STAGE.json')
for name, expected in stage['source_projects'].items():
    assert audit.identity(ROOT / 'output' / name) == expected and audit.identity(REVIEW / 'output' / name) == expected
runner = ROOT / 'experiments/neon_windows_original_20261116/run_canonical_owned.ps1'
assert sha(runner) == '8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4'
folder = REVIEW / 'output' / ('windows-neon-fe9aace-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
folder.mkdir(exist_ok=False)
packet = ROOT / 'experiments/neon_windows_fe9aace_20261117'
packet.mkdir(exist_ok=False)
record = {'format': 'has_neon_fe9_full_windows_preparation_1', 'revision': REV, 'checkout': str(REVIEW), 'run_folder': str(folder),
    'runner': str(runner), 'runner_sha256': sha(runner), 'functional_source_files': 1029, 'approved_runtime_executables': 6,
    'original_SourceIO574_and_owned_copy_preserved': True, 'exporter120_preserved': True, 'retained_native_fixture_files': 36,
    'native_fixture_bytes': 31109803, 'expected_groups': 158, 'core_groups': 36, 'new_neon_workspace_checks': 12504,
    'actual_source_foundation': 167, 'separate_crosswalk': 77, 'separate_headless_bindings': 96,
    'foundation_root_verification_sha256': sha(focused / 'verification.json'), 'preceding_helper_cpu': 208, 'preceding_helper_graphical': 266,
    'sole_functional_delta_from_375': 'tests/source_bone_bindings_unit.gd one CR stripping expression; product unchanged',
    'preceding_failed_full_preserved_and_closed': True, 'candidate_reconstruction_index_sha256': sha(ROOT / 'experiments/neon_fe9_candidate_reconstruction_20261117/INDEX.json'),
    'review_branch_fe9_upload': 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION_MAIN_PACKET_PENDING', 'main_merged': False, 'result': 'UNRUN'}
(folder / 'preflight-source.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8', newline='\n')
for path in (packet / 'PREPARATION.json', folder / 'preparation.json'):
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
