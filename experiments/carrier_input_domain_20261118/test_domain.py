import copy
import json
import struct
import unittest
from unittest.mock import patch

from input_domain import Refusal, Snapshot, compare_qualified_non_normal, qualify_input_domain, read_semantic_glb
from semantic_compare import freeze
from test_semantic_compare import fixture, carrier_and_relayout, change_component


def glb(doc, binary, raw_json=None):
    payload = raw_json if raw_json is not None else json.dumps(doc, allow_nan=False).encode()
    payload += b' ' * (-len(payload) % 4)
    binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(payload) + len(binary)) +
            struct.pack('<I4s', len(payload), b'JSON') + payload +
            struct.pack('<I4s', len(binary), b'BIN\0') + binary)


class DomainTests(unittest.TestCase):
    def test_valid_bridge_preserves_exact_typed_inputs(self):
        doc, binary = fixture(); original = freeze(doc)
        carrier, packed = carrier_and_relayout(doc, binary)
        result = compare_qualified_non_normal(glb(doc, binary), glb(carrier, packed))
        self.assertTrue(result['before_domain']['passed'])
        self.assertTrue(result['carrier_domain']['passed'])
        self.assertTrue(result['preservation']['passed'])
        self.assertFalse(result['native_normal_repair_or_adoption_qualified'])
        self.assertEqual(freeze(doc), original)

    def test_original_lexical_negative_zero_is_rejected(self):
        doc, binary = fixture()
        raw = json.dumps(doc).encode().replace(b'"integer": 1', b'"integer": -0')
        with self.assertRaises(Refusal): read_semantic_glb(glb(doc, binary, raw))

    def test_float_negative_zero_is_retained(self):
        doc, binary = fixture(); parsed, _ = read_semantic_glb(glb(doc, binary))
        self.assertEqual(struct.pack('<d', parsed['extras']['zero']), struct.pack('<d', -0.0))

    def test_duplicate_json_and_extra_chunks_refuse(self):
        doc, binary = fixture()
        raw = json.dumps(doc).encode().replace(b'"version": "2.0"', b'"version":"2.0","version":"2.0"')
        with self.assertRaises(Refusal): read_semantic_glb(glb(doc, binary, raw))
        bad = bytearray(glb(doc, binary)); bad.extend(b'12345678'); struct.pack_into('<I', bad, 8, len(bad))
        with self.assertRaises(Refusal): read_semantic_glb(bytes(bad))

    def test_joint_component_joins_owning_skin_domain(self):
        doc, binary = change_component(*fixture(), 'JOINTS_0', b'\xff')
        with self.assertRaisesRegex(Refusal, 'Joint component outside'): qualify_input_domain(doc, binary)

    def test_duplicate_skin_joint_is_rejected_with_matching_bind_count(self):
        doc, binary = fixture(); binary = bytearray(binary); skin = doc['skins'][0]
        a = doc['accessors'][skin['inverseBindMatrices']]; view = doc['bufferViews'][a['bufferView']]
        old = bytes(binary[view['byteOffset']:view['byteOffset'] + view['byteLength']])
        binary.extend(b'\0' * (-len(binary) % 4)); view.update(byteOffset=len(binary), byteLength=128)
        binary.extend(old + old); a['count'] = 2; skin['joints'] = [1, 1]; doc['buffers'][0]['byteLength'] = len(binary)
        with self.assertRaisesRegex(Refusal, 'Duplicate skin joint'): qualify_input_domain(doc, bytes(binary))

    def test_cycle_and_multiple_parent_reject(self):
        for mode in ('cycle', 'multiple'):
            doc, binary = fixture()
            if mode == 'cycle': doc['nodes'][1]['children'] = [0]
            else: doc['nodes'].append({'children': [1]})
            with self.assertRaises(Refusal): qualify_input_domain(doc, binary)

    def test_scene_root_cannot_have_parent(self):
        doc, binary = fixture(); doc['scenes'][0]['nodes'] = [1]
        with self.assertRaisesRegex(Refusal, 'graph roots'): qualify_input_domain(doc, binary)

    def test_skin_pair_and_no_skin_owner_reject(self):
        for mode in ('no_skin', 'unpaired', 'alias'):
            doc, binary = fixture(); attrs = doc['meshes'][0]['primitives'][0]['attributes']
            if mode == 'no_skin': del doc['nodes'][0]['skin']
            elif mode == 'unpaired': attrs['WEIGHTS_1'] = attrs.pop('WEIGHTS_0')
            else: attrs['JOINTS_00'] = attrs.pop('JOINTS_0')
            with self.assertRaises(Refusal): qualify_input_domain(doc, binary)

    def test_animation_rotation_requires_VEC4(self):
        doc, binary = fixture(); doc['animations'][0]['channels'][0]['target']['path'] = 'rotation'
        with self.assertRaisesRegex(Refusal, 'output shape/count'): qualify_input_domain(doc, binary)

    def test_animation_time_monotonic_and_nonnegative(self):
        for times in ((1.0, 0.0), (0.0, 0.0), (-1.0, 1.0)):
            doc, binary = fixture(); binary = bytearray(binary)
            a = doc['accessors'][doc['animations'][0]['samplers'][0]['input']]; v = doc['bufferViews'][a['bufferView']]
            struct.pack_into('<2f', binary, v['byteOffset'], *times)
            with self.assertRaisesRegex(Refusal, 'Animation times'): qualify_input_domain(doc, bytes(binary))

    def test_cubic_count_and_duplicate_target_reject(self):
        for mode in ('cubic', 'duplicate'):
            doc, binary = fixture(); animation = doc['animations'][0]
            if mode == 'cubic': animation['samplers'][0]['interpolation'] = 'CUBICSPLINE'
            else: animation['channels'].append(copy.deepcopy(animation['channels'][0]))
            with self.assertRaises(Refusal): qualify_input_domain(doc, binary)

    def test_negative_weight_and_rest_binding_changes(self):
        doc, binary = change_component(*fixture(), 'WEIGHTS_0', struct.pack('<f', -0.5))
        with self.assertRaisesRegex(Refusal, 'weight component'): qualify_input_domain(doc, binary)
        doc, binary = fixture(); before = qualify_input_domain(doc, binary)
        doc['nodes'][1]['translation'] = [1.0, 0.0, 0.0]
        after = qualify_input_domain(doc, binary)
        self.assertNotEqual(before['rest_skin_binding_sha256'], after['rest_skin_binding_sha256'])

    def test_boolean_index_and_nonzero_BIN_padding_refuse(self):
        doc, binary = fixture(); doc['nodes'][0]['skin'] = True
        with self.assertRaises(Refusal): qualify_input_domain(doc, binary)
        doc, binary = fixture(); raw = bytearray(glb(doc, binary + b'x')); doc['buffers'][0]['byteLength'] = len(binary)
        with self.assertRaises(Refusal): read_semantic_glb(glb(doc, binary + b'x'))

    def test_unused_sampler_and_unowned_mesh_refuse(self):
        for mode in ('sampler', 'mesh'):
            doc, binary = fixture()
            if mode == 'sampler': doc['animations'][0]['samplers'].append(copy.deepcopy(doc['animations'][0]['samplers'][0]))
            else: doc['meshes'].append(copy.deepcopy(doc['meshes'][0]))
            with self.assertRaisesRegex(Refusal, 'Unused'): qualify_input_domain(doc, binary)

    def test_cost_refuses_before_parent_decodes(self):
        doc, binary = fixture()
        for accessor in doc['accessors']: accessor['count'] = 2_000_000
        with patch.object(Snapshot, 'canonical', side_effect=AssertionError('Parent must not decode')):
            with self.assertRaisesRegex(Refusal, 'Preflight decoded'): qualify_input_domain(doc, binary)

    def test_shared_mesh_checked_against_each_skin(self):
        doc, binary = fixture()
        # One mesh, two owners, same valid skin: each owner is checked.
        doc['nodes'].append({'mesh': 0, 'skin': 0})
        doc['scenes'][0]['nodes'].append(2)
        result = qualify_input_domain(doc, binary)
        self.assertEqual(result['skinned_owners'], 2)

    def test_primitive_and_channel_caps_precede_parent(self):
        for mode in ('primitive', 'channel'):
            doc, binary = fixture()
            if mode == 'primitive': doc['meshes'][0]['primitives'] *= 6
            else: doc['animations'][0]['channels'] *= 6
            with patch('input_domain.MAX_EDGES', 5), patch.object(Snapshot, 'canonical', side_effect=AssertionError('Must not decode')):
                with self.assertRaisesRegex(Refusal, 'Preflight .*entry bound'): qualify_input_domain(doc, binary)


if __name__ == '__main__':
    unittest.main(verbosity=2)
