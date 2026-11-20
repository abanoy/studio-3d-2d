"""Synthetic stdlib-only coordinator tests. No Blender, CIM, Git or real fixtures.

All launch/read callbacks are local fakes. These tests qualify admission logic
and retained handle behavior only; they cannot qualify native IDs or fidelity.
"""
from pathlib import Path
import copy
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('current_id_root_driver_under_test', Path(__file__).with_name('run_probe.py'))
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def context():
    source = {'src/fake_%04d.gd' % index: dict(bytes=1, mtime_ns=123456789,
                                             sha256='a' * 64, git_sha1='b' * 40)
              for index in range(driver.COUNT)}
    normal = dict(format='studio_private_desktop_1', desktop='HAS_Test_normal', job_closed=True,
                  desktop_closed=True, child_desktop_confirmed=True, foreground_child_observed=False,
                  desktop_switch_requested=False, exit=0)
    cancel = dict(normal, desktop='HAS_Test_cancel', exit=2, cancelled=True, error='Owned converter cancelled')
    jobs = [dict(path='output/fake/receipt.json', value=normal),
            dict(path='output/krita-cancel/receipt.json', value=cancel)]
    value = dict(format='has_reference_body_full_coordinator_1', revision=driver.TESTED, exit=0,
                 functional_source_count=driver.COUNT, current_jobs=jobs, unique_current_private_jobs=2)
    for key in ('whole_verifier_pass', 'child_reaped', 'functional_sources_unchanged', 'revision_unchanged',
                'fresh_final_report', 'all_private_jobs_isolated_closed', 'nonzero_jobs_are_expected_cancellations',
                'receipt_provenance_verified'):
        value[key] = True
    return dict(root_lane_confirmed=True, completion=value,
                launch=dict(revision=driver.TESTED, pid=1001, coordinator_pid=1002, started_ns=123456789),
                before=source, after=copy.deepcopy(source),
                committed={name: row['git_sha1'] for name, row in source.items()})


def native_result():
    observation = dict(format='has_fresh_sourceio_current_id_and_RNA_weight_observation_1',
                       observed_new_models=2, observed_new_points=9661, observed_new_corners=42702,
                       fresh_creation_chain_matches_independent_native_candidate=True,
                       current_exact_family_ordered_weight_storage_observed=True,
                       models=[dict(points=8011, corners=34332, groups=69, observed_stages=4),
                               dict(points=1650, corners=8370, groups=69, observed_stages=4)])
    for key in ('historical_saved_B_native_causality_qualified', 'current_B_opened_or_relabelled',
                'generic_weight_storage_qualified', 'native_normal_fidelity_qualified', 'carrier_or_exporter_binding_qualified',
                'non_normal_semantic_equivalence_qualified', 'application_adoption_qualified'):
        observation[key] = False
    result = dict(format='has_fresh_sourceio_current_id_probe_1',
                  status='MATCHED_FRESH_NATIVE_IDS_AND_CURRENT_RNA_WEIGHTS', observation=observation,
                  material_files_opened=0, image_datablocks_created=0, sourceio_catalogue_files=574,
                  input_identities={str(index): dict(bytes=1, sha256='a' * 64) for index in range(16)},
                  observer_ast_inverse=dict(setter_sites=1, validate_sites=1, observer_calls=4,
                                            original_function_AST_restored=True))
    for key in ('sourceio_import_executed', 'importer_attribute_never_patched', 'hidden_placement_verified',
                'all_read_inputs_hash_size_stamp_unchanged', 'original_importer_attribute_unchanged'):
        result[key] = True
    for key in ('historical_saved_B_native_causality_qualified', 'B_opened', 'material_library_appended',
                'exporter_invoked', 'carrier_written', 'image_pixels_read', 'blend_saved', 'native_arrays_published',
                'normal_fidelity_qualified', 'outer_physical_closure_verified_by_worker'):
        result[key] = False
    policy = dict(format='has_hidden_background_desktop_placement_sentinel_1', **{'class': 'STATIC'},
                  requested_size_pixels=[0, 0], disabled=True, noactivate_style=True, toolwindow_style=True,
                  visible_at_creation=False, visible_before_destruction=False,
                  owned_pid_and_thread_verified=True, destroyed_in_finally=True,
                  show_or_activation_calls=False, thread_desktop_switch_calls=False)
    placement = dict(format='has_current_native_hidden_placement_1', policy=policy,
                     worker_verified_hidden_sentinel_closed=True)
    desktop = dict(format='studio_private_desktop_1', desktop='HAS_Test_fake', child_pid=400,
                   exit=0, job_memory_limit_bytes=4096 * 1024 * 1024, job_closed=True, desktop_closed=True,
                   child_desktop_confirmed=True, private_window_seen=True,
                   foreground_child_observed=False, desktop_switch_requested=False)
    return result, placement, desktop


