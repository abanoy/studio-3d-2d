"""Synthetic stdlib-only coordinator tests. No Blender, CIM, Git or real fixtures.

All launch/read callbacks are local fakes. The retained77 cases adapt only the explicit605/export protocol. New carrier
contracts are added below. This author executed none. These tests qualify admission logic
and retained handle behavior only; they cannot qualify native IDs or fidelity.
"""
from pathlib import Path
import copy
import hashlib
import json
from contextlib import ExitStack
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('current_id_root_driver_under_test', Path(__file__).with_name('run_carrier.py'))
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


def native_path_report():
    value=dict(format='has_finite_native_preloaded_material_path_witness_1',status='RETURNED_BINDING_OBSERVED',
        selected_material_records=4,metadata_rows_observed=4,genuine_material_rows=4,full_path_present=4,full_path_missing=0,
        full_path_string=4,full_path_nonstring=0,selected_domain_memberships=4,candidate_membership_matches=4,
        candidate_membership_missing=0,candidate_membership_ambiguous=0,global_lookup_matches=4,global_lookup_conflicts=0,
        native_material_records=4,cache_materials_observed=4,source_B_refs_observed=4,provider_true=4,provider_false=4,
        provider_queries=8,native_candidates=8,domain_material_records=5,check_calls=80,complete_check_calls=64,
        phase_observations=8,returned_observations=1,candidate_order_sha256='1'*64,native_path_provenance_sha256='2'*64,
        current_reference_witness_sha256='3'*64,resolved_cache_witness_sha256='4'*64)
    for key in ('preflight_admitted','resolver_bound','resolution_complete','returned_binding_observed',
                'no_metadata_writes','no_material_file_IO','no_file_existence_claim'): value[key]=True
    for key in ('native_or_historical_point_identity_qualified','resource_or_normal_fidelity_qualified',
                'exporter_invoked','application_adoption_qualified'): value[key]=False
    return value


def binding_report():
    return dict(format='has_fresh_sourceio_resolved_material_slot_skin_observation_1',
        native_path_witness=native_path_report(),explicit_read_only_preloaded_path_profile=True,
        external_material_file_existence_qualified=False,B_material_properties_written=False,
        native_material_records=4, native_skin_families=1, native_skin_references=4,
        native_body_parts=2, native_model_records=3, native_mesh_records=4,
        observed_models=2, observed_faces=14234, used_raw_mesh_material_count=4,
        sourceio_raw_matches_candidate_default_skin_on_used_meshes=True,
        candidate_default_skin_row_sha256='a' * 64,
        exact_family_raw_material_placeholder_slot_face_binding_observed=True,
        exact_family_skin_property_reference_or_name_storage_observed=True,
        models=[dict(faces=2790, slots=1, observed_stages=4, skin_storage='MATERIAL_ID', raw_face_material_order_sha256='b' * 64),
                dict(faces=11444, slots=3, observed_stages=4, skin_storage='MATERIAL_ID', raw_face_material_order_sha256='c' * 64)],
        resolved_native_default_skin_equivalence_qualified=False, native_skin_switching_qualified=False,
        material_files_or_B_opened=False, B_dependency_closure_qualified=False,
        native_normal_fidelity_qualified=False, carrier_or_exporter_binding_qualified=False,
        non_normal_semantic_equivalence_qualified=False, application_adoption_qualified=False)


def add_owned_B_report(result):
    summary=dict(format='has_material_only_library_inspection_summary_2',
        status='INSPECTED_MATERIAL_ONLY_OWNED_LIBRARY_AND_PACKED_PNG_HEADERS_2',append_requested=True,
        append_completed=True,surviving_originals_unchanged=True,requested_materials=4,inspected_material_graphs=4,
        available_materials=5,unrequested_catalogue_materials=1,reached_images=2,shared_image_references=2,
        packed_bytes_copied=100,prospective_rgba_f32_bytes=1000,before_id_count=1,after_id_count=8,
        retained_owned_source_libraries=1,owned_source_library_validation_attempted=True,
        retained_owned_source_library_verified=True,retained_library_filepath_sha256=driver.owned_library_path_digest(r'C:\owned\material-source.blend'),
        added_id_counts=dict(materials=4,images=2,libraries=1),material_names_sha256='a'*64,
        graph_metadata_sha256='b'*64,packed_observation_sha256='c'*64)
    for key in ('material_binding_qualified','resource_equivalence_qualified','B_dependency_closure_qualified',
                'non_normal_semantic_equivalence_qualified','native_or_historical_point_identity_qualified','exporter_qualified',
                'normal_fidelity_qualified','application_adoption_qualified','transient_ID_or_C_level_read_absence_qualified',
                'image_buffer_getters_used','blend_saved','exporter_invoked','external_filepath_retrieval_attempted'): summary[key]=False
    result.update(native_material_path_witness=native_path_report(),
        preloaded_resolver_runtime_attestation=dict(format='has_preloaded_material_resolver_runtime_attestation_1',
            complete_module_code_equal=True,actual_globals_and_aliases_equal=True,source_catalogue_helpers=2,
            genuine_functions=3,original_importer_attribute_unchanged=True,no_resolver_replacement=True),
        readonly_preloaded_material_adaptation=dict(format='has_readonly_preloaded_material_adaptation_1',
            no_metadata_writes=True,no_material_renames=True,no_material_swaps=True,native_imports_before_append=0),
        material_library_appended=True,material_resources_loaded=True,owned_B_materials_precede_native_import=True,
        owned_B_resources_unchanged_after_native_import=True,all_four_source_materials_reuse_admitted_B_refs=True,
        owned_B_enumeration=dict(format='has_empty_library_enumeration_summary_2',actual_id_census_unchanged=True,
            all_destination_requests_empty=True,source_materials=5,before_id_count=1,after_id_count=1,
            id_collections=4,source_id_types=4,destination_request_types=4,source_catalogue_name_count=7,
            source_material_names_sha256='d'*64,source_catalogue_sha256='e'*64),owned_B_inspection=summary,
        ordinary_importer_material_reuse_preflight=dict(format='has_owned_B_ordinary_material_lookup_preflight_1',
            materials=4,exact_full_path_rule=True,unique_actual_refs=True,material_names_sha256='a'*64,
            material_renames=0,material_swaps=0,native_imports_before_append=0))


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
    result = dict(format='has_fresh_source_native_carrier_export_probe_1',
                  status='MATCHED_FRESH_NATIVE_IDS_OWNED_MATERIALS_AND_CARRIER_EXPORT', observation=observation,
                  sourceio_material_files_opened=0, sourceio_image_datablocks_created=0, sourceio_catalogue_files=574,
                  input_identities={str(index): dict(bytes=1, sha256='a' * 64) for index in range(31)},
                  material_binding=binding_report(), original_current_ID_RNA_controls_retained=True,
                  inherited_authenticated_reads=590, exact_authenticated_reads=605,
                  resolved_native_default_skin_equivalence_qualified=False,
                  material_resources_loaded=True, B_dependency_closure_qualified=False,
                  observer_ast_inverse=dict(setter_sites=1, validate_sites=1, observer_calls=4,
                                            original_function_AST_restored=True))
    for key in ('sourceio_import_executed', 'importer_attribute_never_patched', 'hidden_placement_verified',
                'all_read_inputs_hash_size_stamp_unchanged', 'original_importer_attribute_unchanged'):
        result[key] = True
    for key in ('historical_saved_B_native_causality_qualified', 'original_B_scene_opened',
                'exporter_invoked', 'carrier_written', 'image_pixels_read', 'blend_saved', 'native_arrays_published',
                'normal_fidelity_qualified', 'outer_physical_closure_verified_by_worker'):
        result[key] = False
    add_owned_B_report(result)
    # Actual operator/owned output are separate from downstream fidelity claims.
    result.update(exporter_invoked=True, carrier_written=True,
        image_buffer_getters_used=True, host_image_pixels_getter_used=False,
        C_encoded_pixel_decode_may_have_occurred=True, C_external_access_absence_proven=False)
    add_carrier_report(result)
    policy = dict(format='has_hidden_background_desktop_placement_sentinel_1', **{'class': 'STATIC'},
                  requested_size_pixels=[0, 0], disabled=True, noactivate_style=True, toolwindow_style=True,
                  visible_at_creation=False, visible_before_destruction=False,
                  owned_pid_and_thread_verified=True, destroyed_in_finally=True,
                  show_or_activation_calls=False, thread_desktop_switch_calls=False)
    placement = dict(format='has_carrier_export_hidden_placement_1', policy=policy,
                     worker_verified_hidden_sentinel_closed=True)
    desktop = dict(format='studio_private_desktop_1', desktop='HAS_Test_fake', child_pid=400,
                   exit=0, job_memory_limit_bytes=4096 * 1024 * 1024, job_closed=True, desktop_closed=True,
                   child_desktop_confirmed=True, private_window_seen=True,
                   foreground_child_observed=False, desktop_switch_requested=False)
    return result, placement, desktop



