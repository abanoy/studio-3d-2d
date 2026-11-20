"""Exact existing-joint derivative proof; all GLBs are synthetic owned fixtures."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_secondary_existing_joints import existing_fixture
from test_secondary_helpers import H, fixture, request, write_glb
import import_basis_helper as B
import secondary_helpers_batch as batch
import wind_helper_preview as preview


class BasisHelperPreservation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.glb'
        self.original = existing_fixture(self.source)
        self.request = {'source_sha256': self.original.sha, 'reviewed': True,
                        'node': 3, 'primitive': 1, 'component': 0, 'anchor_node': 4,
                        'segments': 3, 'use_existing_joints': True}
        self.result = H.build(self.source, self.root / 'derived', self.request)
        self.candidate = Path(self.result['glb'])

    def tearDown(self):
        self.temp.cleanup()

    def proof(self):
        return B.check_existing_derivative(self.source, self.candidate, self.original.sha,
                                           hashlib.sha256(self.candidate.read_bytes()).hexdigest())

    def mutate(self, change):
        value = H.GLB(self.candidate)
        change(value)
        write_glb(self.candidate, value.doc, bytes(value.binary))

    def test_existing_joints_preserve_exact_reference_without_remeasurement(self):
        before = self.source.read_bytes()
        stamp = self.source.stat().st_mtime_ns
        proof = self.proof()
        payload = json.loads(proof['payload'])
        self.assertEqual(proof['format'], B.FORMAT)
        self.assertEqual(hashlib.sha256(proof['payload'].encode()).hexdigest(), proof['preservation_sha256'])
        self.assertEqual(payload['method'], B.METHOD)
        self.assertTrue(payload['geometry_root_rest_skin_morph_preserved'])
        self.assertTrue(payload['exact_binary_preserved'])
        self.assertEqual(payload['original_nodes'], len(self.original.doc['nodes']))
        self.assertEqual(payload['appended_unweighted_endpoints'], 1)
        self.assertEqual(payload['candidate_springs'], payload['original_springs'] + 1)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.source.stat().st_mtime_ns, stamp)
        self.assertNotIn('height', payload)  # No posed or inferred stature value.

    def test_existing_container_and_nonzero_morph_defaults_are_preserved(self):
        doc = copy.deepcopy(self.original.doc)
        doc['nodes'][0]['translation'] = [2., 3., 4.]
        doc['nodes'][0]['scale'] = [2., 2., 2.]
        doc['meshes'][0]['weights'] = [.25]
        doc['extras'] = {'kept': '日本語', 'has_secondary_helpers_1': {
            'specVersion': '1.0', 'springs': [{'name': 'OriginalRoot', 'joints': [{'node': 1}]}]}}
        source = self.root / 'with-original.glb'
        write_glb(source, doc, bytes(self.original.binary))
        original = H.GLB(source)
        plan = dict(self.request, source_sha256=original.sha)
        derived = H.build(source, self.root / 'with-original-derived', plan)
        proof = B.check_existing_derivative(source, derived['glb'], original.sha, H.GLB(derived['glb']).sha)
        payload = json.loads(proof['payload'])
        self.assertEqual(payload['original_springs'], 1)
        self.assertEqual(payload['candidate_springs'], 2)

    def test_batch_uses_common_original_to_final_proof(self):
        result = batch.build(self.source, self.root / 'batch', {
            'format': batch.FORMAT, 'source_sha256': self.original.sha,
            'reviewed': True, 'items': [copy.deepcopy(self.request), copy.deepcopy(self.request)]})
        proof = B.check_existing_derivative(self.source, result['glb'], self.original.sha,
                                            result['batch']['final_sha256'])
        self.assertEqual(proof['parent_sha256'], self.original.sha)
        self.assertEqual(json.loads(proof['payload'])['appended_unweighted_endpoints'], 1)

    def test_actual_weighted_derivative_is_refused_without_changing_legacy_builder(self):
        source = self.root / 'weighted.glb'
        original = fixture(source)
        value = H.build(source, self.root / 'weighted-derived', request(original))
        self.assertTrue(Path(value['glb']).is_file())
        with self.assertRaisesRegex(ValueError, 'weighted joints'):
            B.check_existing_derivative(source, value['glb'], original.sha, H.GLB(value['glb']).sha)

    def test_tampered_binary_geometry_or_morph_data_refuses(self):
        self.mutate(lambda value: value.binary.__setitem__(0, value.binary[0] ^ 1))
        with self.assertRaisesRegex(ValueError, 'weighted joints'):
            self.proof()

    def test_root_rest_parent_and_original_node_metadata_changes_refuse(self):
        raw = self.candidate.read_bytes()
        changes = [lambda value: value.doc['nodes'][0].update(translation=[0, .01, 0]),
                   lambda value: value.doc['nodes'][5].update(rotation=[0, .1, 0, .99]),
                   lambda value: value.doc['nodes'][0].update(extras={'unrelated': True}),
                   lambda value: value.doc['nodes'][4].update(children=[6])]
        for change in changes:
            with self.subTest(change=change):
                self.candidate.write_bytes(raw)
                self.mutate(change)
                with self.assertRaises(ValueError):
                    self.proof()

    def test_mesh_skin_morph_scene_material_changes_refuse(self):
        raw = self.candidate.read_bytes()
        changes = [lambda value: value.doc['meshes'][0].update(weights=[.5]),
                   lambda value: value.doc['skins'][0]['joints'].reverse(),
                   lambda value: value.doc['materials'][0].update(doubleSided=False),
                   lambda value: value.doc['scenes'][0].update(nodes=[1]),
                   lambda value: value.doc['meshes'][0]['primitives'][0]['targets'].clear()]
        for change in changes:
            with self.subTest(change=change):
                self.candidate.write_bytes(raw)
                self.mutate(change)
                with self.assertRaisesRegex(ValueError, 'geometry/skin/morph/material'):
                    self.proof()

    def test_new_endpoint_must_be_unweighted_leaf_with_one_original_parent(self):
        raw = self.candidate.read_bytes()
        changes = [lambda value: value.doc['nodes'][-1].update(mesh=0),
                   lambda value: value.doc['nodes'][-1].update(scale=[1, 1, 1]),
                   lambda value: value.doc['nodes'][-1].update(children=[0]),
                   lambda value: value.doc['nodes'][1].setdefault('children', []).append(len(value.doc['nodes']) - 1)]
        for change in changes:
            with self.subTest(change=change):
                self.candidate.write_bytes(raw)
                self.mutate(change)
                with self.assertRaises(ValueError):
                    self.proof()

    def test_additive_declaration_must_match_exact_endpoint_and_fixed_controls(self):
        raw = self.candidate.read_bytes()
        for field, value in [('stiffness', 2.), ('dragForce', True), ('node', 0)]:
            with self.subTest(field=field):
                self.candidate.write_bytes(raw)
                self.mutate(lambda g: g.doc['extras']['has_secondary_helpers_1']['springs'][-1]['joints'][-1].update({field: value}))
                with self.assertRaises(ValueError):
                    self.proof()

    def test_caller_identity_and_no_op_derivative_refuse(self):
        current = H.GLB(self.candidate).sha
        for parent, target in [('0' * 64, current), (self.original.sha, '0' * 64),
                               (self.original.sha, self.original.sha), (True, current)]:
            with self.subTest(parent=parent, target=target):
                with self.assertRaises(ValueError):
                    B.check_existing_derivative(self.source, self.candidate, parent, target)

    def test_combined_native_and_generated_spring_budget_is_retained(self):
        self.mutate(lambda value: value.doc.setdefault('extensions', {}).update(
            {'VRMC_springBone': {'springs': [{'name': str(i), 'joints': []} for i in range(128)]}}))
        with self.assertRaisesRegex(ValueError, 'excessive existing spring'):
            self.proof()

    def test_actual_worker_basis_check_returns_independent_proof_and_refuses_bad_identity(self):
        worker = Path(__file__).resolve().parents[1] / 'tools/secondary_helper_worker.py'
        for index, source_sha in enumerate((self.original.sha, '0' * 64)):
            folder = self.root / ('worker-' + str(index))
            folder.mkdir()
            (folder / 'request.json').write_text(json.dumps({
                'source_sha256': source_sha, 'candidate_sha256': H.GLB(self.candidate).sha,
                'candidate': str(self.candidate)}), encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(worker), str(self.source),
                                     'basis_check', str(folder)], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads((folder / 'result.json').read_bytes())
            self.assertIs(value['ok'], index == 0)
            if index == 0:
                self.assertEqual(value['value'], self.proof())
            else:
                self.assertIn('identity differs', value['error'])

    def test_preview_receipt_binds_and_revalidates_the_same_reference_proof(self):
        owned = self.root / 'preview-owned'
        owned.mkdir()
        job = owned / 'job'
        job.mkdir()
        context = {'actor_id': 'actor', 'root_instance_id': '1', 'revision': '1', 'frame': '0',
                   'authored_sha256': 'a' * 64, 'shape_sha256': 'b' * 64, 'bindings_sha256': 'c' * 64}
        envelope = preview.make_envelope(self.source, [self.request], context, 1)
        (job / 'request.json').write_bytes(preview.encoded(envelope))
        result = preview.build_candidate(job, owned)
        receipt = preview.check_receipt(job, owned, preview.digest((job / 'request.json').read_bytes()),
                                        context, result['completion']['receipt_sha256'])
        proof = receipt['basis_preservation']
        self.assertEqual(proof, B.check_existing_derivative(self.source, job / 'candidate/scene.glb',
                                                          self.original.sha, receipt['candidate']['identity']['sha256']))
        # Even a newly trusted receipt hash cannot authenticate a forged geometry proof.
        tampered = copy.deepcopy(receipt)
        tampered['basis_preservation']['preservation_sha256'] = '0' * 64
        (job / 'preview-receipt.json').write_bytes(preview.encoded(tampered))
        with self.assertRaisesRegex(ValueError, 'preservation proof changed'):
            preview.check_receipt(job, owned, preview.digest((job / 'request.json').read_bytes()), context,
                                  preview.digest((job / 'preview-receipt.json').read_bytes()))


if __name__ == '__main__':
    unittest.main()
