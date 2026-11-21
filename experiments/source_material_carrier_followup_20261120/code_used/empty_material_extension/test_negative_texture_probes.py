"""Pure fake RNA + pinned SDK filter/helper/cache code. No bpy/native import.

The actual texture_info source is compiled only and its two functions receive
explicit fake navigation/resource globals. This tests the absent branch, not
an actual SDK export. Root alone executes; no source is patched in place.
"""
import hashlib
import types
import unittest

import export_hook_proposal as H
import resource_gate_proposal as R
import shared_image_cache_proposal as S
import test_export_hook_proposal as F
import test_shared_image_cache_proposal as P


def direct(code, name):
    rows = [value for value in code.co_consts if type(value) is types.CodeType and value.co_name == name]
    if len(rows) != 1: raise AssertionError('unique pinned direct function code required')
    return rows[0]


class BoundedSockets:
    # Blender RNA socket collections expose len(); the inherited old fakes do not.
    def __init__(self, original): self.values, self.named = original.values, original.named
    def __iter__(self): return iter(self.values)
    def __len__(self): return len(self.values)
    def __getitem__(self, key): return self.named[key]


def case(*, malicious=None):
    cache, binary = P.primary_definitions()
    c = P.Case(cache, binary, (0,), attach=False)
    source_case = c.cases[0]
    for identifier in ('Emission Color', 'Normal'):
        socket = F.Socket(node=source_case.shader, default_value=None, identifier=identifier,
                          is_output=False, id_data=source_case.tree)
        source_case.shader.inputs.values.append(socket)
        source_case.shader.inputs.named[identifier] = socket
    source_case.shader.inputs = BoundedSockets(source_case.shader.inputs)
    c.resources = R.SimplePackedResources((source_case.material,), c.tickets, F.rna_types(),
        types.SimpleNamespace(NodeSocket=F.NodeSocket), F.ENCODE, F.GLTF, allow_shared_images=True)
    c.lookups, c.positive_steps = [], []
    path, digest = H.PINS['texture_info']
    path = H.EXPORTER_ROOT / path
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest: raise AssertionError('exact pinned texture_info source required')
    compiled = compile(raw, str(path), 'exec', dont_inherit=True)
    def node_from_socket(wrapper, settings):
        c.lookups.append(wrapper)
        # Independent fake graph navigation; the real SDK filter decides absent.
        links = [link for link in source_case.tree.links
                 if link.to_socket.as_pointer() == wrapper.socket.as_pointer()]
        return None if not links else types.SimpleNamespace(shader_node=links[0].from_node)
    def transform(primary, settings):
        c.positive_steps.append('transform')
        return None, {}
    def index(sockets, tile, settings):
        c.positive_steps.append('index')
        return c.call('gather_texture', sockets, tile, settings)
    def dispatch(name, settings, info, sockets):
        if name != 'gather_texture_info_hook': raise AssertionError('unexpected resource hook')
        c.positive_steps.append('hook')
        c.resources.texture_info(info, sockets)
    def forbidden(*args, **kwargs): raise AssertionError('unadmitted normal/occlusion resource creation')
    namespace = dict(get_texture_node_from_socket=node_from_socket,
        __gather_texture_transform_and_tex_coord=transform, __gather_index=index,
        __gather_extensions=lambda *args: None, __gather_extras=lambda *args: None,
        export_user_extensions=dispatch,
        gltf2_io=types.SimpleNamespace(TextureInfo=F.TextureInfo,
            MaterialNormalTextureInfoClass=forbidden, MaterialOcclusionTextureInfoClass=forbidden))
    namespace['__filter_texture_info'] = types.FunctionType(direct(compiled, '__filter_texture_info'), namespace)
    actual = types.FunctionType(direct(compiled, '__gather_texture_info_helper'), namespace)
    if malicious is None: function = actual
    else:
        def function(primary, sockets, kind, filter_type, settings):
            return malicious(c, actual, primary, sockets, kind, filter_type, settings)
    c.specs['texture_info'] = cache['cached'](function)
    c.bridge = S.SharedImageCaches(c.resources, c.specs, binary, F.Image)
    c.probe = lambda name='Emission Color': F.NodeSocket(source_case.shader.inputs[name], [source_case.tree])
    return c


def probe(c, *, name='Emission Color', kind='DEFAULT', filter_type='ALL', wrapper=None):
    wrapper = c.probe(name) if wrapper is None else wrapper
    return c.call('texture_info', wrapper, (wrapper,), kind, filter_type, c.settings)


