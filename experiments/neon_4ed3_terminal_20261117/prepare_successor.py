"""Context-only successor preparation; no active run state/report/log reads."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'neon_ffcf_terminal_20261117'
REVIEW = HERE.parents[2] / 'has-neon-review-20261116-c2d52ff'
OLD_COMMIT = 'ffcf4c54ab9ab7af7cb01329a5b3b5b6f4589865'
COMMIT = '4ed3a63b716f696daa1699a76443d6f1abb9b096'
PINS = {
    'INDEX.json': '22e0c12e4a1ee55b079571a4befa01f7c3d75902a151d2a0c918dee5986e7317',
    'close_terminal.py': 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21',
    'legacy_result_gates.py': '0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460',
    'test_terminal.py': '861ded03ac673fa2cf8ab2f0a88192ee42c8d7571fd279d2036ea9479ac8377c',
    'bind_context.py': 'd771101029ac1bf7367bb90947a71062ad5c769ea2d7464aa5b57c3925246882',
    'test_bind_context.py': '53146b2225b99af5ababb3661ac3c4bdce47dcddd35b13dc3825051bdb6de95a',
    'RESULT_REGISTRY.json': '3ffae0d4d19d051a3e46c061b46b813f2fabc38662cb32635d6145a5ea4553b9',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(name, raw):
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


def transform(raw, changes):
    result = raw
    rows = []
    for before, after, count in changes:
        before, after = before.encode(), after.encode()
        assert result.count(before) == count, before
        assert after not in result, after
        result = result.replace(before, after)
        rows.append((before, after, count))
    inverse = result
    for before, after, count in reversed(rows):
        assert inverse.count(after) == count, after
        inverse = inverse.replace(after, before)
    assert inverse == raw
    ast.parse(result)
    return result


def main():
    assert not (HERE / 'INDEX.json').exists() and not (HERE / 'CONTEXT.json').exists()
    old = {name: (OLD / name).read_bytes() for name in PINS}
    for name, raw in old.items():
        assert sha(raw) == PINS[name], name
    for name in ('close_terminal.py', 'legacy_result_gates.py', 'test_terminal.py'):
        write(name, old[name])
    binder = transform(old['bind_context.py'], [
        (OLD_COMMIT, COMMIT, 1),
        ('windows-neon-ffcf4c5-20261117T021833', 'windows-neon-4ed3a63-20261117T030209', 1),
        ('27512', '22224', 2), ('27124', '1820', 1),
        ('2026-11-17T02:22:31.2361797Z', '2026-11-17T03:02:32.4796950Z', 1),
        ('2026-11-17T02:22:31.8526561Z', '2026-11-17T03:02:33.0241444Z', 1),
        ('Exact ffcf1029 source manifest required', 'Exact 4ed31029 source manifest required', 1),
        ('has_neon_ffcf_terminal_source_context_1', 'has_neon_4ed3_terminal_source_context_1', 1),
    ])
    tests = transform(old['test_bind_context.py'], [
        ('2026-11-17T02:22:31.8526560Z', '2026-11-17T03:02:33.0241443Z', 2),
        ('2026-11-17T02:22:31.2361790Z', '2026-11-17T03:02:32.4796940Z', 1),
    ])
    registry = json.loads(old['RESULT_REGISTRY.json'])
    assert registry['source_commit'] == OLD_COMMIT
    registry['source_commit'] = COMMIT
    registry_raw = (json.dumps(registry, indent=2) + '\n').encode()
    registry_inverse = json.loads(registry_raw)
    registry_inverse['source_commit'] = OLD_COMMIT
    assert (json.dumps(registry_inverse, indent=2) + '\n').encode() == old['RESULT_REGISTRY.json']
    assert len(registry['expected_result_keys']) == len(set(registry['expected_result_keys'])) == 158
    assert len(registry['expected_core_process_keys']) == 36 and len(registry['expected_movie_keys']) == 21
    verifier = (REVIEW / 'tests/verify.py').read_bytes()
    assert sha(verifier) == registry['verifier_sha256'] == '192aa4b889a367787f2368f58c95de5813628dbff80b01a5f7e640efdf1f2f0f'
    write('bind_context.py', binder)
    write('test_bind_context.py', tests)
    write('RESULT_REGISTRY.json', registry_raw)
    proof = {
        'status': 'CONTEXT_ONLY_SUCCESSOR_SOURCE_PREPARATION',
        'parent_index_sha256': PINS['INDEX.json'], 'source_commit': COMMIT,
        'close_terminal_entire_file_exact': True, 'legacy_entire_file_exact': True,
        'terminal_tests_entire_file_exact': True,
        'binder_coordinate_and_label_only_exact_inverse': True,
        'binding_tests_timestamp_literals_only_exact_inverse': True,
        'registry_source_commit_only_exact_inverse': True,
        'registry158_core36_movie21': True, 'neon_checks': 12504, 'lifecycle_checks': 29,
        'verifier_entire_file_exact_to_parent': True, 'verifier_sha256': sha(verifier),
        'source_snapshot_expected': 1029, 'physical_job_count': 'DERIVE_ACTUAL_NO_ASSUMPTION',
        'helper_output_format_labels_inherited_ffcf_unchanged': True,
        'helper_sha256': sha(old['close_terminal.py']),
        'binder_sha256': sha(binder), 'registry_sha256': sha(registry_raw),
        'legacy_result_gates_sha256': sha(old['legacy_result_gates.py']),
        'run_state_report_log_read': False, 'observer_engines_CIM_Git_executed': False,
    }
    write('SOURCE_DERIVATION.json', (json.dumps(proof, indent=2) + '\n').encode())
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
