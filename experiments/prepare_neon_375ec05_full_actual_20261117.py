"""Fresh full reservation after actual helper208/266 and preceding run closure."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
REV = '375ec05e925159850ff3b0abf2e8f98f9d2ce129'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == REV
focused = REVIEW / 'output/neon-helper-375ec05-20261117-attempt1'
check = load(focused / 'verification.json')
assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
assert check['revision'] == REV and [(row['mode'], row['report']['checks']) for row in check['rows']] == [('cpu', 208), ('graphical', 266)]
assert all(row['root_exact_suite_assertions_passed'] is True for row in check['rows'])
assert all(load(focused / f'{label}-worker-closure.json')['owned_count'] == 0 for label in ('before', 'cpu-after', 'graphical-after', 'after'))
release = load(REVIEW / 'output/windows-neon-4ed3a63-20261117T030209/graphics-lease-closed.json')
assert release['released'] is True and release['physical_jobs'] == 49
files = [p for d in ('src', 'tests', 'tools', 'data', 'examples') for p in (REVIEW / d).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
files += [REVIEW / n for n in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
assert len(files) == 1029
assert subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=REVIEW) == b''
sources = {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(files)}
assert sources == load(focused / 'source-before.json') == load(focused / 'source-after.json')
old = load(REVIEW / 'output/windows-neon-4ed3a63-20261117T030209/source-before.json')['source_sha256']
assert set(old) == set(sources) and [name for name in sources if sources[name] != old[name]] == ['tests/helper_preview_port_files.json']
assert sources['tests/helper_preview_port_files.json'] == '2c9e483649108b9760aeb96e20c8ac95025a4b595fa0cfbb730308247fb7a8f0'
lock = load(ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json')
reader = ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
spec = importlib.util.spec_from_file_location('neon_375_approved_input_reader', reader)
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
folder = REVIEW / 'output' / ('windows-neon-375ec05-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
folder.mkdir(exist_ok=False)
packet = ROOT / 'experiments/neon_windows_375ec05_20261117'
packet.mkdir(exist_ok=False)
record = {'format': 'has_neon_375_full_windows_preparation_1', 'revision': REV, 'checkout': str(REVIEW), 'run_folder': str(folder),
    'runner': str(runner), 'runner_sha256': sha(runner), 'functional_source_files': 1029, 'approved_runtime_executables': 6,
    'original_SourceIO574_and_owned_copy_preserved': True, 'exporter120_preserved': True, 'retained_native_fixture_files': 36,
    'native_fixture_bytes': 31109803, 'expected_groups': 158, 'core_groups': 36, 'new_neon_workspace_checks': 12504,
    'actual_helper_focused_cpu': 208, 'actual_helper_focused_graphical': 266, 'helper_focused_verification_sha256': sha(focused / 'verification.json'),
    'preceding_failed_full_preserved_and_closed': True, 'candidate_reconstruction_index_sha256': sha(ROOT / 'experiments/neon_375_candidate_reconstruction_20261117/INDEX.json'),
    'review_branch_backup_375': 'AUTO_REVIEW_REJECTED_NOT_RETRIED_MAIN_PACKET_PUBLICATION_PENDING', 'main_merged': False, 'result': 'UNRUN'}
(folder / 'preflight-source.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8', newline='\n')
for path in (packet / 'PREPARATION.json', folder / 'preparation.json'):
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
