"""Pure compiler-context regression; no Blender/SDK/native module import.

Root alone runs. Actual pinned Python SOURCE is read/compiled, never imported
or executed wholesale. Runtime targets are fabricated FunctionType objects
holding full-module code; default checks keep the previous narrow construction.
"""
import ast
import copy
import hashlib
from pathlib import Path
import types
import unittest

import export_hook_proposal as H

HERE = Path(__file__).resolve().parent
SDK_SOURCE = Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647\blender_bindings\models\mdl49\import_mdl.py')
SDK_PIN = (12880, '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b')


def direct(code, name):
    values = [item for item in code.co_consts if type(item) is types.CodeType and item.co_name == name]
    if len(values) != 1: raise AssertionError('one independent direct code object required')
    return values[0]


def code_for(source, filename, name, owner=None):
    code = compile(source, filename, 'exec', dont_inherit=True)
    return direct(direct(code, owner), name) if owner is not None else direct(code, name)


def mangle(owner, name):
    return '_' + owner.lstrip('_') + name if owner and name.startswith('__') and not name.endswith('__') else name


def runtime(source, name='f', owner=None, *, defaults=None, kwdefaults=None, filename='synthetic_context.py'):
    module = types.ModuleType('_has_synthetic_complete_context')
    module.__file__ = filename
    code = code_for(source, filename, name, owner)
    target = types.FunctionType(code, vars(module), name, defaults)
    target.__kwdefaults__ = kwdefaults
    if owner is None: setattr(module, name, target)
    else:
        klass = type(owner, (), {'__module__': module.__name__})
        setattr(klass, mangle(owner, name), target)
        setattr(module, owner, klass)
    return module, target


def node_for(source, name, owner=None):
    body = ast.parse(source).body
    if owner:
        body = next(node.body for node in body if isinstance(node, ast.ClassDef) and node.name == owner)
    return next(node for node in body if isinstance(node, ast.FunctionDef) and node.name == name)


def literal_defaults(node):
    positional = tuple(ast.literal_eval(value) for value in node.args.defaults) or None
    keyword = {arg.arg: ast.literal_eval(value) for arg, value in zip(node.args.kwonlyargs, node.args.kw_defaults)
               if value is not None} or None
    return positional, keyword


