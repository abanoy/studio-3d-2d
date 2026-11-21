"""UNRUN fabricated-reference tests; no Blender, assets, IO or native execution."""
from collections import defaultdict
import copy
import hashlib
import json
import struct
import types
import unittest

import material_binding as binding


class NativeMaterial:
    def __init__(self, name, flags, used, placeholder):
        self.name, self.flags, self.used, self.bpy_material = name, flags, used, placeholder


class NativeMesh:
    def __init__(self, material, start, count):
        self.material_index, self.vertex_index_start, self.vertex_count = material, start, count


class NativeModel:
    def __init__(self, name, start, count, meshes):
        self.name, self.vertex_offset, self.vertex_count, self.meshes = name, start, count, meshes


class NativeBody:
    def __init__(self, name, models):
        self.name, self.models = name, models


class Material:
    def __init__(self, name):
        self.name, self.original = name, self
        self.properties = {'full_path': name.lstrip('/').casefold()}

    def get(self, key):
        return self.properties.get(key)


class Polygon:
    def __init__(self, index, material_index=0):
        self.index, self.loop_start, self.loop_total, self.material_index = index, index * 3, 3, material_index


class Mesh:
    def __init__(self, faces):
        self.original, self.materials = self, []
        self.polygons = [Polygon(index) for index in range(faces)]


class Object:
    def __init__(self, mesh):
        self.data, self.original = mesh, self
        self.properties = {'active_skin': '0', 'model_type': 's1'}
        self.links = None

    @property
    def material_slots(self):
        return [types.SimpleNamespace(material=material, link='DATA' if self.links is None else self.links[index])
                for index, material in enumerate(self.data.materials)]

    def get(self, key):
        return self.properties.get(key)


