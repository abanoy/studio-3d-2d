"""Read frozen closed scalar/source originals; mutate valid JSON in RAM only."""
from pathlib import Path
import copy
import hashlib
import json
import unittest
import archive_checks as gate

HERE = Path(__file__).resolve().parent
R = gate.ROOT_RUN
C = R + 'source-choices/'


def put(raw, path, value): raw['REVIEW:' + path] = (json.dumps(value, allow_nan=False) + '\n').encode()


def get(raw, path): return gate.load(raw['REVIEW:' + path])


def report(raw): return get(raw, R + 'verification.json')['rows'][0]['report']


def sync(raw, value):
    root = get(raw, R + 'verification.json'); root['rows'][0]['report'] = value
    put(raw, R + 'verification.json', root); put(raw, R + 'foundation-report.json', value); put(raw, C + 'verification.json', value)


class Admission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frozen = (HERE / 'INPUTS.json').read_bytes()
        assert hashlib.sha256(frozen).hexdigest() == 'd1f896070f114f78d72ede167d3056b3e22f0e81d8def63e80c07c2f1f27f2f6'
        spec = gate.load(frozen); cls.spec = spec; cls.original = {}
        for row in spec['inputs']:
            data = (Path(spec['roots'][row['root']]) / row['path']).read_bytes()
            assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
            cls.original[row['root'] + ':' + row['path']] = data
    def setUp(self): self.raw = dict(self.original)
    def rejects(self):
        with self.assertRaises((ValueError, KeyError)): gate.check(self.raw, self.spec['roots']['REVIEW'])

    def test_exact_closed77_input_corpus_admitted(self):
        self.assertTrue(gate.same(gate.check(self.raw, self.spec['roots']['REVIEW']), self.spec['expected_summary']))
    def test_root_false_result_refused(self):
        v = get(self.raw, R + 'verification.json'); v['passed'] = False; put(self.raw, R + 'verification.json', v); self.rejects()
    def test_source_after_mutation_refused(self):
        v = get(self.raw, R + 'source-after.json'); v['tests/source_bone_bindings_unit.gd'] = '0' * 64; put(self.raw, R + 'source-after.json', v); self.rejects()
    def test_coherent_root_timeout_refused(self):
        v = get(self.raw, R + 'verification.json'); v['rows'][0]['timed_out'] = True; put(self.raw, R + 'verification.json', v)
        p = get(self.raw, R + 'foundation-process.json'); p['timed_out'] = True; put(self.raw, R + 'foundation-process.json', p); self.rejects()
    def test_coherent_foundation_count_change_refused(self):
        v = report(self.raw); v['checks'] = 168; sync(self.raw, v); self.rejects()
    def test_separate_count_not_folded_or_waived(self):
        v = report(self.raw); v['separate_checks']['crosswalk_cpu'] = 76; sync(self.raw, v); self.rejects()
    def test_resource_skip_cannot_be_relabelled_pass(self):
        v = report(self.raw); v['reports']['resource_write']['passed'] = 7; v['reports']['resource_write']['skipped'] = 0; sync(self.raw, v); self.rejects()
    def test_coherent_headless_graphics_claim_refused(self):
        v = report(self.raw); v['reports']['bone_bindings_headless']['graphics'] = True
        put(self.raw, C + 'bindings-headless/verification.json', v['reports']['bone_bindings_headless']); sync(self.raw, v); self.rejects()
    def test_coherent_authored_golden_digest_tamper_refused(self):
        v = report(self.raw); entry = v['reports']['bone_bindings_headless']['reports']['bindings']; entry['result']['fixture_glb_sha256'] = '0' * 64
        put(self.raw, C + 'bindings-headless/bindings/verified.json', entry['result']); put(self.raw, C + 'bindings-headless/bindings/fixture/result.json', entry['result'])
        put(self.raw, C + 'bindings-headless/verification.json', v['reports']['bone_bindings_headless']); sync(self.raw, v); self.rejects()
    def test_coherent_physical_foreground_violation_refused(self):
        v = report(self.raw); ui = v['reports']['ui']; ui['receipt']['foreground_child_observed'] = True
        physical = gate.relative(ui['private_receipt'], self.spec['roots']['REVIEW']); put(self.raw, physical, ui['receipt']); put(self.raw, C + 'ui/verification.json', ui); sync(self.raw, v); self.rejects()
    def test_stale_saved_private_receipt_path_refused(self):
        v = get(self.raw, C + 'ui/command.json'); v[v.index('--receipt') + 1] += '.stale'; put(self.raw, C + 'ui/command.json', v); self.rejects()
    def test_headless_command_cannot_claim_private_graphics(self):
        p = C + 'bindings-headless/bindings/run-command.json'; v = get(self.raw, p); v.remove('--headless'); put(self.raw, p, v); self.rejects()
    def test_changed_headless_ordered_log_refused(self):
        self.raw['REVIEW:' + C + 'bindings-headless/bindings/run-console.log'] += b'changed\n'; self.rejects()
    def test_coherent_cancel_exit_not_fabricated(self):
        v = report(self.raw); ui = v['reports']['ui']; ui['result']['actual_metadata_children'][1]['exit'] = 0
        put(self.raw, C + 'ui/result.json', ui['result']); put(self.raw, C + 'ui/verification.json', ui); sync(self.raw, v); self.rejects()
    def test_recorded_nonzero_scope_refused(self):
        p = R + 'after-closure.json'; v = get(self.raw, p); v['owned_count'] = 1; put(self.raw, p, v); self.rejects()
    def test_duplicate_JSON_and_container_type_aliases_refused(self):
        with self.assertRaises(ValueError): gate.load(b'{"a":1,"a":1}')
        self.assertFalse(gate.same(True, 1)); self.assertFalse(gate.same(1, 1.0))


if __name__ == '__main__': unittest.main(verbosity=2)
