"""Synthetic CPU tests and read-only pinned exporter source inspection; no native assets."""
import ast
import copy
import hashlib
from pathlib import Path
import struct
import types
import unittest

import observer_instrumentation as O
import exact_point_join as J
from identity_manifest import ManifestLedger

EXPORTER = Path(r'C:\Program Files\Blender Foundation\Blender 5.1\5.1\scripts\addons_core\io_scene_gltf2\blender\exp\primitive_extract.py')
SYNTHETIC = '''class PrimitiveCreator:
    def __init__(self):
        self.dots = {'vertex_index': [0, 1, 2]}
        self.prim_dots = {'vertex_index': [2, 0, 1]}
    def __private(self):
        return 'original private method'
    def primitive_creation_shared(self):
        self.blender_idxs = self.dots['vertex_index']
        return self.__private()
    def primitive_creation_not_shared(self):
        primitives = []
        material_idx = 7
        indices = [0, 1, 2]
        self.blender_idxs = self.prim_dots['vertex_index']
        primitives.append(self.__private())
        return primitives
'''


def fake_module(source=SYNTHETIC):
    module = types.ModuleType('synthetic_exporter')
    module.__file__ = '/synthetic_exporter.py'
    exec(compile(source, module.__file__, 'exec', dont_inherit=True), module.__dict__)
    return module


def synthetic_install(module, callback, source=SYNTHETIC):
    clean, changed, proof = O._instrument(source, {name: (field, None) for name, (field, _) in O.ANCHORS.items()})
    return O._install(module, callback, source, clean, changed, proof)


