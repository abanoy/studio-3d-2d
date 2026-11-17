"""Isolated Blender-like script entry imports; never enters host main or bpy."""
from pathlib import Path
from contextlib import contextmanager
import builtins
import hashlib
import sys
import unittest
import source_import_fix as F

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'native_normal_resource_diagnostic_failed_full_20261117'


@contextmanager
def isolated_entry_path():
    previous_path = sys.path[:]
    previous_support = sys.modules.pop('diagnostic_support', None)
    # Blender --python does not promise to add the script's own folder.
    # Remove explicit workspace paths and the implicit empty/CWD path so that
    # the predecessor cannot accidentally resolve support through this test.
    sys.path[:] = [entry for entry in previous_path if entry
                   and not Path(entry).resolve().is_relative_to(ROOT.parent)]
    try:
        assert str(HERE) not in sys.path and '' not in sys.path
        yield
    finally:
        sys.path[:] = previous_path
        sys.modules.pop('diagnostic_support', None)
        if previous_support is not None: sys.modules['diagnostic_support'] = previous_support


def load_entry(path):
    attempts = {'bpy': 0, 'input_checks': 0}
    normal_import = builtins.__import__
    def forbidden_inputs(*args, **kwargs):
        attempts['input_checks'] += 1
        raise AssertionError('Actual root/native input checking must not execute in entry test')
    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'bpy' or name.startswith('bpy.'):
            attempts['bpy'] += 1
            raise AssertionError('Blender API must not import during source-entry test')
        module = normal_import(name, globals, locals, fromlist, level)
        if name == 'diagnostic_support': module.check_inputs = forbidden_inputs
        return module
    namespace = {'__name__': 'isolated_blender_source_entry', '__file__': str(path),
                 '__builtins__': dict(vars(builtins), __import__=guarded_import)}
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), namespace)
    return namespace, attempts


class EntryImportTests(unittest.TestCase):
    def test_predecessor_reproduces_missing_support_when_here_is_absent(self):
        with isolated_entry_path():
            with self.assertRaises(ModuleNotFoundError) as caught:
                load_entry(OLD / 'diagnostic_host.py')
            self.assertEqual(caught.exception.name, 'diagnostic_support')

    def test_fixed_entry_resolves_its_own_support_without_entering_main(self):
        with isolated_entry_path():
            namespace, attempts = load_entry(HERE / 'diagnostic_host.py')
            self.assertEqual(Path(namespace['S'].__file__).resolve(), HERE / 'diagnostic_support.py')
            self.assertEqual(namespace['S'].HERE, HERE)
            self.assertEqual(sys.path[0], str(HERE))
            self.assertEqual(attempts, {'bpy': 0, 'input_checks': 0})
            self.assertTrue(callable(namespace['main']))

    def test_exact_one_line_host_derivation_and_inverse(self):
        old = (OLD / 'diagnostic_host.py').read_text(encoding='utf-8')
        current = (HERE / 'diagnostic_host.py').read_text(encoding='utf-8')
        self.assertEqual(F.derive(old), current); self.assertEqual(F.restore(current), old)
        self.assertEqual(len(current.splitlines()) - len(old.splitlines()), 1)

    def test_all_other_host_bytes_and_support_driver_guards_are_preserved(self):
        current = (HERE / 'diagnostic_host.py').read_text(encoding='utf-8')
        self.assertEqual(hashlib.sha256(F.restore(current).encode()).hexdigest(), F.BASE_HOST_SHA256)
        for name in ('diagnostic_support.py', 'root_runner.py'):
            self.assertEqual((HERE / name).read_bytes(), (OLD / name).read_bytes())

    def test_derivation_refuses_changed_or_ambiguous_sources(self):
        old = (OLD / 'diagnostic_host.py').read_text(encoding='utf-8')
        current = (HERE / 'diagnostic_host.py').read_text(encoding='utf-8')
        for source in (old + '\n', old + F.BEFORE):
            with self.assertRaises(ValueError): F.derive(source)
        for source in (current + F.AFTER, current.replace('load_ui=False', 'load_ui=True')):
            with self.assertRaises(ValueError): F.restore(source)


if __name__ == '__main__': unittest.main(verbosity=2)
