"""Pure diagnostic-delegation guards; no Blender, SDK, native file or child."""
from pathlib import Path
import contextlib
import io
import sys
import types
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import junko_part_rest_diagnostic as D


class DiagnosticGuards(unittest.TestCase):
    def fixture(self, code=D.ERROR):
        calls = []
        def require(condition, reason):
            calls.append((condition, reason))
            if not condition: raise ValueError(reason)
        C = types.SimpleNamespace(require=require)
        def prove(): C.require(False, code)
        C.prove_native_blender = prove
        return C, calls, require

    def test_unrelated_profile_unchanged(self):
        C, _, original = self.fixture()
        with D.capture(C, {'sha256':'0'*64}): self.assertIs(C.require, original)

    def test_success_predicate_delegates(self):
        C, calls, original = self.fixture()
        with D.capture(C, {'sha256':D.BODY_SHA}): C.require(True, 'native_check')
        self.assertEqual(calls, [(True,'native_check')]); self.assertIs(C.require, original)

    def test_other_failure_delegates_unchanged(self):
        C, calls, original = self.fixture('other_native_failure')
        with mock.patch.object(D, 'emit') as emit:
            with D.capture(C, {'sha256':D.BODY_SHA}):
                with self.assertRaisesRegex(ValueError, '^other_native_failure$'): C.prove_native_blender()
            emit.assert_not_called()
        self.assertEqual(calls, [(False,'other_native_failure')]); self.assertIs(C.require, original)

    def test_first_failure_observed_then_original_raised(self):
        C, calls, original = self.fixture()
        with mock.patch.object(D, 'emit') as emit:
            with D.capture(C, {'sha256':D.BODY_SHA}):
                with self.assertRaisesRegex(ValueError, '^'+D.ERROR+'$'): C.prove_native_blender()
            emit.assert_called_once()
        self.assertEqual(calls, [(False,D.ERROR)]); self.assertIs(C.require, original)

    def test_capture_error_does_not_replace_original(self):
        C, calls, original = self.fixture()
        with mock.patch.object(D, 'emit', side_effect=RuntimeError('synthetic capture failure')):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with D.capture(C, {'sha256':D.BODY_SHA}):
                    with self.assertRaisesRegex(ValueError, '^'+D.ERROR+'$'): C.prove_native_blender()
            self.assertIn('JUNKO_PART_REST_DIAGNOSTIC_CAPTURE_FAILED', output.getvalue())
            self.assertNotIn('synthetic capture failure', output.getvalue())
        self.assertEqual(calls, [(False,D.ERROR)]); self.assertIs(C.require, original)

    def test_capture_only_once_but_every_refusal_preserved(self):
        C, calls, original = self.fixture()
        with mock.patch.object(D, 'emit') as emit:
            with D.capture(C, {'sha256':D.BODY_SHA}):
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError, '^'+D.ERROR+'$'): C.prove_native_blender()
            emit.assert_called_once()
        self.assertEqual(calls, [(False,D.ERROR),(False,D.ERROR)]); self.assertIs(C.require, original)

    def test_wrong_callsite_preserves_refusal_without_capture(self):
        C, calls, original = self.fixture()
        with mock.patch.object(D, 'emit') as emit:
            with D.capture(C, {'sha256':D.BODY_SHA}):
                with self.assertRaisesRegex(ValueError, '^'+D.ERROR+'$'): C.require(False,D.ERROR)
            emit.assert_not_called()
        self.assertEqual(calls, [(False,D.ERROR)]); self.assertIs(C.require, original)

    def test_restore_after_unrelated_exception(self):
        C, _, original = self.fixture()
        with self.assertRaisesRegex(RuntimeError, '^unrelated$'):
            with D.capture(C, {'sha256':D.BODY_SHA}): raise RuntimeError('unrelated')
        self.assertIs(C.require, original)

    def test_scalar_component_errors(self):
        a = [0.]*16; b = [0.]*16; b[3] = 3.; b[0] = .5
        self.assertEqual(D.maximum(a,b),3.)
        self.assertEqual(D.maximum(a,b,(0,1,2,4,5,6,8,9,10)),.5)
        self.assertEqual(D.normalized(a,b),1.)


if __name__ == '__main__': unittest.main(verbosity=2)
