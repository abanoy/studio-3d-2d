"""Independent final-serialized extension absence tests; no Blender/native input.

Synthetic GLB JSON is encoded/parsed independently before the resource invariant.
The old resource positive fixture supplies actual fake hook/reference coverage;
other tests here do not authenticate runtime SDK classes or claim export success.
"""
import copy
import json
import struct
import unittest

import export_hook_proposal as H
import resource_gate_proposal as R
import test_empty_material_extensions as E


OBSERVED_EMPTY_NAMES = (
    'KHR_materials_anisotropy', 'KHR_materials_clearcoat',
    'KHR_materials_emissive_strength', 'KHR_materials_ior',
    'KHR_materials_specular', 'KHR_materials_transmission',
)


def parsed_glb(document):
    """One literal synthetic GLB JSON chunk, not an exporter or source asset."""
    encoded = json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf8')
    encoded += b' ' * ((-len(encoded)) % 4)
    raw = struct.pack('<4sII', b'glTF', 2, 20 + len(encoded))
    raw += struct.pack('<I4s', len(encoded), b'JSON') + encoded
    magic, version, count = struct.unpack_from('<4sII', raw)
    length, kind = struct.unpack_from('<I4s', raw, 12)
    if magic != b'glTF' or version != 2 or count != len(raw) or kind != b'JSON' or length + 20 != count:
        raise AssertionError('Synthetic GLB framing differs')
    return json.loads(raw[20:20 + length])


def assert_final(document):
    # The invariant itself is independent of runtime profile admission.
    return R.SimplePackedResources._assert_no_serialized_material_extensions(None, document)


