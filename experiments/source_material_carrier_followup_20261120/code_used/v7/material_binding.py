"""UNRUN stdlib-only observer for one new, closed SourceIO MDL49 import.

No IO, Blender imports, mutations, material resolution, skin switching, library
append or export. Native candidates come only from the pinned cbb4/c04 readers.
The host authenticates those readers/inputs and supplies exact genuine API types
and bounded typed snapshots. Private identities and arrays never leave RAM.
"""
from collections import defaultdict
import hashlib
import re
import struct

PHASES = ('before_setter', 'after_setter', 'before_validate', 'after_validate')
MAX_MATERIALS, MAX_MODELS, MAX_PARTS = 256, 1024, 256
MAX_POINTS, MAX_FACES, MAX_MESHES = 200_000, 333_333, 65_536
SNAPSHOT_KEYS = {'source_materials', 'source_skins', 'source_parts', 'slots',
                 'object_slots', 'faces', 'skin_groups', 'active_skin', 'model_type'}


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def integer(value, maximum, code, minimum=0):
    need(type(value) is int and minimum <= value <= maximum, code)
    return value


def text(value, code, maximum=256):
    need(type(value) is str and 0 < len(value) <= maximum and
         all(32 <= ord(char) < 127 for char in value), code)
    return value


def tuple_of(value, maximum, code, minimum=0):
    need(type(value) is tuple and minimum <= len(value) <= maximum, code)
    return value


def _identities(value):
    need(type(value) is dict and set(value) == {'mdl', 'vvd', 'vtx'}, 'THREE_NATIVE_IDENTITIES_REQUIRED')
    result = {}
    for role, row in value.items():
        need(type(row) is dict and set(row) == {'bytes', 'sha256'}, 'EXACT_NATIVE_IDENTITY_SCHEMA')
        integer(row['bytes'], 128 * 1024 * 1024, 'NATIVE_IDENTITY_SIZE', 1)
        need(type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None,
             'NATIVE_IDENTITY_SHA256')
        result[role] = (row['bytes'], row['sha256'])
    return result


