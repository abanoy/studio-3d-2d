"""Reviewed shape snapshots, immutable helpers and bounded sparse POSITION morphs."""
from pathlib import Path
import sys
import tempfile
import unittest
import json
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_secondary_helpers import H, fixture, request, write_glb


def shape_fixture(path):
    g = fixture(path)
    for pi, primitive in enumerate(g.doc['meshes'][0]['primitives']):
        positions = g.skin(3, pi)[4]
        primitive['targets'] = [
            {'POSITION': g.append([(.7 * (2-y) if pi == 1 else .4, .1, .2) for x, y, z in positions], 'VEC3')},
            {'POSITION': g.append([(-.2, 0., 0.)] * len(positions), 'VEC3')}]
    g.doc['meshes'][0]['weights'] = [.75, -.3]
    g.doc['meshes'][0]['extras']['targetNames'] = ['Loose part shape', 'Second shape']
    g.doc['nodes'][3]['weights'] = [.6, .2]
    write_glb(path, g.doc, bytes(g.binary))
    return H.GLB(path)


class MorphReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.path = self.root / 'shape.glb'; self.g = shape_fixture(self.path)

    def tearDown(self): self.temp.cleanup()

    def test_existing_review_stays_neutral(self):
        self.assertEqual(self.g.shaped_skin(3, 1)[4], self.g.skin(3, 1)[4])
        neutral = H.preview(self.path, request(self.g))
        self.assertEqual(neutral, H.preview(self.path, dict(request(self.g), source_morph_defaults=False)))

    def test_node_overrides_mesh_defaults_and_snapshot_overrides_both(self):
        self.assertEqual(self.g.morph_weights(3, {'source_morph_defaults': True}), [.6, .2])
        self.g.doc['nodes'][3].pop('weights')
        self.assertEqual(self.g.morph_weights(3, {'source_morph_defaults': True}), [.75, -.3])
        self.assertEqual(self.g.morph_weights(3, {'source_morph_defaults': True, 'morph_weights': {'3': [-1., 2.]}}), [-1., 2.])
        self.g.doc['meshes'][0].pop('weights')
        self.assertEqual(self.g.morph_weights(3, {'source_morph_defaults': True}), [0., 0.])

    def test_multiple_signed_targets_are_deltas_before_skinning(self):
        positions = self.g.skin(3, 1)[4]
        shaped = self.g.shaped_skin(3, 1, {'morph_weights': {'3': [-1., 2.]}})[4]
        for p, actual in zip(positions, shaped):
            expected = (p[0] - .7*(2-p[1]) - .4, p[1] - .1, p[2] - .2)
            for a, b in zip(actual, expected): self.assertAlmostEqual(a, b, places=6)

    def test_preview_and_derived_controls_use_shape_without_baking_source(self):
        before = (self.path.read_bytes(), self.path.stat().st_mtime_ns)
        plan = dict(request(self.g), source_morph_defaults=True)
        shaped = H.preview(self.path, plan); neutral = H.preview(self.path, request(self.g))
        self.assertEqual(shaped['source_vertices'], neutral['source_vertices'])
        self.assertNotEqual(shaped['points_in_anchor'], neutral['points_in_anchor'])
        for source_index, influences in zip(shaped['source_vertices'], shaped['vertices']):
            expected = self.g.shaped_skin(3, 1, plan)[4][source_index]
            actual = tuple(sum(v[k+1]*v[4] for v in influences) + (2. if k == 1 else 0.) for k in range(3))
            for a, b in zip(actual, expected): self.assertAlmostEqual(a, b, places=6)
        result = H.build(self.path, self.root / 'derived', plan); derived = H.GLB(result['glb'])
        self.assertEqual(result['report']['review_morph_weights'], [.6, .2])
        self.assertEqual(result['report']['points_in_anchor'], [tuple(p) for p in shaped['points_in_anchor']])
        self.assertEqual(derived.skin(3, 1)[4], self.g.skin(3, 1)[4])
        self.assertEqual(derived.doc['meshes'][0]['weights'], self.g.doc['meshes'][0]['weights'])
        self.assertEqual(derived.doc['nodes'][3]['weights'], self.g.doc['nodes'][3]['weights'])
        self.assertEqual(derived.doc['meshes'][0]['primitives'][1]['targets'], self.g.doc['meshes'][0]['primitives'][1]['targets'])
        self.assertTrue(bytes(derived.binary).startswith(self.g.binary))
        self.assertEqual((self.path.read_bytes(), self.path.stat().st_mtime_ns), before)

    def sparse(self, dense=False):
        primitive = self.g.doc['meshes'][0]['primitives'][1]
        a = self.g.doc['accessors'][primitive['targets'][0]['POSITION']]
        if not dense: a.pop('bufferView'); a.pop('byteOffset', None)
        indices = self.g.append([(2,), (8,)], 'SCALAR', 5121)
        values = self.g.append([(.9, .2, 0.), (.3, .4, .1)], 'VEC3')
        a['sparse'] = {'count': 2, 'indices': {'bufferView': self.g.doc['accessors'][indices]['bufferView'], 'componentType': 5121},
                       'values': {'bufferView': self.g.doc['accessors'][values]['bufferView']}}
        return a

    def test_sparse_zero_base_and_dense_replacement(self):
        for dense in (False, True):
            self.g = shape_fixture(self.path); a = self.sparse(dense)
            result = self.g.morph_delta(self.g.doc['meshes'][0]['primitives'][1]['targets'][0]['POSITION'], 24)
            self.assertAlmostEqual(result[2][0], .9, places=6); self.assertAlmostEqual(result[8][1], .4, places=6)
            self.assertAlmostEqual(result[0][0], 0., places=6)
            self.assertAlmostEqual(result[4][0], .168 if dense else 0., places=6)

    def test_invalid_weights_and_budget_refuse_before_output(self):
        for change in ({'source_morph_defaults': 1}, {'morph_weights': []}, {'morph_weights': {'03': [1., 0.]}},
                       {'morph_weights': {'3': [1.]}}, {'morph_weights': {'3': [True, 0.]}},
                       {'morph_weights': {'3': [float('nan'), 0.]}}, {'morph_weights': {'3': [101., 0.]}},
                       {'morph_weights': {'999': [1., 0.]}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                H.build(self.path, self.root / 'refused', dict(request(self.g), **change))
            self.assertFalse((self.root / 'refused').exists())
        self.g.morph_operations = 8000000
        with self.assertRaisesRegex(ValueError, 'budget'): self.g.shaped_skin(3, 1, {'source_morph_defaults': True})

    def test_sparse_corruption_and_target_mismatch_refuse(self):
        for change in ('count', 'indices', 'values', 'type', 'stride', 'nan'):
            self.g = shape_fixture(self.path); a = self.sparse()
            sparse = a['sparse']
            if change == 'count': sparse['count'] = 25
            if change == 'indices':
                import struct
                view = self.g.doc['bufferViews'][sparse['indices']['bufferView']]
                self.g.binary[view['byteOffset']:view['byteOffset']+2] = b'\x02\x02'
            if change == 'values': sparse['values']['byteOffset'] = 100000
            if change == 'type': a['componentType'] = 5123
            if change == 'stride': self.g.doc['bufferViews'][sparse['values']['bufferView']]['byteStride'] = 12
            if change == 'nan':
                import struct
                view = self.g.doc['bufferViews'][sparse['values']['bufferView']]
                struct.pack_into('<f', self.g.binary, view['byteOffset'], float('nan'))
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.g.shaped_skin(3, 1, {'source_morph_defaults': True})
        self.g = shape_fixture(self.path); self.g.doc['meshes'][0]['primitives'][0]['targets'].pop()
        with self.assertRaisesRegex(ValueError, 'Inconsistent'): self.g.morph_weights(3)

    def test_worker_uses_same_snapshot_for_inspect_preview_and_build(self):
        root = Path(__file__).resolve().parents[1]
        plan = dict(request(self.g), source_morph_defaults=True)
        results = {}
        for operation in ('inspect', 'preview', 'build'):
            folder = self.root / operation; folder.mkdir()
            (folder / 'request.json').write_text(json.dumps(plan), encoding='utf-8')
            subprocess.run([sys.executable, str(root / 'tools/secondary_helper_worker.py'), str(self.path), operation, str(folder)], check=True, timeout=10)
            result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
            self.assertTrue(result['ok'], result); results[operation] = result['value']
        row = next(r for r in results['inspect']['regions'] if r['node'] == 3 and r['primitive'] == 1 and r['component'] == 0)
        self.assertEqual(row, results['preview']['region'])
        self.assertEqual(row, results['build']['report']['region'])

    def test_component_ids_survive_shapes_moving_separate_regions_together(self):
        positions = self.g.skin(3, 1)[4]
        deltas = [(0., 0., 0.)] * 20 + [tuple(positions[i][k]-positions[20+i][k] for k in range(3)) for i in range(4)]
        self.g.doc['meshes'][0]['primitives'][1]['targets'][0]['POSITION'] = self.g.append(deltas, 'VEC3')
        write_glb(self.path, self.g.doc, bytes(self.g.binary)); self.g = H.GLB(self.path)
        plan = dict(request(self.g), component=1, morph_weights={'3': [1., 0.]})
        rows = H.inspect(self.path, plan)['regions']
        self.assertEqual(len(rows), 3)
        preview = H.preview(self.path, plan)
        self.assertEqual(preview['source_vertices'], [20, 21, 22, 23])
        self.assertEqual(preview['region']['component'], 1)

    def test_large_retained_target_list_with_one_active_high_index(self):
        for primitive in self.g.doc['meshes'][0]['primitives']:primitive['targets']=[primitive['targets'][0]]*520
        self.g.doc['meshes'][0]['extras']['targetNames']=['Shape '+str(i) for i in range(520)]
        self.g.doc['meshes'][0]['weights']=[0.]*520;self.g.doc['nodes'][3]['weights']=[0.]*519+[.6]
        write_glb(self.path,self.g.doc,bytes(self.g.binary));self.g=H.GLB(self.path)
        plan=dict(request(self.g),source_morph_defaults=True)
        positions=self.g.shaped_skin(3,1,plan)[4];base=self.g.skin(3,1)[4]
        for a,b in zip(positions,base):self.assertAlmostEqual(a[0],b[0]+.6*.7*(2-b[1]),places=6)
        result=H.build(self.path,self.root/'many-targets',plan)
        self.assertEqual(len(result['report']['review_morph_weights']),520)
        self.assertEqual(H.GLB(result['glb']).doc['meshes'][0]['primitives'][1]['targets'],self.g.doc['meshes'][0]['primitives'][1]['targets'])
        for primitive in self.g.doc['meshes'][0]['primitives']:primitive['targets']=[primitive['targets'][0]]*2049
        with self.assertRaisesRegex(ValueError,'excessive'):self.g.morph_weights(3,plan)


if __name__ == '__main__': unittest.main(verbosity=2)
