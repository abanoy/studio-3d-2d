"""Fresh strict full reservation after native catalogue/comparison/height success."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
REV = '00bf0f916a549f5e858cb39dd91a149071fd5181'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == REV
focused = REVIEW / 'output/neon-catalogue-00bf0f9-20261117-attempt1'
check = load(focused / 'verification.json')
assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
assert [(row['label'], row['report']['checks'], row['report']['failures']) for row in check['rows']] == [('catalogue', 130, 0), ('comparison', 94, 0), ('height', 105, 0)]
assert check['rows'][0]['report']['unit_checks'] == 34 and 'Supplied Mima' in check['rows'][0]['report']['plans']
assert check['rows'][2]['report']['native_import'] == {'checks': 9, 'failures': 0}
prior_run = REVIEW / 'output/windows-neon-fe9aace-20261117T040348'
release = load(prior_run / 'graphics-lease-closed.json')
assert release['released'] is True and release['physical_jobs'] == 68
paths = [p for d in ('src', 'tests', 'tools', 'data', 'examples') for p in (REVIEW / d).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
paths += [REVIEW / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
assert len(paths) == 1029
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=REVIEW).strip()
sources = {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(paths)}
assert sources == load(focused / 'source-before.json') == load(focused / 'source-after.json')
old = load(prior_run / 'source-before.json')['source_sha256']
assert set(old) == set(sources)
assert {name for name in sources if sources[name] != old[name]} == {'tests/verify_shape_catalog.py', 'tests/verify_character_height.py'}
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
folder = REVIEW / 'output' / ('windows-neon-00bf0f9-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
folder.mkdir(exist_ok=False)
packet = ROOT / 'experiments/neon_windows_00bf0f9_20261117'
packet.mkdir(exist_ok=False)
record = {'format': 'has_neon_00bf_full_windows_preparation_1', 'revision': REV, 'checkout': str(REVIEW), 'run_folder': str(folder),
    'runner': str(runner), 'runner_sha256': sha(runner), 'functional_source_files': 1029, 'approved_runtime_executables': 6,
    'SourceIO_original_and_owned_copy574_preserved': True, 'exporter120_preserved': True, 'retained_native_fixture_files': 36,
    'actual_focused_checks': {'catalogue': 130, 'catalogue_unit': 34, 'comparison': 94, 'height': 105, 'raw_VRM': 9},
    'focused_verification_sha256': sha(focused / 'verification.json'), 'additional_input_identities': extra,
    'expected_groups': 158, 'core_groups': 36, 'movie_groups': 21, 'preceding_failed_full_closed': True,
    'sole_functional_delta': 'two test fixture selectors; product source unchanged', 'main_merged': False,
    'review_branch_upload': 'NOT_ATTEMPTED_AFTER_PRIOR_REJECTION_MAIN_RECONSTRUCTION_PENDING', 'result': 'UNRUN'}
(folder / 'preflight-source.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8', newline='\n')
for target in (folder / 'preparation.json', packet / 'PREPARATION.json'):
    target.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