def add_carrier_report(result):
    # Pure synthetic cross-bound summaries, never real output/provenance evidence.
    digest = '5' * 64
    result.update(operator_preflight_observed=True, scene_or_registration_restoration_failed=False,
        carrier_output_present_unqualified=True, carrier_output_bytes_unqualified=28,
        carrier_output_sha256_unqualified=digest,
        carrier_export=dict(operator_invocations=1, own_carrier_attributes=2, ordinary_operator_finished=True,
            carrier_glb_bytes=28, carrier_glb_sha256=digest, private_relation_sha256='6' * 64,
            export_observation=dict(format='has_source_export_hook_proposal_1',
                source_normal_threshold_unchanged=2e-5, source_normal_error_measured=False,
                actual_export_binding=dict(passed=True, meshes=2, primitives=4, source_ids=9661,
                                           carrier_glb_sha256=digest),
                resources=dict(format='has_narrow_shared_actual_resource_reference_observation_3',
                               materials=4, source_images=2, images=2, image_bindings=4, textures=4))),
        bounded_image_buffer_readiness=dict(format='has_bounded_packed_png_buffer_readiness_1',
            status='BOUNDED_PACKED_PNG_BUFFERS_READY_1', complete_set_admitted_before_buffer_getters=True,
            packed_memory_branch_preconditions_validated=True, nonbuffer_metadata_and_packed_refs_unchanged=True,
            packed_hashes_rechecked=True, images_verified_ready=2))


