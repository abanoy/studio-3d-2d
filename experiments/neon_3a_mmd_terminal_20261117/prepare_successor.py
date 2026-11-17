"""Bind a fresh strict context from original7ed; never use unqualified closure code."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'neon_3a_terminal_20261117'
PARENT_INDEX = '7ed937daaf6b2b1c39b6c0d877243f2e6fdec0215bb86a34bfbf897baaf0fd62'
CHANGES = {
    'bind_context.py': [
        ('windows-neon-3a3701a-20261117T185401541257', 'windows-neon-3a3701a-mmd-20261117T200622956559', 1),
        ('19500', '21536', 2), ('3592', '2976', 1),
        ('2026-11-17T18:59:01.8851457Z', '2026-11-17T20:07:58.6062857Z', 1),
        ('2026-11-17T18:59:02.3970713Z', '2026-11-17T20:07:59.1058242Z', 1)],
    'test_bind_context.py': [
        ('2026-11-17T18:59:02.3970712Z', '2026-11-17T20:07:59.1058241Z', 2),
        ('2026-11-17T18:59:01.8851447Z', '2026-11-17T20:07:58.6062847Z', 1)],
    'test_api_detail.py': [
        ('2026-11-17T18:59:02.3970710Z', '2026-11-17T20:07:59.1058240Z', 2)],
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def write(name, raw):
    with (HERE / name).open('xb') as stream: stream.write(raw)


def transform(raw, changes):
    result = raw
    for before, after, count in changes:
        before, after = before.encode(), after.encode()
        assert result.count(before) == count and after not in result
        result = result.replace(before, after)
    inverse = result
    for before, after, count in reversed(changes):
        before, after = before.encode(), after.encode()
        assert inverse.count(after) == count
        inverse = inverse.replace(after, before)
    assert inverse == raw
    ast.parse(result)
    return result


def main():
    assert not (HERE / 'INDEX.json').exists() and not (HERE / 'CONTEXT.json').exists()
    index_raw = (OLD / 'INDEX.json').read_bytes(); assert sha(index_raw) == PARENT_INDEX
    rows = {r['path']: r for r in json.loads(index_raw)['files']}
    names = ('close_terminal.py', 'legacy_result_gates.py', 'RESULT_REGISTRY.json',
             'test_terminal.py', 'bind_context.py', 'test_bind_context.py', 'test_api_detail.py',
             'bind_immutable_only.py')
    original = {}
    for name in names:
        raw = (OLD / name).read_bytes(); row = rows[name]
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        original[name] = raw
    for name in ('close_terminal.py', 'legacy_result_gates.py', 'RESULT_REGISTRY.json', 'test_terminal.py'):
        write(name, original[name])
    assert sha(original['close_terminal.py']) == 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'
    assert sha(original['legacy_result_gates.py']) == '0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
    for name, changes in CHANGES.items(): write(name, transform(original[name], changes))
    binder = (HERE / 'bind_context.py').read_bytes()
    wrapper_changes = [
        ('f795528e29b522473bc5542a5dc686ddef39ab666d26e7101977228f8d7cf865', sha(binder), 1),
        ('2026-11-17T18:59:02.3970710Z', '2026-11-17T20:07:59.1058240Z', 1)]
    write('bind_immutable_only.py', transform(original['bind_immutable_only.py'], wrapper_changes))
    left, right = ast.parse(original['bind_context.py']), ast.parse(binder)
    functions = [n.name for n in left.body if isinstance(n, ast.FunctionDef)]
    for name in functions:
        a = next(n for n in left.body if isinstance(n, ast.FunctionDef) and n.name == name)
        b = next(n for n in right.body if isinstance(n, ast.FunctionDef) and n.name == name)
        assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    proof = {
        'format': 'has_3a_mmd_strict_context_only_source_derivation_1',
        'parent_path': OLD.relative_to(HERE.parents[1]).as_posix(), 'parent_INDEX_sha256': PARENT_INDEX,
        'source_commit': '3a3701ab6edfa81dc883759403c170b8555aab07',
        'entire_observer_legacy_registry_and_terminal17_tests_byte_exact': True,
        'all_binder_function_ASTs_exact': functions,
        'binder_context_literal_changes': CHANGES['bind_context.py'],
        'synthetic_binding_timestamp_changes': CHANGES['test_bind_context.py'],
        'actual_API_timestamp_test_changes': CHANGES['test_api_detail.py'],
        'four_input_wrapper_only_pin_and_actual_CIM_literal_changes': wrapper_changes,
        'all_source_transforms_complete_raw_byte_inverse': True,
        'expected_functional_sources': 1029, 'expected_groups': 158, 'expected_core': 36,
        'expected_movies': 21, 'expected_Neon_checks': 12504, 'CPU_methods_expected': 29,
        'actual_result_counts_or_PASS_observed': False,
        'physical_job_count': 'DERIVE_ACTUAL_NO_ASSUMPTION',
        'expected_GetProcess_birth': '2026-11-17T20:07:59.1058242Z',
        'actual_CIM_metadata': '2026-11-17T20:07:59.1058240Z',
        'synthetic_negative_CIM_timestamp': '2026-11-17T20:07:59.1058241Z',
        'birth_identity_API': 'Get-Process.StartTime',
        'unqualified_closure_code_used': False,
        'current_state_log_result_source_after_current_functional_or_native_read': False,
        'process_CIM_Git_or_engine_invoked': False}
    write('SOURCE_DERIVATION.json', (json.dumps(proof, indent=2) + '\n').encode())
    print(json.dumps({'binder_sha256': sha(binder),
                      'registry_sha256': sha(original['RESULT_REGISTRY.json']),
                      'observer_byte_exact': True, 'source_context_only': True}))


if __name__ == '__main__': main()