class Admission(unittest.TestCase):
    def callbacks(self, value):
        self.calls = []
        def source():
            self.calls.append('source')
            return copy.deepcopy(value['after'])
        def git():
            self.calls.append('git')
            return dict(head=driver.TESTED, tested_is_ancestor=True,
                        tested_blobs=copy.deepcopy(value['committed']), head_blobs=copy.deepcopy(value['committed']))
        def physical():
            self.calls.append('physical')
            return dict(format='has_current_id_physical_closure_1', owned_processes=0, full_pids_absent=True,
                        observer_retained_waited_reaped=True, observer_exit=0,
                        excluded_exact_pid=os.getpid(), observed_ns=time.time_ns())
        def runtime():
            self.calls.append('runtime')
            return dict(immutable_lock_verified=True, six_runtime_identities_verified=True,
                        sourceio574_exact_including_mtime=True, literal_helpers_verified=True,
                        exporter120_exact_including_mtime=True)
        def launch(proof):
            self.calls.append('launch')
            self.assertEqual(proof['tested_revision'], driver.TESTED)
            return 'FAKE_ONLY'
        return dict(source_reader=source, git_reader=git, physical_reader=physical, runtime_reader=runtime, launch=launch)

    def refuse(self, value, code=None, override=None):
        callbacks = self.callbacks(value)
        callbacks.update(override or {})
        with self.assertRaises(driver.Refusal) as caught:
            driver.admitted_launch(value, **callbacks)
        if code:
            self.assertEqual(str(caught.exception), code)
        self.assertNotIn('launch', self.calls)
        return self.calls

    def test_complete_synthetic_context_reaches_one_fake_launch(self):
        value = context()
        self.assertEqual(driver.admitted_launch(value, **self.callbacks(value)), 'FAKE_ONLY')
        self.assertEqual(self.calls, ['source', 'git', 'physical', 'runtime', 'launch'])

    def test_root_attestation_is_not_inferred_from_zero_processes(self):
        value = context()
        value['root_lane_confirmed'] = False
        self.assertEqual(self.refuse(value, 'EXPLICIT_ROOT_LANE_REQUIRED'), [])

    def test_every_required_full_flag_refuses_before_source_or_native_reads(self):
        keys = ('whole_verifier_pass', 'child_reaped', 'functional_sources_unchanged', 'revision_unchanged',
                'fresh_final_report', 'all_private_jobs_isolated_closed', 'nonzero_jobs_are_expected_cancellations',
                'receipt_provenance_verified')
        for key in keys:
            with self.subTest(key=key):
                for replacement in (False, None, 1, 'true'):
                    value = context()
                    value['completion'][key] = replacement
                    self.assertEqual(self.refuse(value), [])

    def test_failed_old_full_cannot_be_used(self):
        for replacement in (1, 2, True, None):
            value = context()
            value['completion']['exit'] = replacement
            self.assertEqual(self.refuse(value), [])

    def test_old_revision_and_1059_context_refuse(self):
        for key, replacement in (('revision', '0' * 40), ('functional_source_count', 1059),
                                 ('functional_source_count', True)):
            value = context()
            value['completion'][key] = replacement
            self.assertEqual(self.refuse(value), [])

    def test_unreaped_or_alias_full_launch_pids_refuse(self):
        for key, replacement in (('pid', True), ('pid', 0), ('pid', 1002), ('coordinator_pid', None),
                                 ('started_ns', '123'), ('revision', 'f' * 40)):
            value = context()
            value['launch'][key] = replacement
            self.assertEqual(self.refuse(value), [])

    def test_mutated_source_bytes_size_or_nsmtime_refuse(self):
        for key, replacement in (('sha256', 'c' * 64), ('bytes', 2), ('mtime_ns', 123456790), ('git_sha1', 'd' * 40)):
            value = context()
            value['after']['src/fake_0000.gd'][key] = replacement
            self.assertEqual(self.refuse(value), [])

    def test_source_membership_or_untyped_rows_refuse(self):
        for mutation in ('missing', 'extra', 'bool_bytes', 'bad_hash', 'parent_escape'):
            value = context()
            rows = value['before']
            if mutation == 'missing': rows.pop('src/fake_0000.gd')
            elif mutation == 'extra': rows['extra.gd'] = dict(rows['src/fake_0000.gd'])
            elif mutation == 'bool_bytes': rows['src/fake_0000.gd']['bytes'] = True
            elif mutation == 'bad_hash': rows['src/fake_0000.gd']['sha256'] = 'x' * 64
            else: rows['../escape'] = rows.pop('src/fake_0000.gd')
            self.assertEqual(self.refuse(value), [])

    def test_unproven_tested_git_membership_refuses(self):
        value = context()
        value['committed']['src/fake_0000.gd'] = 'd' * 40
        self.assertEqual(self.refuse(value), [])

    def test_full_receipt_flags_cannot_hide_bad_actual_jobs(self):
        for key, replacement in (('job_closed', False), ('desktop_closed', False), ('child_desktop_confirmed', False),
                                 ('foreground_child_observed', True), ('desktop_switch_requested', True), ('exit', True)):
            value = context()
            value['completion']['current_jobs'][0]['value'][key] = replacement
            self.assertEqual(self.refuse(value), [])

    def test_full_archive_duplicates_are_not_counted_as_current_jobs(self):
        value = context()
        value['completion']['current_jobs'].append(copy.deepcopy(value['completion']['current_jobs'][0]))
        value['completion']['unique_current_private_jobs'] = 3
        self.assertEqual(self.refuse(value), [])

    def test_only_one_expected_krita_cancel_is_admissible(self):
        for mutation in ('none', 'normal_failure', 'non_krita', 'duplicate_cancel'):
            value = context()
            jobs = value['completion']['current_jobs']
            if mutation == 'none': jobs[1]['value']['exit'] = 0
            elif mutation == 'normal_failure': jobs[0]['value']['exit'] = 1
            elif mutation == 'non_krita': jobs[1]['path'] = 'output/unrelated/receipt.json'
            else:
                jobs.append(copy.deepcopy(jobs[1]))
                jobs[-1]['value']['desktop'] = 'HAS_Test_cancel_2'
                value['completion']['unique_current_private_jobs'] = 3
            self.assertEqual(self.refuse(value), [])

    def test_current_source_change_stops_before_git_process_or_runtime(self):
        value = context()
        changed = copy.deepcopy(value['after'])
        changed['src/fake_0000.gd']['mtime_ns'] += 1
        self.refuse(value, 'CURRENT_SOURCE_BYTES_OR_NS_STAMPS_DIFFER', {'source_reader': lambda: changed})
        self.assertEqual(self.calls, [])

    def test_unrelated_head_or_changed_committed_bytes_refuse_before_runtime(self):
        for key, replacement in (('tested_is_ancestor', False), ('head', 'bad'), ('head_blobs', {}), ('tested_blobs', {})):
            value = context()
            git = dict(head=driver.TESTED, tested_is_ancestor=True,
                       tested_blobs=value['committed'], head_blobs=value['committed'])
            git[key] = replacement
            self.refuse(value, 'HEAD_LINEAGE_OR_COMMITTED_RAW_BYTES_DIFFER', {'git_reader': lambda: git})
            self.assertEqual(self.calls, ['source'])

    def test_docs_only_descendant_head_is_distinct_but_admitted(self):
        value = context()
        callbacks = self.callbacks(value)
        callbacks['git_reader'] = lambda: dict(head='d' * 40, tested_is_ancestor=True,
                                              tested_blobs=value['committed'], head_blobs=value['committed'])
        self.assertEqual(driver.admitted_launch(value, **callbacks), 'FAKE_ONLY')

    def test_fresh_physical_zero_and_full_pid_absence_are_both_required(self):
        for physical in ({'owned_processes': 1, 'full_pids_absent': True},
                         {'owned_processes': False, 'full_pids_absent': True},
                         {'owned_processes': 0, 'full_pids_absent': False}):
            value = context()
            self.refuse(value, 'FRESH_PHYSICAL_CLOSURE_REQUIRED', {'physical_reader': lambda: physical})
            self.assertEqual(self.calls, ['source', 'git'])

    def test_stale_or_unreaped_physical_observer_refuses(self):
        for key, replacement in (('observed_ns', time.time_ns() - 61 * 10**9),
                                 ('observer_retained_waited_reaped', False), ('observer_exit', True),
                                 ('excluded_exact_pid', os.getpid() + 1)):
            physical = dict(format='has_current_id_physical_closure_1', owned_processes=0, full_pids_absent=True,
                            observer_retained_waited_reaped=True, observer_exit=0,
                            excluded_exact_pid=os.getpid(), observed_ns=time.time_ns())
            physical[key] = replacement
            self.refuse(context(), 'FRESH_PHYSICAL_CLOSURE_REQUIRED', {'physical_reader': lambda: physical})
            self.assertEqual(self.calls, ['source', 'git'])

    def test_every_runtime_qualification_is_required(self):
        for key in ('immutable_lock_verified', 'six_runtime_identities_verified',
                    'sourceio574_exact_including_mtime', 'literal_helpers_verified', 'exporter120_exact_including_mtime'):
            runtime = dict(immutable_lock_verified=True, six_runtime_identities_verified=True,
                           sourceio574_exact_including_mtime=True, literal_helpers_verified=True,
                           exporter120_exact_including_mtime=True)
            runtime[key] = False
            self.refuse(context(), 'EXACT_APPROVED_RUNTIME_REQUIRED', {'runtime_reader': lambda: runtime})
            self.assertEqual(self.calls, ['source', 'git', 'physical'])