def qualified_creation_report():
    # Earlier actual v3 record, separate from this new carrier job's result.
    value = dict(format='has_root_fresh_source_owned_B_resolved_material_creation_run_1',
        status='CURRENT_IDS_RNA_WITH_OWNED_B_RESOLVED_MATERIALS_MATCHED',
        tested_full_revision=driver.TESTED, current_source_head='5f6a0efba5205f2b1ad4dda73271d968993db4c7',
        functional_source_count=1061, exact_authenticated_reads=596,
        models=2, points=9661, corners=42702, sourceio_files=574,
        material_binding=binding_report(), native_material_path_witness=native_path_report(),
        fresh_physical_after=dict(owned_processes=0, observer_retained_waited_reaped=True,
                                 full_pids_absent=True, observer_exit=0))
    for key in ('whole_full_pass_required', 'private_job_closed', 'launcher_reaped', 'hidden_placement_verified',
                'original_and_staged_hash_bytes_nsmtime_unchanged', 'source_and_head_unchanged',
                'material_library_appended', 'material_resources_loaded', 'all_four_source_materials_reuse_admitted_B_refs'):
        value[key] = True
    for key in ('historical_saved_B_native_causality_qualified', 'normal_fidelity_qualified', 'exporter_qualified',
                'carrier_qualified', 'non_normal_semantic_equivalence_qualified', 'application_adoption_qualified',
                'original_B_scene_opened', 'exporter_invoked', 'blend_saved', 'native_arrays_published'):
        value[key] = False
    return value


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
            return dict(format='has_source_material_binding_physical_closure_1', owned_processes=0, full_pids_absent=True,
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
            physical = dict(format='has_source_material_binding_physical_closure_1', owned_processes=0, full_pids_absent=True,
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
    def test_new_scope_rejects_old_current_id_only_success(self):
        result, placement, desktop = native_result()
        result.pop('material_binding')
        with self.assertRaisesRegex(driver.Refusal, 'RAW_MATERIAL_BINDING_REPORT_REQUIRED'):
            driver.validate_result(result, placement, desktop, 0)

    def test_material_binding_requires_whole_faces_and_four_stages(self):
        for field, value in (('observed_faces', 14233), ('native_mesh_records', 2), ('native_model_records', 2)):
            report = binding_report()
            report[field] = value
            with self.assertRaises(driver.Refusal): driver.validate_material_report(report)
        report = binding_report()
        report['models'][0]['observed_stages'] = 3
        with self.assertRaises(driver.Refusal): driver.validate_material_report(report)

    def test_material_report_keeps_native_semantics_resources_and_export_unqualified(self):
        for field in ('resolved_native_default_skin_equivalence_qualified', 'native_skin_switching_qualified',
                      'material_files_or_B_opened', 'B_dependency_closure_qualified', 'native_normal_fidelity_qualified',
                      'carrier_or_exporter_binding_qualified', 'non_normal_semantic_equivalence_qualified', 'application_adoption_qualified'):
            report = binding_report()
            report[field] = True
            with self.assertRaises(driver.Refusal): driver.validate_material_report(report)

    def test_native_default_agreement_and_both_actual_skin_storage_branches(self):
        for branch in ('MATERIAL_ID', 'STRING'):
            report = binding_report()
            for row in report['models']: row['skin_storage'] = branch
            driver.validate_material_report(report)
        report = binding_report()
        report['sourceio_raw_matches_candidate_default_skin_on_used_meshes'] = False
        with self.assertRaises(driver.Refusal): driver.validate_material_report(report)

    def test_extra_two_authenticated_sources_cannot_replace_inherited_590(self):
        result, placement, desktop = native_result()
        result['inherited_authenticated_reads'] = 596
        with self.assertRaises(driver.Refusal): driver.validate_result(result, placement, desktop, 0)
    def process(self, pid, command='', name='python.exe', executable=None):
        return dict(ProcessId=pid, ParentProcessId=10, Name=name, ExecutablePath=executable, CommandLine=command)

    def test_own_exact_pid_is_excluded_but_not_another_primary_worker(self):
        launch = context()['launch']
        own = self.process(42, str(driver.ROOT / 'output/run_carrier.py'))
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
                                 ('sourceio_import_executed', False), ('exporter_invoked', False),
                                 ('original_B_scene_opened', True), ('native_arrays_published', True),
                                 ('normal_fidelity_qualified', True), ('sourceio_material_files_opened', 1),
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

    def test_all_four_phases_and_all_605_reads_required(self):
        for mutation in ('stage', 'groups', 'input_count'):
            result, placement, desktop = native_result()
            if mutation == 'stage': result['observation']['models'][0]['observed_stages'] = 3
            elif mutation == 'groups': result['observation']['models'][0]['groups'] = 68
            else: result['input_identities'].pop('0')
            with self.assertRaises(driver.Refusal):
                driver.validate_result(result, placement, desktop, 0)


class FilesAndOwnedHandles(unittest.TestCase):
    def synthetic_pinned_open(self, *, opened_changes=None, final_changes=None, wrong_hash=False, expect=None):
        """Exercise the real reader against independent fake stat/open records."""
        raw = b'known pinned scalar runtime bytes'
        fields = dict(st_dev=11, st_ino=22, st_size=len(raw), st_mtime_ns=333333333,
                      st_nlink=1, st_mode=0o100644, st_file_attributes=0x20)
        before = SimpleNamespace(**dict(fields, st_file_attributes=0x40020))
        opened = SimpleNamespace(**dict(fields, **(opened_changes or {})))
        final_open = SimpleNamespace(**dict(fields, **(final_changes or {})))
        final_path = SimpleNamespace(**dict(fields, **(final_changes or {})))
        class Stream:
            reads = 0
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def fileno(self): return 987654
            def read(self, count):
                self.reads += 1
                return raw[:count]
        stream = Stream()
        pin = (len(raw), '0' * 64 if wrong_hash else driver.sha(raw))
        with patch.object(driver, 'safe', side_effect=lambda value: Path(value)), \
             patch.object(Path, 'lstat', side_effect=[before, final_path]), \
             patch.object(Path, 'open', return_value=stream), \
             patch.object(driver.os, 'fstat', side_effect=[opened, final_open]):
            if expect is not None:
                with self.assertRaisesRegex(driver.Refusal, '^' + expect + '$'):
                    driver.read_checked(Path('synthetic-pinned-runtime.exe'), pin)
                return stream.reads
            actual, row, identity = driver.read_checked(Path('synthetic-pinned-runtime.exe'), pin)
        self.assertEqual(actual, raw)
        self.assertEqual(row, dict(bytes=len(raw), mtime_ns=fields['st_mtime_ns'], sha256=driver.sha(raw)))
        self.assertEqual(identity, driver.stamp(final_path))
        return stream.reads

    def test_recall_on_open_hint_transition_accepts_exact_pinned_stable_identity(self):
        self.assertEqual(driver.FILE_ATTRIBUTE_RECALL_ON_OPEN, 0x40000)
        self.assertEqual(self.synthetic_pinned_open(), 1)

    def test_recall_transition_cannot_hide_changed_identity_or_nsmtime(self):
        changes = (('st_dev', 12), ('st_ino', 23), ('st_size', 99),
                   ('st_mtime_ns', 333333334), ('st_nlink', 2))
        for field, value in changes:
            with self.subTest(field=field):
                self.assertEqual(self.synthetic_pinned_open(opened_changes={field: value},
                    expect='FILE_CHANGED_BEFORE_READ'), 0)
                self.assertEqual(self.synthetic_pinned_open(final_changes={field: value},
                    expect='READ_CHANGED_FILE'), 1)

    def test_recall_mask_preserves_reparse_and_every_other_tested_attribute(self):
        # Include RECALL_ON_DATA_ACCESS as well as reparse/readonly/compressed/
        # offline: none shares the one explicitly normalized enumeration bit.
        for attribute in (0x400, 0x1, 0x800, 0x1000, 0x400000):
            with self.subTest(attribute=attribute):
                self.assertEqual(self.synthetic_pinned_open(opened_changes={'st_file_attributes': 0x20 | attribute},
                    expect='FILE_CHANGED_BEFORE_READ'), 0)

    def test_recall_transition_still_requires_exact_literal_content_hash(self):
        self.assertEqual(self.synthetic_pinned_open(wrong_hash=True, expect='LITERAL_PIN_DIFFERS'), 1)

    def test_raw_attribute_diagnostics_remain_unmasked(self):
        fields = dict(st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4, st_nlink=1)
        before = SimpleNamespace(**fields, st_file_attributes=0x40020)
        opened = SimpleNamespace(**fields, st_file_attributes=0x20)
        self.assertEqual(driver.raw_stamp(before)[-1], 0x40020)
        self.assertEqual(driver.raw_stamp(opened)[-1], 0x20)
        self.assertEqual(driver.stamp(before), driver.stamp(opened))

    def test_observer_uses_only_exact_approved_hash_pinned_codex_pwsh(self):
        expected = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
        self.assertEqual(driver.PWSH, expected)
        self.assertEqual(driver.PWSH_PIN, (301360, '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'))
        events = []
        def reader(path, pin):
            events.append('pin_before_observer')
            self.assertEqual(path, expected)
            self.assertEqual(pin, driver.PWSH_PIN)
            return b'', {}, ()
        def observer(args):
            events.append('one_hidden_retained_observer')
            self.assertEqual(args[0], str(expected))
            self.assertEqual(args[1:5], ['-NoLogo', '-NoProfile', '-NonInteractive', '-Command'])
            self.assertIn('Get-CimInstance Win32_Process', args[5])
            return b'[]'
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(driver, 'read_checked', side_effect=reader), \
             patch.object(driver, 'retained_output', side_effect=observer), \
             patch.object(driver.subprocess, 'Popen', side_effect=AssertionError('no actual process')) as spawn:
            proof = driver.observe_physical(Path(directory), context()['launch'], 'FAKE_ONLY')
            self.assertTrue(proof['observer_retained_waited_reaped'])
            self.assertEqual(proof['owned_processes'], 0)
            spawn.assert_not_called()
        self.assertEqual(events, ['pin_before_observer', 'one_hidden_retained_observer'])

    def test_wrong_pwsh_literal_hash_refuses_before_observer_or_Popen(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'fake_pwsh.exe'
            executable.write_bytes(b'x' * driver.PWSH_PIN[0])
            with patch.object(driver, 'PWSH', executable), \
                 patch.object(driver, 'retained_output', side_effect=AssertionError('must not observe')) as observer, \
                 patch.object(driver.subprocess, 'Popen', side_effect=AssertionError('must not launch')) as spawn:
                with self.assertRaisesRegex(driver.Refusal, 'LITERAL_PIN_DIFFERS'):
                    driver.observe_physical(Path(directory), context()['launch'], 'MUST_NOT_EXIST')
                observer.assert_not_called()
                spawn.assert_not_called()
                self.assertFalse((Path(directory) / 'PRIVATE_CIM_MUST_NOT_EXIST.json').exists())

    def physical_proof(self):
        return dict(format='has_source_material_binding_physical_closure_1', owned_processes=0, full_pids_absent=True,
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
        args = ['run_carrier.py', '--driver-sha256', 'a' * 64, '--worker-sha256', 'b' * 64,
                '--ledger-sha256', 'c' * 64, '--binding-sha256', driver.BINDING_PIN[1],
                '--qualified-creation', 'FAKE_ONLY_CREATION.json', '--qualified-creation-sha256', 'd' * 64]
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
        args = ['run_carrier.py', '--root-lane-confirmed', '--driver-sha256', driver.sha(raw),
                '--worker-sha256', 'b' * 64, '--ledger-sha256', 'c' * 64, '--binding-sha256', driver.BINDING_PIN[1],
                '--qualified-creation', 'FAKE_ONLY_CREATION.json', '--qualified-creation-sha256', 'd' * 64]
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


class CombinedMaterialReportTests(unittest.TestCase):
    def test_new_written_worker_receipt_retains_exact_hash_and_stamp_for_failure_audit(self):
        row = dict(path='FAKE_ONLY', bytes=3, sha256='a' * 64)
        identity = dict(bytes=3, sha256='a' * 64, mtime_ns=123)
        checks = {}; stamp = ('volume', 'inode', 123)
        with patch.object(driver, 'read_checked', return_value=(b'abc', identity, stamp)):
            self.assertIs(driver.remember_written_file(checks, 'worker_input_root_request', row), row)
            self.assertTrue(checks['worker_input_root_request']())
        with patch.object(driver, 'read_checked', return_value=(b'abc', identity, ('volume', 'inode', 124))):
            self.assertFalse(checks['worker_input_root_request']())

    def test_existing_stage_is_not_owned_or_written_on_timestamp_collision(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'output').mkdir()
            stage = root / 'output/source-material-carrier-run-123'
            stage.mkdir(); marker = stage / 'foreign.txt'; marker.write_bytes(b'foreign-owner')
            with patch.object(driver, 'ROOT', root), patch.object(driver.time, 'time_ns', return_value=123):
                with self.assertRaisesRegex(driver.Refusal, 'FRESH_STAGE_BOUNDARY'): driver.new_stage()
            self.assertEqual(tuple(item.name for item in stage.iterdir()), ('foreign.txt',))
            self.assertEqual(marker.read_bytes(), b'foreign-owner')

    def test_current_carrier_scope_keeps_material_inspection_and_fidelity_claims_distinct(self):
        result, placement, desktop = native_result()
        driver.validate_result(result, placement, desktop, 0)
        summary = driver.validate_owned_B_report(result, expected_owned_path=r'C:\owned\material-source.blend')
        self.assertEqual((summary['reached_images'], summary['shared_image_references']), (2, 2))
        self.assertTrue(result['exporter_invoked'])
        self.assertFalse(result['normal_fidelity_qualified'])

    def test_old_placeholder_only_report_cannot_enter_new_namespace(self):
        result, placement, desktop = native_result()
        for key in ('material_library_appended', 'material_resources_loaded', 'all_four_source_materials_reuse_admitted_B_refs'):
            changed = copy.deepcopy(result); changed[key] = False
            with self.assertRaises(driver.Refusal): driver.validate_result(changed, placement, desktop, 0)
        changed = copy.deepcopy(result); changed['format'] = 'has_fresh_source_material_binding_probe_1'
        with self.assertRaises(driver.Refusal): driver.validate_result(changed, placement, desktop, 0)

    def test_owned_library_digest_is_bound_to_actual_new_stage_not_an_old_success_token(self):
        result, _placement, _desktop = native_result()
        with self.assertRaisesRegex(driver.Refusal, 'COMBINED_OWNED_LIBRARY_PATH_DIFFERS'):
            driver.validate_owned_B_report(result, expected_owned_path=r'C:\other-job\material-source.blend')
        result['owned_B_inspection']['retained_library_filepath_sha256'] = driver.owned_library_path_digest(r'C:\other-job\material-source.blend')
        driver.validate_owned_B_report(result, expected_owned_path=r'c:/OTHER-JOB/material-source.blend')

    def test_bool_counts_extra_geometry_or_unpreserved_originals_cannot_be_accepted(self):
        for mutate in (
            lambda value: value['owned_B_inspection'].__setitem__('requested_materials', True),
            lambda value: value['owned_B_inspection']['added_id_counts'].__setitem__('objects', 1),
            lambda value: value['owned_B_inspection'].__setitem__('surviving_originals_unchanged', False),
            lambda value: value['owned_B_enumeration'].__setitem__('after_id_count', 2),
            lambda value: value['owned_B_inspection'].__setitem__('before_id_count', 2),
        ):
            result, _placement, _desktop = native_result(); mutate(result)
            with self.assertRaises(driver.Refusal): driver.validate_owned_B_report(result)

    def test_no_rename_swap_late_append_or_unearned_downstream_qualification(self):
        for key in ('no_material_renames', 'no_material_swaps', 'native_imports_before_append'):
            result, _placement, _desktop = native_result()
            result['readonly_preloaded_material_adaptation'][key] = 1 if key == 'native_imports_before_append' else False
            with self.assertRaises(driver.Refusal): driver.validate_owned_B_report(result)
        for key in ('exporter_qualified', 'normal_fidelity_qualified', 'transient_ID_or_C_level_read_absence_qualified'):
            result, _placement, _desktop = native_result(); result['owned_B_inspection'][key] = True
            with self.assertRaises(driver.Refusal): driver.validate_owned_B_report(result)

    def test_all_thirty_one_nonSDK_rows_are_required(self):
        result, placement, desktop = native_result()
        self.assertEqual(len(result['input_identities']), 31)
        result['input_identities'].pop(next(iter(result['input_identities'])))
        with self.assertRaisesRegex(driver.Refusal, 'EXACT_605_WORKER_INPUT_READS'):
            driver.validate_result(result, placement, desktop, 0)

    def test_incremental_original_or_staged_check_remains_registered_on_later_failure(self):
        checks = {}; row = {'bytes': 3, 'sha256': 'a' * 64}; stamp = ('owned', 123)
        driver.register_file_check(checks, 'owned_B', Path('FAKE_ONLY'), (3, 'a' * 64), row, stamp)
        with patch.object(driver, 'read_checked', return_value=(b'abc', row, stamp)):
            self.assertTrue(checks['owned_B']())
        with patch.object(driver, 'read_checked', side_effect=driver.Refusal('CHANGED_COPY')):
            audit = driver.failed_run_audit(checks, primary_error=driver.Refusal('PRIMARY_LATER'), launcher_reaped=False,
                worker_receipt_present=False, native_launch_attempted=False,
                closure_observer=lambda: dict(format='has_source_material_binding_physical_closure_1',
                    owned_processes=0, full_pids_absent=True, observer_retained_waited_reaped=True,
                    observer_exit=0, excluded_exact_pid=os.getpid(), observed_ns=time.time_ns()))
        self.assertFalse(audit['checks']['owned_B'])
        self.assertEqual(audit['primary_error_code'], 'PRIMARY_LATER')
        self.assertFalse(audit['native_launch_attempted'])
        self.assertFalse(audit['owned_launcher_reaped'])
        self.assertTrue(audit['physical_closure_confirmed'])
        self.assertFalse(audit['runtime_lane_released'])
        self.assertEqual(audit['status'], 'UNQUALIFIED_FAILED_RUN')


class ResolvedPathReceiptTests(unittest.TestCase):
    def test_complete_native_candidate_profile_accepts_later_readonly_check_counters(self):
        result,placement,desktop=native_result()
        result['native_material_path_witness']['check_calls'] += 10
        result['native_material_path_witness']['complete_check_calls'] += 10
        driver.validate_result(result,placement,desktop,0)

    def test_path_provenance_mismatch_between_binding_and_outer_report_refuses(self):
        for key in ('candidate_order_sha256','native_path_provenance_sha256',
                    'current_reference_witness_sha256','resolved_cache_witness_sha256'):
            result,placement,desktop=native_result()
            result['native_material_path_witness'][key]='f'*64
            with self.assertRaisesRegex(driver.Refusal,'MATERIAL_PATH_WITNESS_REPORT_BINDING_DIFFERS'):
                driver.validate_result(result,placement,desktop,0)

    def test_missing_or_nonstring_path_counts_cannot_be_success(self):
        for key,value in (('full_path_present',3),('full_path_missing',1),('full_path_nonstring',1),
                          ('candidate_membership_missing',1),('global_lookup_conflicts',1),
                          ('phase_observations',7),('returned_observations',False)):
            report=native_path_report();report[key]=value
            with self.assertRaises(driver.Refusal):driver.validate_native_path_witness(report)

    def test_runtime_resolver_attestation_and_no_existence_claim_remain_required(self):
        result,placement,desktop=native_result()
        for key in ('complete_module_code_equal','actual_globals_and_aliases_equal','no_resolver_replacement'):
            altered=copy.deepcopy(result);altered['preloaded_resolver_runtime_attestation'][key]=False
            with self.assertRaises(driver.Refusal):driver.validate_result(altered,placement,desktop,0)
        for key in ('no_metadata_writes','no_material_file_IO','no_file_existence_claim'):
            witness=native_path_report();witness[key]=False
            with self.assertRaises(driver.Refusal):driver.validate_native_path_witness(witness)

    def test_contradictory_existence_or_property_write_flags_refuse(self):
        for key in ('external_material_file_existence_qualified','B_material_properties_written'):
            report=binding_report();report[key]=True
            with self.assertRaisesRegex(driver.Refusal,'RESOLVED_MATERIAL_READONLY_SCOPE_REQUIRED'):
                driver.validate_material_report(report)


class CarrierQualificationGateTests(unittest.TestCase):
    def test_prior_closed_real_model_receipt_is_a_separate_required_gate(self):
        value = qualified_creation_report()
        self.assertIs(driver.validate_qualified_creation(value), value)
        self.assertFalse(value['exporter_invoked'])
        self.assertTrue(value['all_four_source_materials_reuse_admitted_B_refs'])

    def test_prior_unreaped_unpreserved_or_incomplete_model_receipt_cannot_authorize_export(self):
        for key in ('whole_full_pass_required', 'private_job_closed', 'launcher_reaped', 'hidden_placement_verified',
                    'original_and_staged_hash_bytes_nsmtime_unchanged', 'source_and_head_unchanged',
                    'material_library_appended', 'material_resources_loaded', 'all_four_source_materials_reuse_admitted_B_refs'):
            for bad in (False, None, 1):
                value = qualified_creation_report(); value[key] = bad
                with self.subTest(field=key, value=bad), self.assertRaises(driver.Refusal):
                    driver.validate_qualified_creation(value)
        for key, bad in (('functional_source_count', True), ('functional_source_count', 1059),
                         ('exact_authenticated_reads', 595), ('exact_authenticated_reads', True)):
            value = qualified_creation_report(); value[key] = bad
            with self.subTest(field=key), self.assertRaises(driver.Refusal): driver.validate_qualified_creation(value)

    def test_prior_receipt_cannot_hide_live_processes_or_unqualified_path_reuse(self):
        for mutate in (
            lambda v: v['fresh_physical_after'].__setitem__('owned_processes', 1),
            lambda v: v['fresh_physical_after'].__setitem__('owned_processes', False),
            lambda v: v['fresh_physical_after'].__setitem__('observer_retained_waited_reaped', False),
            lambda v: v['fresh_physical_after'].__setitem__('full_pids_absent', False),
            lambda v: v['native_material_path_witness'].__setitem__('resolution_complete', False),
            lambda v: v['native_material_path_witness'].__setitem__('no_metadata_writes', False),
            lambda v: v['native_material_path_witness'].__setitem__('no_file_existence_claim', False),
        ):
            value = qualified_creation_report(); mutate(value)
            with self.assertRaises(driver.Refusal): driver.validate_qualified_creation(value)

    def test_prior_success_does_not_authorize_unsupported_fidelity_or_input_publication(self):
        for key in ('historical_saved_B_native_causality_qualified', 'normal_fidelity_qualified', 'exporter_qualified',
                    'carrier_qualified', 'non_normal_semantic_equivalence_qualified', 'application_adoption_qualified',
                    'original_B_scene_opened', 'exporter_invoked', 'blend_saved', 'native_arrays_published'):
            value = qualified_creation_report(); value[key] = True
            with self.subTest(field=key), self.assertRaises(driver.Refusal): driver.validate_qualified_creation(value)
        value = qualified_creation_report(); value['format'] = 'has_fresh_source_owned_B_resolved_material_creation_probe_1'
        with self.assertRaises(driver.Refusal): driver.validate_qualified_creation(value)


class CarrierOutputFailureClosureTests(unittest.TestCase):
    def test_output_or_relation_read_failure_does_not_skip_later_preservation_and_physical_closure(self):
        events = []
        primary = driver.Refusal('STRICT_CARRIER_COMPARISON_REFUSED')
        def output(): events.append('carrier-output'); raise OSError('private owned output path')
        def relation(): events.append('private-relation'); return True
        def runtime(): events.append('runtime'); return True
        def closure():
            events.append('physical')
            return dict(format='has_source_material_binding_physical_closure_1', owned_processes=0,
                full_pids_absent=True, observer_retained_waited_reaped=True, observer_exit=0,
                excluded_exact_pid=os.getpid(), observed_ns=time.time_ns())
        audit = driver.failed_run_audit({'carrier-output': output, 'private-relation': relation, 'runtime': runtime},
            primary_error=primary, launcher_reaped=True, worker_receipt_present=True, closure_observer=closure)
        self.assertEqual(events, ['carrier-output', 'private-relation', 'runtime', 'physical'])
        self.assertEqual(audit['checks'], {'carrier-output': False, 'private-relation': True, 'runtime': True})
        self.assertEqual(audit['primary_error_code'], str(primary))
        self.assertFalse(audit['all_attempted_checks_passed'])
        self.assertTrue(audit['physical_closure_confirmed'])
        self.assertFalse(audit['runtime_lane_released'])
        self.assertFalse(audit['application_adoption_qualified'])



class CarrierReportTests(unittest.TestCase):
    def test_cross_bound_single_operator_resource_and_cold_readiness_report_accepts(self):
        value, placement, desktop = native_result()
        self.assertIs(driver.validate_carrier_report(value), value['carrier_export'])
        self.assertIs(driver.validate_result(value, placement, desktop, 0), value['observation'])
        self.assertFalse(value['carrier_export']['export_observation']['source_normal_error_measured'])
        self.assertFalse(value['normal_fidelity_qualified'])

    def test_attempt_file_or_preflight_alone_cannot_replace_complete_actual_operator(self):
        for key in ('exporter_invoked', 'operator_preflight_observed', 'carrier_written'):
            for missing in (False, None, 1):
                with self.subTest(key=key, missing=missing):
                    value, _, _ = native_result(); value[key] = missing
                    with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)
        for missing in (True, None, 0):
            value, _, _ = native_result(); value['scene_or_registration_restoration_failed'] = missing
            with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_duplicate_operator_partial_attributes_or_cancelled_status_cannot_be_success(self):
        for key, values in (('operator_invocations', (True, 0, 2, 1.0)),
                            ('own_carrier_attributes', (True, 1, 3, 2.0)),
                            ('ordinary_operator_finished', (False, None, 1))):
            for replacement in values:
                with self.subTest(key=key, replacement=replacement):
                    value, _, _ = native_result(); value['carrier_export'][key] = replacement
                    with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_carrier_and_relation_pins_refuse_unbounded_or_untyped_public_values(self):
        for key, values in (('carrier_glb_bytes', (True, 27, 128 * 1024 * 1024 + 1, 28.0)),
                            ('carrier_glb_sha256', ('5' * 63, 'G' * 64, b'5' * 64)),
                            ('private_relation_sha256', ('6' * 65, 'x' * 64, None))):
            for replacement in values:
                with self.subTest(key=key, replacement=replacement):
                    value, _, _ = native_result(); value['carrier_export'][key] = replacement
                    with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_final_primitive_relation_is_bound_to_exact_created_meshes_and_output_hash(self):
        for key, replacement in (('passed', 1), ('meshes', True), ('meshes', 1),
                                 ('primitives', 3), ('source_ids', 9660), ('carrier_glb_sha256', '9' * 64)):
            with self.subTest(key=key, replacement=replacement):
                value, _, _ = native_result()
                value['carrier_export']['export_observation']['actual_export_binding'][key] = replacement
                with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_normal_threshold_is_not_a_measured_error_or_fidelity_qualification(self):
        for key, replacement in (('source_normal_threshold_unchanged', 0.001),
                                 ('source_normal_threshold_unchanged', '2e-5'),
                                 ('source_normal_error_measured', True)):
            value, _, _ = native_result(); value['carrier_export']['export_observation'][key] = replacement
            with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)
        value, _, _ = native_result()
        observation = value['carrier_export']['export_observation']
        observation['source_normal_max_error_unchanged'] = observation.pop('source_normal_threshold_unchanged')
        with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_shared_bindings_are_distinct_from_unique_images_and_cannot_hide_extra_resources(self):
        for key, replacement in (('materials', 5), ('source_images', 3), ('images', 4),
                                 ('image_bindings', 1), ('image_bindings', 5), ('textures', 3), ('textures', 4.0)):
            with self.subTest(key=key, replacement=replacement):
                value, _, _ = native_result()
                value['carrier_export']['export_observation']['resources'][key] = replacement
                with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_every_cold_admission_and_post_read_guard_remains_required(self):
        for key in ('complete_set_admitted_before_buffer_getters', 'packed_memory_branch_preconditions_validated',
                    'nonbuffer_metadata_and_packed_refs_unchanged', 'packed_hashes_rechecked'):
            for replacement in (False, None, 1):
                with self.subTest(key=key, replacement=replacement):
                    value, _, _ = native_result(); value['bounded_image_buffer_readiness'][key] = replacement
                    with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)
        for count in (True, 1, 3, 2.0):
            value, _, _ = native_result(); value['bounded_image_buffer_readiness']['images_verified_ready'] = count
            with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)


    def test_final_private_file_presence_and_readback_remain_bound_after_restoration(self):
        for key, replacement in (('carrier_output_present_unqualified', False),
                                 ('carrier_output_presence_check_failed', True),
                                 ('carrier_output_bytes_unqualified', 29),
                                 ('carrier_output_sha256_unqualified', '0' * 64)):
            with self.subTest(key=key, replacement=replacement):
                value, _, _ = native_result(); value[key] = replacement
                with self.assertRaisesRegex(driver.Refusal, 'FINAL_OWNED_OUTPUT_READBACK_REQUIRED'):
                    driver.validate_carrier_report(value)
        value, _, _ = native_result(); value.pop('carrier_output_bytes_unqualified')
        with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)

    def test_public_report_never_contains_private_relation_or_carrier_payload(self):
        for key, payload in (('private_relation_bytes', b'private'), ('carrier_glb', b'glTF'),
                             ('raw', b'glTF'), ('relation', [[1, 2]]), ('source_ids', [7, 19])):
            value, _, _ = native_result(); value['carrier_export'][key] = payload
            with self.assertRaises(driver.Refusal): driver.validate_carrier_report(value)


