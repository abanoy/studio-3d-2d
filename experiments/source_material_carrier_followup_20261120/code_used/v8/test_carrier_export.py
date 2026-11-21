"""Pure fake scene/operator tests. No bpy/NumPy/native input or GPU import.

Synthetic RNA references, F32 arrays and temporary byte files test orchestration
only. Fake hooks/session are explicitly not an exporter/fidelity qualification.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import struct
import tempfile
import types
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('carrier_export_under_test', HERE / 'carrier_export.py')
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


class Array:
    def __init__(self, values): self.values = list(values)
    def tobytes(self): return struct.pack('<' + 'f' * len(self.values), *self.values)


class NP:
    float32 = object()
    def empty(self, count, *, dtype):
        if dtype is not self.float32: raise AssertionError('wrong dtype')
        return Array([0.0] * count)
    def asarray(self, values, *, dtype):
        if dtype is not self.float32: raise AssertionError('wrong dtype')
        return Array(float(value) for value in values)


class AttributeData:
    def __init__(self, count): self.values = [0.0] * count
    def __len__(self): return len(self.values)
    def foreach_get(self, field, target):
        if field != 'value': raise AssertionError('wrong field')
        if len(target.values) != len(self.values): raise ValueError('wrong buffer length')
        target.values[:] = self.values
    def foreach_set(self, field, source):
        if field != 'value': raise AssertionError('wrong field')
        if len(source.values) != len(self.values): raise ValueError('wrong buffer length')
        self.values[:] = source.values


class FloatAttribute:
    serial = 1000
    def __init__(self, owner, name, data_type, domain):
        self.id_data, self.name, self.data_type, self.domain = owner, name, data_type, domain
        FloatAttribute.serial += 1
        self.pointer = FloatAttribute.serial
        self.data = AttributeData(len(owner.coordinates))
    def as_pointer(self): return self.pointer


class Attributes:
    def __init__(self, owner): self.owner, self.rows, self.fail_new, self.fresh_get = owner, [], False, False
    def __len__(self): return len(self.rows)
    def __iter__(self): return iter(tuple(self.rows))
    def get(self, name):
        row = next((row for row in self.rows if row.name == name), None)
        if row is None or not self.fresh_get: return row
        wrapper = FloatAttribute.__new__(FloatAttribute)
        wrapper.__dict__ = row.__dict__
        return wrapper
    def new(self, *, name, type, domain):
        if self.fail_new: raise RuntimeError('synthetic attribute allocation failure')
        if self.get(name) is not None: raise AssertionError('would overwrite existing source attribute')
        row = FloatAttribute(self.owner, name, type, domain)
        self.rows.append(row)
        return row
    def remove(self, row):
        actual = next((value for value in self.rows if type(row) is type(value) and
            row.id_data is value.id_data and row.as_pointer() == value.as_pointer()), None)
        if actual is None: raise ValueError('RNA attribute is not a member')
        self.rows.remove(actual)


class Mesh:
    def __init__(self, name, count):
        self.name, self.original = name, self
        self.coordinates = tuple((float(index), 1.0, 2.0) for index in range(count))
        self.attributes = Attributes(self)
        self.materials = (object(), object())
        self.attributes.new(name='source_attribute', type='FLOAT', domain='POINT')


def matrix(x=0.0):
    return [[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


class Obj:
    def __init__(self, bpy, name, mesh=None, x=0.0):
        self.bpy, self.name, self.data, self.original = bpy, name, mesh, self
        self.matrix_world, self.selected = matrix(x), False
    def select_set(self, selected):
        if selected and all(row is not self for row in self.bpy.context.scene.objects):
            raise RuntimeError('cannot select an object outside the scene')
        self.selected = selected


class Links:
    def __init__(self, scene): self.scene = scene
    def link(self, obj):
        if any(row is obj for row in self.scene.objects): raise AssertionError('duplicate owned link')
        self.scene.objects.append(obj)
    def unlink(self, obj):
        self.scene.objects.remove(obj)
        obj.selected = False


class Scene:
    def __init__(self):
        self.objects = []
        self.collection = types.SimpleNamespace(objects=Links(self))


class ViewLayer:
    def __init__(self): self.objects, self.updates = types.SimpleNamespace(active=None), 0
    def update(self): self.updates += 1


class Context:
    def __init__(self):
        self.scene, self.view_layer = Scene(), ViewLayer()
        self.preferences = types.SimpleNamespace(addons={})
    @property
    def selected_objects(self): return [obj for obj in self.scene.objects if obj.selected]


class Ledger:
    def __init__(self, objects): self.records = {obj.name: dict(obj=obj, mesh=obj.data) for obj in objects}
    def _snapshot(self, fact, actual, early):
        if early is not False or actual != fact['expected']:
            raise E.Refusal('SYNTHETIC_CURRENT_POINT_STATE_CHANGED')


def snapshot(obj, mesh): return (obj.name, mesh, mesh.coordinates)


class Fixture:
    def __init__(self, *, armature_linked=False):
        self.bpy = types.SimpleNamespace(types=types.SimpleNamespace(FloatAttribute=FloatAttribute), context=Context())
        self.np = NP()
        self.old = [Obj(self.bpy, 'original_a'), Obj(self.bpy, 'original_b')]
        self.bpy.context.scene.objects.extend(self.old)
        self.old[0].select_set(True)
        self.bpy.context.view_layer.objects.active = self.old[0]
        self.objects = [Obj(self.bpy, 'a', Mesh('a_mesh', 2), 2.0),
                        Obj(self.bpy, 'b', Mesh('b_mesh', 1), -3.0)]
        self.armature = Obj(self.bpy, 'actual_armature', x=4.0)
        if armature_linked: self.bpy.context.scene.objects.append(self.armature)
        self.container = types.SimpleNamespace(armature=self.armature)
        self.ledger = Ledger(self.objects)
        self.facts = {obj.name: dict(ids=((7, 19) if index == 0 else (42,)),
                                   expected=snapshot(obj, obj.data)) for index, obj in enumerate(self.objects)}
        self.primitive_counts = {'a': 2, 'b': 2}
        self.before_objects = tuple(self.bpy.context.scene.objects)
        self.before_selection = tuple(self.bpy.context.selected_objects)
        self.before_attributes = tuple(tuple(obj.data.attributes.rows) for obj in self.objects)
        self.scene = None

    def make(self):
        self.scene = E.CarrierScene(self.bpy, self.np, self.container, self.ledger,
            self.facts, snapshot, self.primitive_counts)
        return self.scene

    def restored(self, case):
        case.assertEqual(tuple(self.bpy.context.scene.objects), self.before_objects)
        case.assertEqual(tuple(self.bpy.context.selected_objects), self.before_selection)
        case.assertIs(self.bpy.context.view_layer.objects.active, self.old[0])
        for obj, original in zip(self.objects, self.before_attributes):
            case.assertEqual(tuple(obj.data.attributes.rows), original)
            case.assertEqual(snapshot(obj, obj.data), self.facts[obj.name]['expected'])


class SceneTests(unittest.TestCase):
    def test_unlinked_armature_and_meshes_are_linked_selected_then_exactly_restored(self):
        f = Fixture(); scene = f.make(); scene.install()
        self.assertEqual(set(id(obj) for obj in f.bpy.context.selected_objects),
                         set(id(obj) for obj in [*f.objects, f.armature]))
        self.assertIs(f.bpy.context.view_layer.objects.active, f.armature)
        self.assertTrue(any(obj is f.armature for obj in f.bpy.context.scene.objects))
        self.assertTrue(scene.point_admission())
        scene.close(); f.restored(self)

    def test_already_linked_armature_is_retained_and_not_duplicated(self):
        f = Fixture(armature_linked=True); scene = f.make(); scene.install()
        self.assertEqual(sum(obj is f.armature for obj in f.bpy.context.scene.objects), 1)
        scene.close(); f.restored(self)

    def test_carrier_contains_exact_one_based_native_f32_words_and_actual_refs(self):
        f = Fixture(); scene = f.make(); scene.install()
        for obj in f.objects: obj.data.attributes.fresh_get = True
        for row, obj in zip(scene.entries, f.objects):
            attr = obj.data.attributes.get(E.CARRIER)
            self.assertEqual((attr.name, attr.data_type, attr.domain), (E.CARRIER, 'FLOAT', 'POINT'))
            expected = tuple(value + 1 for value in f.facts[obj.name]['ids'])
            self.assertEqual(tuple(attr.data.values), expected)
            self.assertEqual(Array(attr.data.values).tobytes(), struct.pack('<' + 'f' * len(expected), *expected))
            self.assertIs(row['object'], obj)
            self.assertIs(row['mesh'], obj.data)
        self.assertTrue(scene.point_admission())
        admissions = scene.admissions()
        self.assertIs(admissions[0]['object'], f.objects[0])
        self.assertEqual(admissions[0]['joined_source_ids'], [7, 19])
        self.assertEqual(admissions[0]['primitive_count'], 2)
        scene.close(); f.restored(self)

    def test_reserved_case_alias_is_refused_without_overwriting(self):
        f = Fixture()
        collision = f.objects[0].data.attributes.new(name=E.CARRIER.lower(), type='FLOAT', domain='POINT')
        with self.assertRaises(E.Refusal): f.make()
        self.assertIs(f.objects[0].data.attributes.get(E.CARRIER.lower()), collision)

    def test_invalid_duplicate_bool_negative_or_unbounded_native_ids_refuse(self):
        for ids in ((7, 7), (True,), (-1,), (200000,)):
            with self.subTest(ids=ids):
                f = Fixture(); f.facts['a']['ids'] = ids
                with self.assertRaises(E.Refusal): f.make()

    def test_primitive_count_domain_and_complete_closed_profile_refuse(self):
        for counts in ({'a': True, 'b': 3}, {'a': 0, 'b': 4}, {'a': 2}, {'a': 1, 'b': 1}):
            with self.subTest(counts=counts):
                f = Fixture(); f.primitive_counts = counts
                with self.assertRaises(E.Refusal): f.make()

    def test_current_geometry_drift_refuses_before_carrier_install(self):
        f = Fixture(); scene = f.make()
        f.objects[0].data.coordinates = ((9.0, 0.0, 0.0),) * 2
        with self.assertRaises(E.Refusal): scene.install()
        self.assertTrue(all(obj.data.attributes.get(E.CARRIER) is None for obj in f.objects))

    def test_object_mesh_and_armature_world_drift_are_not_repaired(self):
        for target in ('object', 'armature', 'mesh'):
            with self.subTest(target=target):
                f = Fixture(); scene = f.make()
                if target == 'object': f.objects[0].matrix_world[0][3] += 1.0
                elif target == 'armature': f.armature.matrix_world[1][3] += 1.0
                else: f.objects[0].data = Mesh('foreign', 2)
                with self.assertRaises(E.Refusal): scene.point_admission()

    def test_carrier_value_drift_refuses_instead_of_reselecting_ids(self):
        f = Fixture(); scene = f.make(); scene.install()
        attr = f.objects[0].data.attributes.get(E.CARRIER)
        attr.data.values[0] += 1.0
        with self.assertRaises(E.Refusal): scene.point_admission()
        scene.close(); f.restored(self)

    def test_attribute_inventory_drift_is_not_hidden_by_carrier_removal(self):
        f = Fixture(); scene = f.make(); scene.install()
        f.objects[0].data.attributes.new(name='unexpected', type='FLOAT', domain='POINT')
        with self.assertRaises(E.Refusal): scene.point_admission()
        with self.assertRaises(E.Refusal): scene.close()
        self.assertIsNotNone(f.objects[0].data.attributes.get('unexpected'))

    def test_partial_second_attribute_failure_restores_first_and_owned_scene_links(self):
        f = Fixture(); scene = f.make(); f.objects[1].data.attributes.fail_new = True
        with self.assertRaises(RuntimeError): scene.install()
        scene.close(); f.restored(self)

    def test_foreign_replacement_carrier_is_not_deleted_during_cleanup(self):
        f = Fixture(); scene = f.make(); scene.install()
        mesh = f.objects[0].data
        own = mesh.attributes.get(E.CARRIER); mesh.attributes.remove(own)
        foreign = mesh.attributes.new(name=E.CARRIER, type='FLOAT', domain='POINT')
        with self.assertRaises(E.Refusal): scene.close()
        self.assertIs(mesh.attributes.get(E.CARRIER), foreign)

    def test_source_attribute_wrapper_pointer_drift_refuses(self):
        f = Fixture(); scene = f.make()
        f.objects[0].data.attributes.rows[0].pointer += 100
        with self.assertRaises(E.Refusal): scene.point_admission()

    def test_exact_matrix_words_preserve_nonidentity_translations_and_reject_nonfinite(self):
        self.assertEqual(E.matrix_words(matrix(2.5))[0][3], float(2.5).hex())
        bad = matrix(); bad[1][2] = float('nan')
        with self.assertRaises(E.Refusal): E.matrix_words(bad)
        bad = matrix(); bad[0][0] = 1
        with self.assertRaises(E.Refusal): E.matrix_words(bad)


class FakeHook:
    PINS = {'addon': ('__init__.py', 'fake'), 'search': ('blender/search.py', 'fake'),
            'encode': ('blender/encode.py', 'fake'), 'gltf': ('io/gltf.py', 'fake')}
    def __init__(self, fixture, *, finish_error=False):
        self.fixture, self.finish_error = fixture, finish_error
        self.sessions, self.surfaces = [], []
        parent = self
        class Session:
            def __init__(self, surface, admissions, np, resources, point_admission, options):
                self.installs, self.finishes, self.preflights = 0, 0, 0
                self.options, self.admissions, self.resources = options, admissions, resources
                self.point_admission = point_admission
                parent.sessions.append(self)
            def pre_export_hook(self, settings):
                self.preflights += 1
                self.point_admission()
            @contextmanager
            def install(self, addon, enabled_names):
                self.installs += 1
                self.point_admission()
                yield self
                self.point_admission()
            def finish(self, raw, expected):
                self.finishes += 1
                if self.preflights != 1: raise E.Refusal('SYNTHETIC_MISSING_GENUINE_PREFLIGHT')
                if parent.finish_error: raise E.Refusal('SYNTHETIC_LATCHED_FINAL_RELATION_FAILURE')
                if hashlib.sha256(raw).hexdigest() != expected: raise AssertionError('wrong observed output pin')
                relation = {(index, primitive): tuple(value + 1 for value in admission['joined_source_ids'])
                            for index, admission in enumerate(self.admissions)
                            for primitive in range(admission['primitive_count'])}
                return relation, dict(fake_observation_only=True, exporter_qualified=False)
        self.ExportHookSession = Session

    def PinnedSurface(self, modules, observer, binder, *, shared_binary_module):
        result = types.SimpleNamespace(modules=modules, observer=observer, binder=binder,
                                       binary=shared_binary_module)
        self.surfaces.append(result)
        return result

    def extension_inventory(self, names): return tuple(names)

class ExportTests(unittest.TestCase):
    def fake_export_environment(self, *, operator_result=None, finish_error=False):
        f = Fixture()
        hook = FakeHook(f, finish_error=finish_error)
        calls = []
        addon = types.SimpleNamespace(__name__='io_scene_gltf2')
        module_map = {'io_scene_gltf2': addon,
            'io_scene_gltf2.blender.search': object(), 'io_scene_gltf2.blender.encode': object(),
            'io_scene_gltf2.io.gltf': object(), 'io_scene_gltf2.io.exp.binary_data': object()}
        def enable(*, module):
            calls.append(('enable', module)); f.bpy.context.preferences.addons[module] = object()
            return {'FINISHED'}
        def disable(*, module):
            calls.append(('disable', module)); del f.bpy.context.preferences.addons[module]
            return {'FINISHED'}
        def gltf(**kwargs):
            calls.append(('operator', kwargs))
            if set(id(obj) for obj in f.bpy.context.selected_objects) != set(id(obj) for obj in [*f.objects, f.armature]):
                raise AssertionError('operator selection was not the actual admitted objects/armature')
            hook.sessions[-1].pre_export_hook({})
            Path(kwargs['filepath']).write_bytes(b'glTF' + bytes(24))
            return {'FINISHED'} if operator_result is None else operator_result
        f.bpy.ops = types.SimpleNamespace(preferences=types.SimpleNamespace(addon_enable=enable, addon_disable=disable),
                                          export_scene=types.SimpleNamespace(gltf=gltf))
        resources = types.SimpleNamespace(SimplePackedResources=lambda *args, **kwargs:
            dict(args=args, kwargs=kwargs, fake_resource_only=True))
        return f, hook, resources, module_map, calls

    def invoke(self, path, f, hook, resources, activity=None):
        if activity is None: activity = {}
        return E.export_once(f.bpy, f.np, f.container, f.ledger, f.facts, snapshot,
            f.primitive_counts, tuple(object() for _ in range(4)), [], hook, resources,
            object(), object(), path, owned_output=path.parent, activity=activity)

    def test_operator_profile_has_explicit_narrow_kwargs_and_matching_observed_settings(self):
        kwargs, options = E.operator_profile(Path('synthetic.glb'))
        pairs = {'export_format': ('gltf_format', 'GLB'), 'use_selection': ('gltf_selected', True),
            'export_animations': ('gltf_animations', False), 'export_current_frame': ('gltf_current_frame', True),
            'export_attributes': ('gltf_attributes', True), 'export_shared_accessors': ('gltf_shared_accessors', False),
            'export_extras': ('gltf_extras', False), 'export_apply': ('gltf_apply', False),
            'export_skins': ('gltf_skins', True), 'export_keep_originals': ('gltf_keep_original_textures', False),
            'export_image_format': ('gltf_image_format', 'AUTO'), 'export_unused_images': ('gltf_unused_images', False),
            'export_unused_textures': ('gltf_unused_textures', False), 'export_image_add_webp': ('gltf_add_webp', False),
            'export_image_webp_fallback': ('gltf_webp_fallback', False)}
        for operator_key, (observed_key, expected) in pairs.items():
            self.assertIs(type(kwargs[operator_key]), type(expected)); self.assertEqual(kwargs[operator_key], expected)
            self.assertIs(type(options[observed_key]), type(expected)); self.assertEqual(options[observed_key], expected)
        self.assertFalse(kwargs['export_cameras']); self.assertFalse(kwargs['export_lights'])
        self.assertFalse(kwargs['export_morph']); self.assertFalse(kwargs['export_tangents'])

    def test_exactly_one_operator_and_session_return_bound_relation_then_restore_scene(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'carrier.glb'
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                result = self.invoke(path, f, hook, resources, activity)
            self.assertEqual(sum(kind == 'operator' for kind, _ in calls), 1)
            self.assertEqual(result['operator_invocations'], 1)
            self.assertEqual(result['carrier_glb_bytes'], 28)
            relation = json.loads(result['private_relation_bytes'])
            self.assertEqual(len(relation), 4)
            self.assertEqual(relation[0]['one_based_source_ids'], [8, 20])
            self.assertEqual(relation[-1]['one_based_source_ids'], [43])
            self.assertEqual(hook.sessions[0].installs, 1)
            self.assertEqual(hook.sessions[0].finishes, 1)
            self.assertTrue(activity['operator_call_attempted'])
            self.assertTrue(activity['exporter_invoked'])
            self.assertTrue(activity['operator_preflight_observed'])
            self.assertTrue(activity['carrier_written'])
            self.assertFalse(activity['scene_or_registration_restoration_failed'])
            self.assertFalse(result['export_observation']['exporter_qualified'])
            self.assertEqual(f.bpy.context.preferences.addons, {})
            f.restored(self)

    def test_existing_output_refuses_before_import_or_scene_changes(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'carrier.glb'; path.write_bytes(b'original synthetic output')
            with patch.object(E.importlib, 'import_module', side_effect=AssertionError('should not import')):
                with self.assertRaises(E.Refusal): self.invoke(path, f, hook, resources)
            self.assertEqual(path.read_bytes(), b'original synthetic output')
            self.assertEqual(calls, [])
            f.restored(self)

    def test_cancelled_operator_refuses_and_restores_owned_links_attributes_and_registration(self):
        f, hook, resources, modules, calls = self.fake_export_environment(operator_result={'CANCELLED'})
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(E.Refusal): self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources)
            self.assertEqual(sum(kind == 'operator' for kind, _ in calls), 1)
            self.assertEqual(f.bpy.context.preferences.addons, {})
            f.restored(self)

    def test_latched_final_relation_failure_remains_failure_even_when_file_exists(self):
        f, hook, resources, modules, calls = self.fake_export_environment(finish_error=True)
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'carrier.glb'
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(E.Refusal): self.invoke(path, f, hook, resources, activity)
            self.assertTrue(path.is_file())
            self.assertEqual(sum(kind == 'operator' for kind, _ in calls), 1)
            self.assertEqual(f.bpy.context.preferences.addons, {})
            self.assertTrue(activity['carrier_written'])
            self.assertTrue(activity['exporter_invoked'])
            self.assertFalse(activity['scene_or_registration_restoration_failed'])
            f.restored(self)

    def test_preexisting_enabled_exporter_registration_is_not_disabled(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        original = object(); f.bpy.context.preferences.addons['io_scene_gltf2'] = original
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources)
        self.assertIs(f.bpy.context.preferences.addons['io_scene_gltf2'], original)
        self.assertFalse(any(kind in ('enable', 'disable') for kind, _ in calls))
        f.restored(self)

    def test_all_seventeen_pinned_module_routes_and_separate_binary_module_are_forwarded(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        expected = {'addon': '__init__.py', 'extractor': 'blender/exp/primitive_extract.py',
            'primitives': 'blender/exp/primitives.py', 'obj_data': 'blender/exp/obj_data.py',
            'nodes': 'blender/exp/nodes.py', 'exporter': 'blender/exp/exporter.py',
            'cache': 'blender/exp/cache.py', 'export': 'blender/exp/export.py',
            'gltf': 'io/com/gltf2_io.py', 'user_extensions': 'io/exp/user_extensions.py',
            'materials': 'blender/exp/material/materials.py', 'texture_info': 'blender/exp/material/texture_info.py',
            'texture': 'blender/exp/material/texture.py', 'image': 'blender/exp/material/image.py',
            'encode': 'blender/exp/material/encode_image.py', 'search': 'blender/exp/material/search_node_tree.py',
            'utils': 'blender/com/gltf2_blender_utils.py'}
        hook.PINS = {key: (relative, 'fake') for key, relative in expected.items()}
        actual_modules = {}
        for key, relative in expected.items():
            name = 'io_scene_gltf2' if key == 'addon' else 'io_scene_gltf2.' + relative[:-3].replace('/', '.')
            modules.setdefault(name, object()); actual_modules[key] = modules[name]
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources)
        surface = hook.surfaces[0]
        self.assertEqual(set(surface.modules), set(expected))
        self.assertEqual(len(surface.modules), 17)
        self.assertTrue(all(surface.modules[key] is value for key, value in actual_modules.items()))
        self.assertIs(surface.binary, modules['io_scene_gltf2.io.exp.binary_data'])
        f.restored(self)

    def test_resource_setup_refusal_does_not_claim_actual_operator_or_preflight(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        def refuse(*args, **kwargs): raise E.Refusal('SYNTHETIC_RESOURCE_PREFLIGHT_REFUSED')
        resources.SimplePackedResources = refuse
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(E.Refusal):
                    self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertFalse(activity.get('operator_call_attempted', False))
        self.assertFalse(activity.get('exporter_invoked', False))
        self.assertFalse(activity.get('operator_preflight_observed', False))
        self.assertFalse(any(kind == 'operator' for kind, _ in calls))
        self.assertEqual(f.bpy.context.preferences.addons, {})
        f.restored(self)

    def test_operator_call_without_observed_preflight_cannot_gain_an_invocation_receipt(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        def no_preflight(**kwargs):
            calls.append(('operator', kwargs)); Path(kwargs['filepath']).write_bytes(b'glTF' + bytes(24))
            return {'FINISHED'}
        f.bpy.ops.export_scene.gltf = no_preflight
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(E.Refusal):
                    self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertTrue(activity['operator_call_attempted'])
        self.assertFalse(activity.get('exporter_invoked', False))
        self.assertFalse(activity.get('operator_preflight_observed', False))
        f.restored(self)

    def test_primary_operator_failure_survives_secondary_registration_cleanup_error(self):
        f, hook, resources, modules, calls = self.fake_export_environment(operator_result={'CANCELLED'})
        def fail_disable(**kwargs): raise RuntimeError('secondary registration cleanup')
        f.bpy.ops.preferences.addon_disable = fail_disable
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(E.Refusal) as error:
                    self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertEqual(str(error.exception), 'ORDINARY_GLTF_OPERATOR_NOT_FINISHED')
        self.assertTrue(activity['scene_or_registration_restoration_failed'])
        self.assertEqual(activity['secondary_cleanup_code'], 'OWNED_EXPORT_SCENE_OR_REGISTRATION_RESTORATION_FAILED')
        f.restored(self)

    def test_successful_body_cannot_return_success_after_registration_cleanup_failure(self):
        f, hook, resources, modules, calls = self.fake_export_environment()
        def fail_disable(**kwargs): raise RuntimeError('secondary registration cleanup')
        f.bpy.ops.preferences.addon_disable = fail_disable
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(RuntimeError):
                    self.invoke(Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertTrue(activity['scene_or_registration_restoration_failed'])
        self.assertTrue(activity['carrier_written'])
        f.restored(self)


def file_info(**changes):
    values = dict(st_dev=4, st_ino=42, st_size=28, st_mtime_ns=1234567, st_nlink=1,
                  st_mode=stat.S_IFREG | 0o600, st_file_attributes=0x20)
    values.update(changes)
    return types.SimpleNamespace(**values)


class FakeParent:
    def __init__(self, info=None):
        self.info = info or file_info(st_mode=stat.S_IFDIR | 0o700)
        self.parents = ()
    def lstat(self): return self.info


class FakeStream:
    def __init__(self, raw): self.raw, self.reads = raw, []
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def fileno(self): return 99
    def read(self, maximum): self.reads.append(maximum); return self.raw


class FakePath:
    def __init__(self, parent, *, before=None, after=None, raw=None):
        self.parent, self.name = parent, 'carrier.glb'
        self.before = before or file_info()
        self.after = after or self.before
        self.stats, self.opens = 0, 0
        self.stream = FakeStream(b'glTF' + bytes(24) if raw is None else raw)
    def lstat(self):
        self.stats += 1
        return self.before if self.stats == 1 else self.after
    def open(self, mode):
        if mode != 'rb': raise AssertionError('reader must not write')
        self.opens += 1
        return self.stream


class OutputTests(unittest.TestCase):
    def test_fresh_path_refuses_wrong_parent_or_name_before_traversal(self):
        parent = FakeParent(); path = FakePath(parent); path.name = 'other.glb'
        with self.assertRaises(E.Refusal): E.fresh_owned_carrier_path(path, parent)
        self.assertEqual(path.stats, 0)
        path.name = 'carrier.glb'
        with self.assertRaises(E.Refusal): E.fresh_owned_carrier_path(path, FakeParent())
        self.assertEqual(path.stats, 0)

    def test_fresh_path_refuses_parent_reparse_or_symlink_before_target(self):
        for info in (file_info(st_mode=stat.S_IFDIR | 0o700, st_file_attributes=0x400),
                     file_info(st_mode=stat.S_IFLNK | 0o700)):
            with self.subTest(mode=info.st_mode):
                parent = FakeParent(info); path = FakePath(parent)
                with self.assertRaises(E.Refusal): E.fresh_owned_carrier_path(path, parent)
                self.assertEqual(path.stats, 0)

    def test_broken_target_link_is_existing_and_never_followed(self):
        parent = FakeParent(); path = FakePath(parent, before=file_info(st_mode=stat.S_IFLNK | 0o700))
        with self.assertRaises(E.Refusal): E.fresh_owned_carrier_path(path, parent)
        self.assertEqual(path.opens, 0)

    def test_reader_accepts_one_immutable_regular_owned_file_with_bounded_read(self):
        parent = FakeParent(); path = FakePath(parent)
        with patch.object(E.os, 'fstat', return_value=file_info()):
            raw = E.read_owned_carrier(path, parent)
        self.assertEqual(raw, b'glTF' + bytes(24))
        self.assertEqual(path.stream.reads, [E.MAX_GLB + 1])

    def test_reader_refuses_reparse_hardlink_symlink_or_budget_before_open(self):
        bad_rows = (file_info(st_file_attributes=0x400), file_info(st_nlink=2),
                    file_info(st_mode=stat.S_IFLNK | 0o600), file_info(st_size=27),
                    file_info(st_size=E.MAX_GLB + 1))
        for info in bad_rows:
            with self.subTest(info=vars(info)):
                parent = FakeParent(); path = FakePath(parent, before=info)
                with self.assertRaises(E.Refusal): E.read_owned_carrier(path, parent)
                self.assertEqual(path.opens, 0)

    def test_reader_refuses_each_opened_identity_or_attribute_drift_before_read(self):
        for key, value in (('st_dev', 5), ('st_ino', 43), ('st_size', 29), ('st_mtime_ns', 1234568),
                           ('st_nlink', 2), ('st_file_attributes', 0x21)):
            with self.subTest(key=key):
                parent = FakeParent(); path = FakePath(parent)
                with patch.object(E.os, 'fstat', return_value=file_info(**{key: value})):
                    with self.assertRaises(E.Refusal): E.read_owned_carrier(path, parent)
                self.assertEqual(path.stream.reads, [])

    def test_reader_refuses_final_inode_change_or_truncated_read(self):
        parent = FakeParent(); path = FakePath(parent, after=file_info(st_ino=99))
        with patch.object(E.os, 'fstat', return_value=file_info()):
            with self.assertRaises(E.Refusal): E.read_owned_carrier(path, parent)
        path = FakePath(parent, raw=b'short')
        with patch.object(E.os, 'fstat', return_value=file_info()):
            with self.assertRaises(E.Refusal): E.read_owned_carrier(path, parent)

    def test_only_reviewed_recall_hint_is_normalized_in_output_stamp(self):
        self.assertEqual(E.output_stamp(file_info(st_file_attributes=0x40020)), E.output_stamp(file_info()))
        self.assertNotEqual(E.output_stamp(file_info(st_file_attributes=0x420)), E.output_stamp(file_info()))
        self.assertNotEqual(E.output_stamp(file_info(st_file_attributes=0x21)), E.output_stamp(file_info()))



class LatchDiagnosticTests(unittest.TestCase):
    def test_wrapped_sdk_runtime_error_keeps_primary_and_reports_only_fixed_latch_stage(self):
        f, hook, resources, modules, calls = ExportTests.fake_export_environment(self)
        primary = RuntimeError('PRIVATE texture filename and owner values')
        def fail(**kwargs):
            calls.append(('operator', kwargs))
            session = hook.sessions[-1]
            session.pre_export_hook({})
            session.latch = types.SimpleNamespace(first=('shared_image_cache_texture_info', 'Refusal'), count=1)
            raise primary
        f.bpy.ops.export_scene.gltf = fail
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(RuntimeError) as caught:
                    ExportTests.invoke(self, Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertIs(caught.exception, primary)
        self.assertEqual(activity['export_failure_latch'], dict(format='has_carrier_safe_latch_failure_1',
            status='LATCHED_FAILURE', latched_failure_observed=True,
            stage='shared_image_cache_texture_info', exception_category='Refusal', failures=1))
        self.assertNotIn('PRIVATE', json.dumps(activity['export_failure_latch']))
        self.assertTrue(activity['operator_call_attempted']); self.assertTrue(activity['operator_preflight_observed'])
        self.assertFalse(activity['carrier_output_present_unqualified'])
        self.assertFalse(activity['scene_or_registration_restoration_failed'])
        self.assertEqual(f.bpy.context.preferences.addons, {})
        f.restored(self)

    def test_wrapped_runtime_failure_without_latch_does_not_invent_a_stage_or_disclose_message(self):
        f, hook, resources, modules, calls = ExportTests.fake_export_environment(self)
        primary = RuntimeError('PRIVATE no-latch object paths')
        def fail(**kwargs):
            hook.sessions[-1].pre_export_hook({})
            raise primary
        f.bpy.ops.export_scene.gltf = fail
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(RuntimeError) as caught:
                    ExportTests.invoke(self, Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertIs(caught.exception, primary)
        self.assertEqual(activity['export_failure_latch'], dict(format='has_carrier_safe_latch_failure_1',
                         status='NO_LATCHED_FAILURE', latched_failure_observed=False))
        self.assertNotIn('PRIVATE', json.dumps(activity['export_failure_latch']))
        self.assertFalse(activity['scene_or_registration_restoration_failed'])
        f.restored(self)

    def test_unknown_latch_metadata_is_sanitized_without_property_or_private_type_name_reads(self):
        for first, count in ((('PRIVATE filename', 'Refusal'), 1),
                             (('shared_image_cache_texture_info', 'Refusal'), True),
                             (['PRIVATE filename', 'PrivateOwnerType'], 1),
                             (('shared_image_cache_texture_info', 'Refusal'), 65537)):
            value = E.public_latch_failure(types.SimpleNamespace(latch=types.SimpleNamespace(first=first, count=count)))
            self.assertEqual(value['status'], 'UNADMITTED_LATCH_METADATA')
            self.assertNotIn('stage', value); self.assertNotIn('exception_category', value)
            self.assertNotIn('PRIVATE', json.dumps(value)); self.assertNotIn('PrivateOwnerType', json.dumps(value))
        value = E.public_latch_failure(types.SimpleNamespace(latch=types.SimpleNamespace(
            first=('shared_image_cache_texture_info', 'PrivateOwnerType'), count=1)))
        self.assertEqual(value['exception_category'], 'OtherError')
        self.assertNotIn('PrivateOwnerType', json.dumps(value))
        touches = []
        class PropertyTrap:
            @property
            def latch(self):
                touches.append(True)
                raise RuntimeError('PRIVATE property should never be read')
        self.assertEqual(E.public_latch_failure(PropertyTrap())['status'], 'NO_LATCHED_FAILURE')
        self.assertEqual(touches, [])
        self.assertEqual(E.public_latch_failure(None)['status'], 'SESSION_NOT_CREATED')

    def test_diagnostic_failure_cannot_replace_primary_or_skip_scene_and_registration_restoration(self):
        f, hook, resources, modules, calls = ExportTests.fake_export_environment(self)
        primary = RuntimeError('original SDK failure')
        def fail(**kwargs): raise primary
        f.bpy.ops.export_scene.gltf = fail
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]), \
                 patch.object(E, 'public_latch_failure', side_effect=MemoryError('secondary diagnostic allocation')):
                with self.assertRaises(RuntimeError) as caught:
                    ExportTests.invoke(self, Path(temporary) / 'carrier.glb', f, hook, resources, {})
        self.assertIs(caught.exception, primary)
        self.assertEqual(f.bpy.context.preferences.addons, {})
        f.restored(self)


def safe_material_report():
    kinds = {key: 'NONE' for key in E._MATERIAL_FIELD_KEYS}
    kinds.update(extensions='DICT', pbr_metallic_roughness='OTHER', base_color_texture='OTHER')
    guards = {key: True for key in E._MATERIAL_GUARD_KEYS}
    guards.update(extensions_is_none=False, extensions_is_exact_empty_dict=False)
    observation = {key: True for key in E._MATERIAL_OBS_BOOLS}
    observation.update({key: 0 for key in E._MATERIAL_OBS_COUNTS})
    observation.update(source_graph_matches=1, captured_image_socket_count=2,
        positive_info_identity_matches=1, positive_info_graph_key_matches=1,
        field_types=kinds, guards=guards,
        extensions=dict(field_type='DICT', count=1, count_in_budget=True,
            unknown_name_count=0, non_string_name_count=0,
            known=[dict(name='KHR_materials_ior', value_type='OTHER', plain_wrapper_fields=True,
                wrapper_name_matches=True, payload_type='DICT', payload_count=1,
                payload_count_in_budget=True, known_field_types={'ior': 'FLOAT'},
                unknown_field_count=0, non_string_field_count=0)]))
    return dict(format='has_strict_material_guard_failure_observation_1', status='OBSERVED',
        failures=1, failure_count_capped=False, first_refusal_code='unsupported_gathered_material_profile',
        observation=observation, original_strict_failure_preserved=True,
        material_admission_changed=False, resource_equivalence_qualified=False)


def material_session(report):
    class Owned: pass
    session, resource = Owned(), Owned()
    session.resources = resource
    resource.public_material_failure = report
    return session


class MaterialDiagnosticTests(unittest.TestCase):
    def test_safe_report_is_freshly_copied_without_payload_or_mutable_expectation_aliases(self):
        original = safe_material_report()
        frozen = json.loads(json.dumps(original))
        result = E.public_material_failure(material_session(original))
        self.assertEqual(result, frozen)
        self.assertIsNot(result, original); self.assertIsNot(result['observation'], original['observation'])
        self.assertIsNot(result['observation']['extensions']['known'], original['observation']['extensions']['known'])
        original['observation']['extensions']['known'][0]['known_field_types']['ior'] = 'PRIVATE factor value'
        original['failures'] = 4
        self.assertEqual(result, frozen)
        self.assertEqual(result['failures'], 1)
        self.assertEqual(result['observation']['extensions']['known'][0]['known_field_types'], {'ior': 'FLOAT'})
        self.assertFalse(result['material_admission_changed']); self.assertFalse(result['resource_equivalence_qualified'])

    def test_unknown_names_payloads_claims_types_and_counts_are_rejected_without_echo(self):
        changes = (
            lambda r: r.__setitem__('private_payload', ['PRIVATE owner material']),
            lambda r: r.__setitem__('first_refusal_code', 'PRIVATE exception text'),
            lambda r: r.__setitem__('failures', True),
            lambda r: r.__setitem__('failure_count_capped', 1),
            lambda r: r.__setitem__('material_admission_changed', True),
            lambda r: r['observation'].__setitem__('positive_info_identity_matches', -1),
            lambda r: r['observation']['field_types'].__setitem__('PRIVATE field', 'FLOAT'),
            lambda r: r['observation']['guards'].__setitem__('source_graph_is_unique', 1),
            lambda r: r['observation']['extensions']['known'][0].__setitem__('name', 'PRIVATE extension'),
            lambda r: r['observation']['extensions']['known'][0].__setitem__('payload', {'ior': 1.45}),
            lambda r: r['observation']['extensions']['known'][0]['known_field_types'].__setitem__('ior', 1.45),
            lambda r: r['observation']['extensions'].__setitem__('count', 2),
        )
        for mutate in changes:
            report = safe_material_report(); mutate(report)
            value = E.public_material_failure(material_session(report))
            self.assertEqual(value, dict(format='has_carrier_material_diagnostic_admission_1',
                status='UNADMITTED_RESOURCE_DIAGNOSTIC', copied=False))
            self.assertNotIn('PRIVATE', json.dumps(value)); self.assertNotIn('1.45', json.dumps(value))

    def test_unavailable_absent_and_uninspected_fields_preserve_their_meaning(self):
        self.assertIsNone(E.public_material_failure(material_session(None)))
        self.assertIsNone(E.public_material_failure(None))
        unavailable = safe_material_report(); unavailable.update(status='UNAVAILABLE', observation=None)
        self.assertEqual(E.public_material_failure(material_session(unavailable)), unavailable)
        unavailable['observation'] = safe_material_report()['observation']
        self.assertEqual(E.public_material_failure(material_session(unavailable))['status'], 'UNADMITTED_RESOURCE_DIAGNOSTIC')
        report = safe_material_report(); observation = report['observation']
        observation.update(actual_material_type=False, fields_available=False, field_types={}, guards={},
            extensions=dict(field_type='NONE', count=0, count_in_budget=False, known=[],
                            unknown_name_count=0, non_string_name_count=0))
        self.assertEqual(E.public_material_failure(material_session(report)), report)
        report['failures'], report['failure_count_capped'] = 128, True
        self.assertEqual(E.public_material_failure(material_session(report))['failures'], 128)
        report['failures'] = 127
        self.assertEqual(E.public_material_failure(material_session(report))['status'], 'UNADMITTED_RESOURCE_DIAGNOSTIC')

    def test_unknown_object_properties_and_dictionary_keys_are_not_evaluated(self):
        touches = []
        class Trap:
            @property
            def resources(self): touches.append('resources'); raise RuntimeError('PRIVATE property')
        self.assertIsNone(E.public_material_failure(Trap()))
        class Key:
            def __hash__(self): touches.append('hash'); return hash('format')
            def __eq__(self, other): touches.append('eq'); raise AssertionError('PRIVATE equality')
        report = safe_material_report(); report.pop('format'); report[Key()] = 'PRIVATE'
        touches.clear()
        value = E.public_material_failure(material_session(report))
        self.assertEqual(value['status'], 'UNADMITTED_RESOURCE_DIAGNOSTIC')
        self.assertEqual(touches, [])
        self.assertNotIn('PRIVATE', json.dumps(value))

    def test_wrapped_sdk_failure_reports_first_material_reason_independently_of_outer_latch_count(self):
        f, hook, resources, modules, calls = ExportTests.fake_export_environment(self)
        primary = RuntimeError('PRIVATE SDK path and values')
        report = safe_material_report()
        def fail(**kwargs):
            session = hook.sessions[-1]; session.pre_export_hook({})
            session.latch = types.SimpleNamespace(first=('gather_material_hook', 'Refusal'), count=4)
            # Use plain owned fields rather than inspecting the raw SDK error.
            session.resources.public_material_failure = report
            raise primary
        f.bpy.ops.export_scene.gltf = fail
        # The base fake resource is a dict. This successor uses the owned object
        # shape of the real SimplePackedResources instance, with the same fake data.
        class OwnedResource: pass
        resources.SimplePackedResources = lambda *args, **kwargs: OwnedResource()
        activity = {}
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]):
                with self.assertRaises(RuntimeError) as caught:
                    ExportTests.invoke(self, Path(temporary) / 'carrier.glb', f, hook, resources, activity)
        self.assertIs(caught.exception, primary)
        self.assertEqual(activity['export_failure_latch']['failures'], 4)
        self.assertEqual(activity['export_material_failure']['failures'], 1)
        self.assertEqual(activity['export_material_failure']['first_refusal_code'], 'unsupported_gathered_material_profile')
        self.assertFalse(activity['export_material_failure']['material_admission_changed'])
        self.assertNotIn('PRIVATE', json.dumps(activity['export_material_failure']))
        self.assertFalse(activity['scene_or_registration_restoration_failed'])
        f.restored(self)

    def test_material_snapshot_failure_never_masks_primary_or_bypasses_cleanup(self):
        f, hook, resources, modules, calls = ExportTests.fake_export_environment(self)
        primary = RuntimeError('original SDK failure')
        def fail(**kwargs): raise primary
        f.bpy.ops.export_scene.gltf = fail
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(E.importlib, 'import_module', side_effect=lambda name: modules[name]), \
                 patch.object(E, 'public_material_failure', side_effect=MemoryError('secondary material diagnostic')):
                with self.assertRaises(RuntimeError) as caught:
                    ExportTests.invoke(self, Path(temporary) / 'carrier.glb', f, hook, resources, {})
        self.assertIs(caught.exception, primary)
        self.assertEqual(f.bpy.context.preferences.addons, {})
        f.restored(self)

if __name__ == '__main__':
    unittest.main()
