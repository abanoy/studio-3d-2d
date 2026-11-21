"""Independent final Image/Texture extension absence; no Blender/native assets.

Synthetic GLB JSON crosses the final resource gate unchanged. These tests do not
prune data, authenticate the SDK dispatcher or explain the actual V10 failure.
"""
import copy
import unittest

import export_hook_proposal as H
import resource_gate_proposal as R
import test_empty_material_extensions as E
import test_final_material_extensions as M


def parsed(document):
    return M.parsed_glb(document)


def final_resource_extensions(document):
    return R.SimplePackedResources._assert_no_serialized_image_texture_extensions(None, document)


def completed_resource_case(profile=None):
    case = E.resource_case(profile)
    E.observe_material(case)
    return case, parsed(case.serialize())


class FinalImageTextureExtensionTests(unittest.TestCase):
    def test_absent_and_exact_empty_tables_preserve_untextured_documents(self):
        for document in ({}, {'images': []}, {'textures': []}, {'images': [], 'textures': []}):
            with self.subTest(document=document):
                document = parsed(document); before = copy.deepcopy(document)
                self.assertIsNone(final_resource_extensions(document))
                self.assertEqual(document, before)

    def test_absent_and_exact_empty_extension_objects_are_accepted_without_mutation(self):
        document = parsed(dict(images=[{}, {'extensions': {}}],
                               textures=[{'source': 0}, {'source': 1, 'extensions': {}}]))
        before = copy.deepcopy(document)
        self.assertIsNone(final_resource_extensions(document))
        self.assertEqual(document, before)

    def test_serialized_images_cannot_retain_even_known_empty_extension_tokens(self):
        for name in ('EXT_texture_webp', 'KHR_texture_basisu', 'KHR_texture_transform'):
            with self.subTest(name=name):
                document = parsed(dict(images=[dict(extensions={name: {}})]))
                with self.assertRaisesRegex(H.Refusal, '^final_image_extensions_not_absent$'):
                    final_resource_extensions(document)
                self.assertEqual(document['images'][0]['extensions'], {name: {}})

    def test_serialized_textures_cannot_retain_even_known_empty_extension_tokens(self):
        for name in ('EXT_texture_webp', 'KHR_texture_basisu', 'KHR_texture_transform'):
            with self.subTest(name=name):
                document = parsed(dict(textures=[dict(extensions={name: {}})]))
                with self.assertRaisesRegex(H.Refusal, '^final_texture_extensions_not_absent$'):
                    final_resource_extensions(document)
                self.assertEqual(document['textures'][0]['extensions'], {name: {}})

    def test_unknown_or_nonempty_image_extension_payloads_are_rejected_not_repaired(self):
        for name, payload in (('KHR_unknown', {}), ('EXT_texture_webp', {'source': 0}),
                              ('KHR_unknown', []), ('KHR_unknown', None)):
            with self.subTest(name=name, payload=payload):
                document = parsed(dict(images=[dict(extensions={name: payload})]))
                before = copy.deepcopy(document)
                with self.assertRaisesRegex(H.Refusal, '^final_image_extensions_not_absent$'):
                    final_resource_extensions(document)
                self.assertEqual(document, before)

    def test_unknown_or_nonempty_texture_extension_payloads_are_rejected_not_repaired(self):
        for name, payload in (('KHR_unknown', {}), ('KHR_texture_basisu', {'source': 0}),
                              ('KHR_unknown', []), ('KHR_unknown', None)):
            with self.subTest(name=name, payload=payload):
                document = parsed(dict(textures=[dict(extensions={name: payload})]))
                before = copy.deepcopy(document)
                with self.assertRaisesRegex(H.Refusal, '^final_texture_extensions_not_absent$'):
                    final_resource_extensions(document)
                self.assertEqual(document, before)

    def test_image_extension_property_is_absent_or_exact_empty_dictionary(self):
        for value in (None, [], '', False, 0):
            with self.subTest(value=value):
                with self.assertRaisesRegex(H.Refusal, '^final_image_extensions_not_absent$'):
                    final_resource_extensions(parsed(dict(images=[dict(extensions=value)])))

    def test_texture_extension_property_is_absent_or_exact_empty_dictionary(self):
        for value in (None, [], '', False, 0):
            with self.subTest(value=value):
                with self.assertRaisesRegex(H.Refusal, '^final_texture_extensions_not_absent$'):
                    final_resource_extensions(parsed(dict(textures=[dict(extensions=value)])))

    def test_resource_tables_and_every_entry_are_exact_bounded_json_domains(self):
        for key in ('images', 'textures'):
            for value in (None, {}, '', False, 0, [None], [False], ['resource'], [{}] * 129):
                with self.subTest(key=key, value=value):
                    with self.assertRaisesRegex(H.Refusal, '^final_image_texture_dictionary_domain_required$'):
                        final_resource_extensions(parsed({key: value}))
        with self.assertRaisesRegex(H.Refusal, '^final_image_texture_dictionary_domain_required$'):
            final_resource_extensions(parsed([]))

    def test_last_resource_of_each_table_is_checked_at_the_admitted_bound(self):
        for key, reason in (('images', 'final_image_extensions_not_absent'),
                            ('textures', 'final_texture_extensions_not_absent')):
            for count in (2, 128):
                with self.subTest(key=key, count=count):
                    document = parsed({key: [{} for _ in range(count)]})
                    self.assertIsNone(final_resource_extensions(document))
                    document[key][-1]['extensions'] = {'KHR_unknown': {}}
                    with self.assertRaisesRegex(H.Refusal, '^' + reason + '$'):
                        final_resource_extensions(document)

    def test_complete_optin_resource_positive_reports_absence_without_pruning(self):
        with E.extension_profile() as profile:
            case, document = completed_resource_case(profile)
            document['images'][0]['extensions'] = {}
            document['textures'][0]['extensions'] = {}
            before = copy.deepcopy(document)
            report = case.resources.finalize(document)
            self.assertTrue(report['final_serialized_image_extensions_absent'])
            self.assertTrue(report['final_serialized_texture_extensions_absent'])
            self.assertFalse(report['serialized_resource_extensions_removed_by_this_observer'])
            self.assertTrue(report['final_serialized_material_extensions_absent'])
            self.assertFalse(report['full_semantic_equivalence'])
            self.assertEqual(document, before)

    def test_complete_resource_finalization_rejects_image_texture_extensions_and_old_reference_drift(self):
        for variant in ('image', 'texture', 'reference'):
            with self.subTest(variant=variant), E.extension_profile() as profile:
                case, document = completed_resource_case(profile)
                if variant == 'image':
                    document['images'][0]['extensions'] = {'EXT_texture_webp': {}}
                    reason = 'final_image_extensions_not_absent'
                elif variant == 'texture':
                    document['textures'][0]['extensions'] = {'KHR_texture_basisu': {}}
                    reason = 'final_texture_extensions_not_absent'
                else:
                    document['textures'][0]['source'] = 1
                    reason = 'serialized_texture_source_differs'
                before = copy.deepcopy(document)
                with self.assertRaisesRegex(H.Refusal, '^' + reason + '$'):
                    case.resources.finalize(document)
                self.assertEqual(document, before)
                self.assertTrue(case.bridge.failed)

    def test_final_image_texture_guard_also_applies_to_unchanged_default_material_profile(self):
        case, document = completed_resource_case()
        self.assertIsNone(case.resources.empty_material_extension_profile)
        report = case.resources.finalize(document)
        self.assertTrue(report['final_serialized_image_extensions_absent'])
        self.assertTrue(report['final_serialized_texture_extensions_absent'])
        self.assertFalse(report['serialized_resource_extensions_removed_by_this_observer'])
        case, document = completed_resource_case()
        document['textures'][0]['extensions'] = {'KHR_unknown': {}}
        with self.assertRaisesRegex(H.Refusal, '^final_texture_extensions_not_absent$'):
            case.resources.finalize(document)
        self.assertTrue(case.bridge.failed)


if __name__ == '__main__':
    unittest.main()
