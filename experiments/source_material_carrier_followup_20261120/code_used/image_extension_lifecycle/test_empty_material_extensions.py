"""Pure pinned Extension SOURCE/fake-RNA controls; never a Blender export.

Only the stdlib-only 1298-byte Extension module is executed here. All material,
image and exporter objects are fabricated; source admission is not host proof.
"""
from contextlib import contextmanager
import hashlib
import inspect
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import export_hook_proposal as H
import resource_gate_proposal as R
import shared_image_cache_proposal as S
import test_export_hook_proposal as F
import test_negative_texture_probes as N
import test_material_guard_diagnostic as D


@contextmanager
def extension_profile():
    relative, count, digest = H.EMPTY_EXTENSION_PIN
    source_path = H.EXPORTER_ROOT / relative
    raw = source_path.read_bytes()
    if len(raw) != count or hashlib.sha256(raw).hexdigest() != digest:
        raise AssertionError('pinned stdlib-only Extension SOURCE required')
    name = 'io_scene_gltf2.io.com.gltf2_io_extensions'
    module = types.ModuleType(name); module.__file__ = str(source_path)
    # No Blender/native/media module is imported by this pinned source.
    exec(compile(raw, str(source_path), 'exec', dont_inherit=True), module.__dict__)
    exporter = types.ModuleType('_has_fake_exporter_extension_alias')
    exporter.gltf2_io_extensions = module
    with patch.dict(sys.modules, {name: module}):
        yield H.EmptyMaterialExtensionProfile(module, exporter)


def resource_case(profile):
    c = N.case()
    gltf = types.SimpleNamespace(**vars(F.GLTF), MaterialPBRMetallicRoughness=F.Identity)
    c.resources = R.SimplePackedResources(tuple(item.material for item in c.cases), c.tickets,
        F.rna_types(), types.SimpleNamespace(NodeSocket=F.NodeSocket), F.ENCODE, gltf,
        allow_shared_images=True, empty_material_extension_profile=profile)
    c.bridge = S.SharedImageCaches(c.resources, c.specs, c.binary, F.Image)
    return c


def observe_material(c, extensions=None):
    f = c.cases[0]
    info, _, _, _ = c.call('texture_info', f.sockets[0], f.sockets, 'DEFAULT', 'ALL', c.settings)
    material = D.emitted(info, extensions=extensions)
    c.resources.material(material, f.material)
    return material


