"""Reviewed native-chain setup preserves skin and discloses shared geometry."""
from pathlib import Path
import copy
import hashlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_secondary_helpers import H, fixture, write_glb


def existing_fixture(path):
    g = fixture(path)
    # Existing weighted head -> strand root -> strand middle -> strand tip.
    g.doc['nodes'][2]['children'] = [4]
    g.doc['nodes'] += [{'name': 'StrandRoot', 'translation': [0, -.2, 0], 'children': [5]},
                       {'name': 'StrandMiddle', 'translation': [0, -.2, 0], 'children': [6]},
                       {'name': 'StrandTip', 'translation': [0, -.2, 0]}]
    skin = g.doc['skins'][0]; skin['joints'] = [1, 2, 4, 5, 6]
    skin['inverseBindMatrices'] = g.append([H.IDENTITY, H.translation((0, -2, 0)),
        H.translation((0, -1.8, 0)), H.translation((0, -1.6, 0)), H.translation((0, -1.4, 0))], 'MAT4')
    p = g.doc['meshes'][0]['primitives'][1]
    p['attributes']['JOINTS_0'] = g.append([(1, 0, 0, 0)] * 4 + [(2, 0, 0, 0)] * 4 +
        [(3, 0, 0, 0)] * 4 + [(4, 0, 0, 0)] * 8 + [(4, 0, 0, 0)] * 4, 'VEC4', 5121)
    # A disconnected surface in this fixture shares the tip's native joint.
    p['attributes']['WEIGHTS_0'] = g.append([(1, 0, 0, 0)] * 24, 'VEC4')
    write_glb(path, g.doc, bytes(g.binary))
    return H.GLB(path)


