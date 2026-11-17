"""Synthetic dictionaries and immutable BIN bytes in RAM only; no GLB file generation."""
import copy
import math
import struct
import unittest

from semantic_compare import CARRIER, Refusal, Snapshot, compare_non_normal, freeze, parse_json_document


def fixture():
    binary = bytearray()
    document = {'asset': {'version': '2.0', 'generator': 'synthetic CPU fixture'}, 'buffers': [{}],
                'bufferViews': [], 'accessors': [], 'scene': 0, 'scenes': [{'nodes': [0]}],
                'nodes': [{'mesh': 0, 'skin': 0, 'children': [1], 'name': 'figure'}, {'name': 'joint'}],
                'skins': [{'joints': [1], 'skeleton': 1}], 'meshes': [{'primitives': [{}], 'weights': [0.0]}],
                'materials': [{'pbrMetallicRoughness': {'baseColorFactor': [1.0, 1.0, 1.0, 1.0],
                               'baseColorTexture': {'index': 0}, 'metallicFactor': 0.0, 'roughnessFactor': 1.0},
                               'extras': {'owner': True}}],
                'textures': [{'source': 0, 'sampler': 0}], 'samplers': [{'magFilter': 9729}],
                'images': [], 'animations': [{'samplers': [{}], 'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}}]}],
                'extras': {'authored': True, 'zero': -0.0, 'integer': 1, 'float': 1.0,
                           'source_units': 'preserved', 'six_foot_policy': 'inactive'}}

    def view(payload, target=None):
        binary.extend(b'\0' * (-len(binary) % 4))
        result = len(document['bufferViews'])
        desc = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(payload)}
        if target is not None: desc['target'] = target
        document['bufferViews'].append(desc); binary.extend(payload)
        return result

    def accessor(name, values, kind, component=5126, target=34962, **extra):
        code = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[component]
        arity = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[kind]
        index = len(document['accessors'])
        document['accessors'].append(dict(name=name, bufferView=view(struct.pack('<' + code * len(values), *values), target),
                                         componentType=component, count=len(values) // arity, type=kind, **extra))
        return index

    attrs = {'POSITION': accessor('position', [0, 0, 0, 1, 0, 0, 0, 1, 0], 'VEC3', min=[0.0, 0.0, 0.0], max=[1.0, 1.0, 0.0]),
             'NORMAL': accessor('normal', [0, 0, 1] * 3, 'VEC3'),
             'TEXCOORD_0': accessor('uv', [0, 0, 1, 0, 0, 1], 'VEC2'),
             'COLOR_0': accessor('color', [255, 128, 64, 255] * 3, 'VEC4', component=5121, normalized=True),
             'JOINTS_0': accessor('joints', [0, 0, 0, 0] * 3, 'VEC4', component=5121),
             'WEIGHTS_0': accessor('weights', [1, 0, 0, 0] * 3, 'VEC4')}
    primitive = document['meshes'][0]['primitives'][0]
    primitive.update(attributes=attrs, indices=accessor('topology', [0, 1, 2], 'SCALAR', component=5123, target=34963), material=0, mode=4,
                     targets=[{'POSITION': accessor('position morph', [.1, 0, 0] * 3, 'VEC3')}])
    document['skins'][0]['inverseBindMatrices'] = accessor('bind', [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], 'MAT4', target=None)
    document['animations'][0]['samplers'][0].update(input=accessor('time', [0, 1], 'SCALAR', target=None, min=[0.0], max=[1.0]),
                                                  output=accessor('motion', [0, 0, 0, 1, 2, 3], 'VEC3', target=None), interpolation='LINEAR')
    document['images'].append({'bufferView': view(b'\x89PNG\r\n\x1a\nsynthetic encoded bytes'), 'mimeType': 'image/png', 'name': 'synthetic image'})
    document['buffers'][0]['byteLength'] = len(binary)
    return document, bytes(binary)


def carrier_and_relayout(document, original_binary):
    """Independent synthetic layout producer: reverse accessor order and repack each channel."""
    document = copy.deepcopy(document); original_binary = bytearray(original_binary)
    original_binary.extend(b'\0' * (-len(original_binary) % 4)); at = len(original_binary)
    original_binary.extend(struct.pack('<3f', 1, 2, 3))
    view_id = len(document['bufferViews']); document['bufferViews'].append({'buffer': 0, 'byteOffset': at, 'byteLength': 12, 'target': 34962})
    carrier_id = len(document['accessors']); document['accessors'].append({'bufferView': view_id, 'componentType': 5126, 'count': 3, 'type': 'SCALAR'})
    document['meshes'][0]['primitives'][0]['attributes'][CARRIER] = carrier_id
    old = copy.deepcopy(document); binary = bytearray(b'RELAYOUT-GAP')
    document['accessors'] = []; document['bufferViews'] = []; mapping = {}

    def append_view(payload, metadata):
        binary.extend(b'\0' * (-len(binary) % 4)); offset = len(binary); binary.extend(payload)
        index = len(document['bufferViews'])
        document['bufferViews'].append(dict(metadata, buffer=0, byteOffset=offset, byteLength=len(payload)))
        return index

    for old_id in reversed(range(len(old['accessors']))):
        source = old['accessors'][old_id]; view = old['bufferViews'][source['bufferView']]
        arity = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[source['type']]
        size = {5121: 1, 5123: 2, 5125: 4, 5126: 4}[source['componentType']] * arity
        start = view.get('byteOffset', 0) + source.get('byteOffset', 0); stride = view.get('byteStride', size)
        payload = b''.join(original_binary[start + i * stride:start + i * stride + size] for i in range(source['count']))
        view_meta = {k: v for k, v in view.items() if k not in {'buffer', 'byteOffset', 'byteLength', 'byteStride'}}
        desc = {k: v for k, v in source.items() if k not in {'bufferView', 'byteOffset'}}
        desc['bufferView'] = append_view(payload, view_meta)
        mapping[old_id] = len(document['accessors']); document['accessors'].append(desc)
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {key: mapping[value] for key, value in primitive['attributes'].items()}
            primitive['indices'] = mapping[primitive['indices']]
            for target in primitive.get('targets', []):
                for key in target: target[key] = mapping[target[key]]
    for skin in document['skins']: skin['inverseBindMatrices'] = mapping[skin['inverseBindMatrices']]
    for animation in document['animations']:
        for sampler in animation['samplers']:
            for key in ('input', 'output'): sampler[key] = mapping[sampler[key]]
    for image in document['images']:
        view = old['bufferViews'][image['bufferView']]; start = view.get('byteOffset', 0)
        image['bufferView'] = append_view(bytes(original_binary[start:start + view['byteLength']]), {k: v for k, v in view.items() if k not in {'buffer', 'byteOffset', 'byteLength'}})
    document['buffers'][0]['byteLength'] = len(binary)
    return document, bytes(binary)


def change_component(document, binary, semantic, replacement, target=False):
    document = copy.deepcopy(document); binary = bytearray(binary)
    primitive = document['meshes'][0]['primitives'][0]
    index = primitive['targets'][0][semantic] if target else primitive['attributes'][semantic]
    accessor = document['accessors'][index]; view = document['bufferViews'][accessor['bufferView']]
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    binary[offset:offset + len(replacement)] = replacement
    return document, bytes(binary)


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.before = fixture(); self.after = carrier_and_relayout(*self.before)

    def compare(self, after=None): return compare_non_normal(*self.before, *(after or self.after))

    def test_relayout_accepts_exact_channels_and_preserves_inputs(self):
        original = copy.deepcopy((self.before, self.after)); result = self.compare()
        self.assertTrue(result['passed']); self.assertEqual(result['primitives'], 1)
        self.assertFalse(result['normal_fidelity_qualified']); self.assertFalse(result['native_carrier_correspondence_qualified'])
        self.assertEqual((self.before, self.after), original)

    def test_interleaved_to_packed_components_accept(self):
        doc, blob = copy.deepcopy(self.before[0]), bytearray(self.before[1])
        attrs = doc['meshes'][0]['primitives'][0]['attributes']; position = doc['accessors'][attrs['POSITION']]; uv = doc['accessors'][attrs['TEXCOORD_0']]
        old_views = doc['bufferViews']; pview = old_views[position['bufferView']]; uview = old_views[uv['bufferView']]
        payload = b''.join(blob[pview['byteOffset'] + i * 12:pview['byteOffset'] + i * 12 + 12] + blob[uview['byteOffset'] + i * 8:uview['byteOffset'] + i * 8 + 8] for i in range(3))
        # Keep the old UV view referenced by POSITION and vice versa to avoid unused table entries.
        blob.extend(b'\0' * (-len(blob) % 4)); offset = len(blob); blob.extend(payload)
        for desc in (pview, uview): desc.update(byteOffset=offset, byteLength=len(payload), byteStride=20)
        position['byteOffset'] = 0; uv['byteOffset'] = 12
        doc['buffers'][0]['byteLength'] = len(blob)
        before = doc, bytes(blob); after = carrier_and_relayout(*before)
        self.assertTrue(compare_non_normal(*before, *after)['passed'])

    def test_normal_words_change_is_explicitly_unqualified(self):
        after = change_component(*self.after, 'NORMAL', struct.pack('<f', .0001))
        result = self.compare(after); self.assertNotEqual(result['before_normal_component_SHA256'], result['after_normal_component_SHA256'])
        self.assertFalse(result['NORMAL_payload_and_minmax_comparison_performed'])

    def test_position_UV_color_joints_weights_component_mutations_refuse(self):
        for semantic in ('POSITION', 'TEXCOORD_0', 'COLOR_0', 'JOINTS_0', 'WEIGHTS_0'):
            with self.subTest(semantic=semantic), self.assertRaises(Refusal):
                self.compare(change_component(*self.after, semantic, b'\x01'))

    def test_position_signed_zero_word_mutation_refuses(self):
        with self.assertRaises(Refusal): self.compare(change_component(*self.after, 'POSITION', struct.pack('<I', 0x80000000)))

    def test_position_morph_mutation_refuses(self):
        with self.assertRaises(Refusal): self.compare(change_component(*self.after, 'POSITION', struct.pack('<f', .2), target=True))

    def test_topology_order_mutation_refuses(self):
        doc, blob = copy.deepcopy(self.after[0]), bytearray(self.after[1]); a = doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']]; at = doc['bufferViews'][a['bufferView']]['byteOffset']; blob[at:at + 6] = struct.pack('<3H', 0, 2, 1)
        with self.assertRaises(Refusal): self.compare((doc, bytes(blob)))

    def test_bind_and_animation_bytes_refuse(self):
        for accessor_id in [self.after[0]['skins'][0]['inverseBindMatrices'], self.after[0]['animations'][0]['samplers'][0]['input'], self.after[0]['animations'][0]['samplers'][0]['output']]:
            doc, blob = copy.deepcopy(self.after[0]), bytearray(self.after[1]); at = doc['bufferViews'][doc['accessors'][accessor_id]['bufferView']]['byteOffset']; blob[at:at + 4] = struct.pack('<f', .25)
            with self.assertRaises(Refusal): self.compare((doc, bytes(blob)))

    def test_encoded_image_byte_mutation_refuses(self):
        doc, blob = copy.deepcopy(self.after[0]), bytearray(self.after[1]); at = doc['bufferViews'][doc['images'][0]['bufferView']]['byteOffset']; blob[at] ^= 1
        with self.assertRaises(Refusal): self.compare((doc, bytes(blob)))

    def test_metadata_types_and_signed_zero_refuse(self):
        for key, value in [('authored', 1), ('integer', 1.0), ('float', 1), ('zero', 0.0)]:
            doc = copy.deepcopy(self.after[0]); doc['extras'][key] = value
            with self.subTest(key=key), self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_minmax_or_accessor_metadata_change_refuses(self):
        for change in (lambda a: a['min'].__setitem__(0, 0), lambda a: a.update(name='changed'), lambda a: a.update(normalized=False)):
            doc = copy.deepcopy(self.after[0]); a = doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['POSITION']]; change(a)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_node_material_skin_animation_metadata_change_refuses(self):
        changes = [lambda d: d['nodes'][0].update(name='other'), lambda d: d['skins'][0].update(extras={'new': True}),
                   lambda d: d['materials'][0]['extras'].update(owner=1), lambda d: d['animations'][0]['samplers'][0].update(interpolation='STEP')]
        for change in changes:
            doc = copy.deepcopy(self.after[0]); change(doc)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_bool_and_float_accessor_view_and_other_indexes_refuse(self):
        changes = [lambda d: d['meshes'][0]['primitives'][0]['attributes'].update(POSITION=True),
                   lambda d: d['meshes'][0]['primitives'][0].update(indices=1.0),
                   lambda d: d['accessors'][0].update(bufferView=True), lambda d: d['bufferViews'][0].update(buffer=False),
                   lambda d: d['nodes'][0].update(mesh=False), lambda d: d['textures'][0].update(source=False),
                   lambda d: d['animations'][0]['channels'][0].update(sampler=False)]
        for change in changes:
            doc = copy.deepcopy(self.after[0]); change(doc)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_unknown_extensions_sparse_and_compression_refuse(self):
        changes = [lambda d: d.update(extensionsUsed=['EXT_meshopt_compression']),
                   lambda d: d['bufferViews'][0].update(extensions={'UNKNOWN_accessor_reference': {'accessor': 0}}),
                   lambda d: d['accessors'][0].update(sparse={}),
                   lambda d: d['meshes'][0]['primitives'][0].update(extensions={'KHR_draco_mesh_compression': {}})]
        for change in changes:
            doc = copy.deepcopy(self.after[0]); change(doc)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_unknown_accessor_view_fields_refuse(self):
        for table in ('accessors', 'bufferViews'):
            doc = copy.deepcopy(self.after[0]); doc[table][0]['newReference'] = 0
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_range_stride_and_component_types_refuse(self):
        changes = [lambda d: d['accessors'][0].update(count=True), lambda d: d['accessors'][0].update(byteOffset=-1),
                   lambda d: d['accessors'][0].update(componentType=5130), lambda d: d['accessors'][0].update(type='MAT3'),
                   lambda d: d['bufferViews'][0].update(byteStride=3), lambda d: d['bufferViews'][0].update(byteLength=1)]
        for change in changes:
            doc = copy.deepcopy(self.after[0]); change(doc)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_unreferenced_accessor_view_or_external_image_refuses(self):
        changes = [lambda d: d['accessors'].append(copy.deepcopy(d['accessors'][0])), lambda d: d['bufferViews'].append(copy.deepcopy(d['bufferViews'][0])),
                   lambda d: d['images'][0].update(uri='private.png')]
        for change in changes:
            doc = copy.deepcopy(self.after[0]); change(doc)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_missing_or_case_colliding_carrier_refuses(self):
        for key in ('missing', CARRIER.lower()):
            doc = copy.deepcopy(self.after[0]); attrs = doc['meshes'][0]['primitives'][0]['attributes']; index = attrs.pop(CARRIER)
            if key != 'missing': attrs[key] = index
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_nonfinite_JSON_and_F32_refuse(self):
        doc = copy.deepcopy(self.after[0]); doc['extras']['nonfinite'] = math.nan
        with self.assertRaises(Refusal): self.compare((doc, self.after[1]))
        with self.assertRaises(Refusal): self.compare(change_component(*self.after, 'NORMAL', struct.pack('<I', 0x7fc00000)))

    def test_allowed_unlit_and_texture_transform_preserved(self):
        doc = copy.deepcopy(self.before[0]); doc['extensionsUsed'] = ['KHR_materials_unlit', 'KHR_texture_transform']; mat = doc['materials'][0]
        mat['extensions'] = {'KHR_materials_unlit': {}}; mat['pbrMetallicRoughness']['baseColorTexture']['extensions'] = {'KHR_texture_transform': {'offset': [0.0, 0.0], 'texCoord': 0}}
        before = doc, self.before[1]; after = carrier_and_relayout(*before)
        self.assertTrue(compare_non_normal(*before, *after)['passed'])

    def test_malformed_core_lists_sampler_and_matrix_profile_refuse(self):
        changes = [lambda d: d['scenes'][0].update(nodes=False), lambda d: d['nodes'][0].update(children=0),
                   lambda d: d['meshes'][0]['primitives'][0].update(targets={}),
                   lambda d: d['samplers'][0].update(magFilter=True), lambda d: d['samplers'][0].update(unknownAccessor=0),
                   lambda d: d['nodes'][0].update(matrix=[1.0] * 16, translation=[0.0] * 3)]
        for change in changes:
            doc = copy.deepcopy(self.after[0]); change(doc)
            with self.assertRaises(Refusal): self.compare((doc, self.after[1]))

    def test_allowed_custom_attribute_and_tangent_are_preserved(self):
        doc = copy.deepcopy(self.before[0]); attrs = doc['meshes'][0]['primitives'][0]['attributes']
        attrs['_AUTHORED_DATA'] = attrs['TEXCOORD_0']
        # Reuse same complete VEC4 float components solely to exercise exact tangent transport.
        attrs['TANGENT'] = attrs['WEIGHTS_0']
        before = doc, self.before[1]; after = carrier_and_relayout(*before)
        self.assertTrue(compare_non_normal(*before, *after)['passed'])

    def test_full_carrier_permutation_is_not_a_correspondence_proof(self):
        doc, blob = copy.deepcopy(self.after[0]), bytearray(self.after[1]); index = doc['meshes'][0]['primitives'][0]['attributes'][CARRIER]
        at = doc['bufferViews'][doc['accessors'][index]['bufferView']]['byteOffset']; blob[at:at + 12] = struct.pack('<3f', 3, 2, 1)
        result = self.compare((doc, bytes(blob)))
        self.assertTrue(result['passed']); self.assertFalse(result['native_carrier_correspondence_qualified'])

    def test_normal_minmax_is_explicit_separate_gate(self):
        doc = copy.deepcopy(self.after[0]); index = doc['meshes'][0]['primitives'][0]['attributes']['NORMAL']
        doc['accessors'][index].update(min=[0.0, 0.0, .9], max=[.1, .1, 1.0])
        result = self.compare((doc, self.after[1])); self.assertFalse(result['NORMAL_payload_and_minmax_comparison_performed'])

    def test_strict_JSON_reader_rejects_duplicate_nonfinite_and_integer_negative_zero(self):
        for raw in (b'{"same":1,"same":2}', b'{"bad":NaN}', b'{"bad":1e999}', b'{"ambiguous":-0}'):
            with self.assertRaises(Refusal): parse_json_document(raw)
        self.assertNotEqual(freeze(parse_json_document(b'{"zero":-0.0}')), freeze(parse_json_document(b'{"zero":0.0}')))
        self.assertNotEqual(freeze(parse_json_document(b'{"value":1}')), freeze(parse_json_document(b'{"value":1e0}')))

    def test_view_buffer_and_image_metadata_are_typed_and_exact(self):
        doc = copy.deepcopy(self.before[0]); index = doc['meshes'][0]['primitives'][0]['attributes']['POSITION']
        doc['bufferViews'][doc['accessors'][index]['bufferView']]['extras'] = {'owner': True}
        doc['buffers'][0]['extras'] = {'owner': True}
        before = doc, self.before[1]; after = carrier_and_relayout(*before)
        self.assertTrue(compare_non_normal(*before, *after)['passed'])
        for table in ('bufferViews', 'buffers', 'images'):
            changed = copy.deepcopy(after[0])
            if table == 'bufferViews':
                index = changed['meshes'][0]['primitives'][0]['attributes']['POSITION']; view = changed['accessors'][index]['bufferView']; changed['bufferViews'][view]['extras']['owner'] = 1
            elif table == 'buffers': changed['buffers'][0]['extras']['owner'] = 1
            else: changed['images'][0]['mimeType'] = 'image/jpeg'
            with self.assertRaises(Refusal): compare_non_normal(*before, changed, after[1])


if __name__ == '__main__': unittest.main(verbosity=2)
