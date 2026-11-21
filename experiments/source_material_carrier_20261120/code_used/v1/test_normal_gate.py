"""Pure synthetic normal oracle tests; no native files, bpy, NumPy or engine.

The fixture covers the exact9661-source/2mesh/4primitive profile with cardinal
native vectors and an independent literal Yup expectation table. Its minimal
synthetic GLB tests this normal subset, not full domain or native provenance.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G = load('normal_measurement_under_test', HERE / 'normal_gate.py')
S = load('normal_measurement_test_semantic', ROOT / 'experiments/carrier_input_domain_20261118/semantic_compare.py')
with patch.dict(sys.modules, {'semantic_compare': S}):
    D = load('normal_measurement_test_domain', ROOT / 'experiments/carrier_input_domain_20261118/input_domain.py')

SOURCE = ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
          (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
YUP = ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0),
       (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0))
FRAME = dict(format='has_actual_identity_source_to_yup_normal_frame_1',
    mesh_world_identity=True, armature_world_identity=True, mesh_count=2,
    export_yup=True, export_apply=False, signed_axis_permutation=[1, 3, -2],
    source_coordinate_policy='sourceio_mdl49_standalone_01905_identity_standard_vtx7_1',
    source_unit_conversion_changed=False, six_foot_normalization_applied=False)


def source_rows():
    models = {}
    for name, ids in (('native_a', list(range(5000))), ('native_b', list(range(5000, 9661)))):
        models[name] = dict(ids=ids, rows=[dict(normal=SOURCE[value % len(SOURCE)]) for value in ids])
    return dict(format='has_private_native_point_source_rows_1', checksum=123,
        source_identities={role: dict(bytes=42, sha256='0' * 64) for role in ('mdl', 'vvd', 'vtx')},
        native_lod0_row_count=9661, native_raw_row_count=9661, models=models)


def relations():
    parts = (list(range(2500)), list(range(2500, 5000)), list(range(5000, 7330)), list(range(7330, 9661)))
    rows = [dict(mesh=index // 2, primitive=index % 2, one_based_source_ids=[value + 1 for value in values])
            for index, values in enumerate(parts)]
    # A split/seam may repeat a native ID; every emitted row still gets measured.
    rows[0]['one_based_source_ids'].append(1)
    return rows


def glb(rows=None, *, normal_change=None, carrier_change=None, document_change=None):
    rows = relations() if rows is None else rows
    data, views, accessors = bytearray(), [], []
    meshes = [dict(primitives=[]), dict(primitives=[])]
    def accessor(values, arity):
        raw = struct.pack('<' + 'f' * len(values), *values)
        offset = len(data); data.extend(raw)
        views.append(dict(buffer=0, byteOffset=offset, byteLength=len(raw), target=34962))
        accessors.append(dict(bufferView=len(views) - 1, componentType=5126,
                              count=len(values) // arity, type='VEC3' if arity == 3 else 'SCALAR'))
        return len(accessors) - 1
    for row in rows:
        mi, pi, ids = row['mesh'], row['primitive'], row['one_based_source_ids']
        normals, carrier = [], []
        for index, identifier in enumerate(ids):
            target = YUP[(identifier - 1) % len(YUP)]
            actual = normal_change(mi, pi, index, identifier, target) if normal_change else target
            normals.extend(actual)
            carrier.append(carrier_change(mi, pi, index, identifier) if carrier_change else float(identifier))
        attrs = dict(POSITION=accessor([0.0] * (3 * len(ids)), 3), NORMAL=accessor(normals, 3))
        attrs[G.CARRIER] = accessor(carrier, 1)
        meshes[mi]['primitives'].append(dict(attributes=attrs, mode=4))
    document = dict(asset=dict(version='2.0'), buffers=[dict(byteLength=len(data))],
                    bufferViews=views, accessors=accessors, meshes=meshes)
    if document_change: document_change(document)
    encoded = json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary = bytes(data) + bytes(-len(data) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary)) +
            struct.pack('<I4s', len(encoded), b'JSON') + encoded +
            struct.pack('<I4s', len(binary), b'BIN\0') + binary)


class NormalGateTests(unittest.TestCase):
    def measure(self, raw=None, rows=None, source=None, frame=None):
        return G.measure_native_normal_gate(glb() if raw is None else raw,
            relations() if rows is None else rows, source_rows() if source is None else source,
            copy.deepcopy(FRAME) if frame is None else frame, D)

    def test_complete_independent_cardinal_expectation_passes_and_counts_repeated_rows(self):
        raw, rows, source, frame = glb(), relations(), source_rows(), copy.deepcopy(FRAME)
        frozen_rows, frozen_source, frozen_frame = copy.deepcopy(rows), copy.deepcopy(source), copy.deepcopy(frame)
        report = self.measure(raw, rows, source, frame)
        self.assertTrue(report['passed'])
        self.assertEqual(report['source_normal_max_component_error'], 0.0)
        self.assertEqual(report['source_normal_max_euclidean_error'], 0.0)
        self.assertEqual(report['source_normal_metric'], 'raw_unnormalized_euclidean_vector_distance')
        self.assertEqual(report['source_normal_threshold'], 2e-5)
        self.assertEqual(report['source_points'], 9661)
        self.assertEqual(report['primitives'], 4)
        self.assertEqual(report['exported_normal_rows'], 9662)
        self.assertEqual(report['compared_components'], 9662 * 3)
        self.assertEqual(report['carrier_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertFalse(report['normalization_or_repair_applied'])
        self.assertFalse(report['nearest_or_numeric_identity_matching_used'])
        self.assertFalse(report['current_or_historical_B_identity_inferred'])
        self.assertEqual(rows, frozen_rows); self.assertEqual(source, frozen_source); self.assertEqual(frame, frozen_frame)
        self.assertTrue(report['all_native_source_points_covered'])

    def test_last_repeated_seam_row_is_compared_instead_of_deduplicated(self):
        def change(mi, pi, index, identifier, target):
            return (0.0, 1.0, 0.0) if (mi, pi, index) == (0, 0, 2500) else target
        report = self.measure(glb(normal_change=change))
        self.assertFalse(report['passed'])
        self.assertEqual(report['source_normal_max_component_error'], 1.0)
        self.assertEqual(report['source_normal_max_euclidean_error'], math.sqrt(2.0))

    def test_threshold_nearest_f32_below_limit_passes_without_relaxation(self):
        delta = struct.unpack('<f', struct.pack('<f', 2e-5))[0]
        self.assertLessEqual(delta, 2e-5)
        def change(mi, pi, index, identifier, target):
            return (target[0], delta, target[2]) if (mi, pi, index) == (0, 0, 0) else target
        report = self.measure(glb(normal_change=change))
        self.assertTrue(report['passed'])
        self.assertEqual(report['source_normal_max_euclidean_error'], delta)
        self.assertEqual(report['source_normal_threshold'], 2e-5)

    def test_next_f32_above_original_threshold_fails_with_measured_maximum(self):
        word = struct.unpack('<I', struct.pack('<f', 2e-5))[0] + 1
        delta = struct.unpack('<f', struct.pack('<I', word))[0]
        self.assertGreater(delta, 2e-5)
        def change(mi, pi, index, identifier, target):
            return (target[0], delta, target[2]) if (mi, pi, index) == (0, 0, 0) else target
        report = self.measure(glb(normal_change=change))
        self.assertFalse(report['passed'])
        self.assertEqual(report['source_normal_max_euclidean_error'], delta)

    def test_two_subthreshold_components_fail_original_euclidean_gate(self):
        delta = struct.unpack('<f', struct.pack('<f', 1.5e-5))[0]
        def change(mi, pi, index, identifier, target):
            return (target[0], delta, delta) if (mi, pi, index) == (0, 0, 0) else target
        report = self.measure(glb(normal_change=change))
        self.assertLess(report['source_normal_max_component_error'], 2e-5)
        self.assertGreater(report['source_normal_max_euclidean_error'], 2e-5)
        self.assertEqual(report['source_normal_max_euclidean_error'], math.sqrt(2 * delta * delta))
        self.assertFalse(report['passed'])
        self.assertFalse(report['normalization_or_repair_applied'])

    def test_unscaled_measured_normal_is_not_normalized_to_force_a_pass(self):
        def change(mi, pi, index, identifier, target):
            return tuple(value * 0.9 for value in target) if index == 0 else target
        report = self.measure(glb(normal_change=change))
        self.assertFalse(report['passed']); self.assertGreater(report['source_normal_max_euclidean_error'], 0.09)
        self.assertFalse(report['normalization_or_repair_applied'])

    def test_wrong_axis_identity_frame_would_fail_actual_components(self):
        def change(mi, pi, index, identifier, target): return SOURCE[(identifier - 1) % len(SOURCE)]
        report = self.measure(glb(normal_change=change))
        self.assertFalse(report['passed']); self.assertGreaterEqual(report['source_normal_max_euclidean_error'], 1.0)

    def test_any_unadmitted_frame_flag_axis_or_policy_refuses(self):
        for key, value in (('mesh_world_identity', False), ('armature_world_identity', False),
            ('mesh_count', True), ('export_yup', False), ('export_apply', True),
            ('signed_axis_permutation', [1, 2, 3]), ('signed_axis_permutation', [True, 3, -2]),
            ('source_coordinate_policy', 'other'), ('source_unit_conversion_changed', True),
            ('six_foot_normalization_applied', True)):
            with self.subTest(key=key):
                frame = copy.deepcopy(FRAME); frame[key] = value
                with self.assertRaises(G.Refusal): self.measure(frame=frame)

    def test_missing_or_extra_frame_fields_refuse(self):
        for frame in ({key: value for key, value in FRAME.items() if key != 'format'}, dict(FRAME, guessed=True)):
            with self.assertRaises(G.Refusal): self.measure(frame=frame)

    def test_carrier_half_integer_or_permuted_words_cannot_select_a_different_identity(self):
        for change in (lambda mi, pi, i, identifier: float(identifier) + (0.5 if i == 0 else 0.0),
                       lambda mi, pi, i, identifier: float(identifier + 1) if i == 0 else float(identifier)):
            with self.subTest(change=change):
                with self.assertRaises(G.Refusal): self.measure(glb(carrier_change=change))

    def test_relation_keys_must_be_exact_unique_actual_primitive_keys(self):
        for edit in ('duplicate', 'missing', 'out_of_range', 'bool_index', 'extra_field'):
            with self.subTest(edit=edit):
                rows = relations()
                if edit == 'duplicate': rows[3] = copy.deepcopy(rows[0])
                elif edit == 'missing': rows.pop()
                elif edit == 'out_of_range': rows[0]['mesh'] = 2
                elif edit == 'bool_index': rows[0]['mesh'] = False
                else: rows[0]['untrusted'] = True
                with self.assertRaises(G.Refusal): self.measure(rows=rows)

    def test_relation_count_or_native_domain_mismatch_refuses(self):
        for edit in ('short', 'bool_id', 'zero_id', 'foreign_id'):
            with self.subTest(edit=edit):
                rows = relations()
                if edit == 'short': rows[0]['one_based_source_ids'].pop()
                else: rows[0]['one_based_source_ids'][0] = {'bool_id': True, 'zero_id': 0, 'foreign_id': 200001}[edit]
                with self.assertRaises(G.Refusal): self.measure(rows=rows)

    def test_missing_native_id_cannot_hide_behind_valid_repeated_carrier_words(self):
        rows = relations(); rows[-1]['one_based_source_ids'][-1] = rows[-1]['one_based_source_ids'][0]
        with self.assertRaises(G.Refusal): self.measure(glb(rows), rows=rows)

    def test_duplicate_native_id_across_models_is_ambiguous_even_for_equal_normals(self):
        source = source_rows(); source['models']['native_b']['ids'][0] = 0
        with self.assertRaises(G.Refusal): self.measure(source=source)

    def test_native_row_count_and_f32_unit_words_are_not_guessed(self):
        for edit in ('missing', 'nonf32', 'nonunit', 'bool_id', 'nonfinite'):
            with self.subTest(edit=edit):
                source = source_rows(); model = source['models']['native_a']
                if edit == 'missing': model['rows'].pop()
                elif edit == 'bool_id': model['ids'][0] = True
                else: model['rows'][0]['normal'] = {'nonf32': (0.8, 0.6, 0.0),
                    'nonunit': (0.5, 0.0, 0.0), 'nonfinite': (float('nan'), 0.0, 0.0)}[edit]
                with self.assertRaises(G.Refusal): self.measure(source=source)

    def test_native_source_point_count_is_exact_not_observed_output_derived(self):
        source = source_rows(); source['models']['native_b']['ids'].pop(); source['models']['native_b']['rows'].pop()
        with self.assertRaises(G.Refusal): self.measure(source=source)

    def test_normal_accessor_component_shape_normalization_and_count_are_strict(self):
        for key, value in (('componentType', 5123), ('type', 'VEC4'), ('normalized', True), ('count', 1)):
            with self.subTest(key=key):
                def change(doc):
                    index = doc['meshes'][0]['primitives'][0]['attributes']['NORMAL']
                    doc['accessors'][index][key] = value
                with self.assertRaises(ValueError): self.measure(glb(document_change=change))

    def test_nonfinite_exported_f32_is_refused_by_the_sealed_accessor_reader(self):
        def change(mi, pi, index, identifier, target):
            return (float('inf'), target[1], target[2]) if index == 0 else target
        with self.assertRaises(ValueError): self.measure(glb(normal_change=change))

    def test_missing_or_case_alias_carrier_channel_refuses(self):
        for edit in ('missing', 'alias'):
            with self.subTest(edit=edit):
                def change(doc):
                    attrs = doc['meshes'][0]['primitives'][0]['attributes']
                    if edit == 'missing': del attrs[G.CARRIER]
                    else: attrs[G.CARRIER.lower()] = attrs[G.CARRIER]
                with self.assertRaises(G.Refusal): self.measure(glb(document_change=change))

    def test_no_public_rows_vectors_or_model_names_are_returned(self):
        report = self.measure()
        encoded = json.dumps(report, allow_nan=False)
        self.assertNotIn('native_a', encoded); self.assertNotIn('native_b', encoded)
        self.assertNotIn('one_based_source_ids', encoded); self.assertNotIn('component_bytes', encoded)
        self.assertLess(len(encoded), 4096)


if __name__ == '__main__':
    unittest.main()
