"""CPU-only imported protocol + real existing builders on authored tiny GLBs.

No Godot, native asset converter, external worker process or private model runs.
"""
from pathlib import Path
import copy
import importlib.util
import io
import json
import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
from test_secondary_helpers import H, two_panel_fixture, request, write_glb
from test_secondary_existing_joints import existing_fixture
import secondary_helpers_batch as batch
spec = importlib.util.spec_from_file_location('output_wind_helper_preview', OUT / 'candidate/tools/wind_helper_preview.py')
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
RUN = OUT / 'cpu-results' / uuid.uuid4().hex


class PreviewProtocol(unittest.TestCase):
    def setUp(self):
        self.root = RUN / self._testMethodName; self.root.mkdir(parents=True, exist_ok=False)
        self.source = self.root / 'authored-source.glb'; self.glb = two_panel_fixture(self.source)
        self.owned = self.root / 'jobs'; self.owned.mkdir()
        self.context = {'actor_id': 'original-object', 'root_instance_id': str(2**63 + 17),
                        'revision': '7', 'frame': '12', 'authored_sha256': 'a' * 64,
                        'shape_sha256': 'b' * 64, 'bindings_sha256': 'c' * 64}
        self.first = request(self.glb); self.second = dict(self.first, component=1)
        self.source_before = P.identity(self.source)
        self.lease = P.DraftLease(self.owned); self.completion = {}

    def build(self, items=None, mode='focused-single'):
        token = self.lease.begin(self.source, items or [self.first], self.context, mode)
        value = P.build_candidate(token['job'], self.owned)
        self.completion = value['completion']
        return token, value['receipt']

    def assert_source(self): self.assertEqual(P.identity(self.source), self.source_before)

    def test_single_precise_controls_prepare_without_install_or_apply(self):
        reviewed = copy.deepcopy(self.first)
        reviewed['points_in_anchor'] = batch.review(self.source, reviewed)['points_in_anchor']
        reviewed['points_in_anchor'][1][0] += 0.0000000001234567
        before = copy.deepcopy(reviewed); token, value = self.build([reviewed])
        receipt = self.lease.accept(self.context, self.completion)
        self.assertEqual(reviewed, before); self.assertEqual(receipt['reports'][0]['points_in_anchor'], reviewed['points_in_anchor'])
        self.assertEqual(self.lease.phase, 'prepared_hidden'); self.assertFalse(receipt['render_admitted'])
        self.assertFalse(receipt['authored_edit_created']); self.assertFalse(receipt['managed_asset_created'])
        self.assertEqual(len(H.GLB(token['job'] / 'candidate/scene.glb').springs()), 1); self.assert_source()

    def test_all_included_setups_build_with_independent_operation_identities(self):
        items = [self.first, self.second]; before = copy.deepcopy(items)
        token, receipt = self.build(items, 'included-batch')
        accepted = self.lease.accept(self.context, self.completion)
        self.assertEqual(items, before); self.assertEqual(accepted['setup_members_built'], 2)
        self.assertEqual(len(H.GLB(token['job'] / 'candidate/scene.glb').springs()), 2)
        self.assertEqual(len({row['operation_id'] for row in receipt['operations']}), 2)
        self.assertEqual({tuple(row['source_regions'][0]) for row in receipt['operations']}, {(3, 1, 0), (3, 1, 1)})
        self.assert_source()

    def test_authored_vrm0_and_vrm1_style_declarations_survive_new_setup(self):
        for family in ('v0', 'v1'):
            with self.subTest(family=family):
                path = self.root / (family + '.glb'); original = two_panel_fixture(path, family)
                before = P.identity(path); lease = P.DraftLease(self.owned)
                token = lease.begin(path, [request(original)], self.context)
                prepared = P.build_candidate(token['job'], self.owned); accepted = lease.accept(self.context, prepared['completion'])
                candidate = H.GLB(token['job'] / 'candidate/scene.glb')
                self.assertEqual(candidate.doc['extensions'], original.doc['extensions'])
                self.assertEqual(len(candidate.springs()), 2); self.assertEqual(P.identity(path), before)
                proof = json.loads((token['job'] / 'bindings.json').read_bytes())
                self.assertEqual(proof['retained_declarations'], 1)

    def test_shared_existing_joints_deduplicate_by_chain_not_display_rows(self):
        path = self.root / 'existing.glb'; original = existing_fixture(path)
        # The base fixture's disconnected patch is tip-only. Give this authored
        # shared-chain fixture all four chain influences, as the existing batch
        # regression does, so both rows actually propose that same full chain.
        primitive = original.doc['meshes'][0]['primitives'][1]
        joints = original.accessor(primitive['attributes']['JOINTS_0'], 'VEC4')
        joints[-4:] = [(1, 0, 0, 0), (2, 0, 0, 0), (3, 0, 0, 0), (4, 0, 0, 0)]
        primitive['attributes']['JOINTS_0'] = original.append(joints, 'VEC4', 5121)
        write_glb(path, original.doc, bytes(original.binary)); original = H.GLB(path); before = P.identity(path)
        first = {'source_sha256': original.sha, 'node': 3, 'primitive': 1, 'component': 0,
                 'anchor_node': 4, 'segments': 3, 'review_only': True, 'use_existing_joints': True, 'reviewed': True}
        lease = P.DraftLease(self.owned)
        token = lease.begin(path, [first, dict(first, component=1)], self.context, 'included-batch')
        prepared = P.build_candidate(token['job'], self.owned); receipt = prepared['receipt']; lease.accept(self.context, prepared['completion'])
        candidate = H.GLB(token['job'] / 'candidate/scene.glb')
        self.assertEqual(receipt['setup_members_built'], 2); self.assertEqual(len(receipt['operations']), 1)
        self.assertEqual(receipt['operations'][0]['configured_source_nodes'], [4, 5, 6])
        self.assertEqual(len(receipt['operations'][0]['source_regions']), 2)
        self.assertEqual(len(candidate.springs()), 1); self.assertEqual(candidate.binary, original.binary)
        self.assertEqual(receipt['reports'][0]['changed_vertices'], 0); self.assertEqual(P.identity(path), before)

    def test_cancellation_rejects_late_completed_candidate_without_deleting_it(self):
        token = self.lease.begin(self.source, [self.first], self.context)
        self.lease.invalidate('closed')
        # A cancelled owned worker may still finish publishing its private files.
        # It must have no path back into the current owner/generation.
        self.completion = P.build_candidate(token['job'], self.owned)['completion']
        with self.assertRaisesRegex(ValueError, 'No live draft'): self.lease.accept(self.context, self.completion)
        self.assertTrue((token['job'] / 'candidate/scene.glb').is_file()); self.assertEqual(self.lease.phase, 'stopped'); self.assert_source()

    def test_old_receipt_cannot_replace_new_generation(self):
        old, _ = self.build(); new = self.lease.begin(self.source, [self.first], self.context)
        (new['job'] / 'preview-receipt.json').write_bytes((old['job'] / 'preview-receipt.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'completion'): self.lease.accept(self.context, self.completion)
        self.assertEqual(self.lease.phase, 'stopped'); self.assertIsNone(self.lease.pending); self.assert_source()

    def test_actor_root_frame_revision_shape_and_binding_context_changes_refuse(self):
        for key in self.context:
            with self.subTest(field=key):
                self.build(); changed = dict(self.context, **{key: self.context[key] + 'changed'})
                with self.assertRaisesRegex(ValueError, 'actor/draft/source changed'): self.lease.accept(changed, self.completion)
                self.assertEqual(self.lease.phase, 'stopped')
        self.assert_source()

    def test_exact_request_bytes_not_only_equivalent_json_are_bound(self):
        token = self.lease.begin(self.source, [self.first], self.context)
        path = token['job'] / 'request.json'; path.write_bytes(path.read_bytes() + b' ')
        self.completion = P.build_candidate(token['job'], self.owned)['completion']
        with self.assertRaisesRegex(ValueError, 'completion'): self.lease.accept(self.context, self.completion)
        self.assert_source()

    def test_source_mtime_only_change_after_worker_is_refused(self):
        self.build(); value = self.source.stat()
        os.utime(self.source, ns=(value.st_atime_ns, value.st_mtime_ns + 1_000_000))
        with self.assertRaisesRegex(ValueError, 'actor/draft/source changed'): self.lease.accept(self.context, self.completion)

    def test_stale_source_before_worker_never_publishes(self):
        token = self.lease.begin(self.source, [self.first], self.context)
        self.source.write_bytes(self.source.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'before preparation'): P.build_candidate(token['job'], self.owned)
        self.assertFalse((token['job'] / 'preview-receipt.json').exists()); self.assertFalse((token['job'] / 'candidate').exists())

    def test_candidate_or_binding_file_changes_after_publication_are_refused(self):
        for filename in ('candidate/scene.glb', 'bindings.json'):
            with self.subTest(file=filename):
                token, _ = self.build(); path = token['job'] / filename; path.write_bytes(path.read_bytes() + b'corrupt')
                with self.assertRaisesRegex(ValueError, 'changed after publication'): self.lease.accept(self.context, self.completion)
        self.assert_source()

    def test_changed_operation_mapping_and_traversal_receipts_refuse(self):
        for change in ('operations', 'path'):
            with self.subTest(change=change):
                token, _ = self.build([self.first, self.second], 'included-batch')
                path = token['job'] / 'preview-receipt.json'; data = json.loads(path.read_bytes())
                if change == 'operations': data['operations'].reverse()
                else: data['candidate']['path'] = '../authored-source.glb'
                path.write_bytes(P.encoded(data))
                with self.assertRaises(ValueError): self.lease.accept(self.context, self.completion)
        self.assert_source()

    def test_reports_are_matched_to_actual_candidate_chains_even_when_reordered(self):
        original = batch.build
        def reordered(*args, **kwargs):
            result = original(*args, **kwargs); result['reports'] = list(reversed(result['reports'])); return result
        with patch.object(batch, 'build', side_effect=reordered):
            token, receipt = self.build([self.first, self.second], 'included-batch')
        self.lease.accept(self.context, self.completion)
        candidate = H.GLB(token['job'] / 'candidate/scene.glb')
        for operation in receipt['operations']:
            report = candidate.doc['nodes'][operation['candidate_helper_nodes'][0]]['extras']['has_generated_helper']['authoring']
            self.assertEqual(report['region']['component'], operation['source_regions'][0][2])
            self.assertEqual(P.digest(P.encoded(report)), operation['report_sha256'])
        self.assert_source()

    def test_worker_report_with_foreign_helper_nodes_is_refused_before_receipt(self):
        original = batch.build
        def misassociated(*args, **kwargs):
            result = original(*args, **kwargs); result['reports'] = copy.deepcopy(result['reports'])
            result['reports'][0]['helper_nodes'] = result['reports'][1]['helper_nodes']; return result
        token = self.lease.begin(self.source, [self.first, self.second], self.context, 'included-batch')
        with patch.object(batch, 'build', side_effect=misassociated), self.assertRaisesRegex(ValueError, 'uniquely match'):
            P.build_candidate(token['job'], self.owned)
        self.assertFalse((token['job'] / 'preview-receipt.json').exists()); self.assert_source()

    def test_receipt_reports_membership_and_boolean_generation_mutations_are_refused(self):
        for field in ('reports', 'setup_members_built', 'generation'):
            with self.subTest(field=field):
                token, _ = self.build(); path = token['job'] / 'preview-receipt.json'; value = json.loads(path.read_bytes())
                value[field] = [] if field == 'reports' else True if field == 'generation' else 99
                path.write_bytes(P.encoded(value))
                with self.assertRaisesRegex(ValueError, 'receipt changed'): self.lease.accept(self.context, self.completion)
        self.assert_source()

    def test_coordinated_file_edits_cannot_replace_trusted_completion_digest(self):
        token, _ = self.build(); candidate_path = token['job'] / 'candidate/scene.glb'
        candidate_path.write_bytes(candidate_path.read_bytes() + b'coordinated change')
        proof_path = token['job'] / 'bindings.json'; proof = json.loads(proof_path.read_bytes())
        proof['candidate_sha256'] = P.identity(candidate_path)['sha256']; proof_path.write_bytes(P.encoded(proof))
        path = token['job'] / 'preview-receipt.json'; value = json.loads(path.read_bytes())
        value['candidate']['identity'] = P.identity(candidate_path); value['bindings']['sha256'] = P.digest(proof_path.read_bytes())
        path.write_bytes(P.encoded(value))
        with self.assertRaisesRegex(ValueError, 'receipt changed'): self.lease.accept(self.context, self.completion)
        self.assert_source()

    def test_unreviewed_different_shapes_and_apply_purpose_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'reviewed'):
            self.lease.begin(self.source, [dict(self.first, reviewed=False)], self.context)
        with self.assertRaisesRegex(ValueError, 'different shape'):
            self.lease.begin(self.source, [self.first, dict(self.second, source_morph_defaults=True)], self.context, 'included-batch')
        token = self.lease.begin(self.source, [self.first], self.context)
        path = token['job'] / 'request.json'; value = json.loads(path.read_bytes()); value['purpose'] = 'apply'; path.write_bytes(P.encoded(value))
        with self.assertRaisesRegex(ValueError, 'preview-only'): P.build_candidate(token['job'], self.owned)
        self.assertFalse((token['job'] / 'candidate').exists()); self.assert_source()

    def test_real_second_builder_failure_publishes_no_partial_candidate(self):
        token = self.lease.begin(self.source, [self.first, self.second], self.context, 'included-batch')
        original = H.build; calls = []
        def fail_later(*args, **kwargs):
            calls.append(args)
            if len(calls) == 2: raise ValueError('CPU controlled second builder failure')
            return original(*args, **kwargs)
        with patch.object(H, 'build', side_effect=fail_later), self.assertRaisesRegex(ValueError, 'second builder'):
            P.build_candidate(token['job'], self.owned)
        self.assertEqual(len(calls), 2); self.assertFalse((token['job'] / 'preview-receipt.json').exists())
        self.assertFalse((token['job'] / 'candidate').exists()); self.assert_source()

    def test_retained_transform_and_skin_reordering_are_refused(self):
        token, _ = self.build(); candidate = H.GLB(token['job'] / 'candidate/scene.glb')
        candidate.doc['nodes'][2]['translation'][0] += 1
        with self.assertRaisesRegex(ValueError, 'base transform'): P.retained_bindings(self.glb, candidate)
        candidate = H.GLB(token['job'] / 'candidate/scene.glb'); candidate.doc['skins'][0]['joints'][:2] = list(reversed(candidate.doc['skins'][0]['joints'][:2]))
        with self.assertRaisesRegex(ValueError, 'reordered'): P.retained_bindings(self.glb, candidate)
        self.assert_source()

    def test_imported_binding_predicate_uses_source_nodes_and_rejects_alias_or_rest_change(self):
        base = list(H.IDENTITY)
        source = {'2': {'kind': 'bone', 'id': 'Original::Head', 'base': base}, '7': {'kind': 'offset', 'id': 'Original::Head', 'base': base}}
        target = {'7': {'kind': 'offset', 'id': 'Derived::Head', 'base': base}, '2': {'kind': 'bone', 'id': 'Derived::Head', 'base': base}}
        self.assertEqual(set(P.imported_binding_map(source, target)), {'2', '7'})
        target['2']['base'] = [*base[:-1], 2]
        with self.assertRaisesRegex(ValueError, 'base transform'): P.imported_binding_map(source, target)
        target['2']['base'] = base; source['3'] = dict(source['2'], id='Original::Other'); target['3'] = dict(target['2'])
        with self.assertRaisesRegex(ValueError, 'alias'): P.imported_binding_map(source, target)

    def test_reused_job_and_boundary_escape_are_refused(self):
        token, _ = self.build()
        with self.assertRaisesRegex(ValueError, 'already been used'): P.build_candidate(token['job'], self.owned)
        with self.assertRaisesRegex(ValueError, 'owned boundary'): P.build_candidate(self.root, self.owned)
        with self.assertRaisesRegex(ValueError, 'owned boundary'): P.owned(self.owned / '..' / 'elsewhere', self.owned)
        self.assert_source()


if __name__ == '__main__':
    stream = io.StringIO(); suite = unittest.defaultTestLoader.loadTestsFromTestCase(PreviewProtocol)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {'format': 'has_wind_helper_draft_protocol_cpu_1', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'passed': result.wasSuccessful(), 'folder': str(RUN),
              'actual_existing_builder_used_in_process': True, 'fixtures': 'tiny self-authored two-panel GLBs only',
              'godot_started': False, 'gpu_used': False, 'external_worker_started': False,
              'native_models_used': False, 'main_or_prototype_source_modified': False,
              'scope': 'CPU candidate protocol/lifecycle only; not a main-view or imported-Godot-binding acceptance result'}
    (OUT / 'cpu-tests.log').write_text(stream.getvalue(), encoding='utf-8')
    (OUT / 'cpu-tests.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(stream.getvalue()); print(json.dumps(report, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
