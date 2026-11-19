"""CPU-only synthetic metadata; fixture source exercises exact old collectors."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import ast
import copy
import hashlib
import unittest

import classification as C
import survey_core as S
from ownership_metadata import collect_ownership_metadata


class RNA:
    serial = 100

    def __init__(self, kind, **values):
        RNA.serial += 1
        self.identity = RNA.serial
        self.bl_rna = NS(identifier=kind)
        self.name = self.name_full = 'SYNTHETIC'
        self.library = self.library_weak_reference = None
        self.__dict__.update(values)

    def as_pointer(self):
        return self.identity

    def path_from_module(self, property=''):
        if not property and self.__dict__.get('general_path_unobserved'):
            raise ValueError('private diagnostic must not escape')
        return 'bpy.data.synthetic[0]' + ('.' + property if property else '')


def fixture():
    def image(source, kind, raw=''):
        return RNA('Image', source=source, type=kind, filepath=raw, filepath_raw=raw,
                   alpha_mode='STRAIGHT', colorspace_settings=NS(name='sRGB'),
                   is_dirty=False, has_data=False, use_multiview=False,
                   is_multiview=False, is_stereo_3d=False, users=1,
                   packed_file=None, packed_files=[])
    images = [image('VIEWER', 'RENDER_RESULT'), image('VIEWER', 'COMPOSITING')]
    material = RNA('Material', use_nodes=False, node_tree=None, general_path_unobserved=True)
    raw = '//synthetic/no_filename_role.blend'
    material.library_weak_reference = RNA('LibraryWeakReference', filepath=raw, id_name='MASYNTHETIC')
    screen = RNA('Screen', areas=[NS(spaces=[RNA('SpaceImageEditor', type='IMAGE_EDITOR', image=im)
                                          for im in images])])
    meshes = [RNA('Object', name=name, type='MESH', hide_render=False, hide_get=lambda: False)
              for name in ('Hat.smd', 'hair.smd')]
    ids = [*images, material, screen, *meshes]
    bpy = NS(data=NS(images=images, materials=[material], libraries=[], screens=[screen]),
             context=NS(scene=NS(objects=meshes)), utils=NS(blend_paths=lambda **kw: [raw]))
    users = {owner: set() for owner in ids}
    bpy.data.user_map = lambda: users
    bpy.data.file_path_foreach = lambda fn, **kw: fn(material, raw, None)
    r, public = S.collect_resources(bpy, 'C:/synthetic/original.blend')
    o, _ = collect_ownership_metadata(bpy, r, public)
    return r, public, o


def bind(r, public, o):
    raw = S.canonical(r)
    public['private_metadata_sha256'] = hashlib.sha256(raw).hexdigest()
    public['private_metadata_bytes'] = len(raw)
    public['profile_issues'] = len(r['issues'])
    public['status'] = 'RESOURCE_PROFILE_REFUSED' if r['issues'] else 'METADATA_SURVEY_ONLY'
    o['source_resource_private_sha256'] = public['private_metadata_sha256']
    o['original_issues'] = copy.deepcopy(r['issues'])


def path_rows(result):
    return [row for row in result['rows'] if row['kind'] == 'external_path']


def image_rows(result):
    return [row for row in result['rows'] if row['kind'] == 'image']


class ClassificationTests(unittest.TestCase):
    def test_exact_parent_bytes_and_six_original_refusals_retained(self):
        here = Path(__file__).resolve().parent
        self.assertEqual(hashlib.sha256((here/'survey_core.py').read_bytes()).hexdigest(),
                         '39a417bfe8e024704f4d400f824293640370074c28446e40613aa401247a4e28')
        self.assertEqual(hashlib.sha256((here/'ownership_metadata.py').read_bytes()).hexdigest(),
                         '94feb0279628b1426b2c48cf37dc5526a73901ded9715ecf51fe46064c440e9d')
        values = fixture(); before = [C.canonical(value) for value in values]
        private, public = C.classify(*values)
        self.assertEqual(before, [C.canonical(value) for value in values])
        self.assertEqual(len(values[0]['issues']), 6)
        self.assertEqual(private['original_issues'], values[0]['issues'])
        self.assertEqual(public['status'], 'RESOURCE_PROFILE_REFUSED')
        self.assertEqual(public['original_issue_rows_retained'], 6)
        self.assertFalse(public['resource_profile_decision_changed'])
        self.assertFalse(public['resources_excluded_or_accepted'])
        self.assertNotIn('SYNTHETIC', C.canonical(public).decode())

    def test_observed_weak_property_local_material_general_path_unknown(self):
        values = fixture(); result, public = C.classify(*values)
        self.assertEqual([row['classification'] for row in path_rows(result)], [C.PROVENANCE]*2)
        owner = next(owner for owner in values[2]['owners'] if owner['rna_type'] == 'Material')
        self.assertEqual(owner['data_path']['status'], 'UNOBSERVED')
        self.assertEqual(public['counts'][C.PROVENANCE], 2)

    def test_both_typed_internal_viewers_need_explicit_editor_witness(self):
        values = fixture(); result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in image_rows(result)], [C.VIEWER]*2)
        for row in image_rows(result):
            self.assertEqual(row['unobserved_scopes'], C.UNKNOWN_VIEWER_SCOPES)
        o = values[2]
        o['image_editor_references'].clear()
        for viewer in o['viewer_reachability']:
            viewer['image_editor_references'].clear()
        result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in image_rows(result)], [C.UNRESOLVED]*2)

    def test_typed_UI_witness_survives_unobserved_optional_human_readable_path(self):
        values = fixture(); o = values[2]
        for row in o['image_editor_references']:
            row['property_data_path'] = {'status': 'UNOBSERVED', 'value': None}
        for viewer in o['viewer_reachability']:
            viewer['image_editor_references'] = [copy.deepcopy(row) for row in o['image_editor_references']
                                                 if row['image'] == viewer['image']]
        result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in image_rows(result)], [C.VIEWER]*2)
        for row in image_rows(result):
            self.assertEqual(row['IMAGE_EDITOR_property_path_statuses'], ['UNOBSERVED'])
            self.assertEqual(row['unobserved_scopes'], C.UNKNOWN_VIEWER_SCOPES)

    def test_unknown_property_linked_owner_or_descriptor_type_is_unresolved(self):
        for variation in ('path', 'suffix', 'linked', 'type', 'target'):
            values = fixture(); o = values[2]; weak = o['ID_library_weak_references'][0]
            if variation == 'path': weak['property_data_path'] = {'status': 'UNOBSERVED', 'value': None}
            if variation == 'suffix': weak['property_data_path']['value'] = 'bpy.data.synthetic[0].filepath'
            if variation == 'linked':
                next(owner for owner in o['owners'] if owner['rna_type'] == 'Material')['linked_library_present'] = True
            if variation == 'type': weak['rna_type'] = 'SomethingElse'
            if variation == 'target': weak['id_name'] = ''
            result, _ = C.classify(*values)
            self.assertEqual([row['classification'] for row in path_rows(result)], [C.UNRESOLVED]*2)

    def test_multiple_owners_descriptors_or_observations_remain_unresolved(self):
        for variation in ('owner', 'descriptor', 'other_descriptor', 'observation'):
            values = fixture(); o = values[2]
            if variation == 'owner':
                duplicate = copy.deepcopy(o['owners'][-1]); duplicate['session_identity'] = 8000
                o['owners'].append(duplicate)
                o['weak_enabled_path_observations'].append({'owner': 8000, 'raw': o['ID_library_weak_references'][0]['filepath']})
                for join in o['external_reference_owner_joins']:
                    join['exact_raw_owner_ids'] = sorted(join['exact_raw_owner_ids'] + [8000])
            if variation == 'descriptor':
                o['ID_library_weak_references'].append(copy.deepcopy(o['ID_library_weak_references'][0]))
                for join in o['external_reference_owner_joins']:
                    join['exact_owner_and_library_weak_reference_rows'] = [0, 1]
            if variation == 'other_descriptor':
                duplicate = copy.deepcopy(o['ID_library_weak_references'][0])
                duplicate['filepath'] = '//synthetic/other.blend'
                o['ID_library_weak_references'].append(duplicate)
            if variation == 'observation':
                o['weak_enabled_path_observations'].append(copy.deepcopy(o['weak_enabled_path_observations'][0]))
            result, _ = C.classify(*values)
            self.assertEqual([row['classification'] for row in path_rows(result)], [C.UNRESOLVED]*2)

    def test_exact_typed_unpacked_library_path_is_required_not_provenance(self):
        values = fixture(); o = values[2]
        owner = next(owner for owner in o['owners'] if owner['rna_type'] == 'Material')
        owner['rna_type'] = 'Library'
        o['ID_library_weak_references'].clear()
        for join in o['external_reference_owner_joins']:
            join['exact_owner_and_library_weak_reference_rows'] = []
            join['nested_reference_property_status'] = 'UNOBSERVED'
        result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in path_rows(result)], [C.REQUIRED]*2)
        values[0]['external_path_references']['unpacked'].clear()
        o['external_reference_owner_joins'].pop()
        bind(*values)
        result, _ = C.classify(*values)
        self.assertEqual(path_rows(result)[0]['classification'], C.UNRESOLVED)

    def test_unpacked_FILE_image_is_required_and_alias_or_packed_is_unresolved(self):
        for variation in ('file', 'alias', 'packed'):
            values = fixture(); r, public, o = values
            image = r['images'][0]; key = image['session_identity']; raw = '//synthetic/texture.png'
            image.update(source='FILE', type='IMAGE', filepath=raw, filepath_raw=raw)
            if variation == 'alias': image['filepath_raw'] = '//synthetic/./texture.png'
            if variation == 'packed': image['packed'] = [{'part': 0, 'bytes': 3}]
            o['viewer_reachability'].pop(0)
            o['image_editor_references'] = [row for row in o['image_editor_references'] if row['image'] != 0]
            for label in ('all', 'unpacked'):
                r['external_path_references'][label] = [{'raw': raw}]
            o['weak_enabled_path_observations'] = [{'owner': key, 'raw': raw}]
            o['ID_library_weak_references'].clear()
            for join in o['external_reference_owner_joins']:
                join.update(exact_raw_owner_ids=[key], exact_owner_and_library_weak_reference_rows=[],
                            nested_reference_property_status='UNOBSERVED')
            bind(*values)
            result, _ = C.classify(*values)
            expected = C.REQUIRED if variation == 'file' else C.UNRESOLVED
            self.assertEqual(image_rows(result)[0]['classification'], expected)
            self.assertEqual([row['classification'] for row in path_rows(result)], [expected]*2)

    def test_alias_paths_and_weak_owner_mismatch_do_not_join(self):
        for replacement in ('//synthetic/./no_filename_role.blend', '//SYNTHETIC/no_filename_role.blend',
                            'C:/synthetic/no_filename_role.blend'):
            values = fixture(); o = values[2]
            o['ID_library_weak_references'][0]['filepath'] = replacement
            for join in o['external_reference_owner_joins']:
                join['exact_owner_and_library_weak_reference_rows'] = []
                join['nested_reference_property_status'] = 'UNOBSERVED'
            result, _ = C.classify(*values)
            self.assertEqual([row['classification'] for row in path_rows(result)], [C.UNRESOLVED]*2)
        values = fixture(); o = values[2]
        o['ID_library_weak_references'][0]['owner'] = values[0]['images'][0]['session_identity']
        for join in o['external_reference_owner_joins']:
            join['exact_owner_and_library_weak_reference_rows'] = []
            join['nested_reference_property_status'] = 'UNOBSERVED'
        result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in path_rows(result)], [C.UNRESOLVED]*2)

    def test_shared_FILE_path_cannot_be_misclassified_as_weak_provenance(self):
        values = fixture(); r, public, o = values
        raw = o['ID_library_weak_references'][0]['filepath']
        image = r['images'][0]
        image.update(source='FILE', type='IMAGE', filepath=raw, filepath_raw=raw)
        o['viewer_reachability'].pop(0)
        o['image_editor_references'] = [row for row in o['image_editor_references'] if row['image'] != 0]
        bind(*values)
        result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in path_rows(result)], [C.UNRESOLVED]*2)

    def test_name_does_not_determine_role(self):
        values = fixture()
        for owner in values[2]['owners']:
            owner['name_full'] = 'essentials_brushes-gp_draw.blend'
        result, _ = C.classify(*values)
        self.assertEqual([row['classification'] for row in path_rows(result)], [C.PROVENANCE]*2)
        self.assertFalse(result['filename_role_inference_used'])

    def test_viewer_material_other_ID_or_file_evidence_cannot_be_ignored(self):
        for variation in ('direct', 'material', 'other', 'node', 'path', 'type', 'linked'):
            values = fixture(); r, public, o = values; viewer = o['viewer_reachability'][0]
            mat = next(owner['session_identity'] for owner in o['owners'] if owner['rna_type'] == 'Material')
            screen = next(owner['session_identity'] for owner in o['owners'] if owner['rna_type'] == 'Screen')
            if variation == 'direct': viewer['direct_id_users'] = [screen]
            if variation == 'material': viewer['reachable_material_ids'] = [mat]
            if variation == 'other': viewer['reachable_other_id_owners'] = [screen]
            if variation == 'node':
                ref = {'tree': 0, 'node': 0, 'image': 0}
                r['material_image_references'].append(ref); viewer['original_material_node_references'] = [ref]
            if variation == 'path': r['images'][0]['filepath'] = '//viewer.png'
            if variation == 'type':
                r['images'][0]['type'] = viewer['type'] = 'IMAGE'
            if variation == 'linked':
                next(owner for owner in o['owners'] if owner['session_identity'] == r['images'][0]['session_identity'])['linked_library_present'] = True
            bind(*values)
            result, _ = C.classify(*values)
            self.assertEqual(image_rows(result)[0]['classification'], C.UNRESOLVED)

    def test_stale_hash_image_ID_owner_join_and_UI_fail_closed(self):
        for variation in ('hash', 'image', 'owner', 'join', 'ui', 'viewer', 'duplicate'):
            values = fixture(); r, public, o = values
            if variation == 'hash': public['private_metadata_sha256'] = '0'*64
            if variation == 'image': r['images'][0]['session_identity'] = 9000; bind(*values)
            if variation == 'owner': o['weak_enabled_path_observations'][0]['owner'] = 9000
            if variation == 'join': o['external_reference_owner_joins'][0]['exact_raw_owner_ids'] = []
            if variation == 'ui': o['image_editor_references'][0]['image'] = 99
            if variation == 'viewer': o['viewer_reachability'][0]['direct_id_users'] = [9000]
            if variation == 'duplicate': o['owners'].append(copy.deepcopy(o['owners'][0]))
            before = [C.canonical(value) for value in values]
            with self.assertRaises(C.ClassificationError): C.classify(*values)
            self.assertEqual(before, [C.canonical(value) for value in values])

    def test_malformed_schema_bool_ID_and_unknown_scope_do_not_partially_classify(self):
        for variation in ('field', 'bool', 'scope', 'property', 'type', 'integer'):
            values = fixture(); o = values[2]
            if variation == 'field': del o['viewer_reachability']
            if variation == 'bool': o['owners'][0]['session_identity'] = True
            if variation == 'scope': o['viewer_reachability'][0]['unobserved_owner_scopes'] = []
            if variation == 'property': o['ID_library_weak_references'][0]['property_data_path'] = {'status': 'OBSERVED', 'value': None}
            if variation == 'type': o['weak_enabled_path_observations'] = {}
            if variation == 'integer': o['image_editor_references'][0]['area'] = -1
            with self.assertRaises(C.ClassificationError): C.classify(*values)

    def test_input_output_structure_text_collection_and_limit_caps(self):
        for field in ('input_bytes_each', 'output_bytes', 'nodes', 'text_bytes', 'text_bytes_each', 'depth', 'rows'):
            with self.assertRaises(C.ClassificationError): C.classify(*fixture(), replace(C.Limits(), **{field: 1}))
            with self.assertRaises(C.ClassificationError):
                C.classify(*fixture(), replace(C.Limits(), **{field: getattr(C.HARD, field)+1}))
        values = fixture(); values[2]['extra'] = values[2]
        with self.assertRaises(C.ClassificationError): C.classify(*values)
        values = fixture(); values[2]['extra'] = float('nan')
        with self.assertRaises(C.ClassificationError): C.classify(*values)

    def test_pure_no_IO_native_process_or_path_normalization(self):
        values = fixture()
        with (patch('builtins.open', side_effect=AssertionError('open')),
              patch.object(Path, 'stat', side_effect=AssertionError('stat'))):
            result, public = C.classify(*values)
        source = ast.parse(Path(C.__file__).read_bytes())
        self.assertEqual({alias.name for node in source.body if isinstance(node, ast.Import)
                          for alias in node.names}, {'hashlib', 'json'})
        forbidden = {'open', 'stat', 'resolve', 'normpath', 'normcase', 'load', 'save', 'write', 'read', 'run', 'Popen'}
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                             and node.func.attr in forbidden for node in ast.walk(source)))
        self.assertFalse(result['full_graph_or_global_unreachability_proven'])
        self.assertFalse(public['strict31_normal_fidelity_export_repair_carrier_or_adoption_qualified'])


if __name__ == '__main__':
    unittest.main()
