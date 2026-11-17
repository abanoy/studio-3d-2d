"""Rebound source inverse plus five original synthetic handler/context methods."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, types, unittest
import baseline_predicate as B
import current_context as C
import known_handler_policy as H
import diagnostic_support as S
import derive_bindings as D

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'native_normal_known_factory_resource_successor_20261117'
RUNTIME_FILES = ('ADMISSION.template.json', 'CURRENT-CLOSED-LANE.template.json', 'baseline_predicate.py',
                 'current_context.py', 'diagnostic_host.py', 'diagnostic_support.py', 'handler_metadata.py',
                 'known_handler_policy.py', 'known_loaded_survey.py', 'root_runner.py')


class BindingTests(unittest.TestCase):
    def test_exact_two_bindings_and_nine_byte_exact_runtime_companions(self):
        self.assertEqual(hashlib.sha256((PARENT / 'INDEX.json').read_bytes()).hexdigest(), D.PARENT_INDEX)
        for name in RUNTIME_FILES:
            original = (PARENT / name).read_bytes(); actual = (HERE / name).read_bytes()
            self.assertEqual(actual, D.render(original) if name == 'diagnostic_support.py' else original)
        with self.assertRaises(ValueError): D.render((PARENT / 'diagnostic_support.py').read_bytes() + b'\n')
        self.assertEqual(S.SURVEY.name, 'native_normal_blender51_resource_api_fix_20261117')
        self.assertEqual(S.SURVEY_SHA, D.SURVEY_INDEX)


raw = (PARENT / 'test_source.py').read_bytes()
if hashlib.sha256(raw).hexdigest() != 'df985e646602a3ed20628301f81ea844c1116a65fb60e9de4434dd19060dcaa5':
    raise ValueError('exact parent synthetic test source required')
tree = ast.parse(raw)
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
source_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SourceTests')
source_class.body = [n for n in source_class.body if not isinstance(n, ast.FunctionDef)
                     or n.name != 'test_six_exact_derivations_inverses_and_original_resource_ownership_guards']
assert len([n for n in source_class.body if isinstance(n, ast.FunctionDef)]) == 5
namespace = dict(globals(), __name__='rebound_original_runtime_cpu', EXPERIMENTS=HERE.parent)
exec(compile(ast.Module(body=[*functions, source_class], type_ignores=[]), '<five exact original synthetic methods>', 'exec'), namespace)
SourceTests = namespace['SourceTests']

if __name__ == '__main__': unittest.main(verbosity=2)
