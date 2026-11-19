"""Synthetic host/placement orchestration and path guards; fake WinAPI only."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest.mock import patch
import copy
import hashlib
import json
import io
import sys
import unittest
from contextlib import redirect_stdout

import protocol as P
import weight_storage_host as H
import root_runner as R


def sidecar():
    return {'format': 'has_hidden_weight_probe_host_placement_1', 'status': 'HIDDEN_PLACEMENT_COMPLETE',
            'run_id': '1' * 32, 'request_sha256': 'a' * 64, 'host_request_sha256': 'b' * 64,
            'runtime_packet_sha256': 'c' * 64, 'host_source_identities': {'synthetic': {'bytes': 1, 'sha256': 'd' * 64}},
            'public_probe_sha256': 'e' * 64, 'probe_return_code': 0, 'placement': copy.deepcopy(H.PLACEMENT),
            'error_type': None, 'placement_sync_hold_seconds_before': 0.5, 'placement_sync_hold_seconds_after': 0.5,
            'host_window_API_scope': 'Exact approved hidden placement helper only; no shown/activated window or desktop switch.',
            'unchanged_probe_window_or_desktop_API_called': False, 'native_storage_rule_qualified': False,
            'native_fidelity_export_repair_adoption_qualified': False}


def validate(value):
    return P.placement(value, request_sha='a' * 64, host_request_sha='b' * 64, run_id='1' * 32,
                       sources={'synthetic': {'bytes': 1, 'sha256': 'd' * 64}}, runtime_sha='c' * 64,
                       report_sha='e' * 64, probe_status='BOUNDED_SYNTHETIC_STORAGE_MATCH')


class HostTests(unittest.TestCase):
    def factory(self, *, bad=None, cleanup_error=False):
        policy = copy.deepcopy(H.PLACEMENT); policy['destroyed_in_finally'] = False; policy['visible_before_destruction'] = None
        active = {'value': False}
        @contextmanager
        def sentinel():
            active['value'] = True
            try: yield policy
            finally:
                active['value'] = False
                if cleanup_error: raise OSError('Synthetic destroy failure')
                policy['destroyed_in_finally'] = True; policy['visible_before_destruction'] = False
                if bad is not None: policy[bad[0]] = bad[1]
        return sentinel, policy, active

    def test_complete_probe_runs_inside_hidden_scope_and_cleanup_precedes_success(self):
        factory, policy, active = self.factory(); holds = []; previous = sys.argv[:]
        def probe():
            self.assertTrue(active['value']); self.assertFalse(policy['destroyed_in_finally'])
            self.assertEqual(sys.argv[1:], ['--', '--plan', 'synthetic-request.json'])
            return 0
        result = H.run_with_placement(probe, factory, 'synthetic-request.json', holds.append)
        self.assertEqual(holds, [0.5, 0.5]); self.assertEqual(sys.argv, previous)
        self.assertTrue(result['placement_complete']); self.assertFalse(active['value'])
        self.assertEqual(result['placement'], H.PLACEMENT)

    def test_mismatch_probe_code_and_original_no_window_scope_remain_unchanged(self):
        factory, _, _ = self.factory(); original = {'window_or_desktop_API_called_by_probe': False}
        before = copy.deepcopy(original)
        result = H.run_with_placement(lambda: 1, factory, 'synthetic', lambda seconds: None)
        self.assertTrue(result['placement_complete']); self.assertEqual(result['probe_return_code'], 1)
        self.assertEqual(original, before)

    def test_probe_error_cleanup_failure_type_and_visibility_changes_refuse(self):
        for failure in (ValueError, SystemExit, KeyboardInterrupt):
            factory, policy, active = self.factory(); previous = sys.argv[:]
            def probe(): raise failure('Synthetic probe failure')
            result = H.run_with_placement(probe, factory, 'synthetic', lambda seconds: None)
            self.assertFalse(result['placement_complete']); self.assertTrue(policy['destroyed_in_finally'])
            self.assertFalse(active['value']); self.assertEqual(sys.argv, previous)
        for bad in (('destroyed_in_finally', False), ('visible_at_creation', True), ('disabled', 1), ('show_or_activation_calls', True)):
            factory, _, _ = self.factory(bad=bad)
            self.assertFalse(H.run_with_placement(lambda: 0, factory, 'synthetic', lambda seconds: None)['placement_complete'])
        factory, _, _ = self.factory(cleanup_error=True)
        self.assertEqual(H.run_with_placement(lambda: 0, factory, 'synthetic', lambda seconds: None)['error_type'], 'OSError')

    def test_post_cleanup_placement_binds_all_hashes_scope_and_exact_policy(self):
        self.assertTrue(validate(sidecar())['hidden_host_placement_complete'])
        for key, value in [('request_sha256', '0' * 64), ('host_request_sha256', '0' * 64), ('public_probe_sha256', '0' * 64),
                           ('host_source_identities', {}), ('placement_sync_hold_seconds_before', 0),
                           ('unchanged_probe_window_or_desktop_API_called', True), ('error_type', 'OSError'), ('probe_return_code', True)]:
            record = sidecar(); record[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): validate(record)
        for key, value in [('destroyed_in_finally', False), ('class', 'MESSAGE_ONLY'), ('noactivate_style', False),
                           ('visible_before_destruction', True), ('thread_desktop_switch_calls', True)]:
            record = sidecar(); record['placement'][key] = value
            with self.subTest(policy=key), self.assertRaises(ValueError): validate(record)

    def test_first_no_window_counterexample_receipt_is_still_refused(self):
        value = {'format': 'studio_private_desktop_1', 'exit': 2, 'child_pid': 123,
                 'private_window_seen': False, 'child_desktop_confirmed': False,
                 'foreground_child_observed': False, 'desktop_switch_requested': False,
                 'job_closed': True, 'desktop_closed': True, 'job_memory_limit_bytes': 2048 * 1024 * 1024,
                 'error': 'No owned graphical window was verified on the private desktop'}
        with self.assertRaises(ValueError): P.receipt(value, 2, None)

    def test_owned_host_request_closure_hash_plan_and_path_guards(self):
        with TemporaryDirectory() as folder:
            output = Path(folder) / 'output'; output.mkdir()
            stage = output / ('weight-storage-probe-20261118-' + '1' * 32); stage.mkdir(); host = stage / 'host'; host.mkdir()
            identities = {}
            for name in H.HOST_NAMES:
                raw = (Path(H.__file__).parent / name).read_bytes(); (host / name).write_bytes(raw)
                identities[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            plan = stage / 'request.json'; plan.write_bytes(b'{"synthetic":true}')
            request = {'format': 'has_owned_hidden_weight_host_request_1', 'run_id': '1' * 32, 'stage': str(stage),
                       'plan': str(plan), 'plan_sha256': hashlib.sha256(plan.read_bytes()).hexdigest(),
                       'runtime_packet_sha256': 'c' * 64, 'host_sources': identities}
            path = stage / 'host-request.json'; raw = json.dumps(request).encode(); path.write_bytes(raw)
            with patch.object(H, 'HERE', host), patch.object(H, 'WORKSPACE_OUTPUT', output):
                self.assertEqual(H.load_request(path, hashlib.sha256(raw).hexdigest())[0], request)
                (host / 'extra.py').write_bytes(b'not a source member')
                with self.assertRaises(ValueError): H.load_request(path, hashlib.sha256(raw).hexdigest())

    def test_post_probe_context_accepts_completed_output_but_rechecks_source_expiry_and_env(self):
        now = datetime.now(timezone.utc)
        with TemporaryDirectory() as folder:
            stage = Path(folder); source = stage / 'source'; source.mkdir(); temp = stage / 'temp'; temp.mkdir()
            for name in H.PROBE_SCRIPTS: (source / name).write_bytes((R.PROBE / name).read_bytes())
            (stage / 'PUBLIC_WEIGHT_STORAGE.json').write_text('{"synthetic_completed":true}')
            plan = {'scripts': copy.deepcopy(H.PROBE_SCRIPTS), 'expires_utc': (now + timedelta(minutes=5)).isoformat(), 'owned_temp': str(temp)}
            with patch.dict(H.os.environ, TEMP=str(temp), TMP=str(temp)):
                H.post_probe_context(source, plan, now)
                expired = dict(plan); expired['expires_utc'] = now.isoformat()
                with self.assertRaises(ValueError): H.post_probe_context(source, expired, now)
                (source / 'weight_storage_contract.py').write_bytes(b'changed')
                with self.assertRaises(ValueError): H.post_probe_context(source, plan, now)

    def test_complete_host_main_does_not_repeat_fresh_output_preflight(self):
        with TemporaryDirectory() as folder:
            output = Path(folder) / 'output'; output.mkdir()
            stage = output / ('weight-storage-probe-20261118-' + '1' * 32); stage.mkdir()
            host = stage / 'host'; host.mkdir(); source = stage / 'source'; source.mkdir(); temp = stage / 'temp'; temp.mkdir()
            identities = {}
            for name in H.HOST_NAMES:
                raw = (Path(H.__file__).parent / name).read_bytes(); (host / name).write_bytes(raw)
                identities[name] = {'bytes': len(raw), 'sha256': H.digest(raw)}
            for name in H.PROBE_SCRIPTS: (source / name).write_bytes((R.PROBE / name).read_bytes())
            public = stage / 'PUBLIC_WEIGHT_STORAGE.json'
            plan = {'scripts': copy.deepcopy(H.PROBE_SCRIPTS), 'run_id': '1' * 32, 'owned_temp': str(temp),
                    'expires_utc': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()}
            plan_path = stage / 'request.json'; plan_raw = json.dumps(plan).encode(); plan_path.write_bytes(plan_raw)
            request = {'format': 'has_owned_hidden_weight_host_request_1', 'run_id': '1' * 32, 'stage': str(stage),
                       'plan': str(plan_path), 'plan_sha256': H.digest(plan_raw), 'runtime_packet_sha256': 'c' * 64, 'host_sources': identities}
            request_path = stage / 'host-request.json'; raw = json.dumps(request).encode(); request_path.write_bytes(raw)
            calls = []
            def fresh_preflight(path):
                calls.append(path)
                self.assertFalse(public.exists(), 'Sealed fresh-output preflight cannot run after probe completion')
                return plan, H.digest(plan_raw)
            def probe_main(): public.write_text('{"completed_synthetic_report":true}'); return 0
            factory, _, active = self.factory()
            fakeprobe = NS(read_plan=fresh_preflight, main=probe_main)
            fakehelper = NS(_hidden_placement_sentinel=factory)
            fakebpy = NS(app=NS(background=True, online_access=False, version=(5, 1, 2)), data=NS(filepath=''),
                         context=NS(preferences=NS(filepaths=NS(use_scripts_auto_execute=False))))
            original = H.run_with_placement
            with (patch.object(H, 'HERE', host), patch.object(H, 'WORKSPACE_OUTPUT', output),
                  patch.dict(H.os.environ, TEMP=str(temp), TMP=str(temp)), patch.dict(sys.modules, {'bpy': fakebpy}),
                  patch.object(H, 'module', side_effect=[fakeprobe, fakehelper]),
                  patch.object(H, 'run_with_placement', side_effect=lambda fn, ctx, path: original(fn, ctx, path, lambda seconds: None)),
                  redirect_stdout(io.StringIO())):
                self.assertEqual(H.main(['--host-request', str(request_path), '--host-request-sha256', H.digest(raw)]), 0)
            result = json.loads((stage / 'PUBLIC_HOST_PLACEMENT.json').read_bytes())
            self.assertEqual(len(calls), 1); self.assertEqual(result['status'], 'HIDDEN_PLACEMENT_COMPLETE')
            self.assertTrue(result['placement']['destroyed_in_finally']); self.assertFalse(active['value'])
            self.assertEqual(result['public_probe_sha256'], H.digest(public.read_bytes()))
