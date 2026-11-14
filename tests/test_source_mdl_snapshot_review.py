"""Independent CPU-only review cases against authored temporary byte fixtures."""
from dataclasses import asdict, replace
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import source_mdl_snapshot as S


class Stream:
    def __init__(self, actual, *, on_read=None, close_error=False):
        self.actual = actual
        self.on_read = on_read
        self.close_error = close_error

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.actual.close()
        if self.close_error:
            raise OSError("authored close failure")

    def fileno(self):
        return self.actual.fileno()

    def read(self, amount):
        if self.on_read:
            return self.on_read(self.actual, amount)
        return self.actual.read(amount)


class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mdl-capture-review-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "authored.mdl"
        self.path.write_bytes(b"independent review bytes\x00\x01")
        self.real_open = open
        self.real_stat = os.stat

    def capture(self):
        return S.capture_selected_mdl(str(self.path))

    def test_initial_stat_permission_is_bounded_not_inspected(self):
        with patch.object(S.os, "stat", side_effect=PermissionError("authored stat denied")):
            with patch("builtins.open", side_effect=AssertionError("initial stat failure must not open")):
                result = self.capture()
        self.assertEqual(asdict(result), {"reason": "initial-selected-mdl-unreadable"})

    def test_open_permission_requires_second_identical_path_stat(self):
        with patch.object(S.os, "stat", wraps=self.real_stat) as observed:
            with patch("builtins.open", side_effect=PermissionError("authored open denied")):
                result = self.capture()
        self.assertIs(type(result), S.NotInspected)
        self.assertEqual(observed.call_count, 2)
        self.assertTrue(all(call.kwargs == {"follow_symlinks": False} for call in observed.call_args_list))

    def test_open_permission_followed_by_stat_permission_is_integrity_error(self):
        initial = self.real_stat(self.path, follow_symlinks=False)
        with patch.object(S.os, "stat", side_effect=[initial, PermissionError("later stat denied")]):
            with patch("builtins.open", side_effect=PermissionError("authored open denied")):
                with self.assertRaises(S.SourceIdentityError):
                    self.capture()

    def test_open_permission_with_real_changed_mtime_is_integrity_error(self):
        before = self.path.stat()

        def denied(*args, **kwargs):
            os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
            raise PermissionError("authored race and open denial")

        with patch("builtins.open", side_effect=denied):
            with self.assertRaises(S.SourceIdentityError):
                self.capture()

    def test_first_fstat_identity_mismatch_does_not_read(self):
        original_snapshot = S._snapshot
        calls = []

        def checked_snapshot(path, info):
            result = original_snapshot(path, info)
            calls.append(result)
            return replace(result, inode=result.inode + 1) if len(calls) == 2 else result

        def opened(path, mode):
            return Stream(self.real_open(path, mode), on_read=lambda *_: self.fail("must reject before read"))

        with patch.object(S, "_snapshot", side_effect=checked_snapshot):
            with patch("builtins.open", side_effect=opened):
                with self.assertRaisesRegex(S.SourceIdentityError, "between stat and open"):
                    self.capture()

    def test_real_mtime_change_after_read_is_integrity_error(self):
        before = self.path.stat()

        def changed(stream, amount):
            raw = stream.read(amount)
            os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
            return raw

        with patch("builtins.open", side_effect=lambda path, mode: Stream(self.real_open(path, mode), on_read=changed)):
            with self.assertRaisesRegex(S.SourceIdentityError, "during read"):
                self.capture()

    def test_close_failure_is_integrity_error(self):
        with patch("builtins.open", side_effect=lambda path, mode: Stream(self.real_open(path, mode), close_error=True)):
            with self.assertRaises(S.SourceIdentityError):
                self.capture()

    def test_read_limit_and_immutable_result(self):
        seen = []

        def observed(stream, amount):
            seen.append(amount)
            return stream.read(amount)

        with patch("builtins.open", side_effect=lambda path, mode: Stream(self.real_open(path, mode), on_read=observed)):
            result = self.capture()
        self.assertEqual(seen, [result.file.size + 1])
        self.assertIs(type(result.raw), bytes)
        self.assertLessEqual(len(result.raw), S.MAX_BYTES)

    def test_recheck_stat_and_read_errors_are_integrity_errors(self):
        capture = self.capture()
        with patch.object(S.os, "stat", side_effect=PermissionError("authored recheck stat denied")):
            with self.assertRaises(S.SourceIdentityError):
                S.recheck_selected_mdl(capture)

        def failed_read(*args):
            raise OSError("authored recheck read failure")

        with patch("builtins.open", side_effect=lambda path, mode: Stream(self.real_open(path, mode), on_read=failed_read)):
            with self.assertRaises(S.SourceIdentityError):
                S.recheck_selected_mdl(capture)


if __name__ == "__main__":
    unittest.main(verbosity=2)
