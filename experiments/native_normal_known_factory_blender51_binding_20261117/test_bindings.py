"""Synthetic binder/current-context semantics; no main/admission/native calls."""
from pathlib import Path
import ast, hashlib, types, unittest
import prepare_root as P
import derive_bindings as D
from test_source import BindingTests

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'native_normal_known_factory_binding_git_tool_20261117'


class SourceBindingTests(unittest.TestCase):
    def test_two_runtime_literals_inverse_and_original_Git_policy_exact(self):
        original = (PARENT / 'prepare_root.py').read_bytes(); actual = (HERE / 'prepare_root.py').read_bytes()
        self.assertEqual(hashlib.sha256((PARENT / 'INDEX.json').read_bytes()).hexdigest(), D.PARENT_INDEX)
        self.assertEqual(D.render(original), actual)
        with self.assertRaises(ValueError): D.render(original + b'\n')
        self.assertEqual(P.SUCCESSOR.name, 'native_normal_known_factory_blender51_resource_20261117')
        self.assertEqual(P.SUCCESSOR_SHA, D.RUNTIME_INDEX)
        self.assertEqual(hashlib.sha256((P.SUCCESSOR / 'INDEX.json').read_bytes()).hexdigest(), D.RUNTIME_INDEX)
        self.assertEqual(actual.count(b'reader.identity(S.safe(GIT), single_link=False)'), 2)
        self.assertIn(b'reader.identity(path, single_link=True)', actual)
        old_functions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(original).body if isinstance(n, ast.FunctionDef)}
        new_functions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(actual).body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(old_functions, new_functions)


raw = (PARENT / 'test_git_policy.py').read_bytes()
if hashlib.sha256(raw).hexdigest() != '21fece0b5c3226d30f7afda85a35ec940bb1b740ea1f03c8b60cf0f5e17b5878':
    raise ValueError('exact parent Git-policy synthetic test source required')
tree = ast.parse(raw)
reader_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SyntheticReader')
policy_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'GitPolicyTests')
policy_class.body = [n for n in policy_class.body if not isinstance(n, ast.FunctionDef)
                     or n.name != 'test_exact_two_git_arguments_and_whole_source_inverse']
assert len([n for n in policy_class.body if isinstance(n, ast.FunctionDef)]) == 2
namespace = dict(globals(), __name__='retained_original_Git_policy_cpu')
exec(compile(ast.Module(body=[reader_class, policy_class], type_ignores=[]), '<two exact original Git-policy methods>', 'exec'), namespace)
GitPolicyTests = namespace['GitPolicyTests']

if __name__ == '__main__': unittest.main(verbosity=2)
