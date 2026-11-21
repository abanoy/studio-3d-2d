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

import fresh_carrier_probe as worker


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


class OwnedMaterialReuseTests(unittest.TestCase):
    def fixture(self):
        class Material:
            def __init__(self, name):
                self.name, self.original, self.library = name, self, None
                self.props = {'full_path': name.lstrip('/').casefold()}
            def get(self, key, default=None): return self.props.get(key, default)
        class TinyPath:
            def __init__(self, value): self.value = value.replace('\\', '/').casefold()
            def __eq__(self, other): return type(other) is type(self) and self.value == other.value
        names = ('Owned A', 'Owned B', 'Owned C', 'Owned D')
        materials = tuple(Material(name) for name in names)
        factory = Material('Factory'); factory.props = {}
        bpy = types.SimpleNamespace(types=types.SimpleNamespace(Material=Material),
            data=types.SimpleNamespace(materials=[factory, *materials], images=[], libraries=[]))
        return bpy, materials, names, TinyPath

    def test_exact_preadmitted_refs_follow_ordinary_lookup_without_name_or_slot_edits(self):
        bpy, materials, names, path_type = self.fixture()
        before = tuple((value, value.name, dict(value.props)) for value in bpy.data.materials)
        report = worker.admit_existing_materials(bpy, materials, names, path_type)
        self.assertTrue(report['unique_actual_refs'])
        self.assertEqual(report['materials'], 4)
        self.assertEqual((report['material_renames'], report['material_swaps']), (0, 0))
        self.assertTrue(all(a[0] is b and a[1:] == (b.name, b.props) for a, b in zip(before, bpy.data.materials)))

    def test_wrong_full_path_or_missing_path_is_not_repaired(self):
        for value, code in (('foreign/path', 'B_MATERIAL_FULL_PATH_DIFFERS_FROM_ORDINARY_IMPORTER'),
                            (None, 'MATERIAL_LOOKUP_PATH_TYPE_OR_BUDGET')):
            bpy, materials, names, path_type = self.fixture()
            materials[1].props['full_path'] = value
            with self.assertRaisesRegex(worker.ControlledRefusal, '^' + code + '$'):
                worker.admit_existing_materials(bpy, materials, names, path_type)
            self.assertIs(materials[1].props['full_path'], value)

    def test_equal_full_path_foreign_candidate_refuses_even_when_material_names_differ(self):
        bpy, materials, names, path_type = self.fixture()
        foreign = type(materials[0])('Other Name')
        foreign.props['full_path'] = materials[0].props['full_path'].upper()
        bpy.data.materials.append(foreign)
        with self.assertRaisesRegex(worker.ControlledRefusal, 'ORDINARY_IMPORTER_MATERIAL_LOOKUP_AMBIGUOUS'):
            worker.admit_existing_materials(bpy, materials, names, path_type)
        self.assertIs(bpy.data.materials[-1], foreign)

    def test_same_valued_ref_outside_actual_domain_or_linked_ref_refuses(self):
        for mode in ('foreign', 'linked', 'duplicate'):
            bpy, materials, names, path_type = self.fixture()
            if mode == 'foreign': bpy.data.materials[1] = type(materials[0])(names[0])
            elif mode == 'linked': materials[0].library = object()
            else: bpy.data.materials.append(materials[0])
            with self.assertRaises(worker.ControlledRefusal):
                worker.admit_existing_materials(bpy, materials, names, path_type)

    def test_native_subset_is_ordered_independently_and_rejects_missing_or_ambiguous_names(self):
        _bpy, _materials, names, _path_type = self.fixture()
        metadata = dict(format='has_private_mdl49_material_skin_metadata_candidate_1',
            metadata=dict(materials=[dict(index=index, name=name) for index, name in enumerate(names)]))
        self.assertEqual(worker.select_owned_native_names(metadata, ('Unused', *reversed(names))), names)
        for available in (names[:3], (*names, names[0])):
            with self.assertRaises(worker.ControlledRefusal): worker.select_owned_native_names(metadata, available)
        metadata['metadata']['materials'][0]['index'] = False
        with self.assertRaises(worker.ControlledRefusal): worker.select_owned_native_names(metadata, names)

    def test_preparation_enumerates_then_appends_and_keeps_post_append_image_baseline(self):
        bpy, materials, names, path_type = self.fixture()
        events, result = [], {}
        factory_materials = tuple(bpy.data.materials[:1]); before_images = tuple(bpy.data.images)
        def enumerate_(actual, owned, summary_sink):
            self.assertIs(actual, bpy); events.append('empty-enumeration')
            summary_sink({'format': 'synthetic-empty'}); return {'material_names': ('Unused', *names)}
        def inspect_(actual, owned, actual_names, enumeration):
            events.append('material-append'); self.assertEqual(actual_names, names)
            bpy.data.images.extend((object(), object()))
            return dict(materials=materials, graphs=(), images=(), summary={'status': 'synthetic-private'}, retained_owned_source_library=None)
        enumeration = types.SimpleNamespace(enumerate_library=enumerate_)
        inspection = types.SimpleNamespace(inspect_material_library=inspect_, Refusal=type('Refusal', (ValueError,), {}))
        metadata = dict(format='has_private_mdl49_material_skin_metadata_candidate_1',
            metadata=dict(materials=[dict(index=index, name=name) for index, name in enumerate(names)]))
        private = worker.prepare_owned_materials(bpy, 'owned', metadata, enumeration, inspection, path_type, result)
        self.assertEqual(events, ['empty-enumeration', 'material-append'])
        self.assertEqual(before_images, ())
        self.assertEqual(len(private['post_append_images']), 2)
        self.assertTrue(all(a is b for a, b in zip(private['post_append_images'], bpy.data.images)))
        self.assertTrue(all(value is not factory_materials[0] for value in private['materials']))
        self.assertTrue(result['material_library_appended'])
        self.assertEqual(private['names'], names)

    def test_factory_material_baseline_accepts_returned_B_ref_but_postappend_baseline_refuses_it(self):
        mdl, obj, mesh, kwargs = SnapshotContractTests().fixture(late=True)
        actual = mdl.materials[0].bpy_material
        factory = type(actual)(); kwargs['baseline_materials'] = (factory,)
        snapshot = worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)
        self.assertIs(snapshot['slots'][0], actual)
        kwargs['baseline_materials'] = (factory, actual)
        with self.assertRaisesRegex(worker.ControlledRefusal, 'HOST_FRESH_MATERIAL_OWNERSHIP'):
            worker.capture_material_snapshot(mdl, obj, mesh, **kwargs)


