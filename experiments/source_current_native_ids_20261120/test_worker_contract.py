"""UNRUN worker bootstrap contracts; no Blender/SourceIO import or native data.

Root-only synthetic temporary files contain empty/arbitrary text. The only
project helper read is the separately hash-verified pure AST instrumentation.
"""
import hashlib
import ast
import json
import tempfile
import types
import unittest
from pathlib import Path

import fresh_current_id_probe as worker


class FileContractTests(unittest.TestCase):
    def test_exact_locked_empty_sdk_file_is_admitted(self):
        with tempfile.TemporaryDirectory(prefix='has-current-id-synthetic-') as folder:
            path = Path(folder) / 'empty.py'
            path.write_bytes(b'')
            raw, before = worker.pinned_read(path, 0, hashlib.sha256(b'').hexdigest())
            self.assertEqual(raw, b'')
            _raw, after = worker.pinned_read(path, 0, hashlib.sha256(b'').hexdigest())
            self.assertEqual(before, after)

    def test_count_type_and_hash_mismatch_refuse_without_coercion(self):
        with tempfile.TemporaryDirectory(prefix='has-current-id-synthetic-') as folder:
            path = Path(folder) / 'synthetic.py'
            path.write_bytes(b'x')
            for count, digest in ((True, hashlib.sha256(b'x').hexdigest()), (1, '0' * 64), (0, hashlib.sha256(b'').hexdigest())):
                with self.assertRaises(worker.ControlledRefusal): worker.pinned_read(path, count, digest)


SYNTHETIC_IMPORTER = '''def import_model(cm, mdl, vtx, vvd, options):
    model, mesh_obj, mesh_data, vertices, vtx_vertices = mdl
    mesh_data.normals_split_custom_set_from_vertices(vertices['normal'])
    mesh_data.validate()
    return mesh_obj
'''


