"""Import and test proposed code in an output shadow; no Godot/model workers.

External-process boundaries use synthetic results explicitly labelled CPU-only.
These tests certify wrapper gates, never any of the830 real GPU assertions.
"""
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import copy
import importlib.util
import io
import json
import os
import shutil
import stat
import sys
import types
import unittest
import uuid
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
MAIN = OUT.parents[1]
PROPOSED = OUT / 'proposed/tests'
VALIDATION = OUT / 'validation'
SHADOW = VALIDATION / ('cpu-shadow-' + uuid.uuid4().hex)


class ProposedDriverCPU(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SHADOW.mkdir(parents=True, exist_ok=False)
        table = json.loads((PROPOSED / 'wind_review_port_files.json').read_bytes())
        packet = MAIN / 'experiments/local_wind_review/production_port_candidate_20261112/overlay'
        for row in table['files']:
            source = PROPOSED / 'wind_review_gpu_common.gd' if row['path'] == 'tests/wind_review_gpu_common.gd' else packet / row['path']
            destination = SHADOW / row['path']; destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, destination)
        for name in ('run.py', 'project.godot', 'main.tscn', 'launch.pyw', 'dependencies.json', 'tools/private_desktop.py', 'src/world_selection.gd'):
            destination = SHADOW / name; destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(MAIN / name, destination)
        for name in ('verify_wind_review.py', 'wind_review_port_files.json'):
            shutil.copyfile(PROPOSED / name, SHADOW / 'tests' / name)
        plans = (MAIN / 'tests/native_fixture_plans.py').read_text(encoding='utf-8') + '\n' + (PROPOSED / 'native_fixture_plans.wind_review.append.py').read_text(encoding='utf-8')
        (SHADOW / 'tests/native_fixture_plans.py').write_text(plans, encoding='utf-8')
        shutil.copyfile(MAIN / 'tests/native_fixture_root.py', SHADOW / 'tests/native_fixture_root.py')
        for name in ('native_fixture_plans', 'native_fixture_root'):
            sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location('proposed_wind_driver_cpu_shadow', SHADOW / 'tests/verify_wind_review.py')
        cls.driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.driver)
        cls.plans = sys.modules['native_fixture_plans']
        assert cls.driver.ROOT == SHADOW
        cls.observed_manifest = VALIDATION / 'observed-manifest.json'
        assert cls.observed_manifest.is_file(), 'Run validate_proposal.py first'
        cls.baseline = {p: p.read_bytes() for p in SHADOW.rglob('*') if p.is_file()}

    def setUp(self):
        self.driver.ALLOW_EOL = False
        self.state = SHADOW / 'output' / 'wind-review' / ('cpu-test-' + uuid.uuid4().hex)
        self.state.mkdir(parents=True)

    def tearDown(self):
        for path, data in self.baseline.items():
            if path.read_bytes() != data:
                path.write_bytes(data)
        self.driver.ALLOW_EOL = False

    def call_main(self, arguments, **boundaries):
        captured = {}
        def capture(path, value):
            captured[Path(path).name] = copy.deepcopy(value)
        with patch.object(sys, 'argv', ['verify_wind_review.py', *arguments]), patch.object(self.driver, 'write_json', side_effect=capture), patch.object(self.driver, 'revision', return_value='cpu-shadow-revision'), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            patches = [patch.object(self.driver, name, value) for name, value in boundaries.items()]
            try:
                for item in patches: item.start()
                code = self.driver.main()
            finally:
                for item in reversed(patches): item.stop()
        return code, captured

    def test_actual_runner_binds_shadow_without_starting_engine(self):
        runner = self.driver.runner()
        self.assertEqual(runner.ROOT, SHADOW)
        self.assertEqual(Path(runner.__file__), SHADOW / 'run.py')

    def test_actual_runner_wrong_root_refused(self):
        (SHADOW / 'run.py').write_text('from pathlib import Path\nROOT=Path("C:/outside-root")\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'Runner did not bind'):
            self.driver.runner()

    def test_mode_must_be_explicit(self):
        with self.assertRaises(SystemExit) as result:
            self.call_main([])
        self.assertEqual(result.exception.code, 2)

    def test_graphical_without_lease_refused_before_runner(self):
        runner = unittest.mock.Mock(side_effect=AssertionError('Runner must not be reached'))
        with self.assertRaisesRegex(RuntimeError, 'released lease'):
            self.call_main(['--mode', 'graphical'], runner=runner)
        runner.assert_not_called()

    def test_existing_output_directory_refused(self):
        target = SHADOW / 'output/wind-review/headless-42'; target.mkdir(parents=True, exist_ok=False)
        with patch.object(self.driver.time, 'time_ns', return_value=42):
            with self.assertRaises(FileExistsError):
                self.call_main(['--mode', 'headless'])

    def test_output_boundary_and_traversal_refused(self):
        guard = self.driver.guard
        self.assertEqual(guard(self.state / 'new.json', self.state), self.state / 'new.json')
        for bad in (self.state, self.state / '..' / 'escape.json', MAIN / 'output/owner-review/file.json'):
            with self.subTest(path=str(bad)), self.assertRaises(RuntimeError):
                guard(bad, self.state)

    def test_output_reparse_attribute_refused(self):
        real = Path.lstat
        def metadata(path, *args, **kwargs):
            value = real(path, *args, **kwargs)
            if path == self.state:
                return types.SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
            return value
        with patch.object(Path, 'lstat', metadata), self.assertRaisesRegex(RuntimeError, 'reparse'):
            self.driver.guard(self.state / 'new.json', self.state)

    def test_reviewed_port_exact_bytes_and_mutation(self):
        self.assertEqual(len(self.driver.runtime_hashes()), 16)
        target = SHADOW / 'src/wind_review.gd'; target.write_bytes(target.read_bytes() + b'\n# CPU negative control\n')
        with self.assertRaisesRegex(RuntimeError, 'Unreviewed main port bytes'):
            self.driver.runtime_hashes()

    def test_eol_reconstruction_requires_explicit_option(self):
        table = json.loads((SHADOW / 'tests/wind_review_port_files.json').read_bytes())
        row = next(row for row in table['files'] if row['sha256'] != row['lf_sha256'])
        target = SHADOW / row['path']; target.write_bytes(target.read_bytes().replace(b'\r\n', b'\n'))
        with self.assertRaises(RuntimeError): self.driver.runtime_hashes()
        self.driver.ALLOW_EOL = True
        bindings = self.driver.runtime_hashes()
        self.assertIn('explicit --allow-checkout-eol', bindings[row['path']]['reconstruction'])
        target.write_bytes(target.read_bytes() + b'# functional mutation\n')
        with self.assertRaises(RuntimeError): self.driver.runtime_hashes()

    def test_prepared_metadata_positive_and_manifest_negative_controls(self):
        with patch.dict(os.environ, {'HYBRID_NATIVE_FIXTURES': str(MAIN / 'output')}):
            plan = self.plans.wind_review_native_plans(self.observed_manifest)
            self.assertEqual(set(plan['inputs']), {'vrm0', 'vrm1', 'backhair'})
            self.assertTrue(self.driver.verify_originals(plan))
            mutated = copy.deepcopy(plan); mutated['inputs']['vrm1']['source_identity']['sha256'] = '0' * 64
            self.assertFalse(self.driver.verify_originals(mutated))
            original = json.loads(self.observed_manifest.read_bytes())
            variations = {}
            bad = copy.deepcopy(original); del bad['inputs']['backhair']; variations['missing-role'] = bad
            bad = copy.deepcopy(original); bad['inputs']['vrm0']['source'] = '../escape.glb'; variations['traversal'] = bad
            bad = copy.deepcopy(original); bad['inputs']['vrm0']['source'] = 'C:/outside.glb'; variations['absolute'] = bad
            bad = copy.deepcopy(original); bad['inputs']['vrm0']['parameters'] = original['inputs']['vrm1']['parameters']; variations['wrong-report'] = bad
            bad = copy.deepcopy(original); bad['inputs']['vrm0']['source'] = original['inputs']['vrm0']['parameters']; bad['inputs']['vrm0']['sha256'] = plan['inputs']['vrm0']['parameters_identity']['sha256']; variations['manifest-cannot-override-pin'] = bad
            for label, document in variations.items():
                # Resolver manifest must remain inside the explicit fixture root.
                path = VALIDATION / ('imported-resolver-' + label + '.json'); path.write_text(json.dumps(document), encoding='utf-8')
                with self.subTest(case=label), self.assertRaises((ValueError, FileNotFoundError)):
                    self.plans.wind_review_native_plans(path)

    def test_input_size_mtime_and_manifest_freshness(self):
        source = self.state / 'source'; parameters = self.state / 'parameters'; manifest = self.state / 'manifest'
        for path in (source, parameters, manifest): path.write_text('before', encoding='utf-8')
        plan = {'manifest': str(manifest), 'manifest_identity': self.driver.identity(manifest), 'inputs': {'x': {'source': str(source), 'source_identity': self.driver.identity(source), 'parameters': str(parameters), 'parameters_identity': self.driver.identity(parameters)}}}
        self.assertTrue(self.driver.verify_originals(plan))
        parameters.write_text('after and different size', encoding='utf-8'); self.assertFalse(self.driver.verify_originals(plan))
        parameters.write_text('before', encoding='utf-8'); plan['inputs']['x']['parameters_identity'] = self.driver.identity(parameters)
        value = source.stat(); os.utime(source, ns=(value.st_atime_ns, value.st_mtime_ns + 1_000_000))
        self.assertFalse(self.driver.verify_originals(plan))
        plan['inputs']['x']['source_identity'] = self.driver.identity(source); manifest.write_text('changed', encoding='utf-8')
        self.assertFalse(self.driver.verify_originals(plan))

    def test_command_root_and_private_launcher_gates(self):
        def runner(arguments): return types.SimpleNamespace(command=lambda *args, **kwargs: list(arguments))
        valid = ['pythonw', str(SHADOW / 'tools/private_desktop.py'), '--receipt', 'old-receipt', '--', 'Godot', '--path', str(SHADOW)]
        args = self.driver.checked_command(runner(valid), 'tests/test.gd', self.state)
        self.assertEqual(args[args.index('--receipt') + 1], str(self.state / 'private-receipt.json'))
        for invalid in ([*valid, '--path', str(SHADOW)], [*valid[:-1], str(MAIN)], ['Godot', '--path', str(SHADOW)]):
            with self.subTest(command=invalid), self.assertRaises(RuntimeError):
                self.driver.checked_command(runner(invalid), 'tests/test.gd', self.state)
        invalid = list(valid); invalid[1] = str(MAIN / 'tools/private_desktop.py')
        with self.assertRaises(RuntimeError): self.driver.checked_command(runner(invalid), 'tests/test.gd', self.state)

    def test_source_and_head_drift_fail_main_gate(self):
        def mutate(folder, runner):
            path = SHADOW / 'src/world_selection.gd'; path.write_bytes(path.read_bytes() + b'\n# shadow-only drift\n')
            return [{'passed': True}]
        code, reports = self.call_main(['--mode', 'headless'], runner=lambda: object(), headless_checks=mutate)
        self.assertEqual(code, 1); self.assertFalse(reports['verification.json']['all_functional_sources_hash_size_mtime_unchanged'])
        # The next scenario needs a stable source snapshot; restoring a shadow
        # file cannot touch the actual root's active frozen verification.
        for path, data in self.baseline.items():
            if path.read_bytes() != data: path.write_bytes(data)
        with patch.object(self.driver, 'revision', side_effect=['old', 'new']), patch.object(sys, 'argv', ['verify_wind_review.py', '--mode', 'headless']), patch.object(self.driver, 'runner', return_value=object()), patch.object(self.driver, 'headless_checks', return_value=[{'passed': True}]), patch.object(self.driver, 'write_json') as capture, redirect_stdout(io.StringIO()):
            self.assertEqual(self.driver.main(), 1)
        report = next(call.args[1] for call in capture.call_args_list if Path(call.args[0]).name == 'verification.json')
        self.assertNotEqual(report['revision_before'], report['revision_after']); self.assertFalse(report['passed'])

    def test_incomplete_matrix_cannot_pass_even_when_returned_rows_pass(self):
        plan = {'manifest': 'unused', 'manifest_identity': {}, 'inputs': {}}
        rows = [{'mode': str(i), 'passed': True, 'checks': 1} for i in range(5)]
        code, reports = self.call_main(['--mode', 'graphical', '--lease-confirmed'], runner=lambda: object(), headless_checks=lambda *args: [], parse_checks=lambda *args: [], wind_review_native_plans=lambda *args: plan, execute_gpu=lambda *args: rows, verify_originals=lambda *args: True)
        self.assertEqual(code, 1); self.assertFalse(reports['verification.json']['passed']); self.assertEqual(len(reports['verification.json']['results']), 5)

    def test_gpu_driver_order_receipts_counts_and_error_negative_controls(self):
        # Only OS/GPU process execution and fixture preparation are replaced.
        # The imported execute_gpu acceptance/order/fail-fast code runs intact.
        valid_command = ['pythonw', str(SHADOW / 'tools/private_desktop.py'), '--receipt', 'placeholder', '--', 'Godot', '--path', str(SHADOW)]
        runner = types.SimpleNamespace(command=lambda *args, **kwargs: list(valid_command))
        staged = {'vrm0': {}, 'vrm1': {}, 'backhair': {}}
        conditions = [
            ('positive-six', None),
            ('short-assertion-count', lambda result, receipt: result.update(checks=result['checks'] - 1)),
            ('assertion-failure', lambda result, receipt: result.update(failures=1)),
            ('wrong-actual-project', lambda result, receipt: result['metrics'].update(project_root=str(MAIN))),
            ('wrong-case', lambda result, receipt: result.update(mode='vrm0')),
            ('stale-startup', lambda result, receipt: result['metrics'].update(fresh_startup_workspace=False)),
            ('receipt-no-desktop', lambda result, receipt: receipt.update(child_desktop_confirmed=False)),
            ('receipt-foreground', lambda result, receipt: receipt.update(foreground_child_observed=True)),
            ('receipt-open-job', lambda result, receipt: receipt.update(job_closed=False)),
            ('receipt-open-desktop', lambda result, receipt: receipt.update(desktop_closed=False)),
            ('receipt-native-crash', lambda result, receipt: receipt.update(exit=3221225477)),
            ('receipt-missing-field', lambda result, receipt: receipt.pop('job_closed')),
            ('process-exit', None), ('engine-error', None), ('missing-result', None), ('missing-receipt', None)
        ]
        real_write = self.driver.write_json
        for label, mutate in conditions:
            target = self.state / label; target.mkdir()
            invoked = []
            def synthetic_invoke(arguments, case, timeout):
                name = case.name; invoked.append(name)
                result = {'mode': name, 'checks': self.driver.COUNTS[name], 'failures': 0,
                          'metrics': {'project_root': str(SHADOW), 'fresh_startup_workspace': True}, '_synthetic_cpu_fixture': True}
                receipt = {'exit': 0, 'child_desktop_confirmed': True, 'foreground_child_observed': False,
                           'job_closed': True, 'desktop_closed': True, '_synthetic_cpu_fixture': True}
                if mutate is not None: mutate(result, receipt)
                if label != 'missing-result': (case / 'result.json').write_text(json.dumps(result), encoding='utf-8')
                if label != 'missing-receipt': (case / 'private-receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
                return (1 if label == 'process-exit' else 0), 'CPU-only synthetic process boundary', ['ERROR:'] if label == 'engine-error' else []
            def labelled_write(path, value):
                if isinstance(value, dict): value = {**value, '_synthetic_cpu_fixture': True}
                elif isinstance(value, list): value = [{**item, '_synthetic_cpu_fixture': True} if isinstance(item, dict) else item for item in value]
                real_write(path, value)
            with self.subTest(case=label), patch.object(self.driver, 'stage_native', return_value=staged), patch.object(self.driver, 'audio'), patch.object(self.driver, 'invoke', side_effect=synthetic_invoke), patch.object(self.driver, 'write_json', side_effect=labelled_write), redirect_stdout(io.StringIO()):
                rows = self.driver.execute_gpu(target, runner, {})
            if label == 'positive-six':
                self.assertEqual(invoked, ['procedural', 'vrm0', 'vrm1', 'backhair', 'lifecycle', 'primary'])
                self.assertEqual(len(rows), 6); self.assertTrue(all(row['passed'] for row in rows))
            else:
                self.assertEqual(invoked, ['procedural']); self.assertEqual(len(rows), 1); self.assertFalse(rows[0]['passed'])


if __name__ == '__main__':
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProposedDriverCPU)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {'format': 'has_wind_proposed_driver_imported_cpu_tests_1', 'tests_run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'passed': result.wasSuccessful(), 'shadow_root': str(SHADOW),
              'imported_proposed_driver': str(SHADOW / 'tests/verify_wind_review.py'),
              'imported_resolver': str(SHADOW / 'tests/native_fixture_plans.py'),
              'actual_prepared_metadata_used_read_only': True, 'external_process_boundaries_mocked': True,
              'godot_started': False, 'native_workers_started': False, 'gpu_used': False,
              'main_or_prototype_modified': False,
              'scope': 'CPU wrapper/resolver gate tests only; no original GPU predicate has run here.'}
    (OUT / 'cpu-tests.log').write_text(stream.getvalue(), encoding='utf-8')
    (OUT / 'cpu-tests.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(stream.getvalue()); print(json.dumps(report, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
