"""Synthetic resource metadata only. No bpy, native assets, media, Win32 or engines."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
import ast
import copy
import contextlib
import ctypes
import hashlib
import importlib.util
import json
import unittest
from ctypes import wintypes as W

import export_provenance as provenance
import loaded_survey
import probe_resources
import stager
from survey_admission import Unstageable
from survey_core import Budget, Limits, SurveyError, canonical, collect_resources, path_metadata

HERE = Path(__file__).resolve().parent
ORIGINAL = r'C:\protected\original\editable.blend'
OWNED = r'C:\owned\scene\editable.blend'


class RNA:
    next_id = 100
    def __init__(self, **values):
        RNA.next_id += 1
        self.identity = RNA.next_id
        self.__dict__.update(values)
    def as_pointer(self): return self.identity
    def __getattr__(self, name):
        raise AssertionError('Unadmitted RNA getter: ' + name)


class Packed(RNA):
    def __init__(self, payload=b'encoded synthetic bytes', size=None):
        super().__init__(size=len(payload) if size is None else size)
        self.payload = payload; self.data_reads = 0; self.changed_size = None
    @property
    def data(self):
        self.data_reads += 1
        if self.changed_size is not None: self.size = self.changed_size
        return self.payload


def image(path='//images/synthetic.png', packed=None, **values):
    items = [] if packed is None else [RNA(packed_file=packed, filepath=path, view=0, tile_number=1001)]
    row = dict(library=None, name='SYNTHETIC_PRIVATE_IMAGE', source='FILE', type='IMAGE',
               filepath=path, filepath_raw=path, alpha_mode='STRAIGHT', colorspace_settings=NS(name='sRGB'),
               is_dirty=False, has_data=False, use_multiview=False, is_multiview=False, is_stereo_3d=False,
               users=1, packed_files=items, packed_file=packed)
    row.update(values)
    return RNA(**row)


def node(kind='ShaderNodeTexImage', **values):
    return RNA(name='SYNTHETIC_PRIVATE_NODE', bl_idname=kind, **values)


def tree(nodes): return RNA(library=None, name='SYNTHETIC_PRIVATE_TREE', bl_idname='ShaderNodeTree', nodes=nodes)


def fixture(images=None, materials=None, paths=None):
    images = [image()] if images is None else images
    if materials is None:
        nodes = [] if not images else [node(image=images[0])]
        materials = [RNA(library=None, name='SYNTHETIC_PRIVATE_MATERIAL', use_nodes=True, node_tree=tree(nodes))]
    if paths is None: paths = [im.filepath for im in images if im.filepath]
    mesh = lambda name: RNA(type='MESH', name=name, hide_render=False, hide_get=lambda: False)
    bpy = NS(data=NS(libraries=[], images=images, materials=materials, filepath=OWNED),
             context=NS(scene=NS(objects=[mesh('Hat.smd'), mesh('hair.smd')]),
                        preferences=NS(filepaths=NS(use_scripts_auto_execute=False))), calls=[])
    names = ('load_pre', 'load_post', 'load_post_fail', 'depsgraph_update_pre', 'depsgraph_update_post',
             'frame_change_pre', 'frame_change_post', 'render_pre', 'render_post', 'save_pre', 'save_post')
    bpy.app = NS(background=True, online_access=False, autoexec_fail=False,
                 handlers=NS(**{name: [] for name in names}))
    def blend_paths(**kwargs):
        bpy.calls.append(kwargs)
        return list(paths)
    bpy.utils = NS(blend_paths=blend_paths)
    return bpy


def references():
    return {'format': 'has_source_normal_followup_hash_only_inputs_1',
            'files': {role: {'sha256': digest, 'bytes': provenance.SIZES[role]}
                      for role, digest in provenance.PINS.items()}}


class ResourceTests(unittest.TestCase):
    def test_minimal_metadata_private_paths_public_scalars_no_forbidden_getters(self):
        bpy = fixture(); private, public = collect_resources(bpy, ORIGINAL)
        self.assertEqual(public['status'], 'METADATA_SURVEY_ONLY')
        self.assertEqual(private['images'][0]['path']['original_base_candidate'], r'C:\protected\original\images\synthetic.png')
        self.assertEqual(private['images'][0]['pixel_properties'], 'UNOBSERVED_AVOID_IMBUF_ACQUISITION')
        self.assertNotIn('SYNTHETIC_PRIVATE', canonical(public).decode())
        self.assertNotIn('synthetic.png', canonical(public).decode())
        self.assertNotIn('C:', canonical(public).decode())
        self.assertFalse(private['external_path_contents_opened_or_statted'])
        self.assertEqual(bpy.calls, [{'absolute': False, 'packed': True, 'local': False}, {'absolute': False, 'packed': False, 'local': False}])
        self.assertEqual(public['private_metadata_sha256'], hashlib.sha256(canonical(private)).hexdigest())

    def test_empty_path_packed_invariants_and_payload_hash_only(self):
        packed = Packed(); im = image('', packed)
        private, public = collect_resources(fixture([im]), ORIGINAL)
        self.assertEqual(public['status'], 'METADATA_SURVEY_ONLY')
        self.assertEqual(public['empty_path_packed_images'], 1)
        self.assertEqual(private['images'][0]['filepath'], '')
        self.assertEqual(private['images'][0]['packed'][0]['sha256'], hashlib.sha256(packed.payload).hexdigest())
        self.assertNotIn(packed.payload.decode(), canonical(private).decode())
        self.assertEqual(packed.data_reads, 1)

    def test_raw_filepath_equivalence_and_basename_are_separate(self):
        images = [image('//a/name.png'), image('//a/name.png'), image('//b/name.png')]
        private, public = collect_resources(fixture(images), ORIGINAL)
        self.assertEqual([r['raw_filepath_class'] for r in private['images']], [0, 0, 1])
        self.assertEqual(public['raw_filepath_classes'], 2)
        self.assertEqual(public['distinct_nonempty_basenames'], 1)
        self.assertEqual([im.filepath for im in images], ['//a/name.png', '//a/name.png', '//b/name.png'])

    def test_conflicting_nonempty_path_packed_bytes_disclosed_but_empty_paths_independent(self):
        images = [image('//same/name.png', Packed(b'a')), image('//same/name.png', Packed(b'b'))]
        private, public = collect_resources(fixture(images), ORIGINAL)
        self.assertEqual(public['raw_path_classes_with_conflicting_packed_content'], 1)
        self.assertIn('SAME_RAW_PATH_CONFLICTING_PACKED_BYTES', {r['code'] for r in private['issues']})
        private, public = collect_resources(fixture([image('', Packed(b'a')), image('', Packed(b'b'))]), ORIGINAL)
        self.assertEqual(public['raw_path_classes_with_conflicting_packed_content'], 0)
        self.assertEqual(public['status'], 'METADATA_SURVEY_ONLY')

    def test_unused_default_generated_image_is_retained_and_refused(self):
        unused = image('', source='GENERATED', type='RENDER_RESULT', users=0)
        private, public = collect_resources(fixture([image(), unused]), ORIGINAL)
        self.assertEqual(len(private['images']), 2)
        self.assertEqual(private['images'][1]['users'], 0)
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')
        self.assertIn('UNSUPPORTED_IMAGE_SOURCE_OR_TYPE', {row['code'] for row in private['issues']})

    def test_image_profile_issues_are_inventory_not_deletion(self):
        im = image('https://invalid.example/private', filepath_raw='different', is_dirty=True, use_multiview=True)
        private, public = collect_resources(fixture([im]), ORIGINAL)
        self.assertEqual(len(private['images']), 1)
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')
        codes = {row['code'] for row in private['issues']}
        self.assertTrue({'DIRTY_IMAGE_REFUSED', 'FILEPATH_ALIAS_PROFILE_REFUSED', 'MULTIVIEW_REFUSED', 'PATH_PROFILE_REFUSED'} <= codes)

    def test_unknown_external_ref_and_network_path_inventory_are_preserved(self):
        private, public = collect_resources(fixture(paths=[r'\\server\share\missing.abc', '//unknown/cache.bin']), ORIGINAL)
        self.assertEqual(public['external_paths_including_packed'], 2)
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')
        self.assertEqual(private['external_path_references']['all'][0]['kind'], 'UNSUPPORTED_NETWORK_PATH')
        self.assertIn('UNCLASSIFIED_EXTERNAL_REFERENCE_REFUSED', {row['code'] for row in private['issues']})

    def test_linked_library_refused_before_image_or_data_traversal(self):
        bpy = fixture(); bpy.data.libraries = [RNA()]; bpy.data.images = None
        with self.assertRaisesRegex(SurveyError, 'LINKED_LIBRARIES_REFUSED'): collect_resources(bpy, ORIGINAL)

    def test_linked_image_and_material_and_tree_refused(self):
        for place, code in [('image', 'LINKED_IMAGE'), ('material', 'LINKED_MATERIAL'), ('tree', 'LINKED_NODE_TREE')]:
            bpy = fixture()
            target = bpy.data.images[0] if place == 'image' else bpy.data.materials[0]
            if place == 'tree': target = target.node_tree
            target.library = RNA()
            with self.assertRaisesRegex(SurveyError, code): collect_resources(bpy, ORIGINAL)

    def test_all_packed_sizes_admitted_before_any_data_getter(self):
        a, b = Packed(b'a'), Packed(b'bc')
        with self.assertRaisesRegex(SurveyError, 'TOTAL_PACKED_BOUND'):
            collect_resources(fixture([image('a', a), image('b', b)]), ORIGINAL, replace(Limits(), packed_bytes_total=2))
        self.assertEqual((a.data_reads, b.data_reads), (0, 0))

    def test_packed_single_size_count_and_payload_stability(self):
        for packed, code in [(Packed(size=True), 'INTEGER_BOUND'), (Packed(size=0), 'EMPTY_PACKED'),
                             (Packed(size=10**9), 'INTEGER_BOUND'), (Packed(b'x', 2), 'PACKED_BYTES_CHANGED')]:
            with self.assertRaisesRegex(SurveyError, code): collect_resources(fixture([image('', packed)]), ORIGINAL)
        packed = Packed(); packed.changed_size = 1
        with self.assertRaisesRegex(SurveyError, 'PACKED_BYTES_CHANGED'): collect_resources(fixture([image('', packed)]), ORIGINAL)
        packed = Packed(b'x'); packed.changed_size = True
        with self.assertRaisesRegex(SurveyError, 'PACKED_BYTES_CHANGED'): collect_resources(fixture([image('', packed)]), ORIGINAL)

    def test_packed_entry_path_is_inventoried_without_open_even_when_not_in_blend_paths(self):
        im = image('', Packed()); im.packed_files[0].filepath = r'\\server\private\packed.png'
        private, public = collect_resources(fixture([im], paths=[]), ORIGINAL)
        self.assertEqual(private['images'][0]['packed'][0]['path']['basename'], 'packed.png')
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')
        self.assertIn('PACKED_PATH_PROFILE_REFUSED', {r['code'] for r in private['issues']})

    def test_packed_pointer_count_and_first_identity(self):
        im = image('', Packed()); im.packed_file = None
        with self.assertRaisesRegex(SurveyError, 'PACKED_POINTER_COUNT'): collect_resources(fixture([im]), ORIGINAL)
        im = image('', Packed()); im.packed_file = Packed()
        with self.assertRaisesRegex(SurveyError, 'FIRST_PACKED_IDENTITY'): collect_resources(fixture([im]), ORIGINAL)

    def test_multiple_packed_payloads_are_disclosed_not_silently_dropped(self):
        im = image('', Packed()); second = Packed(b'two')
        im.packed_files.append(RNA(packed_file=second, filepath='', view=1, tile_number=1002))
        private, public = collect_resources(fixture([im]), ORIGINAL)
        self.assertEqual(public['packed_parts'], 2)
        self.assertEqual(len(private['images'][0]['packed']), 2)
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')

    def test_recursive_shared_tree_and_all_image_nodes_inventory(self):
        im = image(); child = tree([node('ShaderNodeTexEnvironment', image=im)])
        root = tree([node('ShaderNodeGroup', node_tree=child), node('ShaderNodeGroup', node_tree=child)])
        mat = RNA(library=None, name='MAT', use_nodes=True, node_tree=root)
        private, public = collect_resources(fixture([im], [mat]), ORIGINAL)
        self.assertEqual(public['node_trees'], 2)
        self.assertEqual(public['material_image_references'], 1)
        self.assertEqual(private['node_trees'][0]['nodes'][0]['group_tree'], private['node_trees'][0]['nodes'][1]['group_tree'])

    def test_node_tree_cycle_depth_and_total_node_bounds(self):
        bpy = fixture(); root = bpy.data.materials[0].node_tree
        root.nodes.append(node('ShaderNodeGroup', node_tree=root))
        with self.assertRaisesRegex(SurveyError, 'CYCLIC_NODE_TREE'): collect_resources(bpy, ORIGINAL)
        bpy = fixture(); bpy.data.materials[0].node_tree.nodes.append(node('ShaderNodeGroup', node_tree=tree([])))
        with self.assertRaisesRegex(SurveyError, 'NODE_TREE_DEPTH'): collect_resources(bpy, ORIGINAL, replace(Limits(), tree_depth=0))
        with self.assertRaisesRegex(SurveyError, 'COLLECTION_BOUND|TOTAL_NODE_BOUND'): collect_resources(fixture(), ORIGINAL, replace(Limits(), nodes=0))

    def test_image_reference_identity_and_reference_budget(self):
        bpy = fixture(); bpy.data.materials[0].node_tree.nodes[0].image = image()
        with self.assertRaisesRegex(SurveyError, 'IMAGE_REFERENCE_OUTSIDE_DATA'): collect_resources(bpy, ORIGINAL)
        with self.assertRaisesRegex(SurveyError, 'IMAGE_REFERENCE_BOUND'):
            collect_resources(fixture(), ORIGINAL, replace(Limits(), image_references=0))

    def test_external_script_and_ies_nodes_are_refused_with_inventory(self):
        bpy = fixture(); bpy.data.materials[0].node_tree.nodes.extend([node('ShaderNodeScript'), node('ShaderNodeTexIES')])
        private, public = collect_resources(bpy, ORIGINAL)
        self.assertEqual(len(private['node_trees'][0]['nodes']), 3)
        self.assertEqual(sum(r['code'] == 'UNSUPPORTED_EXTERNAL_NODE' for r in private['issues']), 2)
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')

    def test_string_utf8_nul_per_item_total_and_final_metadata_caps(self):
        for value in ['a\0b', '\ud800', 'x' * 4097]:
            with self.assertRaises(SurveyError): collect_resources(fixture([image(value)]), ORIGINAL)
        with self.assertRaisesRegex(SurveyError, 'TOTAL_TEXT_BOUND'):
            collect_resources(fixture(), ORIGINAL, replace(Limits(), string_bytes_total=30))
        with self.assertRaisesRegex(SurveyError, 'FINAL_METADATA_BOUND'):
            collect_resources(fixture(), ORIGINAL, replace(Limits(), metadata_bytes=1))

    def test_no_budget_widening_and_bool_is_not_int(self):
        for limits in [replace(Limits(), images=129), replace(Limits(), nodes=True), replace(Limits(), materials=-1)]:
            with self.assertRaisesRegex(SurveyError, 'LIMIT_DOMAIN'): collect_resources(fixture(), ORIGINAL, limits)
        im = image(users=True)
        with self.assertRaisesRegex(SurveyError, 'INTEGER_BOUND'): collect_resources(fixture([im]), ORIGINAL)
        im = image(has_data=1)
        with self.assertRaisesRegex(SurveyError, 'BOOLEAN_TYPE'): collect_resources(fixture([im]), ORIGINAL)

    def test_collection_and_path_enumeration_bounds(self):
        with self.assertRaisesRegex(SurveyError, 'COLLECTION_BOUND'):
            collect_resources(fixture(), ORIGINAL, replace(Limits(), images=0))
        with self.assertRaisesRegex(SurveyError, 'EXTERNAL_PATH_COUNT'):
            collect_resources(fixture(), ORIGINAL, replace(Limits(), external_paths=0))

    def test_duplicate_identity_and_visible_mesh_profile(self):
        im = image()
        with self.assertRaisesRegex(SurveyError, 'DUPLICATE_IMAGE_IDENTITY'): collect_resources(fixture([im, im]), ORIGINAL)
        bpy = fixture(); bpy.context.scene.objects[0].name = 'unexpected'
        private, public = collect_resources(bpy, ORIGINAL)
        self.assertIn('VISIBLE_MESH_PROFILE_REFUSED', {r['code'] for r in private['issues']})
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')

    def test_path_classification_is_lexical_not_search_or_exists(self):
        self.assertEqual(path_metadata('', ORIGINAL)['kind'], 'EMPTY')
        self.assertEqual(path_metadata(r'C:\outside\missing.png', ORIGINAL)['kind'], 'WINDOWS_ABSOLUTE')
        self.assertEqual(path_metadata('//../sibling/image.png', ORIGINAL)['original_base_candidate'], r'C:\protected\sibling\image.png')
        self.assertEqual(path_metadata('relative.png', ORIGINAL)['kind'], 'UNQUALIFIED_RELATIVE_OR_URI')
        self.assertEqual(path_metadata(r'\\server\share\file', ORIGINAL)['kind'], 'UNSUPPORTED_NETWORK_PATH')

    def test_hash_only_export_provenance_never_guesses_branch(self):
        metadata = references(); metadata['original_export_invocation'] = {'branch': 'bone_collector'}
        result = provenance.classify_public_reference(metadata)
        self.assertEqual(result['export_branch'], 'UNKNOWN')
        self.assertTrue(result['unqualified_explicit_branch_label_present'])
        self.assertFalse(result['plain_branch_assumed'] or result['bone_collector_branch_assumed'])
        self.assertFalse(result['parameters_body_decoded'])

    def test_hash_only_public_reference_rejects_changed_identity_types(self):
        for field, value in [('sha256', '0' * 64), ('bytes', True), ('bytes', 1), ('bytes', float(provenance.SIZES['blend']))]:
            metadata = references(); metadata['files']['blend'][field] = value
            with self.assertRaises(ValueError): provenance.classify_public_reference(metadata)
        for metadata in [None, {'format': 'other'}, {'format': references()['format'], 'files': []}]:
            with self.assertRaises(ValueError): provenance.classify_public_reference(metadata)

    def test_loaded_helper_repeated_snapshot_allows_unknown_export_branch(self):
        bpy = fixture(); private, public, result = loaded_survey.inspect_loaded_owned_scene(bpy, ORIGINAL, OWNED, references())
        self.assertEqual(public['status'], 'METADATA_SURVEY_ONLY')
        self.assertEqual(public['export_branch'], 'UNKNOWN')
        self.assertTrue(public['resource_observation_repeated_exactly'])
        self.assertFalse(public['export_invoked'] or public['blend_saved'])
        self.assertEqual(len(bpy.calls), 4)

    def test_loaded_helper_detects_resource_change_without_normalizing(self):
        bpy = fixture(); old = bpy.utils.blend_paths
        def changed(**kwargs):
            result = old(**kwargs)
            if len(bpy.calls) == 2: bpy.data.images[0].name = 'CHANGED'
            return result
        bpy.utils.blend_paths = changed
        with self.assertRaisesRegex(SurveyError, 'RESOURCE_OBSERVATION_CHANGED'):
            loaded_survey.inspect_loaded_owned_scene(bpy, ORIGINAL, OWNED, references())

    def test_loaded_helper_refuses_context_and_monitored_handler_mismatches(self):
        for owner, key, value, code in [('app', 'background', False, 'BACKGROUND'), ('app', 'online_access', True, 'OFFLINE'),
                                        ('app', 'autoexec_fail', True, 'AUTOEXEC'), ('data', 'filepath', ORIGINAL, 'OWNED_BLEND')]:
            bpy = fixture(); setattr(getattr(bpy, owner), key, value)
            with self.assertRaisesRegex(SurveyError, code): loaded_survey.inspect_loaded_owned_scene(bpy, ORIGINAL, OWNED, references())
        bpy = fixture(); bpy.app.handlers.load_post.append('not callable or executed')
        with self.assertRaisesRegex(SurveyError, 'UNEXPECTED_HANDLER'): loaded_survey.inspect_loaded_owned_scene(bpy, ORIGINAL, OWNED, references())

    def test_probe_and_stager_always_refuse_before_any_native_operation(self):
        for entry in [probe_resources.main, stager.main]:
            with self.assertRaisesRegex(Unstageable, 'SOURCE_ONLY'): entry()
        for filename in ('probe_resources.py', 'stager.py', 'survey_admission.py'):
            source = (HERE / filename).read_text(encoding='utf-8')
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    self.assertFalse(any(n.name in ('bpy', 'subprocess', 'os', 'pathlib') for n in node.names))

    def test_exact_original_core_support_and_hidden_sentinel_sources(self):
        for filename, digest in [('setter_support.py', 'fda14a49be8fb57908524aad7869a851ea234036a7c30892ef3e01777ba73bb9'),
                                 ('placement_sentinel.py', 'e42fa44efa599851396c517fa0b4bc90a692efb1f911517fa3d748879d1462c2')]:
            self.assertEqual(hashlib.sha256((HERE / filename).read_bytes()).hexdigest(), digest)
        unit = ast.parse((HERE / 'setter_support.py').read_text(encoding='utf-8'))
        roles = next(n.value for n in unit.body if isinstance(n, ast.Assign) and any(isinstance(v, ast.Name) and v.id == 'ROLES' for v in n.targets))
        self.assertEqual(len(ast.literal_eval(roles)), 26)

    def test_exact_sentinel_fake_api_placement_finally_and_failure_guards(self):
        prerequisite = HERE.parent / 'normal_setter_boundary_sentinel_20261117' / 'test_sentinel.py'
        self.assertEqual(hashlib.sha256(prerequisite.read_bytes()).hexdigest(), 'c070508aea3face5986b491f25bd06ba5b7bd0627853bedbdda34c01d98d6ae2')
        spec = importlib.util.spec_from_file_location('survey_approved_sentinel_fake_api', prerequisite)
        fakes = importlib.util.module_from_spec(spec); spec.loader.exec_module(fakes)
        method = next(n for n in ast.parse((HERE / 'placement_sentinel.py').read_text(encoding='utf-8')).body
                      if isinstance(n, ast.FunctionDef) and n.name == '_hidden_placement_sentinel')
        namespace = {'C': None, 'W': W, 'sys': NS(platform='win32'), 'contextmanager': contextlib.contextmanager}
        for fault in [None, 'bad_pid', 'bad_tid', 'bad_rect', 'bad_style', 'bad_exstyle', 'fail_create', 'fail_destroy']:
            api = fakes.FakeAPI(); namespace['C'] = fakes.FakeC(api)
            if fault: setattr(api, fault, True)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), '<fake-only-survey-sentinel>', 'exec'), namespace)
            if fault:
                with self.assertRaises((RuntimeError, OSError)):
                    with namespace['_hidden_placement_sentinel'](): pass
            else:
                with namespace['_hidden_placement_sentinel']() as policy:
                    self.assertTrue(api.active)
                    self.assertFalse(policy['visible_at_creation'])
                self.assertTrue(policy['destroyed_in_finally'])
                self.assertEqual(api.destroy_calls, 1)
            self.assertTrue(all(name not in {'ShowWindow', 'SetForegroundWindow', 'SwitchDesktop', 'SetThreadDesktop'} for name, _ in api.calls))


if __name__ == '__main__': unittest.main(verbosity=2)