def fixture():
    identity4 = [[float(r == c) for c in range(4)] for r in range(4)]
    identity3 = [[float(r == c) for c in range(3)] for r in range(3)]
    snapshot = {'name': 'synthetic_hair', 'mesh_name': 'synthetic_mesh',
                'vertices': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                'corner_vertex_indices': [0, 1, 2], 'corner_edge_indices': [0, 1, 2],
                'edges': [[0, 1], [1, 2], [2, 0]], 'faces': [{'start': 0, 'count': 3, 'material': 0, 'smooth': True}],
                'vertex_groups': ['joint_A', 'joint_B'], 'vertex_weights': [[[0, 1.0]], [[1, 1.0]], [[0, .5], [1, .5]]],
                'corner_uv_active': [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
                'object_matrix_world': identity4, 'armature_matrix_world': copy.deepcopy(identity4), 'normal_transform': identity3}
    setter = {'source_lod0_vertex_indices': [10, 11, 12], 'source_raw_vertex_indices': [20, 21, 22],
              'initial_vertices': copy.deepcopy(snapshot['vertices']), 'initial_corner_indices': [0, 1, 2],
              'setter_payload': [[0.0, 0.0, 1.0]] * 3}
    native = {key: copy.deepcopy(snapshot[key]) for key in J.NATIVE_FIELDS}
    native.update(format='has_independent_native_point_expectation_1', logical_name='synthetic_hair',
                  native_lod0_row_count=13, native_raw_row_count=23, source_lod0_vertex_indices=[10, 11, 12],
                  source_raw_vertex_indices=[20, 21, 22], native_normal_words_as_F32=copy.deepcopy(setter['setter_payload']))
    return snapshot, setter, copy.deepcopy(snapshot), native


class ObserverTests(unittest.TestCase):
    def test_pinned_assignment_anchors_and_complete_AST_inverse(self):
        source = EXPORTER.read_bytes().decode('utf-8')
        clean, changed, proof = O.instrument_pinned_class(source)
        self.assertEqual([row['source_line'] for row in proof['sites']], [834, 917])
        self.assertTrue(proof['original_complete_class_AST_restored'])
        self.assertEqual(proof['callback_count'], 2)
        self.assertEqual(len(clean.body[-1].body), len(changed.body[-1].body))
        code = compile(changed, str(EXPORTER), 'exec', dont_inherit=True)
        cls = next(x for x in code.co_consts if isinstance(x, types.CodeType) and x.co_name == 'PrimitiveCreator')
        method = next(x for x in cls.co_consts if isinstance(x, types.CodeType) and x.co_name == 'primitive_creation_not_shared')
        self.assertIn('_PrimitiveCreator__set_regular_attribute', method.co_names)

    def test_full_class_compilation_preserves_private_calls_and_only_two_methods_change(self):
        module = fake_module(); before = dict(module.PrimitiveCreator.__dict__); calls = []
        with synthetic_install(module, lambda *args: calls.append(args)):
            current = module.PrimitiveCreator.__dict__
            self.assertEqual({key for key in before if before[key] is not current[key]}, set(O.METHODS))
            obj = module.PrimitiveCreator()
            self.assertEqual(obj.primitive_creation_shared(), 'original private method')
            self.assertEqual(obj.primitive_creation_not_shared(), ['original private method'])
            self.assertNotIn(O.CALLBACK, module.__dict__)
        self.assertTrue(all(module.PrimitiveCreator.__dict__[key] is value for key, value in before.items()))
        self.assertEqual(calls[0][1:3], ('shared', [0, 1, 2]))
        self.assertEqual(calls[1][1:], ('not_shared', [2, 0, 1], 7, [0, 1, 2], 0))

    def test_callback_failure_still_restores_original_method_objects(self):
        module = fake_module(); before = {name: getattr(module.PrimitiveCreator, name) for name in O.METHODS}
        def fail(*args): raise RuntimeError('synthetic observer failure')
        with self.assertRaises(RuntimeError):
            with synthetic_install(module, fail): module.PrimitiveCreator().primitive_creation_not_shared()
        self.assertTrue(all(getattr(module.PrimitiveCreator, name) is value for name, value in before.items()))

    def test_pinned_source_change_refuses(self):
        with self.assertRaises(ValueError): O.instrument_pinned_class(EXPORTER.read_bytes().decode('utf-8') + '\n')

    def test_anchor_class_construction_and_default_mutations_refuse(self):
        sources = [SYNTHETIC.replace("self.prim_dots['vertex_index']", "self.prim_dots['another']"),
                   SYNTHETIC.replace('class PrimitiveCreator:', 'class PrimitiveCreator(object):'),
                   SYNTHETIC.replace('def __init__(self):', 'def __init__(self, value=list()):')]
        for source in sources:
            with self.assertRaises(ValueError): O._instrument(source, {name: (field, None) for name, (field, _) in O.ANCHORS.items()})

    def test_prepatched_runtime_and_callback_global_collision_refuse(self):
        module = fake_module(); module.PrimitiveCreator.primitive_creation_shared = lambda self: None
        with self.assertRaises(ValueError):
            with synthetic_install(module, lambda *args: None): pass
        module = fake_module(); module.__dict__[O.CALLBACK] = object()
        with self.assertRaises(ValueError):
            with synthetic_install(module, lambda *args: None): pass


class JoinTests(unittest.TestCase):
    def join(self, values=None): return J.join_saved_point_ids('synthetic_hair', *(values or fixture()))

    def test_exact_join_detached_and_explicitly_not_adapter_qualification(self):
        values = fixture(); before = copy.deepcopy(values); ids, report = self.join(values)
        self.assertEqual(ids, (10, 11, 12)); self.assertEqual(values, before)
        self.assertTrue(report['exact_components_joined']); self.assertFalse(report['nearest_matching_used'])
        self.assertFalse(report['native_expected_adapter_independently_qualified'])

    def test_every_saved_current_field_change_refuses(self):
        changes = {'name': 'other', 'mesh_name': 'other', 'vertices': [[0.0, 0.0, 0.0]] * 3,
                   'corner_vertex_indices': [0, 2, 1], 'corner_edge_indices': [2, 1, 0],
                   'edges': [[0, 2], [2, 1], [1, 0]], 'faces': [{'start': 0, 'count': 3, 'material': 1, 'smooth': True}],
                   'vertex_groups': ['joint_B', 'joint_A'], 'vertex_weights': [[[0, .5]], [[1, 1.0]], [[0, .5], [1, .5]]],
                   'corner_uv_active': [[0.0, 0.0]] * 3,
                   'object_matrix_world': [[float(r == c) * 2 for c in range(4)] for r in range(4)],
                   'armature_matrix_world': [[float(r == c) * 2 for c in range(4)] for r in range(4)],
                   'normal_transform': [[float(r == c) * 2 for c in range(3)] for r in range(3)]}
        for key, value in changes.items():
            values = fixture(); values[2][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.join(values)

    def test_setter_position_loop_and_native_word_changes_refuse(self):
        for key, value in [('initial_vertices', [[0.0, 0.0, 0.0]] * 3), ('initial_corner_indices', [0, 2, 1]),
                           ('setter_payload', [[0.0, 1.0, 0.0]] * 3)]:
            values = fixture(); values[1][key] = value
            with self.assertRaises(ValueError): self.join(values)

    def test_native_expected_field_change_refuses(self):
        for key in J.NATIVE_FIELDS:
            values = fixture(); values[3][key] = None
            with self.subTest(key=key), self.assertRaises(ValueError): self.join(values)

    def test_bool_float_duplicate_out_of_domain_and_missing_raw_IDs_refuse(self):
        for value in ([True, 11, 12], [10.0, 11, 12], [10, 10, 12], [10, 11, 13]):
            values = fixture(); values[1]['source_lod0_vertex_indices'] = value
            with self.assertRaises(ValueError): self.join(values)
        values = fixture(); values[1].pop('source_raw_vertex_indices')
        with self.assertRaises(ValueError): self.join(values)

    def test_float_word_signed_zero_and_nonF32_types_refuse(self):
        values = fixture(); values[2]['vertices'][0][0] = -0.0
        with self.assertRaises(ValueError): self.join(values)
        for value in (True, 0, .1, float('nan')):
            values = fixture(); values[2]['vertices'][0][0] = value
            with self.assertRaises(ValueError): self.join(values)

    def test_weight_group_domain_and_nonuniform_matrix_refuse(self):
        values = fixture(); values[2]['vertex_weights'][0] = [[2, 1.0]]
        with self.assertRaises(ValueError): self.join(values)
        values = fixture(); values[2]['normal_transform'][0][0] = 2.0
        with self.assertRaises(ValueError): self.join(values)


class ManifestTests(unittest.TestCase):
    def test_order_comes_only_from_native_point_map_and_exporter_indices(self):
        ledger = ManifestLedger({'synthetic_hair': (10, 11, 12)})
        ledger.record('synthetic_hair', 'not_shared', [2, 0, 1], 0, [0, 1, 2], 0)
        private, public = ledger.finalize(1, 3)
        self.assertEqual(private['rows'][0]['one_based_source_ids'], [13, 11, 12])
        self.assertFalse(public['reads_carrier_values']); self.assertFalse(public['GLTF_mesh_primitive_binding_qualified'])

    def test_shared_branch_or_bad_order_or_types_refuse(self):
        for branch, points, material, topology, ordinal in [('shared', [0, 1, 2], 0, [0, 1, 2], 0),
                ('not_shared', [0, 1, 2], 0, [0, 1, 2], 1), ('not_shared', [True, 1, 2], 0, [0, 1, 2], 0),
                ('not_shared', [0, 1, 2], True, [0, 1, 2], 0), ('not_shared', [0, 1, 2], 0, [0, 1, 3], 0)]:
            with self.assertRaises(ValueError): ManifestLedger({'synthetic_hair': (10, 11, 12)}).record('synthetic_hair', branch, points, material, topology, ordinal)

    def test_incomplete_coverage_duplicate_observation_and_overlap_refuse(self):
        ledger = ManifestLedger({'synthetic_hair': (10, 11, 12)}); ledger.record('synthetic_hair', 'not_shared', [0, 1], 0, [0, 1, 0], 0)
        with self.assertRaises(ValueError): ledger.finalize(1, 3)
        with self.assertRaises(ValueError): ManifestLedger({'a': [1], 'b': [1]})


if __name__ == '__main__': unittest.main(verbosity=2)
