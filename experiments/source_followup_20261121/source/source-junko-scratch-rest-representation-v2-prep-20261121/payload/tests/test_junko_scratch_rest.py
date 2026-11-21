"""Synthetic input/schedule/arithmetic controls only. No Blender or SDK."""
from pathlib import Path
import json
import sys
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import junko_scratch_rest as S


def identity():
    return [float(r==c) for r in range(4) for c in range(4)]


class ScratchControls(unittest.TestCase):
    def test_schedule_has22_unique_cases(self):
        self.assertEqual(len(S.schedule()),22);self.assertEqual(len(set(S.schedule())),22)

    def test_schedule_preserves_baseline_and_lengths(self):
        self.assertEqual(S.schedule()[0],('original_baseline',None))
        self.assertEqual([x[1] for x in S.schedule()[1:8]],list(S.LENGTHS))

    def test_finite_matrix_accepts_identity(self):
        self.assertEqual(S.finite_matrix(identity()),tuple(identity()))

    def test_bool_matrix_refused(self):
        value=identity();value[0]=True
        with self.assertRaisesRegex(ValueError,'EXACT_FINITE_MATRIX'):S.finite_matrix(value)

    def test_nonfinite_matrix_refused(self):
        value=identity();value[0]=float('nan')
        with self.assertRaisesRegex(ValueError,'EXACT_FINITE_MATRIX'):S.finite_matrix(value)

    def test_wrong_private_sha_refused(self):
        with self.assertRaisesRegex(ValueError,'EXACT_PRIVATE_FACTORY_CAPTURE'):S.profile(b'{}')

    def test_wrong_native_index_refused_after_mocked_hash(self):
        value={'format':'has_private_first_native_rest_refusal_1','private_do_not_publish':True,
               'native_mdl_sha256':S.BODY_SHA,'native_index':37}
        with mock.patch.object(S,'sha',return_value=S.PRIVATE_SHA):
            with self.assertRaisesRegex(ValueError,'EXACT_NATIVE38_CAPTURE'):S.profile(json.dumps(value).encode())

    def test_close_source_pin_refused(self):
        with self.assertRaisesRegex(ValueError,'PINNED_REFERENCE_CLOSE_SOURCE'):S.load_close(b'', 'wrong')

    def test_missing_close_refused(self):
        raw=b'x=1\n'
        with self.assertRaisesRegex(ValueError,'ONE_REFERENCE_CLOSE'):S.load_close(raw,S.sha(raw))

    def test_pinned_close_ast_excludes_other_statements(self):
        raw=b'raise RuntimeError("must not run")\ndef close(a,b):\n return a==b\n'
        close=S.load_close(raw,S.sha(raw));self.assertTrue(close([1.],[1.]))

    def test_measured_row_uses_original_close(self):
        close=lambda a,b:tuple(a)==tuple(b)
        row=S.measured_row('synthetic',1.,identity(),identity(),identity(),identity(),close)
        self.assertTrue(row['original_close_rest_native']);self.assertEqual(row['rest_to_native_reference_error'],0.)

    def test_failed_representation_stays_failed(self):
        rest=identity();rest[0]+=.01
        row=S.measured_row('synthetic',1.,identity(),rest,identity(),identity(),lambda a,b:tuple(a)==tuple(b))
        self.assertFalse(row['original_close_rest_native']);self.assertGreater(row['rest_to_native_reference_error'],0.)


if __name__=='__main__':unittest.main(verbosity=2)
