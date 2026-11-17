"""Fake WinAPI only. Exact approved helper, no desktop/process/Blender calls."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import patch

import placement_sentinel as S

HERE = Path(__file__).resolve().parent
ORIGINAL_TESTS = HERE.parent / 'normal_setter_boundary_sentinel_20261117/test_sentinel.py'
assert hashlib.sha256(ORIGINAL_TESTS.read_bytes()).hexdigest() == 'c070508aea3face5986b491f25bd06ba5b7bd0627853bedbdda34c01d98d6ae2'
spec = importlib.util.spec_from_file_location('approved_fake_sentinel_API', ORIGINAL_TESTS)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


class PlacementTests(unittest.TestCase):
    def test_decorated_helper_raw_and_AST_identity(self):
        text = (HERE / 'placement_sentinel.py').read_bytes().decode()
        node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef))
        start = min([node.lineno, *[x.lineno for x in node.decorator_list]]) - 1
        raw = ''.join(text.splitlines(keepends=True)[start:node.end_lineno])
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), F.HELPER_SHA)

    def test_fake_success_remains_hidden_owned_destroyed(self):
        api = F.FakeAPI()
        with patch.object(S, 'C', F.FakeC(api)), patch.object(S, 'sys', types.SimpleNamespace(platform='win32')):
            with S._hidden_placement_sentinel() as policy: self.assertFalse(policy['destroyed_in_finally'])
        self.assertFalse(api.active); self.assertTrue(policy['destroyed_in_finally'])
        self.assertTrue(policy['owned_pid_and_thread_verified']); self.assertFalse(policy['show_or_activation_calls'])

    def test_fake_body_failure_still_destroys(self):
        api = F.FakeAPI()
        with patch.object(S, 'C', F.FakeC(api)), patch.object(S, 'sys', types.SimpleNamespace(platform='win32')):
            with self.assertRaisesRegex(RuntimeError, 'synthetic body'):
                with S._hidden_placement_sentinel(): raise RuntimeError('synthetic body')
        self.assertFalse(api.active); self.assertEqual(api.destroy_calls, 1)

    def test_fake_visible_or_failed_creation_refuses(self):
        for attr in ('visible', 'fail_create'):
            api = F.FakeAPI(); setattr(api, attr, True)
            with patch.object(S, 'C', F.FakeC(api)), patch.object(S, 'sys', types.SimpleNamespace(platform='win32')):
                with self.assertRaises((RuntimeError, OSError)):
                    with S._hidden_placement_sentinel(): self.fail('must refuse')


if __name__ == '__main__': unittest.main(verbosity=2)
