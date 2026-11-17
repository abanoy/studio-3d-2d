"""Synthetic installed-tool identity only; no installed tools or inputs read."""
import ast
from pathlib import Path
import types
import unittest
import derive
import prepare_root as P
from test_source import BindingTests


class SyntheticReader:
    def __init__(self, links=2, stamp=None):
        self.links = links
        self.stamp = dict(P.GIT_ID if stamp is None else stamp)
        self.calls = []

    def identity(self, path, *, single_link):
        self.calls.append(single_link)
        if single_link and self.links != 1:
            raise ValueError('Synthetic source/model hardlink refused')
        return dict(self.stamp)


class GitPolicyTests(unittest.TestCase):
    def test_exact_two_git_arguments_and_whole_source_inverse(self):
        parent = Path(__file__).resolve().parents[1] / 'native_normal_known_factory_binding_source_20261117/prepare_root.py'
        original = parent.read_bytes(); raw = Path(P.__file__).read_bytes()
        self.assertEqual(derive.render(original), raw)
        self.assertEqual(raw.replace(derive.NEW, derive.OLD), original)
        self.assertEqual(raw.count(derive.NEW), 2)
        self.assertNotIn(derive.OLD, raw)
        self.assertIn(b'reader.identity(path, single_link=True)', raw)
        with self.assertRaises(ValueError): derive.render(original + b'\n')

    def test_two_link_installed_git_requires_exact_identity_at_both_checks(self):
        tree = ast.parse(Path(P.__file__).read_bytes())
        guards = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Name) and node.func.id == 'need'
                  and node.args and isinstance(node.args[0], ast.Compare)
                  and any(isinstance(item, ast.Name) and item.id == 'GIT_ID' for item in ast.walk(node.args[0]))]
        self.assertEqual(len(guards), 2)
        def run(guard, reader):
            namespace = {'need': P.need, 'reader': reader, 'S': types.SimpleNamespace(safe=lambda value: value),
                         'GIT': P.GIT, 'GIT_ID': P.GIT_ID}
            eval(compile(ast.Expression(body=guard), '<synthetic actual Git guard>', 'eval'), namespace)
        for guard in guards:
            reader = SyntheticReader(links=2); run(guard, reader)
            self.assertEqual(reader.calls, [False])
            for field, replacement in (('bytes', 46481), ('mtime_ns', 1760720930000000001), ('sha256', 'f' * 64)):
                changed = dict(P.GIT_ID); changed[field] = replacement
                with self.assertRaises(ValueError): run(guard, SyntheticReader(links=2, stamp=changed))

    def test_generic_source_descriptor_still_refuses_links_and_git_is_readonly(self):
        tree = ast.parse(Path(P.__file__).read_bytes())
        descriptor = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'descriptor')
        reader = SyntheticReader(links=2)
        namespace = {'reader': reader, 'S': types.SimpleNamespace(safe=lambda value: value)}
        exec(compile(ast.Module(body=[descriptor], type_ignores=[]), '<synthetic unchanged source descriptor>', 'exec'), namespace)
        with self.assertRaises(ValueError): namespace['descriptor']('SYNTHETIC_SOURCE')
        self.assertEqual(reader.calls, [True])
        commands = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr == 'check_output']
        self.assertEqual(len(commands), 1)
        self.assertEqual(ast.unparse(commands[0].args[0]), "[str(GIT), 'rev-parse', 'HEAD']")


if __name__ == '__main__': unittest.main(verbosity=2)
