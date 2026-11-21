"""Pure source/fake-reference tests; no assets, Blender, native or process runs.

Root alone executes. Three pinned SDK SOURCE files supply the lexical TinyPath
and ordinary resolver/lookup definitions; their IO methods are never invoked.
Actual host/runtime/native/normal qualification is not inferred from these fakes.
"""
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
import textwrap
import types
import unittest
from types import SimpleNamespace as NS

import material_binding as B
import resolved_profile as P
import test_material_binding_default as F

SDK = Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
PINS = {
    'library/utils/tiny_path.py': (6259, '630299955d9becd10021774cf759f2070436c777e4218f8ef016a3c26a11784e'),
    'blender_bindings/models/materials.py': (1940, 'd0ef0bb1fa338d59b481fd1e12f607feab66606b21ab5d3be53233e734602979'),
    'blender_bindings/utils/bpy_utils.py': (7221, '4c8bb4a31ed7cac3278567632673acf53befd84dc852635dff813a20f38332e4'),
}


def source(name):
    raw = (SDK/name).read_bytes()
    count, expected = PINS[name]
    if len(raw) != count or hashlib.sha256(raw).hexdigest() != expected:
        raise AssertionError('exact primary source required')
    return raw


def primary_tiny():
    namespace = {'__name__': '_has_tiny_path_cpu_only'}
    exec(compile(source('library/utils/tiny_path.py'), str(SDK/'library/utils/tiny_path.py'), 'exec', dont_inherit=True), namespace)
    # Explicit Windows lexical behavior for this Windows-only qualification;
    # no filesystem methods are called even if the source is inspected elsewhere.
    namespace['is_windows'] = True
    namespace['os'] = NS(name='nt')
    return namespace['TinyPath']


def definitions(raw, names, namespace, filename):
    nodes = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise AssertionError('exact source function set required')
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), filename, 'exec', dont_inherit=True), namespace)
    return namespace


class Material(F.Material):
    def __init__(self, name):
        super().__init__(name)
        self.library = None
        self.writes = 0
    def keys(self): return self.properties.keys()
    def get(self, key, default=None): return self.properties.get(key, default)
    def __setitem__(self, key, value):
        self.writes += 1
        raise AssertionError('no Material property writes are allowed')


class Domain(list):
    def __init__(self, rows): super().__init__(rows); self.new_calls = 0
    def new(self, *_args, **_kwargs):
        self.new_calls += 1
        raise AssertionError('ordinary lookup must reuse the already inspected exact B ref')


