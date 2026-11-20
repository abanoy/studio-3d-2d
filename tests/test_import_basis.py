"""Deterministic six-foot basis and derivative-chain contracts; synthetic only."""
from copy import deepcopy
from decimal import localcontext, ROUND_DOWN, Inexact
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import import_basis as B

A, Z, P = (hashlib.sha256(x).hexdigest() for x in (b'raw', b'derived', b'preservation'))


def model(height='2'):
    return {'kind': 'model', 'sha256': A, 'scale': 1, 'metadata': {},
            'asset_basis': B.create_record(A, height)['record']}


def document(row=None):
    return {'schema_version': 4, 'world': {'format': 'studio_world_1', 'objects': [row] if row else []}}


class ImportBasisTests(unittest.TestCase):
    def test_ratio_is_exact_and_context_independent(self):
        for precision in (1, 7, 28, 99):
            with localcontext() as context:
                context.prec = precision
                context.rounding = ROUND_DOWN
                context.traps[Inexact] = True
                self.assertEqual(B.factor_for('2'), '0.9144')
                self.assertEqual(B.factor_for('3'), '0.6096')
                self.assertEqual(B.factor_for('7'), '0.26125714285714285714285714285714285714285714285714')

    def test_record_wrapper_and_canonical_height(self):
        self.assertEqual(B.create_record(A, '2')['record']['decision'], 'explicit_complete_human_override')
        for height in ('0', '2.0', '02', '2e0', '-2', 2, True, None):
            self.assertIn('error', B.create_record(A, height))
        self.assertIn('error', B.create_record('not a sha', '2'))

    def test_legacy_absence_does_not_reinterpret_old_fit(self):
        row = {'metadata': {'import_height': {'factor': '4', 'target_metres': '1.8288'}}}
        self.assertEqual(B.factor(row), 1)
        self.assertFalse(B.active(row))
        self.assertEqual(B.model_admission(row)['factor'], 1)

    def test_source_identity_and_measurement_tampering_refuse(self):
        for field, value in (('source_sha256', Z), ('factor', '0.9'), ('target_metres', '2'),
                             ('classification', 'partial'), ('decision', True)):
            row = model()
            row['asset_basis'][field] = value
            self.assertTrue(B.record_error(row), field)
        row = model()
        row['kind'] = 'environment'
        self.assertTrue(B.record_error(row))

    def test_active_capability_and_real_boolean_readiness(self):
        row = model()
        with self.assertRaises(B.BasisError):
            B.factor(row)
        self.assertEqual(B.factor(row, capability=True), Q(1143, 1250))
        for value in (0, 1, 'true', None):
            self.assertIn('error', B.model_admission(row, value, True))
            self.assertIn('error', B.model_admission(row, True, value))
        self.assertIn('error', B.model_admission(row, True, False))

    def test_source_replacement_cannot_forge_a_bare_basis(self):
        row = model()
        row['sha256'] = row['asset_basis']['source_sha256'] = Z
        self.assertIn('lineage', B.record_error(row))

    def test_authored_gd_lineage_parity_fixture(self):
        fixture = json.loads((Path(__file__).with_name('import_basis_lineage_parity.json')).read_text(encoding='utf-8'))
        self.assertEqual(fixture['format'], 'has_import_basis_lineage_parity_fixture_1')
        self.assertEqual(len(fixture['cases']), 16)
        for row in fixture['cases']:
            error = B.record_error(row['model'])
            self.assertEqual(not error, row['accepted'], row['name'])
            if row['accepted']:
                self.assertEqual(B.model_admission(row['model'])['factor_text'], row['factor_text'])

    def test_derivative_requires_actual_verified_flag(self):
        for value in (False, 0, 1, 'true', None):
            self.assertIn('error', B.authenticated_derivative(model(), Z, P, value))

    def test_derivative_preserves_measurement_and_original(self):
        original = model()
        frozen = deepcopy(original)
        out = B.authenticated_derivative(original, Z, P, True)['model']
        self.assertEqual(original, frozen)
        self.assertEqual(out['sha256'], Z)
        self.assertEqual(out['asset_basis']['source_sha256'], Z)
        self.assertEqual(out['asset_basis']['measured_from_sha256'], A)
        self.assertEqual(out['asset_basis']['factor'], frozen['asset_basis']['factor'])
        self.assertEqual(out['metadata']['import_basis_lineage']['steps'],
                         [{'parent_sha256': A, 'source_sha256': Z, 'preservation_sha256': P}])
        self.assertEqual(B.record_error(out), '')

    def test_discontinuity_cycles_fields_and_lineage_identity_refuse(self):
        valid = B.authenticated_derivative(model(), Z, P, True)['model']
        for field, value in (('parent_sha256', P), ('source_sha256', A),
                             ('preservation_sha256', 'x' * 64)):
            changed = deepcopy(valid)
            changed['metadata']['import_basis_lineage']['steps'][0][field] = value
            self.assertTrue(B.record_error(changed), field)
        for key, value in (('measured_from_sha256', P), ('source_sha256', P), ('extra', True)):
            changed = deepcopy(valid)
            changed['metadata']['import_basis_lineage'][key] = value
            self.assertTrue(B.record_error(changed), key)
        self.assertIn('error', B.authenticated_derivative(valid, A, P, True))

    def test_orphan_and_redundant_lineage_refuse(self):
        self.assertTrue(B.record_error({'metadata': {'import_basis_lineage': {}}}))
        row = model()
        row['metadata']['import_basis_lineage'] = {}
        self.assertTrue(B.record_error(row))

    def test_lineage_capacity_is_exact_and_continuous(self):
        row = model()
        for index in range(128):
            digest = hashlib.sha256(('step%d' % index).encode()).hexdigest()
            row = B.authenticated_derivative(row, digest, P, True)['model']
        self.assertEqual(len(row['metadata']['import_basis_lineage']['steps']), 128)
        self.assertEqual(B.record_error(row), '')
        self.assertIn('error', B.authenticated_derivative(row, Z, P, True))

    def test_same_hash_is_an_authenticated_noop(self):
        row = model()
        self.assertEqual(B.authenticated_derivative(row, A, P, True)['model'], row)

    def test_legacy_raw_root_identity_and_active_refusals(self):
        raw = ((-2, 1, 0, 4), (0, 3, 0, 5), (0, 0, 4, 6), (0, 0, 0, 1))
        self.assertEqual(B.configure_import_root(raw, {})['base_root'], raw)
        self.assertIn('error', B.configure_import_root(raw, model()))
        for raw in (((-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
                    ((1, 0, 0, 0), (0, 2, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))):
            self.assertIn('error', B.configure_import_root(raw, model()))

    def test_basis_order_and_artist_multiplier(self):
        raw = ((0, 0, 2, 1), (0, 2, 0, 2), (-2, 0, 0, 3), (0, 0, 0, 1))
        configured = B.ImportRoot.configured(raw, model(), capability=True)
        c = Q(1143, 1250)
        expected = ((0, 0, 2*c, c), (0, 2*c, 0, 2*c), (-2*c, 0, 0, 3*c), (0, 0, 0, 1))
        self.assertEqual(configured.effective_base(), expected)
        self.assertEqual(configured.raw_root, raw)
        for artist_scale in (Q(1, 2), Q(1), Q(2)):
            artist = tuple(tuple(artist_scale if i == j and i < 3 else int(i == j)
                                 for j in range(4)) for i in range(4))
            result = configured.evaluate(artist)
            self.assertEqual(result[1][1], 2*c*artist_scale)

    def test_scene_local_capability_and_transient_view(self):
        parent = document()
        parent.update(schema_version=6, sequence_graph={'assets': [{'scene': document(model())}]})
        encoded = B.encode_capability(parent)
        self.assertEqual(encoded['schema_version'], 9)
        self.assertEqual(encoded['sequence_graph']['assets'][0]['scene']['schema_version'], 9)
        frozen = deepcopy(encoded)
        view = B.legacy_validation_view(encoded)
        self.assertEqual(encoded, frozen)
        self.assertEqual(view['schema_version'], 6)
        self.assertEqual(view['sequence_graph']['assets'][0]['scene']['schema_version'], 4)
        self.assertIn('asset_basis', view['sequence_graph']['assets'][0]['scene']['world']['objects'][0])
        child = encoded['sequence_graph']['assets'][0]['scene']
        child['schema_version'] = child.pop('basis_content_schema_version')
        del child['import_basis_capability']
        with self.assertRaises(B.BasisError):
            B.inspect_capability(encoded)

    def test_old_empty_graph_is_not_newly_admitted(self):
        row = document()
        row.update(schema_version=6, sequence_graph={'assets': []})
        with self.assertRaises(B.BasisError):
            B.inspect_capability(row)

    def test_portable_facade_requires_matching_runtime_and_keeps_source(self):
        document_with_basis = B.encode_capability(document(model()))
        seen = []
        reader = lambda value: seen.append(deepcopy(value)) or ['unchanged-resource-result']
        with self.assertRaises(B.BasisError):
            B.members_with_capability(document_with_basis, reader)
        self.assertFalse(seen)
        self.assertEqual(B.members_with_capability(document_with_basis, reader, runtime_basis_ready=True),
                         ['unchanged-resource-result'])
        self.assertEqual(seen[0]['schema_version'], 4)
        self.assertEqual(document_with_basis['schema_version'], 9)


if __name__ == '__main__':
    unittest.main()
