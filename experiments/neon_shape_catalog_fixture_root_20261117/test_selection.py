"""Run real selector/helper AST with virtual paths; no native/filesystem IO."""
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import ast
import hashlib
import ntpath
import unittest

HERE = Path(__file__).resolve().parent
CHECKOUT = r'C:\virtual\studio'
EXTERNAL = r'C:\virtual\current-fixtures'


class VirtualPath:
    directories = set()
    files = set()
    calls = []
    def __init__(self, value): self.value = PureWindowsPath(str(value))
    def __str__(self): return str(self.value)
    def __truediv__(self, value): return VirtualPath(self.value / str(value))
    @property
    def parents(self): return tuple(VirtualPath(value) for value in self.value.parents)
    def expanduser(self):
        self.calls.append(('expanduser', str(self)))
        text = str(self)
        return VirtualPath(r'C:\virtual\home' + text[1:]) if text.startswith('~') else self
    def resolve(self, strict=False):
        self.calls.append(('resolve', str(self), strict))
        text = str(self)
        if not self.value.is_absolute(): text = ntpath.join(CHECKOUT, text)
        resolved = VirtualPath(ntpath.normpath(text))
        if strict and str(resolved) not in self.directories | self.files: raise FileNotFoundError('Virtual configured root absent')
        return resolved
    def is_dir(self): return str(self) in self.directories
    def is_file(self): return str(self) in self.files


def namespace(environment):
    source = (HERE / 'original-native_fixture_root.py').read_text(encoding='utf-8')
    definition = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'fixture_output')
    values = {'Path': VirtualPath, 'os': SimpleNamespace(environ=environment), '__file__': CHECKOUT + r'\tests\native_fixture_root.py', 'ROOT': VirtualPath(CHECKOUT)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[definition], type_ignores=[])), '<actual-source-helper-virtual-paths>', 'exec'), values)
    return values


def select(filename, target, environment):
    source = (HERE / filename).read_text(encoding='utf-8'); tree = ast.parse(source)
    assignment = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == target for t in n.targets))
    return eval(compile(ast.fix_missing_locations(ast.Expression(assignment.value)), '<actual-selector-AST-only>', 'eval'), namespace(environment))


class Selection(unittest.TestCase):
    def setUp(self):
        VirtualPath.directories = {CHECKOUT + r'\output', EXTERNAL}
        VirtualPath.files = {CHECKOUT + r'\output\sfm-face-pilot.json', EXTERNAL + r'\sfm-face-pilot.json'}
        VirtualPath.calls = []
    def shape(self, env=None): return select('verify_shape_catalog.proposed.py', 'face', env or {})
    def test_default_lookup_is_exact_existing_checkout_output(self):
        self.assertEqual(str(self.shape()), CHECKOUT + r'\output\sfm-face-pilot.json')
    def test_override_selects_current_fixture_root_not_stale_checkout(self):
        env = {'HYBRID_NATIVE_FIXTURES': EXTERNAL}
        self.assertEqual(str(self.shape(env)), EXTERNAL + r'\sfm-face-pilot.json')
        old = select('original-verify_shape_catalog.py', 'face', env)
        self.assertEqual(str(old), CHECKOUT + r'\output\sfm-face-pilot.json')
        self.assertNotEqual(str(old), str(self.shape(env)))
    def test_shape_VRM_and_face_descriptors_share_selected_root(self):
        env = {'HYBRID_NATIVE_FIXTURES': EXTERNAL}
        native = select('verify_shape_catalog.proposed.py', 'native', env)
        self.assertEqual(str(native), EXTERNAL + r'\native-import-verification.json')
        self.assertEqual(str(self.shape(env)), EXTERNAL + r'\sfm-face-pilot.json')
    def test_missing_override_refuses_instead_of_falling_back(self):
        with self.assertRaises(FileNotFoundError): self.shape({'HYBRID_NATIVE_FIXTURES': r'C:\virtual\missing'})
        self.assertTrue(any(call[0] == 'resolve' and call[2] is True for call in VirtualPath.calls if call[0] == 'resolve'))
    def test_file_override_refuses_even_when_checkout_descriptor_exists(self):
        fake_file = r'C:\virtual\not-a-directory'; VirtualPath.files.add(fake_file)
        with self.assertRaisesRegex(ValueError, 'existing prepared-fixture directory'): self.shape({'HYBRID_NATIVE_FIXTURES': fake_file})
    def test_empty_override_preserves_existing_helper_default_policy(self):
        self.assertEqual(str(self.shape({'HYBRID_NATIVE_FIXTURES': ''})), CHECKOUT + r'\output\sfm-face-pilot.json')
    def test_absent_selected_descriptor_does_not_fall_back_to_present_stale_one(self):
        VirtualPath.files.remove(EXTERNAL + r'\sfm-face-pilot.json')
        selected = self.shape({'HYBRID_NATIVE_FIXTURES': EXTERNAL})
        self.assertEqual(str(selected), EXTERNAL + r'\sfm-face-pilot.json'); self.assertFalse(selected.is_file())
        self.assertTrue(VirtualPath(CHECKOUT + r'\output\sfm-face-pilot.json').is_file())
    def test_relative_and_home_override_keep_actual_helper_resolution_steps(self):
        relative = CHECKOUT + r'\prepared'; home = r'C:\virtual\home\prepared'
        VirtualPath.directories.update((relative, home))
        self.assertEqual(str(self.shape({'HYBRID_NATIVE_FIXTURES': 'prepared'})), relative + r'\sfm-face-pilot.json')
        self.assertEqual(str(self.shape({'HYBRID_NATIVE_FIXTURES': r'~\prepared'})), home + r'\sfm-face-pilot.json')
    def test_shape_exact_byte_inverse_preserves_every_original_check_and_native_case(self):
        old = (HERE / 'original-verify_shape_catalog.py').read_bytes(); new = (HERE / 'verify_shape_catalog.proposed.py').read_bytes()
        before = b"face=ROOT/'output/sfm-face-pilot.json'"; after = b"face=fixture_output()/'sfm-face-pilot.json'"
        self.assertEqual(old.count(before), 1); self.assertEqual(new.count(after), 1); self.assertEqual(new.replace(after, before), old)
        self.assertIn(b"'label':'Supplied Mima'", new); self.assertIn(b"('h264',1920,1080,'24/1','48')", new)
    def test_height_separate_selector_default_override_and_exact_inverse(self):
        default = select('verify_character_height.proposed.py', 'native_manifest', {})
        override = select('verify_character_height.proposed.py', 'native_manifest', {'HYBRID_NATIVE_FIXTURES': EXTERNAL})
        self.assertEqual(str(default), CHECKOUT + r'\output\native-import-verification.json')
        self.assertEqual(str(override), EXTERNAL + r'\native-import-verification.json')
        old = (HERE / 'original-verify_character_height.py').read_bytes(); new = (HERE / 'verify_character_height.proposed.py').read_bytes()
        newline = b'\r\n' if b'\r\n' in old else b'\n'; added = b'from native_fixture_root import fixture_output' + newline
        self.assertEqual(new.replace(added, b'').replace(b"native_manifest=fixture_output()/'native-import-verification.json'", b"native_manifest=ROOT/'output/native-import-verification.json'"), old)
    def test_missing_default_output_raises_original_helper_error(self):
        VirtualPath.directories.remove(CHECKOUT + r'\output')
        with self.assertRaises(ValueError): self.shape()


if __name__ == '__main__': unittest.main(verbosity=2)
