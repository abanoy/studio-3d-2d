"""Run synthetic tests in-process; write only a new local evidence record."""
from pathlib import Path
import datetime
import hashlib
import io
import json
import unittest

import derive_api_fix as D
import test_resources
import test_api_fix

HERE = Path(__file__).resolve().parent
SOURCES = ('derive_api_fix.py', 'test_api_fix.py', 'validate_cpu.py', *D.COPY_NAMES, *D.RULES)


def identities():
    return {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            for name in SOURCES for raw in [(HERE / name).read_bytes()]}


def main():
    before = identities(); parent_before = D.parent_sources()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (test_resources.ResourceTests, test_api_fix.APIFixTests))
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    assert identities() == before and D.parent_sources() == parent_before, 'Source changed during synthetic CPU checks'
    report = {'format': 'has_B_resource_Blender51_API_cpu_validation_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'tests': result.testsRun, 'original_test_methods': 31, 'API_boundary_test_methods': 7,
              'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
              'status': 'SOURCE_CPU_PASS' if result.wasSuccessful() else 'SOURCE_CPU_FAIL',
              'stdout': stream.getvalue(), 'source_identities': before, 'source_unchanged': True,
              'original_sealed_packet_changed': False, 'native_assets_or_private_outputs_read': False,
              'bpy_imported_or_native_process_launched': False, 'process_CIM_Git_or_network_invoked': False,
              'actual_resource_discovery_or_native_fidelity_qualified': False}
    with (HERE / 'CPU_VALIDATION.json').open('x', encoding='utf-8', newline='\n') as output:
        json.dump(report, output, indent=2); output.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'tests', 'failures', 'errors', 'skips')}))
    if not result.wasSuccessful(): raise SystemExit(1)


if __name__ == '__main__': main()
