"""Pure primary-cache/fake-RNA contracts; no Blender/native/process/API runs.

Root alone may execute. Tests read two authenticated exporter SOURCE files,
execute the stdlib-only cache definitions and compile the BinaryData class AST.
All meshes/materials/images/hooks are fabricated and never qualify an export.
"""
import array
import ast
import builtins
import copy
import hashlib
from pathlib import Path
import sys
import types
import typing
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import export_hook_proposal as H
import resource_gate_proposal as R
import shared_image_cache_proposal as S
import test_export_hook_proposal as F


def primary_definitions():
    cache_path, cache_sha = H.PINS['cache']
    cache_path = H.EXPORTER_ROOT/cache_path
    raw_cache = cache_path.read_bytes()
    if hashlib.sha256(raw_cache).hexdigest() != cache_sha:
        raise AssertionError('exact primary cache source required')
    cache = {'__name__': '_has_pinned_cache_cpu_only', '__file__': str(cache_path)}
    exec(compile(raw_cache, str(cache_path), 'exec', dont_inherit=True), cache)
    path, count, expected = H.SHARED_BINARY_PIN
    path = H.EXPORTER_ROOT/path
    raw_binary = path.read_bytes()
    if len(raw_binary) != count or hashlib.sha256(raw_binary).hexdigest() != expected:
        raise AssertionError('exact primary BinaryData source required')
    classes = [node for node in ast.parse(raw_binary).body if isinstance(node, ast.ClassDef) and node.name == 'BinaryData']
    if len(classes) != 1:
        raise AssertionError('one primary BinaryData class required')
    # Only annotations for unused from_list require this fabricated enum name.
    # No source import, Blender, NumPy, media or native data is involved.
    namespace = {'__name__': '_has_primary_binary_cpu_only', 'typing': typing, 'array': array,
                 'gltf2_io_constants': NS(ComponentType=object)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=classes, type_ignores=[])), str(path), 'exec',
                 dont_inherit=True), namespace)
    return cache, namespace['BinaryData']


