"""Unrun bounded RAM-only MDL49 material/skin metadata candidate.

No IO, Blender, SourceIO import, geometry observations or output-derived labels.
The Root caller must authenticate the three input descriptors against its lock.
This does not decode VTX triangles, qualify face slots, or admit B resources.
"""
from bisect import bisect_left
import hashlib
import math
import re
import struct

MAX_BYTES = 128 * 1024 * 1024
MAX_POINTS = 200_000
MAX_MATERIALS = MAX_PATHS = MAX_SKINS = MAX_PARTS = 256
MAX_MODELS = 1024
MAX_MESHES = 65_536
MAX_TABLES = 4096
MAX_STRING_BYTES = 256


class Refusal(ValueError):
    pass


def need(value, code):
    if not value:
        raise Refusal(code)


def bounded(value, maximum, code, minimum=0):
    need(type(value) is int and minimum <= value <= maximum, code)
    return value


class _Binary:
    """Own only the metadata tables read here; other MDL sections stay unqualified."""
    def __init__(self, raw, minimum):
        need(type(raw) is bytes and minimum <= len(raw) <= MAX_BYTES, 'IMMUTABLE_BOUNDED_NATIVE_BYTES')
        self.raw, self.minimum = raw, minimum
        self.tables, self.starts, self.strings = [(0, minimum)], [0], []

    def unpack(self, fmt, offset):
        size = struct.calcsize(fmt)
        need(type(offset) is int and 0 <= offset <= len(self.raw) - size, 'TRUNCATED_METADATA_FIELD')
        return struct.unpack_from(fmt, self.raw, offset)

    def table(self, offset, count, stride, maximum):
        bounded(count, maximum, 'METADATA_TABLE_COUNT_BUDGET')
        need(type(offset) is int and 0 <= offset <= len(self.raw), 'METADATA_TABLE_OFFSET_DOMAIN')
        if not count:
            return offset
        need(offset >= self.minimum and count <= (len(self.raw) - offset) // stride,
             'TRUNCATED_OR_HEADER_ALIASED_TABLE')
        need(len(self.tables) < MAX_TABLES, 'METADATA_TABLE_NUMBER_BUDGET')
        end = offset + count * stride
        index = bisect_left(self.starts, offset)
        need((index == 0 or self.tables[index - 1][1] <= offset) and
             (index == len(self.tables) or end <= self.tables[index][0]), 'OVERLAPPING_METADATA_TABLES')
        self.starts.insert(index, offset)
        self.tables.insert(index, (offset, end))
        return offset

    def relative_table(self, base, relative, count, stride, maximum):
        need(type(relative) is int and (relative > 0 or count == 0 and relative == 0),
             'RELATIVE_METADATA_TABLE_OFFSET')
        return self.table(base + relative, count, stride, maximum)

    def string(self, base, relative, *, empty=False, maximum=MAX_STRING_BYTES):
        # Source1 offset zero means an empty string, not an address at `base`.
        need(type(relative) is int and relative >= 0, 'NEGATIVE_STRING_OFFSET_OUTSIDE_PROFILE')
        if relative == 0:
            need(empty, 'EMPTY_REQUIRED_METADATA_NAME')
            return ''
        offset = base + relative
        need(self.minimum <= offset < len(self.raw), 'STRING_OFFSET_DOMAIN')
        end = self.raw.find(b'\0', offset, min(len(self.raw), offset + maximum + 1))
        need(end >= 0, 'UNTERMINATED_OR_OVERLONG_METADATA_STRING')
        value = self.raw[offset:end]
        need((empty or bool(value)) and all(32 <= byte < 127 for byte in value), 'PRINTABLE_ASCII_METADATA_PROFILE')
        self.strings.append((offset, end + 1))
        return value.decode('ascii')

    def finish(self):
        # Shared/duplicate string spans are permitted; none may alias a table.
        for start, end in self.strings:
            index = bisect_left(self.starts, end)
            need(index == 0 or self.tables[index - 1][1] <= start, 'STRING_ALIASES_METADATA_TABLE')


def _admit(native_refs):
    need(type(native_refs) is dict and set(native_refs) == {'mdl', 'vvd', 'vtx'}, 'EXACT_THREE_NATIVE_INPUTS')
    raw, identities = {}, {}
    for role in ('mdl', 'vvd', 'vtx'):
        row = native_refs[role]
        need(type(row) is dict and set(row) == {'raw', 'bytes', 'sha256'}, 'EXACT_NATIVE_DESCRIPTOR_SCHEMA')
        value, count, digest = row['raw'], row['bytes'], row['sha256']
        need(type(value) is bytes and 0 < len(value) <= MAX_BYTES and type(count) is int and count == len(value),
             'NATIVE_DESCRIPTOR_BYTES_OR_SIZE')
        need(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest) is not None and
             hashlib.sha256(value).hexdigest() == digest, 'NATIVE_DESCRIPTOR_SHA256')
        raw[role] = value
        identities[role] = dict(bytes=count, sha256=digest)
    return raw, identities