class FinalMaterialExtensionTests(unittest.TestCase):
    def test_absent_extensions_pass_parsed_glb_and_leave_all_material_values_unchanged(self):
        document = parsed_glb(dict(asset=dict(version='2.0'), materials=[
            dict(pbrMetallicRoughness=dict(baseColorFactor=[.2, .3, .4, 1.0], metallicFactor=0.0)),
            dict(alphaMode='BLEND', doubleSided=True)]))
        before = copy.deepcopy(document)
        self.assertIsNone(assert_final(document))
        self.assertEqual(document, before)

    def test_exact_empty_final_extension_containers_are_allowed(self):
        document = parsed_glb(dict(materials=[dict(extensions={}), {}], extensions={},
                                  extensionsUsed=[], extensionsRequired=[]))
        before = copy.deepcopy(document)
        self.assertIsNone(assert_final(document))
        self.assertEqual(document, before)

    def test_each_observed_known_empty_token_must_be_gone_from_serialized_materials(self):
        for name in OBSERVED_EMPTY_NAMES:
            with self.subTest(name=name):
                document = parsed_glb(dict(materials=[dict(extensions={name: {}})]))
                with self.assertRaisesRegex(H.Refusal, '^final_material_extensions_not_absent$'):
                    assert_final(document)
                self.assertEqual(document['materials'][0]['extensions'], {name: {}})

    def test_unknown_empty_material_token_is_never_an_absence(self):
        document = parsed_glb(dict(materials=[dict(extensions={'KHR_unknown_extension': {}})]))
        with self.assertRaisesRegex(H.Refusal, '^final_material_extensions_not_absent$'):
            assert_final(document)

    def test_nonempty_known_material_payload_is_never_pruned_or_repaired(self):
        for payload in ({'ior': 1.45}, {'ior': None}, {'texture': {'index': 0}}, [], None, 0, False):
            with self.subTest(payload=payload):
                document = parsed_glb(dict(materials=[dict(extensions={'KHR_materials_ior': payload})]))
                before = copy.deepcopy(document)
                with self.assertRaisesRegex(H.Refusal, '^final_material_extensions_not_absent$'):
                    assert_final(document)
                self.assertEqual(document, before)

    def test_material_extension_property_must_be_absent_or_an_exact_empty_dict(self):
        for value in (None, [], '', False, 0):
            with self.subTest(value=value):
                document = parsed_glb(dict(materials=[dict(extensions=value)]))
                with self.assertRaisesRegex(H.Refusal, '^final_material_extensions_not_absent$'):
                    assert_final(document)

    def test_root_retained_known_empty_or_unknown_payloads_are_rejected(self):
        for name, payload in (('KHR_materials_ior', {}), ('KHR_unknown_extension', {}),
                              ('KHR_lights_punctual', {'lights': []})):
            with self.subTest(name=name):
                document = parsed_glb(dict(materials=[{}], extensions={name: payload}))
                with self.assertRaisesRegex(H.Refusal, '^final_root_extensions_outside_empty_profile$'):
                    assert_final(document)

    def test_root_extension_property_rejects_other_json_container_types(self):
        for value in (None, [], '', False, 0):
            with self.subTest(value=value):
                document = parsed_glb(dict(materials=[{}], extensions=value))
                with self.assertRaisesRegex(H.Refusal, '^final_root_extensions_outside_empty_profile$'):
                    assert_final(document)

    def test_extensions_used_must_not_declare_even_a_known_empty_extension(self):
        for value in (['KHR_materials_ior'], ['KHR_unknown_extension'], None, {}, '', False, 0):
            with self.subTest(value=value):
                document = parsed_glb(dict(materials=[{}], extensionsUsed=value))
                with self.assertRaisesRegex(H.Refusal, '^final_extension_declarations_outside_empty_profile$'):
                    assert_final(document)

    def test_extensions_required_must_not_declare_even_a_known_empty_extension(self):
        for value in (['KHR_materials_ior'], ['KHR_unknown_extension'], None, {}, '', False, 0):
            with self.subTest(value=value):
                document = parsed_glb(dict(materials=[{}], extensionsRequired=value))
                with self.assertRaisesRegex(H.Refusal, '^final_extension_declarations_outside_empty_profile$'):
                    assert_final(document)

    def test_material_domain_is_bounded_and_every_serialized_entry_is_a_dict(self):
        for value in (None, {}, [], [None], [False], ['material'], [{}] * 129):
            with self.subTest(value=value):
                document = parsed_glb(dict(materials=value))
                with self.assertRaisesRegex(H.Refusal, '^final_material_dictionary_domain_required$'):
                    assert_final(document)
        with self.assertRaisesRegex(H.Refusal, '^final_material_dictionary_domain_required$'):
            assert_final(parsed_glb({}))

    def test_all_serialized_materials_are_checked_including_the_last_admitted_slot(self):
        for count in (2, 128):
            document = parsed_glb(dict(materials=[{} for _ in range(count)]))
            self.assertIsNone(assert_final(document))
            document['materials'][-1]['extensions'] = {'KHR_materials_ior': {}}
            with self.assertRaisesRegex(H.Refusal, '^final_material_extensions_not_absent$'):
                assert_final(document)


    def test_complete_optin_resource_positive_finalizes_without_pruning_any_wrapper_itself(self):
        with E.extension_profile() as profile:
            c = E.resource_case(profile)
            extensions = {name: profile.extension_type(name, {}, False) for name in OBSERVED_EMPTY_NAMES}
            material = E.observe_material(c, extensions)
            wrapper_refs = tuple((name, value, value.extension) for name, value in extensions.items())
            document = parsed_glb(c.serialize())
            before = copy.deepcopy(document)
            report = c.resources.finalize(document)
            self.assertEqual((report['materials'], report['source_images'], report['images'], report['textures']),
                             (1, 1, 1, 1))
            self.assertEqual(report['observed_empty_extension_wrappers'], 6)
            self.assertTrue(report['final_serialized_material_extensions_absent'])
            self.assertTrue(report['final_used_and_required_extensions_absent'])
            self.assertFalse(report['extensions_removed_by_this_observer'])
            self.assertFalse(report['full_semantic_equivalence'])
            self.assertEqual(document, before)
            self.assertIs(material.extensions, extensions)
            for name, wrapper, payload in wrapper_refs:
                self.assertIs(extensions[name], wrapper)
                self.assertIs(wrapper.extension, payload)
                self.assertEqual(payload, {})

    def test_complete_optin_resource_finalization_rejects_retained_extensions_and_preserves_old_reference_gate(self):
        variants = ('material', 'root', 'used', 'required', 'texture_reference')
        for variant in variants:
            with self.subTest(variant=variant), E.extension_profile() as profile:
                c = E.resource_case(profile)
                E.observe_material(c, {'KHR_materials_ior': profile.extension_type('KHR_materials_ior', {}, False)})
                document = parsed_glb(c.serialize())
                if variant == 'material':
                    document['materials'][0]['extensions'] = {'KHR_materials_ior': {}}
                    reason = 'final_material_extensions_not_absent'
                elif variant == 'root':
                    document['extensions'] = {'KHR_unknown_extension': {}}
                    reason = 'final_root_extensions_outside_empty_profile'
                elif variant in ('used', 'required'):
                    document['extensionsUsed' if variant == 'used' else 'extensionsRequired'] = ['KHR_materials_ior']
                    reason = 'final_extension_declarations_outside_empty_profile'
                else:
                    document['textures'][0]['source'] = 1
                    reason = 'serialized_texture_source_differs'
                before = copy.deepcopy(document)
                with self.assertRaisesRegex(H.Refusal, '^' + reason + '    unittest.main()
):
                    c.resources.finalize(document)
                self.assertEqual(document, before)
                self.assertTrue(c.bridge.failed)


if __name__ == '__main__':
    unittest.main()
