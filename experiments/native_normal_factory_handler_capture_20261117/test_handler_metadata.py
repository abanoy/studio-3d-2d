"""Synthetic callbacks and source inverses only; no Blender/root/native checks."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast
import hashlib
import json
import unittest
import handler_metadata as H
import source_capture as C

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'native_normal_resource_diagnostic_import_fix_20261117'


def handlers(**values):
    return SimpleNamespace(**{name: values.get(name, []) for name in H.HANDLERS})


class MetadataTests(unittest.TestCase):
    def test_python_callback_identity_code_hash_without_callback_or_path_open(self):
        namespace = {'__name__': 'SYNTHETIC_PRIVATE_MODULE'}
        exec(compile('def callback(*args):\n raise AssertionError("must not call")\n',
                     r'C:\DO_NOT_OPEN\private_factory.py', 'exec'), namespace)
        callback = namespace['callback']; callback.__qualname__ = 'SYNTHETIC_PRIVATE_QUALNAME'
        with patch('builtins.open', side_effect=AssertionError('No path may open')):
            raw, summary = H.capture_handlers(handlers(load_post=[callback]))
        row = json.loads(raw)['callbacks'][0]
        self.assertEqual(row['name'], 'callback'); self.assertEqual(row['module'], 'SYNTHETIC_PRIVATE_MODULE')
        self.assertEqual(row['qualname'], 'SYNTHETIC_PRIVATE_QUALNAME')
        self.assertEqual(row['code_filename'], r'C:\DO_NOT_OPEN\private_factory.py')
        self.assertEqual(row['first_line'], callback.__code__.co_firstlineno)
        self.assertEqual(row['bytecode_sha256'], hashlib.sha256(callback.__code__.co_code).hexdigest())
        self.assertFalse(summary['known_B_opened']); self.assertFalse(summary['resource_or_native_PASS'])

    def test_bound_builtin_and_custom_callable_never_execute_custom_getters(self):
        class Bound:
            def hook(self, *args): raise AssertionError('Do not call')
        class Trap:
            def __getattribute__(self, name): raise AssertionError('Do not inspect custom getter')
            def __call__(self, *args): raise AssertionError('Do not call')
        raw, _ = H.capture_handlers(handlers(load_pre=[Bound().hook, len, Trap()]))
        rows = json.loads(raw)['callbacks']
        self.assertEqual(rows[0]['kind'], 'BOUND_PYTHON_METHOD')
        self.assertEqual(rows[1]['kind'], 'BUILTIN_NO_PYTHON_CODE'); self.assertIsNone(rows[1]['bytecode_sha256'])
        self.assertEqual(rows[2]['kind'], 'UNSUPPORTED_CALLBACK_TYPE_METADATA_UNOBSERVED')
        self.assertIsNone(rows[2]['name']); self.assertIsNone(rows[2]['code_filename'])

    def test_counts_and_metadata_string_caps_refuse_without_callback_calls(self):
        def callback(): raise AssertionError('Do not call')
        with self.assertRaises(ValueError): H.capture_handlers(handlers(load_pre=[callback] * 65))
        with self.assertRaises(ValueError): H.capture_handlers(handlers(**{name: [callback] * 64 for name in H.HANDLERS}))
        callback.__module__ = 'x' * 4097
        with self.assertRaises(ValueError): H.capture_handlers(handlers(load_pre=[callback]))

    def test_summary_contains_only_counts_statuses_hashes_not_private_names_or_bytecode(self):
        def callback(): raise AssertionError('Do not call')
        callback.__module__ = 'SYNTHETIC_PRIVATE_MODULE'
        raw, summary = H.capture_handlers(handlers(load_pre=[callback]))
        public = json.dumps(summary)
        self.assertNotIn('SYNTHETIC_PRIVATE_MODULE', public); self.assertNotIn('code_filename', public)
        self.assertEqual(summary['private_metadata_bytes'], len(raw))
        self.assertEqual(summary['private_metadata_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertFalse(json.loads(raw)['callbacks_called']); self.assertFalse(json.loads(raw)['code_paths_opened'])

    def test_exact_capture_inverse_keeps_every_original_guard_and_returns_before_B_open(self):
        source = (HERE / 'diagnostic_host.py').read_text(encoding='utf-8')
        old = (OLD / 'diagnostic_host.py').read_text(encoding='utf-8')
        self.assertEqual(C.derive(old), source); self.assertEqual(C.restore(source), old)
        for name in ('diagnostic_support.py', 'root_runner.py'):
            self.assertEqual((HERE / name).read_bytes(), (OLD / name).read_bytes())
        main = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        early = next(node for node in main.body if isinstance(node, ast.Return))
        opens = [node for node in ast.walk(main) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'open_mainfile']
        self.assertEqual(len(opens), 1); self.assertLess(early.lineno, opens[0].lineno)
        self.assertIn('Unexpected pre-load handler', source)
        with self.assertRaises(ValueError): C.restore(source.replace('load_ui=False', 'load_ui=True'))


if __name__ == '__main__': unittest.main(verbosity=2)
