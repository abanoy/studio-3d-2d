"""Source-only same-commit context successor; never reads active terminal data."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'neon_00bf_terminal_20261117'
PARENT_INDEX = '704a31e41fda629c78befb12fc9f28a107c93cf25c7516c8fa66850fff94f49e'
COMMIT = '00bf0f916a549f5e858cb39dd91a149071fd5181'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def write(name, raw):
    with (HERE / name).open('xb') as stream: stream.write(raw)


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
    index_raw = (OLD / 'INDEX.json').read_bytes(); assert sha(index_raw) == PARENT_INDEX
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
    assert sha(old['RESULT_REGISTRY.json']) == 'b03dc3bf06baf6044a034d17b0c9a430f2cfb364bac762f399fcc53c6a9013eb'
    for name in ('close_terminal.py', 'legacy_result_gates.py', 'RESULT_REGISTRY.json', 'test_terminal.py'):
        write(name, old[name])
    binder_changes = [
        ('windows-neon-00bf0f9-20261117T044200', 'windows-neon-00bf0f9-replay2-20261117T155709412051', 1),
        ('21216', '19808', 2), ('16808', '8888', 1),
        ('2026-11-17T04:42:33.4387679Z', '2026-11-17T15:58:55.2656645Z', 1),
        ('2026-11-17T04:42:33.9446445Z', '2026-11-17T15:58:55.9596269Z', 1)]
    binder = transform(old['bind_context.py'], binder_changes)
    old_tree, new_tree = ast.parse(old['bind_context.py']), ast.parse(binder)
    adapter = lambda tree: next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'adapt_actual_api_detail')
    assert ast.dump(adapter(old_tree), include_attributes=False) == ast.dump(adapter(new_tree), include_attributes=False)
    call = b"api_identity=adapt_actual_api_detail(values['root-birth-api-detail.json'])"
    assert old['bind_context.py'].count(call) == binder.count(call) == 1
    write('bind_context.py', binder)
    bind_changes = [('2026-11-17T04:42:33.9446444Z', '2026-11-17T15:58:55.9596268Z', 2),
                    ('2026-11-17T04:42:33.4387669Z', '2026-11-17T15:58:55.2656635Z', 1)]
    api_changes = [('2026-11-17T04:42:33.9446440Z', '2026-11-17T15:58:55.9596260Z', 2)]
    write('test_bind_context.py', transform(old['test_bind_context.py'], bind_changes))
    write('test_api_detail.py', transform(old['test_api_detail.py'], api_changes))
    proof = {'format': 'has_00bf_replay2_context_only_terminal_source_derivation_1', 'source_commit': COMMIT,
        'parent_index_sha256': PARENT_INDEX, 'helper_legacy_registry_terminal17tests_entire_files_exact': True,
        'binder_run_PID_birth_literals_only_raw_byte_inverse': True,
        'strict_sevenfield_API_adapter_entire_function_and_main_call_exact': True,
        'binding_and_API_tests_timestamp_literals_only_raw_inverse': True,
        'registry_same_00bf_commit_entire_file_byte_exact': True,
        'expected_sources': 1029, 'expected_groups': 158, 'expected_core': 36, 'expected_movies': 21,
        'Neon_checks': 12504, 'lifecycle_checks': 29, 'CPU_methods_expected': 29,
        'physical_job_count': 'DERIVE_ACTUAL_NO_ASSUMPTION', 'binder_changes': binder_changes,
        'bind_test_changes': bind_changes, 'api_test_changes': api_changes,
        'expected_GetProcess_birth': '2026-11-17T15:58:55.9596269Z',
        'expected_actual_CIM_metadata': '2026-11-17T15:58:55.9596260Z',
        'synthetic_negative_CIM_timestamp': '2026-11-17T15:58:55.9596268Z',
        'helper_output_format_labels_inherited_ffcf_unchanged': True,
        'active_state_report_log_source_after_or_process_query_read': False,
        'engines_CIM_Git_executed': False}
    write('SOURCE_DERIVATION.json', (json.dumps(proof, indent=2) + '\n').encode())
    print(json.dumps({'binder_sha256': sha(binder), 'registry_sha256': sha(old['RESULT_REGISTRY.json']),
                      'source_prepared': True, 'terminal_unread': True}))


if __name__ == '__main__': main()