class NegativeTextureProbes(unittest.TestCase):
    def test_pinned_sdk_emission_absence_has_exact_result_and_creates_no_resources(self):
        c = case(); result = probe(c)
        self.assertEqual(result, (None, {}, {}, None))
        self.assertEqual(c.positive_steps, [])
        self.assertEqual(c.body_calls, [])
        for name in ('descriptors', 'images', 'image_bindings', 'textures', 'infos', 'gathered_materials'):
            self.assertEqual(getattr(c.resources, name), [])
        self.assertEqual(len(c.bridge.absences), 1)
        self.assertEqual(c.bridge.specs['texture_info']['calls'], 1)
        self.assertEqual(c.bridge.specs['texture_info']['misses'], 1)
        self.assertTrue(all(row['calls'] == 0 for name, row in c.bridge.specs.items() if name != 'texture_info'))
        self.assertEqual(c.bridge.encoded_bytes, 0)

    def test_pinned_sdk_normal_absence_returns_before_normal_texture_constructor(self):
        c = case(); result = probe(c, name='Normal', kind='NORMAL')
        self.assertEqual(result, (None, {}, {}, None))
        self.assertEqual(c.positive_steps, []); self.assertEqual(c.body_calls, [])
        self.assertEqual(c.bridge.absences[0]['kind'], 'NORMAL')

    def test_genuine_cache_hit_preserves_first_absent_result_and_does_not_replay_body(self):
        c = case(); wrapper = c.probe()
        first = probe(c, wrapper=wrapper); second = probe(c, wrapper=wrapper)
        self.assertIs(second, first)
        self.assertEqual(len(c.lookups), 1)
        self.assertEqual((len(c.bridge.absences), c.bridge.absence_hits), (1, 1))
        self.assertEqual(c.bridge.specs['texture_info']['hits'], 1)

    def test_fresh_wrapper_for_same_c_pointer_is_a_real_distinct_cache_miss(self):
        c = case(); first, second = c.probe(), c.probe()
        self.assertIsNot(first, second)
        a, b = probe(c, wrapper=first), probe(c, wrapper=second)
        self.assertIsNot(a, b)
        self.assertEqual(len(c.lookups), 2)
        self.assertEqual(len(c.bridge.absences), 2)
        self.assertEqual(c.bridge.absence_hits, 0)

    def test_absent_probe_does_not_become_an_image_descriptor_binding_key(self):
        c = case(); wrapper = c.probe()
        with self.assertRaises(H.Refusal): c.resources._socket_key((wrapper,))
        with self.assertRaises(H.Refusal): c.resources.before_image_data((wrapper,), None)
        self.assertEqual(c.resources.descriptors, [])

    def test_absence_then_positive_image_binding_keeps_original_coverage_and_reference_gates(self):
        c = case(); probe(c); probe(c, name='Normal', kind='NORMAL')
        c.gather(); document = c.serialize()
        summary = c.resources.finalize(document)
        self.assertEqual((len(c.resources.images), len(c.resources.image_bindings), len(c.resources.infos)), (1, 1, 1))
        cache_report = c.bridge.summary()
        self.assertEqual(cache_report['observed_negative_texture_probe_misses'], 2)
        self.assertEqual(cache_report['observed_negative_texture_probe_hits'], 0)
        self.assertFalse(cache_report['actual_export_or_native_fidelity_qualified'])
        self.assertEqual(summary['image_bindings'], 1)

    def test_connected_image_with_wrong_kind_is_not_treated_as_an_absence(self):
        c = case(); wrapper = c.cases[0].sockets[0]
        with self.assertRaises(H.Refusal): probe(c, wrapper=wrapper, kind='NORMAL')
        self.assertEqual(c.lookups, [])
        self.assertTrue(c.bridge.failed)

    def test_none_empty_group_foreign_socket_and_output_are_refused_before_key_lookup(self):
        for variant in ('none', 'missing', 'group', 'foreign', 'output', 'image_input'):
            with self.subTest(variant=variant):
                c = case(); f = c.cases[0]
                wrapper = {'none': None, 'missing': F.NodeSocket(None, None),
                    'group': F.NodeSocket(f.shader.inputs['Emission Color'], [f.tree, f.tree]),
                    'foreign': F.NodeSocket(F.Socket(node=f.shader, id_data=f.tree, default_value=None,
                        identifier='Emission Color', is_output=False), [f.tree]),
                    'output': F.NodeSocket(f.shader.outputs['BSDF'], [f.tree]),
                    'image_input': F.NodeSocket(f.tex.inputs['Vector'], [f.tree])}[variant]
                with self.assertRaises(H.Refusal): c.call('texture_info', wrapper, (wrapper,), 'DEFAULT', 'ALL', c.settings)
                self.assertEqual(c.lookups, [])

    def test_unsupported_kind_filter_and_multiple_probe_sockets_remain_refused(self):
        for kind, filtering in (('OCCLUSION', 'ALL'), ('DEFAULT', 'ANY'), ('DEFAULT', 'NONE'), ('UNKNOWN', 'ALL')):
            with self.subTest(kind=kind, filter=filtering):
                c = case()
                with self.assertRaises(H.Refusal): probe(c, kind=kind, filter_type=filtering)
                self.assertEqual(c.lookups, [])
        c = case(); wrapper = c.probe()
        with self.assertRaises(H.Refusal): c.call('texture_info', wrapper, (wrapper, c.probe('Normal')), 'DEFAULT', 'ALL', c.settings)

    def test_probe_primary_must_be_the_same_known_c_socket_as_single_input(self):
        c = case()
        with self.assertRaises(H.Refusal):
            c.call('texture_info', c.probe(), (c.probe('Normal'),), 'DEFAULT', 'ALL', c.settings)
        self.assertEqual(c.lookups, [])

    def test_link_or_default_or_metadata_drift_after_preflight_refuses(self):
        for change in ('link', 'default', 'identifier', 'membership'):
            with self.subTest(change=change):
                c = case(); f = c.cases[0]; wrapper = c.probe()
                if change == 'link': f.tree.links.append(f.link(f.tex.outputs['Color'], wrapper.socket))
                elif change == 'default': wrapper.socket.default_value = 0.2
                elif change == 'identifier': wrapper.socket.identifier = 'different'
                else: f.shader.inputs.values.remove(wrapper.socket)
                with self.assertRaises(H.Refusal): probe(c, wrapper=wrapper)
                self.assertEqual(c.lookups, [])

    def test_exact_absent_tuple_requires_real_empty_dicts_and_no_texture_or_factor(self):
        class ForeignDict(dict): pass
        for result in ((None, {}, {}, 1.0), (F.TextureInfo(index=0), {}, {}, None),
                       (None, {'uv': 0}, {}, None), (None, {}, {'udim': True}, None),
                       (None, ForeignDict(), {}, None), [None, {}, {}, None]):
            with self.subTest(result_type=type(result).__name__):
                c = case(malicious=lambda *args: result)
                with self.assertRaises(H.Refusal): probe(c)
                self.assertTrue(c.bridge.failed)

    def test_absent_return_cannot_hide_resource_creation_or_replacement(self):
        for field in ('descriptors', 'images', 'image_bindings', 'textures', 'infos', 'gathered_materials'):
            with self.subTest(field=field):
                def create(c, actual, primary, sockets, kind, filtering, settings):
                    getattr(c.resources, field).append(object())
                    return None, {}, {}, None
                c = case(malicious=create)
                with self.assertRaises(H.Refusal): probe(c)
                self.assertTrue(c.bridge.failed)

    def test_absent_return_cannot_hide_a_nested_genuine_positive_gather(self):
        def nested(c, actual, primary, sockets, kind, filtering, settings):
            c.call('gather_texture', c.cases[0].sockets, None, settings)
            return None, {}, {}, None
        c = case(malicious=nested)
        with self.assertRaises(H.Refusal): probe(c)
        self.assertTrue(c.bridge.failed)

    def test_cached_empty_result_mutation_is_refused_on_hit_and_final_coverage(self):
        c = case(); wrapper = c.probe(); result = probe(c, wrapper=wrapper); result[1]['changed'] = True
        with self.assertRaises(H.Refusal): probe(c, wrapper=wrapper)
        c = case(); result = probe(c); result[2]['changed'] = True
        with self.assertRaises(H.Refusal): c.bridge._coverage()

    def test_unknown_wrapper_equality_and_hash_are_not_called_during_argument_admission(self):
        class Foreign:
            def __eq__(self, other): raise AssertionError('foreign equality touched')
            def __hash__(self): raise AssertionError('foreign hash touched')
        c = case(); probe(c)
        with self.assertRaises(H.Refusal): c.call('texture_info', Foreign(), (Foreign(),), 'DEFAULT', 'ALL', c.settings)


if __name__ == '__main__':
    unittest.main()