class ProcessAndReceipts(unittest.TestCase):
    def process(self, pid, command='', name='python.exe', executable=None):
        return dict(ProcessId=pid, ParentProcessId=10, Name=name, ExecutablePath=executable, CommandLine=command)

    def test_own_exact_pid_is_excluded_but_not_another_primary_worker(self):
        launch = context()['launch']
        own = self.process(42, str(driver.ROOT / 'output/run_probe.py'))
        proof = driver.validate_physical([own], 42, launch)
        self.assertEqual(proof['excluded_exact_pid'], 42)
        with self.assertRaises(driver.Refusal):
            driver.validate_physical([own, self.process(43, own['CommandLine'])], 42, launch)

    def test_full_child_coordinator_and_known_native_pid_must_be_absent(self):
        for pid in (1001, 1002, 7000):
            launch = dict(context()['launch'], extra_absent_pids=[7000])
            with self.assertRaisesRegex(driver.Refusal, 'FULL_CHILD_OR_COORDINATOR_STILL_PRESENT'):
                driver.validate_physical([self.process(pid, None, name='foreign.exe')], 42, launch)

    def test_missing_receipt_orphan_descendants_with_missing_commands_still_block_closure(self):
        child = self.process(3001, None, name='blender.exe')
        child['ParentProcessId'] = 1001
        grandchild = self.process(3002, None, name='python.exe')
        grandchild['ParentProcessId'] = 3001
        with self.assertRaisesRegex(driver.Refusal, 'FULL_CHILD_OR_COORDINATOR_STILL_PRESENT'):
            driver.validate_physical([child, grandchild], 42, context()['launch'])

    def test_owner_studio_and_protected_old_reviews_are_outside_scope(self):
        rows = [self.process(43, r'C:\owner\Studio\studio.exe', name='godot.exe'),
                self.process(44, str(driver.OLD / 'output/review/test.py')),
                self.process(45, str(driver.ROOT.parent / 'has-body-addition-20261120-old/tests/verify.py'))]
        # A root prefix embedded in a different sibling path must not count.
        driver.validate_physical(rows, 42, context()['launch'])

    def test_no_global_tool_name_lock_is_inferred(self):
        rows = [self.process(43, r'C:\other\job.py', name='blender.exe'), self.process(44, None)]
        driver.validate_physical(rows, 42, context()['launch'])

    def test_duplicate_or_untyped_cim_rows_refuse(self):
        for rows in ([self.process(43), self.process(43)], [self.process(True)], [dict(ProcessId=43)]):
            with self.assertRaises(driver.Refusal):
                driver.validate_physical(rows, 42, context()['launch'])

    def test_private_job_and_real_hidden_sentinel_positive(self):
        result, placement, desktop = native_result()
        self.assertEqual(driver.validate_result(result, placement, desktop, 0)['observed_new_points'], 9661)

    def test_job_visibility_resource_limit_and_closure_negatives(self):
        for key, replacement in (('private_window_seen', False), ('child_desktop_confirmed', False), ('job_closed', False),
                                 ('desktop_closed', False), ('foreground_child_observed', True),
                                 ('desktop_switch_requested', True), ('job_memory_limit_bytes', 0), ('exit', True),
                                 ('monitor_error', 'x'), ('cancelled', True)):
            result, placement, desktop = native_result()
            desktop[key] = replacement
            with self.assertRaises(driver.Refusal):
                driver.validate_result(result, placement, desktop, 0)

    def test_fake_or_visible_sentinel_refuses(self):
        for key, replacement in (('class', 'other'), ('requested_size_pixels', [1, 1]), ('disabled', False),
                                 ('noactivate_style', False), ('toolwindow_style', False),
                                 ('visible_at_creation', True), ('visible_before_destruction', True),
                                 ('destroyed_in_finally', False), ('owned_pid_and_thread_verified', False),
                                 ('show_or_activation_calls', True), ('thread_desktop_switch_calls', True)):
            result, placement, desktop = native_result()
            placement['policy'][key] = replacement
            with self.assertRaises(driver.Refusal):
                driver.validate_result(result, placement, desktop, 0)

    def test_worker_status_and_qualification_negatives(self):
        for key, replacement in (('status', 'REFUSED'), ('all_read_inputs_hash_size_stamp_unchanged', False),
                                 ('sourceio_import_executed', False), ('exporter_invoked', True),
                                 ('B_opened', True), ('native_arrays_published', True),
                                 ('normal_fidelity_qualified', True), ('material_files_opened', 1),
                                 ('sourceio_catalogue_files', 573)):
            result, placement, desktop = native_result()
            result[key] = replacement
            with self.assertRaises(driver.Refusal):
                driver.validate_result(result, placement, desktop, 0)

    def test_current_only_observation_and_exact_family_required(self):
        for key, replacement in (('historical_saved_B_native_causality_qualified', True),
                                 ('current_exact_family_ordered_weight_storage_observed', False),
                                 ('fresh_creation_chain_matches_independent_native_candidate', False),
                                 ('observed_new_points', 9660), ('application_adoption_qualified', True)):
            result, placement, desktop = native_result()
            result['observation'][key] = replacement
            with self.assertRaises(driver.Refusal):
                driver.validate_result(result, placement, desktop, 0)

    def test_all_four_phases_and_all_590_reads_required(self):
        for mutation in ('stage', 'groups', 'input_count'):
            result, placement, desktop = native_result()
            if mutation == 'stage': result['observation']['models'][0]['observed_stages'] = 3
            elif mutation == 'groups': result['observation']['models'][0]['groups'] = 68
            else: result['input_identities'].pop('0')
            with self.assertRaises(driver.Refusal):
                driver.validate_result(result, placement, desktop, 0)


