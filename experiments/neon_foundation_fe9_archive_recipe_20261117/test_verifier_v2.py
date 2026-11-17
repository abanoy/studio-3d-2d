"""Artifact-only coherent constituent negatives; no original files/native IO."""
from pathlib import Path, PureWindowsPath
import gzip
import hashlib
import json
import unittest
import verify_packet_v2 as verifier

HERE = Path(__file__).resolve().parent
R = 'output/neon-foundation-fe9aace-20261117-attempt1/'
C = R + 'source-choices/'


def put(raw, path, value): raw['REVIEW:' + path] = (json.dumps(value, allow_nan=False) + '\n').encode()


class VerifierV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = verifier.PACKET; index_raw = (folder / 'INDEX.json').read_bytes()
        assert hashlib.sha256(index_raw).hexdigest() == '7679403431be50d5a84197bda8c027a78b770e0b7404cac62246d03d4743fc31'
        index = json.loads(index_raw); decoded = {}
        for row in index['objects']:
            packed = (folder / row['path']).read_bytes(); assert hashlib.sha256(packed).hexdigest() == row['sha256']
            data = gzip.decompress(packed); assert len(data) == row['decoded_bytes'] and hashlib.sha256(data).hexdigest() == row['decoded_sha256']; decoded[row['decoded_sha256']] = data
        bindings = json.loads((folder / 'BINDINGS.json').read_bytes()); cls.review = bindings['roots']['REVIEW']
        cls.original = {row['root'] + ':' + row['path']: decoded[row['sha256']] for row in bindings['bindings']}
    def setUp(self):
        self.raw = dict(self.original); self.parts = verifier.parse(self.raw['REVIEW:' + C + 'verification.json'])['reports']
    def check(self): verifier.verify_constituents(self.raw, self.review, C, self.parts)
    def rejects(self):
        with self.assertRaises(ValueError): self.check()
    def sync_cpu(self, label):
        line = next(line for line in self.raw['REVIEW:' + C + label + '.log'].splitlines() if line.startswith(b'{'))
        location = verifier.parse(line)['folder' if label == 'catalogue' else 'run']
        relative = PureWindowsPath(location).relative_to(PureWindowsPath(self.review)).as_posix()
        put(self.raw, relative + '/result.json', self.parts[label])
    def sync_ui(self):
        put(self.raw, C + 'ui/verification.json', self.parts['ui']); put(self.raw, C + 'ui/result.json', self.parts['ui']['result'])

    def test_unchanged_artifact_constituents_and_full_v2_verification_pass(self):
        self.check(); self.assertTrue(verifier.verify()['passed'])
    def test_exact_nine_membership_cannot_waive_or_add_constituents(self):
        for operation in ('remove', 'add'):
            with self.subTest(operation=operation):
                self.setUp()
                if operation == 'remove': self.parts.pop('appearance')
                else: self.parts['unqualified_extra'] = {}
                self.rejects()
    def test_coherent_CPU_failed_error_or_source_flags_refused(self):
        for label in ('catalogue', 'appearance'):
            for field, value in [('passed', False), ('failures', 1), ('errors', 1), ('source_preserved', False), ('tests', float(53 if label == 'catalogue' else 29))]:
                with self.subTest(label=label, field=field):
                    self.setUp(); self.parts[label][field] = value; self.sync_cpu(label); self.rejects()
    def test_direct_raw_CPU_result_join_refuses_inconsistent_copy(self):
        for label in ('catalogue', 'appearance'):
            with self.subTest(label=label):
                self.setUp(); self.sync_cpu(label)
                line = next(line for line in self.raw['REVIEW:' + C + label + '.log'].splitlines() if line.startswith(b'{'))
                where = verifier.parse(line)['folder' if label == 'catalogue' else 'run']; relative = PureWindowsPath(where).relative_to(PureWindowsPath(self.review)).as_posix()
                altered = dict(self.parts[label]); altered['unbound_extra'] = True; put(self.raw, relative + '/result.json', altered); self.rejects()
    def test_authored_catalogue_cannot_claim_native_model_run(self):
        for field, value in [('actual_native_inputs_read', True), ('actual_models_tested', 1)]:
            with self.subTest(field=field):
                self.setUp(); self.parts['catalogue'][field] = value; self.sync_cpu('catalogue'); self.rejects()
    def test_coherent_unit_failure_graphics_or_native_flags_refused(self):
        for field, value in [('failures', 1), ('headless', False), ('graphics', True), ('native_conversion', True)]:
            with self.subTest(field=field):
                self.setUp(); self.parts['unit'][field] = value; put(self.raw, C + 'unit/result.json', self.parts['unit']); self.rejects()
    def test_coherent_UI_result_failure_nonapp_or_native_flags_refused(self):
        for field, value in [('failures', 1), ('actual_app', False), ('native_conversion', True)]:
            with self.subTest(field=field):
                self.setUp(); self.parts['ui']['result'][field] = value; self.sync_ui(); self.rejects()
    def test_coherent_UI_preservation_flags_refused(self):
        for field in ('source_unchanged', 'originals_unchanged'):
            with self.subTest(field=field):
                self.setUp(); self.parts['ui'][field] = False; self.sync_ui(); self.rejects()


if __name__ == '__main__': unittest.main(verbosity=2)