class OwnedMaterialRecheckTests(unittest.TestCase):
    def fixture(self):
        import material_inspection as actual_inspection  # Pure definitions, no host/asset IO.
        bpy, materials, names, path_type = OwnedMaterialReuseTests().fixture()
        class Packed:
            def __init__(self, owner, pointer=40):
                self.id_data, self.pointer, self.raw, self.size, self.reads = owner, pointer, b'x' * 40, 40, 0
            def as_pointer(self): return self.pointer
            @property
            def data(self): self.reads += 1; return self.raw
        class Part:
            def __init__(self, owner, packed): self.id_data, self.packed_file, self.pointer = owner, packed, 41
            def as_pointer(self): return self.pointer
        class Image:
            def __init__(self):
                self.original, self.library, self.name, self.filepath = self, None, 'Synthetic', ''
                self.source, self.type, self.forbidden_getters = 'FILE', 'IMAGE', 0
                self.packed_file = Packed(self); self.packed_files = [Part(self, self.packed_file)]
            @property
            def size(self): self.forbidden_getters += 1; raise AssertionError('No ImBuf size read')
            @property
            def channels(self): self.forbidden_getters += 1; raise AssertionError('No ImBuf channels read')
            @property
            def pixels(self): self.forbidden_getters += 1; raise AssertionError('No pixel read')
        class Library:
            def __init__(self):
                self.original, self.library, self.pointer = self, None, 71
                self.filepath = r'C:\owned\material-source.blend'
                self.parent = self.packed_file = self.archive_parent_library = None
                self.is_archive, self.archive_libraries = False, []
            def as_pointer(self): return self.pointer
        image, library = Image(), Library()
        bpy.data.libraries.append(library)
        bpy.types.ImagePackedFile, bpy.types.PackedFile, bpy.types.Library = Part, Packed, Library
        bpy.data.images.append(image)
        for material in materials: material.tree, material.tone = object(), .5
        def graph(material, _types):
            return (dict(tree=material.tree, node_keys=(10,), link_keys=(11,), edge_keys=(12,), images=(image,)),
                    dict(name=material.name, tone=material.tone))
        inspection = types.SimpleNamespace(_graph=graph, _digest=actual_inspection._digest,
            _nonid_key=actual_inspection._nonid_key, _owned_library=actual_inspection._owned_library)
        graph_rows = [graph(material, bpy.types) for material in materials]
        part, packed = image.packed_files[0], image.packed_file
        private = dict(materials=materials, names=names, graphs=tuple(row[0] for row in graph_rows),
            summary=dict(graph_metadata_sha256=actual_inspection._digest([row[1] for row in graph_rows])),
            images=(dict(image=image, name=image.name, filepath=image.filepath,
                encoded_bytes=packed.size, encoded_sha256=hashlib.sha256(packed.raw).hexdigest(),
                packed_part_key=inspection._nonid_key(part, Part, image),
                packed_key=inspection._nonid_key(packed, Packed, image)),),
            library_snapshot=inspection._owned_library(library, bpy.types, library.filepath),
            post_append_libraries=tuple(bpy.data.libraries))
        return bpy, private, inspection, path_type, image, library, actual_inspection

    def test_post_import_recheck_preserves_graph_packed_and_owned_library_refs(self):
        bpy, private, inspection, path_type, image, library, _actual = self.fixture()
        worker.recheck_owned_materials(bpy, library.filepath, private, inspection, path_type)
        self.assertEqual(image.packed_file.reads, 1)
        self.assertEqual(image.forbidden_getters, 0)
        self.assertIs(private['library_snapshot']['library'], library)

    def test_additional_or_same_valued_replaced_library_refuses_before_resource_copy(self):
        for mode in ('additional', 'replacement'):
            bpy, private, inspection, path_type, image, library, _actual = self.fixture()
            foreign = type(library)()
            if mode == 'additional': bpy.data.libraries.append(foreign)
            else: bpy.data.libraries[0] = foreign
            with self.assertRaisesRegex(worker.ControlledRefusal, 'OWNED_B_LIBRARY_DOMAIN_CHANGED_AFTER_IMPORT'):
                worker.recheck_owned_materials(bpy, library.filepath, private, inspection, path_type)
            self.assertEqual((image.packed_file.reads, image.forbidden_getters), (0, 0))

    def test_graph_metadata_or_tree_ref_drift_refuses_before_packed_copy(self):
        for mode in ('metadata', 'tree'):
            bpy, private, inspection, path_type, image, library, _actual = self.fixture()
            if mode == 'metadata': private['materials'][0].tone = .25
            else: private['materials'][0].tree = object()
            with self.assertRaises(worker.ControlledRefusal):
                worker.recheck_owned_materials(bpy, library.filepath, private, inspection, path_type)
            self.assertEqual((image.packed_file.reads, image.forbidden_getters), (0, 0))

    def test_packed_pointer_or_size_drift_refuses_before_data_getter(self):
        for mode in ('pointer', 'size', 'bool'):
            bpy, private, inspection, path_type, image, library, _actual = self.fixture()
            if mode == 'pointer': image.packed_file.pointer += 1
            else: image.packed_file.size = True if mode == 'bool' else image.packed_file.size + 1
            with self.assertRaises(worker.ControlledRefusal):
                worker.recheck_owned_materials(bpy, library.filepath, private, inspection, path_type)
            self.assertEqual((image.packed_file.reads, image.forbidden_getters), (0, 0))

    def test_packed_payload_drift_refuses_without_image_buffer_acquisition(self):
        bpy, private, inspection, path_type, image, library, _actual = self.fixture()
        image.packed_file.raw = b'y' * 40
        with self.assertRaisesRegex(worker.ControlledRefusal, 'OWNED_B_PACKED_BYTES_CHANGED_AFTER_IMPORT'):
            worker.recheck_owned_materials(bpy, library.filepath, private, inspection, path_type)
        self.assertEqual((image.packed_file.reads, image.forbidden_getters), (1, 0))

    def test_packed_budget_refusal_precedes_byte_getter_even_with_consistent_reported_size(self):
        bpy, private, inspection, path_type, image, library, _actual = self.fixture()
        private['images'][0]['encoded_bytes'] = image.packed_file.size = 64 * 1024 * 1024 + 1
        with self.assertRaisesRegex(worker.ControlledRefusal, 'OWNED_B_PACKED_RECHECK_BUDGET'):
            worker.recheck_owned_materials(bpy, library.filepath, private, inspection, path_type)
        self.assertEqual((image.packed_file.reads, image.forbidden_getters), (0, 0))

    def test_owned_library_raw_path_pointer_or_dependency_drift_refuses(self):
        for mode in ('raw_path', 'pointer', 'parent'):
            bpy, private, inspection, path_type, image, library, actual = self.fixture()
            if mode == 'raw_path': library.filepath = r'c:\OWNED\material-source.blend'
            elif mode == 'pointer': library.pointer += 1
            else: library.parent = object()
            with self.assertRaises((worker.ControlledRefusal, actual.Refusal)):
                worker.recheck_owned_materials(bpy, r'C:\owned\material-source.blend', private, inspection, path_type)
            self.assertEqual(image.forbidden_getters, 0)