class ExistingJoints(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root/'native.glb'; self.g = existing_fixture(self.source)
        self.request = {'source_sha256': self.g.sha, 'node': 3, 'primitive': 1,
                        'component': 0, 'anchor_node': 4, 'segments': 3,
                        'review_only': True, 'use_existing_joints': True, 'reviewed': True}
    def tearDown(self): self.temp.cleanup()

    def test_explicit_opt_in_keeps_single_anchor_generation_refusal(self):
        ordinary = dict(self.request); ordinary.pop('use_existing_joints')
        self.assertFalse(H.preview(self.source, ordinary)['can_apply'])
        ordinary.pop('review_only')
        with self.assertRaisesRegex(ValueError, 'no usable weights'): H.preview(self.source, ordinary)
        view = H.preview(self.source, self.request)
        self.assertTrue(view['can_apply']); self.assertEqual(view['existing_chain']['joint_nodes'], [4, 5, 6])
        self.assertEqual(view['existing_chain']['center_node'], 2)

    def test_preview_discloses_every_shared_region_and_terminal_endpoint(self):
        view = H.preview(self.source, self.request)
        self.assertEqual([r['component'] for r in view['affected_regions']], [0, 1])
        self.assertEqual([r['affected_vertices'] for r in view['affected_regions']], [16, 4])
        self.assertEqual(len(view['vertices']), 24)
        points = view['points_in_anchor']
        self.assertEqual(len(points), 4)
        self.assertGreater(H.distance(points[-1], points[-2]), 1e-6)

    def test_build_changes_no_skin_accessor_binary_or_native_animation(self):
        self.g.doc['animations'] = [{'name': 'retained', 'channels': [], 'samplers': []}]
        write_glb(self.source, self.g.doc, bytes(self.g.binary)); self.g = H.GLB(self.source)
        self.request['source_sha256'] = self.g.sha
        original = self.source.read_bytes(); stamp = self.source.stat().st_mtime_ns
        result = H.build(self.source, self.root/'derived', self.request); new = H.GLB(result['glb'])
        for key in ['skins', 'meshes', 'accessors', 'bufferViews', 'materials', 'images', 'animations']:
            self.assertEqual(new.doc.get(key), self.g.doc.get(key), key)
        self.assertEqual(new.binary, self.g.binary)
        self.assertEqual(result['report']['changed_vertices'], 0)
        self.assertEqual(len(new.doc['nodes']), len(self.g.doc['nodes']) + 1)
        self.assertEqual(new.doc['nodes'][:-1], self.g.doc['nodes'][:6] +
                         [dict(self.g.doc['nodes'][6], children=[7])])
        self.assertEqual(new.springs()[0]['joints'][-1]['node'], 7)
        self.assertNotIn(7, new.doc['skins'][0]['joints'])
        self.assertEqual(self.source.read_bytes(), original); self.assertEqual(self.source.stat().st_mtime_ns, stamp)

    def test_declared_chain_cannot_be_reconfigured_or_overwritten(self):
        result = H.build(self.source, self.root/'first', self.request); new = H.GLB(result['glb'])
        request = dict(self.request, source_sha256=new.sha)
        with self.assertRaisesRegex(ValueError, 'no available'): H.build(new.source, self.root/'second', request)
        self.assertFalse((self.root/'second').exists())
        with self.assertRaisesRegex(ValueError, 'never replaced'): H.build(self.source, self.root/'first', self.request)

    def test_review_stale_invalid_mode_and_patch_refuse_before_output(self):
        for change in [{'reviewed': False}, {'source_sha256': '0'*64},
                       {'use_existing_joints': 'yes'}, {'vertex_mask': list(range(8))}]:
            with self.assertRaises(ValueError): H.build(self.source, self.root/'no', dict(self.request, **change))
            self.assertFalse((self.root/'no').exists())

    def test_branched_weights_do_not_offer_an_automatic_chain(self):
        self.g.doc['nodes'][2]['children'].append(6)
        self.g.doc['nodes'][5].pop('children')
        write_glb(self.source, self.g.doc, bytes(self.g.binary)); self.g = H.GLB(self.source)
        with self.assertRaisesRegex(ValueError, 'no available'):
            H.preview(self.source, dict(self.request, source_sha256=self.g.sha))

    def test_endpoint_cannot_exceed_source_node_budget(self):
        self.g.doc['nodes'] += [{} for _ in range(100000-len(self.g.doc['nodes']))]
        write_glb(self.source, self.g.doc, bytes(self.g.binary)); self.g = H.GLB(self.source)
        with self.assertRaisesRegex(ValueError, '100000source-node'):
            H.build(self.source, self.root/'too-many-nodes', dict(self.request, source_sha256=self.g.sha))
        self.assertFalse((self.root/'too-many-nodes').exists())

    def test_endpoint_cannot_exceed_combined_spring_node_budget(self):
        start = len(self.g.doc['nodes'])
        self.g.doc['nodes'] += [{'name': 'OtherSpring'+str(i)} for i in range(512)]
        self.g.doc['extras'] = {'has_secondary_helpers_1': {'specVersion': '1.0',
            'springs': [{'joints': [{'node': start+i} for i in range(512)]}]}}
        write_glb(self.source, self.g.doc, bytes(self.g.binary)); self.g = H.GLB(self.source)
        with self.assertRaisesRegex(ValueError, '512spring-node'):
            H.build(self.source, self.root/'too-many-springs', dict(self.request, source_sha256=self.g.sha))
        self.assertFalse((self.root/'too-many-springs').exists())

    def test_extrapolated_endpoint_must_stay_in_supported_coordinates(self):
        binds = self.g.accessor(self.g.doc['skins'][0]['inverseBindMatrices'], 'MAT4')
        binds[-1] = H.translation((-100000, -1.4, 0))
        self.g.doc['skins'][0]['inverseBindMatrices'] = self.g.append(binds, 'MAT4')
        write_glb(self.source, self.g.doc, bytes(self.g.binary)); self.g = H.GLB(self.source)
        with self.assertRaisesRegex(ValueError, 'no available'):
            H.build(self.source, self.root/'far-endpoint', dict(self.request, source_sha256=self.g.sha))
        self.assertFalse((self.root/'far-endpoint').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