class Fixture:
    def __init__(self):
        identities = {key: {'bytes': 100 + index, 'sha256': str(index + 1) * 64}
                      for index, key in enumerate(('mdl', 'vvd', 'vtx'))}
        # Independent literal oracle: front's COMPLETE reversed triangle stream
        # is [1,0,1]; back uses raw1 but its sole Blender slot is0, not1.
        self.native = dict(format='has_private_native_point_source_rows_1', source_identities=identities, checksum=123,
                           models={'front.smd': dict(ids=[0, 1, 2, 3, 4, 5], corners=[0, 1, 2, 3, 4, 5, 0, 2, 3], materials=[1, 0, 1]),
                                   'back.smd': dict(ids=[6, 7, 8], corners=[0, 1, 2], materials=[1])})
        materials = [dict(index=0, name='test/Hair', flags=5, used=3),
                     dict(index=1, name='test/Hat', flags=9, used=1)]
        mesh = lambda index, raw, start, count: dict(index=index, material_index=raw, vertex_start=start, vertex_count=count)
        model = lambda index, name, start, count, meshes: dict(index=index, logical_name=name, vertex_start=start,
                                                            vertex_count=count, meshes=meshes)
        self.metadata = dict(format='has_private_mdl49_material_skin_metadata_candidate_1', source_identities=copy.deepcopy(identities),
                             checksum=123, metadata=dict(materials=materials, skin_reference_count=2,
                             skin_families=[[0, 1], [1, 1]], body_parts=[
                                 dict(index=0, name='torso', models=[model(0, 'front.smd', 0, 6, [mesh(0, 0, 0, 3), mesh(1, 1, 3, 3)]),
                                                                      model(1, 'blank', 0, 0, [])]),
                                 dict(index=1, name='accessories', models=[model(0, 'back.smd', 6, 3, [mesh(0, 1, 0, 3)])])]))
        self.placeholders = [Material('test/Hair'), Material('test/Hat')]
        self.materials = [NativeMaterial('test/Hair', 5, 3, self.placeholders[0]),
                          NativeMaterial('test/Hat', 9, 1, self.placeholders[1])]
        front = NativeModel('front.smd', 0, 6, [NativeMesh(0, 0, 3), NativeMesh(1, 3, 3)])
        blank = NativeModel('blank', 0, 0, [])
        back = NativeModel('back.smd', 6, 3, [NativeMesh(1, 0, 3)])
        self.parts = [NativeBody('torso', [front, blank]), NativeBody('accessories', [back])]
        self.models = {'front.smd': front, 'back.smd': back}
        self.skins = [[self.materials[0], self.materials[1]], [self.materials[1], self.materials[1]]]
        self.objects = {'front.smd': Object(Mesh(3)), 'back.smd': Object(Mesh(1))}
        self.container = types.SimpleNamespace(objects=list(self.objects.values()), bodygroups=defaultdict(list, {
            'torso': [self.objects['front.smd'], None], 'accessories': [self.objects['back.smd']]}))

    def collector(self):
        return binding.MaterialBinding(self.native, self.metadata, source_material_type=NativeMaterial,
                                       source_model_type=NativeModel, source_body_type=NativeBody,
                                       source_mesh_type=NativeMesh, object_type=Object, mesh_types=(Mesh,), material_type=Material)

    def set_late(self, name, mode='MATERIAL_ID'):
        obj = self.objects[name]
        if name == 'front.smd':
            obj.data.materials[:] = self.placeholders
            for polygon, index in zip(obj.data.polygons, (1, 0, 1)):
                polygon.material_index = index
        else:
            obj.data.materials[:] = [self.placeholders[1]]
        groups = [[self.placeholders[0], self.placeholders[1]], [self.placeholders[1], self.placeholders[1]]]
        obj.properties['skin_groups'] = {str(index): [value if mode == 'MATERIAL_ID' else value.name for value in values]
                                         for index, values in enumerate(groups)}

    def snapshot(self, name):
        obj, mesh = self.objects[name], self.objects[name].data
        skin_groups = obj.get('skin_groups')
        return dict(source_materials=tuple((ref, ref.name, ref.flags, ref.used, ref.bpy_material,
                                          ref.bpy_material.name, ref.bpy_material.get('full_path')) for ref in self.materials),
                    source_skins=tuple(tuple(values) for values in self.skins),
                    source_parts=tuple((part, part.name, tuple((model, model.name, model.vertex_offset, model.vertex_count,
                         tuple((mesh, mesh.material_index, mesh.vertex_index_start, mesh.vertex_count) for mesh in model.meshes))
                         for model in part.models)) for part in self.parts), slots=tuple(mesh.materials),
                    object_slots=tuple(slot.material for slot in obj.material_slots),
                    faces=tuple((face.index, face.loop_start, face.loop_total, face.material_index) for face in mesh.polygons),
                    skin_groups=None if skin_groups is None else tuple((key, tuple(values)) for key, values in skin_groups.items()),
                    active_skin=obj.get('active_skin'), model_type=obj.get('model_type'))

    def observe(self, collector, phase, name='front.smd', snapshot=None):
        obj = self.objects[name]
        collector.observe(phase, self.models[name], obj, obj.data, self.snapshot(name) if snapshot is None else snapshot)

    def through_early(self, collector, name='front.smd'):
        self.observe(collector, 'before_setter', name)
        self.observe(collector, 'after_setter', name)

    def complete(self, collector, mode='MATERIAL_ID'):
        for name in self.models:
            self.through_early(collector, name)
            self.set_late(name, mode)
            self.observe(collector, 'before_validate', name)
            self.observe(collector, 'after_validate', name)

    def returned(self, collector):
        return collector.returned(self.container, [(obj, self.snapshot(name)) for name, obj in self.objects.items()])


class MaterialBindingTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()

    def refusal(self, code, operation):
        with self.assertRaisesRegex(binding.Refusal, '^' + code + '$'):
            operation()

    def test_literal_multimodel_face_slot_identity_and_private_summary(self):
        collector = self.f.collector()
        self.f.complete(collector)
        report = self.f.returned(collector)
        self.assertEqual(report['observed_models'], 2)
        self.assertEqual(report['observed_faces'], 4)
        self.assertEqual([row['slots'] for row in report['models']], [2, 1])
        self.assertEqual(report['models'][0]['raw_face_material_order_sha256'], hashlib.sha256(struct.pack('<III', 1, 0, 1)).hexdigest())
        self.assertTrue(report['sourceio_raw_matches_candidate_default_skin_on_used_meshes'])
        self.assertFalse(report['resolved_native_default_skin_equivalence_qualified'])
        self.assertFalse(report['carrier_or_exporter_binding_qualified'])
        encoded = json.dumps(report)
        for private in ('front.smd', 'back.smd', 'test/Hair', 'test/Hat', 'torso'):
            self.assertNotIn(private, encoded)

    def test_material_id_skin_rows_preserve_many_to_one_nondefault_mapping(self):
        collector = self.f.collector()
        self.f.complete(collector)
        self.assertEqual([row['skin_storage'] for row in self.f.returned(collector)['models']], ['MATERIAL_ID', 'MATERIAL_ID'])
        self.assertIs(self.f.objects['front.smd'].get('skin_groups')['1'][0], self.f.objects['front.smd'].get('skin_groups')['1'][1])

    def test_exact_string_fallback_is_supported_without_name_lookup(self):
        collector = self.f.collector()
        self.f.complete(collector, 'STRING')
        self.assertEqual([row['skin_storage'] for row in self.f.returned(collector)['models']], ['STRING', 'STRING'])

    def test_candidate_default_nonidentity_refused_not_repaired(self):
        self.f.metadata['metadata']['skin_families'][0] = [1, 0]
        original = copy.deepcopy(self.f.metadata)
        self.refusal('SOURCEIO_RAW_DEFAULT_SKIN_NONIDENTITY_REFUSED_WITHOUT_REPAIR', self.f.collector)
        self.assertEqual(self.f.metadata, original)

    def test_raw_texture_domain_does_not_imply_skin_reference_domain(self):
        self.f.metadata['metadata']['skin_reference_count'] = 1
        self.f.metadata['metadata']['skin_families'] = [[0], [1]]
        self.refusal('USED_RAW_MESH_OUTSIDE_NATIVE_SKIN_REFERENCE_DOMAIN', self.f.collector)

    def test_native_family_digest_mixing_refused(self):
        self.f.metadata['source_identities']['mdl']['sha256'] = 'f' * 64
        self.refusal('NATIVE_FAMILY_IDENTITIES_DIFFER', self.f.collector)

    def test_native_bool_indices_do_not_equal_integer_ordinals(self):
        self.f.native['models']['front.smd']['materials'][0] = True
        self.refusal('NATIVE_FACE_MATERIAL_DOMAIN', self.f.collector)

    def test_native_face_count_and_corner_stream_count_must_agree(self):
        self.f.native['models']['front.smd']['materials'].pop()
        self.refusal('NATIVE_FACE_POINT_CARDINALITY', self.f.collector)

    def test_duplicate_native_material_names_refuse_ambiguous_string_fallback(self):
        self.f.metadata['metadata']['materials'][1]['name'] = 'test/Hair'
        self.refusal('DUPLICATE_NATIVE_MATERIAL_NAME_OUTSIDE_PROFILE', self.f.collector)

    def test_placeholder_alias_across_native_ordinals_refused(self):
        self.f.materials[1].bpy_material = self.f.placeholders[0]
        # Preserve a name/path-valid row through same-native-name alias fixture;
        # unique native names otherwise already refuse the alias before this gate.
        self.f.materials[1].name = 'test/Hair'
        collector = self.f.collector()
        self.refusal('SOURCE_MATERIAL_FIELDS_OR_PLACEHOLDER_DIFFERS', lambda: self.f.observe(collector, 'before_setter'))

    def test_actual_placeholder_full_path_must_match_no_io_profile(self):
        self.f.placeholders[0].properties['full_path'] = 'other/resource'
        collector = self.f.collector()
        self.refusal('NO_MATERIAL_IO_PLACEHOLDER_NAME_OR_PATH_DIFFERS', lambda: self.f.observe(collector, 'before_setter'))

    def test_same_named_replacement_material_identity_is_not_accepted(self):
        collector = self.f.collector()
        self.f.observe(collector, 'before_setter')
        self.f.materials[0].bpy_material = Material('test/Hair')
        self.refusal('SOURCE_OR_PLACEHOLDER_REFERENCE_CHANGED', lambda: self.f.observe(collector, 'after_setter'))

    def test_snapshot_cannot_hide_actual_native_placeholder_change(self):
        collector = self.f.collector()
        snapshot = self.f.snapshot('front.smd')
        self.f.materials[0].bpy_material = Material('test/Hair')
        self.refusal('SOURCE_MATERIAL_FIELDS_OR_PLACEHOLDER_DIFFERS', lambda: self.f.observe(collector, 'before_setter', snapshot=snapshot))

    def test_source_skin_uses_native_material_refs_not_equal_names(self):
        self.f.skins[0][0] = NativeMaterial('test/Hair', 5, 3, self.f.placeholders[0])
        collector = self.f.collector()
        self.refusal('SOURCE_SKIN_MATERIAL_IDENTITY_DIFFERS', lambda: self.f.observe(collector, 'before_setter'))

    def test_source_body_model_and_blank_ordinals_are_bound(self):
        collector = self.f.collector()
        self.f.observe(collector, 'before_setter')
        self.f.parts[0].models[1] = NativeModel('blank', 0, 0, [])
        self.refusal('SOURCE_OR_PLACEHOLDER_REFERENCE_CHANGED', lambda: self.f.observe(collector, 'after_setter'))

    def test_actual_native_mesh_fields_cannot_hide_behind_snapshot(self):
        collector = self.f.collector()
        snapshot = self.f.snapshot('front.smd')
        self.f.models['front.smd'].meshes[0].material_index = 1
        self.refusal('SOURCE_MESH_IDENTITY_OR_FIELDS_DIFFER', lambda: self.f.observe(collector, 'before_setter', snapshot=snapshot))

    def test_early_boundary_rejects_already_assigned_slots(self):
        collector = self.f.collector()
        self.f.objects['front.smd'].data.materials[:] = [self.f.placeholders[0]]
        self.refusal('EXACT_RAW_MATERIAL_TO_PLACEHOLDER_SLOT_MAPPING_DIFFERS', lambda: self.f.observe(collector, 'before_setter'))

    def test_true_polygon_reversal_error_is_detected(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].data.polygons[0].material_index = 0
        self.refusal('ORDERED_WHOLE_POLYGON_MATERIAL_STREAM_DIFFERS', lambda: self.f.observe(collector, 'before_validate'))

    def test_same_face_histogram_in_wrong_order_is_rejected(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        for face, value in zip(self.f.objects['front.smd'].data.polygons, (1, 1, 0)):
            face.material_index = value
        self.refusal('ORDERED_WHOLE_POLYGON_MATERIAL_STREAM_DIFFERS', lambda: self.f.observe(collector, 'before_validate'))

    def test_raw_material_one_on_back_maps_to_actual_slot_zero(self):
        collector = self.f.collector()
        self.f.through_early(collector, 'back.smd')
        self.f.set_late('back.smd')
        self.f.objects['back.smd'].data.polygons[0].material_index = 1
        self.refusal('ORDERED_WHOLE_POLYGON_MATERIAL_STREAM_DIFFERS', lambda: self.f.observe(collector, 'before_validate', 'back.smd'))

    def test_mesh_slot_order_is_reference_exact(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].data.materials.reverse()
        self.refusal('EXACT_RAW_MATERIAL_TO_PLACEHOLDER_SLOT_MAPPING_DIFFERS', lambda: self.f.observe(collector, 'before_validate'))

    def test_object_linked_override_refused(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].links = ['OBJECT', 'DATA']
        self.refusal('OBJECT_AND_MESH_DATA_SLOTS_DIFFER', lambda: self.f.observe(collector, 'before_validate'))

    def test_material_stream_bool_is_not_integer_one(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].data.polygons[0].material_index = True
        self.refusal('EXACT_POLYGON_INTEGER_FIELDS_REQUIRED', lambda: self.f.observe(collector, 'before_validate'))

    def test_polygon_layout_change_is_not_only_material_equivalence(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].data.polygons[1].loop_start = 2
        self.refusal('ORDERED_WHOLE_POLYGON_MATERIAL_STREAM_DIFFERS', lambda: self.f.observe(collector, 'before_validate'))

    def test_string_fallback_is_exact_and_case_sensitive(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd', 'STRING')
        self.f.objects['front.smd'].properties['skin_groups']['0'][0] = 'test/hair'
        self.refusal('SKIN_PROPERTY_EXACT_NAME_FALLBACK_DIFFERS', lambda: self.f.observe(collector, 'before_validate'))

    def test_wrong_same_named_material_ref_in_skin_property_refused(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].properties['skin_groups']['0'][0] = Material('test/Hair')
        self.refusal('SKIN_PROPERTY_MATERIAL_IDENTITY_DIFFERS', lambda: self.f.observe(collector, 'before_validate'))

    def test_mixed_pointer_and_string_skin_property_is_not_inferred(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        self.f.objects['front.smd'].properties['skin_groups']['0'][0] = 'test/Hair'
        self.refusal('MIXED_OR_UNTYPED_SKIN_PROPERTY_REFUSED', lambda: self.f.observe(collector, 'before_validate'))

    def test_skin_snapshot_cannot_hide_actual_property_change(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.f.set_late('front.smd')
        snapshot = self.f.snapshot('front.smd')
        self.f.objects['front.smd'].properties['skin_groups']['0'][0] = Material('test/Hair')
        self.refusal('SNAPSHOT_NOT_ACTUAL_SKIN_PROPERTY_VALUES', lambda: self.f.observe(collector, 'before_validate', snapshot=snapshot))

    def test_phase_omission_and_replay_are_refused(self):
        collector = self.f.collector()
        self.refusal('CREATION_BOUNDARY_MISSING', lambda: self.f.observe(collector, 'after_setter'))
        collector = self.f.collector()
        self.f.observe(collector, 'before_setter')
        self.refusal('REPEATED_OR_ALIASED_OBJECT_CREATION', lambda: self.f.observe(collector, 'before_setter'))

    def test_swallowed_failure_latches_and_cannot_later_publish(self):
        collector = self.f.collector()
        snapshot = self.f.snapshot('front.smd')
        snapshot['unexpected'] = True
        self.refusal('EXACT_MATERIAL_SNAPSHOT_SCHEMA', lambda: self.f.observe(collector, 'before_setter', snapshot=snapshot))
        self.assertEqual(collector.failed, 'EXACT_MATERIAL_SNAPSHOT_SCHEMA')
        self.refusal('COLLECTOR_FAILED_CLOSED_OR_PHASE_INVALID', lambda: self.f.observe(collector, 'after_setter'))
        self.refusal('INCOMPLETE_OR_FAILED_MATERIAL_OBSERVATION', lambda: self.f.returned(collector))

    def test_returned_incomplete_and_reordered_objects_refused(self):
        collector = self.f.collector()
        self.f.through_early(collector)
        self.refusal('INCOMPLETE_OR_FAILED_MATERIAL_OBSERVATION', lambda: self.f.returned(collector))
        collector = self.f.collector()
        self.f.complete(collector)
        self.f.container.objects.reverse()
        self.refusal('RETURNED_RENDERABLE_OBJECT_ORDER_OR_IDENTITY_DIFFERS', lambda: self.f.returned(collector))

    def test_returned_blank_bodygroup_entry_must_remain_none(self):
        collector = self.f.collector()
        self.f.complete(collector)
        self.f.container.bodygroups['torso'][1] = self.f.objects['front.smd']
        self.refusal('RETURNED_BODYGROUP_MODEL_OR_BLANK_IDENTITY_DIFFERS', lambda: self.f.returned(collector))

    def test_returned_skin_mode_change_refused(self):
        collector = self.f.collector()
        self.f.complete(collector)
        self.f.set_late('front.smd', 'STRING')
        self.refusal('RETURNED_MODEL_OR_SKIN_STORAGE_CHANGED', lambda: self.f.returned(collector))

    def test_success_closes_collector_and_observer_never_mutates_inputs(self):
        collector = self.f.collector()
        expected_native, expected_metadata = copy.deepcopy(self.f.native), copy.deepcopy(self.f.metadata)
        self.f.complete(collector)
        snapshots = [self.f.snapshot(name) for name in self.f.objects]
        before_material_refs = tuple(self.f.materials)
        before_placeholder_refs = tuple(self.f.placeholders)
        before_slot_refs = [tuple(obj.data.materials) for obj in self.f.objects.values()]
        self.f.returned(collector)
        self.assertEqual(self.f.native, expected_native)
        self.assertEqual(self.f.metadata, expected_metadata)
        self.assertEqual(snapshots, [self.f.snapshot(name) for name in self.f.objects])
        self.assertTrue(all(left is right for left, right in zip(before_material_refs, self.f.materials)))
        self.assertTrue(all(left is right for left, right in zip(before_placeholder_refs, self.f.placeholders)))
        self.assertTrue(all(all(left is right for left, right in zip(before, obj.data.materials))
                            for before, obj in zip(before_slot_refs, self.f.objects.values())))
        self.refusal('INCOMPLETE_OR_FAILED_MATERIAL_OBSERVATION', lambda: self.f.returned(collector))


if __name__ == '__main__':
    unittest.main()
