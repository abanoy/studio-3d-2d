"""Fresh3a reservation after closed color44/tail44; ancestor camera evidence stays historical."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
REV = '3a3701ab6edfa81dc883759403c170b8555aab07'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
# BEGIN 3A FOCUSED AND RELEASE GATES
# Color is actual closed3a evidence. Camera/Neon/controls are unchanged-app ancestor evidence.
FOCUSED_VERIFICATION_SHA256 = '84569db064d65d35e6fa8f4087bbcd21f18b9a5d8db14a8e0ad29152ea0920b2'
TAIL_VERIFICATION_SHA256 = 'e366426598261c13674aafdd4c8fedc9cb5a350ebfcf8be08bd10906d4011167'
TAIL_COMPLETION_SHA256 = '2ed5edd7bed4a83b2a3245ff73da41d52d7cf5c78ba55d83eba88e5b54e0408a'


def validate_functional_dirt(tracked, untracked):
    # Exact declared functional scope excludes session caches; retain their bytes.
    for names in (tracked, untracked):
        assert type(names) is list and all(type(name) is str for name in names)
        assert not [name for name in names if '__pycache__' not in Path(name).parts and Path(name).suffix != '.pyc']


def validate_source_delta(sources, old):
    assert type(sources) is dict and type(old) is dict and len(sources) == len(old) == 1029
    assert set(sources) == set(old)
    assert {name for name in sources if sources[name] != old[name]} == {'tests/color_sampler_smoke.gd'}
    assert old['tests/color_sampler_smoke.gd'] == '7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141'
    assert sources['tests/color_sampler_smoke.gd'] == '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'


def validate_focused(check):
    assert check['format'] == 'has_root_workspace_followup_1'
    assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
    assert type(check['functional_source_files']) is int and check['functional_source_files'] == 1029
    assert check['full_suite_pass_claimed'] is False
    row, = check['rows']
    assert row['label'] == 'color' and type(row['exit']) is int and row['exit'] == 0
    assert row['retained_Popen_reaped'] is True and row['timed_out'] is False
    report = row['report']
    assert type(report['checks']) is int and report['checks'] == 44
    assert type(report['failures']) is int and report['failures'] == 0
    assert type(report['native_projects']) is list and len(report['native_projects']) == 3


def validate_ancestor_focused(check):
    assert check['format'] == 'has_root_workspace_followup_1'
    assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
    assert type(check['functional_source_files']) is int and check['functional_source_files'] == 1029
    assert check['full_suite_pass_claimed'] is False
    assert [(row['label'], row['report']['checks'], row['report']['failures']) for row in check['rows']] == [('camera', 60, 0), ('neon', 12504, 0), ('controls', 48, 0)]
    for row in check['rows']:
        assert type(row['exit']) is int and row['exit'] == 0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False
        assert type(row['report']['checks']) is int and type(row['report']['failures']) is int
    camera, neon, controls = [row['report'] for row in check['rows']]
    assert type(camera['native_models']) is int and camera['native_models'] == 5
    assert neon['format'] == 'has_neon_workspace_verification_1' and neon['passed'] is True
    assert neon['expected_checks'] == {'inset': 12384, 'behavior': 32, 'compact': 14, 'rail': 45, 'lifecycle': 29}
    assert neon['all_functional_sources_hash_size_mtime_unchanged'] is True and neon['all_private_jobs_and_desktops_closed'] is True


def validate_prior_release(release):
    assert release['format'] == 'has_root_neon_ffcf_graphics_lease_release_1' and release['released'] is True
    assert release['source_commit'] == '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
    assert release['canonical_run'] == 'windows-neon-696ca7f-20261117T170720480423'
    assert type(release['physical_jobs']) is int and release['physical_jobs'] == 93
    assert release['receipt_inventory_sha256'] == 'c11d074afa51f2144cce34eb4605280aea39f789904cf327e4fc30cbcfa96e97'
    assert release['release_kind'] == 'closed_failed_partial_run' and release['full_suite_passed'] is False and release['final_full_report_used'] is False
    assert type(release['suite_exit']) is int and release['suite_exit'] == 1
    assert all(type(release[name]) is int for name in ('coordinator_pid', 'python_pid', 'functional_sources'))
    assert release['coordinator_pid'] == 12740 and release['python_pid'] == 5384 and release['functional_sources'] == 1029
    assert release['released_utc'] == '2026-11-17T17:42:05.1961829Z'
    assert release['all_collected_jobs_desktops_closed_private'] is True and release['all_inline_exact_physical_matches'] is True and release['root_observer_issued_no_termination'] is True


def validate_tail(check, completion, cases, canonical_report):
    assert check['format'] == 'has_root_workspace_followup_1'
    assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
    assert type(check['functional_source_files']) is int and check['functional_source_files'] == 1029
    assert check['full_suite_pass_claimed'] is False
    assert len(cases) == 44 and len(check['rows']) == 44
    assert [row['label'] for row in check['rows']] == [row[0] for row in cases]
    for row in check['rows']:
        assert type(row['exit']) is int and row['exit'] == 0
        assert row['retained_Popen_reaped'] is True and row['timed_out'] is False and type(row['report']) is dict
        canonical_report(row['label'], row['report'])
    assert completion['format'] == 'has_targeted_neon_late_stage_completion_1'
    assert completion['candidate_commit'] == '3a3701ab6edfa81dc883759403c170b8555aab07'
    assert type(completion['expected_wrappers']) is int and completion['expected_wrappers'] == 44
    assert completion['all44_completed_and_canonical_reports_passed'] is True
    assert type(completion['host_return']) is int and completion['host_return'] == 0
    assert completion['full_PASS_or_merge_claimed'] is False


for pin in (FOCUSED_VERIFICATION_SHA256, TAIL_VERIFICATION_SHA256, TAIL_COMPLETION_SHA256):
    assert type(pin) is str and len(pin) == 64 and all(c in '0123456789abcdef' for c in pin), 'Actual closed focused/tail seals required before reservation'
# END 3A FOCUSED AND RELEASE GATES
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == REV
focused = REVIEW / 'output/neon-color-center-3a3701a-attempt1'
assert sha(focused / 'verification.json') == FOCUSED_VERIFICATION_SHA256
check = load(focused / 'verification.json')
validate_focused(check)
assert sha(focused / 'source-before.json') == '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'
assert sha(focused / 'source-after.json') == '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'
ancestor_focus = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1'
assert sha(ancestor_focus / 'verification.json') == '9a0a959734ae56925af31a63207ba711ff6443fe44b38ef8f14425f64aa6bb4c'
validate_ancestor_focused(load(ancestor_focus / 'verification.json'))
late_packet = ROOT / 'experiments/neon_late_stage_cases_source_20261117'
assert sha(late_packet / 'INDEX.json') == '790277ef5e25f78e63d46350dba0304dce6c083c84ad5e010ac478fcea865ea3'
for row in load(late_packet / 'INDEX.json')['files']:
    path = late_packet / row['path']
    assert path.resolve().is_relative_to(late_packet) and not path.is_symlink()
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
assert sha(late_packet / 'late_cases.py') == '6a2f0b07dd684dbfcb99ac89b35f4fbe93891a735ada368fa543d38db25b2f43'
late_spec = importlib.util.spec_from_file_location('root_sealed3a_late_cases', late_packet / 'late_cases.py')
late = importlib.util.module_from_spec(late_spec); late_spec.loader.exec_module(late)
late.check_source((REVIEW / 'tests/verify.py').read_bytes(), (ROOT / 'experiments/run_neon_scene_followup_20261117.py').read_bytes())
tail = REVIEW / 'output/neon-late-3a-attempt2'
assert sha(tail / 'verification.json') == TAIL_VERIFICATION_SHA256
assert sha(tail / 'TARGETED-COMPLETION.json') == TAIL_COMPLETION_SHA256
validate_tail(load(tail / 'verification.json'), load(tail / 'TARGETED-COMPLETION.json'), late.CASES, late.assert_canonical_report)
for name in ('source-before.json', 'source-after.json'):
    assert sha(tail / name) == '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'
prior_run = REVIEW / 'output/windows-neon-696ca7f-20261117T170720480423'
release = load(prior_run / 'graphics-lease-closed.json')
validate_prior_release(release)
assert sha(prior_run / 'source-before.json') == '594cf0dfc7c28c402e5ddd01a81f42c6764761a969e1758df0ae37757b061eab'
paths = [p for d in ('src', 'tests', 'tools', 'data', 'examples') for p in (REVIEW / d).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
paths += [REVIEW / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
assert len(paths) == 1029
functional_scope = ('src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw')
tracked_dirt = subprocess.check_output(['git', 'diff', '--name-only', '--', *functional_scope], cwd=REVIEW, text=True).splitlines()
untracked_dirt = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', *functional_scope], cwd=REVIEW, text=True).splitlines()
validate_functional_dirt(tracked_dirt, untracked_dirt)
sources = {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(paths)}
assert sources == load(focused / 'source-before.json') == load(focused / 'source-after.json')
old = load(prior_run / 'source-before.json')['source_sha256']
assert set(old) == set(sources)
assert load(ancestor_focus / 'source-before.json') == load(ancestor_focus / 'source-after.json') == old
validate_source_delta(sources, old)
# BEGIN 3A SOURCE PINS
assert sources['src/app.gd'] == '79b34e7d591f433e060edf72888d22443d1a0fc5e22dd2a246eb77c83fcad1b6'
assert sources['tests/helper_preview_port_files.json'] == 'e4fd9597bbf1f9371cece5379a62c0982f53bbc32e83fafef13e19c361beebba'
assert sources['tests/wind_review_port_files.json'] == '2db0f61835d9b1918385a31202123b7cbf2e993b047d608a9f0dd1eec4b84de7'
assert sources['tests/camera_range_smoke.gd'] == 'e8b8287451874d26fed4f6ed7d91e463322ed08af179fc80b330150cde841bef'
assert sources['tests/color_sampler_smoke.gd'] == '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
# END 3A SOURCE PINS
assert sources['tests/verify_shape_catalog.py'] == '54431c2c486bce9828ec47ebe046da9f413b3854e8c0290829c24183fe72e057'
assert sources['tests/verify_character_height.py'] == 'cccfb7d472b5d552cbd3cfc07dc9058c1789b9c1947f6a1a548c924dd38a3f79'
lock = load(ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json')
spec = importlib.util.spec_from_file_location('neon_00bf_approved_input_reader', ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py')
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
prepared = load(ROOT / 'experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json')
descriptor = Path(prepared['descriptor_path'])
assert sha(descriptor) == prepared['descriptor_sha256']
scene = Path(prepared['bundle']) / 'scene.glb'
assert audit.identity(scene) == prepared['scene']
native_descriptor = ROOT / 'output/native-import-verification.json'
extra = {str(descriptor): audit.identity(descriptor), str(scene): audit.identity(scene), str(native_descriptor): audit.identity(native_descriptor)}
for bundle_name in load(native_descriptor).get('bundles', []):
    bundle = Path(bundle_name)
    parameter_path = bundle / 'parameters.json'
    params = load(parameter_path)
    if params.get('kind') == 'vrm_preparation':
        raw = bundle / 'native' / params.get('source_file', '')
        if raw.is_file():
            identity = audit.identity(raw)
            assert identity['sha256'] == params['source_sha256']
            extra[str(raw)] = identity
runner = ROOT / 'experiments/neon_windows_original_20261116/run_canonical_owned.ps1'
assert sha(runner) == '8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4'
# BEGIN 696 PWSH SEAL
powershell = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
assert sha(powershell) == '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
# END 696 PWSH SEAL
folder = REVIEW / 'output' / ('windows-neon-3a3701a-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
folder.mkdir(exist_ok=False)
packet = ROOT / 'experiments/neon_windows_3a3701a_20261117'
packet.mkdir(exist_ok=False)
record = {'format': 'has_neon_3a3701a_full_windows_preparation_1', 'revision': REV, 'checkout': str(REVIEW), 'run_folder': str(folder),
    'runner': str(runner), 'runner_sha256': sha(runner), 'powershell': str(powershell), 'powershell_sha256': sha(powershell), 'functional_source_files': 1029, 'approved_runtime_executables': 6,
    'SourceIO_original_and_owned_copy574_preserved': True, 'exporter120_preserved': True, 'retained_native_fixture_files': 36,
    'actual_focused_checks': {'color': 44, 'native_projects': 3, 'late_wrappers': 44},
    'ancestor696_focused_checks_not_fresh3a': {'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48},
    'tail_verification_sha256': TAIL_VERIFICATION_SHA256, 'tail_completion_sha256': TAIL_COMPLETION_SHA256,
    'main_metadata_checkpoint': '855d67fe44868793a29d6c6c75c61c0ba86236d2',
    'main_functional_source_commit': '52f63c944ded7a651da871524d23a345b606424d', 'main_functional_sources': 1019,
    'focused_verification_sha256': sha(focused / 'verification.json'), 'additional_input_identities': extra,
    'expected_groups': 158, 'core_groups': 36, 'movie_groups': 21, 'preceding_failed_full_closed': True,
    'sole_functional_delta': 'one native fixture click targets the same expected pixel center; all assertions/thresholds/cases and app/helper/wind bytes unchanged',
    'dirt_check_ignores_only_declared_pycache_and_pyc_scope_exclusions': True, 'cache_reset_or_deleted': False, 'main_merged': False,
    'review_branch_upload': 'NOT_ATTEMPTED_AFTER_PRIOR_REJECTION_MAIN_RECONSTRUCTION_PENDING', 'result': 'UNRUN'}
(folder / 'preflight-source.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8', newline='\n')
for target in (folder / 'preparation.json', packet / 'PREPARATION.json'):
    target.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
