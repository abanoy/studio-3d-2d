"""Bounded, RAM-only MDL49/VVD4/VTX7 source-derived point expectation.

This is an unqualified CPU candidate, not a native launcher or export repair.
No scene, carrier, saved snapshot, setter payload or nearest-match data enters
the derivation. The observed setter ID order is compared only at the end.
Input byte identities must come from a separately admitted immutable lock.
Returned native arrays and names are private; do not publish them.
"""
import hashlib
from bisect import bisect_left
import math
import re
import struct

MAX_BYTES = 128 * 1024 * 1024
MAX_POINTS = 200_000
MAX_CORNERS = 1_000_000
MAX_BONES = 256
MAX_MODELS = 1024
MAX_TABLES = 16_384
MAX_BONE_STATE_ROWS = 200_000
UNIT_TOLERANCE = 2.5e-7
COORDINATE_POLICY = 'sourceio_mdl49_standalone_01905_identity_standard_vtx7_1'
F32_SCALE = struct.unpack('<f', struct.pack('<f', .01905))[0]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, label)
    return value


def f32(value):
    try:
        result = struct.unpack('<f', struct.pack('<f', value))[0]
    except (OverflowError, struct.error) as error:
        raise ValueError('F32 arithmetic overflow') from error
    require(math.isfinite(result), 'Nonfinite F32 arithmetic')
    return result


def _ascii(raw, label, maximum=63):
    require(type(raw) is bytes and 1 <= len(raw) <= maximum and
            all(32 <= value < 127 for value in raw), 'Bounded ASCII ' + label + ' required')
    return raw.decode('ascii')


class _Reader:
    def __init__(self, raw, label, minimum):
        require(type(raw) is bytes and minimum <= len(raw) <= MAX_BYTES,
                'Bounded immutable ' + label + ' bytes required')
        self.raw, self.label, self.minimum = raw, label, minimum
        self.tables = [(0, minimum, 'header')]
        self._starts = [0]

    def unpack(self, fmt, offset):
        size = struct.calcsize(fmt)
        require(type(offset) is int and 0 <= offset <= len(self.raw) - size,
                'Truncated ' + self.label + ' field')
        return struct.unpack_from(fmt, self.raw, offset)

    def table(self, offset, count, stride, label, maximum=MAX_POINTS):
        integer(count, 0, maximum, 'Table count budget: ' + label)
        require(type(offset) is int and self.minimum <= offset <= len(self.raw) and
                count * stride <= len(self.raw) - offset, 'Truncated/invalid table: ' + label)
        require(len(self.tables) < MAX_TABLES, 'Table-count budget')
        if count:
            end = offset + count * stride
            position = bisect_left(self._starts, offset)
            require((position == 0 or self.tables[position - 1][1] <= offset) and
                    (position == len(self.tables) or end <= self.tables[position][0]),
                    'Overlapping table: ' + label)
            self._starts.insert(position, offset)
            self.tables.insert(position, (offset, end, label))
        return offset

    def relative_table(self, base, relative, count, stride, label, maximum=MAX_POINTS):
        require(type(relative) is int and relative > 0, 'Positive relative table offset: ' + label)
        return self.table(base + relative, count, stride, label, maximum)

    def source_string(self, base, relative, label):
        require(type(relative) is int and relative > 0, 'Positive Source string offset required')
        start = base + relative
        require(self.minimum <= start < len(self.raw), 'Source string outside file')
        end = self.raw.find(b'\0', start, min(start + 64, len(self.raw)))
        require(end != -1, 'Unterminated/overlong Source string')
        return _ascii(self.raw[start:end], label), (start, end + 1)


def _admit_refs(native_refs):
    require(type(native_refs) is dict and set(native_refs) == {'mdl', 'vvd', 'vtx'},
            'Exact three-file native family required')
    admitted, identities = {}, {}
    for name in ('mdl', 'vvd', 'vtx'):
        row = native_refs[name]
        require(type(row) is dict and set(row) == {'raw', 'bytes', 'sha256'}, 'Exact native byte descriptor required')
        raw = row['raw']
        require(type(raw) is bytes and 1 <= len(raw) <= MAX_BYTES, 'Bounded immutable native bytes required')
        require(type(row['bytes']) is int and row['bytes'] == len(raw), 'Native byte length differs')
        digest = row['sha256']
        require(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest) is not None,
                'Explicit lowercase SHA256 required')
        require(hashlib.sha256(raw).hexdigest() == digest, 'Native SHA256 differs')
        admitted[name] = raw
        identities[name] = {'bytes': len(raw), 'sha256': digest}
    return admitted, identities