class CompilerContextTests(unittest.TestCase):
    def test_complete_module_top_level_raise_import_and_decorator_are_not_executed(self):
        source = "import must_never_import\n@must_never_decorate\ndef f(a=3, *, b=4):\n    return a+b\nraise RuntimeError('top level must not run')\n"
        module, target = runtime(source, defaults=(3,), kwdefaults={'b': 4})
        self.assertIs(H._plain(module, source, 'f'), target)
        self.assertEqual(target(8, b=5), 13)
        self.assertNotIn('must_never_import', vars(module))
        self.assertNotIn('must_never_decorate', vars(module))

    def test_future_annotations_and_private_class_method_keep_full_flags_qualname_defaults(self):
        source = "from __future__ import annotations\nclass _Owner:\n    def __turn(self, value: AnnotationMustNotResolve=7, *, mode='LOCAL') -> OtherUnknown:\n        return value,mode\nraise RuntimeError('never')\n"
        module, target = runtime(source, '__turn', '_Owner', defaults=(7,), kwdefaults={'mode': 'LOCAL'})
        self.assertIs(H._plain(module, source, '__turn', '_Owner', target), target)
        self.assertEqual(target.__code__.co_qualname, '_Owner.__turn')
        self.assertEqual(target(None, 9), (9, 'LOCAL'))
        self.assertNotIn('AnnotationMustNotResolve', vars(module))

    def test_decorated_code_firstline_comes_from_original_complete_module(self):
        source = "# header\n@never_decorate\n@another_unexecuted_decorator\ndef f(value=None):\n    return value\n"
        module, target = runtime(source, defaults=(None,))
        self.assertEqual(target.__code__.co_firstlineno, 2)
        self.assertIs(H._plain(module, source, 'f'), target)

    def test_changed_complete_runtime_code_still_refuses(self):
        source = 'def f(value=4):\n    return value+1\n'
        module, target = runtime(source, defaults=(4,))
        changed = code_for(source.replace('+1', '+2'), module.__file__, 'f')
        target.__code__ = changed
        with self.assertRaises(H.Refusal): H._plain(module, source, 'f')

    def test_changed_positional_default_still_refuses_after_exact_code_match(self):
        source = 'def f(value=4):\n    return value\n'
        module, target = runtime(source, defaults=(99,))
        with self.assertRaises(H.Refusal): H._plain(module, source, 'f')

    def test_changed_keyword_default_still_refuses_after_exact_code_match(self):
        source = "def f(*, mode='LOCAL'):\n    return mode\n"
        module, target = runtime(source, kwdefaults={'mode': 'WORLD'})
        with self.assertRaises(H.Refusal): H._plain(module, source, 'f')

    def test_foreign_globals_or_filename_are_not_accepted_by_code_equivalence(self):
        source = 'def f():\n    return 1\n'
        module, target = runtime(source)
        foreign = types.FunctionType(target.__code__, dict(vars(module)))
        with self.assertRaises(H.Refusal): H._plain(module, source, 'f', runtime=foreign)
        target.__code__ = target.__code__.replace(co_filename='foreign.py')
        with self.assertRaises(H.Refusal): H._plain(module, source, 'f')

    def test_closure_and_ambiguous_whole_module_definitions_refuse(self):
        source = 'def f():\n    return 1\n'
        module, _ = runtime(source)
        def outer():
            value = 9
            def closed(): return value
            return closed
        with self.assertRaises(H.Refusal): H._plain(module, source, 'f', runtime=outer())
        ambiguous = 'if flag:\n    def f(): return 1\nelse:\n    def f(): return 2\n'
        with self.assertRaises(H.Refusal):
            H._function_code(compile(ambiguous, module.__file__, 'exec', dont_inherit=True), 'f')

    def test_pinned_sdk_actual_function_context_regression_requires_full_code(self):
        raw = SDK_SOURCE.read_bytes()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), SDK_PIN)
        source = raw.decode()
        node = node_for(source, 'import_model')
        defaults, kwdefaults = literal_defaults(node)
        module, target = runtime(source, 'import_model', defaults=defaults, kwdefaults=kwdefaults, filename=str(SDK_SOURCE))
        # Only header annotation symbols are needed to retain the original
        # metadata-construction checks; no SourceIO imports/function body run.
        for annotation in [node.returns, *(arg.annotation for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs])]:
            if annotation is not None:
                for item in ast.walk(annotation):
                    if isinstance(item, ast.Name): vars(module).setdefault(item.id, object())
        isolated = compile(H._definition(source, 'import_model'), str(SDK_SOURCE), 'exec', dont_inherit=True)
        self.assertNotEqual(target.__code__, direct(isolated, 'import_model'))
        self.assertIs(H._plain(module, source, 'import_model'), target)

    def test_actual_pinned_primitive_class_context_matches_retained_isolated_guard(self):
        relative, digest = H.PINS['extractor']
        path = H.EXPORTER_ROOT / relative
        raw = path.read_bytes(); self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        source = raw.decode()
        full = compile(source, str(path), 'exec', dont_inherit=True)
        tree = ast.parse(source)
        klass = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'PrimitiveCreator')
        futures = [copy.deepcopy(node) for node in tree.body
                   if isinstance(node, ast.ImportFrom) and node.module == '__future__']
        isolated = compile(ast.fix_missing_locations(ast.Module(body=[*futures, copy.deepcopy(klass)], type_ignores=[])),
                           str(path), 'exec', dont_inherit=True)
        for method in ('primitive_creation_shared', 'primitive_creation_not_shared'):
            with self.subTest(method=method):
                self.assertEqual(direct(direct(full, 'PrimitiveCreator'), method),
                                 direct(direct(isolated, 'PrimitiveCreator'), method),
                                 'A concrete class-context mismatch requires fixing successor observed_methods before native retry')

    def test_actual_observer_and_binder_source_metadata_stays_meaningful(self):
        for filename, owner in (('observer_instrumentation.py', None), ('gather_binding.py', 'GatherBinding')):
            source = (HERE / filename).read_text(encoding='utf-8')
            tree = ast.parse(source)
            body = tree.body if owner is None else next(node.body for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner)
            for node in body:
                if not isinstance(node, ast.FunctionDef) or node.decorator_list: continue
                with self.subTest(file=filename, name=node.name):
                    defaults, kwdefaults = literal_defaults(node)
                    module, target = runtime(source, node.name, owner, defaults=defaults,
                                             kwdefaults=kwdefaults, filename=str(HERE / filename))
                    self.assertIs(H._plain(module, source, node.name, owner, target), target)


if __name__ == '__main__':
    unittest.main()