def _vvd_header(raw):
    reader = _Binary(raw, 64)
    header = reader.unpack('<4s15I', 0)
    magic, version, checksum, lods = header[:4]
    need(magic == b'IDSV' and version == 4, 'VVD4_SIGNATURE_VERSION')
    bounded(lods, 8, 'VVD_LOD_COUNT', 1)
    counts = header[4:12]
    bounded(counts[0], MAX_POINTS, 'VVD_LOD0_COUNT', 1)
    need(all(0 < value <= counts[0] for value in counts[:lods]), 'VVD_ACTIVE_LOD_COUNT')
    fixups, fixup_offset, vertex_offset, tangent_offset = header[12:]
    reader.table(fixup_offset, fixups, 12, MAX_POINTS)
    reader.table(vertex_offset, counts[0], 48, MAX_POINTS)
    reader.table(tangent_offset, counts[0], 16, MAX_POINTS)
    need(tangent_offset + counts[0] * 16 == len(raw), 'VVD_TRAILING_OR_EXTRA_UV_PROFILE')
    return checksum, counts[0]


def _mdl_materials(raw, checksum, point_count):
    reader = _Binary(raw, 408)
    magic, version, actual_checksum = reader.unpack('<4sII', 0)
    need(magic == b'IDST' and version == 49, 'MDL49_SIGNATURE_VERSION')
    need(actual_checksum == checksum, 'NATIVE_FAMILY_CHECKSUM')
    need(reader.unpack('<I', 76)[0] == len(raw), 'MDL_DECLARED_SIZE')
    need(reader.unpack('<I', 152)[0] & 0x10 == 0, 'STATIC_PROP_OUTSIDE_PROFILE')
    material_count, material_offset, path_count, path_offset, skin_refs, skin_count, skin_offset = reader.unpack('<7I', 204)
    bounded(material_count, MAX_MATERIALS, 'MATERIAL_COUNT_BUDGET', 1)
    reader.table(material_offset, material_count, 64, MAX_MATERIALS)
    reader.table(path_offset, path_count, 4, MAX_PATHS)
    bounded(skin_refs, MAX_MATERIALS, 'SKIN_REFERENCE_COUNT_BUDGET')
    bounded(skin_count, MAX_SKINS, 'SKIN_FAMILY_COUNT_BUDGET')
    need(bool(skin_refs) == bool(skin_count), 'PARTIAL_EMPTY_SKIN_DIMENSIONS')
    reader.table(skin_offset, skin_refs * skin_count, 2, MAX_MATERIALS * MAX_SKINS)
    materials = []
    for index in range(material_count):
        entry = material_offset + 64 * index
        relative, flags, used = reader.unpack('<iII', entry)
        name = reader.string(entry, relative)
        materials.append(dict(index=index, name=name, flags=flags, used=used,
                              descriptor_sha256=hashlib.sha256(raw[entry:entry + 64]).hexdigest()))
    paths = [reader.string(0, reader.unpack('<i', path_offset + 4 * index)[0], empty=True)
             for index in range(path_count)]
    skins = []
    for family in range(skin_count):
        indices = list(reader.unpack('<' + 'H' * skin_refs, skin_offset + family * skin_refs * 2))
        need(all(index < material_count for index in indices), 'SKIN_MATERIAL_INDEX_DOMAIN')
        skins.append(indices)
    part_count, part_offset = reader.unpack('<2I', 232)
    bounded(part_count, MAX_PARTS, 'BODY_PART_COUNT_BUDGET', 1)
    reader.table(part_offset, part_count, 16, MAX_PARTS)
    parts, models_total, meshes_total, vertices_total = [], 0, 0, 0
    logical_names = set()
    for part_index in range(part_count):
        base = part_offset + 16 * part_index
        name_relative, model_count, body_base, model_relative = reader.unpack('<4I', base)
        part_name = reader.string(base, name_relative, maximum=63)
        models_total += model_count
        bounded(models_total, MAX_MODELS, 'AGGREGATE_MODEL_BUDGET')
        model_offset = reader.relative_table(base, model_relative, model_count, 148, MAX_MODELS)
        models = []
        for model_index in range(model_count):
            entry = model_offset + 148 * model_index
            fixed = raw[entry:entry + 64]
            need(b'\0' in fixed, 'UNTERMINATED_FIXED_MODEL_NAME')
            name_bytes = fixed.split(b'\0', 1)[0]
            need(all(32 <= byte < 127 for byte in name_bytes), 'PRINTABLE_ASCII_MODEL_NAME')
            native_name = name_bytes.decode('ascii')
            mesh_count, mesh_relative, vertices, byte_start = reader.unpack('<4I', entry + 72)
            bounded(vertices, MAX_POINTS, 'MODEL_VERTEX_COUNT')
            need(byte_start % 48 == 0 and byte_start // 48 <= point_count and
                 vertices <= point_count - byte_start // 48, 'MODEL_VVD_RANGE_OR_BYTE_ALIGNMENT')
            vertices_total += vertices
            bounded(vertices_total, MAX_POINTS, 'AGGREGATE_MODEL_VERTEX_BUDGET')
            if vertices:
                need(bool(native_name) and native_name not in logical_names, 'UNIQUE_RENDERABLE_LOGICAL_NAME')
                logical_names.add(native_name)
                need(mesh_count > 0, 'RENDERABLE_MODEL_REQUIRES_MESH_METADATA')
            else:
                need(bool(native_name) or not any(fixed), 'EMPTY_MODEL_NAME_PADDING_PROFILE')
            eyeballs = reader.unpack('<I', entry + 100)[0]
            need(eyeballs == 0, 'EYEBALLS_OUTSIDE_PROFILE')
            meshes_total += mesh_count
            bounded(meshes_total, MAX_MESHES, 'AGGREGATE_MESH_BUDGET')
            mesh_offset = reader.relative_table(entry, mesh_relative, mesh_count, 116, MAX_MESHES)
            meshes = []
            for mesh_index in range(mesh_count):
                mesh_entry = mesh_offset + 116 * mesh_index
                material, _model_offset, count, start, flexes = reader.unpack('<Ii3I', mesh_entry)
                need(material < material_count, 'MESH_MATERIAL_INDEX_DOMAIN')
                need(start <= vertices and count <= vertices - start, 'MDL_MESH_VERTEX_RANGE')
                need(flexes == 0, 'FLEXES_OUTSIDE_PROFILE')
                material_type, material_parameter = reader.unpack('<2I', mesh_entry + 24)
                meshes.append(dict(index=mesh_index, material_index=material,
                                   vertex_start=start, vertex_count=count,
                                   material_type=material_type, material_parameter=material_parameter))
            models.append(dict(index=model_index, native_name=native_name,
                               logical_name=native_name or 'blank', vertex_start=byte_start // 48,
                               vertex_count=vertices, meshes=meshes))
        parts.append(dict(index=part_index, name=part_name, body_base=body_base, models=models))
    need(bool(logical_names), 'RENDERABLE_LOGICAL_MODEL_REQUIRED')
    reader.finish()
    return dict(materials=materials, search_paths=paths, skin_reference_count=skin_refs,
                skin_families=skins, body_parts=parts,
                model_records=models_total, mesh_records=meshes_total)


def _vtx_metadata(raw, checksum, parts):
    reader = _Binary(raw, 36)
    version, _cache, strip_bones, _triangle_bones, vertex_bones, actual, lods, replacements, part_count, part_offset = reader.unpack('<IIHH6I', 0)
    need(version == 7 and vertex_bones == 3 and lods == 1, 'STANDARD_VTX7_THREE_SLOT_ONE_LOD_PROFILE')
    bounded(strip_bones, 512, 'VTX_STRIP_BONE_HEADER', 1)
    need(actual == checksum, 'NATIVE_FAMILY_CHECKSUM')
    reader.table(replacements, 1, 8, 1)
    replacement_count, relative = reader.unpack('<2i', replacements)
    need(replacement_count == 0 and 0 <= replacements + relative <= len(raw), 'VTX_MATERIAL_REPLACEMENTS_OUTSIDE_PROFILE')
    need(part_count == len(parts), 'VTX_MDL_BODY_PART_COUNT')
    reader.table(part_offset, part_count, 8, MAX_PARTS)
    for part_index, part in enumerate(parts):
        base = part_offset + part_index * 8
        models, relative = reader.unpack('<2I', base)
        need(models == len(part['models']), 'VTX_MDL_MODEL_COUNT')
        model_offset = reader.relative_table(base, relative, models, 8, MAX_MODELS)
        for index, model in enumerate(part['models']):
            entry = model_offset + index * 8
            lod_count, lod_relative = reader.unpack('<2i', entry)
            need(lod_count == 1, 'VTX_MODEL_LOD_COUNT')
            lod_offset = reader.relative_table(entry, lod_relative, 1, 12, 1)
            meshes, mesh_relative, switch_point = reader.unpack('<2If', lod_offset)
            need(math.isfinite(switch_point) and meshes == len(model['meshes']), 'VTX_MDL_MESH_COUNT_OR_SWITCH')
            reader.relative_table(lod_offset, mesh_relative, meshes, 9, MAX_MESHES)
            # Strip groups, indices and per-face order are deliberately not read.


def derive_material_metadata(native_refs):
    """Return PRIVATE metadata only; caller authenticates descriptors via Root lock.

    Validates MDL49 material/skin/mesh metadata plus VVD4 table extents and VTX7
    body/model/LOD/mesh header correspondence. No native geometry is decoded.
    No Blender material/slot IDs or B observations can enter this derivation.
    """
    raw, identities = _admit(native_refs)
    checksum, point_count = _vvd_header(raw['vvd'])
    metadata = _mdl_materials(raw['mdl'], checksum, point_count)
    _vtx_metadata(raw['vtx'], checksum, metadata['body_parts'])
    return dict(format='has_private_mdl49_material_skin_metadata_candidate_1',
                checksum=checksum, source_identities=identities, metadata=metadata,
                native_geometry_qualified=False, VTX_face_material_order_qualified=False,
                Blender_face_slot_binding_qualified=False, B_dependency_closure_qualified=False,
                historical_B_identity_qualified=False, resource_or_export_qualified=False,
                normal_fidelity_qualified=False, application_adoption_qualified=False)
