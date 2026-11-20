"""Synthetic-only proposed checks; no native capture or native input is opened."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('saved_weight_join_subject', HERE / 'join_saved_weights.py')
J = importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)


class SavedWeightJoin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = J.load_helper('native', (J.PROJECT / J.HELPERS['native'][0]).read_bytes())
        cls.snapshot = J.load_helper('snapshot', (J.PROJECT / J.HELPERS['snapshot'][0]).read_bytes())

    def fixture(self):
        def identity(width):
            return [[float(row == column) for column in range(width)] for row in range(width)]
        groups = ['Hip', 'Arm', 'Tip']
        source_positions = [[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]
        positions = [[self.native.f32(value * self.native.F32_SCALE) for value in row] for row in source_positions]
        rows = []
        writes = [[[2, .5], [1, .75], [2, .25]], [[0, 1.]], [[1, .5], [2, .5]]]
        for index in range(3):
            rows.append({'position': source_positions[index], 'normal': [0., 0., 1.],
                         'uv': [[0., 0.], [1., 0.], [0., 1.]][index],
                         'positive_weight_writes': writes[index]})
        native = {'rows': rows, 'ids': [0, 1, 2], 'raw_ids': [5, 6, 7], 'corners': [0, 1, 2]}
        saved = {'name': 'Synthetic', 'mesh_name': 'SyntheticMesh', 'vertices': positions,
                 'corner_vertex_indices': [0, 1, 2], 'corner_edge_indices': [0, 1, 2],
                 'edges': [[0, 1], [1, 2], [2, 0]],
                 'faces': [{'start': 0, 'count': 3, 'material': 0, 'smooth': True}],
                 'vertex_groups': groups, 'vertex_weights': [[[2, .25], [1, .75]], [[0, 1.]], [[1, .5], [2, .5]]],
                 'corner_uv_active': [[0., 1.], [1., 1.], [0., 0.]],
                 'object_matrix_world': identity(4), 'armature_matrix_world': identity(4),
                 'normal_transform': identity(3)}
        state = {'vertices': copy.deepcopy(positions), 'corner_vertex_indices': [0, 1, 2]}
        setter = {'source_lod0_vertex_indices': [0, 1, 2], 'source_raw_vertex_indices': [5, 6, 7],
                  'initial_vertices': copy.deepcopy(positions), 'initial_corner_indices': [0, 1, 2],
                  'setter_payload': [[0., 0., 1.] for _ in range(3)],
                  'stages': {stage: copy.deepcopy(state) for stage in ('after_setter', 'before_validate', 'after_validate')},
                  'unobserved_control': copy.deepcopy(state)}
        return native, saved, setter, groups

    def run_join(self, data):
        return J.compare_model(*data, self.native, self.snapshot)

    def test_first_positive_order_last_replace_matches_explicit_observation(self):
        result = self.run_join(self.fixture())
        self.assertTrue(result['all_exact'])
        self.assertEqual(result['positive_source_calls'], 6)
        self.assertEqual(result['distinct_positive_group_histogram'], {'1': 1, '2': 2})

    def test_sorted_group_normalization_is_detected(self):
        data = self.fixture();data[1]['vertex_weights'][0].reverse()
        result = self.run_join(data)
        self.assertFalse(result['all_exact'])
        self.assertEqual(result['mismatches']['stored_weight_group_order_rows'], 1)
        self.assertEqual(result['mismatches']['stored_weight_value_rows'], 0)

    def test_wrong_last_replace_value_is_detected(self):
        data = self.fixture();data[1]['vertex_weights'][0][0][1] = .5
        result = self.run_join(data)
        self.assertEqual(result['mismatches']['ordered_stored_weight_rows'], 1)
        self.assertEqual(result['mismatches']['stored_weight_group_order_rows'], 0)

    def test_complete_source_id_permutation_refuses(self):
        data = self.fixture();data[2]['source_lod0_vertex_indices'] = [1, 0, 2]
        with self.assertRaises(J.Refusal):self.run_join(data)

    def test_raw_id_permutation_refuses(self):
        data = self.fixture();data[2]['source_raw_vertex_indices'] = [6, 5, 7]
        with self.assertRaises(J.Refusal):self.run_join(data)

    def test_coincident_points_do_not_choose_source_identities(self):
        data = self.fixture();data[0]['rows'][1]['position'] = [0., 0., 0.]
        data[1]['vertices'][1] = [0., 0., 0.]
        data[2]['initial_vertices'][1] = [0., 0., 0.]
        for stage in (*data[2]['stages'].values(), data[2]['unobserved_control']):stage['vertices'][1] = [0., 0., 0.]
        data[2]['source_lod0_vertex_indices'] = [1, 0, 2]
        with self.assertRaises(J.Refusal):self.run_join(data)

    def test_one_float32_position_word_is_detected_without_epsilon(self):
        data = self.fixture();data[1]['vertices'][0][0] = struct.unpack('<f', struct.pack('<I', 1))[0]
        result = self.run_join(data)
        self.assertEqual(result['mismatches']['native_to_saved_position_rows'], 1)
        self.assertEqual(result['mismatches']['setter_to_saved_position_rows'], 1)

    def test_one_float32_uv_word_is_detected(self):
        data = self.fixture();data[1]['corner_uv_active'][1][0] = struct.unpack('<f', struct.pack('<I', 0x3f800001))[0]
        self.assertEqual(self.run_join(data)['mismatches']['native_to_saved_uv_rows'], 1)

    def test_setter_normal_word_identity_is_checked(self):
        data = self.fixture();data[2]['setter_payload'][0][0] = self.native.f32(.001)
        self.assertEqual(self.run_join(data)['mismatches']['native_to_setter_normal_input_rows'], 1)

    def test_setter_signed_zero_word_is_not_collapsed(self):
        data = self.fixture();data[2]['setter_payload'][0][0] = -0.
        self.assertEqual(self.run_join(data)['mismatches']['native_to_setter_normal_input_rows'], 1)

    def test_saved_normal_readback_never_proves_this_point_weight_join(self):
        data = self.fixture();data[1]['corner_normals_stored_snapshot'] = [[100., 100., 100.]] * 3
        self.assertTrue(self.run_join(data)['all_exact'])

    def test_boolean_source_id_does_not_pass_integer_identity(self):
        data = self.fixture();data[2]['source_lod0_vertex_indices'][1] = True
        with self.assertRaises(J.Refusal):self.run_join(data)

    def test_duplicate_stored_group_refuses(self):
        data = self.fixture();data[1]['vertex_weights'][0][1][0] = 2
        with self.assertRaises((J.Refusal, ValueError)):self.run_join(data)

    def test_zero_stored_weight_refuses_instead_of_filtering(self):
        data = self.fixture();data[1]['vertex_weights'][0][0][1] = 0.
        with self.assertRaises((J.Refusal, ValueError)):self.run_join(data)

    def test_stages_and_loop_order_are_joined(self):
        data = self.fixture();data[2]['stages']['after_validate']['corner_vertex_indices'] = [0, 2, 1]
        self.assertEqual(self.run_join(data)['mismatches']['after_validate_corner_indices'], 2)

    def test_boolean_setter_corner_indices_never_equal_integer_indices(self):
        for stage in ('initial', 'after_setter', 'before_validate', 'after_validate', 'unobserved_control'):
            with self.subTest(stage=stage):
                data = self.fixture()
                if stage == 'initial':data[2]['initial_corner_indices'][1] = True
                elif stage == 'unobserved_control':data[2][stage]['corner_vertex_indices'][1] = True
                else:data[2]['stages'][stage]['corner_vertex_indices'][1] = True
                with self.assertRaises(J.Refusal):self.run_join(data)

    def test_no_inputs_are_modified(self):
        data = self.fixture();before = copy.deepcopy(data)
        self.run_join(data)
        self.assertEqual(data, before)

    def test_changed_helper_is_refused_before_execution(self):
        with self.assertRaises(J.Refusal):J.load_helper('native', b'raise RuntimeError("must not execute")')

    def test_report_shape_contains_no_native_arrays(self):
        def verify(value):
            self.assertNotIsInstance(value, (list, tuple, bytes, bytearray))
            if isinstance(value, dict):
                for child in value.values():verify(child)
        verify(self.run_join(self.fixture()))


if __name__ == '__main__':
    unittest.main()
