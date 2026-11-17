"""Seal source/context evidence without accessing any current run document."""
from pathlib import Path
import ast
import hashlib
import json

import prepare_successor as P

HERE = Path(__file__).resolve().parent
NAMES = ('audit_source.py', 'bind_context.py', 'bind_immutable_only.py', 'BINDING_RECEIPT.json',
         'close_terminal.py', 'CONTEXT.json', 'CPU_REPORT.json', 'CPU_TESTS.log',
         'legacy_result_gates.py', 'prepare_successor.py', 'README.md', 'RESULT_REGISTRY.json',
         'seal_source.py', 'SOURCE_DERIVATION.json', 'test_api_detail.py',
         'test_bind_context.py', 'test_terminal.py')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parent_raw = (P.OLD / 'INDEX.json').read_bytes(); assert sha(parent_raw) == P.PARENT_INDEX
    parent = {r['path']: r for r in json.loads(parent_raw)['files']}
    for name in ('close_terminal.py', 'legacy_result_gates.py', 'RESULT_REGISTRY.json', 'test_terminal.py'):
        assert sha((HERE / name).read_bytes()) == parent[name]['sha256']
    for name, rules in P.CHANGES.items():
        raw = (HERE / name).read_bytes()
        for before, after, count in reversed(rules):
            assert raw.count(after.encode()) == count
            raw = raw.replace(after.encode(), before.encode())
        assert sha(raw) == parent[name]['sha256']
    context_raw = (HERE / 'CONTEXT.json').read_bytes()
    context = json.loads(context_raw); receipt = json.loads((HERE / 'BINDING_RECEIPT.json').read_bytes())
    assert sha(context_raw) == '5424628e28385ce331b55be404384039a3d54262033cbbc96a12445c8dfeb8ba'
    assert receipt['context_sha256'] == sha(context_raw)
    assert context['run_name'] == 'windows-neon-3a3701a-mmd-20261117T200622956559'
    assert (context['result_groups'], context['core_groups'], context['movie_groups']) == (158, 36, 21)
    assert context['terminal_state_or_full_report_read_by_preparation'] is False
    cpu = json.loads((HERE / 'CPU_REPORT.json').read_bytes())
    assert (cpu['tests'], cpu['failures'], cpu['errors'], cpu['skips']) == (29, 0, 0, 0)
    assert {p.name for p in HERE.iterdir()} == set(NAMES)
    files = []
    for name in sorted(NAMES):
        raw = (HERE / name).read_bytes()
        if name.endswith('.py'): ast.parse(raw)
        files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
    value = {'format': 'has_source_experiment_index_1', 'packet': HERE.name,
             'status': 'SEALED_STRICT_CONTEXT_ONLY_SOURCE_CPU_PASS_ACTUAL_TERMINAL_UNREAD',
             'files': files, 'payload_files': len(files), 'payload_bytes': sum(r['bytes'] for r in files),
             'parent_INDEX_sha256': P.PARENT_INDEX, 'context_sha256': sha(context_raw),
             'source_context_only': True, 'CPU_methods': 29, 'failures': 0, 'errors': 0,
             'observer_legacy_registry_and_terminal17_bytes_exact': True,
             'expected_counts_not_full_PASS': True, 'actual_terminal_observed': False,
             'unqualified_closure_code_used': False}
    with (HERE / 'INDEX.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')
    print(json.dumps({'INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes()),
                      'context_sha256': sha(context_raw), 'payload_files': len(files),
                      'payload_bytes': value['payload_bytes'], 'CPU_methods': 29}))


if __name__ == '__main__': main()
