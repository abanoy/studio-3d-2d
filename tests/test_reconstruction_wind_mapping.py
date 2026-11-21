"""Generated-only reconstruction -> real hidden wind-candidate admission controls.

No processes, renderer, private inputs, authored-model installation or network.
"""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import secondary_helpers as H
import secondary_helpers_batch as B
import wind_helper_preview as W
from test_secondary_helpers import mixed_fixture


class ReconstructionWindMapping(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)
        self.source = self.folder / 'source.glb'
        self.before = mixed_fixture(self.source)
        self.original = self.source.read_bytes()
        self.stamp = self.source.stat().st_mtime_ns
        self.item = dict(source_sha256=self.before.sha, reviewed=True, node=3,
                         primitive=1, component=0, segments=3,
                         reconstruct_weights=True)
        self.context = dict(actor_id='generated-model', root_instance_id='42',
                            revision='7', frame='0', authored_sha256='a' * 64,
                            shape_sha256='b' * 64, bindings_sha256='c' * 64)

    def tearDown(self):
        try:
            self.assertEqual(self.source.read_bytes(), self.original)
            self.assertEqual(self.source.stat().st_mtime_ns, self.stamp)
        finally:
            self.temporary.cleanup()

    def build(self, items=None):
        items = copy.deepcopy(items or [self.item])
        setup = dict(format=B.FORMAT, source_sha256=self.before.sha,
                     reviewed=True, items=items)
        plan = B.plan(self.source, setup)
        result = B.build(self.source, self.folder / 'candidate', setup)
        after = H.GLB(result['glb'])
        return plan, result, after

    def hidden(self, items=None):
        items = copy.deepcopy(items or [self.item])
        boundary = self.folder / 'wind'
        boundary.mkdir()
        lease = W.DraftLease(boundary)
        pending = lease.begin(self.source, items, self.context,
                              'included-batch' if len(items) > 1 else 'focused-single')
        value = W.build_candidate(pending['job'], boundary)
        return lease, pending, value

    def second_reconstructed(self):
        # This independent four-vertex patch has too few cross-sections for the
        # automatic four-point average; use an actually reviewed nonzero guide.
        return dict(self.item, component=1,
                    points_in_anchor=[[-.55, .4, .1], [-.55, .7, .1],
                                      [-.55, 1., .1], [-.55, 1.3, .1]])

    def test_single_real_candidate_is_hidden_and_all_guides_are_mapped(self):
        lease, pending, value = self.hidden()
        accepted = lease.accept(self.context, value['completion'])
        self.assertEqual(lease.phase, 'prepared_hidden')
        self.assertEqual(accepted['operations'][0]['mode'], 'reconstructed_weights')
        candidate = H.GLB(pending['job'] / accepted['candidate']['path'])
        actual = [j['node'] for c in candidate.springs() for j in c['joints']]
        self.assertEqual(accepted['operations'][0]['candidate_helper_nodes'], actual)
        self.assertEqual(len(candidate.springs()), 3)
        self.assertEqual(len(actual), 12)
        self.assertFalse(accepted['authored_edit_created'])
        self.assertFalse(accepted['managed_asset_created'])
        self.assertFalse(accepted['render_admitted'])

    def test_two_reconstructed_regions_have_disjoint_complete_operation_groups(self):
        second = self.second_reconstructed()
        lease, pending, value = self.hidden([self.item, second])
        accepted = lease.accept(self.context, value['completion'])
        candidate = H.GLB(pending['job'] / accepted['candidate']['path'])
        groups = [set(x['candidate_helper_nodes']) for x in accepted['operations']]
        self.assertEqual(len(groups), 2)
        self.assertFalse(groups[0] & groups[1])
        self.assertEqual(set.union(*groups),
                         {j['node'] for c in candidate.springs() for j in c['joints']})
        self.assertEqual(len({x['operation_id'] for x in accepted['operations']}), 2)
        self.assertEqual({tuple(x['source_regions'][0]) for x in accepted['operations']},
                         {(3, 1, 0), (3, 1, 1)})

    def test_mixed_reconstructed_and_ordinary_weighted_paths_remain_distinct(self):
        ordinary = dict(self.item, component=1, reconstruct_weights=False,
                        anchor_node=2)
        lease, _, value = self.hidden([self.item, ordinary])
        accepted = lease.accept(self.context, value['completion'])
        self.assertEqual([x['mode'] for x in accepted['operations']],
                         ['reconstructed_weights', 'weighted'])

    def test_report_order_is_not_used_as_an_operation_identity(self):
        plan, result, after = self.build([self.item, self.second_reconstructed()])
        expected = W.operation_map(plan, result, self.before, after)
        result['reports'].reverse()
        self.assertEqual(W.operation_map(plan, result, self.before, after), expected)

    def test_wrong_report_prefix_is_refused(self):
        plan, result, after = self.build()
        result['reports'][0]['guide_prefix'] += '_wrong'
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_changed_candidate_joint_name_is_refused(self):
        plan, result, after = self.build()
        node = result['reports'][0]['helper_nodes'][1]
        after.doc['nodes'][node]['name'] += '_wrong'
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_duplicated_guide_node_is_refused(self):
        plan, result, after = self.build()
        nodes = result['reports'][0]['helper_nodes']
        nodes[1] = nodes[0]
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_changed_reviewed_points_are_refused(self):
        plan, result, after = self.build()
        result['reports'][0]['points_in_anchor'][1][1] -= .2
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_report_from_another_source_is_refused(self):
        plan, result, after = self.build()
        result['reports'][0]['source_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_changed_actual_guide_position_is_refused_before_wind(self):
        plan, result, after = self.build()
        node = result['reports'][0]['helper_nodes'][1]
        after.doc['nodes'][node]['translation'][1] -= .4
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_changed_actual_guide_parent_is_refused_before_wind(self):
        plan, result, after = self.build()
        first, second = result['reports'][0]['helper_nodes'][:2]
        after.doc['nodes'][first]['children'].remove(second)
        after.doc['nodes'][0].setdefault('children', []).append(second)
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_extra_guide_scale_is_refused_before_wind(self):
        plan, result, after = self.build()
        node = result['reports'][0]['helper_nodes'][1]
        after.doc['nodes'][node]['scale'] = [2., 1., 1.]
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_changed_generated_inverse_bind_is_refused_before_wind(self):
        plan, result, after = self.build()
        skin = after.doc['skins'][0]
        binds = after.accessor(skin['inverseBindMatrices'], 'MAT4')
        node = result['reports'][0]['helper_nodes'][1]
        slot = skin['joints'].index(node)
        changed = list(binds[slot])
        changed[13] -= .4
        binds[slot] = changed
        skin['inverseBindMatrices'] = after.append(binds, 'MAT4')
        with self.assertRaises(ValueError):
            W.operation_map(plan, result, self.before, after)

    def test_actor_context_change_rejects_an_otherwise_complete_hidden_candidate(self):
        lease, _, value = self.hidden()
        with self.assertRaises(ValueError):
            lease.accept(dict(self.context, revision='8'), value['completion'])
        self.assertEqual(lease.phase, 'stopped')

    def test_post_completion_candidate_tamper_is_not_admitted(self):
        lease, pending, value = self.hidden()
        path = pending['job'] / value['receipt']['candidate']['path']
        raw = bytearray(path.read_bytes())
        raw[-1] ^= 1
        path.write_bytes(raw)
        with self.assertRaises(ValueError):
            lease.accept(self.context, value['completion'])
        self.assertIsNone(lease.prepared)

    def test_post_completion_report_tamper_is_not_admitted(self):
        lease, pending, value = self.hidden()
        path = pending['job'] / 'preview-receipt.json'
        receipt = json.loads(path.read_bytes())
        receipt['reports'][0]['guide_prefix'] += '_wrong'
        path.write_bytes(W.encoded(receipt))
        with self.assertRaises(ValueError):
            lease.accept(self.context, value['completion'])


if __name__ == '__main__':
    unittest.main()