def facts_from_independent(native, material_metadata):
    """Copy bounded private material facts; accept no observed identities/labels.

    cbb4's materials stream ALREADY reverses the complete triangle order. It is
    consumed unchanged here. These are SourceIO raw mesh-material indices, not a
    resolved native skin-family result. Native normal/geometry qualification is
    not created by this function.
    """
    need(type(native) is dict and native.get('format') == 'has_private_native_point_source_rows_1',
         'NATIVE_POINT_CANDIDATE_FORMAT')
    need(type(material_metadata) is dict and material_metadata.get('format') ==
         'has_private_mdl49_material_skin_metadata_candidate_1', 'MATERIAL_METADATA_FORMAT')
    identities = _identities(native.get('source_identities'))
    need(identities == _identities(material_metadata.get('source_identities')), 'NATIVE_FAMILY_IDENTITIES_DIFFER')
    checksum = integer(native.get('checksum'), 0xffffffff, 'EXACT_NATIVE_CHECKSUM')
    need(type(material_metadata.get('checksum')) is int and checksum == material_metadata['checksum'],
         'NATIVE_FAMILY_CHECKSUM_DIFFERS')
    metadata = material_metadata.get('metadata')
    need(type(metadata) is dict, 'MATERIAL_METADATA_REQUIRED')
    materials = metadata.get('materials')
    need(type(materials) is list and 0 < len(materials) <= MAX_MATERIALS, 'BOUNDED_NATIVE_MATERIAL_TABLE')
    names, material_facts = set(), []
    for ordinal, row in enumerate(materials):
        need(type(row) is dict and type(row.get('index')) is int and row['index'] == ordinal,
             'NATIVE_MATERIAL_ORDINAL_DOMAIN')
        name = text(row.get('name'), 'NATIVE_MATERIAL_NAME')
        need(name not in names, 'DUPLICATE_NATIVE_MATERIAL_NAME_OUTSIDE_PROFILE')
        names.add(name)
        material_facts.append((name, integer(row.get('flags'), 0xffffffff, 'NATIVE_MATERIAL_FLAGS'),
                               integer(row.get('used'), 0xffffffff, 'NATIVE_MATERIAL_USED')))
    skin_refs = integer(metadata.get('skin_reference_count'), MAX_MATERIALS, 'NATIVE_SKIN_REFERENCE_COUNT')
    skins = metadata.get('skin_families')
    need(type(skins) is list and len(skins) <= MAX_MATERIALS and bool(skin_refs) == bool(skins),
         'NATIVE_SKIN_FAMILY_DOMAIN')
    skin_facts = []
    for family in skins:
        need(type(family) is list and len(family) == skin_refs, 'NATIVE_SKIN_FAMILY_WIDTH')
        skin_facts.append(tuple(integer(index, len(materials) - 1, 'NATIVE_SKIN_TEXTURE_ORDINAL') for index in family))
    parts = metadata.get('body_parts')
    need(type(parts) is list and 0 < len(parts) <= MAX_PARTS, 'BOUNDED_NATIVE_BODY_PARTS')
    point_models = native.get('models')
    need(type(point_models) is dict and 0 < len(point_models) <= MAX_MODELS, 'BOUNDED_NATIVE_POINT_MODELS')
    part_facts, model_facts, part_names, used_raw_mesh_materials = [], {}, set(), set()
    model_count = mesh_count = point_count = face_count = 0
    for part_index, part in enumerate(parts):
        need(type(part) is dict and type(part.get('index')) is int and part['index'] == part_index,
             'NATIVE_BODY_PART_ORDINAL')
        part_name = text(part.get('name'), 'NATIVE_BODY_PART_NAME', 63)
        need(part_name not in part_names, 'DUPLICATE_BODY_NAME_OUTSIDE_PROFILE')
        part_names.add(part_name)
        models = part.get('models')
        need(type(models) is list and len(models) <= MAX_MODELS, 'BOUNDED_NATIVE_MODEL_TABLE')
        expected_models = []
        for model_index, model in enumerate(models):
            model_count += 1
            need(model_count <= MAX_MODELS and type(model) is dict and
                 type(model.get('index')) is int and model['index'] == model_index, 'NATIVE_MODEL_ORDINAL_OR_BUDGET')
            name = text(model.get('logical_name'), 'NATIVE_LOGICAL_MODEL_NAME', 63)
            start = integer(model.get('vertex_start'), MAX_POINTS, 'NATIVE_MODEL_START')
            count = integer(model.get('vertex_count'), MAX_POINTS, 'NATIVE_MODEL_COUNT')
            need(start + count <= MAX_POINTS, 'NATIVE_MODEL_RANGE_BUDGET')
            meshes = model.get('meshes')
            need(type(meshes) is list and len(meshes) <= MAX_MESHES, 'BOUNDED_NATIVE_MESH_TABLE')
            expected_meshes = []
            for mesh_index, mesh in enumerate(meshes):
                mesh_count += 1
                need(mesh_count <= MAX_MESHES and type(mesh) is dict and
                     type(mesh.get('index')) is int and mesh['index'] == mesh_index, 'NATIVE_MESH_ORDINAL_OR_BUDGET')
                raw_material = integer(mesh.get('material_index'), len(materials) - 1, 'RAW_MESH_TEXTURE_DOMAIN')
                mesh_start = integer(mesh.get('vertex_start'), count, 'NATIVE_MESH_VERTEX_START')
                mesh_vertices = integer(mesh.get('vertex_count'), count, 'NATIVE_MESH_VERTEX_COUNT')
                need(mesh_start + mesh_vertices <= count, 'NATIVE_MESH_VERTEX_RANGE')
                expected_meshes.append((raw_material, mesh_start, mesh_vertices))
            expected_models.append((name, start, count, tuple(expected_meshes)))
            if count:
                used_raw_mesh_materials.update(row[0] for row in expected_meshes)
                need(name not in model_facts and name in point_models, 'UNIQUE_RENDERABLE_NATIVE_MODEL_DOMAIN')
                point_model = point_models[name]
                need(type(point_model) is dict, 'NATIVE_POINT_MODEL_SCHEMA')
                indices, corners, face_materials = point_model.get('ids'), point_model.get('corners'), point_model.get('materials')
                need(type(indices) is list and 0 < len(indices) <= MAX_POINTS and
                     type(corners) is list and 0 < len(corners) <= MAX_FACES * 3 and len(corners) % 3 == 0 and
                     type(face_materials) is list and len(face_materials) * 3 == len(corners), 'NATIVE_FACE_POINT_CARDINALITY')
                for index in indices:
                    integer(index, start + count - 1, 'NATIVE_POINT_MODEL_RANGE', start)
                for corner in corners:
                    integer(corner, len(indices) - 1, 'NATIVE_CORNER_INDEX_DOMAIN')
                used_raw = {row[0] for row in expected_meshes}
                faces = tuple(integer(value, len(materials) - 1, 'NATIVE_FACE_MATERIAL_DOMAIN') for value in face_materials)
                need(all(value in used_raw for value in faces), 'NATIVE_FACE_MATERIAL_NOT_IN_MODEL_MESHES')
                point_count += len(indices); face_count += len(faces)
                need(point_count <= MAX_POINTS and face_count <= MAX_FACES, 'AGGREGATE_POINT_FACE_BUDGET')
                model_facts[name] = dict(start=start, count=count, faces=faces, slots=tuple(sorted(set(faces))))
        part_facts.append((part_name, tuple(expected_models)))
    need(set(point_models) == set(model_facts), 'NATIVE_RENDERABLE_MODEL_DOMAIN_DIFFERS')
    need(bool(skin_facts), 'DEFAULT_SKIN_FAMILY_REQUIRED_FOR_CLOSED_BINDING_PROFILE')
    need(all(raw < skin_refs for raw in used_raw_mesh_materials), 'USED_RAW_MESH_OUTSIDE_NATIVE_SKIN_REFERENCE_DOMAIN')
    need(all(skin_facts[0][raw] == raw for raw in used_raw_mesh_materials),
         'SOURCEIO_RAW_DEFAULT_SKIN_NONIDENTITY_REFUSED_WITHOUT_REPAIR')
    return dict(identities=identities, checksum=checksum, materials=tuple(material_facts),
                skins=tuple(skin_facts), skin_refs=skin_refs, parts=tuple(part_facts), models=model_facts,
                points=point_count, faces=face_count, model_records=model_count, mesh_records=mesh_count,
                used_raw_mesh_materials=tuple(sorted(used_raw_mesh_materials)))


