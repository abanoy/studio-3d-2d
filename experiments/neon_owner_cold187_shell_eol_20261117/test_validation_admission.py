"""Synthetic/source-only negatives; no real admission, native files or processes."""
from pathlib import Path
import ast
import copy
import unittest
from unittest.mock import patch
import validation_admission as V


HERE = Path(__file__).resolve().parent


def copy_fixture():
    d = {'final': Path(r'C:\authored\HAS-Review-Neon-bbbbbbb-native'), 'merged_revision': 'b' * 40,
         'candidate_commit': 'a' * 40, 'source_hashes': {'src/authored.gd': '1' * 64},
         'support_source_hashes': {'docs/authored.md': '2' * 64}, 'source_delta_admission': {'old': True, 'second': True},
         'preparation': {'authored.py': {'sha256': '3' * 64}}, 'full_gate': {'closed.json': {'sha256': '4' * 64}},
         'eol_recipe': {'src/authored.gd': {'mode': 'exact_Git_blob'}}}
    b = {'format': 'has_neon_qualified_merge_owner_review_copy_1', 'passed': True, 'source_commit': d['merged_revision'],
         'candidate_commit': d['candidate_commit'], 'graphics_launched': False, 'native_sources_included': True,
         'functional_source_hashes': d['source_hashes'], 'support_source_hashes': d['support_source_hashes'],
         'source_hashes': {**d['source_hashes'], **d['support_source_hashes']}, 'source_delta_admission': d['source_delta_admission'],
         'builder_preparation': d['preparation'], 'full_run_gate': d['full_gate'], 'checkout_EOL_admission': d['eol_recipe'],
         'final': str(d['final']), 'source_mode': 'candidate_tested_raw_bytes_with_reviewed_Git_EOL_bridge',
         'support_source_mode': 'exact_committed_nonfunctional_Git_blobs',
         'startup_or_final_replay': 'UNRUN_root_private_187_validation_required', 'native_source_files': 495,
         'native_source_bytes': 451266730, 'sourceio_files': 574, 'installed_exporter_sources_preserved': 120}
    return copy.deepcopy(b), copy.deepcopy(d)


