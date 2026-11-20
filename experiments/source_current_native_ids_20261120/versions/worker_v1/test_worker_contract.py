"""UNRUN worker bootstrap contracts; no Blender/SourceIO import or native data.

Root-only synthetic temporary files contain empty/arbitrary text. The only
project helper read is the separately hash-verified pure AST instrumentation.
"""
import hashlib
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


if __name__ == '__main__':
    unittest.main()
