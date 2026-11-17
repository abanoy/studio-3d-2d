"""Original synthetic CPU suite; never execute the actual terminal observer."""
from pathlib import Path
import datetime
import hashlib
import io
import json
import unittest

import test_terminal
import test_bind_context
import test_api_detail

HERE = Path(__file__).resolve().parent
SOURCES = ('prepare_successor.py', 'audit_source.py', 'close_terminal.py', 'legacy_result_gates.py',
           'bind_context.py', 'bind_immutable_only.py', 'test_terminal.py',
           'test_bind_context.py', 'test_api_detail.py', 'RESULT_REGISTRY.json', 'CONTEXT.json')


def identities():
    return {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            for name in SOURCES for raw in [(HERE / name).read_bytes()]}


def main():
    before = identities(); methods = []
    suite = unittest.TestSuite()
    for module in (test_terminal, test_bind_context, test_api_detail):
        loaded = unittest.defaultTestLoader.loadTestsFromModule(module)
        for group in loaded:
            methods.extend(test.id() for test in group)
        suite.addTests(loaded)
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    assert identities() == before, 'Source/context changed during synthetic checks'
    assert result.testsRun == 29
    with (HERE / 'CPU_TESTS.log').open('x', encoding='utf-8', newline='\n') as output:
        output.write(stream.getvalue())
    report = {'format': 'has_3a_mmd_strict_terminal_source_cpu_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skips': len(result.skipped), 'status': 'SOURCE_CPU_PASS' if result.wasSuccessful() else 'SOURCE_CPU_FAIL',
              'methods': methods, 'source_and_context_identities': before, 'source_unchanged': True,
              'original_terminal_methods': 17, 'binding_methods': 8, 'strict_actual_API_methods': 4,
              'counts_are_expectations_not_actual_results': True, 'actual_terminal_or_PASS_observed': False,
              'unqualified_closure_code_used': False,
              'current_state_log_report_source_after_functional_or_native_read': False,
              'actual_process_CIM_Git_or_engine_invoked': False}
    with (HERE / 'CPU_REPORT.json').open('x', encoding='utf-8', newline='\n') as output:
        json.dump(report, output, indent=2); output.write('\n')
    print(json.dumps({k: report[k] for k in ('status', 'tests', 'failures', 'errors', 'skips')}))
    if not result.wasSuccessful(): raise SystemExit(1)


if __name__ == '__main__': main()
