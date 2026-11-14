"""Authored file/race controls; no native models or conversion imports."""
from dataclasses import asdict, FrozenInstanceError, replace
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import source_mdl_snapshot as S


class ReadWrapper:
    def __init__(self, stream, action):
        self.stream, self.action = stream, action
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return self.stream.__exit__(*args)
    def fileno(self):
        return self.stream.fileno()
    def read(self, amount):
        return self.action(self.stream, amount)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="has-mdl-capture-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "authored.mdl"
        self.path.write_bytes(b"authored immutable native bytes\x00\x01")
        self.real_open = open

    def capture(self):
        return S.capture_selected_mdl(str(self.path))

    def test_stable_capture_uses_independent_hash_and_preserves_file(self):
        before = self.path.stat()
        raw = self.path.read_bytes()
        value = self.capture()
        self.assertIsInstance(value, S.MdlCapture)
        self.assertEqual(value.raw, raw)
        self.assertEqual(value.native_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(value.file.path, str(self.path))
        self.assertEqual((value.file.size, value.file.mtime_ns, value.file.device, value.file.inode),
            (before.st_size, before.st_mtime_ns, before.st_dev, before.st_ino))
        self.assertIsNone(S.recheck_selected_mdl(value))
        after = self.path.stat()
        self.assertEqual((before.st_size, before.st_mtime_ns, before.st_dev, before.st_ino),
            (after.st_size, after.st_mtime_ns, after.st_dev, after.st_ino))
        self.assertEqual(self.path.read_bytes(), raw)

    def test_capture_and_snapshot_are_immutable(self):
        value = self.capture()
        self.assertIs(type(value.raw), bytes)
        with self.assertRaises(FrozenInstanceError): value.raw = b"changed"
        with self.assertRaises(FrozenInstanceError): value.file.size = 0

    def test_exact_limit_is_admitted(self):
        with self.path.open("wb") as stream: stream.truncate(S.MAX_BYTES)
        value = self.capture()
        self.assertIsInstance(value, S.MdlCapture)
        self.assertEqual(len(value.raw), S.MAX_BYTES)

    def test_oversize_is_not_inspected_and_has_no_native_sha(self):
        with self.path.open("wb") as stream: stream.truncate(S.MAX_BYTES + 1)
        with patch("builtins.open", side_effect=AssertionError("must not open oversize")):
            value = self.capture()
        self.assertEqual(asdict(value), {"reason": "selected-mdl-exceeds-16-mib-capture-limit"})

    def test_directory_and_relative_path_are_not_inspected(self):
        for path in (self.temp.name, "relative.mdl"):
            with self.subTest(path=path):
                value = S.capture_selected_mdl(path)
                self.assertIsInstance(value, S.NotInspected)
                self.assertEqual(set(asdict(value)), {"reason"})
                self.assertLess(len(value.reason), 80)

    def test_initial_missing_is_not_inspected_without_fake_sha(self):
        value = S.capture_selected_mdl(str(self.path.with_name("missing.mdl")))
        self.assertEqual(asdict(value), {"reason": "initial-selected-mdl-unreadable"})

    def test_initial_open_permission_with_unchanged_identity_is_not_inspected(self):
        with patch("builtins.open", side_effect=PermissionError("authored denied")):
            value = self.capture()
        self.assertEqual(asdict(value), {"reason": "initial-selected-mdl-unreadable"})

    def test_open_failure_after_disappearance_is_integrity_error(self):
        def gone(*args, **kwargs):
            self.path.unlink()
            raise FileNotFoundError("authored disappearance")
        with patch("builtins.open", side_effect=gone):
            with self.assertRaises(S.SourceIdentityError): self.capture()

    def test_same_bytes_replacement_between_stat_and_open_is_integrity_error(self):
        before = self.path.stat()
        other = self.path.with_name("replacement.mdl")
        other.write_bytes(self.path.read_bytes())
        os.utime(other, ns=(before.st_atime_ns, before.st_mtime_ns))
        def changed(path, mode):
            os.replace(other, self.path)
            return self.real_open(path, mode)
        with patch("builtins.open", side_effect=changed):
            with self.assertRaises(S.SourceIdentityError): self.capture()

    def test_short_read_cannot_be_optional_fallback(self):
        def shortened(path, mode):
            return ReadWrapper(self.real_open(path, mode), lambda stream, amount: stream.read(amount)[:-1])
        with patch("builtins.open", side_effect=shortened):
            with self.assertRaises(S.SourceIdentityError): self.capture()

    def test_read_failure_is_integrity_error(self):
        def failed_read(stream, amount): raise OSError("authored I/O error")
        def failed(path, mode): return ReadWrapper(self.real_open(path, mode), failed_read)
        with patch("builtins.open", side_effect=failed):
            with self.assertRaises(S.SourceIdentityError): self.capture()

    def test_mutation_during_read_is_integrity_error(self):
        def changed_read(stream, amount):
            raw = stream.read(amount)
            with self.real_open(self.path, "ab") as changed: changed.write(b"additional")
            return raw
        with patch("builtins.open", side_effect=lambda path, mode: ReadWrapper(self.real_open(path, mode), changed_read)):
            with self.assertRaises(S.SourceIdentityError): self.capture()

    def test_postread_path_disappearance_is_integrity_error(self):
        actual = S._path_snapshot
        count = 0
        def path_snapshot(path):
            nonlocal count
            count += 1
            if count == 2: raise FileNotFoundError("controlled postread stat failure")
            return actual(path)
        with patch.object(S, "_path_snapshot", side_effect=path_snapshot):
            with self.assertRaises(S.SourceIdentityError): self.capture()

    def test_recheck_detects_changed_length(self):
        value = self.capture()
        self.path.write_bytes(value.raw + b"changed")
        with self.assertRaises(S.SourceIdentityError): S.recheck_selected_mdl(value)

    def test_recheck_rehashes_same_length_even_when_mtime_restored(self):
        value = self.capture()
        before = self.path.stat()
        self.path.write_bytes(b"X" + value.raw[1:])
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(S._path_snapshot(str(self.path)), value.file)
        with self.assertRaisesRegex(S.SourceIdentityError, "bytes changed"):
            S.recheck_selected_mdl(value)

    def test_recheck_detects_same_bytes_replacement_identity(self):
        value = self.capture()
        other = self.path.with_name("replacement.mdl")
        other.write_bytes(value.raw)
        os.utime(other, ns=(self.path.stat().st_atime_ns, value.file.mtime_ns))
        os.replace(other, self.path)
        with self.assertRaises(S.SourceIdentityError): S.recheck_selected_mdl(value)

    def test_recheck_never_falls_back_when_unreadable_or_short(self):
        value = self.capture()
        with patch("builtins.open", side_effect=PermissionError("authored denied")):
            with self.assertRaises(S.SourceIdentityError): S.recheck_selected_mdl(value)
        with patch("builtins.open", side_effect=lambda path, mode: ReadWrapper(self.real_open(path, mode), lambda stream, amount: stream.read(amount)[:-1])):
            with self.assertRaises(S.SourceIdentityError): S.recheck_selected_mdl(value)

    def test_invalid_capture_cannot_supply_a_hash_or_mutable_bytes(self):
        value = self.capture()
        for invalid in (S.NotInspected("unavailable"), replace(value, native_sha256="0" * 64),
            replace(value, raw=bytearray(value.raw)), replace(value, file=replace(value.file, size=S.MAX_BYTES + 1))):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises(S.SourceIdentityError): S.recheck_selected_mdl(invalid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