class Fixture:
    def __init__(self, tiny, chosen=(1, 0, 2, 1)):
        self.T = tiny
        self.f = F.Fixture()
        self.names = ('test/Hair', 'test/Hat', 'test/Skin', 'test/Shoe')
        self.paths = ['', 'models/unit/', 'MODELS/UNIT', 'C:/skip', 'alternate']
        table = self.f.metadata['metadata']
        table['materials'] += [dict(index=2, name=self.names[2], flags=2, used=1), dict(index=3, name=self.names[3], flags=3, used=1)]
        table.update(search_paths=list(self.paths), skin_reference_count=4, skin_families=[[0,1,2,3], [1,1,2,3]])
        self.materials = tuple(Material(name) for name in self.names)
        for name, material, ordinal in zip(self.names, self.materials, chosen):
            prefix = ('', 'models/unit/', 'alternate/')[ordinal]
            material.properties['full_path'] = (prefix + name).casefold()
        self.f.placeholders = list(self.materials)
        self.f.materials = [F.NativeMaterial(name, row['flags'], row['used'], None)
                            for name, row in zip(self.names, table['materials'])]
        self.f.skins = [[self.f.materials[index] for index in family] for family in table['skin_families']]
        original_set_late = self.f.set_late
        def late(name, mode='MATERIAL_ID'):
            original_set_late(name, mode)
            if name == 'front.smd': self.f.objects[name].data.materials[:] = list(self.materials[:2])
            self.f.objects[name].properties['skin_groups'] = {
                str(index): [self.materials[value] if mode == 'MATERIAL_ID' else self.materials[value].name for value in family]
                for index, family in enumerate(table['skin_families'])}
        self.f.set_late = late
        self.mdl = NS(materials=self.f.materials, materials_paths=list(self.paths))
        factory = Material('factory'); factory.properties.clear()
        self.domain = Domain([factory, *self.materials])
        self.witness = None
        namespace = {'TinyPath': tiny, 'ContentManager': object}
        self.resolver = definitions(source('blender_bindings/models/materials.py'),
            ('resolve_model_material', 'get_model_material_names'), namespace, str(SDK/'blender_bindings/models/materials.py'))
        lookup = {'TinyPath': tiny, 'bpy': NS(data=NS(materials=self.domain)), 'random': NS(uniform=lambda *_: 0)}
        self.lookup = definitions(source('blender_bindings/utils/bpy_utils.py'), ('get_or_create_material',), lookup,
                                  str(SDK/'blender_bindings/utils/bpy_utils.py'))['get_or_create_material']
        globals_ = dict(get_model_material_names=self.resolver['get_model_material_names'], get_or_create_material=self.lookup)
        exec('def import_model(content_manager, mdl):\n'
             '    names = get_model_material_names(content_manager, mdl)\n'
             '    for material in mdl.materials:\n'
             '        if material.bpy_material is None:\n'
             '            material.bpy_material = get_or_create_material(material.name, names[material.name])\n'
             '    return names\n', globals_)
        self.importer = globals_['import_model']

    def create(self, bind=True):
        self.witness = P.ResolvedMaterialPaths(self.f.native, self.f.metadata, self.mdl, self.materials,
            source_material_type=F.NativeMaterial, material_type=Material, tiny_path_type=self.T,
            material_domain_supplier=lambda: tuple(self.domain))
        if bind: self.bind()
        return self.witness

    def bind(self):
        self.witness.bind_resolver(self.resolver['resolve_model_material'], self.resolver['get_model_material_names'],
                                   self.lookup, self.importer)

    def resolve(self):
        self.importer(self.witness.provider, self.mdl)
        self.witness.check(require_resolution=True)
        return self.witness

    def collector(self):
        return P.ResolvedMaterialBinding(self.f.native, self.f.metadata, witness=self.witness,
            source_material_type=F.NativeMaterial, source_model_type=F.NativeModel, source_body_type=F.NativeBody,
            source_mesh_type=F.NativeMesh, object_type=F.Object, mesh_types=(F.Mesh,), material_type=Material)


