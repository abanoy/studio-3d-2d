"""Independent synthetic capture-boundary probes; installed reader source is never executed."""
import hashlib
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

SOURCE = Path(__file__).resolve().parent.parent / 'pmx_physics_capture_prototype_20261117'
assert hashlib.sha256((SOURCE / 'INDEX.json').read_bytes()).hexdigest() == '544208654bebc2b74909afae6391dadc32d27f3374291406b7923c12abfe2f56'
assert hashlib.sha256((SOURCE / 'capture_decoded.py').read_bytes()).hexdigest() == '6a0af8e9209ce0e782f140da37405fda9d3bd82d02b241c432dbac32c83ad78e'
sys.path.insert(0, str(SOURCE))
import capture_decoded as C
from test_capture_decoded import PARSER_SOURCE, model, header


def capture(value, source=None, limits=None):
    return C.capture_decoded(value, source if source is not None else header(), parser_source_bytes=PARSER_SOURCE,
                             **({'limits': limits} if limits is not None else {}))


def inactive(result):
    assert result['applied'] is False and result['runtime_support'] == 'NONE'
    assert result['native_file_join'] == 'UNQUALIFIED' and result['native_file_preservation_complete'] is False


class PeerBoundaryTests(unittest.TestCase):
    def test_exact_capsule_boundary_accepts_and_one_less_refuses(self):
        original = capture(model()); size = len(C.canonical_bytes(original))
        result = capture(model(), limits=C.Limits(capsule_bytes=size))
        self.assertEqual(C.canonical_bytes(result), C.canonical_bytes(original)); inactive(result)
        with self.assertRaises(C.CaptureError): capture(model(), limits=C.Limits(capsule_bytes=size - 1))

    def test_every_limit_rejects_boolean_without_coercion(self):
        for name in C.HARD_LIMITS:
            with self.subTest(name=name), self.assertRaises(C.CaptureError):
                capture(model(), limits=C.Limits(**{name: True}))

    def test_all_supported_float_fields_preserve_negative_zero(self):
        item = model()
        for body in item.rigids:
            for name in C.RIGID_FLOATS: setattr(body, name, -0.0)
            for name in C.RIGID_VECTORS: setattr(body, name, (-0.0,) * 3)
        for joint in item.joints:
            for name in C.JOINT_VECTORS: setattr(joint, name, (-0.0,) * 3)
        result = json.loads(C.canonical_bytes(capture(item))); inactive(result)
        for row in result['rigids']:
            for name in C.RIGID_FLOATS: self.assertEqual(struct.pack('<d', row[name]), struct.pack('<d', -0.0))
            for name in C.RIGID_VECTORS:
                for value in row[name]: self.assertEqual(struct.pack('<d', value), struct.pack('<d', -0.0))
        for row in result['joints']:
            for name in C.JOINT_VECTORS:
                for value in row[name]: self.assertEqual(struct.pack('<d', value), struct.pack('<d', -0.0))

    def test_empty_tables_and_header_only_bytes_never_qualify_native_join(self):
        result = capture(NS(bones=[], rigids=[], joints=[]), source=header(payload=b'')); inactive(result)
        self.assertTrue(result['decoded_supported_fields_complete'])
        self.assertEqual(result['source_fingerprint']['validation_scope'], 'FIXED_HEADER_ONLY_NOT_A_NATIVE_FILE_DECODER')

    def test_changed_supplied_bytes_never_create_a_join(self):
        a = capture(model(), source=header(payload=b'A')); b = capture(model(), source=header(payload=b'B'))
        self.assertNotEqual(a['source_fingerprint']['sha256'], b['source_fingerprint']['sha256'])
        self.assertEqual(a['rigids'], b['rigids']); inactive(a); inactive(b)

    def test_unknown_values_only_described_and_never_qualify_native_join(self):
        item = model(); item.rigids[0].unknown = {'uncaptured_private_value': [1, 2, 3]}
        result = capture(item, source=header('2.1')); inactive(result)
        self.assertFalse(result['decoded_supported_fields_complete'])
        unknown = next(x for x in result['issues'] if x['path'] == 'rigids[0].unknown')
        self.assertEqual(unknown['python_type'], 'dict'); self.assertFalse(unknown['values_captured'])
        self.assertNotIn('uncaptured_private_value', C.canonical_bytes(result).decode())


if __name__ == '__main__': unittest.main(verbosity=2)