class CloneContractTests(unittest.TestCase):
    def setUp(self):
        raw, _before = worker.pinned_read(worker.INSTRUMENTATION, *worker.INSTRUMENTATION_PIN)
        self.instrument = types.ModuleType('synthetic_importer_instrumentation')
        self.instrument.__file__ = str(worker.INSTRUMENTATION)
        exec(compile(raw, str(worker.INSTRUMENTATION), 'exec', dont_inherit=True), self.instrument.__dict__)
        self.module = types.ModuleType('synthetic_native_importer')
        self.module.__file__ = '<synthetic_native_importer.py>'
        exec(compile(SYNTHETIC_IMPORTER, self.module.__file__, 'exec', dont_inherit=True), self.module.__dict__)

    def test_four_real_boundaries_clone_without_patching_original(self):
        events = []
        class SyntheticMesh:
            def normals_split_custom_set_from_vertices(self, normals): events.append(('setter', normals))
            def validate(self): events.append(('validate',))
        model, obj, mesh, normals, mapping = object(), object(), SyntheticMesh(), object(), [0, 1, 2]
        vertices = {'normal': normals}
        def callback(phase, actual_model, actual_obj, actual_mesh, actual_vertices, actual_mapping):
            self.assertIs(actual_model, model); self.assertIs(actual_obj, obj); self.assertIs(actual_mesh, mesh)
            self.assertIs(actual_vertices, vertices); self.assertIs(actual_mapping, mapping)
            events.append((phase,))
        original = self.module.import_model
        found, clone, proof = worker.observed_clone(self.module, SYNTHETIC_IMPORTER, self.instrument, callback)
        self.assertIs(found, original)
        self.assertIs(clone(None, (model, obj, mesh, vertices, mapping), None, None, None), obj)
        self.assertEqual([event[0] for event in events], ['before_setter', 'setter', 'after_setter',
                                                        'before_validate', 'validate', 'after_validate'])
        self.assertIs(self.module.import_model, original)
        self.assertTrue(proof['original_function_AST_restored'])

    def test_runtime_original_body_mismatch_refuses_before_call(self):
        altered = compile('def import_model(cm, mdl, vtx, vvd, options):\n    return None\n', self.module.__file__, 'exec')
        namespace = {}
        exec(altered, namespace)
        self.module.import_model.__code__ = namespace['import_model'].__code__
        with self.assertRaises(worker.ControlledRefusal):
            worker.observed_clone(self.module, SYNTHETIC_IMPORTER, self.instrument, lambda *args: None)

    def test_real_pinned_source_uses_full_module_context_without_sdk_execution(self):
        # Source compilation only. Do NOT import/exec the SourceIO module/body.
        raw, _before = worker.pinned_read(worker.IMPORTER, *worker.IMPORTER_PIN)
        source = raw.decode('utf-8')
        module = types.ModuleType('synthetic_full_source_context')
        module.__file__ = str(worker.IMPORTER)
        full = worker.direct_function_code(compile(raw, module.__file__, 'exec', dont_inherit=True, optimize=-1), 'import_model')
        definition = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'import_model'][0]
        isolated = worker.direct_function_code(compile(ast.fix_missing_locations(ast.Module(body=[definition], type_ignores=[])),
                                                       module.__file__, 'exec', dont_inherit=True, optimize=-1), 'import_model')
        self.assertNotEqual(full, isolated)  # Exact173a Root CPython313 reproducer.
        module.import_model = types.FunctionType(full, module.__dict__)
        diagnostics = {}
        original, clone, proof = worker.observed_clone(module, source, self.instrument, lambda *args: None,
                                                       diagnostics=diagnostics)
        self.assertIs(original, module.import_model)
        self.assertTrue(diagnostics['importer_code_attestation']['original_vs_full_source']['complete_code_equal'])
        self.assertTrue(diagnostics['importer_code_attestation']['raw_full_source_vs_full_AST']['complete_code_equal'])
        self.assertFalse(diagnostics['importer_code_attestation']['full_source_vs_isolated_AST']['complete_code_equal'])
        self.assertTrue(diagnostics['importer_code_attestation']['complete_module_AST_inverse_exact'])
        self.assertFalse(diagnostics['importer_code_attestation']['module_top_level_executed_for_clone'])
        self.assertNotIn('_HAS_NORMAL_OBSERVER', module.__dict__)
        self.assertIsNot(clone.__globals__, module.__dict__)
        self.assertTrue(proof['original_function_AST_restored'])

    def test_top_level_imports_and_side_effects_are_never_executed_for_clone(self):
        source = 'from math import *\n' + SYNTHETIC_IMPORTER + 'raise RuntimeError("synthetic top-level MUST NOT EXECUTE")\n'
        module = types.ModuleType('synthetic_unexecuted_full_module')
        module.__file__ = '<synthetic_unexecuted_full_module.py>'
        original_code = worker.direct_function_code(compile(source, module.__file__, 'exec', dont_inherit=True), 'import_model')
        module.import_model = types.FunctionType(original_code, module.__dict__)
        original, clone, _proof = worker.observed_clone(module, source, self.instrument, lambda *args: None)
        self.assertIs(module.import_model, original)
        self.assertNotIn('sin', module.__dict__)
        self.assertNotIn('sin', clone.__globals__)
        self.assertIn(self.instrument.CALLBACK, clone.__globals__)

    def test_defaults_annotations_and_genuine_globals_are_preserved_without_reevaluation(self):
        source = '''events = ['module']
def default_factory():
    events.append('default')
    return object()
def annotation_factory():
    events.append('annotation')
    return int
DEFAULT = default_factory()
GLOBAL_MARKER = object()
def import_model(cm, mdl, vtx, vvd, options=DEFAULT, *, label: annotation_factory()=DEFAULT):
    model, mesh_obj, mesh_data, vertices, vtx_vertices = mdl
    mesh_data.normals_split_custom_set_from_vertices(vertices['normal'])
    mesh_data.validate()
    return GLOBAL_MARKER
'''
        module = types.ModuleType('synthetic_metadata_preservation')
        module.__file__ = '<synthetic_metadata_preservation.py>'
        exec(compile(source, module.__file__, 'exec', dont_inherit=True), module.__dict__)
        self.assertEqual(module.events, ['module', 'default', 'annotation'])
        original, clone, _proof = worker.observed_clone(module, source, self.instrument, lambda *args: None)
        self.assertEqual(module.events, ['module', 'default', 'annotation'])
        self.assertIs(clone.__defaults__, original.__defaults__)
        self.assertIs(clone.__kwdefaults__['label'], original.__kwdefaults__['label'])
        self.assertIsNot(clone.__kwdefaults__, original.__kwdefaults__)
        self.assertEqual(clone.__annotations__, original.__annotations__)
        self.assertIsNot(clone.__annotations__, original.__annotations__)
        self.assertIs(clone.__globals__['GLOBAL_MARKER'], module.GLOBAL_MARKER)
        self.assertIsNot(clone.__globals__, module.__dict__)
        self.assertNotIn(self.instrument.CALLBACK, module.__dict__)

    def test_code_only_mismatch_diagnostic_still_refuses_and_publishes_no_constants(self):
        altered = compile('def import_model(cm, mdl, vtx, vvd, options):\n    return "synthetic-private-constant-marker"\n',
                          self.module.__file__, 'exec', dont_inherit=True)
        self.module.import_model.__code__ = worker.direct_function_code(altered, 'import_model')
        diagnostics = {}
        with self.assertRaisesRegex(worker.ControlledRefusal, 'IMPORTER_RUNTIME_FULL_MODULE_CODE_DIFFERS'):
            worker.observed_clone(self.module, SYNTHETIC_IMPORTER, self.instrument, lambda *args: None,
                                  diagnostics=diagnostics)
        attestation = diagnostics['importer_code_attestation']
        self.assertFalse(attestation['original_vs_full_source']['complete_code_equal'])
        self.assertTrue(attestation['original_vs_full_source']['differing_fields'])
        encoded = json.dumps(diagnostics)
        self.assertNotIn('synthetic-private-constant-marker', encoded)
        self.assertNotIn(SYNTHETIC_IMPORTER, encoded)

    def test_complete_module_inverse_refuses_unrelated_instrumentation_changes(self):
        genuine = self.instrument.observed_import_function
        def changed(source):
            tree, proof = genuine(source)
            tree.body[0].body.append(ast.Expr(value=ast.Constant(value='unrelated injected source')))
            ast.fix_missing_locations(tree)
            return tree, proof
        fake = types.SimpleNamespace(CALLBACK=self.instrument.CALLBACK, observed_import_function=changed)
        original = self.module.import_model
        with self.assertRaisesRegex(worker.ControlledRefusal, 'COMPLETE_MODULE_OBSERVER_AST_INVERSE_DIFFERS'):
            worker.observed_clone(self.module, SYNTHETIC_IMPORTER, fake, lambda *args: None)
        self.assertIs(self.module.import_model, original)


if __name__ == '__main__':
    unittest.main()
