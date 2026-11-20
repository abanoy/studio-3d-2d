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
from unittest.mock import patch

import fresh_material_binding_probe as worker


class SnapshotContractTests(unittest.TestCase):
    def fixture(self, late=False, strings=False):
        class Material:
            def __init__(self): self.name = 'synthetic_material'; self.original = self
            def get(self, name): return self.name if name == 'full_path' else None
        class SourceMaterial: pass
        class Body: pass
        class Model: pass
        class SourceMesh: pass
        class Object:
            def get(self, key): return self.properties.get(key)
        class Mesh: pass
        class Slot: pass
        class Polygon: pass
        class IDGroup(dict): pass
        material, source = Material(), SourceMaterial()
        source.name, source.flags, source.used, source.bpy_material = material.name, 0, 1, material
        native_mesh = SourceMesh()
        native_mesh.material_index, native_mesh.vertex_index_start, native_mesh.vertex_count = 0, 0, 3
        model, blank, body = Model(), Model(), Body()
        model.name, model.vertex_offset, model.vertex_count, model.meshes = 'synthetic', 0, 3, [native_mesh]
        blank.name, blank.vertex_offset, blank.vertex_count, blank.meshes = 'blank', 0, 0, []
        body.name, body.models = 'body', [model, blank]
        mdl = types.SimpleNamespace(materials=[source], skin_groups=[[source]], body_parts=[body])
        obj, mesh = Object(), Mesh()
        obj.data, obj.original, mesh.original = mesh, obj, mesh
        mesh.materials = [material] if late else []
        obj.material_slots = []
        if late:
            slot = Slot(); slot.material, slot.link, slot.id_data = material, 'DATA', obj
            obj.material_slots.append(slot)
        polygon = Polygon()
        polygon.id_data, polygon.index, polygon.loop_start, polygon.loop_total, polygon.material_index = mesh, 0, 0, 3, 0
        mesh.polygons = [polygon]
        obj.properties = dict(active_skin='0', model_type='s1')
        if late: obj.properties['skin_groups'] = IDGroup({'0': [material.name if strings else material]})
        classes = dict(source_material=SourceMaterial, source_body=Body, source_model=Model,
                       source_mesh=SourceMesh, object=Object, mesh=(Mesh,), material=Material,
                       material_slot=Slot, polygon=Polygon)
        kwargs = dict(classes=classes, baseline_materials=(), material_domain=(material,),
                      object_domain=(obj,), mesh_domain=(mesh,), idprop_types=dict(group=IDGroup, sequences=(list, tuple)))
        return mdl, obj, mesh, kwargs

    def test_early_snapshot_retains_actual_source_refs_and_blank_model_with_empty_slots(self):
        mdl, obj, mesh, kwargs = self.fixture()
        actual = worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        self.assertEqual(set(actual), {'source_materials', 'source_skins', 'source_parts', 'slots', 'object_slots',
                                       'faces', 'skin_groups', 'active_skin', 'model_type'})
        self.assertIs(actual['source_materials'][0][0], mdl.materials[0])
        self.assertIs(actual['source_materials'][0][4], mdl.materials[0].bpy_material)
        self.assertIs(actual['source_parts'][0][2][1][0], mdl.body_parts[0].models[1])
        self.assertEqual(actual['source_parts'][0][2][1][3], 0)
        self.assertEqual(actual['slots'], ())
        self.assertEqual(actual['object_slots'], ())
        self.assertIsNone(actual['skin_groups'])
        self.assertEqual(actual['faces'], ((0, 0, 3, 0),))

    def test_late_snapshot_reads_actual_data_slots_and_pointer_skin_branch(self):
        mdl, obj, mesh, kwargs = self.fixture(late=True)
        actual = worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        material = mdl.materials[0].bpy_material
        self.assertIs(actual['slots'][0], material)
        self.assertIs(actual['object_slots'][0], material)
        self.assertIs(actual['skin_groups'][0][1][0], material)

    def test_string_skin_branch_is_captured_as_string_without_identity_invention(self):
        mdl, obj, mesh, kwargs = self.fixture(late=True, strings=True)
        actual = worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        self.assertEqual(actual['skin_groups'], (('0', (mdl.materials[0].name,)),))
        self.assertIs(type(actual['skin_groups'][0][1][0]), str)

    def test_object_linked_slot_is_refused_without_mutation(self):
        mdl, obj, mesh, kwargs = self.fixture(late=True)
        obj.material_slots[0].link = 'OBJECT'
        with self.assertRaisesRegex(worker.ControlledRefusal, 'HOST_DATA_LINKED_OBJECT_SLOT'):
            worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        self.assertEqual(obj.material_slots[0].link, 'OBJECT')

    def test_reused_baseline_material_is_refused(self):
        mdl, obj, mesh, kwargs = self.fixture()
        kwargs['baseline_materials'] = (mdl.materials[0].bpy_material,)
        with self.assertRaisesRegex(worker.ControlledRefusal, 'HOST_FRESH_MATERIAL_OWNERSHIP'):
            worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)

    def test_actual_rna_owner_and_domain_are_required(self):
        for field in ('object_domain', 'mesh_domain', 'material_domain'):
            mdl, obj, mesh, kwargs = self.fixture()
            kwargs[field] = ()
            with self.assertRaises(worker.ControlledRefusal):
                worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        mdl, obj, mesh, kwargs = self.fixture(late=True)
        mesh.polygons[0].id_data = obj
        with self.assertRaisesRegex(worker.ControlledRefusal, 'HOST_ACTUAL_POLYGON_OWNERSHIP'):
            worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)

    def test_duck_typed_source_and_skin_containers_refuse_before_callbacks(self):
        mdl, obj, mesh, kwargs = self.fixture()
        mdl.materials[0] = types.SimpleNamespace(**mdl.materials[0].__dict__)
        with self.assertRaisesRegex(worker.ControlledRefusal, 'HOST_ACTUAL_SOURCE_MATERIAL_TYPE'):
            worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        mdl, obj, mesh, kwargs = self.fixture(late=True)
        class Poison:
            def keys(self): raise AssertionError('untyped protocol must not be invoked')
        obj.properties['skin_groups'] = Poison()
        with self.assertRaisesRegex(worker.ControlledRefusal, 'HOST_IDPROPERTY_SKIN_GROUP'):
            worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)

    def test_snapshot_does_not_modify_source_or_properties_or_slot_refs(self):
        mdl, obj, mesh, kwargs = self.fixture(late=True)
        source_before = tuple(mdl.materials)
        props_before = dict(obj.properties)
        slots_before = tuple(mesh.materials)
        worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        self.assertEqual(tuple(mdl.materials), source_before)
        self.assertEqual(obj.properties, props_before)
        self.assertTrue(all(left is right for left, right in zip(mesh.materials, slots_before)))


