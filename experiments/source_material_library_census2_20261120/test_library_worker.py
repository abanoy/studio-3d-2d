"""Pure fake-RNA and synthetic-file contracts; no Blender/native asset imports."""
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

import library_worker as worker


class ID:
    def __init__(self, name, pointer, library=None):
        self.name = self.name_full = name
        self.pointer, self.library = pointer, library
        self.original = self
    def as_pointer(self):
        return self.pointer


class Image(ID):
    @property
    def size(self): raise AssertionError('image.size MUST NOT be read')
    @property
    def channels(self): raise AssertionError('image.channels MUST NOT be read')
    @property
    def pixels(self): raise AssertionError('image.pixels MUST NOT be read')


class LibraryView:
    def __init__(self, values): self.values = values
    def __dir__(self): return list(self.values)
    def __getattr__(self, key): return self.values[key]


class Context:
    def __init__(self, source, destination, enter=None, exit=None):
        self.source, self.destination, self.enter_action, self.exit_action = source, destination, enter, exit
        self.entered = self.exited = 0
    def __enter__(self):
        self.entered += 1
        if self.enter_action: self.enter_action()
        return self.source, self.destination
    def __exit__(self, *_args):
        self.exited += 1
        if self.exit_action: self.exit_action()
        return False


class Libraries(list):
    def load(self, path, *, link):
        if link is not False: raise AssertionError('only link=False is admitted')
        self.calls.append((path, link))
        return self.context


def fake_bpy():
    root = NS(types=NS(ID=ID))
    data = root.data = NS()
    data.objects = [ID('Factory Cube', 11), ID('Factory Camera', 12)]
    data.materials = [ID('Factory Material', 13)]
    data.images = [Image('Factory Render Result', 14)]
    data.libraries = Libraries()
    data.libraries.calls = []
    id_type = NS(identifier='ID', base=None)
    data.bl_rna = NS(properties=[NS(identifier='rna_type', type='POINTER')])
    for name in ('objects', 'materials', 'images', 'libraries'):
        data.bl_rna.properties.append(NS(identifier=name, type='COLLECTION', fixed_type=NS(identifier=name, base=id_type)))
    catalog = dict(objects=['private-B-object-name'], materials=['B Mat 2', 'B Mat 1', 'B Mat 4', 'B Mat 3'],
                   images=['private-B-image-name'], libraries=[], version=(5, 1, 0))
    destination = {key: [] for key in catalog if key != 'version'} | {'version': (5, 1, 0)}
    context = Context(LibraryView(catalog), LibraryView(destination))
    data.libraries.context = context
    return root, context