class ResolvedHostWiringTests(unittest.TestCase):
    def fixture(self, refusal=False):
        bpy,materials,names,path_type=OwnedMaterialReuseTests().fixture()
        for material in materials:material.props['full_path']='native/directory/'+material.name.casefold()
        events=[];native=object();mdl=object()
        metadata=dict(format='has_private_mdl49_material_skin_metadata_candidate_1',
            metadata=dict(materials=[dict(index=i,name=name) for i,name in enumerate(names)]))
        def enum(actual,owned,summary_sink):
            events.append('enumeration');summary_sink({'status':'synthetic'});return {'material_names':names}
        def inspect(actual,owned,selected,enumeration):
            events.append('inspection')
            return dict(materials=materials,graphs=(),images=(),summary={'status':'synthetic'},retained_owned_source_library=None)
        class ProfileRefusal(ValueError):
            def __init__(self,code,summary):super().__init__(code);self.summary=summary
        class Witness:
            def __init__(self,actual_native,actual_metadata,actual_mdl,actual_materials,**kwargs):
                events.append('witness')
                assert actual_native is native and actual_metadata is metadata and actual_mdl is mdl
                assert all(a is b for a,b in zip(actual_materials,materials))
                assert all(a is b for a,b in zip(kwargs['material_domain_supplier'](),bpy.data.materials))
                self.summary=dict(format='synthetic-counts',metadata_rows_observed=4,full_path_missing=2)
                if refusal:raise ProfileRefusal('PRELOADED_FULL_PATH_MISSING',self.summary)
        enumeration=types.SimpleNamespace(enumerate_library=enum)
        inspection=types.SimpleNamespace(inspect_material_library=inspect,Refusal=type('Refusal',(ValueError,),{}))
        profile=types.SimpleNamespace(ResolvedMaterialPaths=Witness,ProfileRefusal=ProfileRefusal)
        return bpy,materials,events,native,metadata,mdl,enumeration,inspection,profile,path_type

    def test_preloaded_path_preparation_uses_exact_refs_without_bare_gate_or_metadata_writes(self):
        bpy,materials,events,native,metadata,mdl,enum,inspection,profile,path_type=self.fixture()
        before=tuple(dict(value.props) for value in materials);result={}
        with patch.object(worker,'admit_existing_materials',side_effect=AssertionError('bare path gate not v3')):
            private=worker.prepare_owned_resolved_materials(bpy,'owned',native,metadata,mdl,enum,inspection,
                profile,path_type,object,result)
        self.assertEqual(events,['enumeration','inspection','witness'])
        self.assertTrue(all(a is b for a,b in zip(private['materials'],materials)))
        self.assertEqual(tuple(value.props for value in materials),before)
        self.assertTrue(result['readonly_preloaded_material_adaptation']['no_metadata_writes'])

    def test_all_row_diagnostic_survives_path_preflight_refusal_without_claiming_model_import(self):
        bpy,materials,events,native,metadata,mdl,enum,inspection,profile,path_type=self.fixture(refusal=True)
        result={}
        with self.assertRaisesRegex(worker.ControlledRefusal,'PRELOADED_FULL_PATH_MISSING'):
            worker.prepare_owned_resolved_materials(bpy,'owned',native,metadata,mdl,enum,inspection,
                profile,path_type,object,result)
        self.assertEqual(result['native_material_path_witness']['metadata_rows_observed'],4)
        self.assertEqual(result['native_material_path_witness']['full_path_missing'],2)
        self.assertNotIn('sourceio_import_executed',result)
        self.assertEqual(events,['enumeration','inspection','witness'])

    def test_runtime_resolver_code_and_alias_attestation_refuses_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);paths=('blender_bindings/models/materials.py','blender_bindings/utils/bpy_utils.py')
            sources=('def resolve_model_material(cm,mdl,name): return None\ndef get_model_material_names(cm,mdl): return resolve_model_material(cm,mdl,"x")\n',
                     'def get_or_create_material(name,full_path): return None\n')
            tiny=type('TinyPath',(),{});bpy=types.SimpleNamespace(data=types.SimpleNamespace(materials=[]))
            modules=[];reads={}
            for relative,source in zip(paths,sources):
                path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source.encode())
                module=types.ModuleType(relative);module.__file__=str(path)
                module.__dict__.update(TinyPath=tiny,bpy=bpy)
                exec(compile(source,str(path),'exec'),module.__dict__)
                raw,stamp=worker.pinned_read(path,len(source.encode()),hashlib.sha256(source.encode()).hexdigest())
                reads['sourceio/'+relative]=(path,len(raw),hashlib.sha256(raw).hexdigest(),stamp);modules.append(module)
            resolver,utils=modules
            importer=types.SimpleNamespace(get_model_material_names=resolver.get_model_material_names,
                get_or_create_material=utils.get_or_create_material)
            with patch.object(worker,'SOURCEIO',root):
                result={};actual=worker.attest_preloaded_resolution(importer,resolver,utils,tiny,bpy,reads,result)
                self.assertIs(actual[0],resolver.resolve_model_material)
                self.assertEqual(result['preloaded_resolver_runtime_attestation']['genuine_functions'],3)
                importer.get_model_material_names=lambda *args:None
                with self.assertRaisesRegex(worker.ControlledRefusal,'ACTUAL_RESOLUTION_HELPER_ALIASES_DIFFER'):
                    worker.attest_preloaded_resolution(importer,resolver,utils,tiny,bpy,reads,{})