class PrivateCarrierReadbackTests(unittest.TestCase):
    def test_bounded_file_reader_returns_the_exact_admitted_bytes_without_transform(self):
        raw = b'glTF' + bytes(24)
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'carrier.glb'; path.write_bytes(raw)
            self.assertEqual(driver.read_private_carrier(path, len(raw), digest), raw)
        marker = b'not-a-parser-test-just-exact-reader'
        with patch.object(driver, 'read_checked', return_value=(marker, {}, ())) as checked:
            actual = driver.read_private_carrier(Path('synthetic-private.glb'), 28, 'a' * 64)
            self.assertIs(actual, marker)
            checked.assert_called_once_with(Path('synthetic-private.glb'), (28, 'a' * 64), limit=128 * 1024 * 1024)

    def test_wrong_readback_pin_or_truncation_refuses_instead_of_rehashing_to_new_baseline(self):
        raw = b'glTF' + bytes(24); digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'carrier.glb'; path.write_bytes(raw)
            for count, expected in ((len(raw) + 1, digest), (len(raw), '0' * 64)):
                with self.subTest(count=count, expected=expected):
                    with self.assertRaises(driver.Refusal): driver.read_private_carrier(path, count, expected)

    def test_untyped_or_unbounded_pin_refuses_before_any_file_access(self):
        for count, digest in ((True, 'a' * 64), (27, 'a' * 64), (128 * 1024 * 1024 + 1, 'a' * 64),
                               (28.0, 'a' * 64), (28, b'a' * 64), (28, 'A' * 64)):
            with self.subTest(count=count, digest=digest):
                with patch.object(driver, 'read_checked', side_effect=AssertionError('must not read')) as checked:
                    with self.assertRaises(driver.Refusal): driver.read_private_carrier(Path('never-open'), count, digest)
                    checked.assert_not_called()

    def test_file_identity_or_namespace_failure_propagates_without_fallback(self):
        failure = driver.Refusal('SYNTHETIC_PRIVATE_CARRIER_IDENTITY_CHANGED')
        with patch.object(driver, 'read_checked', side_effect=failure) as checked:
            with self.assertRaises(driver.Refusal) as error:
                driver.read_private_carrier(Path('owned-private.glb'), 28, 'a' * 64)
            self.assertIs(error.exception, failure)
            self.assertEqual(checked.call_count, 1)


