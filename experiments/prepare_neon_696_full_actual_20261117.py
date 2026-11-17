"""Fresh696 full reservation only after actual root-sealed camera/Neon/control success."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
REV = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
# BEGIN 696 FOCUSED AND RELEASE GATES
# Root supplied the actual closed focused seal; this source preparation executes no preflight.
FOCUSED_VERIFICATION_SHA256 = '9a0a959734ae56925af31a63207ba711ff6443fe44b38ef8f14425f64aa6bb4c'


def validate_focused(check):
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
    assert release['source_commit'] == '00bf0f916a549f5e858cb39dd91a149071fd5181'
    assert release['canonical_run'] == 'windows-neon-00bf0f9-replay2-20261117T155709412051'
    assert type(release['physical_jobs']) is int and release['physical_jobs'] == 92
    assert release['receipt_inventory_sha256'] == 'acd509905aed7330636e0300d6ed48b9453ec1d1ed3a121130dba7509b888328'
    assert release['release_kind'] == 'closed_failed_partial_run' and release['full_suite_passed'] is False and release['final_full_report_used'] is False
    assert type(release['suite_exit']) is int and release['suite_exit'] != 0
    assert all(type(release[name]) is int for name in ('coordinator_pid', 'python_pid', 'functional_sources'))
    assert release['coordinator_pid'] == 19808 and release['python_pid'] == 8888 and release['functional_sources'] == 1029
    assert release['all_collected_jobs_desktops_closed_private'] is True and release['all_inline_exact_physical_matches'] is True and release['root_observer_issued_no_termination'] is True


assert type(FOCUSED_VERIFICATION_SHA256) is str and len(FOCUSED_VERIFICATION_SHA256) == 64 and all(c in '0123456789abcdef' for c in FOCUSED_VERIFICATION_SHA256), 'Actual focused verification is not yet root-sealed; no preflight reservation allowed'
# END 696 FOCUSED AND RELEASE GATES
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == REV
focused = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1'
assert sha(focused / 'verification.json') == FOCUSED_VERIFICATION_SHA256
check = load(focused / 'verification.json')
validate_focused(check)
prior_run = REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051'
release = load(prior_run / 'graphics-lease-closed.json')
validate_prior_release(release)
assert sha(prior_run / 'source-before.json') == '5064dc9e7932cfb05360e3df974dbbeb56cae682bfade6cb286e3040302ab67f'
paths = [p for d in ('src', 'tests', 'tools', 'data', 'examples') for p in (REVIEW / d).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
paths += [REVIEW / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
assert len(paths) == 1029
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=REVIEW).strip()
sources = {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(paths)}
assert sources == load(focused / 'source-before.json') == load(focused / 'source-after.json')
old = load(prior_run / 'source-before.json')['source_sha256']
assert set(old) == set(sources)
assert {name for name in sources if sources[name] != old[name]} == {'src/app.gd', 'tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'}
# BEGIN 696 SOURCE PINS
assert sources['src/app.gd'] == '79b34e7d591f433e060edf72888d22443d1a0fc5e22dd2a246eb77c83fcad1b6'
assert sources['tests/helper_preview_port_files.json'] == 'e4fd9597bbf1f9371cece5379a62c0982f53bbc32e83fafef13e19c361beebba'
assert sources['tests/wind_review_port_files.json'] == '2db0f61835d9b1918385a31202123b7cbf2e993b047d608a9f0dd1eec4b84de7'
assert sources['tests/camera_range_smoke.gd'] == 'e8b8287451874d26fed4f6ed7d91e463322ed08af179fc80b330150cde841bef'
# END 696 SOURCE PINS
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
folder = REVIEW / 'output' / ('windows-neon-696ca7f-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
folder.mkdir(exist_ok=False)
packet = ROOT / 'experiments/neon_windows_696ca7f_20261117'
packet.mkdir(exist_ok=False)
record = {'format': 'has_neon_696_full_windows_preparation_1', 'revision': REV, 'checkout': str(REVIEW), 'run_folder': str(folder),
    'runner': str(runner), 'runner_sha256': sha(runner), 'powershell': str(powershell), 'powershell_sha256': sha(powershell), 'functional_source_files': 1029, 'approved_runtime_executables': 6,
    'SourceIO_original_and_owned_copy574_preserved': True, 'exporter120_preserved': True, 'retained_native_fixture_files': 36,
    'actual_focused_checks': {'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48},
    'focused_verification_sha256': sha(focused / 'verification.json'), 'additional_input_identities': extra,
    'expected_groups': 158, 'core_groups': 36, 'movie_groups': 21, 'preceding_failed_full_closed': True,
    'sole_functional_delta': 'one existing camera-inspector refresh; exact two app-hash manifest rows; test predicates unchanged', 'main_merged': False,
    'review_branch_upload': 'NOT_ATTEMPTED_AFTER_PRIOR_REJECTION_MAIN_RECONSTRUCTION_PENDING', 'result': 'UNRUN'}
(folder / 'preflight-source.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8', newline='\n')
for target in (folder / 'preparation.json', packet / 'PREPARATION.json'):
    target.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
