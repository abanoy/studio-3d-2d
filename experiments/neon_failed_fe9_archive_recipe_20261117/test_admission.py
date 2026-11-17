"""Coherent RAM negatives on public closed metadata; never builds/runs native code."""
from pathlib import Path
import ast
import json
import unittest
from unittest.mock import patch
import archive_checks as C

HERE = Path(__file__).resolve().parent


def put(raw, name, obj):
    raw[name] = (json.dumps(obj, allow_nan=False) + '\n').encode()


class Admission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = C.parse((HERE / 'INPUTS.json').read_bytes())
        assert C.sha((HERE / 'INPUTS.json').read_bytes()) == 'a0b2ecdcd8db87363384188a927eb1f58f071250ca6bba34e952e8a40d07f230'
        cls.original = {}
        for row in spec['inputs']:
            data = (Path(spec['roots'][row['root']]) / row['path']).read_bytes()
            assert C.sha(data) == row['sha256'] and len(data) == row['bytes']
            cls.original[row['alias']] = data
    def setUp(self):
        self.raw = dict(self.original)
    def reject(self):
        with self.assertRaises(ValueError): C.check(self.raw)
    def coherent_inventory(self, inventory, receipt_index=None):
        if receipt_index is not None:
            put(self.raw, 'receipts/%03d.json' % receipt_index, inventory['rows'][receipt_index]['receipt'])
            inventory['rows'][receipt_index]['source_sha256'] = C.sha(self.raw['receipts/%03d.json' % receipt_index])
        put(self.raw, 'receipt-inventory.json', inventory)
        release = C.parse(self.raw['graphics-lease-closed.json']); release['receipt_inventory_sha256'] = C.sha(self.raw['receipt-inventory.json']); put(self.raw, 'graphics-lease-closed.json', release)
        return patch.object(C, 'INVENTORY', C.sha(self.raw['receipt-inventory.json']))
    def test_actual_closed_public_metadata_admits(self):
        result = C.check(self.raw); self.assertFalse(result['full_suite_passed']); self.assertEqual(result['physical_jobs'], 68)
    def test_source_or_captured_wrapper_drift_refuses(self):
        for name in ('source-after.json', 'original-verify_shape_catalog.py'):
            with self.subTest(name=name):
                self.setUp(); self.raw[name] += b' '; self.reject()
    def test_passed_state_or_stale_final_report_refuses(self):
        for name, key, value in [('state.json', 'status', 'passed'), ('graphics-lease-closed.json', 'final_full_report_used', True)]:
            with self.subTest(key=key):
                self.setUp(); body = C.parse(self.raw[name]); body[key] = value; put(self.raw, name, body); self.reject()
    def test_birth_precision_or_parent_tamper_refuses(self):
        for key, value in [('creation_utc', '2026-11-17T04:04:18.1277600Z'), ('parent_pid', 19669)]:
            with self.subTest(key=key):
                self.setUp(); body = C.parse(self.raw['root-birth-observation.json']); body['python'][key] = value; put(self.raw, 'root-birth-observation.json', body); self.reject()
    def test_coherent_open_desktop_refuses(self):
        body = C.parse(self.raw['receipt-inventory.json']); body['rows'][1]['receipt']['desktop_closed'] = False
        with self.coherent_inventory(body, 1): self.reject()
    def test_coherent_boolean_exit_is_not_zero(self):
        body = C.parse(self.raw['receipt-inventory.json']); body['rows'][1]['receipt']['exit'] = False
        with self.coherent_inventory(body, 1): self.reject()
    def test_coherent_duplicate_physical_job_refuses(self):
        body = C.parse(self.raw['receipt-inventory.json']); body['rows'][2]['receipt']['desktop'] = body['rows'][1]['receipt']['desktop']
        with self.coherent_inventory(body, 2): self.reject()
    def test_coherent_unregistered_cancellation_refuses(self):
        body = C.parse(self.raw['receipt-inventory.json']); body['rows'][0]['receipt']['exit'] = 1
        with self.coherent_inventory(body, 0): self.reject()
    def test_coherent_orphan_inline_receipt_refuses(self):
        body = C.parse(self.raw['receipt-inventory.json']); body['inline_receipts'][0]['receipt']['child_pid'] = -20
        with self.coherent_inventory(body): self.reject()
    def test_coherent_nonempty_root_scope_refuses(self):
        body = C.parse(self.raw['receipt-inventory.json']); body['process_observation']['owned_runtime_matches'] = [{'synthetic': True}]
        put(self.raw, 'host-observation.json', body['process_observation'])
        with self.coherent_inventory(body): self.reject()
    def test_missing_exact_failure_or_earlier_order_refuses(self):
        self.raw['canonical.log'] = self.raw['canonical.log'].replace(b'FileNotFoundError', b'OtherFailureError'); self.reject()
    def test_no_descriptor_media_or_model_inputs_and_verifier_imports(self):
        spec = C.parse((HERE / 'INPUTS.json').read_bytes())
        self.assertEqual(len(spec['inputs']), 85)
        for row in spec['inputs']:
            self.assertNotEqual(Path(row['path']).name, 'sfm-face-pilot.json'); self.assertIn(Path(row['path']).suffix, ('.json', '.log', '.py', '.ps1'))
        source = ast.parse((HERE / 'verify_packet.py').read_bytes())
        imports = [n.module for n in ast.walk(source) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn('archive_checks', imports); self.assertNotIn('build_packet', imports)


if __name__ == '__main__':
    unittest.main(verbosity=2)
