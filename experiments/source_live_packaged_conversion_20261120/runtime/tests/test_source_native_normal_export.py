"""Pure live-adapter contracts; synthetic files and fake bpy/RNA/export only.

No native model, Blender, SourceIO, NumPy or actual operator is used. Existing
sealed normal/bone tests own algorithm qualification; this file tests wiring.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location('_has_live_adapter_under_test', ROOT / 'tools/source_native_normal_export.py')
L = importlib.util.module_from_spec(spec); sys.modules[spec.name] = L
spec.loader.exec_module(L)
NS = types.SimpleNamespace


def request():
    return dict(sourceio_revision=L.REVISION, scale=.01905, appearance=None, source_member=None)


class RoutingAndFileTests(unittest.TestCase):
    def test_unknown_profiles_keep_legacy_route_before_any_new_toolkit_native_or_sidecar_io(self):
        capture = NS(native_sha256=L.KNOWN_MDL)
        variants = [(None, capture), (request(), NS(native_sha256='0' * 64)),
                    (dict(request(), scale=1.0), capture), (dict(request(), scale=True), capture),
                    (dict(request(), sourceio_revision='other'), capture),
                    (dict(request(), appearance={}), capture), (dict(request(), source_member='member.mdl'), capture)]
        with patch.object(L, 'Workflow', side_effect=AssertionError('must not construct/read toolkit')):
            for req, selected in variants:
                with self.subTest(known_hash=getattr(selected, 'native_sha256', None) == L.KNOWN_MDL):
                    self.assertIsNone(L.prepare_import(req, selected, object(), object(), object(), 'unused',
                        lambda *args: (_ for _ in ()).throw(AssertionError('sidecar IO'))))

    def test_exact_known_route_constructs_and_imports_once_with_same_caller_references(self):
        req, capture, bpy, cm, options, source, resolver = request(), NS(native_sha256=L.KNOWN_MDL), object(), object(), object(), object(), object()
        calls = []
        class Workflow:
            def __init__(self, *args): calls.append(args)
            def import_native(self): calls.append('import')
        with patch.object(L, 'Workflow', Workflow):
            result = L.prepare_import(req, capture, bpy, cm, options, source, resolver)
        self.assertIs(type(result), Workflow)
        self.assertEqual(calls, [(req, capture, bpy, cm, options, source, resolver), 'import'])

    def test_read_pin_accepts_only_exact_bounded_immutable_bytes(self):
        raw = b'synthetic source code only'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.py'; path.write_bytes(raw)
            actual, stamp = L.read_pin(path, len(raw), L.sha(raw))
            self.assertEqual(actual, raw); self.assertEqual(stamp, L.stamp(path.lstat()))
            for count, digest in ((len(raw) + 1, L.sha(raw)), (len(raw), '0' * 64), (True, L.sha(raw))):
                with self.subTest(count=count), self.assertRaises(L.Refusal): L.read_pin(path, count, digest)

    def test_opened_file_identity_changes_are_rejected_before_acceptance(self):
        raw = b'synthetic file'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.py'; path.write_bytes(raw); base = path.stat()
            def fake(**changes):
                values = {name: getattr(base, name, 0) for name in
                    ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink', 'st_file_attributes')}
                values.update(changes); return NS(**values)
            for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink'):
                with self.subTest(field=field), patch.object(L.os, 'fstat', return_value=fake(**{field: getattr(base, field) + 1})):
                    with self.assertRaisesRegex(L.Refusal, '^LIVE_INPUT_CHANGED_BEFORE_READ$'):
                        L.read_pin(path, len(raw), L.sha(raw))

    def test_only_reviewed_recall_hint_is_normalized_in_source_stamp(self):
        base = dict(st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4, st_nlink=1)
        self.assertEqual(L.stamp(NS(**base, st_file_attributes=0x40020)), L.stamp(NS(**base, st_file_attributes=0x20)))
        self.assertNotEqual(L.stamp(NS(**base, st_file_attributes=0x420)), L.stamp(NS(**base, st_file_attributes=0x20)))

    def test_toolkit_collision_refuses_before_source_reads(self):
        name = next(iter(L.TOOLKIT))
        with patch.dict(sys.modules, {name: types.ModuleType(name)}), \
             patch.object(L, 'read_pin', side_effect=AssertionError('must refuse before IO')):
            with self.assertRaisesRegex(L.Refusal, '^LIVE_TOOLKIT_MODULE_COLLISION$'): L.load_toolkit()

    def test_bad_source_pin_cannot_publish_partial_toolkit_modules(self):
        removed = {name: sys.modules.pop(name) for name in L.TOOLKIT if name in sys.modules}
        try:
            with patch.object(L, 'read_pin', side_effect=L.Refusal('synthetic pin mismatch')):
                with self.assertRaises(L.Refusal): L.load_toolkit()
            self.assertTrue(all(name not in sys.modules for name in L.TOOLKIT))
        finally:
            sys.modules.update(removed)

    def test_real_adjacent_source_toolkit_has_one_canonical_hook_resource_cache_and_parser_alias(self):
        names = set(L.TOOLKIT) | {'experiments', 'experiments.carrier_input_domain_20261118',
            'experiments.carrier_input_domain_20261118.semantic_compare'}
        prior = {name: sys.modules.pop(name) for name in names if name in sys.modules}
        try:
            modules = L.load_toolkit()
            self.assertEqual(set(modules), set(L.TOOLKIT))
            self.assertIs(modules['export_hook_proposal'].shared_images, modules['shared_image_cache_proposal'])
            self.assertIs(modules['shared_image_cache_proposal'].R, modules['resource_gate_proposal'])
            self.assertIs(modules['resource_gate_proposal'].Refusal, modules['export_hook_proposal'].Refusal)
            self.assertIs(modules['input_domain'].Snapshot, modules['semantic_compare'].Snapshot)
        finally:
            for name in names: sys.modules.pop(name, None)
            sys.modules.update(prior)


class ID:
    def __init__(self, **values): self.__dict__.update(values)
    def as_pointer(self): return id(self)
class Material(ID): pass
class Image(ID):
    @property
    def packed_file(self): return self._packed
    @property
    def size(self): raise AssertionError('image buffer acquisition must belong to admitted cold helper')
    @property
    def channels(self): raise AssertionError('image buffer getter before admission')
    @property
    def pixels(self): raise AssertionError('pixels getter forbidden in metadata fixture')
class PackedFile(ID):
    @property
    def data(self): self.reads += 1; return self.raw
class ImagePackedFile(ID): pass
class MaterialSlot(ID): pass
class MeshPolygon(ID): pass


def png():
    chunk = b'IHDR' + struct.pack('>IIBBBBB', 32, 32, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + chunk + struct.pack('>I', zlib.crc32(chunk)) + b'synthetic only'


def resources_fixture():
    raw = png(); images = []
    for index in range(2):
        image = Image(name='synthetic-' + str(index), filepath='', original=None, library=None, source='FILE', type='IMAGE')
        image.original = image
        packed = PackedFile(id_data=image, size=len(raw), raw=raw, reads=0)
        part = ImagePackedFile(id_data=image, packed_file=packed)
        image._packed, image.packed_files = packed, [part]
        images.append(image)
    materials = [Material(tree=object(), image=images[index % 2], revision=0) for index in range(4)]
    def graph(material, types):
        return dict(tree=material.tree, images=(material.image,), node_keys=(1,), link_keys=(2,), edge_keys=(3,)), (material.revision,)
    def key(value, expected, owner):
        if type(value) is not expected or value.id_data is not owner: raise ValueError('fake ownership')
        return expected, id(owner), value.as_pointer()
    def header(raw):
        if raw != png(): raise ValueError('fake PNG pin')
        return 32, 32
    inspector = NS(_graph=graph, _nonid_key=key, _png=header)
    cold = NS(_structure=lambda row, types, inspector: dict(metadata=(row['image'].name, row['image'].filepath)))
    w = object.__new__(L.Workflow)
    w.bpy = NS(types=NS(Material=Material, Image=Image, PackedFile=PackedFile, ImagePackedFile=ImagePackedFile),
               data=NS(libraries=[]))
    w.mdl = NS(materials=[NS(bpy_material=material) for material in materials])
    w.modules = dict(material_inspection=inspector, cold_image_readiness=cold)
    return w, materials, images


class LiveResourceTests(unittest.TestCase):
    def test_unique_live_png_refs_are_kept_without_scene_or_pixel_getters(self):
        w, materials, images = resources_fixture(); private = w.live_resources()
        self.assertEqual(private['materials'], tuple(materials))
        self.assertEqual(len(private['images']), 2)
        self.assertTrue(all(row['image'] is image for row, image in zip(private['images'], images)))
        self.assertEqual([image._packed.reads for image in images], [1, 1])
        w.recheck_live_resources(private)
        self.assertEqual([image._packed.reads for image in images], [2, 2])

    def test_all_encoded_sizes_are_admitted_before_any_packed_data_copy(self):
        w, materials, images = resources_fixture(); images[-1]._packed.size = 64 * 1024 * 1024 + 1
        with self.assertRaisesRegex(L.Refusal, '^LIVE_ENCODED_PACK_BUDGET$'): w.live_resources()
        self.assertEqual([image._packed.reads for image in images], [0, 0])

    def test_pack_alias_owner_and_four_native_material_identity_are_required(self):
        w, materials, images = resources_fixture(); images[0].packed_files[0].id_data = object()
        with self.assertRaises(ValueError): w.live_resources()
        self.assertEqual([image._packed.reads for image in images], [0, 0])
        w, materials, images = resources_fixture(); w.mdl.materials[1].bpy_material = materials[0]
        with self.assertRaisesRegex(L.Refusal, '^LIVE_FOUR_ACTUAL_NATIVE_MATERIALS_REQUIRED$'): w.live_resources()
        self.assertEqual([image._packed.reads for image in images], [0, 0])

    def test_live_resource_recheck_refuses_graph_image_pack_and_library_drift(self):
        for change in ('graph', 'image', 'pack', 'library'):
            with self.subTest(change=change):
                w, materials, images = resources_fixture(); private = w.live_resources()
                if change == 'graph': materials[0].revision += 1
                elif change == 'image': images[0].name = 'changed'
                elif change == 'pack': images[0]._packed.raw = images[0]._packed.raw[:-1] + b'!'
                else: w.bpy.data.libraries.append(object())
                with self.assertRaises(L.Refusal): w.recheck_live_resources(private)


def slot_fixture():
    w = object.__new__(L.Workflow)
    w._skin_phase = 'NATIVE_DATA'
    materials = [Material(original=None, library=None) for _ in range(4)]
    for material in materials: material.original = material
    w.bpy = NS(types=NS(Material=Material, MaterialSlot=MaterialSlot, MeshPolygon=MeshPolygon))
    w.mdl = NS(materials=[NS(bpy_material=material) for material in materials])
    w.native = {'models': {'logical': {'materials': [3, 1, 3, 1]}}}
    mesh = NS(materials=[materials[1], materials[3]], polygons=[])
    obj = NS(material_slots=[])
    obj.material_slots = [MaterialSlot(id_data=obj, link='DATA', material=material) for material in mesh.materials]
    mesh.polygons = [MeshPolygon(id_data=mesh, index=index, material_index=value)
                     for index, value in enumerate((1, 0, 1, 0))]
    return w, obj, mesh, materials


class MaterialSlotTests(unittest.TestCase):
    def test_native_full_face_order_determines_sorted_actual_slots_and_data_owners(self):
        w, obj, mesh, materials = slot_fixture()
        self.assertEqual(w.check_native_material_slots(obj, mesh, 'logical'), 2)
        self.assertEqual(mesh.materials, [materials[1], materials[3]])

    def test_slot_identity_object_link_and_owner_drift_are_refused(self):
        for edit in ('material', 'link', 'owner'):
            with self.subTest(edit=edit):
                w, obj, mesh, materials = slot_fixture()
                if edit == 'material': mesh.materials.reverse()
                elif edit == 'link': obj.material_slots[0].link = 'OBJECT'
                else: obj.material_slots[0].id_data = object()
                with self.assertRaises(L.Refusal): w.check_native_material_slots(obj, mesh, 'logical')


class SkinObject(dict):
    def __setitem__(self, key, value):
        self.writes.append((key, value)); return super().__setitem__(key, value)


@contextmanager
def genuine_skin_fixture():
    """Compile exact pinned SDK functions without executing its bpy imports."""
    w, original, mesh, materials = slot_fixture()
    obj = SkinObject(skin_groups={'0': [materials[1], materials[3]]})
    obj.writes = []; obj.type = 'MESH'; obj.material_slots = original.material_slots
    for slot in obj.material_slots: slot.id_data = obj
    w.container = NS(objects=[obj]); w.summary = {}
    w.ledger = NS(records={'logical': {'obj': obj, 'mesh': mesh}})
    sourceio = Path(os.environ.get('HYBRID_SOURCEIO', "C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff/output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647"))
    source_path = sourceio / 'blender_bindings/shared/skins.py'
    raw = source_path.read_bytes()
    if (len(raw), hashlib.sha256(raw).hexdigest()) != L.SKINS_PIN:
        raise AssertionError('exact genuine SDK skin SOURCE required')
    name = 'SourceIO.blender_bindings.shared.skins'
    module = types.ModuleType(name); module.__file__ = str(source_path); module.bpy = w.bpy
    def forbidden(*args): raise AssertionError('default same-Material route must not resolve/create materials')
    module.get_or_create_material = module.TinyPath = forbidden
    code = compile(raw, str(source_path), 'exec', dont_inherit=True)
    def direct(compiled, function_name):
        found = [value for value in compiled.co_consts if type(value) is types.CodeType and value.co_name == function_name]
        if len(found) != 1: raise AssertionError('unique actual direct function required')
        return found[0]
    for function_name in ('_material', 'set_skin', 'set_model_skin'):
        module.__dict__[function_name] = types.FunctionType(direct(code, function_name), module.__dict__)
    w.request = {'sourceio': str(sourceio)}
    w.modules = {'creation_support': NS(direct_function_code=direct)}
    real_import = L.importlib.import_module
    with patch.dict(sys.modules, {name: module}), \
         patch.object(L.importlib, 'import_module', side_effect=lambda key: module if key == name else real_import(key)):
        yield w, obj, mesh, materials, module


class DefaultSkinLifecycleTests(unittest.TestCase):
    def test_genuine_default_zero_setter_is_called_once_and_only_same_refs_transition_to_object(self):
        with genuine_skin_fixture() as (w, obj, mesh, materials, module):
            before_slots, before_faces = tuple(mesh.materials), tuple(face.material_index for face in mesh.polygons)
            self.assertIsNone(w.apply_default_skin(w.container, 0, module.set_model_skin))
            self.assertEqual(w._skin_phase, 'DEFAULT_SKIN_OBJECT')
            self.assertTrue(all(slot.link == 'OBJECT' for slot in obj.material_slots))
            self.assertEqual(tuple(mesh.materials), before_slots)
            self.assertEqual(tuple(face.material_index for face in mesh.polygons), before_faces)
            self.assertTrue(all(slot.material is actual for slot, actual in zip(obj.material_slots, before_slots)))
            self.assertEqual([key for key, _ in obj.writes].count('active_skin'), 1)
            self.assertEqual(w.summary['default_skin_transition']['ordinary_setter_calls'], 1)
            self.assertFalse(w.summary['default_skin_transition']['generic_skin_switching_qualified'])
            self.assertEqual(w.check_native_material_slots(obj, mesh, 'logical'), 2)
            with self.assertRaises(L.Refusal): w.apply_default_skin(w.container, 0, module.set_model_skin)
            self.assertEqual([key for key, _ in obj.writes].count('active_skin'), 1)

    def test_nonzero_bool_wrong_container_and_unobserved_object_phase_are_refused_before_call(self):
        for edit in ('skin', 'bool', 'container', 'premature_object'):
            with self.subTest(edit=edit), genuine_skin_fixture() as (w, obj, mesh, materials, module):
                if edit == 'premature_object': obj.material_slots[0].link = 'OBJECT'
                container = object() if edit == 'container' else w.container
                skin = 1 if edit == 'skin' else False if edit == 'bool' else 0
                with self.assertRaises(L.Refusal): w.apply_default_skin(container, skin, module.set_model_skin)
                self.assertEqual(obj.writes, [])
                self.assertEqual(w._skin_phase, 'NATIVE_DATA')

    def test_setter_source_code_or_alias_substitution_refuses_before_any_transition(self):
        for edit in ('code', 'alias', 'foreign_setter'):
            with self.subTest(edit=edit), genuine_skin_fixture() as (w, obj, mesh, materials, module):
                setter = module.set_model_skin
                if edit == 'code':
                    def changed(container, skin): return None
                    setter.__code__ = changed.__code__
                elif edit == 'alias': module.set_model_skin = lambda *args: None
                else: setter = lambda *args: None
                with self.assertRaises(L.Refusal): w.apply_default_skin(w.container, 0, setter)
                self.assertEqual(obj.writes, []); self.assertEqual(w._skin_phase, 'NATIVE_DATA')

    def test_setter_failure_keeps_exact_primary_and_enters_nonreplayable_failed_phase(self):
        with genuine_skin_fixture() as (w, obj, mesh, materials, module):
            primary = RuntimeError('synthetic RNA assignment failure')
            class FailingSlot(ID):
                def __setattr__(self, name, value):
                    if name == 'link' and value == 'OBJECT': raise primary
                    object.__setattr__(self, name, value)
            w.bpy.types.MaterialSlot = FailingSlot
            obj.material_slots = [FailingSlot(**slot.__dict__) for slot in obj.material_slots]
            with self.assertRaises(RuntimeError) as caught: w.apply_default_skin(w.container, 0, module.set_model_skin)
            self.assertIs(caught.exception, primary); self.assertEqual(w._skin_phase, 'FAILED_DEFAULT_SKIN')
            with self.assertRaises(L.Refusal): w.apply_default_skin(w.container, 0, module.set_model_skin)

    def test_postsetter_ref_owner_face_or_link_mismatch_cannot_be_admitted_as_default_skin(self):
        for edit in ('face', 'ref', 'owner', 'link'):
            with self.subTest(edit=edit), genuine_skin_fixture() as (w, obj, mesh, materials, module):
                class DriftSlot(ID):
                    def __setattr__(self, name, value):
                        object.__setattr__(self, name, value)
                        if name == 'link' and value == 'OBJECT':
                            if edit == 'face': mesh.polygons[0].material_index = 0
                            elif edit == 'owner': object.__setattr__(self, 'id_data', object())
                            elif edit == 'link': object.__setattr__(self, 'link', 'DATA')
                        if name == 'material' and edit == 'ref' and self.link == 'OBJECT': object.__setattr__(self, 'material', materials[0])
                w.bpy.types.MaterialSlot = DriftSlot
                # Initial construction must stay the qualified DATA snapshot.
                obj.material_slots = [DriftSlot(**slot.__dict__) for slot in obj.material_slots]
                with self.assertRaises(L.Refusal): w.apply_default_skin(w.container, 0, module.set_model_skin)
                self.assertEqual(w._skin_phase, 'FAILED_DEFAULT_SKIN')

    def test_export_requires_the_observed_default_skin_phase_not_an_arbitrary_object_link(self):
        f = export_fixture(); f.w._skin_phase = 'NATIVE_DATA'
        with self.assertRaisesRegex(L.Refusal, '^LIVE_OBSERVED_DEFAULT_SKIN_REQUIRED_BEFORE_EXPORT$'):
            f.w.export_final(Path('unused'), f.observation, f.bone)
        self.assertEqual(f.events, [])

    def test_full_face_sequence_integer_domains_and_native_material_domain_remain_required(self):
        for edit in ('sequence', 'index_bool', 'material_bool', 'native_bool', 'native_range', 'face_owner'):
            with self.subTest(edit=edit):
                w, obj, mesh, materials = slot_fixture()
                if edit == 'sequence':
                    mesh.polygons[0].material_index, mesh.polygons[1].material_index = 0, 1
                elif edit == 'index_bool': mesh.polygons[0].index = False
                elif edit == 'material_bool': mesh.polygons[0].material_index = True
                elif edit == 'native_bool': w.native['models']['logical']['materials'][0] = True
                elif edit == 'native_range': w.native['models']['logical']['materials'][0] = 4
                else: mesh.polygons[0].id_data = object()
                with self.assertRaises(L.Refusal): w.check_native_material_slots(obj, mesh, 'logical')


def export_fixture():
    events, calls = [], []
    raw, final = b'glTF' + bytes(24), b'glTF' + bytes(25)
    capture, proof, source = object(), object(), object()
    raw_observation = NS(capture=capture, proof=proof, recheck=lambda: events.append('raw_recheck'))
    w = object.__new__(L.Workflow)
    w.capture, w.container, w.np, w.export_attempted = capture, object(), object(), False
    w._skin_phase = 'DEFAULT_SKIN_OBJECT'
    w.facts = {'hair.smd': {'ids': (0, 1)}, 'Hat.smd': {'ids': (2,)}}
    w.native = {'checksum': 17, 'models': {'hair.smd': {'materials': [0, 1]}, 'Hat.smd': {'materials': [2, 3]}}}
    w.raw = {'vvd': b'synthetic VVD stand-in'}
    w.ledger, w.snapshot = NS(records={}), object()
    w.summary = dict(application_adoption_qualified=False)
    w.recheck_inputs = lambda: events.append('input_recheck')
    private = dict(materials=tuple(object() for _ in range(4)), images=(), graphs=(), serial=())
    w.live_resources = lambda: private
    w.recheck_live_resources = lambda value: events.append('resource_recheck') if value is private else (_ for _ in ()).throw(AssertionError('private refs changed'))
    scene = NS(install=lambda: events.append('install'), close=lambda: events.append('close'),
               admissions=lambda: ['actual fake admission'], point_admission=object())
    relation, rebound, finalization = {(0, 0): (1, 2), (1, 0): (3,)}, {'fake_bones': True}, {'fake_finalization': True}
    sessions = []
    class Session:
        def __init__(self, *args, **kwargs):
            sessions.append(self); self.args, self.kwargs = args, kwargs
        @contextmanager
        def install(self, addon, names): events.append('registration_enter'); yield; events.append('registration_exit')
        def finish(self, value, digest):
            if value != raw or digest != L.sha(raw): raise AssertionError('raw completion pin')
            events.append('normal_finish'); return relation, {'fake_binding': True}
        def finish_bones(self, value):
            if value != raw: raise AssertionError('bone proof must see raw')
            events.append('bones_finish'); return {'fake_raw_bones': True}
    def finalize(value, **kwargs):
        if value != raw or kwargs['native'] is not source or kwargs['independent_relation'] is not relation:
            raise AssertionError('qualified data must flow unchanged')
        if kwargs['expected_source_ids'] != [1, 2, 3] or kwargs['axes'] != (1, 3, -2):
            raise AssertionError('independent IDs or frame changed')
        kwargs['bone_collector'].finish(raw); events.append('finalize')
        return final, finalization, rebound
    def publication(observation, actual_bones, actual_report, *, raw_path, final_path, identity_reader):
        if observation is not raw_observation or actual_bones is not rebound or actual_report is not finalization:
            raise AssertionError('final publication provenance changed')
        identity_reader(raw_path, L.sha(raw)); identity_reader(final_path, L.sha(final))
        events.append('publication'); return {'observation': observation, 'observed': actual_bones}
    adapter = NS(admit_identity_normal_frame=lambda c: {'fake_identity_frame': True},
                 compose_session_class=lambda h, b: Session, finalize_native_normals=finalize,
                 make_publication_state=publication)
    hook = NS(PINS={'addon': ('__init__.py', ''), 'exporter': ('blender/exp/exporter.py', ''),
                    'search': ('blender/search.py', ''), 'encode': ('blender/encode.py', ''), 'gltf': ('io/gltf.py', '')})
    ticket = object()
    def surface(*args, **kwargs):
        calls.append(('surface', args, kwargs)); return NS(empty_material_extension_profile=ticket)
    hook.PinnedSurface = surface
    def resources(*args, **kwargs): calls.append(('resources', args, kwargs)); return object()
    carrier = NS(CarrierScene=lambda *args: scene,
        fresh_owned_carrier_path=lambda path, parent: events.append('fresh_raw'),
        operator_profile=lambda path: ({'filepath': str(path)}, {'fake_options': True}),
        read_owned_carrier=lambda path, parent: Path(path).read_bytes())
    correction = NS(source_from_vvd=lambda *args: source)
    w.modules = dict(normal_export_adapter=adapter, material_inspection=object(), export_hook_proposal=hook,
        resource_gate_proposal=NS(SimplePackedResources=resources), carrier_export=carrier,
        cold_image_readiness=NS(acquire_packed_png_buffers=lambda *args: ([], {'fake_ready': True})),
        observer_instrumentation=object(), gather_binding=object(), normal_identity_carrier=correction)
    modules = {'io_scene_gltf2': object(), 'io_scene_gltf2.blender.exp.exporter': NS(gltf2_io_extensions=object()),
               'io_scene_gltf2.blender.search': object(), 'io_scene_gltf2.blender.encode': object(),
               'io_scene_gltf2.io.gltf': object(), 'io_scene_gltf2.io.exp.binary_data': object()}
    def gltf(**kwargs): calls.append(('operator', kwargs)); Path(kwargs['filepath']).write_bytes(raw); return {'FINISHED'}
    w.bpy = NS(types=NS(), context=NS(preferences=NS(addons={'io_scene_gltf2': object()})),
               ops=NS(export_scene=NS(gltf=gltf)))
    bone = NS(EXPLICIT_KWARGS={'export_skins': True}, ObservedCollector=object(), C=NS(EXPORTER_PINS={'fake': 'pin'}))
    return NS(w=w, events=events, calls=calls, raw=raw, final=final, modules=modules,
              observation=raw_observation, bone=bone, sessions=sessions, ticket=ticket)


class ExportWiringTests(unittest.TestCase):
    def test_one_export_raw_completion_bones_correction_and_final_publication_are_ordered_and_restored(self):
        f = export_fixture()
        with tempfile.TemporaryDirectory() as tmp, patch.object(L.importlib, 'import_module', side_effect=lambda name: f.modules[name]):
            publication, report = f.w.export_final(Path(tmp), f.observation, f.bone)
            self.assertEqual((Path(tmp) / 'carrier.glb').read_bytes(), f.raw)
            self.assertEqual((Path(tmp) / 'scene.glb').read_bytes(), f.final)
        self.assertEqual(sum(call[0] == 'operator' for call in f.calls), 1)
        for first, second in (('normal_finish', 'bones_finish'), ('bones_finish', 'finalize'), ('finalize', 'publication'), ('publication', 'close')):
            self.assertLess(f.events.index(first), f.events.index(second))
        self.assertIs(publication['observation'], f.observation)
        self.assertFalse(report['application_adoption_qualified'])
        self.assertIs(f.calls[1][2]['empty_material_extension_profile'], f.ticket)
        self.assertEqual(len(f.sessions), 1)

    def test_actual_operator_failure_is_not_retried_and_owned_scene_is_closed(self):
        f = export_fixture(); primary = RuntimeError('synthetic actual operator failure')
        def fail(**kwargs): f.calls.append(('operator', kwargs)); raise primary
        f.w.bpy.ops.export_scene.gltf = fail
        with tempfile.TemporaryDirectory() as tmp, patch.object(L.importlib, 'import_module', side_effect=lambda name: f.modules[name]):
            with self.assertRaises(RuntimeError) as caught: f.w.export_final(Path(tmp), f.observation, f.bone)
        self.assertIs(caught.exception, primary); self.assertEqual(f.events.count('close'), 1)
        self.assertEqual(sum(call[0] == 'operator' for call in f.calls), 1)
        self.assertNotIn('finalize', f.events)

    def test_finalizer_failure_cannot_publish_a_scene_or_skip_restore(self):
        f = export_fixture(); primary = ValueError('synthetic failed exact normal contract')
        def fail(*args, **kwargs): raise primary
        f.w.modules['normal_export_adapter'].finalize_native_normals = fail
        with tempfile.TemporaryDirectory() as tmp, patch.object(L.importlib, 'import_module', side_effect=lambda name: f.modules[name]):
            with self.assertRaises(ValueError) as caught: f.w.export_final(Path(tmp), f.observation, f.bone)
            self.assertFalse((Path(tmp) / 'scene.glb').exists())
        self.assertIs(caught.exception, primary); self.assertIn('close', f.events); self.assertNotIn('publication', f.events)

    def test_workflow_replay_and_wrong_raw_observation_capture_refuse_before_new_export(self):
        f = export_fixture(); f.w.export_attempted = True
        with self.assertRaises(L.Refusal): f.w.export_final(Path('unused'), f.observation, f.bone)
        self.assertEqual(f.events, [])
        f = export_fixture(); f.observation.capture = object()
        with self.assertRaises(L.Refusal): f.w.export_final(Path('unused'), f.observation, f.bone)
        self.assertEqual(f.events, [])


if __name__ == '__main__':
    unittest.main()