class FilesAndOwnedHandles(unittest.TestCase):
    def physical_proof(self):
        return dict(format='has_current_id_physical_closure_1', owned_processes=0, full_pids_absent=True,
                    observer_retained_waited_reaped=True, observer_exit=0,
                    excluded_exact_pid=os.getpid(), observed_ns=time.time_ns())

    def test_failed_launch_record_reaps_only_owned_handle_then_attempts_CIM_without_receipt(self):
        events = []
        class Owned:
            returncode = None
            def poll(self): return self.returncode
            def kill(self): events.append('kill_exact_owned_handle'); self.returncode = -9
            def wait(self, timeout=None): events.append(('wait_owned', timeout)); return self.returncode
        process = Owned()
        primary = driver.Refusal('PRIMARY_RECORD_WRITE_FAILED')
        def writer():
            events.append('write_launch_record')
            raise primary
        with self.assertRaises(driver.Refusal) as caught:
            driver.wait_recorded_owned(process, writer)
        self.assertIs(caught.exception, primary)
        self.assertEqual(events, ['write_launch_record', 'kill_exact_owned_handle', ('wait_owned', 20)])
        def closure():
            events.append('fresh_retained_CIM_after_reap')
            raise driver.Refusal('CIM_FAILED')
        audit = driver.failed_run_audit(
            {'exact_source': lambda: True, 'native_mdl': lambda: True,
             'native_vvd': lambda: False, 'native_vtx': lambda: True},
            primary_error=primary, launcher_reaped=driver.reap_owned_launcher(process),
            worker_receipt_present=False, closure_observer=closure)
        self.assertEqual(events[-1], 'fresh_retained_CIM_after_reap')
        self.assertEqual(audit['primary_error_code'], 'PRIMARY_RECORD_WRITE_FAILED')
        self.assertEqual(audit['status'], 'UNQUALIFIED_FAILED_RUN')
        self.assertTrue(audit['owned_launcher_reaped'])
        self.assertTrue(audit['physical_closure_attempted'])
        self.assertFalse(audit['physical_closure_confirmed'])
        self.assertFalse(audit['worker_receipt_present'])
        self.assertTrue(audit['owned_lock_retained'])
        self.assertFalse(audit['runtime_lane_released'])
        self.assertEqual(audit['checks'], {'exact_source': True, 'native_mdl': True, 'native_vvd': False, 'native_vtx': True})
        self.assertFalse(audit['all_attempted_checks_passed'])
        self.assertFalse(audit['native_fidelity_qualified'])

    def test_native_timeout_remains_failed_even_after_confirmed_closure_and_preservation(self):
        events = []
        class Owned:
            returncode = None
            def poll(self): return self.returncode
            def kill(self): events.append('kill_exact_owned_handle'); self.returncode = -9
            def wait(self, timeout=None):
                events.append(('wait_owned', timeout))
                if timeout == 185: raise subprocess.TimeoutExpired('FAKE_NATIVE_ONLY', timeout)
                return self.returncode
        process = Owned()
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            driver.wait_recorded_owned(process, lambda: events.append('one_record_write'))
        self.assertEqual(events, ['one_record_write', ('wait_owned', 185), 'kill_exact_owned_handle', ('wait_owned', 20)])
        def closure():
            events.append('fresh_CIM')
            return self.physical_proof()
        audit = driver.failed_run_audit({'exact_source': lambda: True, 'native_mdl': lambda: True,
                                          'native_vvd': lambda: True, 'native_vtx': lambda: True},
            primary_error=caught.exception, launcher_reaped=driver.reap_owned_launcher(process),
            worker_receipt_present=False, closure_observer=closure)
        self.assertEqual(events[-1], 'fresh_CIM')
        self.assertTrue(audit['physical_closure_confirmed'])
        self.assertTrue(audit['all_attempted_checks_passed'])
        self.assertEqual(audit['primary_error_type'], 'TimeoutExpired')
        self.assertEqual(audit['status'], 'UNQUALIFIED_FAILED_RUN')
        self.assertFalse(audit['runtime_lane_released'])
        self.assertFalse(audit['application_adoption_qualified'])
        self.assertFalse(audit['native_fidelity_qualified'])

    def test_poll_exit_without_successful_wait_cannot_qualify_reap_or_release_lock(self):
        class Owned:
            def poll(self): return 0
            def kill(self): raise AssertionError('already exited handle must not be killed')
            def wait(self, timeout=None): raise OSError('fake owned wait failure')
        reaped = driver.reap_owned_launcher(Owned())
        self.assertFalse(reaped)
        audit = driver.failed_run_audit({'source': lambda: True},
            primary_error=driver.Refusal('PRIMARY_NATIVE_FAILURE'), launcher_reaped=reaped,
            worker_receipt_present=False, closure_observer=self.physical_proof)
        self.assertTrue(audit['physical_closure_attempted'])
        self.assertFalse(audit['physical_closure_confirmed'])
        self.assertTrue(audit['owned_lock_retained'])
        self.assertFalse(audit['runtime_lane_released'])

    def test_failed_preservation_check_does_not_skip_later_native_checks_or_CIM(self):
        events = []
        def broken():
            events.append('source')
            raise OSError('private fake path deliberately not published')
        def native(): events.append('native'); return True
        def closure(): events.append('CIM'); return self.physical_proof()
        audit = driver.failed_run_audit({'source': broken, 'native': native},
            primary_error=driver.Refusal('PRIMARY_NATIVE_FAILURE'), launcher_reaped=True,
            worker_receipt_present=False, closure_observer=closure)
        self.assertEqual(events, ['source', 'native', 'CIM'])
        self.assertEqual(audit['checks'], {'source': False, 'native': True})
        self.assertEqual(audit['primary_error_code'], 'PRIMARY_NATIVE_FAILURE')
        self.assertFalse(audit['all_attempted_checks_passed'])
        self.assertEqual(audit['status'], 'UNQUALIFIED_FAILED_RUN')

    def test_successfully_waited_exited_handle_is_never_killed_again(self):
        events = []
        class Owned:
            def poll(self): return 1
            def kill(self): raise AssertionError('must not kill an exited retained process')
            def wait(self, timeout=None): events.append(timeout); return 1
        self.assertTrue(driver.reap_owned_launcher(Owned()))
        self.assertEqual(events, [20])

    def test_main_without_root_attestation_stops_before_any_reader_or_process(self):
        args = ['run_probe.py', '--driver-sha256', 'a' * 64, '--worker-sha256', 'b' * 64,
                '--ledger-sha256', 'c' * 64]
        with patch.object(sys, 'argv', args), \
             patch.object(driver, 'read_checked', side_effect=AssertionError('must not read')) as reader, \
             patch.object(driver.subprocess, 'Popen', side_effect=AssertionError('must not launch')) as spawn:
            with self.assertRaisesRegex(driver.Refusal, 'EXPLICIT_ROOT_LANE_REQUIRED'):
                driver.main()
            reader.assert_not_called()
            spawn.assert_not_called()

    def test_main_failed_full_stops_before_runtime_or_source_or_process(self):
        value = context()
        value['completion']['whole_verifier_pass'] = False
        data = {'completion.json': value['completion'], 'launch.json': value['launch'],
                'source-before.json': value['before'], 'source-after.json': value['after'],
                'committed-source-blobs.json': value['committed']}
        raw = b'fake driver source'
        args = ['run_probe.py', '--root-lane-confirmed', '--driver-sha256', driver.sha(raw),
                '--worker-sha256', 'b' * 64, '--ledger-sha256', 'c' * 64]
        with patch.object(sys, 'argv', args), patch.object(driver, 'safe', side_effect=lambda path, **kwargs: Path(path)), \
             patch.object(driver, 'read_checked', return_value=(raw, {}, ())), \
             patch.object(driver, 'json_read', side_effect=lambda path: (data[Path(path).name], {})), \
             patch.object(driver, 'source_snapshot', side_effect=AssertionError('must not read source')) as source, \
             patch.object(driver, 'runtime_check', side_effect=AssertionError('must not read runtime')) as runtime, \
             patch.object(driver.subprocess, 'Popen', side_effect=AssertionError('must not launch')) as spawn:
            with self.assertRaisesRegex(driver.Refusal, 'UNQUALIFIED_FULL_WHOLE_VERIFIER_PASS'):
                driver.main()
            source.assert_not_called()
            runtime.assert_not_called()
            spawn.assert_not_called()

    def test_duplicate_and_nonfinite_json_refused(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaises(driver.Refusal):
                driver.strict_json(raw)

    def test_relative_path_escapes_and_aliases_refused(self):
        for name in ('../x', '/x', 'a/../x', 'a\\x', 'C:x', 'a//x', './x', ''):
            with self.assertRaises(driver.Refusal):
                driver.relative(name)

    def test_checked_empty_and_nonempty_files_preserve_hash_size_nsmtime(self):
        with tempfile.TemporaryDirectory() as directory:
            for raw in (b'', b'known scalar source'):
                path = Path(directory) / ('empty' if not raw else 'data')
                path.write_bytes(raw)
                actual, row, before = driver.read_checked(path, (len(raw), driver.sha(raw)))
                self.assertEqual(actual, raw)
                self.assertEqual(row['bytes'], len(raw))
                self.assertEqual(row['mtime_ns'], path.stat().st_mtime_ns)
                self.assertEqual(before, driver.stamp(path.stat()))

    def test_wrong_literal_pin_and_read_budget_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data'
            path.write_bytes(b'abcd')
            with self.assertRaises(driver.Refusal): driver.read_checked(path, (4, '0' * 64))
            with self.assertRaises(driver.Refusal): driver.read_checked(path, limit=3)

    def test_hardlink_is_refused_without_reading_original(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'original'
            alias = Path(directory) / 'alias'
            original.write_bytes(b'private')
            os.link(original, alias)
            with self.assertRaisesRegex(driver.Refusal, 'HARDLINK_PATH'):
                driver.read_checked(alias)

    def test_reparse_attribute_is_refused(self):
        class Info:
            st_mode = 0o100644
            st_file_attributes = 0x400
            st_nlink = 1
        with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'is_symlink', return_value=False), \
             patch.object(Path, 'lstat', return_value=Info()):
            with self.assertRaisesRegex(driver.Refusal, 'LINK_OR_REPARSE_PATH'):
                driver.safe(Path(tempfile.gettempdir()) / 'fake')

    def test_complete_sdk_catalogue_does_not_hide_unexpected_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'source.py').write_bytes(b'source')
            (folder / '__pycache__').mkdir()
            (folder / '__pycache__/unexpected.pyc').write_bytes(b'cache')
            self.assertEqual(set(driver.complete_catalogue(folder)), {'source.py', '__pycache__/unexpected.pyc'})
            self.assertEqual(set(driver.complete_catalogue(folder, exporter=True)), {'source.py'})

    def test_unlisted_sdk_file_is_refused_before_any_contents_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'unexpected-private-file').write_bytes(b'must not read')
            with patch.object(driver, 'read_checked', side_effect=AssertionError('must not read')) as reader:
                with self.assertRaisesRegex(driver.Refusal, 'BEFORE_READ_CATALOGUE_MEMBERSHIP_DIFFERS'):
                    driver.complete_catalogue(folder, expected={})
                reader.assert_not_called()

    def test_wrong_pinned_size_is_refused_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'known'
            path.write_bytes(b'not the pinned length')
            with patch.object(Path, 'open', side_effect=AssertionError('must not open')) as opened:
                with self.assertRaisesRegex(driver.Refusal, 'BEFORE_READ_LITERAL_PIN_OR_SIZE_DIFFERS'):
                    driver.read_checked(path, (1, 'a' * 64))
                opened.assert_not_called()

    def test_runtime_lock_path_is_refused_before_any_file_read(self):
        with patch.object(driver, 'read_checked', side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(driver.Refusal, 'IMMUTABLE_APPROVED_LOCK_PATH_DIFFERS'):
                driver.runtime_check(Path(tempfile.gettempdir()) / 'untrusted.json')

    def test_fresh_output_refuses_overwrite_or_outside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'output').mkdir()
            existing = root / 'output/existing.json'
            existing.write_bytes(b'original')
            with patch.object(driver, 'ROOT', root):
                with self.assertRaises(driver.Refusal): driver.write_new(existing, {'x': 1})
                with self.assertRaises(driver.Refusal): driver.write_new(root / 'outside.json', {'x': 1})
                row = driver.write_new(root / 'output/fresh.json', {'x': 1})
                self.assertEqual(row['sha256'], driver.sha((root / 'output/fresh.json').read_bytes()))
            self.assertEqual(existing.read_bytes(), b'original')

    def test_retained_readonly_observer_waits_and_reaps(self):
        class Fake:
            returncode = 0
            def communicate(self, timeout=None):
                self.waited = timeout
                return b'[]', b''
            def poll(self): return 0
        process = Fake()
        with patch.object(driver.subprocess, 'Popen', return_value=process) as spawn, \
             patch.object(driver.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
            self.assertEqual(driver.retained_output(['FAKE_READ_ONLY'], timeout=7), b'[]')
            self.assertEqual(process.waited, 7)
            self.assertEqual(spawn.call_args.kwargs['creationflags'], 0x08000000)
            self.assertEqual(spawn.call_args.kwargs['stdin'], subprocess.DEVNULL)

    def test_retained_observer_timeout_kills_only_its_exact_owned_handle_then_reaps(self):
        class Fake:
            returncode = None
            calls = []
            def communicate(self, timeout=None):
                self.calls.append(('communicate', timeout))
                if timeout is not None: raise subprocess.TimeoutExpired('FAKE_ONLY', timeout)
                self.returncode = -1
                return b'', b''
            def poll(self): return self.returncode
            def kill(self): self.calls.append(('kill_exact_owned_handle', None))
        process = Fake()
        with patch.object(driver.subprocess, 'Popen', return_value=process), \
             patch.object(driver.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
            with self.assertRaises(subprocess.TimeoutExpired):
                driver.retained_output(['FAKE_READ_ONLY'], timeout=1)
        self.assertEqual(process.calls, [('communicate', 1), ('kill_exact_owned_handle', None), ('communicate', None)])

    def test_failed_observer_has_no_visible_or_second_launch_fallback(self):
        class Fake:
            returncode = 1
            def communicate(self, timeout=None): return b'', b'private error'
            def poll(self): return 1
        with patch.object(driver.subprocess, 'Popen', return_value=Fake()) as spawn, \
             patch.object(driver.subprocess, 'CREATE_NO_WINDOW', 0x08000000, create=True):
            with self.assertRaises(driver.Refusal): driver.retained_output(['FAKE_READ_ONLY'])
            self.assertEqual(spawn.call_count, 1)


if __name__ == '__main__':
    unittest.main()