class Admission(unittest.TestCase):
    def test_inactive_factory_refuses_before_any_external_read(self):
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('Unexpected IO')) as read:
            with self.assertRaises(ValueError): V.require_validated_inputs()
            read.assert_not_called()

    def test_inactive_token_or_recheck_refuses_before_IO(self):
        with patch.object(V, 'identity', side_effect=AssertionError('Unexpected IO')) as read:
            for action in (V.assert_validated, V.recheck):
                with self.assertRaises(ValueError): action({'fabricated': True})
            read.assert_not_called()

    def test_exact_activated_Q_literal_only_accepts_source_derivation(self):
        reference = (HERE / 'reference_qualified_inputs.py').read_bytes(); activation = b'{"authored":true}\n'
        actual = reference.replace(b'APPROVED_ACTIVATION_SHA256=None', ('APPROVED_ACTIVATION_SHA256=' + repr(V.sha(activation))).encode())
        V.activated_Q_matches_reference(actual, reference, activation)

    def test_Q_activation_absent_wrong_hash_or_nonliteral_refuses(self):
        reference = (HERE / 'reference_qualified_inputs.py').read_bytes()
        for value in ('None', repr('0' * 64), "str('0'*64)"):
            actual = reference.replace(b'APPROVED_ACTIVATION_SHA256=None', ('APPROVED_ACTIVATION_SHA256=' + value).encode())
            with self.assertRaises(ValueError): V.activated_Q_matches_reference(actual, reference, b'{}')

    def test_Q_other_guard_change_refuses_even_with_exact_activation(self):
        reference = (HERE / 'reference_qualified_inputs.py').read_bytes(); raw = b'{}'
        actual = reference.replace(b'APPROVED_ACTIVATION_SHA256=None', ('APPROVED_ACTIVATION_SHA256=' + repr(V.sha(raw))).encode())
        for old, new in [(b"context['functional_sources']==1029", b"context['functional_sources']==1028"),
                         (b"and not final.exists()", b"or not final.exists()")]:
            changed = actual.replace(old, new); self.assertNotEqual(changed, actual)
            with self.assertRaises(ValueError): V.activated_Q_matches_reference(changed, reference, raw)

    def test_factory_has_exact_single_lifecycle_inverse(self):
        source = (HERE / 'reference_qualified_inputs.py').read_bytes()
        old = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'require_qualified_inputs')
        new = V.existing_factory_ast(source); new.name = old.name; changed = 0
        for item in ast.walk(new):
            if isinstance(item, ast.Call) and len(item.args) > 1 and isinstance(item.args[1], ast.Constant) and item.args[1].value == 'exact existing copied review sibling required':
                self.assertEqual(ast.dump(item.args[0]), ast.dump(ast.parse('final.parent==WORKSPACE and final.is_dir()', mode='eval').body))
                item.args[0] = ast.parse('final.parent==WORKSPACE and not final.exists()', mode='eval').body
                item.args[1] = ast.Constant('exact fresh new review sibling required'); changed += 1
        self.assertEqual(changed, 1); self.assertEqual(ast.dump(new), ast.dump(old))

    def test_factory_missing_or_altered_original_precondition_refuses(self):
        source = (HERE / 'reference_qualified_inputs.py').read_bytes()
        for changed in (source.replace(b'and not final.exists()', b'or not final.exists()'),
                        source.replace(b'exact fresh new review sibling required', b'other lifecycle')):
            with self.assertRaises(ValueError): V.existing_factory_ast(changed)

    def test_pure_receipt_keeps_tested_candidate_and_merged_revision_distinct(self):
        b, d = copy_fixture(); self.assertNotEqual(d['candidate_commit'], d['merged_revision'])
        self.assertTrue(V.validate_copy_receipt(b, d))

    def test_copy_failed_or_launched_or_wrong_candidate_refuses(self):
        for key, value in [('passed', False), ('graphics_launched', True), ('native_sources_included', False),
                           ('candidate_commit', 'b' * 40), ('source_commit', 'a' * 40)]:
            b, d = copy_fixture(); b[key] = value
            with self.assertRaises(ValueError): V.validate_copy_receipt(b, d)

    def test_each_full_source_delta_builder_EOL_join_is_required(self):
        for key in ('functional_source_hashes', 'support_source_hashes', 'source_hashes', 'source_delta_admission',
                    'builder_preparation', 'full_run_gate', 'checkout_EOL_admission'):
            b, d = copy_fixture(); b[key] = {}
            with self.assertRaises(ValueError): V.validate_copy_receipt(b, d)

    def test_copy_modes_location_and_unrun_cold_state_are_exact(self):
        for key in ('final', 'source_mode', 'support_source_mode', 'startup_or_final_replay'):
            b, d = copy_fixture(); b[key] = 'unreviewed'
            with self.assertRaises(ValueError): V.validate_copy_receipt(b, d)

    def test_fixed_input_counts_keep_exact_JSON_types(self):
        for key in ('native_source_files', 'native_source_bytes', 'sourceio_files', 'installed_exporter_sources_preserved'):
            b, d = copy_fixture(); b[key] = float(b[key])
            with self.assertRaises(ValueError): V.validate_copy_receipt(b, d)

    def test_metadata_duplicate_and_nonfinite_refuse(self):
        for raw in (b'{"same":1,"same":1}', b'{"value":NaN}'):
            with self.assertRaises(ValueError): V.parse(raw)

    def test_descriptor_types_or_caps_refuse_before_filesystem(self):
        row = {'path': 'authored.json', 'bytes': 1, 'mtime_ns': 1, 'sha256': 'a' * 64}
        with patch.object(V, 'guarded', side_effect=AssertionError('Unexpected IO')):
            for key, value in [('bytes', True), ('bytes', 17 * 1024 * 1024), ('mtime_ns', False), ('sha256', False)]:
                changed = dict(row); changed[key] = value
                with self.assertRaises(ValueError): V.read_bound(changed, HERE, {})

    def test_snapshot_changes_for_mutation_and_numeric_type(self):
        self.assertNotEqual(V.snapshot({'value': True}), V.snapshot({'value': 1}))
        self.assertNotEqual(V.snapshot({'values': [1, 2]}), V.snapshot({'values': [1, 3]}))

    def test_nested_source_packet_refuses_before_reading_wrong_ROOT_layout(self):
        nested = V.EXPERIMENTS / 'authored' / 'nested'
        with patch.object(V, 'guarded', return_value=nested), patch.object(V, 'identity', side_effect=AssertionError('Unexpected IO')):
            with self.assertRaises(ValueError): V.packet(nested, 'a' * 64, {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