class Case:
    def __init__(self, cache, binary, groups=(0, 0), *, attach=True):
        self.cases = [F.graph_fixture() for _ in groups]
        unique = {}
        for index, group in enumerate(groups):
            if group not in unique:
                unique[group] = self.cases[index]
                unique[group].image.name = 'source-png-' + str(group)
            self.cases[index].tex.image = unique[group].image
        self.tickets = [case.tickets[0] for case in unique.values()]
        self.resources = R.SimplePackedResources(tuple(case.material for case in self.cases), self.tickets,
            F.rna_types(), NS(NodeSocket=F.NodeSocket), F.ENCODE, F.GLTF, allow_shared_images=True)
        self.binary, self.settings = binary, {'gltf_format': 'GLB'}
        self.bridge = None
        self.common_name = None
        self.duplicate_hook = False
        self.change_mapping = False
        self.skip_hook = False
        self.original_error = None
        self.corrupt_stack = False
        self.make_buffer_override = None
        self.grow_make_cache = False
        self.body_calls = []

        def uri(descriptor, mime, name, settings):
            self.body_calls.append('uri')
            return None, None
        def buffer_view(descriptor, mime, name, settings):
            self.body_calls.append('buffer_view')
            return binary(descriptor.fills[0].image.packed_file.data), None
        def make_image(buffer, extensions, extras, mime, name, uri, settings):
            self.body_calls.append('make_image')
            if self.corrupt_stack: self.bridge.stack.clear()
            if self.grow_make_cache:
                func = self.bridge.specs['make_image']['func']
                for index in range(S.MAX_ENTRIES + 1): getattr(func, '__cache')[('unknown', index)] = object()
            if self.original_error is not None: raise self.original_error
            return F.Image(buffer_view=buffer, extensions=extensions, extras=extras,
                           mime_type=mime, name=name, uri=uri)
        def gather_image(sockets, tile, settings):
            self.body_calls.append('gather_image')
            self.resources.before_image_data(sockets, tile)
            image = self.resources._socket_key(sockets)[0][1]
            descriptor = F.ExportImage()
            descriptor.fills = {channel: F.FillImage(image, channel) for channel in range(image.channels)}
            if self.change_mapping: descriptor.fills[1].src_chan = 0
            self.resources.after_image_data(sockets, (descriptor, None))
            name = image.name if self.common_name is None else self.common_name
            self.call('uri', descriptor, 'image/png', name, settings)
            buffer, _factor = self.call('buffer_view', descriptor, 'image/png', name, settings)
            argument = buffer if self.make_buffer_override is None else self.make_buffer_override
            gltf_image = self.call('make_image', argument, None, None, 'image/png', name, None, settings)
            if not self.skip_hook:
                self.resources.image(gltf_image, descriptor, sockets)
                if self.duplicate_hook: self.resources.image(gltf_image, descriptor, sockets)
            return gltf_image, descriptor, None, None
        def gather_texture(sockets, tile, settings):
            self.body_calls.append('gather_texture')
            image, _descriptor, _factor, _udim = self.call('gather_image', sockets, tile, settings)
            texture = F.Texture(source=image, extensions=None, extras=None)
            self.resources.texture(texture, sockets)
            return texture, None, None
        def texture_info(primary, sockets, kind, filter_type, settings):
            self.body_calls.append('texture_info')
            texture, _factor, _udim = self.call('gather_texture', sockets, None, settings)
            info = F.TextureInfo(index=texture, tex_coord=None, extensions=None, extras=None)
            self.resources.texture_info(info, sockets)
            return info, {}, {}, None
        functions = dict(uri=uri, buffer_view=buffer_view, make_image=make_image,
                         gather_image=gather_image, gather_texture=gather_texture, texture_info=texture_info)
        self.specs = {name: cache['cached'](function) for name, function in functions.items()}
        if attach:
            self.bridge = S.SharedImageCaches(self.resources, self.specs, binary, F.Image)

    def call(self, name, *args):
        return self.bridge.call(name, self.specs[name], args, {})

    def gather(self):
        self.materials = []
        for case in self.cases:
            info, _uv, _udim, _factor = self.call('texture_info', case.sockets[0], case.sockets,
                                                'DEFAULT', 'ALL', self.settings)
            material = F.Material(extensions=None, extras=None, normal_texture=None,
                                 occlusion_texture=None, emissive_texture=None,
                                 pbr_metallic_roughness=F.Identity(metallic_roughness_texture=None, base_color_texture=info))
            self.resources.material(material, case.material)
            self.materials.append(material)
        return self

    def serialize(self):
        for index, row in enumerate(self.resources.images):
            self.resources.reference('image', row['image'], index)
            row['image'].buffer_view = index  # Known original exporter reference transition.
        for index, row in enumerate(self.resources.textures):
            image_index = next(i for i, image in enumerate(self.resources.images) if image['image'] is row['image'])
            row['texture'].source = image_index
            self.resources.reference('texture', row['texture'], index)
        for index, row in enumerate(self.resources.gathered_materials):
            info = row['info']
            info.index = next(i for i, texture in enumerate(self.resources.textures)
                              if any(record['info'] is info and record['texture'] is texture['texture']
                                     for record in self.resources.infos))
            self.resources.reference('material', row['material'], index)
        document = dict(images=[{} for _ in self.resources.images],
            textures=[dict(source=row['texture'].source) for row in self.resources.textures],
            materials=[dict(pbrMetallicRoughness=dict(baseColorTexture=dict(index=row['info'].index)))
                       for row in self.resources.gathered_materials])
        return document


