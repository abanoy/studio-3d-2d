"""Synthetic material diagnostics only; no Blender/native/export/process run.

The original strict material method remains the oracle for refusal/pass. The
positive image setup uses the preserved fake-RNA/pinned SOURCE cache controls.
Nothing here qualifies an actual exporter material or a permissive profile.
"""
import copy
import json
import types
import unittest

import export_hook_proposal as H
import resource_gate_proposal as R
import test_export_hook_proposal as F
import test_negative_texture_probes as N


class Extension:
    def __init__(self, name, extension, required=False):
        self.name, self.extension, self.required = name, extension, required


def emitted(info=None, **changes):
    values = dict(extensions=None, extras=None, normal_texture=None, occlusion_texture=None,
        emissive_texture=None, pbr_metallic_roughness=F.Identity(
            metallic_roughness_texture=None, base_color_texture=info), name='PRIVATE source material')
    values.update(changes)
    return F.Material(**values)


def prepared():
    c = N.case()
    # The real generated class has this name; F.Identity is only its fake stand-in.
    c.resources.gltf = types.SimpleNamespace(**vars(F.GLTF), MaterialPBRMetallicRoughness=F.Identity)
    f = c.cases[0]
    info, _, _, _ = c.call('texture_info', f.sockets[0], f.sockets, 'DEFAULT', 'ALL', c.settings)
    return c, emitted(info), f.material


def fail(resources, material, source):
    try:
        resources.material(material, source)
    except BaseException as error:
        return error
    raise AssertionError('original strict material method must still refuse')