class EnumerationTests(unittest.TestCase):
    def test_additional_unused_catalogue_materials_do_not_create_requests(self):
        bpy, context = fake_bpy()
        context.source.values['materials'].extend(['Extra Unused 1', 'Extra Unused 2'])
        result = worker.enumerate_library(bpy, Path('owned-synthetic.blend'))
        self.assertEqual(result['summary']['source_materials'], 6)
        self.assertEqual(len(result['material_names']), 6)
        self.assertTrue(result['summary']['all_destination_requests_empty'])
        for key, value in context.destination.values.items():
            if key != 'version': self.assertEqual(value, [])

    def test_overbudget_catalogue_retains_summary_before_count_refusal(self):
        bpy, context = fake_bpy()
        context.source.values['materials'] = ['Synthetic %03d' % index for index in range(257)]
        result = {'status': 'REFUSED'}
        with self.assertRaisesRegex(worker.Refusal, 'BOUNDED_SOURCE_MATERIAL_CATALOGUE_COUNT'):
            worker.enumerate_library(bpy, Path('owned-synthetic.blend'),
                                     summary_sink=lambda summary: worker.record_summary(result, summary))
        self.assertEqual(result['status'], 'REFUSED')
        self.assertEqual(result['summary']['source_materials'], 257)
        self.assertTrue(result['summary']['actual_id_census_unchanged'])
        self.assertTrue(result['complete_actual_ID_census_observed'])
        self.assertNotIn('material_names', result)

    def test_changed_id_census_summary_is_available_before_safety_refusal(self):
        bpy, context = fake_bpy()
        context.exit_action = lambda: bpy.data.materials.append(ID('Unexpected synthetic ID', 500))
        summaries = []
        with self.assertRaisesRegex(worker.Refusal, 'ACTUAL_ID_CENSUS_CHANGED'):
            worker.enumerate_library(bpy, Path('owned-synthetic.blend'), summary_sink=summaries.append)
        self.assertEqual(len(summaries), 1)
        self.assertFalse(summaries[0]['actual_id_census_unchanged'])
        self.assertEqual(summaries[0]['after_id_count'], summaries[0]['before_id_count'] + 1)

    def test_summary_survives_a_later_factory_profile_failure(self):
        bpy, context = fake_bpy()
        result = {'status': 'REFUSED'}
        observation = worker.enumerate_library(bpy, Path('owned-synthetic.blend'),
                                               summary_sink=lambda summary: worker.record_summary(result, summary))
        with self.assertRaisesRegex(worker.Refusal, 'SYNTHETIC_LATER_FACTORY_REFUSAL'):
            worker.need(False, 'SYNTHETIC_LATER_FACTORY_REFUSAL')
        self.assertEqual(result['summary'], observation['summary'])
        self.assertEqual(result['status'], 'REFUSED')
        self.assertNotIn('material_names', result)

    def test_material_catalogue_bound_rejects_boolean_noninteger_zero_and_overflow(self):
        for count in (True, False, 0, -1, 257, 4.0, '5', None):
            with self.assertRaisesRegex(worker.Refusal, 'BOUNDED_SOURCE_MATERIAL_CATALOGUE_COUNT'):
                worker.validate_source_material_count(count)
        for count in (1, 4, 5, 256): worker.validate_source_material_count(count)

    def test_empty_requests_preserve_actual_complete_id_set_and_return_private_names(self):
        bpy, context = fake_bpy()
        result = worker.enumerate_library(bpy, Path('owned-synthetic.blend'))
        self.assertEqual(bpy.data.libraries.calls, [('owned-synthetic.blend', False)])
        self.assertEqual(context.entered, 1); self.assertEqual(context.exited, 1)
        self.assertEqual(result['material_names'], ('B Mat 2', 'B Mat 1', 'B Mat 4', 'B Mat 3'))
        summary = result['summary']
        self.assertEqual((summary['before_id_count'], summary['after_id_count'], summary['id_collections']), (4, 4, 4))
        self.assertEqual((summary['source_materials'], summary['source_id_types'], summary['source_catalogue_name_count']), (4, 4, 6))
        self.assertTrue(summary['actual_id_census_unchanged'])
        self.assertTrue(summary['all_destination_requests_empty'])
        self.assertTrue(all(value == [] for key, value in context.destination.values.items() if key != 'version'))

    def test_public_summary_contains_no_names_paths_pointers_or_id_rows(self):
        bpy, _context = fake_bpy()
        summary = worker.enumerate_library(bpy, 'private-owned-path')['summary']
        encoded = json.dumps(summary)
        for forbidden in ('private-owned-path', 'private-B-object-name', 'private-B-image-name', 'B Mat', 'Factory Cube'):
            self.assertNotIn(forbidden, encoded)
        self.assertNotIn('material_names', summary)
        self.assertNotIn('ids', summary)

    def test_material_order_and_spelling_change_digest_without_sorting_names(self):
        bpy, context = fake_bpy()
        first = worker.enumerate_library(bpy, 'owned')['summary']['source_material_names_sha256']
        context.source.values['materials'].reverse()
        second = worker.enumerate_library(bpy, 'owned')['summary']['source_material_names_sha256']
        self.assertNotEqual(first, second)
        context.source.values['materials'][0] = '非英語 material'
        third = worker.enumerate_library(bpy, 'owned')['summary']['source_material_names_sha256']
        self.assertNotEqual(second, third)

    def test_poison_image_getters_are_never_touched(self):
        bpy, _context = fake_bpy()
        self.assertIsInstance(bpy.data.images[0], Image)
        self.assertTrue(worker.enumerate_library(bpy, 'owned')['summary']['actual_id_census_unchanged'])

    def test_complete_census_checks_nonmaterial_collection_additions(self):
        bpy, context = fake_bpy()
        context.exit_action = lambda: bpy.data.objects.append(ID('Unexpected geometry ID', 25))
        with self.assertRaisesRegex(worker.Refusal, '^ACTUAL_ID_CENSUS_CHANGED$'):
            worker.enumerate_library(bpy, 'owned')
        self.assertEqual(context.exited, 1)

    def test_removal_or_rename_of_existing_ids_refuses(self):
        for mutate in ('remove', 'name', 'name_full'):
            bpy, context = fake_bpy()
            def change():
                if mutate == 'remove': bpy.data.objects.pop()
                else: setattr(bpy.data.objects[0], mutate, 'changed')
            context.exit_action = change
            with self.assertRaisesRegex(worker.Refusal, '^ACTUAL_ID_CENSUS_CHANGED$'):
                worker.enumerate_library(bpy, 'owned')

    def test_equal_numeric_pointer_and_name_cannot_replace_actual_id_reference(self):
        bpy, context = fake_bpy()
        context.exit_action = lambda: bpy.data.objects.__setitem__(0, ID('Factory Cube', 11))
        with self.assertRaisesRegex(worker.Refusal, '^ACTUAL_ID_CENSUS_CHANGED$'):
            worker.enumerate_library(bpy, 'owned')

    def test_actual_library_reference_changes_refuse_without_changing_id_count(self):
        bpy, context = fake_bpy()
        library = ID('Existing library', 31); bpy.data.libraries.append(library)
        context.exit_action = lambda: setattr(bpy.data.objects[0], 'library', library)
        with self.assertRaisesRegex(worker.Refusal, '^ACTUAL_ID_CENSUS_CHANGED$'):
            worker.enumerate_library(bpy, 'owned')

    def test_iteration_order_alone_does_not_invent_an_id_change(self):
        bpy, context = fake_bpy()
        context.exit_action = lambda: bpy.data.objects.reverse()
        self.assertTrue(worker.enumerate_library(bpy, 'owned')['summary']['actual_id_census_unchanged'])

    def test_unknown_or_cyclic_rna_collection_type_is_not_silently_skipped(self):
        for cycle in (False, True):
            bpy, _context = fake_bpy()
            fixed = NS(identifier='Unknown', base=None)
            if cycle: fixed.base = fixed
            bpy.data.bl_rna.properties.append(NS(identifier='unclassified', type='COLLECTION', fixed_type=fixed))
            bpy.data.unclassified = []
            with self.assertRaisesRegex(worker.Refusal, 'UNKNOWN_BLENDDATA_COLLECTION_TYPE'):
                worker.enumerate_library(bpy, 'owned')
            self.assertEqual(bpy.data.libraries.calls, [])

    def test_nonoriginal_alias_or_boolean_pointer_refuses_before_library_io(self):
        for mutation in ('original', 'pointer', 'alias'):
            bpy, _context = fake_bpy()
            if mutation == 'original': bpy.data.objects[0].original = ID('evaluated', 41)
            elif mutation == 'pointer': bpy.data.objects[0].pointer = True
            else: bpy.data.materials.append(bpy.data.objects[0])
            with self.assertRaises(worker.Refusal): worker.enumerate_library(bpy, 'owned')
            self.assertEqual(bpy.data.libraries.calls, [])

    def test_nonempty_destination_is_refused_and_never_rewritten(self):
        bpy, context = fake_bpy()
        context.destination.values['materials'] = ['unrequested preexisting request']
        with self.assertRaisesRegex(worker.Refusal, '^NONEMPTY_LIBRARY_REQUEST_REFUSED$'):
            worker.enumerate_library(bpy, 'owned')
        self.assertEqual(context.destination.values['materials'], ['unrequested preexisting request'])
        self.assertEqual(context.exited, 1)  # A body error is not assumed to roll back __exit__.

    def test_destination_mutation_during_context_exit_is_detected(self):
        bpy, context = fake_bpy()
        context.exit_action = lambda: context.destination.values['images'].append('unexpected')
        with self.assertRaisesRegex(worker.Refusal, '^NONEMPTY_LIBRARY_REQUEST_REFUSED$'):
            worker.enumerate_library(bpy, 'owned')

    def test_library_names_types_duplicates_and_budget_are_checked(self):
        for bad in ([7], ['same', 'same'], ['x' * 1025], ['x'] * (worker.MAX_NAMES + 1)):
            bpy, context = fake_bpy(); context.source.values['materials'] = bad
            with self.assertRaises(worker.Refusal): worker.enumerate_library(bpy, 'owned')
            self.assertEqual(context.exited, 1)

    def test_library_schema_and_version_are_not_guessed(self):
        for mutation in ('source_type', 'destination_key', 'version'):
            bpy, context = fake_bpy()
            if mutation == 'source_type': context.source.values['materials'] = ('not', 'a', 'list')
            elif mutation == 'destination_key': context.destination.values['foreign'] = []
            else: context.source.values['version'] = (True, 1, 0)
            with self.assertRaises(worker.Refusal): worker.enumerate_library(bpy, 'owned')


