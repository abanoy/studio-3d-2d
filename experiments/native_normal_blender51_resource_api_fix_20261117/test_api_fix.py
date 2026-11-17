"""Synthetic API-boundary regression, exact inverses, and public source evidence."""
from pathlib import Path
import ast
import dataclasses
import importlib.util
import sys
import unittest

import derive_api_fix as D
import survey_core as C
import test_resources as T

HERE = Path(__file__).resolve().parent


class APIFixTests(unittest.TestCase):
    def test_entire_source_inverses_and_companion_bytes(self):
        for name, original in D.parent_sources().items():
            actual = (HERE / name).read_bytes()
            self.assertEqual(actual, D.render(name, original))
            self.assertEqual(D.inverse(name, actual), original)

    def test_namespaced_only_mock_reproduces_old_failure_and_new_success(self):
        spec = importlib.util.spec_from_file_location('api_fix_original_collector_cpu_only', D.PARENT / 'survey_core.py')
        old = importlib.util.module_from_spec(spec); sys.modules[spec.name] = old
        try:
            spec.loader.exec_module(old)
            bpy = T.fixture()
            self.assertFalse(hasattr(bpy, 'blend_paths'))
            with self.assertRaisesRegex(AttributeError, 'blend_paths'):
                old.collect_resources(bpy, T.ORIGINAL)
            self.assertEqual(bpy.calls, [])
            private, public = C.collect_resources(bpy, T.ORIGINAL)
            self.assertEqual(public['status'], 'METADATA_SURVEY_ONLY')
            self.assertFalse(private['external_path_contents_opened_or_statted'])
            self.assertEqual(bpy.calls, [{'absolute': False, 'packed': True, 'local': False},
                                         {'absolute': False, 'packed': False, 'local': False}])
            self.assertEqual(dataclasses.asdict(C.HARD), dataclasses.asdict(old.HARD))
        finally: del sys.modules[spec.name]

    def test_top_level_callable_is_never_used(self):
        bpy = T.fixture()
        def forbidden(**kwargs): raise AssertionError('Wrong top-level API was called')
        bpy.blend_paths = forbidden
        C.collect_resources(bpy, T.ORIGINAL)
        self.assertEqual(len(bpy.calls), 2)

    def test_missing_correct_api_does_not_fall_back(self):
        bpy = T.fixture(); del bpy.utils
        bpy.blend_paths = lambda **kwargs: []
        with self.assertRaisesRegex(AttributeError, 'utils'): C.collect_resources(bpy, T.ORIGINAL)

    def test_path_type_count_and_api_exception_guards_remain(self):
        for value in [(), [''] * (C.HARD.external_paths + 1)]:
            bpy = T.fixture(); bpy.utils.blend_paths = lambda **kwargs: value
            with self.assertRaisesRegex(C.SurveyError, 'EXTERNAL_PATH_COUNT'): C.collect_resources(bpy, T.ORIGINAL)
        bpy = T.fixture()
        def failed(**kwargs): raise RuntimeError('synthetic utils refusal')
        bpy.utils.blend_paths = failed
        with self.assertRaisesRegex(RuntimeError, 'synthetic utils refusal'): C.collect_resources(bpy, T.ORIGINAL)

    def test_public_source_exports_utils_api_without_importing_it(self):
        value = D.source_evidence()
        self.assertTrue(value['blend_paths_in_utils_all'])
        self.assertTrue(value['utils_imports_blend_paths_from_bpy_extension'])
        self.assertFalse(value['module_imported_or_executed'])

    def test_collector_capabilities_and_original_test_assertions_unchanged(self):
        original = D.parent_sources()
        self.assertEqual(ast.dump(ast.parse(D.inverse('survey_core.py', (HERE / 'survey_core.py').read_bytes()))),
                         ast.dump(ast.parse(original['survey_core.py'])))
        old_tests = ast.parse(original['test_resources.py'])
        new_tests = ast.parse((HERE / 'test_resources.py').read_bytes())
        assertions = lambda unit: [ast.dump(n) for n in ast.walk(unit)
                                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                                  and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self'
                                  and n.func.attr.startswith('assert')]
        self.assertEqual(assertions(old_tests), assertions(new_tests))
        self.assertEqual(len(unittest.defaultTestLoader.getTestCaseNames(T.ResourceTests)), 31)
        for node in ast.walk(ast.parse((HERE / 'survey_core.py').read_bytes())):
            if isinstance(node, ast.Import):
                self.assertFalse(any(a.name.split('.')[0] in {'bpy', 'os', 'sys', 'pathlib', 'subprocess', 'socket', 'ctypes', 'requests', 'urllib'} for a in node.names))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {'open', 'eval', 'exec', '__import__'})


if __name__ == '__main__': unittest.main(verbosity=2)
