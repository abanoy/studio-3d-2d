"""Pure CPU tests of archive admission and reversible transport; no archive creation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('followup_builder_under_test', HERE / 'build_archive.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def row(data, path='output/case/public.json', compressed=False):
    return {'path': path, 'archive_path': 'actual/case/public.json' + ('.gz' if compressed else ''),
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'gzip_exact_original': compressed}


class TransportTests(unittest.TestCase):
    def test_exact_plain_transport(self):
        data = b'{"checks":15,"failures":0}\n'
        self.assertEqual(BUILDER.transport(row(data), data), data)

    def test_deterministic_gzip_roundtrip(self):
        import gzip
        data = b'{"checks":15,"failures":0}\n'
        a = BUILDER.transport(row(data, compressed=True), data)
        self.assertEqual(a, BUILDER.transport(row(data, compressed=True), data))
        self.assertEqual(gzip.decompress(a), data)

    def test_digest_mutation_refused(self):
        data = b'{}'; plan = row(data); plan['sha256'] = '0' * 64
        with self.assertRaises(AssertionError): BUILDER.transport(plan, data)

    def test_bool_size_refused(self):
        data = b'0'; plan = row(data); plan['bytes'] = True
        with self.assertRaises(AssertionError): BUILDER.transport(plan, data)

    def test_non_bool_compression_refused(self):
        data = b'{}'; plan = row(data); plan['gzip_exact_original'] = 1
        with self.assertRaises(AssertionError): BUILDER.transport(plan, data)

    def test_media_suffix_refused(self):
        data = b'PNG'
        with self.assertRaises(AssertionError): BUILDER.transport(row(data, 'output/scene.png'), data)

    def test_native_array_refused(self):
        data = json.dumps({'corner_normals': [[0, 1, 0]]}).encode()
        with self.assertRaises(AssertionError): BUILDER.transport(row(data), data)

    def test_large_numeric_array_refused(self):
        data = json.dumps({'unknown': list(range(33))}).encode()
        with self.assertRaises(AssertionError): BUILDER.transport(row(data), data)

    def test_private_native_path_refused(self):
        with self.assertRaises(AssertionError): BUILDER.safe_relative('output/PRIVATE_SETTER.json')

    def test_public_physical_receipt_path_allowed(self):
        self.assertEqual(BUILDER.safe_relative('output/private-desktop/case.json').name, 'case.json')

    def test_path_escape_refused(self):
        with self.assertRaises(AssertionError): BUILDER.safe_relative('../private.json')


if __name__ == '__main__':
    unittest.main(verbosity=2)
