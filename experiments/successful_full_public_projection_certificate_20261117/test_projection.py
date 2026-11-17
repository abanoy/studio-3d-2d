"""Authored RAM reports only, with canaries instead of real native/private data."""
import copy
import json
import math
import unittest

import projection_core as P

CANARY = 'AUTHORED_PRIVATE_CANARY_DO_NOT_PUBLISH_71'
BEHAVIOR = ['authored_predicate_%02d' % n for n in range(32)]


def fixture():
    core = ['core_%02d' % n for n in range(36)]
    movies = ['movie_%02d' % n for n in range(21)]
    ignored = ['private_group_%03d' % n for n in range(100)]
    keys = core + movies + ignored + ['neon_workspace']
    registry = {'expected_result_keys': keys, 'expected_core_process_keys': core,
                'expected_movie_keys': movies}
    report = {name: {'exit': 0, 'seconds': .25} for name in core}
    report.update({name: {'frames': 48, 'fps': '24/1', 'duration': '2.000000'} for name in movies})
    report.update({name: {'native_pose': [CANARY, [1.0, 2.0, 3.0]],
                         'source_snapshot': {'path': CANARY}, 'opaque': CANARY} for name in ignored})
    results = {
        'inset': {'checks': 12384, 'failures': 0, 'status': 'PASS', 'configurations': 576,
                  'maximum_projection_error_pixels': .0008, 'maximum_ray_error': .0000002,
                  'native_assets_used': False},
        'behavior': {'format': 'has_neon_behavior_regression_result_1', 'checks': 32, 'failures': 0,
                     'expected_checks': 32, 'complete_assertion_set': True,
                     'named_checks': {n: True for n in BEHAVIOR},
                     'synthetic_included_assets_only': True, 'save_and_fullscreen_actions_instrumented': True,
                     'refresh_preserved_faded_context': True,
                     'toast_diagnostics': [{'private_path': CANARY, 'arbitrary_transform': [1, 2, 3]}]},
        'compact': {'checks': 14, 'failures': 0, 'native_owner_assets_used': False,
                    'compact_timeline_preserved': True,
                    'samples': [{'row': n, 'visible_before_route': True, 'selected_after_route': True,
                                 'viewport_height': 62.0, 'scroll_vertical': n * 21} for n in (0, 32, 63)]},
        'rail': {'format': 'has_neon_rail_placement_regression_1', 'checks': 45, 'failures': 0,
                 'synthetic_fixture_only': True, 'screenshots_written': False},
        'lifecycle': {'format': 'has_neon_world_rail_lifecycle_1', 'checks': 29, 'failures': 0,
                      'cases': list(P.LIFECYCLE), 'source_only_fixture_uses_native_models': False},
    }
    rows = {name: {'result': result, 'process': {'exit': 0, 'reaped': True, 'timed_out': False,
             'seconds': 1.5, 'private_path': CANARY}, 'headless': name == 'inset',
             'result_path': CANARY} for name, result in results.items()}
    report['neon_workspace'] = {'format': 'has_neon_workspace_verification_1', 'passed': True,
        'checks': 12504, 'failures': 0, 'expected_checks': dict(P.COUNTS), 'reports': rows,
        'all_functional_sources_hash_size_mtime_unchanged': True,
        'all_private_jobs_and_desktops_closed': True,
        'source_before': {'path': CANARY, 'native_arrays': [1, 2, 3]}}
    return report, registry