class EmptyMaterialExtensionsTests(unittest.TestCase):
    def test_default_seventeen_module_surface_and_resource_profile_remain_explicitly_off(self):
        self.assertEqual(len(H.PINS), 17)
        self.assertIsNone(inspect.signature(H.PinnedSurface).parameters['empty_material_extension_module'].default)
        self.assertIsNone(inspect.signature(R.SimplePackedResources).parameters['empty_material_extension_profile'].default)
        with extension_profile() as profile:
            c, material, source = D.prepared()
            material.extensions = {'KHR_materials_anisotropy': profile.extension_type('KHR_materials_anisotropy', {}, False)}
            error = D.fail(c.resources, material, source)
            self.assertEqual(error.args, ('unsupported_gathered_material_profile',))
            self.assertEqual(c.resources.gathered_materials, [])

    def test_six_exact_empty_optional_wrappers_admit_without_changing_any_input_object(self):
        with extension_profile() as profile:
            c = resource_case(profile)
            extensions = {name: profile.extension_type(name, {}, False) for name in sorted(H.EMPTY_MATERIAL_EXTENSION_NAMES)}
            snapshots = [(name, wrapper, wrapper.__dict__, wrapper.extension, dict(wrapper.__dict__))
                         for name, wrapper in extensions.items()]
            material = observe_material(c, extensions)
            self.assertIs(material.extensions, extensions)
            self.assertEqual(len(c.resources.empty_material_extension_rows), 6)
            self.assertEqual(len(c.resources.gathered_materials), 1)
            self.assertIsNone(c.resources.public_material_failure)
            for name, wrapper, fields, payload, previous in snapshots:
                self.assertIs(extensions[name], wrapper); self.assertIs(wrapper.__dict__, fields)
                self.assertIs(wrapper.extension, payload); self.assertEqual(wrapper.__dict__, previous)
            c.resources.check_unchanged()

    def test_plain_empty_dictionary_and_none_still_admit_with_optin(self):
        for value in (None, {}):
            with self.subTest(is_none=value is None), extension_profile() as profile:
                c = resource_case(profile); observe_material(c, value)
                self.assertEqual(c.resources.empty_material_extension_rows, [])
                self.assertEqual(len(c.resources.gathered_materials), 1)

    def test_nonempty_payload_unknown_name_and_wrong_wrapper_name_are_refused(self):
        for variant in ('payload', 'unknown', 'name'):
            with self.subTest(variant=variant), extension_profile() as profile:
                key = 'KHR_materials_anisotropy' if variant != 'unknown' else 'KHR_materials_unlit'
                name = key if variant != 'name' else 'KHR_materials_ior'
                payload = {'anisotropyStrength': 0.0} if variant == 'payload' else {}
                c = resource_case(profile)
                with self.assertRaises(H.Refusal): observe_material(c, {key: profile.extension_type(name, payload, False)})
                self.assertEqual(c.resources.gathered_materials, [])

    def test_required_true_bool_alias_and_nonempty_none_payload_are_refused(self):
        for required, payload in ((True, {}), (0, {}), (1, {}), (False, None), (False, [])):
            with self.subTest(required_type=type(required).__name__, payload_type=type(payload).__name__), extension_profile() as profile:
                c = resource_case(profile)
                with self.assertRaises(H.Refusal):
                    observe_material(c, {'KHR_materials_ior': profile.extension_type('KHR_materials_ior', payload, required)})
                self.assertEqual(c.resources.gathered_materials, [])

    def test_child_of_root_subclass_foreign_object_and_metadata_shape_cannot_replace_genuine_type(self):
        with extension_profile() as profile:
            class Foreign:
                def __getattribute__(self, name): raise AssertionError('foreign wrapper getter evaluated')
            candidates = [profile.module.ChildOfRootExtension([], 'KHR_materials_ior', {}, False),
                          Foreign(), dict(name='KHR_materials_ior', extension={}, required=False)]
            for item in candidates:
                with self.subTest(actual_is_dict=type(item) is dict):
                    with self.assertRaises(H.Refusal): profile.admit({'KHR_materials_ior': item})

    def test_extra_or_nonstring_instance_fields_refuse_before_unknown_equality(self):
        class Key:
            def __hash__(self): return hash('name')
            def __eq__(self, other): raise AssertionError('unknown field-key equality evaluated')
        with extension_profile() as profile:
            wrapper = profile.extension_type('KHR_materials_ior', {}, False)
            wrapper.private = 'not part of the genuine constructor'
            with self.assertRaises(H.Refusal): profile.admit({'KHR_materials_ior': wrapper})
            wrapper = profile.extension_type('KHR_materials_ior', {}, False)
            fields = {Key(): 'unknown'}
            fields['extension'] = {}; fields['required'] = False
            object.__setattr__(wrapper, '__dict__', fields)
            with self.assertRaises(H.Refusal): profile.admit({'KHR_materials_ior': wrapper})

    def test_constructor_code_defaults_and_class_marker_drift_are_refused(self):
        for edit in ('code', 'defaults', 'marker'):
            with self.subTest(edit=edit), extension_profile() as profile:
                constructor = profile.constructor
                if edit == 'code':
                    def other(self, name, extension, required=True): self.name = name
                    constructor.__code__ = other.__code__
                elif edit == 'defaults': constructor.__defaults__ = (False,)
                else: profile.extension_type.extension = False
                with self.assertRaises(H.Refusal): profile.admit({'KHR_materials_ior': object()})

    def test_runtime_module_class_registration_and_exporter_alias_drift_refuse(self):
        for edit in ('alias', 'class', 'registration'):
            with self.subTest(edit=edit), extension_profile() as profile:
                if edit == 'alias': profile.exporter_module.gltf2_io_extensions = object()
                elif edit == 'class': profile.module.Extension = object()
                else: sys.modules[profile.module_name] = types.ModuleType(profile.module_name)
                with self.assertRaises(H.Refusal): profile.check()

    def test_initial_constructor_attestation_rejects_changed_code_or_default(self):
        for edit in ('code', 'defaults'):
            with self.subTest(edit=edit), extension_profile() as profile:
                if edit == 'defaults': profile.constructor.__defaults__ = (False,)
                else:
                    def other(self, name, extension, required=True): self.name = name
                    profile.constructor.__code__ = other.__code__
                with self.assertRaises(H.Refusal): H.EmptyMaterialExtensionProfile(profile.module, profile.exporter_module)

    def test_retained_payload_identity_empty_state_and_required_flag_remain_checked(self):
        for edit in ('replace_empty', 'fill', 'required', 'name'):
            with self.subTest(edit=edit), extension_profile() as profile:
                c = resource_case(profile)
                wrapper = profile.extension_type('KHR_materials_ior', {}, False)
                observe_material(c, {'KHR_materials_ior': wrapper})
                if edit == 'replace_empty': wrapper.extension = {}
                elif edit == 'fill': wrapper.extension['ior'] = 1.5
                elif edit == 'required': wrapper.required = True
                else: wrapper.name = 'KHR_materials_specular'
                with self.assertRaises(H.Refusal): c.resources.check_unchanged()

    def test_all_other_original_material_guards_and_repeated_source_guard_stay_strict(self):
        for field in ('normal_texture', 'occlusion_texture', 'emissive_texture', 'extras'):
            with self.subTest(field=field), extension_profile() as profile:
                c = resource_case(profile)
                f = c.cases[0]
                info, _, _, _ = c.call('texture_info', f.sockets[0], f.sockets, 'DEFAULT', 'ALL', c.settings)
                material = D.emitted(info, extensions={'KHR_materials_ior': profile.extension_type('KHR_materials_ior', {}, False)},
                                     **{field: object()})
                with self.assertRaises(H.Refusal): c.resources.material(material, f.material)
                self.assertEqual(c.resources.gathered_materials, [])
        with extension_profile() as profile:
            c = resource_case(profile); material = observe_material(c)
            with self.assertRaises(H.Refusal): c.resources.material(material, c.cases[0].material)
            self.assertEqual(len(c.resources.gathered_materials), 1)


if __name__ == '__main__':
    unittest.main()
