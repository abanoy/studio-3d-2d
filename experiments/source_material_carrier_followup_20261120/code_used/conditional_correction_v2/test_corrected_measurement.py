"""Tiny pure measurement controls; no native asset/model/process is accessed."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path, pin=None):
    raw = path.read_bytes()
    if pin is not None and (len(raw), hashlib.sha256(raw).hexdigest()) != pin:
        raise AssertionError('sealed source pin differs')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module


V = load('_conditional_measure_vvd', ROOT / 'experiments/native_normal_carrier_strategy_20261117/vvd_normals.py',
         (4184, 'f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb'))
with patch.dict(sys.modules, {'vvd_normals': V}):
    C = load('_conditional_measure_corrector', ROOT / 'experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py',
             (17632, '37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08'))
W = load('_conditional_measure_wrapper', HERE / 'conditional_correction.py')


def fixture(first=(1.0, 0.0, 0.0), *, carrier=False, normalized=False):
    binary = b''.join(struct.pack('<3f', *row) for row in (first, (1., 0., 0.), (1., 0., 0.), (1., 0., 0.)))
    views = [dict(buffer=0, byteOffset=12 * i, byteLength=12) for i in range(4)]
    accessors = [dict(bufferView=i, componentType=5126, count=1, type='VEC3') for i in range(4)]
    if normalized: accessors[0]['normalized'] = True
    primitives = [dict(attributes={'NORMAL': i}) for i in range(4)]
    if carrier: primitives[0]['attributes'][C.CARRIER] = 0
    document = dict(asset=dict(version='2.0'), buffers=[dict(byteLength=len(binary))],
                    bufferViews=views, accessors=accessors,
                    meshes=[dict(primitives=primitives[:2]), dict(primitives=primitives[2:])],
                    extras={C.PROVENANCE: {'synthetic_provenance_retained': True}})
    return C.pack_glb(document, binary)


def relation():
    return {(0, 0): (1,), (0, 1): (2,), (1, 0): (3,), (1, 1): (4,)}


class CorrectedMeasurementTests(unittest.TestCase):
    def setUp(self):
        # Only the measurement component is exercised here. The actual wrapper
        # obtains its9661-point expected map from the pinned cbb4/raw-gate path.
        self.source = {i: (1.0, 0.0, 0.0) for i in range(4)}
        self.raw_gate = types.SimpleNamespace(CARRIER=C.CARRIER, _sources=lambda source: source)

    def measure(self, raw, ids=None):
        return W.measure_final(raw, relation() if ids is None else ids, self.source, self.raw_gate, C)

    def test_exact_values_pass_and_derivative_provenance_is_preserved_not_pruned(self):
        raw = fixture(); before = bytes(raw)
        report = self.measure(raw)
        self.assertTrue(report['passed']); self.assertEqual(report['source_normal_max_euclidean_error'], 0.0)
        self.assertEqual((report['source_points'], report['normal_rows'], report['compared_components']), (4, 4, 12))
        self.assertFalse(report['measurement_normalization_or_repair_applied'])
        self.assertEqual(report['source_normal_metric'], 'raw_unnormalized_euclidean_vector_distance')
        self.assertEqual(report['source_normal_threshold'], 2e-5)
        document, _ = C.parse_glb(raw)
        self.assertEqual(document['extras'][C.PROVENANCE], {'synthetic_provenance_retained': True})
        self.assertEqual(raw, before)

    def test_two_individually_subthreshold_errors_jointly_fail_original_euclidean_gate(self):
        raw = fixture((1.0, 1.5e-5, 1.5e-5))
        document, binary = C.parse_glb(raw)
        actual = C._float_accessor(document, binary, 0, 'VEC3')[0]
        self.assertLess(abs(actual[1]), 2e-5); self.assertLess(abs(actual[2]), 2e-5)
        report = self.measure(raw)
        self.assertFalse(report['passed'])
        self.assertGreater(report['source_normal_max_euclidean_error'], 2e-5)
        self.assertFalse(report['measurement_normalization_or_repair_applied'])

    def test_scaled_values_are_not_normalized_into_a_pass(self):
        report = self.measure(fixture((2.0, 0.0, 0.0)))
        self.assertFalse(report['passed']); self.assertEqual(report['source_normal_max_euclidean_error'], 1.0)

    def test_relation_keys_counts_ids_and_complete_source_coverage_remain_required(self):
        variants = []
        ids = relation(); ids.pop((1, 1)); variants.append((ids, 'CORRECTED_PRIMITIVE_DOMAIN'))
        ids = relation(); ids[(0, 0)] = (1, 2); variants.append((ids, 'CORRECTED_NORMAL_DOMAIN'))
        ids = relation(); ids[(0, 0)] = (5,); variants.append((ids, 'CORRECTED_SOURCE_ID_DOMAIN'))
        ids = {key: (1,) for key in relation()}; variants.append((ids, 'CORRECTED_SOURCE_COVERAGE'))
        for ids, code in variants:
            with self.subTest(code=code), self.assertRaisesRegex(W.Refusal, '^' + code + '$'):
                self.measure(fixture(), ids)

    def test_retained_carrier_normalized_and_nonfinite_accessor_values_are_rejected(self):
        with self.assertRaisesRegex(W.Refusal, '^CARRIER_NOT_STRIPPED$'):
            self.measure(fixture(carrier=True))
        with self.assertRaises(ValueError): self.measure(fixture(normalized=True))
        with self.assertRaises(ValueError): self.measure(fixture((float('nan'), 0.0, 0.0)))


if __name__ == '__main__':
    unittest.main()
