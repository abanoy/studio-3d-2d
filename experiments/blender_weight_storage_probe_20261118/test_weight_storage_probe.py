"""CPU fakes/oracles only. Importing the probe does not import or run Blender."""
import copy
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import types
import unittest
from unittest.mock import patch

import weight_storage_contract as C
import blender_weight_storage_probe as P

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN_ID = 'a' * 32


class FakeID:
    def as_pointer(self):
        return id(self)


class FakeVertex:
    def __init__(self):
        self.groups = []


class FakeVertices(list):
    def add(self, count):
        self.extend(FakeVertex() for _ in range(count))


class FakeMesh(FakeID):
    def __init__(self, name, mode):
        self.name, self.mode = name, mode
        self.vertices = FakeVertices()
        self.validate_calls = 0

    def update(self):
        pass

    def validate(self):
        self.validate_calls += 1
        if self.mode == 'validate_raises':
            raise RuntimeError('synthetic validate failure')
        if self.mode == 'validate_reverse':
            for vertex in self.vertices:
                vertex.groups.reverse()
        return False


class FakeGroup:
    def __init__(self, name, index, owner):
        self.name, self.index, self.owner = name, index, owner

    def add(self, indices, value, mode):
        if self.owner.mode == 'write_raises':
            raise RuntimeError('synthetic weight failure')
        if type(indices) is not list or len(indices) != 1 or mode != 'REPLACE' or not value > 0:
            raise AssertionError('SourceIO API call shape differs')
        self.owner.add_calls += 1
        row = self.owner.data.vertices[indices[0]].groups
        if self.owner.mode == 'flush_subnormal' and 0 < value < 2 ** -126:
            value = 0.0
        found = next((entry for entry in row if entry.group == self.index), None)
        if found is None:
            row.append(types.SimpleNamespace(group=self.index, weight=value))
        elif self.owner.mode != 'keep_first':
            found.weight = value
        if self.owner.mode == 'sort_groups':
            row.sort(key=lambda item: item.group)


class FakeGroups(list):
    def __init__(self, owner):
        super().__init__(); self.owner = owner

    def new(self, *, name):
        group = FakeGroup(name, len(self), self.owner)
        self.append(group)
        return group


class FakeObject(FakeID):
    def __init__(self, name, mesh, mode):
        self.name, self.data, self.mode = name, mesh, mode
        self.vertex_groups = FakeGroups(self)
        self.add_calls = 0


class FakeCollection(list):
    def __init__(self, kind, mode):
        super().__init__(); self.kind, self.mode = kind, mode
        self.created = []

    def get(self, name):
        return next((item for item in self if item.name == name), None)

    def new(self, name, mesh=None):
        item = FakeMesh(name, self.mode) if self.kind == 'mesh' else FakeObject(name, mesh, self.mode)
        self.append(item); self.created.append(item)
        return item

    def remove(self, item, *, do_unlink):
        if do_unlink is not True:
            raise AssertionError('Owned removal must unlink')
        if self.mode == 'cleanup_raises' and self.kind == 'object':
            raise RuntimeError('synthetic cleanup failure')
        super().remove(item)


def fake_bpy(mode='correct'):
    meshes, objects = FakeCollection('mesh', mode), FakeCollection('object', mode)
    original_mesh = meshes.new('factory_mesh')
    original_object = objects.new('factory_object', original_mesh)
    return types.SimpleNamespace(data=types.SimpleNamespace(meshes=meshes, objects=objects)), original_mesh, original_object


class WeightStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = C.cases()

    def test_finite_counts_and_signed_zero_alphabet(self):
        self.assertEqual(len(self.catalogue), 21_952)
        calls = sum(word not in (0, 0x80000000) for case in self.catalogue for _, word in case)
        self.assertEqual(calls, 47_040)
        histogram = {index: 0 for index in range(4)}
        for case in self.catalogue:
            histogram[len(C.expected_row(case))] += 1
        self.assertEqual(histogram, {0: 512, 1: 6740, 2: 11700, 3: 3000})
        self.assertEqual(C.float_word(C.word_float(0x80000000)), 0x80000000)
        self.assertEqual(C.float_word(C.word_float(1)), 1)
        self.assertEqual(len({case for case in self.catalogue}), 21_952)
        for invalid in (.1, float('nan'), float('inf')):
            with self.assertRaises(ValueError): C.float_word(invalid)

    def test_independent_event_oracle_agrees_with_existing_generalized_source_ledger(self):
        source = ROOT / 'experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d')
        spec = importlib.util.spec_from_file_location('pinned_existing_replace_ledger', source)
        existing = importlib.util.module_from_spec(spec); spec.loader.exec_module(existing)
        for case in self.catalogue:
            writes = [[group, C.word_float(word)] for group, word in case]
            row = existing.replay_replace_weight_writes(writes)
            self.assertEqual(tuple((group, C.float_word(value)) for group, value in row), C.expected_row(case))

    def test_correct_fake_full_API_and_cleanup(self):
        bpy, original_mesh, original_object = fake_bpy()
        report = P.exercise_storage_api(bpy, RUN_ID)
        self.assertEqual(report['status'], 'BOUNDED_SYNTHETIC_STORAGE_MATCH')
        self.assertEqual(report['positive_add_calls'], 47_040)
        self.assertTrue(report['immediate']['all_cases_match'])
        self.assertTrue(report['after_validate']['all_cases_match'])
        self.assertTrue(report['immediate_vs_after_validate_exact'])
        self.assertEqual(bpy.data.meshes, [original_mesh])
        self.assertEqual(bpy.data.objects, [original_object])
        self.assertEqual(bpy.data.meshes.created[-1].validate_calls, 1)
        self.assertTrue(report['owned_object_mesh_cleanup_exact'])
        self.assertFalse(report['native_storage_rule_qualified'])
        self.assertFalse(report['actual_source_rows_or_saved_scene_qualified'])

    def test_wrong_storage_rules_are_counted_and_subnormal_failure_retained(self):
        for mode in ('sort_groups', 'keep_first', 'flush_subnormal'):
            with self.subTest(mode=mode):
                bpy, _, _ = fake_bpy(mode)
                report = P.exercise_storage_api(bpy, RUN_ID)
                self.assertEqual(report['status'], 'BOUNDED_SYNTHETIC_STORAGE_MISMATCH')
                for phase in ('immediate', 'after_validate'):
                    evidence = report[phase]
                    self.assertGreater(evidence['mismatch_cases'], 0)
                    self.assertLessEqual(len(evidence['bounded_examples']), 12)
                    self.assertNotEqual(evidence['observed_ordered_rows_sha256'], evidence['expected_ordered_rows_sha256'])
                self.assertTrue(report['owned_object_mesh_cleanup_exact'])
                if mode == 'flush_subnormal':
                    examples = report['immediate']['bounded_examples']
                    self.assertTrue(any(any(word == '00000001' for _, word in example['expected']) and
                                        any(word == '00000000' for _, word in example['observed']) for example in examples))

    def test_validate_order_change_is_distinguished_from_immediate_behavior(self):
        bpy, _, _ = fake_bpy('validate_reverse')
        report = P.exercise_storage_api(bpy, RUN_ID)
        self.assertTrue(report['immediate']['all_cases_match'])
        self.assertFalse(report['after_validate']['all_cases_match'])
        self.assertFalse(report['immediate_vs_after_validate_exact'])
        self.assertEqual(report['status'], 'BOUNDED_SYNTHETIC_STORAGE_MISMATCH')
        self.assertTrue(report['owned_object_mesh_cleanup_exact'])

    def test_failure_cleanup_preserves_only_preexisting_IDs(self):
        for mode in ('write_raises', 'validate_raises'):
            bpy, original_mesh, original_object = fake_bpy(mode)
            report = P.exercise_storage_api(bpy, RUN_ID)
            self.assertEqual(report['status'], 'PROBE_FAILED')
            self.assertEqual(report['error_type'], 'RuntimeError')
            self.assertTrue(report['owned_object_mesh_cleanup_exact'])
            self.assertEqual(bpy.data.meshes, [original_mesh])
            self.assertEqual(bpy.data.objects, [original_object])

    def test_cleanup_failure_refuses_success(self):
        bpy, _, _ = fake_bpy('cleanup_raises')
        report = P.exercise_storage_api(bpy, RUN_ID)
        self.assertEqual(report['status'], 'PROBE_FAILED')
        self.assertFalse(report['owned_object_mesh_cleanup_exact'])
        self.assertEqual(report['cleanup_error_types'], ['object:RuntimeError'])

    def test_background_receipt_requires_desktop_without_fabricated_window(self):
        receipt = {'format': 'studio_private_desktop_1', 'exit': 0, 'child_desktop_confirmed': True,
                   'foreground_child_observed': False, 'desktop_switch_requested': False,
                   'job_closed': True, 'desktop_closed': True, 'private_window_seen': False}
        self.assertFalse(C.qualify_background_receipt(receipt)['private_window_seen'])
        for field, value in [('exit', False), ('child_desktop_confirmed', False),
                             ('foreground_child_observed', True), ('job_closed', 1),
                             ('private_window_seen', 0), ('error', 'failed'), ('cancelled', False)]:
            bad = dict(receipt); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): C.qualify_background_receipt(bad)

    def test_public_report_validator_binds_complete_evidence_and_rejects_canned_status(self):
        bpy, _, _ = fake_bpy(); report = P.exercise_storage_api(bpy, RUN_ID)
        scripts = {name: {'bytes': 1, 'sha256': 'b' * 64} for name in
                   ('blender_weight_storage_probe.py', 'weight_storage_contract.py')}
        runtime = {'path': 'synthetic-runtime', 'bytes': 1, 'sha256': 'c' * 64}
        report.update({'request_sha256': 'a' * 64, 'copied_script_identities': scripts,
                       'Root_expected_runtime_identity': runtime, 'runtime_binary_hash_verified_by_probe': False,
                       'runtime_version': [5, 1, 0], 'runtime_version_string': 'synthetic CPU fake',
                       'runtime_build_hash': 'synthetic', 'native_API_execution_observed_by_this_script': True,
                       'factory_background_no_model_file': True, 'scene_or_native_model_files_opened': False,
                       'files_exported_or_blend_saved': False, 'window_or_desktop_API_called_by_probe': False})
        report = json.loads(json.dumps(report))  # Actual file's JSON key types.
        options = dict(expected_request_sha256='a' * 64, expected_run_id=RUN_ID,
                       expected_scripts=scripts, expected_runtime=runtime)
        self.assertFalse(C.validate_matching_public_report(report, **options)['native_storage_rule_qualified'])
        for mutation in ('request', 'observed_hash', 'case_bool', 'missing_phase', 'mismatch_status', 'extra_payload'):
            bad = copy.deepcopy(report)
            if mutation == 'request': bad['request_sha256'] = '0' * 64
            elif mutation == 'observed_hash': bad['immediate']['observed_ordered_rows_sha256'] = '0' * 64
            elif mutation == 'case_bool': bad['immediate']['mismatch_cases'] = False
            elif mutation == 'missing_phase': del bad['after_validate']
            elif mutation == 'mismatch_status': bad['status'] = 'BOUNDED_SYNTHETIC_STORAGE_MISMATCH'
            else: bad['unexpected_geometry'] = []
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                C.validate_matching_public_report(bad, **options)

    def test_missing_extra_and_reordered_readback_rows_refuse(self):
        rows = tuple(C.expected_row(case) for case in self.catalogue)
        self.assertFalse(C.compare_readback(self.catalogue, rows[:-1])['all_cases_match'])
        self.assertFalse(C.compare_readback(self.catalogue, rows + ((),))['all_cases_match'])
        permuted = list(rows); permuted[0], permuted[2] = permuted[2], permuted[0]
        self.assertGreater(C.compare_readback(self.catalogue, tuple(permuted))['mismatch_cases'], 0)
        with self.assertRaises(ValueError): C.row_digest((((True, 1),),))
        with self.assertRaises(ValueError): C.expected_row(((0, True), (1, 0), (2, 0)))

    def test_fresh_owned_request_script_pin_and_path_guards(self):
        with tempfile.TemporaryDirectory(prefix='synthetic-weight-plan-') as directory:
            allowed = Path(directory).resolve(); owned = allowed / 'run'; source = owned / 'source'
            source.mkdir(parents=True); (owned / 'temp').mkdir()
            scripts = {}
            for name in ('blender_weight_storage_probe.py', 'weight_storage_contract.py'):
                raw = (HERE / name).read_bytes(); (source / name).write_bytes(raw)
                scripts[name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            plan = {'format': 'has_fresh_synthetic_weight_storage_request_1',
                    'phase': 'ROOT_APPROVED_FRESH_SYNTHETIC_ONLY', 'run_id': RUN_ID,
                    'expires_utc': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                    'owned_root': str(owned), 'owned_temp': str(owned / 'temp'),
                    'public_output': str(owned / 'PUBLIC_WEIGHT_STORAGE.json'),
                    'runtime': {'path': str(allowed / 'synthetic_runtime.exe'), 'bytes': 1, 'sha256': 'a' * 64},
                    'scripts': scripts}
            path = owned / 'request.json'; path.write_text(json.dumps(plan), encoding='utf-8')
            with patch.object(P, 'WORKSPACE_OUTPUT', allowed), patch.object(P, 'HERE', source), \
                    patch.object(P.C, '__file__', str(source / 'weight_storage_contract.py')), \
                    patch.dict(P.os.environ, {'TEMP': str(owned / 'temp'), 'TMP': str(owned / 'temp')}):
                checked, _ = P.read_plan(path)
                self.assertEqual(checked, plan)
                for field, value in [('expires_utc', (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()),
                                     ('public_output', str(allowed / 'other.json')),
                                     ('phase', 'EXPIRED_DCB_ADMISSION')]:
                    bad = copy.deepcopy(plan); bad[field] = value; path.write_text(json.dumps(bad), encoding='utf-8')
                    with self.subTest(field=field), self.assertRaises(ValueError): P.read_plan(path)
                path.write_text(json.dumps(plan), encoding='utf-8')
                oversized = owned / 'oversized.json'; oversized.write_bytes(b'x' * (32 * 1024 + 1))
                with self.assertRaises(ValueError): P._bounded_regular_bytes(oversized, 32 * 1024)
                with self.assertRaises(ValueError): P._bounded_regular_bytes(path, 32 * 1024, expected_size=True)
                (source / 'weight_storage_contract.py').write_bytes(b'changed source')
                with self.assertRaises(ValueError): P.read_plan(path)
                with self.assertRaises(ValueError): P._unique_pairs([('a', 1), ('a', 2)])


if __name__ == '__main__':
    unittest.main()
