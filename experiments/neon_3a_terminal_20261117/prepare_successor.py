"""3a context-only source successor; no active terminal or process access."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'neon_696_terminal_20261117'
PARENT_INDEX = 'eecfb76051db35ffe062a174802de1a13613f7f5e5a2e15abee8b6e45d723079'
OLD_COMMIT = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
COMMIT = '3a3701ab6edfa81dc883759403c170b8555aab07'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(name, raw):
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


def transform(raw, changes):
    changed = raw
    for before, after, count in changes:
        before, after = before.encode(), after.encode()
        assert changed.count(before) == count and after not in changed
        changed = changed.replace(before, after)
    inverse = changed
    for before, after, count in reversed(changes):
        before, after = before.encode(), after.encode()
        assert inverse.count(after) == count
        inverse = inverse.replace(after, before)
    assert inverse == raw
    ast.parse(changed)
    return changed


def main():
    assert not (HERE / 'INDEX.json').exists() and not (HERE / 'CONTEXT.json').exists()
    index_raw = (OLD / 'INDEX.json').read_bytes()
    assert sha(index_raw) == PARENT_INDEX
    rows = {row['path']: row for row in json.loads(index_raw)['files']}
    names = ('bind_context.py', 'close_terminal.py', 'legacy_result_gates.py', 'RESULT_REGISTRY.json',
             'test_terminal.py', 'test_bind_context.py', 'test_api_detail.py')
    old = {}
    for name in names:
        raw = (OLD / name).read_bytes()
        assert sha(raw) == rows[name]['sha256'] and len(raw) == rows[name]['bytes']
        old[name] = raw
    assert sha(old['close_terminal.py']) == 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'
    assert sha(old['legacy_result_gates.py']) == '0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
    for name in ('close_terminal.py', 'legacy_result_gates.py', 'test_terminal.py'):
        write(name, old[name])
    binder_changes = [
        (OLD_COMMIT, COMMIT, 1),
        ('windows-neon-696ca7f-20261117T170720480423', 'windows-neon-3a3701a-20261117T185401541257', 1),
        ('12740', '19500', 2), ('5384', '3592', 1),
        ('2026-11-17T17:07:54.3896834Z', '2026-11-17T18:59:01.8851457Z', 1),
        ('2026-11-17T17:07:54.8423868Z', '2026-11-17T18:59:02.3970713Z', 1),
        ('Exact 6961029', 'Exact 3a1029', 1),
        ('has_neon_696_terminal_source_context_1', 'has_neon_3a_terminal_source_context_1', 1),
    ]
    binder = transform(old['bind_context.py'], binder_changes)
    a, b = ast.parse(old['bind_context.py']), ast.parse(binder)
    for name in ('adapt_actual_api_detail', 'read_input', 'validate', 'main'):
        left = next(node for node in a.body if isinstance(node, ast.FunctionDef) and node.name == name)
        right = next(node for node in b.body if isinstance(node, ast.FunctionDef) and node.name == name)
        if name in ('adapt_actual_api_detail', 'read_input'):
            assert ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False)
    call = b"api_identity=adapt_actual_api_detail(values['root-birth-api-detail.json'])"
    assert old['bind_context.py'].count(call) == binder.count(call) == 1
    write('bind_context.py', binder)
    bind_changes = [('2026-11-17T17:07:54.8423867Z', '2026-11-17T18:59:02.3970712Z', 2),
                    ('2026-11-17T17:07:54.3896824Z', '2026-11-17T18:59:01.8851447Z', 1)]
    api_changes = [('2026-11-17T17:07:54.8423860Z', '2026-11-17T18:59:02.3970710Z', 2)]
    write('test_bind_context.py', transform(old['test_bind_context.py'], bind_changes))
    write('test_api_detail.py', transform(old['test_api_detail.py'], api_changes))
    assert old['RESULT_REGISTRY.json'].count(OLD_COMMIT.encode()) == 1
    registry = old['RESULT_REGISTRY.json'].replace(OLD_COMMIT.encode(), COMMIT.encode(), 1)
    assert registry.replace(COMMIT.encode(), OLD_COMMIT.encode(), 1) == old['RESULT_REGISTRY.json']
    write('RESULT_REGISTRY.json', registry)
    proof = {'format': 'has_3a_context_only_terminal_source_derivation_1', 'source_commit': COMMIT,
        'parent_index_sha256': PARENT_INDEX,
        'helper_legacy_terminal17tests_entire_files_exact': True,
        'binder_context_literals_only_raw_byte_inverse': True,
        'strict_sevenfield_API_adapter_entire_function_and_main_call_exact': True,
        'binding_and_API_tests_timestamp_literals_only_raw_inverse': True,
        'registry_sole_commit_raw_byte_inverse_no_EOL_change': True,
        'expected_sources': 1029, 'expected_groups': 158, 'expected_core': 36, 'expected_movies': 21,
        'Neon_checks': 12504, 'lifecycle_checks': 29, 'CPU_methods_expected': 29,
        'physical_job_count': 'DERIVE_ACTUAL_NO_ASSUMPTION', 'binder_changes': binder_changes,
        'bind_test_changes': bind_changes, 'api_test_changes': api_changes,
        'expected_GetProcess_birth': '2026-11-17T18:59:02.3970713Z',
        'expected_actual_CIM_metadata': '2026-11-17T18:59:02.3970710Z',
        'synthetic_negative_CIM_timestamp': '2026-11-17T18:59:02.3970712Z',
        'helper_output_format_labels_inherited_ffcf_unchanged': True,
        'binding_preparation_uses_four_documents_and_pure_functions_not_binder_main': True,
        'current_verifier_runner_or_Pwsh_not_rehashed_during_preparation': True,
        'active_state_report_log_source_after_or_process_query_read': False,
        'engines_CIM_Git_executed': False}
    write('SOURCE_DERIVATION.json', (json.dumps(proof, indent=2) + '\n').encode())
    print(json.dumps({'binder_sha256': sha(binder), 'registry_sha256': sha(registry),
                      'source_prepared': True, 'terminal_unread': True}))


if __name__ == '__main__':
    main()
