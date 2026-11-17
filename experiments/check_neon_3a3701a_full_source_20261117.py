"""Exact inverse, compiled source and authored RAM gate negatives; no preflight IO."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'experiments/neon_3a3701a_full_preflight_source_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
bindings = json.loads((FOLDER / 'BINDINGS.json').read_bytes())
derive_path = FOLDER / 'derive_source.py'
assert sha(derive_path.read_bytes()) == bindings['derive_source_sha256']
spec = importlib.util.spec_from_file_location('pure_exact3a_derivation', derive_path)
D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
base = (ROOT / 'experiments/prepare_neon_696_full_actual_20261117.py').read_bytes()
assert sha(base) == bindings['base_preparer_sha256'] == D.BASE_SHA
assert sha((ROOT / 'experiments/check_neon_696_full_source_20261117.py').read_bytes()) == bindings['base_checker_sha256']
successor = ROOT / 'experiments/prepare_neon_3a3701a_full_actual_20261117.py'
raw = successor.read_bytes(); new = raw.decode('utf-8'); old = base.decode('utf-8')
expected, changes = D.derive(base, bindings['tail_verification_sha256'], bindings['tail_completion_sha256'])
assert expected == raw
compile(new, str(successor), 'exec')
inverse = new
for before, after in reversed(changes):
    assert inverse.count(after) == 1
    inverse = inverse.replace(after, before, 1)
assert inverse.encode('utf-8') == base
protected = lambda text: text[text.index('lock = load(ROOT'):text.index('folder = REVIEW')]
assert protected(new) == protected(old), 'Every original runtime/SourceIO/exporter/native/VRM/Mima/runner/Pwsh guard is byte-exact'
tree = ast.parse(new)
assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr in {'Popen', 'run', 'call', 'check_call'} for node in ast.walk(tree))
names = {'validate_functional_dirt', 'validate_source_delta', 'validate_focused',
         'validate_ancestor_focused', 'validate_prior_release', 'validate_tail'}
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in functions} == names
namespace = {'Path': Path}
exec(compile(ast.Module(body=functions, type_ignores=[]), '<pure3a_gate_functions_only>', 'exec'), namespace)
late_path = ROOT / 'experiments/neon_late_stage_cases_source_20261117/late_cases.py'
late_raw = late_path.read_bytes()
assert sha(late_raw) == '6a2f0b07dd684dbfcb99ac89b35f4fbe93891a735ada368fa543d38db25b2f43'
late_tree = ast.parse(late_raw)
cases, = [ast.literal_eval(node.value) for node in late_tree.body if isinstance(node, ast.Assign)
          and any(isinstance(target, ast.Name) and target.id == 'CASES' for target in node.targets)]
assert len(cases) == 44
canonical, = [node for node in late_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'assert_canonical_report']
late_namespace = {'CASES': cases}
exec(compile(ast.Module(body=[canonical], type_ignores=[]), '<pure_sealed_late_report_predicate_only>', 'exec'), late_namespace)


def row(label, report):
    return {'label': label, 'exit': 0, 'retained_Popen_reaped': True, 'timed_out': False, 'report': report}


def followup(rows):
    return {'format': 'has_root_workspace_followup_1', 'passed': True, 'host_scopes_closed': True,
            'all_functional_source_unchanged': True, 'functional_source_files': 1029,
            'full_suite_pass_claimed': False, 'rows': rows}


color = followup([row('color', {'checks': 44, 'failures': 0,
                              'native_projects': ['AUTHORED_A', 'AUTHORED_B', 'AUTHORED_C']})])
ancestor = followup([row('camera', {'checks': 60, 'failures': 0, 'native_models': 5}),
    row('neon', {'checks': 12504, 'failures': 0, 'format': 'has_neon_workspace_verification_1', 'passed': True,
        'expected_checks': {'inset': 12384, 'behavior': 32, 'compact': 14, 'rail': 45, 'lifecycle': 29},
        'all_functional_sources_hash_size_mtime_unchanged': True, 'all_private_jobs_and_desktops_closed': True}),
    row('controls', {'checks': 48, 'failures': 0})])
release = {'format': 'has_root_neon_ffcf_graphics_lease_release_1', 'released': True,
    'source_commit': '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9',
    'canonical_run': 'windows-neon-696ca7f-20261117T170720480423', 'physical_jobs': 93,
    'receipt_inventory_sha256': 'c11d074afa51f2144cce34eb4605280aea39f789904cf327e4fc30cbcfa96e97',
    'release_kind': 'closed_failed_partial_run', 'full_suite_passed': False, 'final_full_report_used': False,
    'suite_exit': 1, 'coordinator_pid': 12740, 'python_pid': 5384, 'functional_sources': 1029,
    'released_utc': '2026-11-17T17:42:05.1961829Z', 'all_collected_jobs_desktops_closed_private': True,
    'all_inline_exact_physical_matches': True, 'root_observer_issued_no_termination': True}
report = {'checks': 1, 'failures': 0, 'writer': {'failures': 0}, 'readers': {'AUTHORED': {'failures': 0}},
          'reader': {'failures': 0}, 'fresh_readers': [{}, {}, {}, {}]}
tail = followup([row(case[0], copy.deepcopy(report)) for case in cases])
completion = {'format': 'has_targeted_neon_late_stage_completion_1',
    'candidate_commit': '3a3701ab6edfa81dc883759403c170b8555aab07', 'expected_wrappers': 44,
    'all44_completed_and_canonical_reports_passed': True, 'host_return': 0, 'full_PASS_or_merge_claimed': False}
tail_gate = lambda check, final: namespace['validate_tail'](check, final, cases, late_namespace['assert_canonical_report'])
namespace['validate_focused'](color); namespace['validate_ancestor_focused'](ancestor)
namespace['validate_prior_release'](release); tail_gate(tail, completion)
negative = 0


def refuses(fn, *args):
    global negative
    try:
        fn(*args)
    except (AssertionError, KeyError, TypeError, ValueError):
        negative += 1
    else:
        raise AssertionError('Altered authored gate unexpectedly admitted')


for fixture, validator in ((color, namespace['validate_focused']), (ancestor, namespace['validate_ancestor_focused'])):
    for key, bad in [('passed', False), ('host_scopes_closed', False), ('all_functional_source_unchanged', False),
                     ('functional_source_files', 1028), ('functional_source_files', 1029.0),
                     ('full_suite_pass_claimed', True), ('rows', [])]:
        mutated = copy.deepcopy(fixture); mutated[key] = bad; refuses(validator, mutated)
    for index in range(len(fixture['rows'])):
        for key, bad in [('exit', 1), ('exit', False), ('retained_Popen_reaped', False), ('timed_out', True)]:
            mutated = copy.deepcopy(fixture); mutated['rows'][index][key] = bad; refuses(validator, mutated)
for key, bad in [('checks', 43), ('checks', 44.0), ('failures', 1), ('failures', False), ('native_projects', ['A', 'B'])]:
    mutated = copy.deepcopy(color); mutated['rows'][0]['report'][key] = bad; refuses(namespace['validate_focused'], mutated)
for index, key, bad in [(0, 'native_models', 4), (0, 'checks', 59), (1, 'checks', 12503), (2, 'checks', 47)]:
    mutated = copy.deepcopy(ancestor); mutated['rows'][index]['report'][key] = bad; refuses(namespace['validate_ancestor_focused'], mutated)
for key, value in release.items():
    mutated = copy.deepcopy(release); mutated[key] = False if value is True else 'WRONG'; refuses(namespace['validate_prior_release'], mutated)
for key in ('physical_jobs', 'coordinator_pid', 'python_pid', 'functional_sources', 'suite_exit'):
    mutated = copy.deepcopy(release); mutated[key] = float(mutated[key]); refuses(namespace['validate_prior_release'], mutated)
for key, bad in [('passed', False), ('host_scopes_closed', False), ('all_functional_source_unchanged', False),
                 ('functional_source_files', 1028), ('full_suite_pass_claimed', True), ('rows', tail['rows'][:-1]),
                 ('rows', list(reversed(tail['rows'])))]:
    mutated = copy.deepcopy(tail); mutated[key] = bad; refuses(tail_gate, mutated, completion)
for key, bad in [('exit', 1), ('exit', False), ('retained_Popen_reaped', False), ('timed_out', True)]:
    mutated = copy.deepcopy(tail); mutated['rows'][0][key] = bad; refuses(tail_gate, mutated, completion)
for key, value in completion.items():
    mutated = copy.deepcopy(completion); mutated[key] = False if value is True else 'WRONG'; refuses(tail_gate, tail, mutated)
for key in ('expected_wrappers', 'host_return'):
    mutated = copy.deepcopy(completion); mutated[key] = float(mutated[key]); refuses(tail_gate, tail, mutated)
for label, field in [('contact_animation', 'failures'), ('contact_persistence', 'writer'),
                     ('project_duration', 'fresh_readers'), ('motion_editor', 'reader')]:
    mutated = copy.deepcopy(tail); record = next(item for item in mutated['rows'] if item['label'] == label)
    record['report'][field] = {'failures': 1} if field in ('writer', 'reader') else ([] if field == 'fresh_readers' else 1)
    refuses(tail_gate, mutated, completion)
namespace['validate_functional_dirt']([], [])
namespace['validate_functional_dirt'](['tests/__pycache__/has_project.cpython-313.pyc'], ['tools/A.pyc'])
for dirt in ('src/app.gd', 'tests/new.py', 'tools/new.py', 'data/new.txt', 'examples/new.json', 'project.godot',
             'main.tscn', 'run.py', 'launch.pyw', 'src/cache.pyc.gd', 'src/not__pycache__/app.gd'):
    refuses(namespace['validate_functional_dirt'], [dirt], [])
    refuses(namespace['validate_functional_dirt'], [], [dirt])
baseline = (ROOT / 'experiments/neon_windows_696ca7f_20261117/active-observation/source-before.json').read_bytes()
assert sha(baseline) == '594cf0dfc7c28c402e5ddd01a81f42c6764761a969e1758df0ae37757b061eab'
old_map = json.loads(baseline)['source_sha256']; current = dict(old_map)
current['tests/color_sampler_smoke.gd'] = '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
namespace['validate_source_delta'](current, old_map)
for name in ('src/app.gd', 'tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'):
    mutated = dict(current); mutated[name] = '0' * 64; refuses(namespace['validate_source_delta'], mutated, old_map)
mutated = dict(current); mutated['src/REAL_UNTRACKED_ADDITION.gd'] = '0' * 64; refuses(namespace['validate_source_delta'], mutated, old_map)
mutated = dict(current); del mutated['src/app.gd']; refuses(namespace['validate_source_delta'], mutated, old_map)
refuses(namespace['validate_source_delta'], old_map, old_map)
assert len(current) == len(old_map) == 1029 and sum(current[name] == old_map[name] for name in old_map) == 1028
pending = bindings['tail_verification_sha256'] is None or bindings['tail_completion_sha256'] is None
print(json.dumps({'source_inverse_exact': True, 'protected_input_block_byte_exact': True,
    'compile': True, 'pure_RAM_gate_positive_schemas_accepted': True, 'negative_gate_checks': negative,
    'public696map_plus_exact_one_test_pin1029': True, 'all1028other_pins_identical': True,
    'cache_only_exclusion_accepted_real_tracked_and_untracked_dirt_refused': True,
    'original696preflight_and_checker_unchanged': True, 'actual_current_focus_tail_release_files_read': False,
    'tail_admission_pending_actual_closed_Root_hashes': pending,
    'preflight_executed': False, 'runner_launched': False, 'Review_or_cache_or_Git_mutation': False,
    'successor_sha256': sha(raw), 'checker_sha256': sha(Path(__file__).read_bytes())}))
