"""Real pinned dispatcher + primary cache, fabricated RNA/image/export objects.

The genuine dispatcher performs its None-to-empty-dict write. The observer does
not mutate image fields. These controls do not qualify an actual Blender export.
"""
import hashlib
import types
import unittest

import export_hook_proposal as H
import shared_image_cache_proposal as S
import test_export_hook_proposal as F
import test_shared_image_cache_proposal as P
import test_material_guard_diagnostic as D


def dispatcher_case(groups=(0, 0), *, constructor_empty=False, hook_mutation=None):
    cache, binary = P.primary_definitions()
    c = P.Case(cache, binary, groups, attach=False)
    relative, digest = H.PINS['user_extensions']
    path = H.EXPORTER_ROOT / relative
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise AssertionError('real pinned dispatcher SOURCE required')
    namespace = {'__name__': '_has_pinned_dispatcher_cpu_only', '__file__': str(path)}
    # This exact SOURCE file defines one function and imports no bpy/NumPy/data.
    exec(compile(raw, str(path), 'exec', dont_inherit=True), namespace)
    dispatch = namespace['export_user_extensions']
    c.pre_dispatch, c.hook_states, c.dispatch_errors = [], [], []
    class Hook:
        def gather_image_hook(self, image, descriptor, sockets, settings):
            if hook_mutation is not None: hook_mutation(image)
            c.hook_states.append((image, image.extensions))
            c.resources.image(image, descriptor, sockets)
    c.settings.update(gltf_user_extensions=[Hook()],
                      log=types.SimpleNamespace(error=c.dispatch_errors.append))
    def gather_image(sockets, tile, settings):
        c.body_calls.append('gather_image')
        c.resources.before_image_data(sockets, tile)
        image = c.resources._socket_key(sockets)[0][1]
        descriptor = F.ExportImage()
        descriptor.fills = {channel: F.FillImage(image, channel) for channel in range(image.channels)}
        c.resources.after_image_data(sockets, (descriptor, None))
        name = image.name
        c.call('uri', descriptor, 'image/png', name, settings)
        buffer, _ = c.call('buffer_view', descriptor, 'image/png', name, settings)
        result = c.call('make_image', buffer, None, None, 'image/png', name, None, settings)
        c.pre_dispatch.append(result.extensions)
        dispatch('gather_image_hook', settings, result, descriptor, sockets)
        return result, descriptor, None, None
    c.specs['gather_image'] = cache['cached'](gather_image)
    if constructor_empty:
        def make_image(buffer, extensions, extras, mime, name, uri, settings):
            c.body_calls.append('make_image')
            return F.Image(buffer_view=buffer, extensions={}, extras=extras, mime_type=mime, name=name, uri=uri)
        c.specs['make_image'] = cache['cached'](make_image)
    c.bridge = S.SharedImageCaches(c.resources, c.specs, binary, F.Image)
    return c


def first_binding(c):
    f = c.cases[0]
    info, _, _, _ = c.call('texture_info', f.sockets[0], f.sockets, 'DEFAULT', 'ALL', c.settings)
    c.resources.material(D.emitted(info), f.material)
    return c.resources.images[0]['image']


def second_binding(c):
    f = c.cases[1]
    return c.call('texture_info', f.sockets[0], f.sockets, 'DEFAULT', 'ALL', c.settings)


