"""Fabricated metadata/RNA/lease contracts only; no native assets or processes."""
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import inspection_worker as worker


def metadata(names=('nativeA', 'nativeB', 'nativeC', 'nativeD')):
    return dict(format='has_private_mdl49_material_skin_metadata_candidate_1',
                metadata=dict(materials=[dict(index=index, name=name) for index, name in enumerate(names)]))


class Node:
    def __init__(self, tree, kind):
        self.id_data, self.bl_idname = tree, kind
    @property
    def image(self): raise AssertionError('diagnostic must not touch images')
    @property
    def inputs(self): raise AssertionError('diagnostic must not traverse sockets')


class ShaderNodeTree:
    def __init__(self, kinds):
        self.original, self.library, self.is_embedded_data = self, None, True
        self.nodes = [Node(self, kind) for kind in kinds]


class Material:
    def __init__(self, kinds=('ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled')):
        self.original, self.library = self, None
        self.node_tree = ShaderNodeTree(kinds)
    @property
    def name(self): raise AssertionError('diagnostic must not publish material names')


def bpy_fixture(materials):
    return NS(data=NS(materials=materials), types=NS(Material=Material, ShaderNodeTree=ShaderNodeTree, Node=Node))


class HelperRefusal(ValueError):
    def __init__(self, code, summary=None):
        super().__init__(code)
        self.summary = summary


def flow_fixture(available=None):
    available = tuple(available or ('unused', 'nativeD', 'nativeB', 'nativeA', 'nativeC', 'unrequested'))
    original = Material()
    bpy = bpy_fixture([original])
    events = []
    buffers = {'native_' + key: ('synthetic_' + key).encode() for key in worker.NATIVE}
    def derive(refs):
        events.append('metadata')
        for key, (_name, count, digest) in worker.NATIVE.items():
            assert refs[key] == dict(raw=buffers['native_' + key], bytes=count, sha256=digest)
        return metadata()
    summary = dict(format='has_empty_library_enumeration_summary_2', source_materials=len(available),
                   all_destination_requests_empty=True, actual_id_census_unchanged=True)
    def enumerate_(actual_bpy, path, summary_sink):
        assert actual_bpy is bpy
        events.append('enumeration')
        summary_sink(summary)
        return dict(material_names=available, summary=summary)
    def inspect(actual_bpy, path, names, enumeration):
        assert actual_bpy is bpy and names == ('nativeA', 'nativeB', 'nativeC', 'nativeD')
        events.append('inspection')
        bpy.data.materials.extend(Material() for _ in names)
        return dict(summary=dict(format='has_material_only_library_inspection_summary_2', status='synthetic'),
                    materials=tuple(bpy.data.materials[1:]))
    return bpy, buffers, NS(enumerate_library=enumerate_), NS(Refusal=HelperRefusal, inspect_material_library=inspect), NS(derive_material_metadata=derive), events