class CarrierBoundaryTests(unittest.TestCase):
    def container(self):
        matrix=lambda:[[float(i==j) for j in range(4)] for i in range(4)]
        objects=[types.SimpleNamespace(matrix_world=matrix()) for _ in range(2)]
        return types.SimpleNamespace(objects=objects,armature=types.SimpleNamespace(matrix_world=matrix()))

    def test_actual_identity_frame_records_only_pinned_yup_transport(self):
        frame=worker.admit_identity_normal_frame(self.container())
        self.assertEqual(frame['signed_axis_permutation'],[1,3,-2])
        self.assertTrue(frame['mesh_world_identity'])
        self.assertFalse(frame['source_unit_conversion_changed'])
        self.assertFalse(frame['six_foot_normalization_applied'])

    def test_nonidentity_or_nontyped_matrix_cannot_invent_normal_transport(self):
        for mode in ('translate','scale','integer','armature'):
            container=self.container()
            if mode=='armature':container.armature.matrix_world[0][0]=-1.0
            elif mode=='integer':container.objects[0].matrix_world[0][0]=1
            else:container.objects[0].matrix_world[0][3 if mode=='translate' else 0]=2.0
            with self.assertRaisesRegex(worker.ControlledRefusal,'NORMAL_FRAME_NONIDENTITY_WORLD_UNQUALIFIED'):
                worker.admit_identity_normal_frame(container)

    def test_frame_rejects_repeated_mesh_object_or_missing_model(self):
        container=self.container();container.objects[1]=container.objects[0]
        with self.assertRaisesRegex(worker.ControlledRefusal,'NORMAL_FRAME_TWO_ACTUAL_OBJECTS_REQUIRED'):
            worker.admit_identity_normal_frame(container)
        container.objects=[]
        with self.assertRaises(worker.ControlledRefusal):worker.admit_identity_normal_frame(container)

    def environment(self, cold_failure=False, export_failure=False):
        events=[]
        class KnownRefusal(ValueError):pass
        class ColdRefusal(ValueError):
            def __init__(self):super().__init__('COLD_BUDGET_REFUSAL');self.summary={'format':'safe_cold_counts','size_getter_attempts':0}
        def acquire(*args):
            events.append('cold')
            if cold_failure:raise ColdRefusal()
            return [],dict(image_buffer_getters_used=True)
        def export(*args,**kwargs):
            events.append('export')
            if export_failure:raise KnownRefusal('AUTHENTICATED_RESOURCE_REFUSAL')
            kwargs['activity'].update(exporter_invoked=True,operator_preflight_observed=True,
                scene_or_registration_restoration_failed=False)
            relation=b'[]\n'
            return dict(private_relation_bytes=relation,private_relation_sha256=hashlib.sha256(relation).hexdigest(),
                export_observation={'source_normal_max_error_unchanged':2e-5})
        ordinary=types.SimpleNamespace(Refusal=KnownRefusal)
        cold=types.SimpleNamespace(Refusal=ColdRefusal,acquire_packed_png_buffers=acquire)
        exporter=types.SimpleNamespace(Refusal=KnownRefusal,export_once=export)
        modules=(ordinary,ordinary,object(),object(),cold,exporter)
        private=dict(images=(),materials=(),path_witness=types.SimpleNamespace(summary={'status':'checked'}))
        binding=types.SimpleNamespace(facts={'models':{'a':{'slots':(0,1)},'b':{'slots':(2,3)}}})
        return events,modules,private,binding

    def invoke(self,target,events,modules,private,binding,result):
        with patch.object(worker,'load_carrier_helpers',return_value=modules), \
             patch.object(worker,'recheck_resolved_material_resources',side_effect=lambda *args:events.append('resource_recheck')):
            worker.perform_carrier_export(object(),object(),self.container(),object(),{'a':{},'b':{}},object(),
                binding,private,object(),object(),'owned',target,{},result)

    def test_export_boundary_rechecks_resources_after_warm_and_after_export(self):
        events,modules,private,binding=self.environment();result={}
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder);self.invoke(target,events,modules,private,binding,result)
            self.assertEqual((target/'PRIVATE_PRIMITIVE_IDS.json').read_bytes(),b'[]\n')
        self.assertEqual(events,['cold','resource_recheck','export','resource_recheck'])
        self.assertNotIn('private_relation_bytes',result['carrier_export'])
        self.assertEqual(result['carrier_export']['export_observation']['source_normal_threshold_unchanged'],2e-5)
        self.assertFalse(result['carrier_export']['export_observation']['source_normal_error_measured'])
        self.assertTrue(result['carrier_written'])
        self.assertFalse(result['C_external_access_absence_proven'])

    def test_cold_refusal_keeps_safe_counts_and_never_attempts_export(self):
        events,modules,private,binding=self.environment(cold_failure=True);result={}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(worker.ControlledRefusal,'COLD_BUDGET_REFUSAL'):
                self.invoke(Path(folder),events,modules,private,binding,result)
        self.assertEqual(events,['cold'])
        self.assertEqual(result['bounded_image_buffer_readiness']['size_getter_attempts'],0)
        self.assertNotIn('exporter_attempted',result)

    def test_authenticated_export_gate_code_is_retained_without_success_claim(self):
        events,modules,private,binding=self.environment(export_failure=True);result={}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(worker.ControlledRefusal,'AUTHENTICATED_RESOURCE_REFUSAL'):
                self.invoke(Path(folder),events,modules,private,binding,result)
        self.assertEqual(events,['cold','resource_recheck','export'])
        self.assertTrue(result['exporter_attempted'])
        self.assertNotIn('carrier_export',result)
        self.assertNotIn('status',result)

    def test_existing_private_relation_is_never_overwritten(self):
        events,modules,private,binding=self.environment();result={}
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder);path=target/'PRIVATE_PRIMITIVE_IDS.json';path.write_bytes(b'owned earlier proof')
            with self.assertRaises(FileExistsError):self.invoke(target,events,modules,private,binding,result)
            self.assertEqual(path.read_bytes(),b'owned earlier proof')
        self.assertNotIn('status',result)

    def test_authenticated_cycle_reuses_exact_resource_module_and_refusal_class(self):
        import sys
        names=('experiments','experiments.carrier_input_domain_20261118',
            'experiments.carrier_input_domain_20261118.semantic_compare','private_carrier_gather_binding',
            'private_carrier_extract_observer','export_hook_proposal','resource_gate_proposal',
            'shared_image_cache_proposal','private_carrier_cold_readiness','private_carrier_export')
        original={name:sys.modules.pop(name) for name in names if name in sys.modules}
        try:
            buffers={role:(worker.HERE/spec[0]).read_bytes() for role,spec in worker.CARRIER_MODULES.items()}
            hook,resources,_observer,_binder,_cold,_export=worker.load_carrier_helpers(buffers)
            self.assertIs(hook.shared_images.R,resources)
            self.assertIs(hook.shared_images,sys.modules['shared_image_cache_proposal'])
            self.assertIs(resources.Refusal,hook.Refusal)
        finally:
            for name in names:sys.modules.pop(name,None)
            sys.modules.update(original)

    def test_existing_authenticated_namespace_refuses_before_helper_execution(self):
        import sys
        with patch.dict(sys.modules,{'experiments':types.ModuleType('experiments')}), \
             patch.object(worker,'loaded_source',side_effect=AssertionError('must not execute')):
            with self.assertRaisesRegex(worker.ControlledRefusal,'COLD_CARRIER_NAMESPACE_REQUIRED'):
                worker.load_carrier_helpers({})


if __name__ == '__main__':
    unittest.main()