class StrictNonNormalComparisonTests(unittest.TestCase):
    def test_exact_raw_inputs_and_result_are_forwarded_once_without_normalization(self):
        before = b'original bytes with every authored property'
        after = b'new carrier bytes with explicit ID attribute'
        returned = {'format': 'synthetic exact strict comparator result', 'passed': True}
        calls = []
        def compare(left, right):
            calls.append((left, right)); return returned
        actual = driver.run_strict_non_normal(before, after, SimpleNamespace(compare_qualified_non_normal=compare))
        self.assertIs(actual, returned)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], before); self.assertIs(calls[0][1], after)

    def test_semantic_mismatch_preserves_original_exception_and_never_retries(self):
        failure = ValueError('SYNTHETIC_MATERIAL_OR_UV_OR_WEIGHT_MISMATCH')
        calls = []
        def compare(left, right): calls.append((left, right)); raise failure
        with self.assertRaises(ValueError) as error:
            driver.run_strict_non_normal(b'before', b'after', SimpleNamespace(compare_qualified_non_normal=compare))
        self.assertIs(error.exception, failure)
        self.assertEqual(calls, [(b'before', b'after')])

    def test_nonbytes_cannot_trigger_any_parser_or_comparison(self):
        for before, after in ((bytearray(b'before'), b'after'), (b'before', memoryview(b'after')), ('before', b'after')):
            calls = []
            def compare(*args): calls.append(args); raise AssertionError('must not compare')
            with self.assertRaises(driver.Refusal):
                driver.run_strict_non_normal(before, after, SimpleNamespace(compare_qualified_non_normal=compare))
            self.assertEqual(calls, [])