def request_fixture(project, **context_changes):
    stage = project / 'output' / 'synthetic-stage'
    for name in ('inputs', 'result', 'temp'):
        (stage / name).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    context = dict(full_suite_passed=True, full_job_physically_closed=True, exclusive_runtime_lease=True,
                   observed_owned_processes=0, functional_file_count=1061, tested_revision=worker.REVISION)
    context.update(context_changes)
    return dict(format='has_owned_B_empty_library_census_request_2', phase='ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED',
                created_utc=now.isoformat(), expires_utc=(now + datetime.timedelta(minutes=10)).isoformat(),
                private_arrays_public=False, owned_stage=str(stage), owned_output=str(stage / 'result'),
                owned_temp=str(stage / 'temp'), source_context=context,
                files={key: {} for key in worker.ROLES})


class SyntheticSupport:
    def safe(self, path): return Path(path).absolute()
    def pinned_read(self, path, count, digest):
        raw = Path(path).read_bytes()
        if type(count) is not int or len(raw) != count or worker.sha(raw) != digest:
            raise worker.Refusal('SYNTHETIC_PIN_REFUSAL')
        return raw, (1, 2, count, 3)


class BootstrapAndLeaseTests(unittest.TestCase):
    def check_lease(self, project, value):
        path = project / 'output' / 'synthetic-request.json'
        raw = json.dumps(value).encode(); path.write_bytes(raw)
        temporary = value['owned_temp']
        with patch.object(worker, 'PROJECT', project), patch.dict(os.environ, TEMP=temporary, TMP=temporary), \
             patch.object(worker.tempfile, 'gettempdir', return_value=temporary):
            return worker._request(SyntheticSupport(), path, worker.sha(raw))

    def test_fresh_exact_closed_root_context_is_admitted_with_eight_read_design(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory); value = request_fixture(project)
            lease, output, read = self.check_lease(project, value)
            self.assertEqual(set(lease['files']), worker.ROLES)
            self.assertEqual(len(lease['files']) + 1, 8)
            self.assertEqual(output, Path(value['owned_output']))
            self.assertEqual(read[2], worker.sha(read[0].read_bytes()))

    def test_false_missing_or_untyped_full_context_cannot_reach_host_api(self):
        changes = ({'full_suite_passed': False}, {'full_job_physically_closed': False},
                   {'exclusive_runtime_lease': False}, {'observed_owned_processes': False},
                   {'observed_owned_processes': 1}, {'functional_file_count': True},
                   {'functional_file_count': 1059}, {'tested_revision': 'old'})
        for change in changes:
            with tempfile.TemporaryDirectory() as directory:
                project = Path(directory); value = request_fixture(project, **change)
                with self.assertRaisesRegex(worker.Refusal, '^ROOT_FULL_9E_CLOSED_CONTEXT$'):
                    self.check_lease(project, value)

    def test_stale_overlong_or_naive_root_lease_refuses(self):
        for mode in ('expired', 'overlong', 'naive'):
            with tempfile.TemporaryDirectory() as directory:
                project = Path(directory); value = request_fixture(project)
                now = datetime.datetime.now(datetime.timezone.utc)
                if mode == 'expired': value['expires_utc'] = (now - datetime.timedelta(seconds=1)).isoformat()
                elif mode == 'overlong': value['expires_utc'] = (now + datetime.timedelta(hours=2)).isoformat()
                else: value['created_utc'] = now.replace(tzinfo=None).isoformat()
                with self.assertRaises(worker.Refusal): self.check_lease(project, value)

    def test_missing_role_wrong_format_and_existing_result_are_refused(self):
        for mode in ('role', 'format', 'result'):
            with tempfile.TemporaryDirectory() as directory:
                project = Path(directory); value = request_fixture(project)
                if mode == 'role': value['files'].pop('sentinel')
                elif mode == 'format': value['format'] = 'another operation'
                else: (Path(value['owned_output']) / 'PUBLIC_LIBRARY_CENSUS2.json').write_bytes(b'old')
                with self.assertRaises(worker.Refusal): self.check_lease(project, value)

    def test_strict_json_rejects_duplicate_or_nonfinite_fields(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaises(worker.Refusal): worker.strict_json(raw)

    def test_bootstrap_compiles_exact_raw_support_without_using_import_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic-support.py'
            raw = b'BOOTSTRAP_SYNTHETIC_VALUE = 42\n'; path.write_bytes(raw)
            name = '_has_empty_library_pinned_support'
            old = sys.modules.pop(name, None)
            try:
                with patch.object(worker, 'SUPPORT', path), patch.object(worker, 'SUPPORT_PIN', (len(raw), worker.sha(raw))):
                    module, record = worker._bootstrap_support()
                self.assertEqual(module.BOOTSTRAP_SYNTHETIC_VALUE, 42)
                self.assertEqual(record[1:3], (len(raw), worker.sha(raw)))
                self.assertEqual(module.__spec__.origin, str(path))
            finally:
                sys.modules.pop(name, None)
                if old is not None: sys.modules[name] = old

    def test_bad_support_hash_refuses_before_any_module_code_executes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic-support.py'
            raw = b'raise AssertionError("untrusted code executed")\n'; path.write_bytes(raw)
            with patch.object(worker, 'SUPPORT', path), patch.object(worker, 'SUPPORT_PIN', (len(raw), '0' * 64)):
                with self.assertRaisesRegex(worker.Refusal, '^SUPPORT_LITERAL_HASH_OR_STAMP$'):
                    worker._bootstrap_support()


if __name__ == '__main__':
    unittest.main()