class FileContractTests(unittest.TestCase):
    def test_old_current_id_request_format_is_refused_before_any_native_scope(self):
        with tempfile.TemporaryDirectory(prefix='has-material-binding-synthetic-') as folder:
            project = Path(folder)
            (project / 'output').mkdir()
            path = project / 'output/old_request.json'
            raw = json.dumps(dict(format='has_fresh_current_native_id_request_1',
                                  phase='ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED', private_arrays_public=False)).encode()
            path.write_bytes(raw)
            with patch.object(worker, 'PROJECT', project):
                with self.assertRaisesRegex(worker.ControlledRefusal, 'ROOT_LEASE_SCOPE'):
                    worker.request_read(path, hashlib.sha256(raw).hexdigest())

    def test_material_helper_alias_refuses_before_source_read_or_execution(self):
        lease = dict(files={'metadata_reader':dict(path=str(worker.HERE / 'unapproved_metadata.py'),
                                                   bytes=worker.METADATA_PIN[0], sha256=worker.METADATA_PIN[1])})
        with patch.object(worker, 'safe', side_effect=lambda value: Path(value)), \
             patch.object(worker, 'pinned_read', side_effect=AssertionError('must not read helper')) as reader, \
             patch.object(worker, 'loaded_source', side_effect=AssertionError('must not execute helper')) as loader:
            with self.assertRaisesRegex(worker.ControlledRefusal, 'PINNED_MATERIAL_HELPER_ALIAS_OR_IDENTITY'):
                worker.verify_file_table(lease, {})
            reader.assert_not_called()
            loader.assert_not_called()

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