class MaterialBinding:
    """One collector; failures latch even if an outer importer swallows them.

    Exact snapshot schema is documented in README. Source parser objects and
    fresh non-evaluated Blender IDs are retained by identity, never rediscovered
    using names, equality, proximity or an old B snapshot. Type admission is a
    host duty: classes supplied here must be the genuine pinned API classes.
    """
    def __init__(self, native, material_metadata, *, source_material_type, source_model_type,
                 source_body_type, source_mesh_type, object_type, mesh_types, material_type):
        classes = (source_material_type, source_model_type, source_body_type, source_mesh_type,
                   object_type, material_type)
        need(all(isinstance(value, type) for value in classes) and type(mesh_types) is tuple and
             0 < len(mesh_types) <= 2 and all(isinstance(value, type) for value in mesh_types), 'EXACT_HOST_API_CLASSES_REQUIRED')
        self.facts = facts_from_independent(native, material_metadata)
        self.source_material_type, self.source_model_type = source_material_type, source_model_type
        self.source_body_type, self.source_mesh_type = source_body_type, source_mesh_type
        self.object_type, self.mesh_types, self.material_type = object_type, mesh_types, material_type
        self.source_refs = None
        self.records = {}
        self.closed, self.failed = False, None

    def _source(self, snapshot):
        material_rows = tuple_of(snapshot['source_materials'], MAX_MATERIALS, 'SOURCE_MATERIAL_SNAPSHOT', 1)
        need(len(material_rows) == len(self.facts['materials']), 'SOURCE_MATERIAL_CARDINALITY_DIFFERS')
        source_refs, placeholders = [], []
        for row, expected in zip(material_rows, self.facts['materials']):
            need(type(row) is tuple and len(row) == 7, 'SOURCE_MATERIAL_ROW_SCHEMA')
            ref, name, flags, used, placeholder, actual_name, full_path = row
            need(type(ref) is self.source_material_type and type(placeholder) is self.material_type and
                 placeholder.original is placeholder, 'GENUINE_SOURCE_AND_NEW_MATERIAL_REFS_REQUIRED')
            need(type(name) is str and type(flags) is int and type(used) is int and (name, flags, used) == expected and
                 type(ref.name) is str and ref.name == name and type(ref.flags) is int and ref.flags == flags and
                 type(ref.used) is int and ref.used == used and ref.bpy_material is placeholder,
                 'SOURCE_MATERIAL_FIELDS_OR_PLACEHOLDER_DIFFERS')
            need(type(actual_name) is str and actual_name == name and placeholder.name == actual_name and
                 type(full_path) is str and full_path == name.lstrip('/').casefold() and
                 placeholder.get('full_path') == full_path, 'NO_MATERIAL_IO_PLACEHOLDER_NAME_OR_PATH_DIFFERS')
            need(all(prior is not ref for prior in source_refs) and all(prior is not placeholder for prior in placeholders),
                 'ALIASED_NATIVE_OR_PLACEHOLDER_MATERIAL_OUTSIDE_PROFILE')
            source_refs.append(ref); placeholders.append(placeholder)
        source_skins = tuple_of(snapshot['source_skins'], MAX_MATERIALS, 'SOURCE_SKIN_SNAPSHOT')
        need(len(source_skins) == len(self.facts['skins']), 'SOURCE_SKIN_FAMILY_CARDINALITY_DIFFERS')
        for actual, expected in zip(source_skins, self.facts['skins']):
            tuple_of(actual, MAX_MATERIALS, 'SOURCE_SKIN_ROW_SCHEMA')
            need(len(actual) == len(expected) and all(ref is source_refs[index] for ref, index in zip(actual, expected)),
                 'SOURCE_SKIN_MATERIAL_IDENTITY_DIFFERS')
        actual_parts = tuple_of(snapshot['source_parts'], MAX_PARTS, 'SOURCE_BODY_SNAPSHOT', 1)
        need(len(actual_parts) == len(self.facts['parts']), 'SOURCE_BODY_CARDINALITY_DIFFERS')
        body_refs, model_refs, mesh_refs, renderable = [], [], [], {}
        for actual_part, (part_name, expected_models) in zip(actual_parts, self.facts['parts']):
            need(type(actual_part) is tuple and len(actual_part) == 3, 'SOURCE_BODY_ROW_SCHEMA')
            part, actual_name, models = actual_part
            need(type(part) is self.source_body_type and type(actual_name) is str and actual_name == part_name and
                 part.name == actual_name and all(prior is not part for prior in body_refs), 'SOURCE_BODY_REF_OR_NAME_DIFFERS')
            body_refs.append(part)
            tuple_of(models, MAX_MODELS, 'SOURCE_MODEL_SNAPSHOT')
            need(len(models) == len(expected_models) == len(part.models), 'SOURCE_MODEL_CARDINALITY_DIFFERS')
            for model_index, (actual_model, expected_model) in enumerate(zip(models, expected_models)):
                need(type(actual_model) is tuple and len(actual_model) == 5, 'SOURCE_MODEL_ROW_SCHEMA')
                model, name, start, count, meshes = actual_model
                expected_name, expected_start, expected_count, expected_meshes = expected_model
                need(type(model) is self.source_model_type and part.models[model_index] is model and
                     all(prior is not model for prior in model_refs) and type(name) is str and
                     type(start) is int and type(count) is int and (name, start, count) ==
                     (expected_name, expected_start, expected_count) and model.name == name and
                     type(model.vertex_offset) is int and model.vertex_offset == start and
                     type(model.vertex_count) is int and model.vertex_count == count, 'SOURCE_MODEL_IDENTITY_OR_RANGE_DIFFERS')
                model_refs.append(model)
                tuple_of(meshes, MAX_MESHES, 'SOURCE_MESH_SNAPSHOT')
                need(len(meshes) == len(expected_meshes) == len(model.meshes), 'SOURCE_MESH_CARDINALITY_DIFFERS')
                for mesh_index, (actual_mesh, expected_mesh) in enumerate(zip(meshes, expected_meshes)):
                    need(type(actual_mesh) is tuple and len(actual_mesh) == 4, 'SOURCE_MESH_ROW_SCHEMA')
                    mesh, raw, start_in_model, vertices = actual_mesh
                    need(type(mesh) is self.source_mesh_type and model.meshes[mesh_index] is mesh and
                         all(prior is not mesh for prior in mesh_refs) and all(type(value) is int for value in (raw, start_in_model, vertices)) and
                         (raw, start_in_model, vertices) == expected_mesh and
                         type(mesh.material_index) is int and mesh.material_index == raw and
                         type(mesh.vertex_index_start) is int and mesh.vertex_index_start == start_in_model and
                         type(mesh.vertex_count) is int and mesh.vertex_count == vertices, 'SOURCE_MESH_IDENTITY_OR_FIELDS_DIFFER')
                    mesh_refs.append(mesh)
                if count:
                    renderable[name] = model
        refs = tuple(source_refs), tuple(placeholders), tuple(body_refs), tuple(model_refs), tuple(mesh_refs)
        if self.source_refs is None:
            self.source_refs = refs
        else:
            need(all(len(a) == len(b) and all(left is right for left, right in zip(a, b))
                     for a, b in zip(refs, self.source_refs)), 'SOURCE_OR_PLACEHOLDER_REFERENCE_CHANGED')
        return tuple(placeholders), renderable

    def _snapshot(self, obj, mesh, snapshot, fact, early):
        need(type(snapshot) is dict and set(snapshot) == SNAPSHOT_KEYS, 'EXACT_MATERIAL_SNAPSHOT_SCHEMA')
        need(type(obj) is self.object_type and type(mesh) in self.mesh_types and obj.data is mesh and
             obj.original is obj and mesh.original is mesh, 'GENUINE_NEW_OBJECT_MESH_REFS_REQUIRED')
        placeholders, models = self._source(snapshot)
        need(type(snapshot['active_skin']) is str and snapshot['active_skin'] == '0' and
             type(snapshot['model_type']) is str and snapshot['model_type'] == 's1' and
             obj.get('active_skin') == '0' and obj.get('model_type') == 's1', 'DEFAULT_SOURCEIO_MODEL_PROPERTIES_DIFFER')
        slots = tuple_of(snapshot['slots'], MAX_MATERIALS, 'MESH_SLOT_SNAPSHOT')
        object_slots = tuple_of(snapshot['object_slots'], MAX_MATERIALS, 'OBJECT_SLOT_SNAPSHOT')
        need(len(slots) == len(mesh.materials) and all(actual is slot for actual, slot in zip(mesh.materials, slots)),
             'SNAPSHOT_NOT_ACTUAL_MESH_SLOT_REFERENCES')
        need(len(object_slots) == len(obj.material_slots) == len(slots) and
             all(slot.material is material and slot.link == 'DATA' for slot, material in zip(obj.material_slots, object_slots)) and
             all(left is right for left, right in zip(slots, object_slots)), 'OBJECT_AND_MESH_DATA_SLOTS_DIFFER')
        expected_raw = () if early else fact['slots']
        need(len(slots) == len(expected_raw) and all(slot is placeholders[index] for slot, index in zip(slots, expected_raw)),
             'EXACT_RAW_MATERIAL_TO_PLACEHOLDER_SLOT_MAPPING_DIFFERS')
        faces = tuple_of(snapshot['faces'], MAX_FACES, 'POLYGON_SNAPSHOT', 1)
        need(len(faces) == len(fact['faces']) == len(mesh.polygons), 'POLYGON_CARDINALITY_DIFFERS')
        raw_to_slot = {raw: slot for slot, raw in enumerate(fact['slots'])}
        for index, (face, raw_material) in enumerate(zip(faces, fact['faces'])):
            need(type(face) is tuple and len(face) == 4 and all(type(value) is int for value in face),
                 'EXACT_POLYGON_INTEGER_FIELDS_REQUIRED')
            expected_slot = 0 if early else raw_to_slot[raw_material]
            need(face == (index, index * 3, 3, expected_slot), 'ORDERED_WHOLE_POLYGON_MATERIAL_STREAM_DIFFERS')
            actual = mesh.polygons[index]
            need(all(type(value) is int for value in (actual.index, actual.loop_start, actual.loop_total, actual.material_index)) and
                 (actual.index, actual.loop_start, actual.loop_total, actual.material_index) == face,
                 'SNAPSHOT_NOT_ACTUAL_POLYGON_FIELDS')
        skin_rows = snapshot['skin_groups']
        if early:
            need(skin_rows is None and obj.get('skin_groups') is None, 'SKIN_PROPERTY_ASSIGNED_BEFORE_EXPECTED_BOUNDARY')
            mode = 'ABSENT'
        else:
            tuple_of(skin_rows, MAX_MATERIALS, 'SKIN_PROPERTY_ROWS')
            need(len(skin_rows) == len(self.facts['skins']), 'SKIN_PROPERTY_FAMILY_CARDINALITY_DIFFERS')
            modes = set()
            for family_index, (row, expected) in enumerate(zip(skin_rows, self.facts['skins'])):
                need(type(row) is tuple and len(row) == 2 and type(row[0]) is str and row[0] == str(family_index),
                     'SKIN_PROPERTY_ORDERED_KEY_DOMAIN')
                values = tuple_of(row[1], MAX_MATERIALS, 'SKIN_PROPERTY_VALUE_SEQUENCE')
                need(len(values) == len(expected), 'SKIN_PROPERTY_REFERENCE_WIDTH')
                if all(type(value) is self.material_type for value in values):
                    mode = 'MATERIAL_ID'
                    need(all(value is placeholders[index] for value, index in zip(values, expected)), 'SKIN_PROPERTY_MATERIAL_IDENTITY_DIFFERS')
                elif all(type(value) is str for value in values):
                    mode = 'STRING'
                    need(all(value == placeholders[index].name for value, index in zip(values, expected)), 'SKIN_PROPERTY_EXACT_NAME_FALLBACK_DIFFERS')
                else:
                    raise Refusal('MIXED_OR_UNTYPED_SKIN_PROPERTY_REFUSED')
                modes.add(mode)
            need(len(modes) <= 1, 'MIXED_SKIN_STORAGE_BRANCHES_REFUSED')
            mode = next(iter(modes)) if modes else 'EMPTY'
            actual_skins = obj.get('skin_groups')
            need(actual_skins is not None and len(actual_skins) == len(skin_rows) and
                 tuple(actual_skins.keys()) == tuple(row[0] for row in skin_rows),
                 'SNAPSHOT_NOT_ACTUAL_SKIN_PROPERTY_KEYS')
            for key, values in skin_rows:
                actual_values = actual_skins[key]
                need(len(actual_values) == len(values) and all(
                    (left is right if mode == 'MATERIAL_ID' else type(left) is str and left == right)
                    for left, right in zip(actual_values, values)), 'SNAPSHOT_NOT_ACTUAL_SKIN_PROPERTY_VALUES')
        return models, mode

    def observe(self, phase, model, obj, mesh, snapshot):
        try:
            need(self.failed is None and not self.closed and type(phase) is str and phase in PHASES, 'COLLECTOR_FAILED_CLOSED_OR_PHASE_INVALID')
            need(type(model) is self.source_model_type and type(model.name) is str and model.name in self.facts['models'],
                 'OBSERVED_MODEL_NOT_NATIVE_RENDERABLE')
            name, fact = model.name, self.facts['models'][model.name]
            if phase == PHASES[0]:
                need(name not in self.records and all(row['obj'] is not obj and row['mesh'] is not mesh
                                                     for row in self.records.values()), 'REPEATED_OR_ALIASED_OBJECT_CREATION')
                self.records[name] = dict(model=model, obj=obj, mesh=mesh, phases=[], mode=None)
            need(name in self.records, 'CREATION_BOUNDARY_MISSING')
            record = self.records[name]
            need(record['model'] is model and record['obj'] is obj and record['mesh'] is mesh,
                 'OBSERVED_OBJECT_MESH_OR_MODEL_IDENTITY_CHANGED')
            need(len(record['phases']) < 4 and phase == PHASES[len(record['phases'])], 'OBSERVED_PHASE_ORDER_OR_REPLAY')
            models, mode = self._snapshot(obj, mesh, snapshot, fact, len(record['phases']) < 2)
            need(models[name] is model, 'OBSERVED_MODEL_NOT_BOUND_SOURCE_MODEL')
            if mode != 'ABSENT':
                need(record['mode'] is None or record['mode'] == mode, 'SKIN_STORAGE_BRANCH_CHANGED')
                record['mode'] = mode
            record['phases'].append(phase)
        except BaseException as error:
            self.failed = str(error) if isinstance(error, Refusal) else 'MATERIAL_OBSERVER_API_FAILURE'
            raise

    def returned(self, container, snapshots):
        try:
            need(self.failed is None and not self.closed and set(self.records) == set(self.facts['models']) and
                 all(tuple(row['phases']) == PHASES for row in self.records.values()), 'INCOMPLETE_OR_FAILED_MATERIAL_OBSERVATION')
            objects = container.objects
            expected_names = [model[0] for _, models in self.facts['parts'] for model in models if model[2]]
            need(type(objects) is list and len(objects) == len(expected_names) and
                 all(actual is self.records[name]['obj'] for actual, name in zip(objects, expected_names)),
                 'RETURNED_RENDERABLE_OBJECT_ORDER_OR_IDENTITY_DIFFERS')
            need(type(container.bodygroups) in (dict, defaultdict) and tuple(container.bodygroups) ==
                 tuple(part[0] for part in self.facts['parts']), 'RETURNED_BODYGROUP_DOMAIN_OR_ORDER_DIFFERS')
            for part_name, models in self.facts['parts']:
                actual = container.bodygroups[part_name]
                need(type(actual) is list and len(actual) == len(models) and all(
                    value is (self.records[model[0]]['obj'] if model[2] else None)
                    for value, model in zip(actual, models)), 'RETURNED_BODYGROUP_MODEL_OR_BLANK_IDENTITY_DIFFERS')
            need(type(snapshots) is list and len(snapshots) == len(objects), 'RETURNED_MATERIAL_SNAPSHOT_CARDINALITY')
            for (obj, snapshot), name in zip(snapshots, expected_names):
                record = self.records[name]
                need(obj is record['obj'] and obj.data is record['mesh'], 'RETURNED_OBJECT_OR_MESH_CHANGED')
                models, mode = self._snapshot(obj, record['mesh'], snapshot, self.facts['models'][name], False)
                need(models[name] is record['model'] and mode == record['mode'], 'RETURNED_MODEL_OR_SKIN_STORAGE_CHANGED')
            self.closed = True
            rows = [dict(faces=len(self.facts['models'][name]['faces']), slots=len(self.facts['models'][name]['slots']),
                         observed_stages=4, skin_storage=self.records[name]['mode'],
                         raw_face_material_order_sha256=hashlib.sha256(struct.pack('<' + 'I' * len(self.facts['models'][name]['faces']),
                                                                                 *self.facts['models'][name]['faces'])).hexdigest())
                    for name in expected_names]
            return dict(format='has_fresh_sourceio_raw_material_slot_skin_observation_1', models=rows,
                        native_material_records=len(self.facts['materials']), native_skin_families=len(self.facts['skins']),
                        native_skin_references=self.facts['skin_refs'], native_body_parts=len(self.facts['parts']),
                        native_model_records=self.facts['model_records'], native_mesh_records=self.facts['mesh_records'],
                        used_raw_mesh_material_count=len(self.facts['used_raw_mesh_materials']),
                        sourceio_raw_matches_candidate_default_skin_on_used_meshes=True,
                        candidate_default_skin_row_sha256=hashlib.sha256(struct.pack('<' + 'I' * len(self.facts['skins'][0]),
                                                                                  *self.facts['skins'][0])).hexdigest(),
                        observed_models=len(rows), observed_faces=self.facts['faces'],
                        exact_family_raw_material_placeholder_slot_face_binding_observed=True,
                        exact_family_skin_property_reference_or_name_storage_observed=True,
                        resolved_native_default_skin_equivalence_qualified=False,
                        native_skin_switching_qualified=False, material_files_or_B_opened=False,
                        B_dependency_closure_qualified=False, native_normal_fidelity_qualified=False,
                        carrier_or_exporter_binding_qualified=False, non_normal_semantic_equivalence_qualified=False,
                        application_adoption_qualified=False)
        except BaseException as error:
            self.failed = str(error) if isinstance(error, Refusal) else 'MATERIAL_RETURNED_API_FAILURE'
            raise
