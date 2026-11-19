"""CPU protocol, path and retained-process fakes; no native child is started."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest.mock import patch
import copy
import hashlib
import importlib.util
import json
import subprocess
import unittest

import protocol as P
import root_runner as R


def contract():
    path = R.PROBE / 'weight_storage_contract.py'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'f71753e3b7183c5fab343bf8af504cd5613879bd95b89d5f338f54123180db18'
    spec = importlib.util.spec_from_file_location('runtime_test_synthetic_contract', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


NOW = datetime(2026, 11, 18, 18, tzinfo=timezone.utc)


def authority(root):
    return {'format': 'has_root_synthetic_weight_storage_execution_authority_1', 'phase': 'ROOT_APPROVED_FRESH_SYNTHETIC_ONLY',
            'metadata_head': P.HEAD, 'run_id': '1' * 32, 'issued_utc': NOW.isoformat(),
            'expires_utc': (NOW + timedelta(minutes=10)).isoformat(),
            'output_root': str(root / 'output' / ('weight-storage-probe-20261118-' + '1' * 32)),
            'runtime_packet_sha256': 'a' * 64, 'probe_packet_sha256': 'b' * 64, 'root_execution_authorized': True,
            'root_lane': {'format': 'has_root_synthetic_weight_storage_closed_lane_1', 'observed_utc': NOW.isoformat(),
                          'owned_count': 0, 'main_count': 0, 'review_count': 0, 'termination_issued': False}}


def receipt(exit_code=0):
    return {'format': 'studio_private_desktop_1', 'exit': exit_code, 'child_pid': 123,
            'child_desktop_confirmed': True, 'private_window_seen': True,
            'foreground_child_observed': False, 'desktop_switch_requested': False,
            'job_closed': True, 'desktop_closed': True, 'job_memory_limit_bytes': 2048 * 1024 * 1024}


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.C = contract(); C = cls.C; catalogue = C.cases()
        cls.rows = tuple(C.expected_row(case) for case in catalogue)
        cls.plan = {'run_id': '1' * 32, 'scripts': {'probe.py': {'bytes': 1, 'sha256': 'a' * 64}},
                    'runtime': {'path': str(R.ROOT / 'synthetic-not-an-executable'), 'bytes': 1, 'sha256': 'b' * 64}}
        cls.report = {'format': 'has_synthetic_blender_weight_storage_observation_1', 'status': 'BOUNDED_SYNTHETIC_STORAGE_MATCH',
                      'run_id': cls.plan['run_id'], 'request_sha256': 'c' * 64, 'copied_script_identities': cls.plan['scripts'],
                      'Root_expected_runtime_identity': cls.plan['runtime'], 'case_count': C.CASE_COUNT, 'group_count': C.GROUP_COUNT,
                      'group_alphabet': list(C.GROUP_IDS), 'weight_word_alphabet': [f'{x:08x}' for x in C.WEIGHT_WORDS],
                      'sourceio_importer_rule_sha256': C.SOURCEIO_IMPORTER_SHA256,
                      'expected_positive_add_calls': C.POSITIVE_WRITE_COUNT, 'positive_add_calls': C.POSITIVE_WRITE_COUNT,
                      'owned_object_mesh_cleanup_exact': True, 'cleanup_error_types': [], 'synthetic_group_indices_exact': True,
                      'runtime_binary_hash_verified_by_probe': False, 'native_API_execution_observed_by_this_script': True,
                      'factory_background_no_model_file': True, 'scene_or_native_model_files_opened': False,
                      'files_exported_or_blend_saved': False, 'window_or_desktop_API_called_by_probe': False,
                      'runtime_version': [5, 1, 2], 'runtime_version_string': '5.1.2', 'runtime_build_hash': 'synthetic-build',
                      'mesh_validate_reported_change': False, 'immediate_vs_after_validate_exact': True,
                      'case_catalogue_sha256': C.case_digest(catalogue),
                      'immediate': C.compare_readback(catalogue, cls.rows), 'after_validate': C.compare_readback(catalogue, cls.rows),
                      **{name: False for name in P.QUALIFICATIONS}}
        cls.report = json.loads(json.dumps(cls.report))

    def test_exact_root_authority_and_fresh_expiry_rechecks(self):
        a = authority(R.ROOT)
        self.assertEqual(P.authority(a, R.ROOT, 'a' * 64, 'b' * 64, NOW), Path(a['output_root']))
        with self.assertRaises(ValueError): P.authority(a, R.ROOT, 'a' * 64, 'b' * 64, NOW + timedelta(minutes=3))
        P.authority(a, R.ROOT, 'a' * 64, 'b' * 64, NOW + timedelta(minutes=3), initial=False)

    def test_expired_old_head_packet_lane_and_stage_substitution_refuse(self):
        for key, value in [('metadata_head', 'dcb' + '0' * 37), ('probe_packet_sha256', 'c' * 64),
                           ('root_execution_authorized', 1), ('expires_utc', NOW.isoformat()),
                           ('output_root', str(R.ROOT / 'output/other'))]:
            a = authority(R.ROOT); a[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): P.authority(a, R.ROOT, 'a' * 64, 'b' * 64, NOW)
        for key, value in [('main_count', 1), ('review_count', False), ('termination_issued', True)]:
            a = authority(R.ROOT); a['root_lane'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): P.authority(a, R.ROOT, 'a' * 64, 'b' * 64, NOW)

    def test_background_hidden_window_requires_real_observation_desktop_and_closure(self):
        value = P.receipt(receipt(), 0, self.C)
        self.assertIs(value['private_window_seen'], True); self.assertIs(value['visible_window_required'], False)
        self.assertEqual(P.receipt(receipt(47), 47, self.C)['child_exit'], 47)

    def test_receipt_headless_bypass_foreground_switch_monitor_or_memory_fail_refuse(self):
        for key, value in [('child_desktop_confirmed', False), ('foreground_child_observed', True),
                           ('desktop_switch_requested', True), ('job_closed', False), ('desktop_closed', False),
                           ('job_memory_limit_bytes', 4096 * 1024 * 1024), ('exit', False), ('private_window_seen', 0), ('private_window_seen', False),
                           ('monitor_error', ''), ('desktop_enumeration_error', 0)]:
            r = receipt(); r[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): P.receipt(r, 0, self.C)

    def test_matching_report_uses_sealed_validator_and_keeps_all_qualification_false(self):
        with patch.object(self.C, 'validate_matching_public_report', wraps=self.C.validate_matching_public_report) as validator:
            summary = P.observation(self.report, self.plan, 'c' * 64, self.C)
            self.assertEqual(validator.call_count, 1)
        self.assertEqual(summary['observation_status'], 'BOUNDED_SYNTHETIC_STORAGE_MATCH')
        self.assertIs(summary['native_storage_rule_qualified'], False)

    def test_nonzero_mismatch_is_valid_retained_not_pass_and_never_pass_validator(self):
        report = copy.deepcopy(self.report); rows = list(self.rows); rows[0] = ((0, 0x3f800000),)
        report['immediate'] = self.C.compare_readback(self.C.cases(), tuple(rows))
        report.update(status='BOUNDED_SYNTHETIC_STORAGE_MISMATCH', immediate_vs_after_validate_exact=False)
        report = json.loads(json.dumps(report))
        with patch.object(self.C, 'validate_matching_public_report', side_effect=AssertionError('Mismatch must not use pass parser')):
            summary = P.observation(report, self.plan, 'c' * 64, self.C)
        self.assertGreater(summary['phases']['immediate']['mismatch_cases'], 0)
        process = {'exit': 47, 'timed_out': False, 'retained_Popen_reaped': True}
        background = P.receipt(receipt(47), 47, self.C)
        self.assertIs(P.completed(process, background, summary, True, True, True, {'hidden_host_placement_complete': True, 'probe_return_code': 1}), False)
        process['exit'] = 0; background['child_exit'] = 0
        self.assertIs(P.completed(process, background, summary, True, True, True, {'hidden_host_placement_complete': True, 'probe_return_code': 1}), False)

    def test_public_report_binding_version_cleanup_flags_and_count_mutations_refuse(self):
        for key, value in [('request_sha256', 'd' * 64), ('run_id', '2' * 32), ('runtime_version', [5, 1, 3]),
                           ('owned_object_mesh_cleanup_exact', False), ('native_storage_rule_qualified', True),
                           ('positive_add_calls', True)]:
            report = copy.deepcopy(self.report); report[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): P.observation(report, self.plan, 'c' * 64, self.C)
        report = copy.deepcopy(self.report); report['immediate']['mismatch_counts']['weight_word'] = 1
        with self.assertRaises(ValueError): P.observation(report, self.plan, 'c' * 64, self.C)

    def test_pass_requires_zero_exit_preservation_both_scopes_and_exact_match(self):
        summary = {'observation_status': 'BOUNDED_SYNTHETIC_STORAGE_MATCH'}
        process = {'exit': 0, 'timed_out': False, 'retained_Popen_reaped': True}
        background = P.receipt(receipt(), 0, self.C)
        placement = {'hidden_host_placement_complete': True, 'probe_return_code': 0}
        self.assertIs(P.completed(process, background, summary, True, True, True, placement), True)
        for preserved, before, after in ((False, True, True), (True, False, True), (True, True, False)):
            self.assertIs(P.completed(process, background, summary, preserved, before, after, placement), False)
        for field, value in [('exit', 47), ('exit', False), ('timed_out', True), ('retained_Popen_reaped', False)]:
            changed = dict(process); changed[field] = value
            self.assertIs(P.completed(changed, background, summary, True, True, True, placement), False)
        self.assertIs(P.completed(process, background, summary, True, True, True, {}), False)


class SourceAndOwnedProcessTests(unittest.TestCase):
    def test_default_invocation_does_not_start_process_or_read_runtime(self):
        with (patch.object(R.subprocess, 'Popen', side_effect=AssertionError('No child')),
              patch.object(R, 'context', side_effect=AssertionError('No context IO'))):
            self.assertEqual(R.main([]), 0)

    def test_exact_approved_command_has_offline_factory_threads_exit47_and_no_model(self):
        pins = json.loads((R.HERE / 'RUNTIME_PINS.json').read_bytes()); stage = R.ROOT / 'output/synthetic-unit-stage'
        argv = R.command(stage, pins, 'd' * 64)
        for flag in ('--factory-startup', '--disable-autoexec', '--offline-mode', '--background'): self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index('--threads') + 1], '1')
        self.assertEqual(argv[argv.index('--python-exit-code') + 1], '47')
        self.assertEqual(argv[argv.index('--timeout') + 1], '120')
        self.assertEqual(argv[argv.index('--memory-limit-mib') + 1], '2048')
        self.assertNotIn('--headless', argv)
        self.assertEqual(argv[-4:], ['--host-request', str(stage / 'host-request.json'), '--host-request-sha256', 'd' * 64])
        self.assertEqual(argv[argv.index('--python') + 1], str(stage / 'host/weight_storage_host.py'))
        self.assertFalse(any(value.lower().endswith(('.blend', '.mdl', '.vvd', '.vtx')) for value in argv))

    def test_bounded_json_duplicate_keys_and_stable_single_link_reads(self):
        with self.assertRaises(ValueError): R.document('{"x":1,"x":2}')
        with self.assertRaises(ValueError): R.document('{"x":NaN}')
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'small.json'; path.write_bytes(b'{}')
            self.assertEqual(R.read(path, 2)[0], b'{}')
            with self.assertRaises(ValueError): R.read(path, 1)
            with self.assertRaises(FileExistsError): R.save(path, {})

    def test_closed_packet_rejects_extra_files_paths_and_changed_payloads(self):
        with TemporaryDirectory() as folder:
            root = Path(folder); body = b'x'; (root / 'source.py').write_bytes(body)
            value = {'files': [{'path': 'source.py', 'bytes': 1, 'sha256': hashlib.sha256(body).hexdigest()}]}
            raw = json.dumps(value).encode(); (root / 'INDEX.json').write_bytes(raw); pin = hashlib.sha256(raw).hexdigest()
            self.assertEqual(set(R.packet(root, pin)), {'source.py'})
            (root / 'source.py').write_bytes(b'y')
            with self.assertRaises(ValueError): R.packet(root, pin)
            (root / 'extra.py').write_bytes(b'x')
            with self.assertRaises(ValueError): R.packet(root, pin)

    def test_retained_wrapper_fake_zero_nonzero_timeout_and_finally_reap(self):
        class Fake:
            pid = 1234
            def __init__(self, code, timeouts): self.returncode = None; self.code = code; self.timeouts = timeouts; self.killed = False; self.terminated = False
            def wait(self, timeout):
                if self.timeouts:
                    self.timeouts -= 1; raise subprocess.TimeoutExpired('synthetic-owned', timeout)
                self.returncode = self.code
                return self.code
            def poll(self): return self.returncode
            def terminate(self): self.terminated = True
            def kill(self): self.killed = True
        for code, timeouts in ((0, 0), (47, 0), (2, 2)):
            fake = Fake(code, timeouts)
            with TemporaryDirectory() as folder, patch.object(R.subprocess, 'Popen', return_value=fake):
                result = R.invoke(Path(folder), ['synthetic-not-an-executable'], {})
                self.assertEqual(result['exit'], code); self.assertIs(result['retained_Popen_reaped'], True)
                self.assertEqual(result['timed_out'], bool(timeouts)); self.assertEqual(fake.killed, bool(timeouts))

    def test_unexpected_wait_failure_still_kills_and_reaps_only_retained_child(self):
        class Fake:
            pid = 1234; returncode = None; waits = 0; killed = False
            def wait(self, timeout):
                self.waits += 1
                if self.waits == 1: raise RuntimeError('Synthetic wait failure')
                self.returncode = 2
                return 2
            def poll(self): return self.returncode
            def kill(self): self.killed = True
        fake = Fake()
        with TemporaryDirectory() as folder, patch.object(R.subprocess, 'Popen', return_value=fake):
            with self.assertRaises(RuntimeError): R.invoke(Path(folder), ['synthetic-not-an-executable'], {})
        self.assertIs(fake.killed, True); self.assertEqual(fake.waits, 2); self.assertEqual(fake.returncode, 2)


if __name__ == '__main__': unittest.main()
