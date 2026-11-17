"""CPU-only source inverse; never import or execute the preparation helper."""
from pathlib import Path
import ast
import copy
import datetime
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
original = ROOT / 'experiments/prepare_neon_00bf_full_actual_20261117.py'
successor = original.with_name('prepare_neon_00bf_full_replay2_actual_20261117.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == 'da3985153792fa2e60f517b953fb308baaab5634711d51a4f5f34321d1734f2b'
old = original.read_text(encoding='utf-8')
new = successor.read_text(encoding='utf-8')
compile(new, str(successor), 'exec')
assert len(re.findall(r'^# BEGIN ROOT RESTART PROOF GATE$', new, re.M)) == 1
assert len(re.findall(r'^# END ROOT RESTART PROOF GATE$', new, re.M)) == 1
inverse, removed = re.subn(r'^# BEGIN ROOT RESTART PROOF GATE\n.*?^# END ROOT RESTART PROOF GATE\n', '', new, flags=re.M | re.S)
assert removed == 1
changes = {
    '"""Fresh strict full reservation after native catalogue/comparison/height success."""': '"""Fresh same-candidate replay2 reservation after separately issued restart proof."""',
    "folder = REVIEW / 'output' / ('windows-neon-00bf0f9-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))": "replay_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')\nfolder = REVIEW / 'output' / ('windows-neon-00bf0f9-replay2-' + replay_id)",
    "packet = ROOT / 'experiments/neon_windows_00bf0f9_20261117'": "packet = ROOT / 'experiments' / ('neon_windows_00bf0f9_replay2_20261117-' + replay_id)",
    "'format': 'has_neon_00bf_full_windows_preparation_1'": "'format': 'has_neon_00bf_full_windows_replay2_preparation_1'",
    "'expected_groups': 158, 'core_groups': 36, 'movie_groups': 21, 'preceding_failed_full_closed': True,": "'expected_groups': 158, 'core_groups': 36, 'movie_groups': 21,\n    'historical_fe9aace_failed_full_closed': True, 'replay': 2,\n    'previous_same_candidate_full_result': 'INTERRUPTED_NO_TERMINAL_RESULT',\n    'previous_same_candidate_full_pass_claimed': False,\n    'root_restart_authority': {'path': str(restart_proof_path), 'sha256': sha(restart_proof_path),\n        'private_freeze_manifest_sha256': restart_authority['private_freeze_manifest_sha256'],\n        'old_state_status': 'running', 'old_suite_exit': None, 'all_old_jobs_gracefully_closed': 'unknown'},",
}
for before, after in changes.items():
    assert inverse.count(after) == 1, after
    inverse = inverse.replace(after, before)
assert inverse == old, 'Unexpected changes outside the bounded restart proof and replay2 destinations/status'
tree = ast.parse(new)
assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr in {'Popen', 'run', 'call', 'check_call'} for node in ast.walk(tree))
assert new.count("'8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4'") == 1
runner = ROOT / 'experiments/neon_windows_original_20261116/run_canonical_owned.ps1'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == '8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4'
assert new.count("['git', 'rev-parse', 'HEAD']") == 1
assert new.count("['git', 'diff', '--name-only', '--'") == 1
pin = 'a69367aa1a317da33ac62fc4005c93f1cbac86df4fe6d92df72bd1b45071c3b0'
assert new.count("assert sha(restart_proof_path) == '" + pin + "'") == 1
assert new.index('validate_restart_authority(restart_authority)') < new.index("assert subprocess.check_output(['git', 'rev-parse', 'HEAD']")
proof_path = ROOT / 'experiments/neon_00bf_OS_interruptions_20261117/RESTART_AUTHORITY.json'
raw = proof_path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == pin
proof = json.loads(raw)
validator_node, = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'validate_restart_authority']
namespace = {'ROOT': ROOT, 'REVIEW': ROOT.parent / 'has-neon-review-20261116-c2d52ff',
             'REV': '00bf0f916a549f5e858cb39dd91a149071fd5181', 'datetime': datetime}
exec(compile(ast.Module(body=[validator_node], type_ignores=[]), '<pure-root-proof-validator>', 'exec'), namespace)
validate = namespace['validate_restart_authority']
validate(proof)

def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + (key,))
    elif isinstance(value, list) and value:
        for index, child in enumerate(value):
            yield from leaves(child, path + (index,))
    else:
        yield path, value

negative_checks = 0
for path, value in leaves(proof):
    changed = copy.deepcopy(proof)
    parent = changed
    for part in path[:-1]:
        parent = parent[part]
    if isinstance(value, bool):
        replacement = not value
    elif isinstance(value, int):
        replacement = value + 1
    elif isinstance(value, str):
        replacement = value + '-invalid'
    elif isinstance(value, list):
        replacement = ['unexpected']
    else:
        assert value is None
        replacement = 'fabricated'
    parent[path[-1]] = replacement
    try:
        validate(changed)
    except (AssertionError, KeyError, TypeError, ValueError):
        negative_checks += 1
    else:
        raise AssertionError('Altered root proof accepted: ' + repr(path))
for key in proof:
    changed = copy.deepcopy(proof)
    del changed[key]
    try:
        validate(changed)
    except (AssertionError, KeyError, TypeError, ValueError):
        negative_checks += 1
    else:
        raise AssertionError('Incomplete root proof accepted: ' + key)
print(json.dumps({'source_inverse': True, 'successor_compile': True,
                  'original_guards_exact': True, 'preflight_executed': False,
                  'canonical_runner_seal_unchanged': True,
                  'actual_root_proof_accepted': True, 'negative_root_proof_checks': negative_checks,
                  'runner_launched': False, 'successor_sha256': hashlib.sha256(successor.read_bytes()).hexdigest()}))
