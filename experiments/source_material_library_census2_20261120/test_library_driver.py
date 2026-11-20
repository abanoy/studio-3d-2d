"""Fabricated library-driver contracts only; no processes/assets/runtime/Git.

The only non-test source read is the exact published pure f9bc guard. Its owned
handle helpers receive fabricated handles; every Popen is blocked in this suite.
Temporary files contain ordinary synthetic text, never B/native/media data.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('library_driver_under_test', Path(__file__).with_name('run_library.py'))
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def fixture():
    inputs = {role: dict(bytes=1, sha256='a' * 64) for role in driver.WORKER_ROLES}
    summary = dict(format='has_empty_library_enumeration_summary_2', before_id_count=20, after_id_count=20,
                   id_collections=4, source_id_types=4, source_catalogue_name_count=10, source_materials=4,
                   source_material_names_sha256='b' * 64, source_catalogue_sha256='c' * 64,
                   destination_request_types=4, all_destination_requests_empty=True, actual_id_census_unchanged=True)
    worker = dict(format='has_owned_B_empty_library_census_result_2',
                  status='BOUNDED_EMPTY_LIBRARY_ENUMERATION_MATCHED_2', summary=summary,
                  input_identities=inputs, all_read_inputs_hash_size_stamp_unchanged=True,
                  hidden_placement_verified=True, library_enumeration_executed=True, complete_actual_ID_census_observed=True)
    for key in ('original_B_scene_opened', 'material_append_requested', 'image_pixels_read', 'blend_saved',
                'exporter_invoked', 'native_arrays_published', 'native_or_historical_point_identity_qualified',
                'resource_or_export_qualified', 'normal_fidelity_qualified', 'application_adoption_qualified',
                'material_binding_qualified', 'transient_ID_or_C_level_read_absence_qualified',
                'outer_physical_closure_verified_by_worker'):
        worker[key] = False
    desktop = dict(format='studio_private_desktop_1', desktop='HAS_Test_synthetic', child_pid=9999, exit=0,
                   job_memory_limit_bytes=4096 * 1024 * 1024, private_window_seen=True, child_desktop_confirmed=True,
                   job_closed=True, desktop_closed=True, foreground_child_observed=False, desktop_switch_requested=False)
    policy = dict(format='has_hidden_background_desktop_placement_sentinel_1', **{'class': 'STATIC'},
                  requested_size_pixels=[0, 0], disabled=True, noactivate_style=True, toolwindow_style=True,
                  destroyed_in_finally=True, owned_pid_and_thread_verified=True, visible_at_creation=False,
                  visible_before_destruction=False, show_or_activation_calls=False, thread_desktop_switch_calls=False)
    placement = dict(format='has_owned_B_empty_library_placement_2', policy=policy, worker_verified_hidden_sentinel_closed=True)
    return worker, placement, desktop, inputs


class LibraryDriver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guard = driver.guard_module()  # Exact pure source, no runtime API called.

    def setUp(self):
        self.no_process = patch.object(subprocess, 'Popen', side_effect=AssertionError('no actual process allowed'))
        self.no_process.start()

    def tearDown(self):
        self.no_process.stop()

    def physical(self):
        import os
        return dict(format='has_current_id_physical_closure_1', owned_processes=0, full_pids_absent=True,
                    observer_retained_waited_reaped=True, observer_exit=0,
                    excluded_exact_pid=os.getpid(), observed_ns=time.time_ns())

    def validate(self, values, exit=0):
        worker, placement, desktop, inputs = values
        return driver.validate_library_result(self.guard, worker, placement, desktop,
                                               launcher_exit=exit, expected_inputs=inputs)

    def test_complete_fabricated_empty_census_schema(self):
        self.assertEqual(self.validate(fixture())['source_materials'], 4)

    def test_every_success_observation_is_required_and_boolean(self):
        for key in ('all_read_inputs_hash_size_stamp_unchanged', 'hidden_placement_verified',
                    'library_enumeration_executed', 'complete_actual_ID_census_observed'):
            for value in (False, 1, None):
                values = fixture(); values[0][key] = value
                with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_all_unsupported_scope_flags_remain_false(self):
        worker = fixture()[0]
        keys = [key for key, value in worker.items() if value is False]
        self.assertEqual(len(keys), 13)
        for key in keys:
            values = fixture(); values[0][key] = True
            with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_old_native_id_or_material_binding_result_cannot_qualify_library_scope(self):
        for format in ('has_fresh_sourceio_current_id_probe_1', 'has_fresh_source_material_binding_probe_1'):
            values = fixture(); values[0]['format'] = format
            with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_exact_eight_roles_and_hash_bindings_are_required(self):
        values = fixture(); values[0]['input_identities'] = {}
        with self.assertRaises(self.guard.Refusal): self.validate(values)
        values = fixture(); values[3]['alien'] = values[3].pop('blend')
        with self.assertRaises(self.guard.Refusal): self.validate(values)
        values = fixture(); values[3]['blend']['bytes'] = True
        with self.assertRaises(self.guard.Refusal): self.validate(values)
        values = fixture(); values[3]['blend']['sha256'] = 'X' * 64
        with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_census_counts_cannot_hide_added_ids_or_material_requests(self):
        for key, value in (('after_id_count', 21), ('source_materials', 257), ('destination_request_types', 3),
                           ('all_destination_requests_empty', False), ('actual_id_census_unchanged', False)):
            values = fixture(); values[0]['summary'][key] = value
            with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_extra_unused_whole_library_materials_are_accepted_without_binding_claim(self):
        for count in (1, 5, 17, 256):
            values = fixture()
            values[0]['summary']['source_materials'] = count
            values[0]['summary']['source_catalogue_name_count'] = count + 6
            summary = self.validate(values)
            self.assertEqual(summary['source_materials'], count)
            self.assertTrue(summary['all_destination_requests_empty'])
            self.assertFalse(values[0]['material_binding_qualified'])

    def test_catalogue_count_boolean_zero_overbudget_and_noninteger_refuse(self):
        for count in (True, False, 0, -1, 257, 4.0, '5', None):
            values = fixture(); values[0]['summary']['source_materials'] = count
            with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_safe_summary_observation_retains_refused_count_but_never_names(self):
        value = fixture()[0]['summary']
        value['source_materials'] = 300
        value['private_names'] = ['must not persist']
        value['source_material_names_sha256'] = 'not-a-digest-private-name'
        observed = driver.public_summary_observation(value)
        self.assertEqual(observed['source_materials'], 300)
        self.assertNotIn('private_names', observed)
        self.assertNotIn('source_material_names_sha256', observed)
        self.assertIsNone(driver.public_summary_observation(dict(format='has_empty_library_enumeration_summary_1')))

    def test_v1_success_is_not_accepted_as_census2(self):
        values = fixture()
        values[0]['format'] = 'has_owned_B_empty_library_census_result_1'
        with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_malformed_census_counts_or_digests_refuse(self):
        for key in ('before_id_count', 'after_id_count', 'id_collections', 'source_id_types',
                    'source_catalogue_name_count', 'destination_request_types'):
            for value in (True, -1, 0, 100000):
                values = fixture(); values[0]['summary'][key] = value
                with self.assertRaises(self.guard.Refusal): self.validate(values)
        for key in ('source_material_names_sha256', 'source_catalogue_sha256'):
            values = fixture(); values[0]['summary'][key] = 'private names are not digests'
            with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_private_placement_and_job_closure_are_all_required(self):
        for key in ('private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'):
            values = fixture(); values[2][key] = False
            with self.assertRaises(self.guard.Refusal): self.validate(values)
        for key in ('foreground_child_observed', 'desktop_switch_requested'):
            values = fixture(); values[2][key] = True
            with self.assertRaises(self.guard.Refusal): self.validate(values)
        for key in ('error', 'monitor_error', 'desktop_enumeration_error', 'cancelled'):
            values = fixture(); values[2][key] = 'failure'
            with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_private_timeout_memory_and_exit_cannot_be_waived(self):
        for key, value in (('job_memory_limit_bytes', 0), ('exit', True), ('child_pid', False), ('desktop', 'owner')):
            values = fixture(); values[2][key] = value
            with self.assertRaises(self.guard.Refusal): self.validate(values)
        with self.assertRaises(self.guard.Refusal): self.validate(fixture(), exit=1)
        with self.assertRaises(self.guard.Refusal): self.validate(fixture(), exit=False)

    def test_real_hidden_sentinel_policy_is_required(self):
        for key in ('disabled', 'noactivate_style', 'toolwindow_style', 'destroyed_in_finally', 'owned_pid_and_thread_verified'):
            values = fixture(); values[1]['policy'][key] = False
            with self.assertRaises(self.guard.Refusal): self.validate(values)
        for key in ('visible_at_creation', 'visible_before_destruction', 'show_or_activation_calls', 'thread_desktop_switch_calls'):
            values = fixture(); values[1]['policy'][key] = True
            with self.assertRaises(self.guard.Refusal): self.validate(values)
        values = fixture(); values[1]['policy']['requested_size_pixels'] = [1, 1]
        with self.assertRaises(self.guard.Refusal): self.validate(values)

    def test_registered_original_and_owned_checks_exist_before_later_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            checks = {}
            original, owned = Path(folder)/'original.txt', Path(folder)/'owned.txt'
            original.write_bytes(b'ordinary synthetic text'); owned.write_bytes(original.read_bytes())
            for label, path in (('protected_original_B', original), ('owned_B_copy', owned)):
                raw, row, identity = self.guard.read_checked(path)
                driver.remember_file(checks, self.guard, label, path, (len(raw), driver.sha(raw)), row, identity)
            owned.write_bytes(b'changed synthetic copy')
            results = driver.preservation_results(checks)
            self.assertEqual(results, {'protected_original_B': True, 'owned_B_copy': False})

    def test_one_failed_preservation_read_does_not_skip_following_checks(self):
        calls = []
        def failed(): calls.append('source'); raise OSError('fake')
        def passed(): calls.append('owned'); return True
        self.assertEqual(driver.preservation_results({'source': failed, 'owned': passed}), {'source': False, 'owned': True})
        self.assertEqual(calls, ['source', 'owned'])

    def test_launch_record_failure_reaps_exact_owned_handle_before_all_checks_and_CIM(self):
        events = []
        class Owned:
            returncode = None
            def poll(self): return self.returncode
            def kill(self): events.append('kill_owned'); self.returncode = -9
            def wait(self, timeout=None): events.append(('wait_owned', timeout)); return self.returncode
        process = Owned()
        error = self.guard.Refusal('PRIMARY_RECORD_WRITE_FAILURE')
        def writer(): events.append('record'); raise error
        with self.assertRaises(self.guard.Refusal) as caught:
            self.guard.wait_recorded_owned(process, writer)
        self.assertIs(caught.exception, error)
        checks = {name: (lambda name=name: events.append(name) or True)
                  for name in ('source', 'runtime', 'original', 'owned', 'probe', 'support', 'driver')}
        def observer(): events.append('CIM'); return self.physical()
        audit = driver.failed_audit(self.guard, checks, error, process=process, launched=True,
                                    receipt_present=False, closure_observer=observer)
        self.assertEqual(events.count('kill_owned'), 1)
        self.assertLess(events.index('kill_owned'), events.index('source'))
        self.assertEqual(events[-1], 'CIM')
        self.assertTrue(all(audit['preservation_checks'].values()))
        self.assertEqual(audit['error_code'], 'PRIMARY_RECORD_WRITE_FAILURE')
        self.assertEqual(audit['status'], 'UNQUALIFIED_FAILED_RUN')
        self.assertFalse(audit['worker_receipt_present'])
        self.assertFalse(audit['runtime_lane_released'])

    def test_timeout_with_missing_receipt_and_failed_CIM_preserves_all_checks_and_primary_error(self):
        events = []
        class Owned:
            returncode = None
            def poll(self): return self.returncode
            def kill(self): events.append('kill_owned'); self.returncode = -9
            def wait(self, timeout=None):
                events.append(('wait', timeout))
                if timeout == 185: raise subprocess.TimeoutExpired('FAKE_ONLY', timeout)
                return self.returncode
        process = Owned()
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            self.guard.wait_recorded_owned(process, lambda: None)
        def check(): events.append('preserve'); return True
        def observer(): events.append('CIM'); raise self.guard.Refusal('CIM_FAILED')
        audit = driver.failed_audit(self.guard, {name: check for name in ('source','runtime','original','owned','code')},
                                    caught.exception, process=process, launched=True, receipt_present=False, closure_observer=observer)
        self.assertEqual(events.count('preserve'), 5)
        self.assertEqual(events.count('kill_owned'), 1)
        self.assertEqual(events[-1], 'CIM')
        self.assertEqual(audit['error_type'], 'TimeoutExpired')
        self.assertFalse(audit['physical_closure_confirmed'])
        self.assertTrue(audit['owned_lock_retained'])
        self.assertFalse(audit['runtime_lane_released'])

    def test_failed_checks_and_successful_closure_never_produce_success(self):
        audit = driver.failed_audit(self.guard, {'source': lambda: False, 'original': lambda: True},
                                    self.guard.Refusal('PRIMARY_FAILURE'), process=None, launched=False,
                                    receipt_present=False, closure_observer=self.physical)
        self.assertTrue(audit['physical_closure_confirmed'])
        self.assertFalse(audit['all_attempted_checks_passed'])
        self.assertEqual(audit['status'], 'UNQUALIFIED_FAILED_RUN')
        self.assertFalse(audit['application_adoption_qualified'])
        self.assertFalse(audit['normal_fidelity_qualified'])

    def test_unproven_closure_retains_lock_without_touching_foreign_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'foreign-lock.txt'; path.write_bytes(b'foreign owner')
            result = driver.release_owned_lock(self.guard, path, None, release_allowed=False)
            self.assertTrue(result['owned_lock_retained'])
            self.assertEqual(path.read_bytes(), b'foreign owner')

    def test_changed_foreign_lock_is_never_unlinked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'lane.lock'; path.write_bytes(b'owned')
            identity = self.guard.stamp(path.lstat())
            path.write_bytes(b'foreign-controller-longer')
            result = driver.release_owned_lock(self.guard, path, identity, release_allowed=True)
            self.assertTrue(result['owned_lock_retained'])
            self.assertTrue(result['owned_lock_cleanup_refused'])
            self.assertEqual(path.read_bytes(), b'foreign-controller-longer')

    def test_only_exact_owned_lock_can_be_removed_after_closure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'lane.lock'
            with path.open('xb') as stream: stream.write(b'owned')
            result = driver.release_owned_lock(self.guard, path, self.guard.stamp(path.lstat()), release_allowed=True)
            self.assertFalse(result['owned_lock_retained'])
            self.assertFalse(path.exists())

    def test_existing_foreign_stage_is_refused_without_writing_into_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'output').mkdir()
            stage = root/'output/source-library-enumeration2-run-123'
            stage.mkdir(); marker=stage/'foreign.txt'; marker.write_bytes(b'foreign')
            with patch.object(driver, 'ROOT', root), patch.object(driver.time, 'time_ns', return_value=123):
                with self.assertRaisesRegex(self.guard.Refusal, 'FRESH_LIBRARY_STAGE_REQUIRED'):
                    driver.new_stage(self.guard)
            self.assertEqual(tuple(path.name for path in stage.iterdir()), ('foreign.txt',))
            self.assertEqual(marker.read_bytes(), b'foreign')

    def test_main_without_root_lane_stops_before_source_runtime_or_native(self):
        args = ['run_library.py', '--driver-sha256', 'a'*64, '--worker-sha256', driver.WORKER_PIN[1]]
        with patch.object(sys, 'argv', args), patch.object(driver, 'guard_module', return_value=self.guard), \
             patch.object(self.guard, 'read_checked', side_effect=AssertionError('no source read')) as reader:
            with self.assertRaises(self.guard.Refusal): driver.main()
            reader.assert_not_called()

    def test_main_wrong_worker_pin_stops_before_any_source_or_native_read(self):
        args = ['run_library.py', '--root-lane-confirmed', '--driver-sha256', 'a'*64, '--worker-sha256', 'b'*64]
        with patch.object(sys, 'argv', args), patch.object(driver, 'guard_module', return_value=self.guard), \
             patch.object(self.guard, 'read_checked', side_effect=AssertionError('no source read')) as reader:
            with self.assertRaisesRegex(self.guard.Refusal, 'FROZEN_LIBRARY_WORKER_REQUIRED'): driver.main()
            reader.assert_not_called()

    def test_bad_full_result_stops_before_lock_source_runtime_process(self):
        raw = b'synthetic driver source'
        failed = dict(format='has_reference_body_full_coordinator_1', revision=self.guard.TESTED, exit=0,
                      functional_source_count=1061, whole_verifier_pass=False)
        def proofs(path): return (failed if path.name=='completion.json' else {}, {})
        args = ['run_library.py', '--root-lane-confirmed', '--driver-sha256', driver.sha(raw), '--worker-sha256', driver.WORKER_PIN[1]]
        with patch.object(sys, 'argv', args), patch.object(driver, 'guard_module', return_value=self.guard), \
             patch.object(self.guard, 'read_checked', return_value=(raw, {}, ())), patch.object(self.guard, 'json_read', side_effect=proofs), \
             patch.object(self.guard, 'source_snapshot', side_effect=AssertionError('no source snapshot')) as source, \
             patch.object(self.guard, 'runtime_check', side_effect=AssertionError('no runtime read')) as runtime, \
             patch.object(driver.os, 'open', side_effect=AssertionError('no lock allocation')) as lock:
            with self.assertRaises(self.guard.Refusal): driver.main()
            source.assert_not_called(); runtime.assert_not_called(); lock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