class SharedCaches(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache, cls.binary = primary_definitions()

    def case(self, groups=(0, 0), **kwargs):
        return Case(self.cache, self.binary, groups, **kwargs)

    def test_primary_cache_binary_bytes_equality_is_the_actual_key_behavior(self):
        calls = []
        @self.cache['cached']
        def body(value, settings):
            calls.append(value)
            return object()
        first, equal = self.binary(b'ordinary synthetic source bytes'), self.binary(b'ordinary synthetic source bytes')
        self.assertIsNot(first, equal)
        self.assertEqual(first, equal)
        settings = {}
        self.assertIs(body(first, settings), body(equal, settings))
        self.assertEqual(len(calls), 1)
        self.assertEqual(H.SHARED_BINARY_PIN[2], 'ed6e29b6557522b6a056a9bb1e3a0b6a8fffe250e9d0afdf47f7f2eef2447dcf')

    def test_extra_source_pin_mismatch_is_not_replaced_by_an_existing_file(self):
        path = H.EXPORTER_ROOT/H.SHARED_BINARY_PIN[0]
        module = types.ModuleType('_has_binary_pin_cpu_negative')
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        try:
            with self.assertRaisesRegex(H.Refusal, 'pinned_source_differs'):
                H._source(module, path, '0'*64)
        finally:
            del sys.modules[module.__name__]

    def test_correct_binary_source_hash_cannot_admit_fake_runtime_method_globals(self):
        path = H.EXPORTER_ROOT/H.SHARED_BINARY_PIN[0]
        module = types.ModuleType('_has_binary_runtime_cpu_negative')
        module.__file__ = str(path)
        class FakeBinaryData:
            def __init__(self, data, bufferViewTarget=None): self.data, self.bufferViewTarget = data, bufferViewTarget
            def __eq__(self, other): return self.data == other.data
            def __hash__(self): return hash(self.data)
        module.BinaryData = FakeBinaryData
        surface = object.__new__(H.PinnedSurface)
        surface.modules = dict(image=NS(gltf2_io_binary_data=module), exporter=NS(gltf2_io_binary_data=module),
                               texture=NS(BinaryData=FakeBinaryData))
        sys.modules[module.__name__] = module
        try:
            with self.assertRaisesRegex(H.Refusal, 'runtime_function_globals_or_filename_differs'):
                surface._shared_surface(module, self.cache['default_key'])
        finally:
            del sys.modules[module.__name__]

    def test_same_source_four_graphs_two_unique_images_keep_distinct_binding_descriptors(self):
        c = self.case((0, 1, 0, 1)).gather()
        self.assertEqual((len(c.resources.image_bindings), len(c.resources.images), len(c.resources.descriptors)), (4, 2, 4))
        self.assertEqual(len({id(row['descriptor']) for row in c.resources.descriptors}), 4)
        first, third = c.resources.image_bindings[0], c.resources.image_bindings[2]
        self.assertIs(first['image'], third['image'])
        self.assertIsNot(first['descriptor'], third['descriptor'])
        # Cached Image retains the first BinaryData, despite a different new
        # BinaryData argument on the later authorized make-image cache hit.
        self.assertIs(first['image'].buffer_view, c.bridge.buffers[0]['buffer'])
        self.assertIsNot(c.bridge.buffers[0]['buffer'], c.bridge.buffers[2]['buffer'])
        report = c.resources.finalize(c.serialize())
        self.assertEqual(report['image_bindings'], 4)
        self.assertEqual(report['cache_observation']['caches']['make_image'], dict(calls=4, hits=2, misses=2, entries=2))
        self.assertFalse(report['cache_observation']['actual_export_or_native_fidelity_qualified'])
        self.assertEqual(H.SOURCE_NORMAL_MAX_ERROR, 2e-5)

    def test_opt_in_unshared_baseline_stays_separate_and_has_no_make_hits(self):
        c = self.case((0, 1)).gather()
        report = c.resources.finalize(c.serialize())
        self.assertEqual((report['source_images'], report['images']), (2, 2))
        self.assertEqual(report['cache_observation']['caches']['make_image']['hits'], 0)

    def test_genuine_gather_cache_hit_has_no_new_descriptor_or_hook(self):
        c = self.case().gather()
        before = len(c.resources.descriptors), len(c.resources.image_bindings), len(c.body_calls)
        sockets = c.cases[0].sockets
        result = c.call('gather_image', sockets, None, c.settings)
        self.assertIs(result, c.bridge.gathers[0]['result'])
        self.assertEqual(before, (len(c.resources.descriptors), len(c.resources.image_bindings), len(c.body_calls)))
        c.resources.finalize(c.serialize())
        self.assertEqual(c.bridge.specs['gather_image']['hits'], 1)

    def test_texture_and_texture_info_cache_hits_do_not_replay_hooks(self):
        c = self.case().gather()
        sockets = c.cases[0].sockets
        count = len(c.resources.textures), len(c.resources.infos), len(c.body_calls)
        c.call('gather_texture', sockets, None, c.settings)
        c.call('texture_info', sockets[0], sockets, 'DEFAULT', 'ALL', c.settings)
        self.assertEqual(count, (len(c.resources.textures), len(c.resources.infos), len(c.body_calls)))
        c.resources.finalize(c.serialize())

    def test_equal_source_bytes_on_distinct_image_ids_cannot_authorize_cache_merge(self):
        c = self.case((0, 1)); c.common_name = 'same-resolved-export-name'
        self.assertIsNot(c.cases[0].image, c.cases[1].image)
        self.assertEqual(c.cases[0].image.packed_file.data, c.cases[1].image.packed_file.data)
        with self.assertRaisesRegex(H.Refusal, 'shared_cache_merge_without_same_source_and_mapping'):
            c.gather()
        self.assertTrue(c.bridge.failed)

    def test_default_profile_still_refuses_source_sharing_without_any_cache_authority(self):
        first, second = F.graph_fixture(), F.graph_fixture()
        second.tex.image = first.image
        for flag in (None, 1, 'yes'):
            with self.assertRaises(H.Refusal):
                R.SimplePackedResources((first.material, second.material), first.tickets, F.rna_types(),
                    NS(NodeSocket=F.NodeSocket), F.ENCODE, F.GLTF, allow_shared_images=flag)
        with self.assertRaisesRegex(H.Refusal, 'source_image_shared_between_materials_outside_profile'):
            R.SimplePackedResources((first.material, second.material), first.tickets, F.rna_types(),
                                   NS(NodeSocket=F.NodeSocket), F.ENCODE, F.GLTF)

    def test_opt_in_without_attested_cache_cannot_use_early_descriptor_or_finalize(self):
        c = self.case(attach=False)
        with self.assertRaisesRegex(H.Refusal, 'shared_image_attested_cache_missing'):
            c.resources.before_image_data(c.cases[0].sockets, None)
        with self.assertRaises(H.Refusal): c.resources.finalize({})

    def test_cache_attachment_cannot_reuse_observer_or_warm_specifications(self):
        c = self.case()
        with self.assertRaises(H.Refusal): S.SharedImageCaches(c.resources, c.specs, c.binary, F.Image)
        fresh = self.case(attach=False)
        func, _key = S._components(fresh.specs['uri'])
        setattr(func, '__cache', {})
        with self.assertRaisesRegex(H.Refusal, 'shared_warm_cache_refused'):
            S.SharedImageCaches(fresh.resources, fresh.specs, fresh.binary, F.Image)

    def test_unobserved_warm_cache_or_entry_is_refused_before_key_lookup(self):
        for mode in ('warm', 'extra', 'replace'):
            c = self.case()
            if mode != 'warm':
                c.call('gather_image', c.cases[0].sockets, None, c.settings)
            func = c.bridge.specs['gather_image']['func']
            if mode == 'warm':
                setattr(func, '__cache', {})
                setattr(func, '__export_settings', c.settings)
            elif mode == 'extra':
                getattr(func, '__cache')[('unobserved',)] = object()
            else:
                setattr(func, '__cache', dict(getattr(func, '__cache')))
            with self.assertRaises(H.Refusal): c.call('gather_image', c.cases[-1].sockets, None, c.settings)

    def test_warm_make_cache_never_reads_foreign_buffer_data_or_equality_before_admission(self):
        touched = []
        class ForeignBuffer:
            @property
            def data(self): touched.append('data'); raise AssertionError('foreign getter')
            def __eq__(self, other): touched.append('eq'); raise AssertionError('foreign equality')
            def __hash__(self): touched.append('hash'); raise AssertionError('foreign hash')
        c = self.case()
        c.call('gather_image', c.cases[0].sockets, None, c.settings)
        self.assertEqual(len(c.bridge.specs['make_image']['entries']), 1)
        c.make_buffer_override = ForeignBuffer()
        with self.assertRaisesRegex(H.Refusal, 'shared_make_image_argument_types'):
            c.call('gather_image', c.cases[1].sockets, None, c.settings)
        self.assertEqual(touched, [])

    def test_cache_length_is_bounded_before_both_items_snapshots(self):
        for boundary in ('before', 'after'):
            c = self.case()
            if boundary == 'before':
                c.call('gather_image', c.cases[0].sockets, None, c.settings)
                cache = getattr(c.bridge.specs['gather_image']['func'], '__cache')
                for index in range(S.MAX_ENTRIES + 1): cache[('unknown', index)] = object()
            else:
                c.grow_make_cache = True
            oversized_snapshots = []
            def bounded_list(items):
                if len(items) > S.MAX_ENTRIES:
                    oversized_snapshots.append(len(items))
                    raise AssertionError('unbounded items allocation')
                return builtins.list(items)
            with patch.object(S, 'list', bounded_list, create=True):
                with self.assertRaisesRegex(H.Refusal, 'shared_cache_entry_budget_before_snapshot'):
                    c.call('gather_image', c.cases[-1].sockets, None, c.settings)
            self.assertEqual(oversized_snapshots, [])

    def test_settings_identity_and_runtime_function_metadata_must_stay_exact(self):
        c = self.case()
        c.call('gather_image', c.cases[0].sockets, None, c.settings)
        with self.assertRaises(H.Refusal):
            c.call('gather_image', c.cases[1].sockets, None, dict(c.settings))
        c = self.case(); func = c.bridge.specs['gather_image']['func']
        func.__defaults__ = (None,)
        with self.assertRaisesRegex(H.Refusal, 'shared_cache_runtime_function_changed'):
            c.call('gather_image', c.cases[0].sockets, None, c.settings)

    def test_complete_descriptor_mapping_and_planned_socket_key_are_required(self):
        c = self.case(); c.change_mapping = True
        with self.assertRaises(H.Refusal): c.gather()
        c = self.case()
        with self.assertRaisesRegex(H.Refusal, 'shared_incomplete_planned_socket_key'):
            c.call('gather_image', (c.cases[0].sockets[0],), None, c.settings)

    def test_fresh_python_wrapper_for_same_canonical_socket_cannot_manufacture_a_second_gather(self):
        c = self.case()
        c.call('gather_image', c.cases[0].sockets, None, c.settings)
        repeated = tuple(F.NodeSocket(wrapper.socket, list(wrapper.group_path)) for wrapper in c.cases[0].sockets)
        with self.assertRaisesRegex(H.Refusal, 'shared_repeated_canonical_socket_gather'):
            c.call('gather_image', repeated, None, c.settings)

    def test_duplicate_or_eventless_image_hook_refuses_permanently(self):
        c = self.case(); c.duplicate_hook = True
        with self.assertRaises(H.Refusal): c.gather()
        with self.assertRaises(H.Refusal): c.bridge.finish()
        c = self.case().gather()
        row = c.resources.image_bindings[0]
        with self.assertRaises(H.Refusal): c.resources.image(row['image'], row['descriptor'], c.cases[0].sockets)

    def test_missing_image_hook_cannot_be_inferred_from_a_returned_cached_image(self):
        c = self.case(); c.skip_hook = True
        with self.assertRaisesRegex(H.Refusal, 'shared_gather_return_or_hook_coverage'): c.gather()

    def test_binary_data_pin_and_target_are_checked_with_actual_objects(self):
        c = self.case()
        frame = dict(key=c.resources._socket_key(c.cases[0].sockets))
        for data, target in ((b'changed', None), (c.cases[0].image.packed_file.data, 34962)):
            with self.assertRaises(H.Refusal): c.bridge._buffer(c.binary(data, target), frame)
        impostor = NS(data=c.cases[0].image.packed_file.data, bufferViewTarget=None)
        with self.assertRaises(H.Refusal): c.bridge._buffer(impostor, frame)

    def test_retained_binary_key_payload_cannot_change_after_an_observed_cache_call(self):
        c = self.case()
        c.call('gather_image', c.cases[0].sockets, None, c.settings)
        c.bridge.buffers[0]['buffer'].data = b'changed'
        with self.assertRaisesRegex(H.Refusal, 'shared_retained_binary_data_changed'):
            c.call('gather_image', c.cases[1].sockets, None, c.settings)

    def test_binary_hash_or_equality_method_mutation_refuses_before_any_cache_lookup(self):
        for name in ('__hash__', '__eq__'):
            c = self.case()
            replacement = (lambda self: 1) if name == '__hash__' else (lambda self, other: True)
            with patch.object(c.binary, name, replacement):
                with self.assertRaisesRegex(H.Refusal, 'shared_binary_runtime_method_changed'):
                    c.call('gather_image', c.cases[0].sockets, None, c.settings)
            self.assertEqual(c.body_calls, [])
        for name in ('data', 'bufferViewTarget'):
            c = self.case()
            c.call('gather_image', c.cases[0].sockets, None, c.settings)
            touched = []
            def getter(_self): touched.append(name); raise AssertionError('class data descriptor')
            with patch.object(c.binary, name, property(getter), create=True):
                with self.assertRaisesRegex(H.Refusal, 'shared_binary_instance_field_descriptor_changed'):
                    c.call('gather_image', c.cases[1].sockets, None, c.settings)
            self.assertEqual(touched, [])

    def test_plain_exporter_wrapper_or_descriptor_equality_cannot_change_cache_semantics(self):
        for klass in (F.NodeSocket, F.ExportImage):
            c = self.case()
            with patch.object(klass, '__eq__', lambda self, other: True, create=True):
                with self.assertRaisesRegex(H.Refusal, 'shared_cache_identity_class_changed'):
                    c.call('gather_image', c.cases[0].sockets, None, c.settings)
            self.assertEqual(c.body_calls, [])

    def test_observed_cache_return_value_cannot_be_replaced_by_a_lookalike(self):
        c = self.case()
        c.call('gather_image', c.cases[0].sockets, None, c.settings)
        row = c.bridge.specs['make_image']; cache = getattr(row['func'], '__cache')
        key = next(iter(cache)); cache[key] = F.Image(**cache[key].__dict__)
        with self.assertRaisesRegex(H.Refusal, 'shared_cache_entries_changed'):
            c.call('gather_image', c.cases[1].sockets, None, c.settings)

    def test_original_exception_is_same_object_no_fallback_and_all_frames_close(self):
        c = self.case(); error = RuntimeError('synthetic original error'); c.original_error = error
        with self.assertRaises(RuntimeError) as caught: c.gather()
        self.assertIs(caught.exception, error)
        self.assertEqual(c.body_calls.count('make_image'), 1)
        self.assertEqual(c.bridge.stack, [])
        self.assertIsNone(c.bridge.active)
        self.assertTrue(c.bridge.failed)
        with self.assertRaises(H.Refusal): c.bridge.finish()

    def test_original_exception_survives_a_corrupted_observer_stack_without_losing_refusal(self):
        c = self.case(); error = RuntimeError('synthetic original error')
        c.original_error, c.corrupt_stack = error, True
        with self.assertRaises(RuntimeError) as caught: c.gather()
        self.assertIs(caught.exception, error)
        self.assertTrue(c.bridge.failed)
        with self.assertRaises(H.Refusal): c.bridge.finish()

    def test_shared_repeat_budget_refuses_before_any_source_image_getter(self):
        cases = [F.graph_fixture() for _ in range(4)]
        for case in cases[1:]: case.tex.image = cases[0].image
        cases[0].tickets[0]['encoded_bytes'] = R.MAX_ENCODED_BYTES
        with self.assertRaisesRegex(H.Refusal, 'shared_binding_encoded_budget'):
            R.SimplePackedResources(tuple(case.material for case in cases), cases[0].tickets,
                F.rna_types(), NS(NodeSocket=F.NodeSocket), F.ENCODE, F.GLTF, allow_shared_images=True)

    def test_missing_planned_graph_binding_cannot_hide_behind_shared_image_ticket_coverage(self):
        c = self.case()
        c.call('gather_image', c.cases[0].sockets, None, c.settings)
        with self.assertRaisesRegex(H.Refusal, 'shared_missing_planned_graph_binding'):
            c.bridge.begin_references()

    def test_gather_after_reference_phase_is_refused(self):
        c = self.case().gather(); c.serialize()
        with self.assertRaisesRegex(H.Refusal, 'shared_cache_call_contract'):
            c.call('gather_image', c.cases[0].sockets, None, c.settings)

    def test_final_reference_indices_and_serialized_shared_incidence_remain_strict(self):
        c = self.case().gather(); document = c.serialize()
        self.assertEqual(document['textures'], [{'source':0}, {'source':0}])
        bad = copy.deepcopy(document); bad['textures'][1]['source'] = 1
        with self.assertRaises(H.Refusal): c.resources.finalize(bad)
        with self.assertRaises(H.Refusal): c.resources.finalize(document)
        c = self.case().gather(); document = c.serialize()
        c.resources.finalize(document)
        with self.assertRaises(H.Refusal): c.resources.reference('image', c.resources.images[0]['image'], 1)

    def test_cold_cache_calls_require_exact_roles_positional_schema_and_real_wrapper(self):
        for mode in ('unknown', 'foreign', 'kwargs', 'short'):
            c = self.case()
            name, original, args, kwargs = 'gather_image', c.specs['gather_image'], (c.cases[0].sockets, None, c.settings), {}
            if mode == 'unknown': name = 'foreign'
            if mode == 'foreign': original = lambda *args: None
            if mode == 'kwargs': kwargs = {'export_settings': c.settings}
            if mode == 'short': args = args[:-1]
            with self.assertRaises(H.Refusal): c.bridge.call(name, original, args, kwargs)


class SessionWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache, cls.binary = primary_definitions()

    def fixture(self):
        old = F.fake_session()
        case = Case(self.cache, self.binary, attach=False)
        old.surface.shared_cache_specs = case.specs
        old.surface.shared_binary_type = self.binary
        for name, (module_name, function) in H.SHARED_CACHE_LOCATIONS.items():
            if module_name not in old.surface.modules: old.surface.modules[module_name] = NS()
            setattr(old.surface.modules[module_name], function, case.specs[name])
        session = H.ExportHookSession(old.surface, old.session.admissions, F.NP, case.resources, lambda: None, old.session.options)
        case.bridge = session.shared_cache
        old.settings['gltf_user_extensions'] = [session]
        session.preflights, session.settings = 0, None
        return old, case, session

    def test_shared_session_requires_explicit_extra_pinned_surface(self):
        old = F.fake_session(); case = Case(self.cache, self.binary, attach=False)
        old.surface.shared_cache_specs, old.surface.shared_binary_type = None, None
        with self.assertRaisesRegex(H.Refusal, 'shared_image_explicit_pinned_surface_required'):
            H.ExportHookSession(old.surface, old.session.admissions, F.NP, case.resources, lambda: None, old.session.options)

    def test_all_shared_slots_are_owned_and_restored_on_original_operator_exception(self):
        old, case, session = self.fixture()
        sys.modules[old.extension.__name__] = old.extension
        error = RuntimeError('synthetic operator')
        try:
            with self.assertRaises(RuntimeError) as caught:
                with session.install(old.extension, [old.extension.__name__]):
                    session.pre_export_hook(old.settings)
                    for name, (module, function) in H.SHARED_CACHE_LOCATIONS.items():
                        self.assertIsNot(getattr(old.surface.modules[module], function), case.specs[name])
                    raise error
            self.assertIs(caught.exception, error)
            for name, (module, function) in H.SHARED_CACHE_LOCATIONS.items():
                self.assertIs(getattr(old.surface.modules[module], function), case.specs[name])
        finally:
            del sys.modules[old.extension.__name__]

    def test_swallowed_shared_observer_failure_keeps_session_latch_and_restores(self):
        old, case, session = self.fixture()
        sys.modules[old.extension.__name__] = old.extension
        try:
            with self.assertRaises(H.Refusal):
                with session.install(old.extension, [old.extension.__name__]):
                    session.pre_export_hook(old.settings)
                    case.duplicate_hook = True
                    try:
                        session._shared_cache_call('gather_image', case.specs['gather_image'],
                                                   (case.cases[0].sockets, None, old.settings), {})
                    except H.Refusal:
                        pass  # Deliberately imitate the pinned extension dispatcher.
            self.assertIsNotNone(session.latch.first)
            for name, (module, function) in H.SHARED_CACHE_LOCATIONS.items():
                self.assertIs(getattr(old.surface.modules[module], function), case.specs[name])
        finally:
            del sys.modules[old.extension.__name__]

    def test_partial_shared_install_restores_owned_earlier_slots_without_clobbering_foreign_slot(self):
        old, case, session = self.fixture()
        sys.modules[old.extension.__name__] = old.extension
        foreign = object()
        owner = old.surface.modules['texture_info']
        setattr(owner, '__gather_texture_info_helper', foreign)
        try:
            with self.assertRaises(H.Refusal):
                with session.install(old.extension, [old.extension.__name__]):
                    self.fail('partial installation must not yield')
            self.assertIs(getattr(owner, '__gather_texture_info_helper'), foreign)
            for name, (module, function) in H.SHARED_CACHE_LOCATIONS.items():
                if name != 'texture_info':
                    self.assertIs(getattr(old.surface.modules[module], function), case.specs[name])
        finally:
            del sys.modules[old.extension.__name__]


if __name__ == '__main__':
    unittest.main()
