"""CPU source inverse and pure gates only; never execute the preflight helper."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
original = ROOT / 'experiments/prepare_neon_00bf_full_actual_20261117.py'
successor = ROOT / 'experiments/prepare_neon_696_full_actual_20261117.py'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
raw = original.read_bytes(); assert sha(raw) == 'da3985153792fa2e60f517b953fb308baaab5634711d51a4f5f34321d1734f2b'
old = raw.decode('utf-8'); new = successor.read_text(encoding='utf-8')
compile(new, str(successor), 'exec')
inverse = new
for label in ('FOCUSED AND RELEASE GATES', 'SOURCE PINS', 'PWSH SEAL'):
    inverse, count = re.subn('^# BEGIN 696 ' + label + '\n.*?^# END 696 ' + label + '\n', '', inverse, flags=re.M | re.S)
    assert count == 1, label
changes = {
    '"""Fresh strict full reservation after native catalogue/comparison/height success."""': '"""Fresh696 full reservation only after actual root-sealed camera/Neon/control success."""',
    "REV = '00bf0f916a549f5e858cb39dd91a149071fd5181'": "REV = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'",
    "focused = REVIEW / 'output/neon-catalogue-00bf0f9-20261117-attempt1'": "focused = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1'",
    "check = load(focused / 'verification.json')\nassert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True\nassert [(row['label'], row['report']['checks'], row['report']['failures']) for row in check['rows']] == [('catalogue', 130, 0), ('comparison', 94, 0), ('height', 105, 0)]\nassert check['rows'][0]['report']['unit_checks'] == 34 and 'Supplied Mima' in check['rows'][0]['report']['plans']\nassert check['rows'][2]['report']['native_import'] == {'checks': 9, 'failures': 0}": "assert sha(focused / 'verification.json') == FOCUSED_VERIFICATION_SHA256\ncheck = load(focused / 'verification.json')\nvalidate_focused(check)",
    "prior_run = REVIEW / 'output/windows-neon-fe9aace-20261117T040348'": "prior_run = REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051'",
    "assert release['released'] is True and release['physical_jobs'] == 68": "validate_prior_release(release)\nassert sha(prior_run / 'source-before.json') == '5064dc9e7932cfb05360e3df974dbbeb56cae682bfade6cb286e3040302ab67f'",
    "assert {name for name in sources if sources[name] != old[name]} == {'tests/verify_shape_catalog.py', 'tests/verify_character_height.py'}": "assert {name for name in sources if sources[name] != old[name]} == {'src/app.gd', 'tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'}",
    "folder = REVIEW / 'output' / ('windows-neon-00bf0f9-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))": "folder = REVIEW / 'output' / ('windows-neon-696ca7f-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))",
    "packet = ROOT / 'experiments/neon_windows_00bf0f9_20261117'": "packet = ROOT / 'experiments/neon_windows_696ca7f_20261117'",
    "'format': 'has_neon_00bf_full_windows_preparation_1'": "'format': 'has_neon_696_full_windows_preparation_1'",
    "'runner': str(runner), 'runner_sha256': sha(runner),": "'runner': str(runner), 'runner_sha256': sha(runner), 'powershell': str(powershell), 'powershell_sha256': sha(powershell),",
    "'actual_focused_checks': {'catalogue': 130, 'catalogue_unit': 34, 'comparison': 94, 'height': 105, 'raw_VRM': 9}": "'actual_focused_checks': {'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48}",
    "'sole_functional_delta': 'two test fixture selectors; product source unchanged'": "'sole_functional_delta': 'one existing camera-inspector refresh; exact two app-hash manifest rows; test predicates unchanged'",
}
for before, after in changes.items():
    assert inverse.count(after) == 1, after
    inverse = inverse.replace(after, before, 1)
assert inverse.encode('utf-8') == raw, 'Unexpected source change outside approved context/gates'
assert new[new.index("lock = load(ROOT"):new.index('folder = REVIEW')].split('# BEGIN 696 PWSH SEAL')[0] == old[old.index("lock = load(ROOT"):old.index('folder = REVIEW')]
tree = ast.parse(new)
assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr in {'Popen', 'run', 'call', 'check_call'} for node in ast.walk(tree))
pin, = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'FOCUSED_VERIFICATION_SHA256' for target in node.targets)]
assert pin == '9a0a959734ae56925af31a63207ba711ff6443fe44b38ef8f14425f64aa6bb4c'
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'validate_focused', 'validate_prior_release'}]
assert len(nodes) == 2
namespace = {}; exec(compile(ast.Module(body=nodes, type_ignores=[]), '<pure696gates>', 'exec'), namespace)
focused = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1'
focus_raw = (focused / 'verification.json').read_bytes(); assert sha(focus_raw) == pin
focus = json.loads(focus_raw); namespace['validate_focused'](focus)
before_raw = (focused / 'source-before.json').read_bytes(); after_raw = (focused / 'source-after.json').read_bytes()
assert json.loads(before_raw) == json.loads(after_raw) and len(json.loads(before_raw)) == 1029
release = {'format': 'has_root_neon_ffcf_graphics_lease_release_1', 'released': True,
    'source_commit': '00bf0f916a549f5e858cb39dd91a149071fd5181',
    'canonical_run': 'windows-neon-00bf0f9-replay2-20261117T155709412051', 'physical_jobs': 92,
    'receipt_inventory_sha256': 'acd509905aed7330636e0300d6ed48b9453ec1d1ed3a121130dba7509b888328',
    'release_kind': 'closed_failed_partial_run', 'full_suite_passed': False, 'final_full_report_used': False,
    'suite_exit': 1, 'coordinator_pid': 19808, 'python_pid': 8888, 'functional_sources': 1029,
    'all_collected_jobs_desktops_closed_private': True, 'all_inline_exact_physical_matches': True,
    'root_observer_issued_no_termination': True}
namespace['validate_prior_release'](release)
negative = 0
for key in ('coordinator_pid', 'python_pid', 'functional_sources'):
    changed = dict(release); changed[key] = float(changed[key])
    try: namespace['validate_prior_release'](changed)
    except AssertionError: negative += 1
    else: raise AssertionError('Numeric alias accepted: ' + key)
for template, validator, mutations in (
    (focus, namespace['validate_focused'], [('passed', False), ('host_scopes_closed', False), ('all_functional_source_unchanged', False), ('functional_source_files', 1028), ('full_suite_pass_claimed', True), ('rows', [])]),
    (release, namespace['validate_prior_release'], [(key, False if value is True else 'wrong') for key, value in release.items()])):
    for key, value in mutations:
        changed = copy.deepcopy(template); changed[key] = value
        try: validator(changed)
        except (AssertionError, KeyError, TypeError, ValueError): negative += 1
        else: raise AssertionError('Altered gate accepted: ' + key)
for index, key, value in [(0, 'native_models', 4), (0, 'checks', 59), (1, 'checks', 12503), (2, 'checks', 47)]:
    changed = copy.deepcopy(focus); changed['rows'][index]['report'][key] = value
    try: namespace['validate_focused'](changed)
    except (AssertionError, KeyError, TypeError, ValueError): negative += 1
    else: raise AssertionError('Altered focused count accepted')
print(json.dumps({'source_inverse_exact': True, 'protected_input_block_byte_exact': True,
    'compile': True, 'actual_closed_focused_schema_accepted': True, 'focused_source_maps_equal1029': True,
    'prior_release_test_is_RAM_schema_only_actual_output_not_read': True, 'negative_gate_checks': negative,
    'preflight_executed': False, 'runner_launched': False,
    'successor_sha256': sha(successor.read_bytes()), 'checker_sha256': sha(Path(__file__).read_bytes()),
    'focused_before_sha256': sha(before_raw), 'focused_after_sha256': sha(after_raw)}))