class MaterialGuardDiagnosticTests(unittest.TestCase):
    def test_nonempty_extension_still_refuses_and_observes_only_safe_shape_and_positive_matches(self):
        c, material, source = prepared()
        material.extensions = {'KHR_materials_anisotropy': Extension('KHR_materials_anisotropy', {})}
        error = fail(c.resources, material, source)
        self.assertIs(type(error), H.Refusal)
        self.assertEqual(error.args, ('unsupported_gathered_material_profile',))
        value = c.resources.public_material_failure
        self.assertEqual(value['first_refusal_code'], 'unsupported_gathered_material_profile')
        self.assertEqual(value['status'], 'OBSERVED'); self.assertEqual(value['failures'], 1)
        self.assertTrue(value['original_strict_failure_preserved'])
        self.assertFalse(value['material_admission_changed']); self.assertFalse(value['resource_equivalence_qualified'])
        observed = value['observation']
        self.assertTrue(observed['actual_material_type']); self.assertTrue(observed['fields_available'])
        self.assertEqual((observed['source_graph_matches'], observed['positive_info_identity_matches'],
                          observed['positive_info_graph_key_matches']), (1, 1, 1))
        self.assertEqual(observed['gathered_material_count'], 0)
        self.assertFalse(observed['guards']['extensions_is_none'])
        self.assertFalse(observed['guards']['extensions_is_exact_empty_dict'])
        extension = observed['extensions']['known'][0]
        self.assertEqual(extension['name'], 'KHR_materials_anisotropy')
        self.assertTrue(extension['plain_wrapper_fields']); self.assertTrue(extension['wrapper_name_matches'])
        self.assertEqual(extension['payload_type'], 'DICT'); self.assertEqual(extension['payload_count'], 0)
        self.assertEqual(c.resources.gathered_materials, [])

    def test_success_keeps_diagnostic_absent_and_original_material_binding_unchanged(self):
        c, material, source = prepared(); material.extensions = {}
        c.resources.material(material, source)
        self.assertIsNone(c.resources.public_material_failure)
        self.assertEqual(len(c.resources.gathered_materials), 1)
        self.assertIs(c.resources.gathered_materials[0]['material'], material)
        self.assertIs(c.resources.gathered_materials[0]['source'], source)
        self.assertIs(c.resources.gathered_materials[0]['info'], material.pbr_metallic_roughness.base_color_texture)

    def test_first_failure_observation_is_retained_while_later_failures_only_increment_count(self):
        c, material, source = prepared()
        material.extensions = {'KHR_materials_anisotropy': Extension('KHR_materials_anisotropy', {})}
        fail(c.resources, material, source)
        first = copy.deepcopy(c.resources.public_material_failure)
        material.extensions = None; material.extras = {'PRIVATE': 3.5}
        for _ in range(3): fail(c.resources, material, source)
        after = dict(c.resources.public_material_failure)
        self.assertEqual(after.pop('failures'), 4)
        first.pop('failures'); self.assertEqual(after, first)
        self.assertEqual(c.resources.gathered_materials, [])

    def test_fixed_guard_fields_identify_nonempty_texture_without_publishing_its_data(self):
        c, material, source = prepared()
        material.normal_texture = F.TextureInfo(index='PRIVATE texture reference')
        fail(c.resources, material, source)
        observed = c.resources.public_material_failure['observation']
        self.assertFalse(observed['guards']['normal_texture_is_none'])
        self.assertEqual(observed['field_types']['normal_texture'], 'OTHER')
        self.assertTrue(observed['guards']['emissive_texture_is_none'])
        self.assertNotIn('PRIVATE', json.dumps(c.resources.public_material_failure))

    def test_reachability_and_repeated_hook_refusals_remain_distinct_original_codes(self):
        c, material, source = prepared()
        material.pbr_metallic_roughness.base_color_texture = F.TextureInfo(index=object())
        error = fail(c.resources, material, source)
        self.assertEqual(error.args, ('material_texture_reachability_missing',))
        observed = c.resources.public_material_failure['observation']
        self.assertEqual((observed['positive_info_identity_matches'], observed['positive_info_graph_key_matches']), (0, 0))
        c, material, source = prepared(); c.resources.material(material, source)
        error = fail(c.resources, material, source)
        self.assertEqual(error.args, ('repeated_or_aliased_material_hook',))
        observed = c.resources.public_material_failure['observation']
        self.assertEqual((observed['repeated_material_identity_count'], observed['repeated_source_identity_count']), (1, 1))
        self.assertEqual(len(c.resources.gathered_materials), 1)

    def test_known_payload_field_types_never_publish_values_unknown_keys_or_private_class_names(self):
        c, material, source = prepared()
        material.extensions = {'PRIVATE extension key': 'PRIVATE extension value',
            'KHR_materials_anisotropy': Extension('KHR_materials_anisotropy',
                {'anisotropyStrength': 'PRIVATE field value', 'anisotropyRotation': 2.25,
                 'anisotropyTexture': F.TextureInfo(index='PRIVATE'), 'PRIVATE payload key': [1, 2, 3]})}
        fail(c.resources, material, source)
        observed = c.resources.public_material_failure['observation']['extensions']
        self.assertEqual(observed['count'], 2); self.assertEqual(observed['unknown_name_count'], 1)
        row = observed['known'][0]
        self.assertEqual(row['known_field_types'], dict(anisotropyStrength='STR', anisotropyRotation='FLOAT', anisotropyTexture='OTHER'))
        self.assertEqual(row['unknown_field_count'], 1); self.assertEqual(row['payload_count'], 4)
        encoded = json.dumps(c.resources.public_material_failure, allow_nan=False)
        for private in ('PRIVATE', 'TextureInfo', '2.25', '1, 2, 3'):
            self.assertNotIn(private, encoded)

    def test_unknown_extension_and_payload_object_getters_and_reprs_are_never_called(self):
        touches = []
        class PrivateOwnerType:
            @property
            def __dict__(self): touches.append('dict'); raise AssertionError('PRIVATE')
            @property
            def extension(self): touches.append('extension'); raise AssertionError('PRIVATE')
            def __repr__(self): touches.append('repr'); raise AssertionError('PRIVATE')
        c, material, source = prepared()
        material.extensions = {'KHR_materials_anisotropy': PrivateOwnerType()}
        fail(c.resources, material, source)
        self.assertEqual(touches, [])
        row = c.resources.public_material_failure['observation']['extensions']['known'][0]
        self.assertFalse(row['plain_wrapper_fields']); self.assertEqual(row['payload_type'], 'UNAVAILABLE')
        self.assertNotIn('PrivateOwnerType', json.dumps(c.resources.public_material_failure))

    def test_extension_and_payload_budgets_are_checked_before_traversing_values(self):
        c, material, source = prepared()
        material.extensions = {('PRIVATE' + str(index)): object() for index in range(33)}
        fail(c.resources, material, source)
        observed = c.resources.public_material_failure['observation']['extensions']
        self.assertEqual(observed['count'], 33); self.assertFalse(observed['count_in_budget'])
        self.assertEqual(observed['known'], [])
        c, material, source = prepared()
        material.extensions = {'KHR_materials_anisotropy': Extension('KHR_materials_anisotropy',
            {'PRIVATE' + str(index): object() for index in range(65)})}
        fail(c.resources, material, source)
        row = c.resources.public_material_failure['observation']['extensions']['known'][0]
        self.assertEqual(row['payload_count'], 65); self.assertFalse(row['payload_count_in_budget'])
        self.assertEqual(row['known_field_types'], {})
        self.assertNotIn('PRIVATE', json.dumps(c.resources.public_material_failure))

    def test_exact_original_exception_survives_diagnostic_allocation_or_schema_failure(self):
        c, material, source = prepared()
        primary = H.Refusal('unsupported_gathered_material_profile')
        def strict(*args): raise primary
        def diagnostic(*args): raise MemoryError('PRIVATE secondary diagnostic failure')
        c.resources._material_strict = strict
        c.resources._material_guard_diagnostic = diagnostic
        self.assertIs(fail(c.resources, material, source), primary)
        value = c.resources.public_material_failure
        self.assertEqual(value['status'], 'UNAVAILABLE'); self.assertIsNone(value['observation'])
        self.assertEqual(value['first_refusal_code'], 'unsupported_gathered_material_profile')
        self.assertNotIn('PRIVATE', json.dumps(value))

    def test_only_four_known_original_refusal_codes_are_published_verbatim(self):
        for code in sorted(R.MATERIAL_REFUSAL_CODES) + ['PRIVATE error text']:
            with self.subTest(known=code in R.MATERIAL_REFUSAL_CODES):
                c, material, source = prepared(); primary = H.Refusal(code)
                def strict(*args): raise primary
                c.resources._material_strict = strict
                self.assertIs(fail(c.resources, material, source), primary)
                expected = code if code in R.MATERIAL_REFUSAL_CODES else 'OTHER_MATERIAL_FAILURE'
                self.assertEqual(c.resources.public_material_failure['first_refusal_code'], expected)
                self.assertNotIn('PRIVATE', json.dumps(c.resources.public_material_failure))

    def test_foreign_material_type_is_not_probed_and_private_getters_are_not_evaluated(self):
        touches = []
        class ForeignMaterial:
            @property
            def extensions(self): touches.append('extensions'); raise AssertionError('PRIVATE')
            def __repr__(self): touches.append('repr'); raise AssertionError('PRIVATE')
        c, material, source = prepared()
        error = fail(c.resources, ForeignMaterial(), source)
        self.assertEqual(error.args, ('unsupported_gathered_material_profile',))
        self.assertEqual(touches, [])
        observed = c.resources.public_material_failure['observation']
        self.assertFalse(observed['actual_material_type']); self.assertFalse(observed['fields_available'])
        self.assertNotIn('ForeignMaterial', json.dumps(c.resources.public_material_failure))

    def test_failure_counter_is_bounded_and_never_replaces_first_guard_observation(self):
        c, material, source = prepared(); material.extensions = {'KHR_materials_unlit': {}}
        fail(c.resources, material, source)
        first = copy.deepcopy(c.resources.public_material_failure['observation'])
        for _ in range(130): fail(c.resources, material, source)
        value = c.resources.public_material_failure
        self.assertEqual(value['failures'], 128); self.assertTrue(value['failure_count_capped'])
        self.assertEqual(value['observation'], first); self.assertEqual(c.resources.gathered_materials, [])


if __name__ == '__main__':
    unittest.main()