class ImageExtensionLifecycleTests(unittest.TestCase):
    def test_genuine_dispatcher_first_hook_then_cache_hit_preserves_one_owned_empty_dictionary(self):
        c = dispatcher_case(); c.gather()
        self.assertEqual(len(c.pre_dispatch), 2); self.assertIsNone(c.pre_dispatch[0])
        image, recorded = c.hook_states[0]
        self.assertIs(type(recorded), dict); self.assertEqual(recorded, {})
        self.assertIs(c.pre_dispatch[1], recorded)
        self.assertIs(c.hook_states[1][0], image); self.assertIs(c.hook_states[1][1], recorded)
        self.assertIs(c.bridge.makes[0]['hook_extensions'], recorded)
        self.assertTrue(c.bridge.makes[0]['hook_extensions_observed'])
        self.assertEqual(c.bridge.specs['make_image']['hits'], 1)
        self.assertEqual(c.body_calls.count('make_image'), 1)
        self.assertEqual(c.dispatch_errors, [])
        report = c.resources.finalize(c.serialize())
        self.assertEqual((report['materials'], report['images'], report['textures']), (2, 1, 2))
        self.assertFalse(report['full_semantic_equivalence'])
        self.assertIs(image.extensions, recorded); self.assertEqual(recorded, {})
        self.assertIsNone(c.bridge.public_make_image_failure)

    def test_distinct_source_images_keep_distinct_dispatcher_owned_dictionaries(self):
        c = dispatcher_case((0, 1)); c.gather()
        self.assertEqual(c.pre_dispatch, [None, None])
        self.assertEqual(len(c.bridge.makes), 2)
        self.assertIsNot(c.hook_states[0][1], c.hook_states[1][1])
        self.assertEqual(c.bridge.specs['make_image']['hits'], 0)
        report = c.resources.finalize(c.serialize())
        self.assertEqual((report['source_images'], report['images']), (2, 2))

    def test_make_miss_still_requires_none_before_the_dispatcher_is_called(self):
        c = dispatcher_case(constructor_empty=True)
        with self.assertRaisesRegex(H.Refusal, '^shared_make_image_return_differs$'): c.gather()
        self.assertEqual(c.pre_dispatch, []); self.assertEqual(c.hook_states, [])
        self.assertEqual(c.bridge.makes, []); self.assertEqual(c.resources.images, [])
        self.assertFalse(c.bridge.public_make_image_failure['observation']['cache_hit'])
        self.assertTrue(c.bridge.failed)

    def test_foreign_replacement_nonempty_or_subclass_dictionary_stays_refused(self):
        class OtherDict(dict): pass
        for change in ('replacement', 'nonempty', 'subclass'):
            with self.subTest(change=change):
                c = dispatcher_case(); image = first_binding(c)
                if change == 'replacement': image.extensions = {}
                elif change == 'nonempty': image.extensions['KHR_unknown'] = {}
                else: image.extensions = OtherDict()
                with self.assertRaisesRegex(H.Refusal, '^shared_recorded_image_extensions_changed$'):
                    second_binding(c)
                self.assertTrue(c.bridge.failed); self.assertEqual(len(c.hook_states), 1)

    def test_cache_hit_cannot_infer_an_unobserved_empty_dictionary_from_the_returned_image(self):
        c = dispatcher_case(); first_binding(c)
        c.bridge.makes[0]['hook_extensions_observed'] = False  # Independent missing-observation control.
        with self.assertRaisesRegex(H.Refusal, '^shared_make_image_return_differs$'): second_binding(c)
        self.assertTrue(c.bridge.failed); self.assertEqual(len(c.hook_states), 1)

    def test_source_or_channel_mapping_relation_cannot_be_replaced_by_empty_extension_state(self):
        for change in ('source', 'mapping'):
            with self.subTest(change=change):
                c = dispatcher_case(); first_binding(c)
                if change == 'source': c.bridge.makes[0]['source'] = object()
                else: c.bridge.makes[0]['mapping'] = ()
                with self.assertRaisesRegex(H.Refusal, '^shared_cache_merge_without_same_source_and_mapping$'):
                    second_binding(c)
                self.assertTrue(c.bridge.failed)

    def test_first_owned_hook_rejects_nonempty_subclass_and_unknown_extension_states(self):
        class OtherDict(dict): pass
        for value in ({'KHR_unknown': {}}, OtherDict(), object()):
            with self.subTest(actual_is_dict=type(value) is dict):
                c = dispatcher_case(hook_mutation=lambda image: setattr(image, 'extensions', value))
                with self.assertRaises(H.Refusal): c.gather()
                self.assertTrue(c.bridge.failed); self.assertTrue(c.dispatch_errors)
                self.assertFalse(c.bridge.makes[0]['hook_extensions_observed'])
                self.assertEqual(c.resources.images, [])

    def test_final_coverage_retains_the_same_empty_dictionary_and_rejects_later_content(self):
        c = dispatcher_case(); c.gather()
        c.hook_states[0][1]['KHR_unknown'] = {}
        with self.assertRaisesRegex(H.Refusal, '^shared_recorded_image_extensions_changed$'):
            c.serialize()
        self.assertEqual(c.hook_states[0][1], {'KHR_unknown': {}})

    def test_legacy_fake_none_hook_state_keeps_existing_shared_cache_behavior(self):
        cache, binary = P.primary_definitions(); c = P.Case(cache, binary)
        c.gather()
        self.assertIsNone(c.bridge.makes[0]['hook_extensions'])
        self.assertTrue(c.bridge.makes[0]['hook_extensions_observed'])
        self.assertEqual(c.bridge.specs['make_image']['hits'], 1)
        self.assertEqual(c.resources.finalize(c.serialize())['images'], 1)

    def test_a_prior_owned_empty_dictionary_does_not_waive_any_other_return_predicate(self):
        c = dispatcher_case(); image = first_binding(c)
        image.name = 'PRIVATE changed name'
        with self.assertRaisesRegex(H.Refusal, '^shared_make_image_return_differs$'): second_binding(c)
        self.assertTrue(c.bridge.failed)
        self.assertTrue(c.bridge.public_make_image_failure['observation']['cache_hit'])
        self.assertFalse(c.bridge.public_make_image_failure['observation']['result_name_matches_frame'])


if __name__ == '__main__':
    unittest.main()
