"""Pure compiler-context regression; no Blender/SDK/native module import.

Root alone runs. Actual pinned Python SOURCE is read/compiled, never imported
or executed wholesale. Runtime targets are fabricated FunctionType objects
holding full-module code; default checks keep the previous narrow construction.
"""
import ast
import copy
import hashlib
import importlib.util
from pathlib import Path
import types
import unittest

import export_hook_proposal as H

HERE = Path(__file__).resolve().parent
SDK_SOURCE = Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647\blender_bindings\models\mdl49\import_mdl.py')
SDK_PIN = (12880, '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b')
_observer_spec = importlib.util.spec_from_file_location('_has_compiler_context_source_observer', HERE / 'observer_instrumentation.py')
O = importlib.util.module_from_spec(_observer_spec)
_observer_spec.loader.exec_module(O)


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


def observer_surface(source, filename, observer):
    """Fabricate actual full-module-code functions; no original class exec."""
    module = types.ModuleType('_has_full_context_extractor')
    module.__file__ = filename
    klass = type('PrimitiveCreator', (), {'__module__': module.__name__})
    module.PrimitiveCreator = klass
    module.unrelated_global_marker = object()
    for name in O.METHODS:
        node = node_for(source, name, 'PrimitiveCreator')
        defaults, kwdefaults = literal_defaults(node)
        function = types.FunctionType(code_for(source, filename, name, 'PrimitiveCreator'),
                                      vars(module), name, defaults)
        function.__kwdefaults__ = kwdefaults
        setattr(klass, name, function)
    surface = H.PinnedSurface.__new__(H.PinnedSurface)
    surface.observer, surface.modules, surface.sources = observer, {'extractor': module}, {'extractor': source}
    return surface, module, klass


def changed_whole_source(source, observer):
    original, changed, proof = observer.instrument_pinned_class(source)
    complete = ast.parse(source)
    for index, node in enumerate(complete.body):
        if isinstance(node, ast.ClassDef) and node.name == 'PrimitiveCreator':
            complete.body[index] = copy.deepcopy(next(item for item in changed.body if isinstance(item, ast.ClassDef)))
            break
    return ast.fix_missing_locations(complete)


SYNTHETIC_CLASS = """from __future__ import annotations
TOP_LEVEL_MARKER = 'must not be executed'
class PrimitiveCreator:
    def primitive_creation_shared(self):
        self.blender_idxs = self.dots['vertex_index']
        return self.blender_idxs
    def primitive_creation_not_shared(self):
        material_idx = 3
        indices = (0, 1)
        primitives = [None]
        self.blender_idxs = self.prim_dots['vertex_index']
        return self.blender_idxs, material_idx, len(primitives)
raise RuntimeError('whole module must never execute')
"""