def _mdl(raw):
    reader = _Reader(raw, 'MDL', 408)
    magic, version, checksum = reader.unpack('<4sII', 0)
    require(magic == b'IDST' and version == 49, 'MDL49 IDST required')
    require(reader.unpack('<I', 76)[0] == len(raw), 'MDL declared file size differs')
    require(not reader.unpack('<I', 152)[0] & 0x10, 'Static prop outside skinned identity profile')
    bone_count, bone_offset = reader.unpack('<2I', 156)
    integer(bone_count, 1, MAX_BONES, 'Bounded native bone count required')
    reader.table(bone_offset, bone_count, 216, 'bones', MAX_BONES)
    bones, parents, strings = [], [], []
    for index in range(bone_count):
        base = bone_offset + 216 * index
        relative, parent = reader.unpack('<ii', base)
        name, span = reader.source_string(base, relative, 'bone name')
        require(-1 <= parent < index, 'Native parent must precede child')
        require(all(math.isfinite(value) for value in reader.unpack('<7f', base + 32)),
                'Nonfinite native bone rest input')
        bones.append(name); parents.append(parent); strings.append(span)
    require(len(set(bones)) == len(bones), 'Native bone names must be unique without renaming')
    part_count, part_offset = reader.unpack('<2I', 232)
    integer(part_count, 1, 256, 'Bounded MDL bodypart count required')
    reader.table(part_offset, part_count, 16, 'bodyparts', 256)
    parts, logical_names = [], set()
    model_total = 0
    for part_index in range(part_count):
        base = part_offset + 16 * part_index
        name_relative, count, _, model_relative = reader.unpack('<4I', base)
        _, span = reader.source_string(base, name_relative, 'bodypart name')
        strings.append(span)
        model_total += count
        require(model_total <= MAX_MODELS, 'Aggregate native model budget')
        model_offset = reader.relative_table(base, model_relative, count, 148, 'models', MAX_MODELS)
        models = []
        for index in range(count):
            entry = model_offset + 148 * index
            fixed_name = raw[entry:entry + 64]
            require(b'\0' in fixed_name, 'Terminated model name required')
            native_name = fixed_name.split(b'\0', 1)[0]
            mesh_count, mesh_relative, vertex_count, vertex_byte_offset = reader.unpack('<4I', entry + 72)
            # ModelV36Plus maps an empty source name to 'blank'. The importer
            # skips zero-vertex models before object-name handling. Preserve
            # that metadata case without admitting empty renderable identities.
            name = ('blank' if not fixed_name.strip(b'\0') and vertex_count == 0
                    else _ascii(native_name, 'model name'))
            eyeball_count, eyeball_relative = reader.unpack('<2I', entry + 100)
            require(eyeball_count == 0, 'Eyeballs outside point expectation profile')
            require(entry + eyeball_relative <= len(raw), 'Empty MDL eyeball seek outside source file')
            require(entry + mesh_relative <= len(raw), 'MDL mesh seek outside source file')
            require(vertex_byte_offset % 48 == 0, 'MDL vertex byte offset must be exactly divisible by 48')
            integer(vertex_count, 0, MAX_POINTS, 'Native model vertex budget')
            if vertex_count:
                require(name not in logical_names, 'Unique native logical model names required')
                logical_names.add(name)
            meshes = []
            if mesh_count:
                mesh_offset = reader.relative_table(entry, mesh_relative, mesh_count, 116, 'MDL meshes', 65536)
                for mesh_index in range(mesh_count):
                    mesh = mesh_offset + 116 * mesh_index
                    material, _, mesh_vertices, vertex_start, flex_count = reader.unpack('<Ii3I', mesh)
                    require(flex_count == 0, 'Flexes outside point expectation profile')
                    require(vertex_start <= vertex_count and mesh_vertices <= vertex_count - vertex_start,
                            'MDL mesh vertex range outside model')
                    integer(material, 0, 65535, 'Material index budget')
                    meshes.append({'material': material, 'count': mesh_vertices, 'start': vertex_start})
            require(not vertex_count or meshes, 'Renderable model requires meshes')
            models.append({'name': name, 'count': vertex_count,
                           'start': vertex_byte_offset // 48, 'meshes': meshes})
        parts.append(models)
    for start, end in strings:
        require(all(end <= table_start or table_end <= start
                    for table_start, table_end, _ in reader.tables), 'Source string overlaps structural table')
    require(logical_names, 'Nonempty native model family required')
    return {'checksum': checksum, 'bones': bones, 'parents': parents, 'parts': parts}


def _vvd(raw, checksum):
    reader = _Reader(raw, 'VVD', 64)
    header = reader.unpack('<4s15I', 0)
    magic, version, actual_checksum, lod_count = header[:4]
    require(magic == b'IDSV' and version == 4, 'VVD4 IDSV required')
    require(actual_checksum == checksum, 'Native family VVD checksum differs')
    integer(lod_count, 1, 8, 'VVD LOD-count domain')
    counts = header[4:12]
    count = integer(counts[0], 1, MAX_POINTS, 'Bounded nonempty LOD0 required')
    require(all(value <= count for value in counts[:lod_count]), 'Active LOD count outside LOD0')
    fixup_count, fixup_offset, vertex_offset, tangent_offset = header[12:16]
    reader.table(vertex_offset, count, 48, 'VVD vertices')
    require(tangent_offset > 0, 'Explicit VVD tangent table required for closed no-extra-UV profile')
    reader.table(tangent_offset, count, 16, 'VVD tangents')
    integer(fixup_count, 0, MAX_POINTS, 'VVD fixup budget')
    raw_indices = []
    if fixup_count:
        reader.table(fixup_offset, fixup_count, 12, 'VVD fixups')
        for index in range(fixup_count):
            lod, start, length = reader.unpack('<3I', fixup_offset + 12 * index)
            require(lod < 8 and start <= count and length <= count - start,
                    'VVD fixup domain/range')
            require(len(raw_indices) + length <= count, 'VVD fixup output exceeds LOD0')
            raw_indices.extend(range(start, start + length))
        require(len(raw_indices) == count, 'Incomplete VVD LOD0 fixup coverage')
    else:
        raw_indices = list(range(count))
    require(tangent_offset + count * 16 == len(raw),
            'Trailing VVD data/extra UV attributes outside closed profile')
    rows = []
    for raw_index in raw_indices:
        base = vertex_offset + 48 * raw_index
        weights = reader.unpack('<3f', base)
        bone_ids = reader.unpack('<3B', base + 12)
        position = reader.unpack('<3f', base + 16)
        normal = reader.unpack('<3f', base + 28)
        uv = reader.unpack('<2f', base + 40)
        require(all(math.isfinite(value) for value in (*weights, *position, *normal, *uv)),
                'Nonfinite VVD source fields')
        require(all(0.0 <= value <= 1.0 for value in weights), 'VVD weight outside closed domain')
        deviation = abs(math.sqrt(sum(value * value for value in normal)) - 1.0)
        require(deviation <= UNIT_TOLERANCE, 'Native unit normal outside unchanged 2.5e-7 profile')
        rows.append({'weights': weights, 'bones': bone_ids, 'position': position,
                     'normal': normal, 'uv': uv})
    return {'count': count, 'raw_count': count, 'raw_indices': raw_indices, 'rows': rows}


def _vtx(raw, mdl):
    """Reproduce the pinned standard VTX7 branch, not its extra8 retry path."""
    reader = _Reader(raw, 'VTX', 36)
    version, _, max_strip_bones, _, max_bones, checksum, lod_count, replacement_offset, part_count, part_offset = reader.unpack('<IIHH6I', 0)
    require(version == 7 and max_bones == 3, 'Standard VTX7 three-slot profile required')
    integer(max_strip_bones, 1, 512, 'VTX hardware slot-count header outside closed range')
    require(checksum == mdl['checksum'], 'Native family VTX checksum differs')
    require(lod_count == 1, 'Only one fully traversed VTX LOD is admitted')
    reader.table(replacement_offset, 1, 8, 'VTX material replacement list', 1)
    replacement_count, replacement_relative = reader.unpack('<2i', replacement_offset)
    require(replacement_count == 0,
            'Material replacements outside closed VTX profile')
    require(0 <= replacement_offset + replacement_relative <= len(raw),
            'Empty material-replacement seek outside source file')
    require(part_count == len(mdl['parts']), 'MDL/VTX bodypart cardinality differs')
    reader.table(part_offset, part_count, 8, 'VTX bodyparts', 256)
    results = {}
    corner_total, point_total, bone_state_total = 0, 0, 0
    for part_index, models in enumerate(mdl['parts']):
        base = part_offset + 8 * part_index
        count, relative = reader.unpack('<2I', base)
        require(count == len(models), 'MDL/VTX model cardinality differs')
        model_offset = reader.relative_table(base, relative, count, 8, 'VTX models', MAX_MODELS)
        for model_index, model in enumerate(models):
            entry = model_offset + 8 * model_index
            lods, lod_relative = reader.unpack('<2i', entry)
            require(lods == lod_count, 'Per-model VTX LOD count differs')
            lod_offset = reader.relative_table(entry, lod_relative, lods, 12, 'VTX LODs', 8)
            mesh_count, mesh_relative, switch_point = reader.unpack('<2If', lod_offset)
            require(math.isfinite(switch_point), 'Finite VTX switch point required')
            require(mesh_count == len(model['meshes']), 'MDL/VTX LOD0 mesh cardinality differs')
            if not mesh_count:
                require(model['count'] == 0, 'Empty VTX model must be blank')
                require(mesh_relative == 0 or lod_offset + mesh_relative <= len(raw),
                        'Empty VTX mesh seek outside source file')
                continue
            mesh_offset = reader.relative_table(lod_offset, mesh_relative, mesh_count, 9, 'VTX meshes', 65536)
            vertices, corners, materials = [], [], []
            accumulated = 0
            for mesh_index, mesh in enumerate(model['meshes']):
                mesh_base = mesh_offset + 9 * mesh_index
                group_count, group_relative, mesh_flags = reader.unpack('<2IB', mesh_base)
                require(mesh_flags & ~3 == 0, 'Unknown VTX mesh flags')
                require(group_relative < len(raw) and
                        (group_relative == 0 or mesh_base + group_relative <= len(raw)),
                        'VTX strip-group seek outside source file')
                if not group_count:
                    continue
                group_offset = reader.relative_table(mesh_base, group_relative, group_count, 25, 'VTX strip groups', 65536)
                local_offset = 0
                for group_index in range(group_count):
                    group = group_offset + 25 * group_index
                    vertex_count, vertex_relative, index_count, index_relative, strip_count, strip_relative, flags = reader.unpack('<6IB', group)
                    require(flags & ~7 == 0, 'Unknown VTX strip-group flags')
                    integer(vertex_count, 1, 65536, 'VTX group vertex budget')
                    integer(index_count, 3, MAX_CORNERS, 'VTX group index budget')
                    require(index_count % 3 == 0, 'VTX triangle-list indices required')
                    integer(strip_count, 1, 65536, 'VTX strip count budget')
                    point_total += vertex_count; corner_total += index_count
                    require(point_total <= MAX_POINTS and corner_total <= MAX_CORNERS, 'Aggregate native geometry budget')
                    vertex_table = reader.relative_table(group, vertex_relative, vertex_count, 9, 'VTX vertices', 65536)
                    index_table = reader.relative_table(group, index_relative, index_count, 2, 'VTX indices', MAX_CORNERS)
                    strip_table = reader.relative_table(group, strip_relative, strip_count, 27, 'VTX strips', 65536)
                    strip_vertices, strip_indices = 0, 0
                    for strip_index in range(strip_count):
                        strip = strip_table + 27 * strip_index
                        indices_count, index_start, vertices_count, vertex_start, bone_count, strip_flags, changes, change_offset = reader.unpack('<4IH B2I', strip)
                        require(strip_flags == 1 and bone_count < 255,
                                'Closed trilist/bounded-bone-count strip required')
                        require(change_offset < len(raw), 'VTX bone-state-change offset outside source domain')
                        integer(changes, 0, 512, 'VTX bone-state row count outside closed range')
                        bone_state_total += changes
                        require(bone_state_total <= MAX_BONE_STATE_ROWS, 'Aggregate VTX bone-state row budget')
                        if changes:
                            state_table = reader.relative_table(strip, change_offset, changes, 8,
                                                                'VTX bone-state changes', 512)
                            for state_index in range(changes):
                                slot, global_bone = reader.unpack('<2i', state_table + 8 * state_index)
                                require(0 <= slot < max_strip_bones and 0 <= global_bone < len(mdl['bones']),
                                        'VTX signed hardware slot/global bone outside bounded metadata range')
                        # Pinned merge/import code never consumes this hardware
                        # state. It cannot replace VVD global bone IDs/weights.
                        require(index_start == strip_indices and vertex_start == strip_vertices and
                                indices_count % 3 == 0, 'Contiguous ordered strip partition required')
                        strip_vertices += vertices_count; strip_indices += indices_count
                    require(strip_vertices == vertex_count and strip_indices == index_count,
                            'Strip partition must exactly cover group vertex/index tables')
                    for index in range(vertex_count):
                        original = reader.unpack('<H', vertex_table + 9 * index + 4)[0]
                        require(original < mesh['count'], 'Original mesh vertex identity outside MDL mesh')
                        vertices.append(mesh['start'] + original)
                    for index in range(index_count):
                        value = reader.unpack('<H', index_table + 2 * index)[0]
                        require(value < vertex_count, 'VTX index outside its strip group')
                        corners.append(accumulated + local_offset + value)
                    materials.extend([mesh['material']] * (index_count // 3))
                    # This is sum(strip.vertex_count), not inferred unique-point count.
                    local_offset += strip_vertices
                accumulated += local_offset
            if not model['count']:
                require(not vertices and not corners, 'Blank MDL model has geometry')
                continue
            require(vertices and corners and len(vertices) == accumulated, 'Complete renderable VTX relation required')
            require(len(set(vertices)) == len(vertices), 'Repeated source point identities outside exact-join profile')
            corners.reverse()  # np.flip on the complete flattened stream, before reshape.
            triangles = [tuple(corners[index:index + 3]) for index in range(0, len(corners), 3)]
            require(all(len(set(triangle)) == 3 for triangle in triangles), 'Degenerate triangles outside stable topology profile')
            require(len({tuple(sorted(triangle)) for triangle in triangles}) == len(triangles), 'Duplicate faces outside stable topology profile')
            results[model['name']] = {'ids': [model['start'] + value for value in vertices],
                                      'corners': corners, 'materials': list(reversed(materials))}
    return results


def derive_native_point_rows(native_refs):
    """Return exact private source facts, including broader ordered weight writes.

    Multi-group rows are exposed as writes, not guessed Blender storage order.
    This accepts no observations or coordinate/matching options.
    """
    raw, identities = _admit_refs(native_refs)
    mdl = _mdl(raw['mdl'])
    vvd = _vvd(raw['vvd'], mdl['checksum'])
    for models in mdl['parts']:
        for model in models:
            require(model['start'] <= vvd['count'] and model['count'] <= vvd['count'] - model['start'],
                    'MDL declared model range outside native LOD0')
    topology = _vtx(raw['vtx'], mdl)
    for model in topology.values():
        require(all(0 <= index < vvd['count'] for index in model['ids']), 'MDL/VTX IDs outside native LOD0')
        model['raw_ids'] = [vvd['raw_indices'][index] for index in model['ids']]
        require(len(set(model['raw_ids'])) == len(model['raw_ids']), 'Repeated original raw IDs outside exact-join profile')
        model['rows'] = [vvd['rows'][index] for index in model['ids']]
        for row in model['rows']:
            writes = [[bone, weight] for bone, weight in zip(row['bones'], row['weights']) if weight > 0.0]
            require(all(bone < len(mdl['bones']) for bone, _ in writes), 'Positive native weight bone outside MDL')
            row['positive_weight_writes'] = writes
    return {'format': 'has_private_native_point_source_rows_1', 'source_identities': identities,
            'checksum': mdl['checksum'], 'native_lod0_row_count': vvd['count'],
            'native_raw_row_count': vvd['raw_count'], 'vertex_groups': mdl['bones'],
            'native_bone_parents': mdl['parents'], 'models': topology,
            'native_adapter_independently_qualified': False,
            'VTX_hardware_palette_or_render_equivalence_qualified': False}


def replay_replace_weight_writes(writes):
    """Pure candidate rule ledger, independently testable by a future native probe.

    This function makes no assertion that Blender stores this order. It records
    first positive insertion order and last positive REPLACE value. Slot order,
    positive-only filtering and replacement are source-derived; storage order
    still requires the separate pinned synthetic API evidence.
    """
    require(type(writes) is list and len(writes) <= 3, 'At most three native weight writes required')
    order, values = [], {}
    for pair in writes:
        require(type(pair) is list and len(pair) == 2, 'Weight write pair required')
        group, value = pair
        integer(group, 0, MAX_BONES - 1, 'Bounded weight write group required')
        require(type(value) is float and math.isfinite(value) and 0.0 <= value <= 1.0
                and struct.unpack('<f', struct.pack('<f', value))[0] == value,
                'Exact finite native F32 weight required')
        if value > 0.0:
            if group not in values:
                order.append(group)
            values[group] = value
    return [[group, values[group]] for group in order]


def build_native_point_expectation(native_refs, setter_ID_order, coordinate_policy, *, logical_name):
    """Derive the existing exact_point_join schema for an unambiguous weight profile.

    At most one distinct positive group per point is admitted. Repeated positive
    writes to that group use the LAST weight, matching SourceIO REPLACE semantics.
    Broader group storage order is not specified by local SourceIO Python and is
    refused until a separately pinned native-storage rule is available.
    """
    require(type(coordinate_policy) is str and coordinate_policy == COORDINATE_POLICY,
            'Explicit unchanged .01905/standalone/identity coordinate policy required')
    require(type(logical_name) is str and logical_name, 'Exact logical name required')
    require(type(setter_ID_order) is list and 1 <= len(setter_ID_order) <= MAX_POINTS,
            'Bounded observed setter ID list required')
    for value in setter_ID_order:
        integer(value, 0, MAX_POINTS - 1, 'Exact bounded observed source ID required')
    require(len(set(setter_ID_order)) == len(setter_ID_order), 'Unique observed source IDs required')
    source = derive_native_point_rows(native_refs)
    require(logical_name in source['models'], 'Logical name not independently present in native family')
    model = source['models'][logical_name]
    require(setter_ID_order == model['ids'], 'Observed setter order differs from independent MDL/VTX derivation')
    vertices, normals, uv_points, weights = [], [], [], []
    for row in model['rows']:
        writes = row['positive_weight_writes']
        require(len({bone for bone, _ in writes}) <= 1,
                'Multi-group Blender stored-weight order is unproved; native expectation refused')
        weights.append(replay_replace_weight_writes(writes))
        vertices.append([f32(value * F32_SCALE) for value in row['position']])
        normals.append(list(row['normal']))
        uv_points.append([row['uv'][0], f32(1.0 - row['uv'][1])])
    identity4 = [[float(row == column) for column in range(4)] for row in range(4)]
    identity3 = [[float(row == column) for column in range(3)] for row in range(3)]
    return {'format': 'has_independent_native_point_expectation_1', 'logical_name': logical_name,
            'native_lod0_row_count': source['native_lod0_row_count'],
            'native_raw_row_count': source['native_raw_row_count'],
            'source_lod0_vertex_indices': model['ids'], 'source_raw_vertex_indices': model['raw_ids'],
            'vertices': vertices, 'corner_vertex_indices': model['corners'],
            'vertex_groups': source['vertex_groups'], 'vertex_weights': weights,
            'corner_uv_active': [uv_points[index][:] for index in model['corners']],
            'object_matrix_world': identity4,
            'armature_matrix_world': [row[:] for row in identity4], 'normal_transform': identity3,
            'native_normal_words_as_F32': normals,
            'source_identities': source['source_identities'], 'source_checksum': source['checksum'],
            'coordinate_policy': coordinate_policy, 'position_scale_F32': F32_SCALE,
            'native_expected_adapter_independently_qualified': False,
            'actual_native_family_profile_observed': False,
            'Blender_storage_or_validate_behavior_qualified': False,
            'VTX_hardware_palette_or_render_equivalence_qualified': False,
            'nearest_matching_used': False, 'source_unit_conversion_changed': False,
            'six_foot_normalization_applied': False,
            'native_runtime_or_normal_fidelity_qualified': False}
