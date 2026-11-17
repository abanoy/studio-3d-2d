"""Source-only context successor; reads no active state/report/log/source-after."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'neon_fe9_terminal_20261117'
PARENT_INDEX = 'a35f9ac209f15e0eafcc20b50a53047e855ac77de899ad6c545a4e9c20c58d26'
OLD_COMMIT = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
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
    names = ('bind_context.py', 'close_terminal.py', 'legacy_result_gates.py', 'RESULT_REGISTRY.json', 'test_terminal.py', 'test_bind_context.py', 'test_api_detail.py')
    old = {}
    for name in names:
        raw = (OLD / name).read_bytes(); assert sha(raw) == rows[name]['sha256'] and len(raw) == rows[name]['bytes']; old[name] = raw
    for name in ('close_terminal.py', 'legacy_result_gates.py', 'test_terminal.py'): write(name, old[name])
    binder_changes = [(OLD_COMMIT, COMMIT, 1), ('windows-neon-fe9aace-20261117T040348', 'windows-neon-00bf0f9-20261117T044200', 1),
        ('19668', '21216', 2), ('28396', '16808', 1),
        ('2026-11-17T04:04:17.2421226Z', '2026-11-17T04:42:33.4387679Z', 1),
        ('2026-11-17T04:04:18.1277602Z', '2026-11-17T04:42:33.9446445Z', 1),
        ('Exact fe91029', 'Exact 00bf1029', 1), ('has_neon_fe9_terminal_source_context_1', 'has_neon_00bf_terminal_source_context_1', 1)]
    binder = transform(old['bind_context.py'], binder_changes); write('bind_context.py', binder)
    bind_changes = [('2026-11-17T04:04:18.1277601Z', '2026-11-17T04:42:33.9446444Z', 2),
                    ('2026-11-17T04:04:17.2421210Z', '2026-11-17T04:42:33.4387669Z', 1)]
    api_changes = [('2026-11-17T04:04:18.1277600Z', '2026-11-17T04:42:33.9446440Z', 2)]
    write('test_bind_context.py', transform(old['test_bind_context.py'], bind_changes))
    write('test_api_detail.py', transform(old['test_api_detail.py'], api_changes))
    assert old['RESULT_REGISTRY.json'].count(OLD_COMMIT.encode()) == 1
    registry = old['RESULT_REGISTRY.json'].replace(OLD_COMMIT.encode(), COMMIT.encode(), 1)
    assert registry.replace(COMMIT.encode(), OLD_COMMIT.encode(), 1) == old['RESULT_REGISTRY.json']
    write('RESULT_REGISTRY.json', registry)
    proof = {'format': 'has_00bf_context_only_terminal_source_derivation_1', 'source_commit': COMMIT, 'parent_index_sha256': PARENT_INDEX,
        'helper_legacy_terminal17tests_entire_files_exact': True, 'binder_literals_only_raw_byte_inverse': True,
        'strict_sevenfield_API_adapter_entire_function_and_main_call_exact': True, 'binding_and_API_tests_timestamp_literals_only_raw_inverse': True,
        'registry_sole_source_commit_raw_byte_inverse_no_EOL_change': True, 'expected_sources': 1029, 'expected_groups': 158, 'expected_core': 36, 'expected_movies': 21,
        'Neon_checks': 12504, 'lifecycle_checks': 29, 'CPU_methods_expected': 29, 'physical_job_count': 'DERIVE_ACTUAL_NO_ASSUMPTION',
        'binder_changes': binder_changes, 'bind_test_changes': bind_changes, 'api_test_changes': api_changes,
        'expected_GetProcess_birth': '2026-11-17T04:42:33.9446445Z', 'expected_actual_CIM_metadata': '2026-11-17T04:42:33.9446440Z',
        'synthetic_negative_CIM_timestamp': '2026-11-17T04:42:33.9446444Z', 'helper_output_format_labels_inherited_ffcf_unchanged': True,
        'active_state_report_log_source_after_or_process_query_read': False, 'engines_CIM_Git_executed': False}
    write('SOURCE_DERIVATION.json', (json.dumps(proof, indent=2) + '\n').encode())
    print(json.dumps({'binder_sha256': sha(binder), 'registry_sha256': sha(registry), 'source_prepared': True, 'terminal_unread': True}, indent=2))


if __name__ == '__main__': main()