def generic_observer(transform=None):
    def instrument(source):
        original, changed, proof = O._instrument(source,
            {'primitive_creation_shared': ('dots', None), 'primitive_creation_not_shared': ('prim_dots', None)})
        if transform: transform(changed)
        return original, changed, proof
    return types.SimpleNamespace(METHODS=O.METHODS, CALLBACK=O.CALLBACK, instrument_pinned_class=instrument)


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

    def test_actual_pinned_class_mismatch_is_diagnostic_and_new_methods_use_complete_context(self):
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
                self.assertNotEqual(direct(direct(full, 'PrimitiveCreator'), method),
                                    direct(direct(isolated, 'PrimitiveCreator'), method))
        surface, module, klass = observer_surface(source, str(path), O)
        callback_calls = []
        callback = lambda *args: callback_calls.append(args)
        original_methods = {name: klass.__dict__[name] for name in O.METHODS}
        rows, proof = surface.observed_methods(callback)
        independent = compile(changed_whole_source(source, O), str(path), 'exec', dont_inherit=True)
        self.assertEqual(len(rows), 2)
        for owner, name, original, observed in rows:
            self.assertIs(owner, klass); self.assertIs(original, original_methods[name])
            self.assertIs(klass.__dict__[name], original)
            self.assertEqual(original.__code__, direct(direct(full, 'PrimitiveCreator'), name))
            self.assertEqual(observed.__code__, direct(direct(independent, 'PrimitiveCreator'), name))
            self.assertIs(observed.__defaults__, original.__defaults__)
            self.assertIs(observed.__kwdefaults__, original.__kwdefaults__)
            self.assertIs(observed.__globals__[O.CALLBACK], callback)
            self.assertTrue(all(observed.__globals__[key] is value for key, value in vars(module).items()))
        self.assertTrue(proof['complete_module_context'])
        self.assertTrue(proof['complete_module_AST_inverse_exact'])
        self.assertFalse(proof['complete_module_execution'])
        self.assertEqual(callback_calls, [])

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

    def test_observed_functions_execute_only_two_callbacks_and_preserve_metadata_and_globals(self):
        observer = generic_observer()
        surface, module, klass = observer_surface(SYNTHETIC_CLASS, 'synthetic_full_class.py', observer)
        calls = []
        callback = lambda *args: calls.append(args)
        marker = object()
        for name in O.METHODS:
            function = klass.__dict__[name]
            function.__kwdefaults__ = {}
            function.__dict__['retained_marker'] = marker
        before = dict(klass.__dict__)
        rows, proof = surface.observed_methods(callback)
        shared_ids, separate_ids = (4, 9), (2, 8)
        obj = types.SimpleNamespace(dots={'vertex_index': shared_ids}, prim_dots={'vertex_index': separate_ids})
        outputs = []
        for owner, name, original, observed in rows:
            self.assertEqual(observed.__name__, original.__name__)
            self.assertEqual(observed.__qualname__, original.__qualname__)
            self.assertEqual(observed.__module__, original.__module__)
            self.assertEqual(observed.__doc__, original.__doc__)
            self.assertEqual(observed.__annotations__, original.__annotations__)
            self.assertIs(observed.__dict__['retained_marker'], marker)
            self.assertIs(observed.__defaults__, original.__defaults__)
            self.assertIs(observed.__kwdefaults__, original.__kwdefaults__)
            self.assertEqual(set(observed.__globals__), set(vars(module)) | {O.CALLBACK})
            self.assertTrue(all(observed.__globals__[key] is value for key, value in vars(module).items()))
            outputs.append(observed(obj))
        self.assertEqual(outputs, [shared_ids, (separate_ids, 3, 1)])
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[0][0], obj); self.assertEqual(calls[0][1], 'shared'); self.assertIs(calls[0][2], shared_ids)
        self.assertIs(calls[1][0], obj); self.assertEqual(calls[1][1], 'not_shared'); self.assertIs(calls[1][2], separate_ids)
        self.assertNotIn('TOP_LEVEL_MARKER', vars(module))
        self.assertEqual(set(klass.__dict__), set(before))
        self.assertTrue(all(klass.__dict__[key] is value for key, value in before.items()))
        self.assertTrue(proof['complete_module_AST_inverse_exact'])
        self.assertFalse(proof['complete_module_execution'])

    def test_unrelated_ast_or_runtime_global_or_callback_catalogue_change_refuses(self):
        def alter_return(changed):
            method = next(node for node in ast.walk(changed) if isinstance(node, ast.FunctionDef)
                          and node.name == 'primitive_creation_shared')
            returned = next(node for node in ast.walk(method) if isinstance(node, ast.Return))
            returned.value = ast.copy_location(ast.Constant(42), returned.value)
        surface, module, klass = observer_surface(SYNTHETIC_CLASS, 'synthetic_inverse.py', generic_observer(alter_return))
        with self.assertRaises(H.Refusal): surface.observed_methods(lambda *args: None)
        surface, module, klass = observer_surface(SYNTHETIC_CLASS, 'synthetic_globals.py', generic_observer())
        original = klass.__dict__[O.METHODS[0]]
        setattr(klass, O.METHODS[0], types.FunctionType(original.__code__, dict(vars(module))))
        with self.assertRaises(H.Refusal): surface.observed_methods(lambda *args: None)
        surface, module, klass = observer_surface(SYNTHETIC_CLASS, 'synthetic_collision.py', generic_observer())
        vars(module)[O.CALLBACK] = object()
        with self.assertRaises(H.Refusal): surface.observed_methods(lambda *args: None)
        observer = generic_observer(); observer.METHODS = (O.METHODS[0], O.METHODS[0])
        surface, module, klass = observer_surface(SYNTHETIC_CLASS, 'synthetic_catalogue.py', observer)
        with self.assertRaises(H.Refusal): surface.observed_methods(lambda *args: None)


if __name__ == '__main__':
    unittest.main()
