"""RAM-only synthetic object/cache/GLB observations; no installed code execution."""
import copy
import hashlib
import json
import struct
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np

from gather_binding import GatherBinding, read_glb


def pack(doc, binary):
    raw = json.dumps(doc, separators=(',', ':')).encode()
    raw += b' ' * (-len(raw) % 4)
    binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(raw) + len(binary))
            + struct.pack('<I4s', len(raw), b'JSON') + raw
            + struct.pack('<I4s', len(binary), b'BIN\0') + binary)


def pin(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture(observe=True, gather=True, final=True):
    slots = [object(), object()]
    materials = [object(), object()]
    owners = [NS(name='same_name'), NS(name='same_name')]
    meshes = [NS(name='same_mesh_name'), NS(name='same_mesh_name')]
    admissions = [dict(object=owners[i], mesh=meshes[i], joined_source_ids=list(range(i * 6, i * 6 + 6)),
                       material_slots=slots, primitive_count=2) for i in range(2)]
    ledger = GatherBinding(admissions)
    doc = dict(asset={'version': '2.0'}, buffers=[{}], bufferViews=[], accessors=[],
               meshes=[{}, {}], materials=[{}, {}])
    binary = bytearray()

    def accessor(values, kind, component):
        binary.extend(b'\0' * (-len(binary) % 4))
        code = {5123: 'H', 5126: 'f'}[component]
        payload = struct.pack('<' + code * len(values), *values)
        vi = len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0, byteOffset=len(binary), byteLength=len(payload)))
        binary.extend(payload)
        ai = len(doc['accessors'])
        doc['accessors'].append(dict(bufferView=vi, componentType=component, count=len(values) // {'SCALAR': 1, 'VEC3': 3}[kind], type=kind))
        return ai

    cases = []
    for oi in range(2):
        creator = NS(blender_object=owners[oi], blender_mesh=meshes[oi])
        internals = []; primitives = []; final_refs = []
        for pi in range(2):
            if observe: ledger.observe_creator(creator, 'not_shared', [pi * 3, pi * 3 + 1, pi * 3 + 2], pi, [2, 0, 1], pi)
            refs = {'POSITION': accessor([0., 0., 0., 1., 0., 0., 0., 1., 0.], 'VEC3', 5126),
                    'NORMAL': accessor([0., 0., 1.] * 3, 'VEC3', 5126),
                    '_HAS_NATIVE_NORMAL_ID': accessor([float(oi * 6 + pi * 3 + k + 1) for k in range(3)], 'SCALAR', 5126)}
            indices = accessor([2, 0, 1], 'SCALAR', 5123)
            attrs = {name: object() for name in refs}; source_indices = object()
            internals.append(dict(material=pi, attributes=attrs, indices=source_indices))
            primitives.append(NS(attributes=attrs, indices=source_indices, material=materials[pi], mode=None,
                                 targets=None, extensions=None, extras=None))
            final_refs.append((refs, indices))
        mesh = NS(primitives=primitives)
        if gather: ledger.bind_gather(creator, slots, internals, primitives, mesh)
        cases.append(dict(creator=creator, internals=internals, primitives=primitives, mesh=mesh, final_refs=final_refs))
    if final:
        ledger.record_material_reference(materials[0], 1)
        ledger.record_material_reference(materials[1], 0)
        for oi in (1, 0):  # Actual final Mesh order intentionally differs from creation.
            case = cases[oi]
            for pi, (primitive, (refs, indices)) in enumerate(zip(case['primitives'], case['final_refs'])):
                primitive.attributes.update(refs); primitive.indices = indices; primitive.material = 1 - pi
            ledger.record_mesh_reference(case['mesh'], 1 - oi)
            doc['meshes'][1 - oi] = {'primitives': [dict(attributes=copy.deepcopy(p.attributes), indices=p.indices, material=p.material)
                                                  for p in case['primitives']]}
    doc['buffers'][0]['byteLength'] = len(binary)
    return NS(ledger=ledger, cases=cases, slots=slots, materials=materials, owners=owners, meshes=meshes,
              admissions=admissions, doc=doc, binary=bytes(binary), raw=pack(doc, bytes(binary)))


class BindingTests(unittest.TestCase):
    def test_exact_actual_reference_indices_override_creation_and_names(self):
        f = fixture(); relation, report = f.ledger.finalize(f.raw, pin(f.raw))
        self.assertEqual(relation, {(0, 0): (7, 8, 9), (0, 1): (10, 11, 12), (1, 0): (1, 2, 3), (1, 1): (4, 5, 6)})
        self.assertEqual((report['meshes'], report['primitives'], report['source_ids']), (2, 4, 12))
        for name in ('carrier_values_used_for_identity', 'names_used_for_identity', 'actual_hooks_observed',
                     'actual_native_GLTF_binding_qualified', 'independent_input_domain_qualified',
                     'native_normal_fidelity_qualified', 'adoption_qualified'):
            self.assertIs(report[name], False)

    def test_carrier_permutation_never_selects_relation_or_qualifies_native_binding(self):
        f = fixture(); binary = bytearray(f.binary)
        for mesh in f.doc['meshes']:
            for primitive in mesh['primitives']:
                a = f.doc['accessors'][primitive['attributes']['_HAS_NATIVE_NORMAL_ID']]
                start = f.doc['bufferViews'][a['bufferView']]['byteOffset']
                binary[start:start + 12] = struct.pack('<3f', 3., 1., 2.)
        changed = pack(f.doc, bytes(binary))
        self.assertEqual(f.ledger.finalize(changed, pin(changed))[0], f.ledger.finalize(f.raw, pin(f.raw))[0])

    def test_fake_same_name_object_or_evaluated_mesh_refuses(self):
        f = fixture(observe=False, gather=False, final=False)
        for creator in (NS(blender_object=NS(name='same_name'), blender_mesh=f.meshes[0]),
                        NS(blender_object=f.owners[0], blender_mesh=NS(name='same_mesh_name'))):
            with self.assertRaises(ValueError): f.ledger.observe_creator(creator, 'not_shared', [0, 1, 2], 0, [2, 0, 1], 0)

    def test_alias_admissions_source_overlap_and_type_substitution_refuse(self):
        f = fixture()
        for key, value in [('object', f.owners[0]), ('mesh', f.meshes[0]), ('joined_source_ids', [0, 1, 2, 3, 4, 5]), ('primitive_count', True)]:
            rows = [dict(row) for row in f.admissions]; rows[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): GatherBinding(rows)

    def test_shared_branch_wrong_ordinal_and_numeric_coercion_refuse(self):
        for changes in [('shared', [0, 1, 2], 0, [2, 0, 1], 0),
                        ('not_shared', [0, 1, 2], 0, [2, 0, 1], 1),
                        ('not_shared', [False, 1, 2], 0, [2, 0, 1], 0),
                        ('not_shared', [0., 1, 2], 0, [2, 0, 1], 0),
                        ('not_shared', [0, 0, 2], 0, [2, 0, 1], 0),
                        ('not_shared', [0, 1, 2], True, [2, 0, 1], 0),
                        ('not_shared', [0, 1, 2], 0, [3, 0, 1], 0)]:
            f = fixture(observe=False, gather=False, final=False)
            with self.subTest(changes=changes), self.assertRaises(ValueError): f.ledger.observe_creator(f.cases[0]['creator'], *changes)

    def test_missing_observer_cold_cache_hit_and_duplicate_creator_refuse(self):
        f = fixture(observe=False, gather=False, final=False); c = f.cases[0]
        with self.assertRaises(ValueError): f.ledger.bind_gather(c['creator'], f.slots, c['internals'], c['primitives'], c['mesh'])
        f = fixture(gather=False, final=False); c = f.cases[0]
        other = NS(blender_object=f.owners[0], blender_mesh=f.meshes[0])
        with self.assertRaises(ValueError): f.ledger.observe_creator(other, 'not_shared', [0, 1, 2], 0, [2, 0, 1], 0)
        f.ledger.bind_gather(c['creator'], f.slots, c['internals'], c['primitives'], c['mesh'])
        with self.assertRaises(ValueError): f.ledger.bind_gather(c['creator'], f.slots, c['internals'], c['primitives'], c['mesh'])

    def test_source_material_order_and_internal_gather_storage_identity_refuse(self):
        for change in ('slots', 'material', 'attributes', 'indices', 'primitive_reuse', 'mesh_list'):
            f = fixture(gather=False, final=False); c = f.cases[0]; slots = f.slots
            if change == 'slots': slots = list(reversed(slots))
            if change == 'material': c['internals'][0]['material'] = 1
            if change == 'attributes': c['internals'][0]['attributes'] = dict(c['primitives'][0].attributes)
            if change == 'indices': c['internals'][0]['indices'] = object()
            if change == 'primitive_reuse': c['primitives'][1] = c['primitives'][0]
            if change == 'mesh_list': c['mesh'].primitives = list(c['primitives'])
            with self.subTest(change=change), self.assertRaises(ValueError): f.ledger.bind_gather(c['creator'], slots, c['internals'], c['primitives'], c['mesh'])

    def test_authentic_numpy_uint32_cached_slots_pass_without_mutation_or_substitution(self):
        f = fixture(gather=False, final=False)
        for case in f.cases:
            for pi, row in enumerate(case['internals']): row['material'] = np.uint32(pi)
            originals = [(row, row['material'], row['attributes'], row['indices']) for row in case['internals']]
            f.ledger.bind_gather(case['creator'], f.slots, case['internals'], case['primitives'], case['mesh'])
            for current, (row, scalar, attributes, indices) in zip(case['internals'], originals):
                self.assertIs(current, row); self.assertIs(current['material'], scalar)
                self.assertIs(current['attributes'], attributes); self.assertIs(current['indices'], indices)

    def test_cached_numpy_float_boolean_wrong_width_and_array_slots_refuse(self):
        for value in (True, 0., np.float32(0), np.bool_(False), np.uint64(0), np.int32(0), np.array([0], dtype=np.uint32)):
            f = fixture(gather=False, final=False); case = f.cases[0]; case['internals'][0]['material'] = value
            with self.subTest(type=type(value)), self.assertRaises(ValueError):
                f.ledger.bind_gather(case['creator'], f.slots, case['internals'], case['primitives'], case['mesh'])

    def test_final_reference_events_require_exact_objects_and_indices(self):
        f = fixture(final=False)
        with self.assertRaises(ValueError): f.ledger.record_material_reference(object(), 0)
        with self.assertRaises(ValueError): f.ledger.record_mesh_reference(NS(primitives=f.cases[0]['primitives']), 0)
        with self.assertRaises(ValueError): f.ledger.record_material_reference(f.materials[0], True)
        f.ledger.record_material_reference(f.materials[0], 0)
        with self.assertRaises(ValueError): f.ledger.record_material_reference(f.materials[1], 0)
        with self.assertRaises(ValueError): f.ledger.finalize(f.raw, pin(f.raw))

    def test_cross_object_internal_cache_and_attribute_aliases_refuse(self):
        for change in ('internal', 'attributes'):
            f = fixture(gather=False, final=False); first, second = f.cases
            f.ledger.bind_gather(first['creator'], f.slots, first['internals'], first['primitives'], first['mesh'])
            if change == 'internal':
                second['internals'][0] = first['internals'][0]
                second['primitives'][0].attributes = first['primitives'][0].attributes
                second['primitives'][0].indices = first['primitives'][0].indices
            else:
                second['internals'][0]['attributes'] = first['primitives'][0].attributes
                second['primitives'][0].attributes = first['primitives'][0].attributes
            with self.subTest(change=change), self.assertRaises(ValueError):
                f.ledger.bind_gather(second['creator'], f.slots, second['internals'], second['primitives'], second['mesh'])

    def test_reordered_final_object_primitives_and_wrong_material_refuse(self):
        for change in ('order', 'material'):
            f = fixture(final=False); c = f.cases[0]
            f.ledger.record_material_reference(f.materials[0], 1); f.ledger.record_material_reference(f.materials[1], 0)
            for pi, (p, (refs, indices)) in enumerate(zip(c['primitives'], c['final_refs'])):
                p.attributes.update(refs); p.indices = indices; p.material = 1 - pi
            if change == 'order': c['mesh'].primitives.reverse()
            else: c['primitives'][0].material = 0
            with self.subTest(change=change), self.assertRaises(ValueError): f.ledger.record_mesh_reference(c['mesh'], 0)

    def test_serialized_mesh_primitive_material_or_accessor_substitution_refuses(self):
        for change in ('meshes', 'primitives', 'material', 'indices', 'missing_carrier'):
            f = fixture(); d = copy.deepcopy(f.doc)
            if change == 'meshes': d['meshes'].reverse()
            if change == 'primitives': d['meshes'][0]['primitives'].reverse()
            if change == 'material': d['meshes'][0]['primitives'][0]['material'] = 0
            if change == 'indices': d['meshes'][0]['primitives'][0]['indices'] = d['meshes'][0]['primitives'][1]['indices']
            if change == 'missing_carrier': del d['meshes'][0]['primitives'][0]['attributes']['_HAS_NATIVE_NORMAL_ID']
            raw = pack(d, f.binary)
            with self.subTest(change=change), self.assertRaises(ValueError): f.ledger.finalize(raw, pin(raw))

    def test_decoded_topology_and_accessor_count_type_or_range_refuse(self):
        for change in ('topology', 'count', 'float_count', 'stride', 'component'):
            f = fixture(); d = copy.deepcopy(f.doc); b = bytearray(f.binary)
            ai = d['meshes'][0]['primitives'][0]['indices']; a = d['accessors'][ai]; view = d['bufferViews'][a['bufferView']]
            if change == 'topology': b[view['byteOffset']:view['byteOffset'] + 6] = struct.pack('<3H', 0, 2, 1)
            if change == 'count': a['count'] = 6
            if change == 'float_count': a['count'] = 3.0
            if change == 'stride': view['byteStride'] = 8
            if change == 'component': a['componentType'] = 5126
            raw = pack(d, bytes(b))
            with self.subTest(change=change), self.assertRaises(ValueError): f.ledger.finalize(raw, pin(raw))

    def test_pinned_bytes_strict_json_chunks_and_bin_padding_refuse(self):
        f = fixture()
        with self.assertRaises(ValueError): f.ledger.finalize(f.raw, '0' * 64)
        size = struct.unpack_from('<I', f.raw, 12)[0]
        text = f.raw[20:20 + size].rstrip()
        for changed in (text.replace(b'"version":"2.0"', b'"version":"2.0","version":"2.0"'),
                        text.replace(b'"componentType":5126', b'"componentType":-0', 1)):
            changed += b' ' * (-len(changed) % 4)
            raw = struct.pack('<4sII', b'glTF', 2, 28 + len(changed) + len(f.binary)) + struct.pack('<I4s', len(changed), b'JSON') + changed + struct.pack('<I4s', len(f.binary), b'BIN\0') + f.binary
            with self.assertRaises(ValueError): f.ledger.finalize(raw, pin(raw))
        with self.assertRaises(ValueError): read_glb(f.raw + b'extra')

    def test_global_coverage_and_early_byte_table_budgets_refuse(self):
        f = fixture(); f.ledger.entries[0]['rows'][1]['ids'] = (1, 2, 3)
        with self.assertRaises(ValueError): f.ledger.finalize(f.raw, pin(f.raw))
        f = fixture()
        with patch('gather_binding.MAX_GLB', len(f.raw) - 1), self.assertRaises(ValueError): f.ledger.finalize(f.raw, pin(f.raw))
        with patch('gather_binding.MAX_TABLE', 1), self.assertRaises(ValueError): f.ledger.finalize(f.raw, pin(f.raw))
        f = fixture(observe=False, gather=False, final=False)
        with patch('gather_binding.MAX_CORNERS', 2), self.assertRaises(ValueError):
            f.ledger.observe_creator(f.cases[0]['creator'], 'not_shared', [0, 1, 2], 0, [0, 1, 2], 0)


if __name__ == '__main__':
    unittest.main()
