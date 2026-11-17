"""Small authored RAM inputs only. Never opens a PMX/native/provenance file."""
from pathlib import Path
import builtins
import importlib.util
import json
import struct
import sys
import types
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagnostic as D
import source_patch as P


def empty_prefix(counts):
    # Authored minimal PMX2.0: UTF8, no extra UV, all reference widths1, four empty
    # model texts, then explicit count words. No candidate builder or layout code.
    return b'PMX ' + struct.pack('<f', 2.0) + bytes((8, 1, 0, 1, 1, 1, 1, 1, 1)) + bytes(16) + b''.join(struct.pack('<i', n) for n in counts)


class DiagnosticTests(unittest.TestCase):
    def test_01_source_exact_inverse_one_call_only(self):
        raw = (D.ORACLE_FOLDER / 'oracle.py').read_bytes()
        patched = P.instrument_source(raw)
        self.assertEqual(P.restore_source(patched), raw)
        self.assertEqual(len(patched) - len(raw), len(P.INSERT))
        self.assertEqual(patched.count(P.INSERT), 1)
        self.assertIn(P.INSERT + P.ANCHOR, patched)
        with self.assertRaises(ValueError): P.instrument_source(raw + b'\n')
        with self.assertRaises(ValueError): P.restore_source(patched + b'\n')

    def test_02_complete_empty_tables_exact_names_limits_offsets(self):
        report = D.diagnostic_counts(empty_prefix([0] * 9))
        self.assertIsNone(report['refusal']); self.assertTrue(report['traversal_completed'])
        self.assertEqual([r['table'] for r in report['observed_tables']], list(D.TABLES))
        self.assertEqual([r['count'] for r in report['observed_tables']], [0] * 9)
        self.assertEqual([r['byte_offset'] for r in report['observed_tables']], list(range(33, 69, 4)))
        self.assertEqual([r['ceiling'] for r in report['observed_tables']], [2000000, 12000000, 10000, 10000, 4096, 4096, 4096, 512, 1024])

    def test_03_body_capacity_observed_before_original_guard(self):
        report = D.diagnostic_counts(empty_prefix([0] * 7 + [513]))
        self.assertEqual(report['observed_tables'][-1], {'table': 'body', 'count': 513, 'ceiling': 512, 'byte_offset': 61, 'within_count_budget': False})
        self.assertEqual(report['refusal'], {'type': 'Refused', 'label': 'oracle table-count budget'})
        self.assertFalse(report['traversal_completed'])

    def test_04_joint_capacity_and_negative_count_observed(self):
        report = D.diagnostic_counts(empty_prefix([0] * 8 + [1025]))
        self.assertEqual(report['observed_tables'][-1]['table'], 'joint')
        self.assertEqual(report['observed_tables'][-1]['count'], 1025)
        self.assertEqual(report['observed_tables'][-1]['byte_offset'], 65)
        negative = D.diagnostic_counts(empty_prefix([-1]))
        self.assertEqual(negative['observed_tables'][0]['count'], -1)
        self.assertEqual(negative['refusal']['label'], 'oracle table-count budget')

    def test_05_truncation_after_valid_count_and_before_count(self):
        valid = D.diagnostic_counts(empty_prefix([0] * 7 + [1]))
        self.assertEqual(valid['observed_tables'][-1]['count'], 1)
        self.assertTrue(valid['observed_tables'][-1]['within_count_budget'])
        self.assertEqual(valid['refusal']['label'], 'truncated PMX table extent')
        short = D.diagnostic_counts(empty_prefix([0] * 7) + b'\x01\x00')
        self.assertEqual(len(short['observed_tables']), 7)
        self.assertEqual(short['refusal']['label'], 'truncated PMX field')

    def test_06_witness_byte_identity_and_module_cleanup(self):
        raw = (D.ORACLE_FOLDER / 'oracle.py').read_bytes()
        fixture = (D.ORACLE_FOLDER / 'MANUAL_FIXTURE_EXPECTATIONS.json').read_bytes()
        self.assertEqual(P.sha(fixture), '323129acee5355b6cc6d99b3068e07253e17d87cd01cbcbc572f3a25eed45b59')
        samples = [empty_prefix([0] * 9), bytes.fromhex(json.loads(fixture)['complete_hex'])]
        original = types.ModuleType('_authored_count_test_original'); sys.modules[original.__name__] = original
        try:
            exec(compile(raw, '<exact-old-oracle>', 'exec'), original.__dict__)
            expected = [original.canonical(original.read_oracle(data)) for data in samples]
        finally: sys.modules.pop(original.__name__, None)
        before = set(sys.modules)
        with D.instrument_module(lambda *_values: None) as observed:
            actual = [observed.canonical(observed.read_oracle(data)) for data in samples]
        self.assertEqual(actual, expected)
        self.assertEqual(set(sys.modules), before)

    def test_07_no_candidate_and_no_witness_payload_returned(self):
        real_import = builtins.__import__
        def guarded(name, *args, **kwargs):
            if any(word in name.lower() for word in ('pmx_native', 'pmx_archive', 'compare_tables')):
                raise AssertionError('candidate/comparator/archive import forbidden')
            return real_import(name, *args, **kwargs)
        with mock.patch.object(builtins, '__import__', side_effect=guarded):
            report = D.diagnostic_counts(empty_prefix([0] * 9))
        for key in ('witness_returned', 'candidate_imported_or_run', 'count_offset_proves_prefix_correct', 'native_protocol_qualified', 'simulation_or_production_adoption'):
            self.assertIs(report[key], False)
        self.assertNotIn('records', report); self.assertNotIn('model_names', report)

    def test_08_explicit_file_import_without_own_search_path(self):
        before = sys.path[:]
        sys.path[:] = [item for item in sys.path if item and not Path(item).resolve().is_relative_to(D.HERE.parent.parent)]
        try:
            spec = importlib.util.spec_from_file_location('_isolated_authored_count_entry', D.HERE / 'diagnostic.py')
            value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
            report = value.diagnostic_counts(empty_prefix([0] * 9))
        finally: sys.path[:] = before
        self.assertIsNone(report['refusal']); self.assertEqual(len(report['observed_tables']), 9)

    def test_09_unsupported_header_remains_original_refusal(self):
        data = bytearray(empty_prefix([0] * 9)); data[4:8] = struct.pack('<f', 2.1)
        report = D.diagnostic_counts(bytes(data))
        self.assertEqual(report['observed_tables'], [])
        self.assertEqual(report['refusal']['label'], 'only exact PMX2.0 supported')


if __name__ == '__main__': unittest.main(verbosity=2)
