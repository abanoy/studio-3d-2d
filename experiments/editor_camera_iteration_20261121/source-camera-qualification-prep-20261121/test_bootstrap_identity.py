"""Focused CPU bootstrap identity guards; synthetic bytes/stat objects only.
Authored unrun. Imports definitions without calling the qualification main.
"""
from pathlib import Path
import hashlib
import importlib.util
import stat
import sys
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
DRIVER = Path(__file__).with_name('run_camera_qualification.py')
spec = importlib.util.spec_from_file_location('_ui_qualification_guard_subject', DRIVER)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
GOOD = b'VALUE = 7\n'
PIN = hashlib.sha256(GOOD).hexdigest()


class FakeParent:
    def __init__(self, *, mode=stat.S_IFDIR|0o755, attributes=0):
        self.mode = mode
        self.attributes = attributes

    def lstat(self):
        return SimpleNamespace(st_mode=self.mode, st_file_attributes=self.attributes)


class FakeInput:
    def __init__(self, *, before=None, after=None, raw=GOOD, parent=None):
        self.before = dict(st_dev=3, st_ino=17, st_size=len(GOOD), st_mtime_ns=3000000001,
                           st_nlink=1, st_mode=stat.S_IFREG|0o644, st_file_attributes=0,
                           st_atime=1.0, st_atime_ns=1000000000)
        self.before.update(before or {})
        self.after = dict(self.before)
        self.after.update(after or {})
        self.raw = raw
        self.read_started = False
        self.parents = (parent or FakeParent(),)

    def __str__(self):
        return '<synthetic-ui-bootstrap-helper.py>'

    def lstat(self):
        return SimpleNamespace(**(self.after if self.read_started else self.before))

    def read_bytes(self):
        self.read_started = True
        return self.raw


class BootstrapIdentityGuards(unittest.TestCase):
    def setUp(self):
        self.name = '_ui_guard_'+self._testMethodName

    def tearDown(self):
        sys.modules.pop(self.name, None)

    def load(self, source, count=len(GOOD), digest=PIN):
        return subject.load_pinned(self.name, source, count, digest)

    def refuses(self, source, error='HELPER_BYTES_OR_IDENTITY_CHANGED', **kwargs):
        with self.assertRaisesRegex(RuntimeError, '^'+error+'$'):
            self.load(source, **kwargs)
        self.assertNotIn(self.name, sys.modules)

    def test_unchanged_identity_and_bytes_load(self):
        module, raw = self.load(FakeInput())
        self.assertEqual(module.VALUE, 7)
        self.assertEqual(raw, GOOD)

    def test_access_time_only_change_loads_exact_pinned_bytes(self):
        source = FakeInput(after={'st_atime': 9.0, 'st_atime_ns': 9000000000})
        self.assertNotEqual(source.before['st_atime_ns'], source.after['st_atime_ns'])
        module, raw = self.load(source)
        self.assertEqual(module.VALUE, 7)
        self.assertEqual(raw, GOOD)
        self.assertEqual(subject.bootstrap_identity(SimpleNamespace(**source.before)),
                         subject.bootstrap_identity(SimpleNamespace(**source.after)))

    def test_nanosecond_mtime_drift_refuses(self):
        self.refuses(FakeInput(after={'st_mtime_ns': 3000000002}))

    def test_inode_drift_refuses(self):
        self.refuses(FakeInput(after={'st_ino': 18}))

    def test_device_drift_refuses(self):
        self.refuses(FakeInput(after={'st_dev': 4}))

    def test_size_drift_after_read_refuses(self):
        self.refuses(FakeInput(after={'st_size': len(GOOD)+1}))

    def test_link_count_drift_after_read_refuses(self):
        self.refuses(FakeInput(after={'st_nlink': 2}))

    def test_mode_drift_after_read_refuses(self):
        self.refuses(FakeInput(after={'st_mode': stat.S_IFREG|0o600}))

    def test_file_attribute_drift_after_read_refuses(self):
        self.refuses(FakeInput(after={'st_file_attributes': 0x2}))

    def test_same_length_hash_drift_refuses(self):
        self.refuses(FakeInput(raw=b'VALUE = 8\n'))

    def test_wrong_expected_size_refuses_before_read(self):
        source = FakeInput()
        self.refuses(source, 'HELPER_REGULAR_PIN_REQUIRED', count=len(GOOD)+1)
        self.assertFalse(source.read_started)

    def test_initial_nonregular_file_refuses(self):
        source = FakeInput(before={'st_mode': stat.S_IFDIR|0o755})
        self.refuses(source, 'HELPER_REGULAR_PIN_REQUIRED')
        self.assertFalse(source.read_started)

    def test_initial_symlink_refuses(self):
        source = FakeInput(before={'st_mode': stat.S_IFLNK|0o777})
        self.refuses(source, 'HELPER_ALIAS_PATH')
        self.assertFalse(source.read_started)

    def test_parent_reparse_alias_refuses(self):
        source = FakeInput(parent=FakeParent(attributes=0x400))
        self.refuses(source, 'HELPER_ALIAS_PATH')
        self.assertFalse(source.read_started)

    def test_initial_hardlink_refuses(self):
        source = FakeInput(before={'st_nlink': 2})
        self.refuses(source, 'HELPER_REGULAR_PIN_REQUIRED')
        self.assertFalse(source.read_started)

    def test_read_length_drift_with_unchanged_stat_refuses(self):
        self.refuses(FakeInput(raw=GOOD+b' '))

    def test_file_type_becomes_symlink_during_read_refuses(self):
        self.refuses(FakeInput(after={'st_mode': stat.S_IFLNK|0o777}))

    def test_initial_file_reparse_alias_refuses(self):
        source = FakeInput(before={'st_file_attributes': 0x400})
        self.refuses(source, 'HELPER_ALIAS_PATH')
        self.assertFalse(source.read_started)


if __name__ == '__main__':
    unittest.main(verbosity=2)
