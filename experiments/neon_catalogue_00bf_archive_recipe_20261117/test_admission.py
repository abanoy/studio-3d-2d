"""Frozen closed public metadata only; coherent negative mutations stay in RAM."""
from pathlib import Path
import hashlib
import json
import unittest
import archive_checks as gate

HERE = Path(__file__).resolve().parent
R = gate.ROOT_RUN


def get(raw, path): return gate.load(raw['REVIEW:' + path])
def put(raw, path, value): raw['REVIEW:' + path] = (json.dumps(value, allow_nan=False) + '\n').encode()


def change_case(raw, index, action):
    root = get(raw, R + 'verification.json'); row = root['rows'][index]; value = row['report']; action(value)
    label = row['label']; child = gate.relative(value['folder'], Admission.review) + '/'
    original = get(raw, child + 'result.json')
    # Preserve the wrapper's raw-result subset relation while changing predicates.
    for key in original:
        if key in value: original[key] = value[key]
    put(raw, child + 'result.json', original); put(raw, R + label + '-report.json', value); put(raw, R + 'verification.json', root)


class Admission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frozen = (HERE / 'INPUTS.json').read_bytes(); assert hashlib.sha256(frozen).hexdigest() == '1d4278e2655f11bd63a001cdfaa72baa2f1196959afdde61782e01a68fb5d927'
        spec = gate.load(frozen); cls.spec = spec; cls.review = spec['roots']['REVIEW']; cls.original = {}
        for row in spec['inputs']:
            data = (Path(spec['roots'][row['root']]) / row['path']).read_bytes()
            assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
            cls.original[row['root'] + ':' + row['path']] = data
    def setUp(self): self.raw = dict(self.original)
    def rejects(self):
        with self.assertRaises((ValueError, KeyError)): gate.check(self.raw, self.review)
    def child(self, index): return gate.relative(get(self.raw, R + 'verification.json')['rows'][index]['report']['folder'], self.review) + '/'

    def test_exact_closed69_corpus_is_admitted(self):
        self.assertTrue(gate.same(gate.check(self.raw, self.review), self.spec['expected_summary']))
    def test_false_root_or_full_pass_claim_refused(self):
        for key, value in [('passed', False), ('full_suite_pass_claimed', True)]:
            with self.subTest(key=key):
                self.setUp(); root = get(self.raw, R + 'verification.json'); root[key] = value; put(self.raw, R + 'verification.json', root); self.rejects()
    def test_source_after_change_refused(self):
        after = get(self.raw, R + 'source-after.json'); after['tests/verify_shape_catalog.py'] = '0' * 64; put(self.raw, R + 'source-after.json', after); self.rejects()
    def test_nonzero_recorded_scope_refused(self):
        path = R + 'height-after-closure.json'; value = get(self.raw, path); value['owned_count'] = 1; put(self.raw, path, value); self.rejects()
    def test_coherent_catalogue_check_count_change_refused(self):
        change_case(self.raw, 0, lambda value: value.update(checks=129)); self.rejects()
    def test_supplied_Mima_cannot_be_omitted_from_catalogue(self):
        change_case(self.raw, 0, lambda value: value['plans'].pop()); self.rejects()
    def test_headless_unit_marker_count_refused_without_private_job_invention(self):
        path = self.child(0) + 'shape_catalog_unit.log'; data = self.raw['REVIEW:' + path]; prefix = b'SHAPE_CATALOG_UNIT '
        lines = data.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if line.startswith(prefix): lines[index] = prefix + b'{"checks":33,"failures":0}\n'
        self.raw['REVIEW:' + path] = b''.join(lines); self.rejects()
    def test_comparison_native_count_not_waived(self):
        change_case(self.raw, 1, lambda value: value.update(native_models_tested=5)); self.rejects()
    def test_Mima_draft_recovery_not_omitted(self):
        child = self.child(1); change_case(self.raw, 1, lambda value: value.update(draft_recovery=None)); put(self.raw, child + 'draft-reader.json', None); self.rejects()
    def test_actual_raw_VRM_nine_checks_not_omitted(self):
        change_case(self.raw, 2, lambda value: value.update(native_import=None)); self.rejects()
    def test_private_foreground_or_unclosed_job_refused(self):
        root = get(self.raw, R + 'verification.json'); path = gate.relative(root['rows'][0]['report']['private_receipts'][0], self.review)
        for key, value in [('foreground_child_observed', True), ('job_closed', False)]:
            with self.subTest(key=key):
                self.setUp(); receipt = get(self.raw, path); receipt[key] = value; put(self.raw, path, receipt); self.rejects()
    def test_duplicate_physical_receipt_not_counted_twice(self):
        change_case(self.raw, 2, lambda value: value['private_receipts'].__setitem__(2, value['private_receipts'][1])); self.rejects()
    def test_height_saved_receipt_argv_staleness_refused(self):
        path = self.child(2) + 'native-command.json'; command = get(self.raw, path); command['args'][command['args'].index('--receipt') + 1] += '.stale'; put(self.raw, path, command); self.rejects()
    def test_Mima_scalar_provenance_tamper_refused(self):
        key = 'MAIN:experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json'
        value = gate.load(self.raw[key]); value['scene']['sha256'] = '0' * 64; self.raw[key] = json.dumps(value).encode(); self.rejects()
    def test_typed_metadata_and_duplicate_JSON_refused(self):
        self.assertFalse(gate.same(True, 1)); self.assertFalse(gate.same(1, 1.0))
        with self.assertRaises(ValueError): gate.load(b'{"a":1,"a":1}')


if __name__ == '__main__': unittest.main(verbosity=2)
