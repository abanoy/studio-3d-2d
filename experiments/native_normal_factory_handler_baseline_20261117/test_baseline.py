"""Authored metadata only; no private captures, Blender modules or callbacks."""
import copy
import json
from unittest.mock import patch
import unittest
import baseline_predicate as B


def fixture():
    paths = {'POSE_LIBRARY_GUI': r'C:\SYNTHETIC\pose.py', 'COPY_GLOBAL_TRANSFORM': r'C:\SYNTHETIC\transform.py'}
    rows = []
    for number, slot in enumerate(B.SLOTS):
        rows.append({'handler_list': slot['handler_list'], 'index': slot['index'], 'kind': 'PYTHON_FUNCTION',
                     'name': 'SYNTHETIC_PRIVATE_CALLBACK_' + str(number), 'module': 'SYNTHETIC_PRIVATE_MODULE',
                     'qualname': 'SYNTHETIC_PRIVATE_QUALNAME_' + str(number),
                     'code_filename': paths[slot['source_role']], 'first_line': 10 + number,
                     'bytecode_sha256': 'c' * 64})
    capture = {'format': 'has_private_Blender_factory_handler_metadata_1', 'phase': 'FACTORY_BEFORE_KNOWN_B_OPEN',
               'handler_list_counts': dict(B.COUNTS), 'callbacks': rows, **{key: False for key in B.FLAGS}}
    return capture, paths, copy.deepcopy(B.SOURCES)


class BaselineTests(unittest.TestCase):
    def test_exact_normalized_policy_slots_and_wrong_order_or_identity(self):
        rows = [{k: row[k] for k in ('handler_list', 'index', 'source_role', 'metadata_signature')} for row in B.SLOTS]
        self.assertTrue(B._check_normalized(rows))
        for changed in (list(reversed(rows)), rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError): B._check_normalized(changed)
        changed = copy.deepcopy(rows); changed[0]['metadata_signature'] = 'f' * 64
        with self.assertRaises(ValueError): B._check_normalized(changed)

    def test_same_bytecode_does_not_collapse_different_function_identity(self):
        capture, paths, identities = fixture(); row = capture['callbacks'][0]
        changed = dict(row); changed['name'] = 'DIFFERENT_FUNCTION'
        self.assertNotEqual(B.signature(row, 'POSE_LIBRARY_GUI'), B.signature(changed, 'POSE_LIBRARY_GUI'))
        with self.assertRaises(ValueError): B.validate_baseline(capture, paths, identities)

    def test_all_counts_empty_lists_strict_false_flags_and_schema_required(self):
        capture, paths, identities = fixture()
        for key, bad in (('save_post', 1), ('save_post', False)):
            changed = copy.deepcopy(capture); changed['handler_list_counts'][key] = bad
            with self.assertRaises(ValueError): B._normalize(changed, paths, identities)
        for flag in B.FLAGS:
            for bad in (True, 0, None):
                changed = copy.deepcopy(capture); changed[flag] = bad
                with self.assertRaises(ValueError): B._normalize(changed, paths, identities)
        changed = copy.deepcopy(capture); changed['unknown'] = 'secret'
        with self.assertRaises(ValueError): B._normalize(changed, paths, identities)

    def test_explicit_trusted_paths_and_whole_source_identities_never_opened(self):
        capture, paths, identities = fixture()
        with patch('builtins.open', side_effect=AssertionError('Pure predicate must not open any path')):
            rows = B._normalize(capture, paths, identities)
        self.assertEqual(len(rows), 3)
        changed = copy.deepcopy(capture); changed['callbacks'][0]['code_filename'] += '.other'
        with self.assertRaises(ValueError): B._normalize(changed, paths, identities)
        changed_ids = copy.deepcopy(identities); changed_ids['POSE_LIBRARY_GUI']['sha256'] = 'f' * 64
        with self.assertRaises(ValueError): B._normalize(capture, paths, changed_ids)

    def test_extra_callback_fields_kind_and_boolean_indices_refused(self):
        capture, paths, identities = fixture()
        for key, value in (('kind', 'BUILTIN_NO_PYTHON_CODE'), ('index', False), ('first_line', True)):
            changed = copy.deepcopy(capture); changed['callbacks'][0][key] = value
            with self.assertRaises(ValueError): B._normalize(changed, paths, identities)
        changed = copy.deepcopy(capture); changed['callbacks'][0]['globals'] = 'unobserved'
        with self.assertRaises(ValueError): B._normalize(changed, paths, identities)

    def test_projection_contains_no_raw_names_paths_or_current_context_qualification(self):
        public = B._public_payload(); text = json.dumps(public)
        for canary in ('SYNTHETIC_PRIVATE', 'code_filename', 'qualname', 'C:\\', '__module__'):
            self.assertNotIn(canary, text)
        for key in ('runtime_co_names_or_globals_observed', 'callbacks_invoked', 'known_B_opened',
                    'handler_safety_or_future_admission_proved', 'current_full_context_established',
                    'old_strict31_native_PASS', 'native_fidelity_repair_export_or_adoption'):
            self.assertIs(public[key], False)
        capture, paths, identities = fixture()
        with self.assertRaises(ValueError): B.project_capture(capture, paths, identities)


if __name__ == '__main__': unittest.main(verbosity=2)
