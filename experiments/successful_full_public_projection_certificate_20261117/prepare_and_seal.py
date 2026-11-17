"""Bind fixed public sources, reuse sealed fourteen-test kernel, add four CPU tests."""
from pathlib import Path
import ast
import hashlib
import importlib
import io
import json
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREDECESSOR = ROOT / 'experiments/successful_full_public_projection_20261117'
TERMINAL = ROOT / 'experiments/neon_00bf_terminal_20261117'
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PREDECESSOR_INDEX_SHA = '260f85f4b2e66ea37906b00b95546c453660c52bd0f3c0a80ba746de9282db41'
REGISTRY_SHA = 'b03dc3bf06baf6044a034d17b0c9a430f2cfb364bac762f399fcc53c6a9013eb'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path).absolute()
    assert '..' not in path.parts
    for ancestor in (path, *path.parents):
        assert not ancestor.is_symlink() and not getattr(ancestor.lstat(), 'st_file_attributes', 0) & 0x400
    before = path.stat()
    assert path.is_file() and before.st_size <= 2 * 1024 * 1024
    raw = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return raw


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    assert not (HERE / 'INDEX.json').exists(), 'Sealed source packet is immutable'
    predecessor_index_raw = read(PREDECESSOR / 'INDEX.json')
    assert sha(predecessor_index_raw) == PREDECESSOR_INDEX_SHA
    predecessor_index = json.loads(predecessor_index_raw)
    old = {}
    for row in predecessor_index['files']:
        assert Path(row['path']).name == row['path']
        raw = read(PREDECESSOR / row['path'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        old[row['path']] = raw
    old_profile = json.loads(old['SOURCE_PROFILE.json'])
    old_cpu = json.loads(old['CPU_RECEIPT.json'])
    assert old_cpu['passed'] is True and old_cpu['tests'] == 14 and old_cpu['failures'] == old_cpu['errors'] == 0
    registry_raw = read(TERMINAL / 'RESULT_REGISTRY.json')
    assert sha(registry_raw) == REGISTRY_SHA
    registry = json.loads(registry_raw)
    assert [len(registry[key]) for key in ('expected_result_keys', 'expected_core_process_keys', 'expected_movie_keys')] == [158, 36, 21]
    before = {}
    # Exact public source profile only; never traverse or glob any run/output folder.
    for name, meta in old_profile['sources'].items():
        alias, relative = name.split(':', 1)
        assert alias in ('MAIN', 'REVIEW') and '..' not in Path(relative).parts and not Path(relative).is_absolute()
        root = ROOT if alias == 'MAIN' else REVIEW
        raw = read(root / relative)
        assert len(raw) == meta['bytes'] and sha(raw) == meta['sha256']
        before[name] = raw
    assert sha(before['REVIEW:tests/verify.py']) == registry['verifier_sha256']
    behavior_raw = before['REVIEW:tests/neon_behavior_regression.gd']
    behavior = sorted(re.findall(r'check\("([^"\n]+)"', behavior_raw.decode('utf-8-sig')))
    assert behavior == old_profile['behavior_names'] and len(set(behavior)) == 32
    for name in ('projection_core.py', 'test_projection.py'):
        with (HERE / name).open('xb') as stream:
            stream.write(old[name])
    constants = {
        'SOURCE_COMMIT': registry['source_commit'], 'RESULT_REGISTRY_SHA256': REGISTRY_SHA,
        'BEHAVIOR_SOURCE_SHA256': sha(behavior_raw),
        'EXPECTED_RESULT_KEYS': tuple(registry['expected_result_keys']),
        'EXPECTED_CORE_PROCESS_KEYS': tuple(registry['expected_core_process_keys']),
        'EXPECTED_MOVIE_KEYS': tuple(registry['expected_movie_keys']), 'BEHAVIOR_NAMES': tuple(behavior),
    }
    with (HERE / 'source_registry.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('"""Exact public source-authored registry; no actual run values."""\n')
        for name, value in constants.items():
            stream.write(name + ' = ' + repr(value) + '\n')
    sys.path.insert(0, str(HERE))
    tests = unittest.TestSuite()
    for name in ('test_projection', 'test_certificate_projection'):
        tests.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
    text = io.StringIO()
    outcome = unittest.TextTestRunner(stream=text, verbosity=2).run(tests)
    assert outcome.wasSuccessful() and outcome.testsRun == 18
    for name, raw in before.items():
        alias, relative = name.split(':', 1)
        assert read((ROOT if alias == 'MAIN' else REVIEW) / relative) == raw
    for name, raw in old.items():
        assert read(PREDECESSOR / name) == raw
    assert read(PREDECESSOR / 'INDEX.json') == predecessor_index_raw
    save('SOURCE_BINDING.json', {
        'format': 'has_public_scalar_projection_certificate_source_binding_1',
        'predecessor_index_sha256': PREDECESSOR_INDEX_SHA,
        'public_source_files': old_profile['sources'], 'source_commit': registry['source_commit'],
        'source_files_unchanged_across_CPU_tests': True, 'predecessor_unchanged': True,
        'frozen_result_names': 158, 'frozen_core_names': 36, 'frozen_movie_names': 21,
        'frozen_behavior_names': 32, 'neon_checks': 12504,
        'actual_run_or_certificate_read': False, 'archive_activation_available': False,
    })
    save('CPU_RECEIPT.json', {
        'format': 'has_public_scalar_projection_certificate_authored_CPU_1',
        'passed': True, 'tests': outcome.testsRun, 'predecessor_methods_reused': 14,
        'certificate_source_methods': 4, 'failures': len(outcome.failures), 'errors': len(outcome.errors),
        'output': text.getvalue(), 'actual_full_PASS_or_root_certificate_supplied': False,
        'engine_CIM_Git_network_or_current_REVIEW_output_access': False,
    })
    files = []
    for name in ('certificate_projection.py', 'test_certificate_projection.py', 'projection_core.py', 'test_projection.py', 'source_registry.py', 'prepare_and_seal.py', 'REVIEW.md', 'SOURCE_BINDING.json', 'CPU_RECEIPT.json'):
        raw = read(HERE / name)
        files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
    save('INDEX.json', {
        'format': 'has_source_experiment_index_1', 'packet': HERE.name,
        'status': 'SEALED_SOURCE_ONLY_PRIVATE_COMMITMENT_PROJECTION_ARCHIVE_UNAVAILABLE',
        'files': files,
    })
    print(json.dumps({'passed': True, 'tests': outcome.testsRun, 'source_files_checked': len(before), 'INDEX_sha256': sha(read(HERE / 'INDEX.json')), 'actual_archive_activation_available': False}))


if __name__ == '__main__':
    main()