class Projection(unittest.TestCase):
    def setUp(self): self.report, self.registry = fixture()
    def project(self): return P.project(self.report, self.registry, BEHAVIOR)
    def result(self, name): return self.report['neon_workspace']['reports'][name]['result']
    def reject(self):
        with self.assertRaises(P.Refusal): self.project()

    def test_exact_domains_and_scalar_count_scope(self):
        out = self.project()
        self.assertEqual((len(out['result_keys']), len(out['core_process_groups']), len(out['movie_groups'])), (158, 36, 21))
        self.assertEqual(out['neon_workspace']['checks'], 12504)
        self.assertFalse(out['independent_validation_of_all_158_groups_claimed'])
        self.assertTrue(out['codec_evidence_must_be_joined_separately'])

    def test_secret_canaries_in_ignored_nested_arrays_diagnostics_paths_never_copied(self):
        self.assertNotIn(CANARY, json.dumps(self.project(), allow_nan=False))

    def test_input_not_mutated_and_output_does_not_alias_input(self):
        original = copy.deepcopy(self.report); out = self.project()
        out['neon_workspace']['reports']['behavior']['named_checks'][BEHAVIOR[0]] = False
        self.assertEqual(self.report, original)

    def test_missing_extra_or_duplicate_registry_names_refuse(self):
        for mutate in ('missing', 'extra', 'duplicate', 'wrong_type'):
            with self.subTest(mutate=mutate):
                self.setUp()
                if mutate == 'missing': del self.report['private_group_000']
                elif mutate == 'extra': self.report['new_group'] = CANARY
                elif mutate == 'duplicate': self.registry['expected_result_keys'][0] = self.registry['expected_result_keys'][1]
                else: self.registry['expected_result_keys'][0] = {}
                self.reject()

    def test_core_exit_seconds_type_and_nonfinite_mutations_refuse(self):
        for field, bad in [('exit', False), ('exit', 0.0), ('exit', 1), ('seconds', True),
                           ('seconds', math.nan), ('seconds', math.inf), ('seconds', 10 ** 1000)]:
            with self.subTest(field=field, bad_type=type(bad).__name__):
                self.setUp(); self.report['core_00'][field] = bad; self.reject()

    def test_core_unknown_field_is_not_stripped_into_valid_row(self):
        self.report['core_00']['secret'] = CANARY; self.reject()

    def test_movie_frames_rate_duration_and_unknown_fields_refuse(self):
        for field, bad in [('frames', True), ('frames', 47), ('fps', '30/1'),
                           ('duration', CANARY), ('duration', math.nan), ('duration', True),
                           ('duration', '2.1'), ('native_art', CANARY)]:
            with self.subTest(field=field, bad_type=type(bad).__name__):
                self.setUp(); self.report['movie_00'][field] = bad; self.reject()

    def test_neon_counts_and_case_membership_not_weakened(self):
        for mode in ('total', 'count_type', 'failed_case', 'missing', 'extra'):
            with self.subTest(mode=mode):
                self.setUp(); neon = self.report['neon_workspace']
                if mode == 'total': neon['checks'] = 12475
                elif mode == 'count_type': neon['expected_checks']['rail'] = 45.0
                elif mode == 'failed_case': self.result('inset')['failures'] = 1
                elif mode == 'missing': del neon['reports']['lifecycle']
                else: neon['reports']['unknown'] = {}
                self.reject()

    def test_behavior_missing_false_extra_or_unfrozen_predicate_refuses(self):
        for mode in ('missing', 'false', 'extra', 'wrong_scope'):
            with self.subTest(mode=mode):
                self.setUp(); value = self.result('behavior')
                if mode == 'missing': del value['named_checks'][BEHAVIOR[0]]
                elif mode == 'false': value['named_checks'][BEHAVIOR[0]] = False
                elif mode == 'extra': value['named_checks']['extra'] = True
                else: value['refresh_preserved_faded_context'] = False
                self.reject()

    def test_compact_original_input_and_height_contract_retained(self):
        for field, bad in [('row', 62), ('row', False), ('selected_after_route', False),
                           ('visible_before_route', False), ('viewport_height', 115),
                           ('scroll_vertical', math.inf)]:
            with self.subTest(field=field):
                self.setUp(); self.result('compact')['samples'][2][field] = bad; self.reject()

    def test_inset_rail_lifecycle_scope_cannot_be_promoted(self):
        for name, field, bad in [('inset', 'maximum_ray_error', .000003),
                                 ('inset', 'native_assets_used', True),
                                 ('rail', 'screenshots_written', True),
                                 ('lifecycle', 'source_only_fixture_uses_native_models', True),
                                 ('lifecycle', 'cases', list(reversed(P.LIFECYCLE)))]:
            with self.subTest(name=name, field=field):
                self.setUp(); self.result(name)[field] = bad; self.reject()

    def test_neon_process_and_reported_closure_are_still_required(self):
        self.report['neon_workspace']['reports']['rail']['process']['timed_out'] = True; self.reject()
        self.setUp(); self.report['neon_workspace']['all_private_jobs_and_desktops_closed'] = False; self.reject()

    def test_omitted_group_failure_is_not_claimed_to_be_validated(self):
        self.report['private_group_000'] = {'passed': False, 'private': CANARY}
        out = self.project()
        self.assertFalse(out['independent_validation_of_all_158_groups_claimed'])
        self.assertEqual(out['qualification'], 'PROJECTION_ONLY_NOT_A_FULL_VALIDATOR_OR_ACTUAL_RECEIPT')
        self.assertNotIn(CANARY, json.dumps(out))

    def test_actual_activation_unconditionally_refuses_even_claimed_root_flags(self):
        with self.assertRaises(P.Refusal):
            P.activate_archive(root_terminal=True, release_closed=True, report=self.report)


if __name__ == '__main__': unittest.main()
