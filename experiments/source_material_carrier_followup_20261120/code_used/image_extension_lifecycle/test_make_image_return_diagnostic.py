"""Pure strict make-image diagnostics, fake RNA and pinned cache SOURCE only.

Synthetic changed-return cases do not identify the actual V9 predicate failure.
They never broaden admission or qualify an actual SDK/native export.
"""
import copy
import json
import types
import unittest
from unittest.mock import patch

import export_hook_proposal as H
import shared_image_cache_proposal as S
import test_export_hook_proposal as F
import test_shared_image_cache_proposal as P
import test_material_guard_diagnostic as D


def fault_case(variant):
    cache, binary = P.primary_definitions()
    c = P.Case(cache, binary, (0,), attach=False)
    c.common_name = 'PRIVATE requested image name'
    def make_image(buffer, extensions, extras, mime, name, uri, settings):
        values = dict(buffer_view=buffer, extensions=extensions, extras=extras,
                      mime_type=mime, name=name, uri=uri)
        if variant == 'buffer_int': values['buffer_view'] = 0
        elif variant == 'buffer_same_bytes': values['buffer_view'] = binary(buffer.data)
        elif variant == 'buffer_wrong_bytes': values['buffer_view'] = binary(b'PRIVATE wrong encoded bytes')
        elif variant == 'mime': values['mime_type'] = 'PRIVATE MIME'
        elif variant == 'uri': values['uri'] = 'PRIVATE external URI'
        elif variant == 'extensions': values['extensions'] = {'PRIVATE': object()}
        elif variant == 'extras': values['extras'] = {'PRIVATE': object()}
        elif variant == 'name': values['name'] = 'PRIVATE other name'
        elif variant == 'foreign':
            class Foreign:
                def __getattribute__(self, name): raise AssertionError('foreign result getter touched')
            return Foreign()
        return F.Image(**values)
    c.specs['make_image'] = cache['cached'](make_image)
    c.bridge = S.SharedImageCaches(c.resources, c.specs, binary, F.Image)
    return c


def refused(c):
    try:
        c.gather()
    except H.Refusal as error:
        if error.args != ('shared_make_image_return_differs',): raise
        return error
    raise AssertionError('the original make-image return guard must still refuse')