class CommittedCarrierAdmissionTests(unittest.TestCase):
    def run_until_qualified_blob(self, *, wrong_pin=False, blob='wrong'):
        value = context()
        qraw = (json.dumps(qualified_creation_report(), sort_keys=True) + '\n').encode()
        own = b'synthetic driver source'
        qualified = driver.ROOT / 'experiments' / 'synthetic' / 'ROOT_RESULT.json'
        qrow = dict(bytes=len(qraw), sha256=driver.sha(qraw), mtime_ns=123456790)
        data = {'completion.json': value['completion'], 'launch.json': value['launch'],
                'source-before.json': value['before'], 'source-after.json': value['after'],
                'committed-source-blobs.json': value['committed']}
        proof = dict(bytes=1, sha256=driver.sha(b'x'), mtime_ns=123456790)
        head = 'e' * 40
        git = dict(head=head, tested_is_ancestor=True, tested_blobs=value['committed'], head_blobs=value['committed'])
        seen = []
        def read(path, *args, **kwargs):
            path = Path(path)
            if path == Path(driver.__file__): return own, {}, ()
            if path == qualified: return qraw, qrow, ('qualified-stamp',)
            if path.name in data: return b'x', dict(proof), ()
            raise AssertionError('unadmitted file read: ' + str(path))
        def retained(args):
            seen.append(args)
            self.assertEqual(args, ['git', 'rev-parse', head + ':experiments/synthetic/ROOT_RESULT.json'])
            if blob == 'stop-after-valid-lookup': raise RuntimeError('SYNTHETIC_STOP_BEFORE_LOCK')
            return (blob + '\n').encode('ascii')
        args = ['run_carrier.py', '--root-lane-confirmed', '--driver-sha256', driver.sha(own),
                '--worker-sha256', 'b' * 64, '--ledger-sha256', 'c' * 64, '--binding-sha256', driver.BINDING_PIN[1],
                '--qualified-creation', str(qualified), '--qualified-creation-sha256', 'f' * 64 if wrong_pin else driver.sha(qraw)]
        with ExitStack() as stack:
            for target, name, replacement in ((sys, 'argv', args),): stack.enter_context(patch.object(target, name, replacement))
            stack.enter_context(patch.object(driver, 'safe', side_effect=lambda path, **kwargs: Path(path)))
            stack.enter_context(patch.object(driver, 'read_checked', side_effect=read))
            stack.enter_context(patch.object(driver, 'json_read', side_effect=lambda path: (data[Path(path).name], dict(proof))))
            source = stack.enter_context(patch.object(driver, 'source_snapshot', return_value=copy.deepcopy(value['after'])))
            stack.enter_context(patch.object(driver, 'git_proof', return_value=git))
            stack.enter_context(patch.object(driver, 'retained_output', side_effect=retained))
            lock = stack.enter_context(patch.object(driver.os, 'open', side_effect=AssertionError('must not create lock')))
            runtime = stack.enter_context(patch.object(driver, 'runtime_check', side_effect=AssertionError('must not read runtime')))
            spawn = stack.enter_context(patch.object(driver.subprocess, 'Popen', side_effect=AssertionError('must not launch')))
            expected = 'QUALIFIED_CREATION_RECEIPT_PIN_DIFFERS' if wrong_pin else (
                'SYNTHETIC_STOP_BEFORE_LOCK' if blob == 'stop-after-valid-lookup' else 'QUALIFIED_CREATION_RECEIPT_NOT_COMMITTED_EXACT_BYTES')
            exception = RuntimeError if blob == 'stop-after-valid-lookup' else driver.Refusal
            with self.assertRaisesRegex(exception, expected): driver.main()
            lock.assert_not_called(); runtime.assert_not_called(); spawn.assert_not_called()
            if wrong_pin: source.assert_not_called()
        return seen

    def test_cli_receipt_digest_must_match_before_source_runtime_or_process_admission(self):
        self.assertEqual(self.run_until_qualified_blob(wrong_pin=True), [])

    def test_same_path_uncommitted_or_wrong_git_blob_cannot_authorize_export(self):
        self.assertEqual(len(self.run_until_qualified_blob(blob='0' * 40)), 1)

    def test_receipt_git_lookup_uses_admitted_immutable_commit_instead_of_mutable_HEAD(self):
        self.assertEqual(len(self.run_until_qualified_blob(blob='stop-after-valid-lookup')), 1)