class Paths(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.T = primary_tiny()

    def fixture(self, **kwargs): return Fixture(self.T, **kwargs)

    def test_exact_primary_lexical_rules_and_ordered_finite_resolution_reuse_without_writes(self):
        c = self.fixture(); before = [dict(mat.properties) for mat in c.materials]
        witness = c.create(); c.resolve()
        self.assertEqual([[row['path_text'] for row in values] for values in witness.candidates], [
            [name, 'models/unit/' + name, 'alternate/' + name] for name in c.names])
        self.assertEqual([path.as_posix() for path in c.mdl._resolved_material_paths.values()],
                         ['models/unit/test/Hair', 'test/Hat', 'alternate/test/Skin', 'models/unit/test/Shoe'])
        self.assertTrue(all(ref.bpy_material is material for ref, material in zip(c.f.materials, c.materials)))
        self.assertEqual([dict(mat.properties) for mat in c.materials], before)
        self.assertEqual([mat.writes for mat in c.materials], [0,0,0,0])
        self.assertEqual(c.domain.new_calls, 0)
        self.assertEqual((witness.summary['provider_queries'], witness.summary['provider_true'], witness.summary['provider_false']), (8,4,4))
        self.assertTrue(witness.summary['no_file_existence_claim'])
        self.assertTrue(witness.summary['no_metadata_writes'])

    def test_windows_case_separator_and_trailing_slash_match_only_genuine_lookup_relation(self):
        c = self.fixture()
        c.materials[0].properties['full_path'] = r'MODELS\UNIT\TEST\HAIR/'
        c.create(); c.resolve()
        self.assertIs(c.f.materials[0].bpy_material, c.materials[0])

    def test_all_four_missing_nonstring_nonmember_rows_are_observed_before_refusal(self):
        for mode, code in (('missing', 'PRELOADED_FULL_PATH_MISSING'), ('nonstring', 'PRELOADED_FULL_PATH_NOT_STRING'),
                           ('foreign', 'PRELOADED_FULL_PATH_NOT_ONE_NATIVE_CANDIDATE')):
            c = self.fixture()
            if mode == 'missing': del c.materials[0].properties['full_path']
            if mode == 'nonstring': c.materials[0].properties['full_path'] = 17
            if mode == 'foreign': c.materials[0].properties['full_path'] = 'foreign/unrelated'
            with self.assertRaisesRegex(P.ProfileRefusal, '^' + code + '$') as caught: c.create()
            summary = caught.exception.summary
            self.assertEqual((summary['metadata_rows_observed'], summary['genuine_material_rows']), (4,4))
            self.assertEqual(summary['full_path_present'], 3 if mode == 'missing' else 4)
            self.assertEqual(summary['full_path_string'], 3 if mode != 'foreign' else 4)
            self.assertEqual(summary['candidate_membership_matches'], 3)
            self.assertEqual(sum(mat.writes for mat in c.materials), 0)
            self.assertFalse(hasattr(c.mdl, '_resolved_material_paths'))

    def test_same_valued_b_reference_alias_and_outside_domain_are_refused(self):
        for mode in ('selected_alias', 'domain_missing', 'global_duplicate'):
            c = self.fixture()
            if mode == 'selected_alias': c.materials = (c.materials[0], c.materials[0], *c.materials[2:])
            if mode == 'domain_missing': c.domain.remove(c.materials[2])
            if mode == 'global_duplicate':
                duplicate = Material('another'); duplicate.properties['full_path'] = c.materials[0].get('full_path')
                c.domain.insert(0, duplicate)
            with self.assertRaises(P.ProfileRefusal) as caught: c.create()
            self.assertEqual(caught.exception.summary['metadata_rows_observed'], 4)
            self.assertEqual(c.domain.new_calls, 0)

    def test_nonstring_unselected_domain_metadata_refuses_before_ordinary_lookup(self):
        c = self.fixture(); c.domain[0].properties['full_path'] = None
        with self.assertRaisesRegex(P.ProfileRefusal, 'CURRENT_DOMAIN_FULL_PATH_NOT_STRING') as caught: c.create()
        self.assertEqual(caught.exception.summary['full_path_string'], 4)
        self.assertEqual(c.domain.new_calls, 0)

    def test_oversized_selected_or_domain_full_path_refuses_without_metadata_writes(self):
        for selected in (True, False):
            c = self.fixture()
            target = c.materials[0] if selected else c.domain[0]
            target.properties['full_path'] = 'x' * 4097
            with self.assertRaisesRegex(P.ProfileRefusal, 'BOUNDED_PRELOADED_FULL_PATH_REQUIRED' if selected else
                                         'BOUNDED_CURRENT_DOMAIN_FULL_PATH_REQUIRED') as caught:
                c.create()
            self.assertEqual(caught.exception.summary['metadata_rows_observed'], 4)
            self.assertEqual(caught.exception.summary['full_path_string'], 4)
            self.assertEqual(c.domain.new_calls, 0)

    def test_independent_and_actual_mdl_names_paths_and_refs_must_agree(self):
        for mode in ('native_name', 'source_name', 'paths', 'source_ref'):
            c = self.fixture()
            if mode == 'native_name': c.f.metadata['metadata']['materials'][0]['name'] = 'different'
            if mode == 'source_name': c.f.materials[0].name = 'different'
            if mode == 'paths': c.mdl.materials_paths.reverse()
            if mode == 'source_ref': c.mdl.materials[0] = object()
            with self.assertRaises(P.ProfileRefusal) as caught: c.create()
            self.assertEqual(caught.exception.summary['metadata_rows_observed'], 4)

    def test_initial_resolver_cache_must_be_absent_even_if_empty_or_same_valued(self):
        for cache in ({}, {'test/Hair': None}, {'test/Hair': 'models/unit/test/Hair'}):
            c = self.fixture(); c.mdl._resolved_material_paths = cache
            with self.assertRaisesRegex(P.ProfileRefusal, 'RESOLVER_CACHE_NOT_FRESH_BEFORE_IMPORT'): c.create()

    def test_preflight_check_can_precede_bind_but_provider_cannot_resolve_without_it(self):
        c = self.fixture(); witness = c.create(bind=False)
        self.assertTrue(witness.check(False))
        with self.assertRaisesRegex(P.ProfileRefusal, 'ORDINARY_RESOLVER_NOT_BOUND'):
            witness.provider.check(c.T('materials/test/Hair.vmt'))

    def test_bind_checks_real_function_aliases_and_declines_rebinding(self):
        c = self.fixture(); witness = c.create()
        with self.assertRaises(P.ProfileRefusal): c.bind()
        c = self.fixture(); witness = c.create(bind=False)
        c.importer.__globals__['get_model_material_names'] = lambda *_: {}
        with self.assertRaisesRegex(P.ProfileRefusal, 'ORDINARY_RESOLVER_LOOKUP_IMPORTER_ALIAS_CHANGED'): c.bind()

    def test_provider_refuses_foreign_type_out_of_domain_order_and_io_methods(self):
        for value in ('materials/test/Hair.vmt', None):
            c = self.fixture(); witness = c.create()
            with self.assertRaises(P.ProfileRefusal): witness.provider.check(value)
        c = self.fixture(); witness = c.create()
        with self.assertRaisesRegex(P.ProfileRefusal, 'PROVIDER_QUERY_OUTSIDE_NATIVE_ORDERED_DOMAIN'):
            witness.provider.check(c.T('materials/foreign/not-native.vmt'))
        c = self.fixture(); witness = c.create()
        with self.assertRaisesRegex(P.ProfileRefusal, 'UNSUPPORTED_PRELOADED_PROVIDER_IO_METHOD'):
            witness.provider.find_file(c.T('anything'))

    def test_provider_true_does_not_claim_a_material_file_exists(self):
        c = self.fixture(chosen=(0,0,0,0)); witness = c.create()
        self.assertTrue(witness.provider.check(c.T('materials/test/Hair.vmt')))
        self.assertEqual(witness.summary['provider_true'], 1)
        self.assertFalse(hasattr(c.mdl, '_resolved_material_paths'))
        self.assertTrue(witness.summary['no_file_existence_claim'])
        self.assertTrue(all(ref.bpy_material is None for ref in c.f.materials))

    def test_complete_resolution_cannot_be_manufactured_from_queries_without_actual_cache(self):
        c = self.fixture(); witness = c.create()
        witness.provider.check(witness.expected_queries[0][1]['query'])
        with self.assertRaisesRegex(P.ProfileRefusal, 'ORDINARY_RESOLVER_CACHE_MISSING'):
            witness.provider.check(witness.expected_queries[1][1]['query'])
        with self.assertRaises(P.ProfileRefusal): witness.check(True)

    def test_cached_resolver_object_path_ref_domain_and_value_drift_are_refused(self):
        for mode in ('dict', 'same_path_ref', 'foreign_path', 'foreign_type', 'extra_key', 'order'):
            c = self.fixture(); witness = c.create(); c.resolve()
            cache = c.mdl._resolved_material_paths
            if mode == 'dict': c.mdl._resolved_material_paths = dict(cache)
            if mode == 'same_path_ref': cache[c.names[0]] = c.T(cache[c.names[0]].as_posix())
            if mode == 'foreign_path': cache[c.names[0]] = c.T('foreign/path')
            if mode == 'foreign_type': cache[c.names[0]] = cache[c.names[0]].as_posix()
            if mode == 'extra_key': cache['foreign'] = c.T('foreign')
            if mode == 'order': c.mdl._resolved_material_paths = dict(reversed(tuple(cache.items())))
            with self.assertRaises(P.ProfileRefusal): witness.check(True)

    def test_current_source_b_ref_substitution_or_reversion_cannot_use_equal_metadata(self):
        for mode in ('lookalike', 'None'):
            c = self.fixture(); witness = c.create(); c.resolve()
            c.f.materials[0].bpy_material = Material(c.names[0]) if mode == 'lookalike' else None
            with self.assertRaisesRegex(P.ProfileRefusal, 'ACTUAL_NATIVE_B_MATERIAL_REFERENCE_SUBSTITUTED'):
                witness.check(True)

    def test_domain_ref_order_raw_metadata_or_lookup_namespace_drift_refuses(self):
        for mode in ('order', 'raw', 'lookup_bpy', 'path_list', 'resolver_alias'):
            c = self.fixture(); witness = c.create(); c.resolve()
            if mode == 'order': c.domain.reverse()
            if mode == 'raw': c.materials[0].properties['full_path'] = c.materials[0].get('full_path').upper()
            if mode == 'lookup_bpy': c.lookup.__globals__['bpy'] = NS(data=NS(materials=list(c.domain[:-1])))
            if mode == 'path_list': c.mdl.materials_paths.append('new')
            if mode == 'resolver_alias': c.resolver['get_model_material_names'].__globals__['resolve_model_material'] = lambda *_: None
            with self.assertRaises(P.ProfileRefusal): witness.check(True)

    def test_public_summary_and_refusal_never_expose_raw_names_paths_refs_or_arrays(self):
        c = self.fixture(); witness = c.create(); c.resolve()
        public = json.dumps(witness.summary)
        for text in ('test/Hair', 'models/unit', 'alternate', 'full_path":', 'properties', 'pointer'):
            self.assertNotIn(text, public)
        for key in ('candidate_order_sha256', 'native_path_provenance_sha256', 'current_reference_witness_sha256', 'resolved_cache_witness_sha256'):
            self.assertEqual(len(witness.summary[key]), 64)
        for key, value in witness.summary.items():
            if key.endswith('_qualified') or key == 'exporter_invoked': self.assertIs(value, False)

    def test_immutable_provenance_digests_stay_stable_while_check_counters_advance(self):
        c = self.fixture(); witness = c.create(); c.resolve()
        first = witness.summary
        witness.check(True); witness.check(False)
        second = witness.summary
        for key in ('candidate_order_sha256', 'native_path_provenance_sha256', 'current_reference_witness_sha256', 'resolved_cache_witness_sha256'):
            self.assertEqual(first[key], second[key])
        self.assertGreater(second['check_calls'], first['check_calls'])
        copy_ = witness.summary; copy_['provider_true'] = -1
        self.assertEqual(witness.summary['provider_true'], 4)

    def test_selected_query_collision_across_native_domains_is_not_a_first_match(self):
        c = self.fixture(chosen=(1,0,0,0))
        c.names = ('test/Hair', 'models/unit/test/Hair', 'test/Skin', 'test/Shoe')
        c.f.metadata['metadata']['materials'][1]['name'] = c.names[1]
        c.f.materials[1].name = c.names[1]
        c.materials[1].name = c.names[1]
        c.materials[1].properties['full_path'] = 'alternate/models/unit/test/hair'
        with self.assertRaisesRegex(P.ProfileRefusal, 'SELECTED_QUERY_AMBIGUOUS_ACROSS_NATIVE_MATERIALS'):
            c.create()

    def test_same_bare_default_is_unchanged_but_opt_in_allows_only_qualified_prefix(self):
        c = self.fixture(); witness = c.create(); c.resolve()
        default = B.MaterialBinding(c.f.native, c.f.metadata, source_material_type=F.NativeMaterial,
            source_model_type=F.NativeModel, source_body_type=F.NativeBody, source_mesh_type=F.NativeMesh,
            object_type=F.Object, mesh_types=(F.Mesh,), material_type=Material)
        with self.assertRaisesRegex(B.Refusal, 'NO_MATERIAL_IO_PLACEHOLDER_NAME_OR_PATH_DIFFERS'):
            c.f.observe(default, 'before_setter')
        collector = c.collector(); c.f.complete(collector)
        result = c.f.returned(collector)
        self.assertEqual(result['format'], 'has_fresh_sourceio_resolved_material_slot_skin_observation_1')
        self.assertEqual((result['native_path_witness']['phase_observations'], result['native_path_witness']['returned_observations']), (8,1))
        self.assertTrue(result['native_path_witness']['returned_binding_observed'])
        self.assertFalse(result['external_material_file_existence_qualified'])
        self.assertFalse(result['B_material_properties_written'])
        self.assertEqual(c.domain.new_calls, 0)

    def test_opt_in_source_method_differs_only_in_the_one_explicit_path_predicate(self):
        base = textwrap.dedent(inspect.getsource(B.MaterialBinding._source))
        changed = textwrap.dedent(inspect.getsource(P.ResolvedMaterialBinding._source))
        self.assertEqual(base.count("full_path == name.lstrip('/').casefold()"), 1)
        expected = base.replace("full_path == name.lstrip('/').casefold()", 'self.witness.source_row(ref, placeholder, name, full_path)')
        self.assertEqual(ast.dump(ast.parse(expected)), ast.dump(ast.parse(changed)))

    def test_slot_skin_source_ref_and_snapshot_other_fields_remain_strict(self):
        for mode in ('slot', 'skin', 'source_ref', 'actual_name'):
            c = self.fixture(); witness = c.create(); c.resolve(); collector = c.collector()
            if mode == 'slot':
                c.f.through_early(collector); c.f.set_late('front.smd'); c.f.objects['front.smd'].data.materials.reverse()
                operation = lambda: c.f.observe(collector, 'before_validate')
            else:
                snapshot = c.f.snapshot('front.smd')
                if mode == 'skin': snapshot['source_skins'] = (tuple(reversed(snapshot['source_skins'][0])), *snapshot['source_skins'][1:])
                if mode == 'source_ref':
                    row = snapshot['source_materials'][0]
                    replacement = F.NativeMaterial(row[1], row[2], row[3], row[4])
                    snapshot['source_materials'] = ((replacement, *row[1:]), *snapshot['source_materials'][1:])
                if mode == 'actual_name':
                    row = snapshot['source_materials'][0]
                    snapshot['source_materials'] = ((*row[:5], 'foreign', row[6]), *snapshot['source_materials'][1:])
                operation = lambda: c.f.observe(collector, 'before_setter', snapshot=snapshot)
            with self.assertRaises(B.Refusal): operation()
            self.assertIsNotNone(collector.failed)

    def test_caught_witness_failure_cannot_return_a_successful_binding(self):
        c = self.fixture(); witness = c.create(); c.resolve(); collector = c.collector()
        c.materials[0].properties['full_path'] = 'foreign'
        with self.assertRaises(P.ProfileRefusal): c.f.observe(collector, 'before_setter')
        c.materials[0].properties['full_path'] = 'models/unit/test/hair'
        with self.assertRaises(B.Refusal): c.f.returned(collector)


if __name__ == '__main__':
    unittest.main()
