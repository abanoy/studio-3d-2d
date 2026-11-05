"""Observed geometry, conservative seed matching and source/identity protection."""
from pathlib import Path
from unittest.mock import patch
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import shape_observations as O
from test_helper_morphs import shape_fixture
from test_secondary_helpers import write_glb


class Observations(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.path = self.root / 'shapes.glb'
        self.g = shape_fixture(self.path)

    def save(self): write_glb(self.path, self.g.doc, bytes(self.g.binary))

    def labels(self, rows):
        return {'format': 'studio_deform_seeds_1', 'source_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(), 'controls': rows}

    def test_signed_observations_agree_with_independent_shared_evaluator(self):
        before = (self.path.read_bytes(), self.path.stat().st_mtime_ns)
        report = O.observe(self.path)
        self.assertEqual(report['target_count'], 2); self.assertEqual(report['signed_position_probes'], 4)
        for row in report['rows']:
            for sign, name in [(1, 'positive_position_bounds'), (-1, 'negative_position_bounds')]:
                weights = [0., 0.]; weights[row['target']] = sign
                points = [p for pi in range(2) for p in self.g.shaped_skin(3, pi, {'morph_weights': {'3': weights}})[4]]
                expected = [[min(p[k] for p in points) for k in range(3)], [max(p[k] for p in points) for k in range(3)]]
                self.assertEqual(row[name], expected)
        self.assertEqual((self.path.read_bytes(), self.path.stat().st_mtime_ns), before)

    def test_overlapping_region_withholds_self_and_uses_explicit_seed(self):
        label = {'node': 3, 'target': 0, 'native_name': 'Loose part shape', 'area': 'Hair', 'provenance': 'Manual choice'}
        report = O.observe(self.path, self.labels([label]))
        self.assertEqual(report['rows'][0]['region_estimate']['area'], 'Other')
        match = report['rows'][1]['region_estimate']
        self.assertEqual(match['area'], 'Hair'); self.assertEqual(match['matches'][0]['seed_target'], 0)
        self.assertEqual(match['matches'][0]['seed_provenance'], 'Manual choice')
        self.assertFalse(report['cross_model_validation']); self.assertFalse(report['probability_calibrated'])

    def test_conflicting_and_disjoint_regions_stay_unassigned(self):
        a = {'area': 'Eyes', 'node': 1, 'target': 0, 'native_name': 'a', 'provenance': 'Name estimate'}
        b = {**a, 'area': 'Mouth', 'target': 1}
        self.assertEqual(O.region_guess(0b1111, [(a, 0b0011), (b, 0b1100)])['area'], 'Other')
        self.assertEqual(O.region_guess(0b0001, [(b, 0b1100)])['area'], 'Other')
        self.assertEqual(O.region_guess(0, [(b, 1)])['area'], 'Other')

    def test_seed_identity_and_provenance_are_required(self):
        valid = {'node': 3, 'target': 0, 'native_name': 'Loose part shape', 'area': 'Hair', 'provenance': 'Name estimate'}
        for changed in [{'node': True}, {'node': 999}, {'target': 999}, {'native_name': 'renamed'}, {'area': 'Emote'}, {'provenance': 'certified'}, {'target': -1}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError): O.observe(self.path, self.labels([{**valid, **changed}]))
        with self.assertRaises(ValueError): O.observe(self.path, self.labels([valid, valid]))
        seeds = self.labels([valid]); seeds['source_sha256'] = '0' * 64
        with self.assertRaises(ValueError): O.observe(self.path, seeds)

    def test_no_position_is_unsupported_instead_of_unchanged(self):
        for primitive in self.g.doc['meshes'][0]['primitives']: primitive['targets'][0] = {'NORMAL': primitive['targets'][0]['POSITION']}
        self.save(); row = O.observe(self.path)['rows'][0]
        self.assertEqual(row['status'], 'position_unsupported'); self.assertTrue(row['nonposition_effects_unevaluated'])
        self.assertFalse(row['position_supported']); self.assertEqual(row['changed_vertices'], 0)

    def test_signed_bounds_include_primitives_without_position_target(self):
        self.g.doc['meshes'][0]['primitives'][1]['targets'][0] = {}; self.save()
        row = O.observe(self.path)['rows'][0]
        weights = [1., 0.]
        points = [p for pi in range(2) for p in self.g.shaped_skin(3, pi, {'morph_weights': {'3': weights}})[4]]
        self.assertEqual(row['positive_position_bounds'], [[min(p[k] for p in points) for k in range(3)], [max(p[k] for p in points) for k in range(3)]])

    def test_other_morph_attributes_are_flagged_unevaluated(self):
        for primitive in self.g.doc['meshes'][0]['primitives']: primitive['targets'][0] = {'TEXCOORD_0': primitive['targets'][0]['POSITION']}
        self.save(); row = O.observe(self.path)['rows'][0]
        self.assertEqual(row['status'], 'position_unsupported'); self.assertTrue(row['nonposition_effects_unevaluated'])

    def test_sparse_positions_are_observed_and_bad_sparse_order_refuses(self):
        primitive = self.g.doc['meshes'][0]['primitives'][1]; accessor = self.g.doc['accessors'][primitive['targets'][0]['POSITION']]
        accessor.pop('bufferView'); accessor.pop('byteOffset', None)
        indices = self.g.append([(2,), (8,)], 'SCALAR', 5121); values = self.g.append([(.9, .2, 0.), (.3, .4, .1)], 'VEC3')
        accessor['sparse'] = {'count': 2, 'indices': {'bufferView': self.g.doc['accessors'][indices]['bufferView'], 'componentType': 5121}, 'values': {'bufferView': self.g.doc['accessors'][values]['bufferView']}}
        self.save(); row = O.observe(self.path)['rows'][0]
        self.assertEqual(row['changed_vertices'], len(self.g.skin(3, 0)[4]) + 2)
        accessor['sparse']['count'] = True; self.save()
        with self.assertRaises(ValueError): O.observe(self.path)

    def test_budget_refuses_whole_report_without_pruning(self):
        with patch.object(O, 'MAX_OPERATIONS', 1), self.assertRaises(ValueError): O.observe(self.path)

    def test_cancellation_is_checked_during_study(self):
        calls = []
        def cancelled():
            calls.append(1)
            return len(calls) >= 4
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'cancelled'): O.observe(self.path, cancelled=cancelled)
        self.assertGreaterEqual(len(calls), 4); self.assertEqual(self.path.read_bytes(), before)

    def test_shared_mesh_nodes_keep_distinct_binding_and_seed_scope(self):
        self.g.doc['nodes'].append(copy.deepcopy(self.g.doc['nodes'][3])); self.save()
        label = {'node': 3, 'target': 0, 'native_name': 'Loose part shape', 'area': 'Hair', 'provenance': 'Name estimate'}
        report = O.observe(self.path, self.labels([label]))
        self.assertEqual(report['target_count'], 4)
        for row in report['rows'][2:]: self.assertEqual(row['region_estimate']['area'], 'Other')

    def test_cli_refuses_overwrite_and_writes_only_report(self):
        script = Path(O.__file__); output = self.root / 'report.json'; before = self.path.read_bytes()
        result = subprocess.run([sys.executable, str(script), str(self.path), str(output)], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(json.loads(output.read_text())['target_count'], 2)
        saved = output.read_bytes()
        result = subprocess.run([sys.executable, str(script), str(self.path), str(output)], capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0); self.assertEqual(output.read_bytes(), saved); self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