class IndependentCarrierComparisonTests(unittest.TestCase):
    def test_non_normal_refusal_still_measures_native_normals_and_keeps_both_outcomes(self):
        events = []; before, carrier = b'before', b'carrier'
        relation, source, frame = object(), object(), object()
        def compare(left, right):
            self.assertIs(left, before); self.assertIs(right, carrier)
            events.append('non-normal'); raise ValueError('synthetic independent material mismatch')
        measured = dict(passed=True, measured=True, source_normal_threshold=2e-5,
                        source_normal_metric='raw_unnormalized_euclidean_vector_distance',
                        source_normal_max_euclidean_error=0.0)
        def measure(raw, ids, native, actualframe, domain):
            events.append('normal'); self.assertIs(raw, carrier); self.assertIs(ids, relation)
            self.assertIs(native, source); self.assertIs(actualframe, frame); self.assertIs(domain, module)
            return measured
        module = SimpleNamespace(compare_qualified_non_normal=compare)
        normal = SimpleNamespace(measure_native_normal_gate=measure)
        result = driver.run_carrier_comparisons(before, carrier, relation, source, frame, module, normal)
        self.assertEqual(events, ['non-normal', 'normal'])
        self.assertFalse(result['non_NORMAL_passed']); self.assertTrue(result['raw_normal_passed'])
        self.assertIs(result['raw_normal'], measured); self.assertFalse(result['passed'])
        self.assertEqual(result['non_NORMAL']['code'], 'STRICT_NON_NORMAL_COMPARISON_REFUSED')

    def test_measured_error_above_unchanged_threshold_cannot_be_hidden_by_non_normal_pass(self):
        strict = dict(passed=True, exact_metadata_and_payload=True)
        measured = dict(passed=False, measured=True, source_normal_threshold=2e-5,
                        source_normal_metric='raw_unnormalized_euclidean_vector_distance',
                        source_normal_max_euclidean_error=0.25)
        normal = SimpleNamespace(measure_native_normal_gate=lambda *args: measured)
        domain = SimpleNamespace(compare_qualified_non_normal=lambda *args: strict)
        result = driver.run_carrier_comparisons(b'before', b'carrier', object(), object(), object(), domain, normal)
        self.assertIs(result['non_NORMAL'], strict); self.assertIs(result['raw_normal'], measured)
        self.assertTrue(result['non_NORMAL_passed']); self.assertFalse(result['raw_normal_passed'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['raw_normal']['source_normal_threshold'], 2e-5)
        self.assertEqual(result['raw_normal']['source_normal_max_euclidean_error'], 0.25)

if __name__ == '__main__':
    unittest.main()