class MakeImageReturnDiagnosticTests(unittest.TestCase):
    def test_success_does_not_create_a_failure_report_or_change_original_coverage(self):
        cache, binary = P.primary_definitions(); c = P.Case(cache, binary)
        c.gather(); report = c.resources.finalize(c.serialize())
        self.assertIsNone(c.bridge.public_make_image_failure)
        self.assertEqual((report['materials'], report['source_images'], report['images']), (2, 1, 1))
        self.assertFalse(c.bridge.failed)

    def test_each_fixed_scalar_predicate_is_observed_without_admitting_the_bad_return(self):
        mapping = dict(mime='result_mime_is_png', uri='result_uri_is_none',
            extensions='result_extensions_is_none', extras='result_extras_is_none', name='result_name_matches_frame')
        for variant, predicate in mapping.items():
            with self.subTest(variant=variant):
                c = fault_case(variant); refused(c)
                report = c.bridge.public_make_image_failure
                self.assertEqual(report['status'], 'OBSERVED'); self.assertEqual(report['failures'], 1)
                self.assertEqual(report['first_refusal_code'], 'shared_make_image_return_differs')
                seen = report['observation']
                self.assertEqual(set(seen), S.MAKE_IMAGE_DIAGNOSTIC_BOOLEANS)
                self.assertTrue(all(type(value) is bool for value in seen.values()))
                self.assertFalse(seen[predicate]); self.assertFalse(seen['all_strict_return_predicates_pass'])
                self.assertTrue(seen['expected_buffer_is_binary_data']); self.assertTrue(seen['expected_buffer_is_retained'])
                self.assertTrue(seen['result_is_expected_image_type']); self.assertFalse(seen['cache_hit'])
                self.assertTrue(c.bridge.failed); self.assertEqual(c.resources.images, [])
                self.assertNotIn('PRIVATE', json.dumps(report))

    def test_result_buffer_integer_is_observed_as_a_boolean_type_fact_without_a_value(self):
        c = fault_case('buffer_int'); refused(c)
        seen = c.bridge.public_make_image_failure['observation']
        self.assertTrue(seen['result_buffer_is_exact_int']); self.assertFalse(seen['result_buffer_is_binary_data'])
        self.assertFalse(seen['result_buffer_is_expected_buffer']); self.assertFalse(seen['result_buffer_is_retained'])
        self.assertFalse(seen['result_buffer_hash_matches_authorized_source'])
        self.assertTrue(seen['incoming_buffer_hash_matches_authorized_source'])
        self.assertTrue(seen['stored_buffer_hash_matches_authorized_source'])
        self.assertTrue(seen['expected_buffer_hash_matches_authorized_source'])
        self.assertTrue(c.bridge.public_make_image_failure['make_image_admission_changed'])

    def test_equal_authorized_bytes_do_not_hide_a_different_unretained_buffer_identity(self):
        c = fault_case('buffer_same_bytes'); refused(c)
        seen = c.bridge.public_make_image_failure['observation']
        self.assertTrue(seen['result_buffer_is_binary_data'])
        self.assertTrue(seen['result_buffer_hash_matches_authorized_source'])
        self.assertFalse(seen['result_buffer_is_retained']); self.assertFalse(seen['result_buffer_is_expected_buffer'])
        self.assertTrue(seen['incoming_buffer_is_retained']); self.assertTrue(seen['stored_buffer_is_retained'])
        self.assertTrue(c.bridge.failed)

    def test_unauthorized_bytes_are_reported_only_as_false_and_never_published(self):
        c = fault_case('buffer_wrong_bytes'); refused(c)
        seen = c.bridge.public_make_image_failure['observation']
        self.assertTrue(seen['result_buffer_is_binary_data'])
        self.assertFalse(seen['result_buffer_hash_matches_authorized_source'])
        self.assertNotIn('PRIVATE', json.dumps(c.bridge.public_make_image_failure))
        self.assertTrue(all(type(value) is bool for value in seen.values()))

    def test_real_cache_hit_can_observe_changed_return_fields_without_replaying_the_make_body(self):
        cache, binary = P.primary_definitions(); c = P.Case(cache, binary)
        first = c.cases[0]
        info, _, _, _ = c.call('texture_info', first.sockets[0], first.sockets, 'DEFAULT', 'ALL', c.settings)
        c.resources.material(D.emitted(info), first.material)
        image = c.resources.images[0]['image']
        image.buffer_view = 0  # Synthetic mutable-return case, not a claim about V9.
        second = c.cases[1]
        with self.assertRaisesRegex(H.Refusal, '^shared_make_image_return_differs$'):
            c.call('texture_info', second.sockets[0], second.sockets, 'DEFAULT', 'ALL', c.settings)
        seen = c.bridge.public_make_image_failure['observation']
        self.assertTrue(seen['cache_hit']); self.assertTrue(seen['result_buffer_is_exact_int'])
        self.assertTrue(seen['expected_buffer_is_retained'])
        self.assertFalse(seen['result_buffer_is_expected_buffer'])
        self.assertTrue(seen['result_mime_is_png']); self.assertTrue(seen['result_name_matches_frame'])
        self.assertEqual(c.body_calls.count('make_image'), 1)
        self.assertEqual(c.bridge.specs['make_image']['hits'], 1)
        self.assertTrue(c.bridge.failed)

    def test_foreign_result_has_no_field_getters_or_private_class_names_read(self):
        c = fault_case('foreign'); refused(c)
        seen = c.bridge.public_make_image_failure['observation']
        self.assertFalse(seen['result_is_expected_image_type']); self.assertFalse(seen['result_fields_observed'])
        encoded = json.dumps(c.bridge.public_make_image_failure)
        self.assertNotIn('Foreign', encoded); self.assertNotIn('PRIVATE', encoded)

    def test_diagnostic_failure_cannot_replace_original_refusal_or_skip_stack_restoration(self):
        c = fault_case('name'); primary = H.Refusal('shared_make_image_return_differs')
        original = S.need
        def strict(value, code):
            if code == 'shared_make_image_return_differs' and not value: raise primary
            return original(value, code)
        def unavailable(*args): raise MemoryError('PRIVATE secondary diagnostic allocation')
        c.bridge._make_image_return_diagnostic = unavailable
        with patch.object(S, 'need', side_effect=strict):
            self.assertIs(refused(c), primary)
        self.assertEqual(c.bridge.public_make_image_failure['status'], 'UNAVAILABLE')
        self.assertIsNone(c.bridge.public_make_image_failure['observation'])
        self.assertEqual(c.bridge.stack, []); self.assertIsNone(c.bridge.active)
        self.assertTrue(c.bridge.failed)
        self.assertNotIn('PRIVATE', json.dumps(c.bridge.public_make_image_failure))

    def test_first_observation_is_detached_and_counter_is_bounded_independently_of_outer_latches(self):
        c = fault_case('name'); refused(c)
        snapshot = copy.deepcopy(c.bridge.public_make_image_failure['observation'])
        for _ in range(130): c.bridge._record_make_image_failure(None, None, None, None, None)
        report = c.bridge.public_make_image_failure
        self.assertEqual(report['failures'], 128); self.assertTrue(report['failure_count_capped'])
        self.assertEqual(report['observation'], snapshot)
        self.assertTrue(report['original_strict_failure_preserved'])
        self.assertTrue(report['make_image_admission_changed']); self.assertFalse(report['resource_equivalence_qualified'])


if __name__ == '__main__':
    unittest.main()
