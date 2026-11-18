"""Synthetic CPU/source seal only; never read full/native outputs or invoke Git."""
from pathlib import Path
import datetime, hashlib, io, json, unittest
import admission_core as A
import derive_source as D
import test_admission_core as Original
import test_shell_eol as Extra

HERE = Path(__file__).resolve().parent
NAMES = ('admission_core.py', *D.COPIES, 'derive_source.py', 'test_shell_eol.py',
         'validate_and_seal.py', 'DERIVATION.json', 'README.md', 'CPU_RESULT.json')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parent_before = D.parent_sources()
    sources = {name: (HERE / name).read_bytes() for name in NAMES if name != 'CPU_RESULT.json'}
    old_suite = unittest.defaultTestLoader.loadTestsFromModule(Original)
    new_suite = unittest.defaultTestLoader.loadTestsFromModule(Extra)
    assert old_suite.countTestCases() == 27 and new_suite.countTestCases() == 7
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite((old_suite, new_suite)))
    assert result.testsRun == 34 and D.parent_sources() == parent_before
    assert all((HERE / name).read_bytes() == raw for name, raw in sources.items())
    report = {'format': 'has_three_shell_EOL_core_source_CPU_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'tests': result.testsRun, 'original_methods_byte_exact': 27, 'new_methods': 7,
              'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
              'status': 'SOURCE_CPU_PASS' if result.wasSuccessful() else 'SOURCE_CPU_FAIL',
              'stdout': stream.getvalue(), 'source_unchanged': True,
              'functional_working_or_Git_bytes_changed': False,
              'actual_full_native_private_process_Git_or_network_access': False,
              'activation_or_Root_approval_supplied': False}
    with (HERE / 'CPU_RESULT.json').open('x', encoding='utf-8', newline='\n') as out:
        json.dump(report, out, indent=2); out.write('\n')
    assert result.wasSuccessful(), stream.getvalue()
    files = []
    for name in sorted(NAMES):
        raw = (HERE / name).read_bytes()
        if name.endswith('.py'): compile(raw, name, 'exec')
        files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
    assert {p.name for p in HERE.iterdir()} == set(NAMES)
    index = {'format': 'has_source_experiment_index_1', 'packet': HERE.name,
             'status': 'SEALED_EXACT_THREE_PATH_TEXT_ADMISSION_SOURCE_CPU_ONLY_INACTIVE',
             'files': files, 'payload_files': len(files), 'payload_bytes': sum(r['bytes'] for r in files),
             'parent_INDEX_sha256': D.PARENT_INDEX, 'admission_core_sha256': sha(sources['admission_core.py']),
             'exact_added_TEXT_PATHS': D.SHELLS, 'tests': 34, 'failures': 0, 'errors': 0,
             'all_core_function_ASTs_and_original27_methods_exact': True,
             'functional_source_or_Git_mutated': False, 'actual_full_or_native_qualification_claimed': False}
    with (HERE / 'INDEX.json').open('x', encoding='utf-8', newline='\n') as out:
        json.dump(index, out, indent=2); out.write('\n')
    print(json.dumps({'INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes()),
                      'core_sha256': index['admission_core_sha256'], 'tests': 34,
                      'payload_files': len(files), 'payload_bytes': index['payload_bytes']}))


if __name__ == '__main__': main()