class MaterialInspectionWorker(unittest.TestCase):
    def test_exact_native_subset_keeps_native_order_with_extra_catalogue(self):
        names, summary = worker.select_native_subset(metadata(), ('unused', 'nativeD', 'nativeB', 'nativeA', 'nativeC'))
        self.assertEqual(names, ('nativeA', 'nativeB', 'nativeC', 'nativeD'))
        self.assertEqual(summary['unrequested_catalogue_materials'], 1)
        self.assertEqual(summary['requested_names_sha256'], worker.digest(names))
        self.assertIs(summary['native_geometry_decoded'], False)

    def test_casefold_or_suffix_or_first_four_cannot_select(self):
        for names in (('nativea', 'nativeB', 'nativeC', 'nativeD'),
                      ('nativeA.001', 'nativeB', 'nativeC', 'nativeD'),
                      ('unused1', 'unused2', 'unused3', 'unused4')):
            with self.assertRaisesRegex(worker.Refusal, 'EXACT_NATIVE_NAME_SUBSET_NOT_AVAILABLE'):
                worker.select_native_subset(metadata(), names)

    def test_duplicate_native_names_or_nonfour_or_bool_index_refused(self):
        for candidate in (metadata(('nativeA', 'nativeA', 'nativeC', 'nativeD')),
                          metadata(('nativeA', 'nativeB', 'nativeC')), metadata()):
            if candidate == metadata(): candidate['metadata']['materials'][0]['index'] = False
            with self.assertRaises(worker.Refusal):
                worker.select_native_subset(candidate, ('nativeA', 'nativeB', 'nativeC', 'nativeD'))

    def test_native_material_table_order_cannot_be_relabelled(self):
        candidate = metadata()
        candidate['metadata']['materials'].reverse()
        with self.assertRaises(worker.Refusal):
            worker.select_native_subset(candidate, ('nativeA', 'nativeB', 'nativeC', 'nativeD'))

    def test_duplicate_or_unbounded_or_list_catalogue_refused(self):
        for available in (('nativeA', 'nativeB', 'nativeC', 'nativeD', 'nativeA'), (),
                          tuple(str(index) for index in range(257)), ['nativeA', 'nativeB', 'nativeC', 'nativeD']):
            with self.assertRaises(worker.Refusal): worker.select_native_subset(metadata(), available)

    def test_upper_bounded_catalogue_allows_native_subset(self):
        available = ('nativeA', 'nativeB', 'nativeC', 'nativeD') + tuple('unused' + str(i) for i in range(252))
        self.assertEqual(worker.select_native_subset(metadata(), available)[1]['available_materials'], 256)

    def test_flow_metadata_then_empty_enumeration_then_exact_append(self):
        bpy, buffers, enumeration, inspection, reader, events = flow_fixture()
        result = {}
        worker.inspect_once(bpy, Path('owned.blend'), buffers, enumeration, inspection, reader, result)
        self.assertEqual(events, ['metadata', 'enumeration', 'inspection'])
        self.assertTrue(result['material_inspection_executed'])
        self.assertTrue(result['complete_actual_ID_census_observed'])
        self.assertEqual(result['node_type_diagnostic']['node_type_counts'],
                         {'ShaderNodeBsdfPrincipled': 4, 'ShaderNodeOutputMaterial': 4})
        self.assertNotIn('materials', result)

    def test_missing_exact_name_never_requests_append_but_retains_enumeration(self):
        bpy, buffers, enumeration, inspection, reader, events = flow_fixture(('nativeA', 'nativeB', 'nativeC', 'other'))
        result = {}
        with self.assertRaises(worker.Refusal):
            worker.inspect_once(bpy, Path('owned.blend'), buffers, enumeration, inspection, reader, result)
        self.assertEqual(events, ['metadata', 'enumeration'])
        self.assertEqual(result['enumeration_summary']['source_materials'], 4)
        self.assertNotIn('material_inspection_attempted', result)

    def test_refusal_retains_header_reason_counts_and_node_types(self):
        bpy, buffers, enumeration, inspection, reader, events = flow_fixture()
        def refuse(*args):
            bpy.data.materials.extend(Material(('ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled', 'ShaderNodeGroup')) for _ in range(4))
            raise HelperRefusal('PNG_IHDR_CRC', dict(status='REFUSED', refusal_code='PNG_IHDR_CRC', packed_bytes_copied=80))
        inspection.inspect_material_library = refuse
        result = {}
        with self.assertRaisesRegex(HelperRefusal, 'PNG_IHDR_CRC'):
            worker.inspect_once(bpy, Path('owned.blend'), buffers, enumeration, inspection, reader, result)
        self.assertEqual(result['inspection_summary']['refusal_code'], 'PNG_IHDR_CRC')
        self.assertEqual(result['node_type_diagnostic']['node_type_counts']['ShaderNodeGroup'], 4)
        self.assertNotIn('material_inspection_executed', result)

    def test_diagnostic_failure_does_not_replace_primary_helper_refusal(self):
        bpy, buffers, enumeration, inspection, reader, events = flow_fixture()
        def refuse(*args):
            bpy.data.materials.extend(Material() for _ in range(5))
            raise HelperRefusal('PRIMARY_FIXED_CODE', {})
        inspection.inspect_material_library = refuse
        result = {}
        with self.assertRaisesRegex(HelperRefusal, 'PRIMARY_FIXED_CODE'):
            worker.inspect_once(bpy, Path('owned.blend'), buffers, enumeration, inspection, reader, result)
        self.assertEqual(result['node_type_diagnostic'], dict(status='REFUSED_BOUNDED_TYPE_DIAGNOSTIC'))

    def test_diagnostic_skips_originals_and_never_reads_image_or_name(self):
        original, new = Material(), Material(('ShaderNodeTexImage',))
        result = worker.node_type_diagnostic(bpy_fixture([original, new]), (original,))
        self.assertEqual(result['materials'], 1)
        self.assertEqual(result['node_type_counts'], {'ShaderNodeTexImage': 1})

    def test_diagnostic_wrong_owner_or_linked_material_refused(self):
        for wrong in ('owner', 'library', 'original'):
            material = Material()
            if wrong == 'owner': material.node_tree.nodes[0].id_data = ShaderNodeTree(())
            if wrong == 'library': material.library = object()
            if wrong == 'original': material.original = object()
            with self.assertRaises(worker.Refusal): worker.node_type_diagnostic(bpy_fixture([material]), ())

    def test_diagnostic_node_type_budgets_and_no_names(self):
        for kinds in (tuple('ShaderNodeGroup' for _ in range(129)), ('private material name',), ('A' * 129,)):
            with self.assertRaises(worker.Refusal): worker.node_type_diagnostic(bpy_fixture([Material(kinds)]), ())

    def test_module_import_is_from_supplied_verified_bytes_without_loader_read(self):
        name = '_has_inspection_test_only_module'
        try:
            module = worker.load_verified_module(Path('nonexistent.py'), b'VALUE = 17\n', name)
            self.assertEqual(module.VALUE, 17)
            with self.assertRaisesRegex(worker.Refusal, 'PRIVATE_MODULE_COLLISION'):
                worker.load_verified_module(Path('nonexistent.py'), b'VALUE=18', name)
        finally:
            sys.modules.pop(name, None)

    def test_failed_module_import_clears_only_its_private_registration(self):
        name = '_has_inspection_test_failure_module'
        with self.assertRaises(RuntimeError):
            worker.load_verified_module(Path('none.py'), b'raise RuntimeError("synthetic")\n', name)
        self.assertNotIn(name, sys.modules)

    def test_literal_module_and_native_pins_cover_thirteen_roles(self):
        literals = worker.literal_inputs(Path('owned-stage'))
        self.assertEqual(set(literals) | {'probe', 'full_completion', 'graphics_release'}, worker.ROLES)
        self.assertEqual(len(worker.ROLES), 13)
        self.assertEqual(literals['inspection_module'][1][1], '5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17')
        self.assertEqual(literals['native_mdl'][0], Path('owned-stage/inputs/native/junko hair.mdl'))

    def test_strict_json_rejects_duplicate_or_nonfinite(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
            with self.assertRaises(worker.Refusal): worker.strict_json(raw)

    def test_all_unsupported_flags_default_false(self):
        self.assertEqual(len(worker.FALSE_FLAGS), 16)
        self.assertNotIn('material_append_requested', worker.FALSE_FLAGS)
        self.assertIn('non_normal_semantic_equivalence_qualified', worker.FALSE_FLAGS)


class RequestLease(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name)
        self.stage = self.project/'output/owned'
        self.stage.mkdir(parents=True)
        for name in ('result', 'temp'): (self.stage/name).mkdir()
        now = datetime.datetime.now(datetime.timezone.utc)
        self.lease = dict(format='has_owned_B_material_inspection_request_2',
            phase='ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED', private_arrays_public=False,
            created_utc=(now-datetime.timedelta(seconds=1)).isoformat(), expires_utc=(now+datetime.timedelta(minutes=10)).isoformat(),
            owned_stage=str(self.stage), owned_output=str(self.stage/'result'), owned_temp=str(self.stage/'temp'),
            files={role:{} for role in worker.ROLES},
            source_context=dict(full_suite_passed=True, full_job_physically_closed=True, exclusive_runtime_lease=True,
                                observed_owned_processes=0, functional_file_count=1061, tested_revision=worker.REVISION))
        self.path = self.stage/'request.json'
        self.support = NS(safe=lambda value: Path(value).absolute(), pinned_read=self.read)

    def read(self, path, count, digest):
        raw = path.read_bytes()
        assert len(raw) == count and hashlib.sha256(raw).hexdigest() == digest
        return raw, ('synthetic-stamp',)

    def request(self):
        raw = json.dumps(self.lease).encode()
        self.path.write_bytes(raw)
        with patch.object(worker, 'PROJECT', self.project), patch.object(worker, 'HERE', self.project/'output/prep'), \
             patch.dict(os.environ, {'TEMP':str(self.stage/'temp'), 'TMP':str(self.stage/'temp')}), \
             patch.object(worker.tempfile, 'gettempdir', return_value=str(self.stage/'temp')):
            return worker._request(self.support, self.path, hashlib.sha256(raw).hexdigest())

    def test_valid_fourteen_identity_lease(self):
        lease, output, identity = self.request()
        self.assertEqual(output, self.stage/'result')
        self.assertEqual(len(lease['files']) + 1, 14)

    def test_each_missing_or_extra_role_refused(self):
        baseline = copy.deepcopy(self.lease['files'])
        for role in baseline:
            self.lease['files'] = {key:value for key,value in baseline.items() if key != role}
            with self.assertRaises(worker.Refusal): self.request()
        self.lease['files'] = dict(baseline, extra={})
        with self.assertRaises(worker.Refusal): self.request()

    def test_context_booleans_and_integer_counts_are_exact(self):
        for key in ('full_suite_passed', 'full_job_physically_closed', 'exclusive_runtime_lease'):
            self.lease['source_context'][key] = 1
            with self.assertRaises(worker.Refusal): self.request()
            self.lease['source_context'][key] = True
        for key, bad, good in (('observed_owned_processes', False, 0), ('functional_file_count', True, 1061),
                               ('tested_revision', 'other', worker.REVISION)):
            self.lease['source_context'][key] = bad
            with self.assertRaises(worker.Refusal): self.request()
            self.lease['source_context'][key] = good

    def test_expired_or_overlong_or_naive_lease_refused(self):
        created, expiry = self.lease['created_utc'], self.lease['expires_utc']
        self.lease['expires_utc'] = self.lease['created_utc']
        with self.assertRaises(worker.Refusal): self.request()
        self.lease['expires_utc'] = (datetime.datetime.fromisoformat(created)+datetime.timedelta(hours=1)).isoformat()
        with self.assertRaises(worker.Refusal): self.request()
        self.lease['expires_utc'] = expiry
        self.lease['created_utc'] = datetime.datetime.now().isoformat()
        with self.assertRaises(worker.Refusal): self.request()

    def test_wrong_scope_or_existing_public_output_refused(self):
        self.lease['private_arrays_public'] = True
        with self.assertRaises(worker.Refusal): self.request()
        self.lease['private_arrays_public'] = False
        (self.stage/'result/PUBLIC_MATERIAL_INSPECTION2.json').write_text('synthetic')
        with self.assertRaises(worker.Refusal): self.request()


if __name__ == '__main__':
    unittest.main()
