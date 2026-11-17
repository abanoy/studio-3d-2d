"""Pure CPU identity admission; inputs/outputs containing arrays stay private in future use.

This does not decode native files or qualify where an expectation came from.
It supplies no nearest matching, geometry edits, scaling or normal reconstruction.
"""
import hashlib
import math
import struct

MAX_POINTS = 200_000
MAX_CORNERS = 1_000_000
SNAPSHOT_FIELDS = ('name', 'mesh_name', 'vertices', 'corner_vertex_indices', 'corner_edge_indices',
                   'edges', 'faces', 'vertex_groups', 'vertex_weights', 'corner_uv_active',
                   'object_matrix_world', 'armature_matrix_world', 'normal_transform')
NATIVE_FIELDS = ('vertices', 'corner_vertex_indices', 'vertex_groups', 'vertex_weights',
                 'corner_uv_active', 'object_matrix_world', 'armature_matrix_world', 'normal_transform')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def typed(value):
    if type(value) is float:
        require(math.isfinite(value), 'Nonfinite metadata')
        return ('f64', struct.pack('<d', value))
    if type(value) is dict:
        require(all(type(key) is str for key in value), 'String metadata keys required')
        return ('dict', tuple((key, typed(value[key])) for key in sorted(value)))
    if type(value) is list: return ('list', tuple(typed(x) for x in value))
    if value is None: return ('null',)
    require(type(value) in (int, str, bool), 'Unsupported metadata type')
    return (type(value).__name__, value)


def integer(value, minimum, maximum):
    require(type(value) is int and minimum <= value <= maximum, 'Exact bounded integer required')
    return value


def f32_words(rows, width):
    require(type(rows) is list and len(rows) <= MAX_CORNERS, 'Bounded row list required')
    output = bytearray()
    for row in rows:
        require(type(row) is list and len(row) == width, 'Exact vector width required')
        for value in row:
            require(type(value) is float and math.isfinite(value), 'Finite decoded F32 float required')
            try:
                word = struct.pack('<f', value)
            except (OverflowError, struct.error) as error:
                raise ValueError('F32 outside range') from error
            require(struct.unpack('<f', word)[0] == value, 'Non-binary32 value refused')
            output.extend(word)
    return bytes(output)


def _snapshot(row, points):
    require(type(row) is dict and set(SNAPSHOT_FIELDS) <= row.keys(), 'Complete saved/current snapshot required')
    require(type(row['name']) is str and row['name'] and type(row['mesh_name']) is str and row['mesh_name'], 'Exact object/mesh names required')
    require(len(row['vertices']) == points, 'Point count differs')
    f32_words(row['vertices'], 3)
    loops = row['corner_vertex_indices']
    require(type(loops) is list and 3 <= len(loops) <= MAX_CORNERS and len(loops) % 3 == 0, 'Triangle loop profile required')
    for index in loops: integer(index, 0, points - 1)
    require(type(row['vertex_groups']) is list and row['vertex_groups'] and all(type(x) is str and x for x in row['vertex_groups']) and len(set(row['vertex_groups'])) == len(row['vertex_groups']), 'Unique exact native bone names required')
    require(type(row['vertex_weights']) is list and len(row['vertex_weights']) == points, 'Weight rows differ')
    for weights in row['vertex_weights']:
        require(type(weights) is list and len(weights) <= len(row['vertex_groups']), 'Weight group bound')
        seen = set()
        for pair in weights:
            require(type(pair) is list and len(pair) == 2, 'Weight pair required')
            group = integer(pair[0], 0, len(row['vertex_groups']) - 1)
            require(group not in seen, 'Repeated stored weight group refused')
            seen.add(group)
            f32_words([[pair[1]]], 1)
            require(0.0 < pair[1] <= 1.0, 'Stored positive weight domain')
    require(len(row['corner_uv_active']) == len(loops), 'UV loop count differs')
    f32_words(row['corner_uv_active'], 2)
    for name, size in [('object_matrix_world', 4), ('armature_matrix_world', 4), ('normal_transform', 3)]:
        value = row[name]
        require(type(value) is list and len(value) == size, 'Exact skinned matrix profile required')
        f32_words(value, size)
    normal = row['normal_transform']
    require(normal[0][0] > 0 and normal[0][0] == normal[1][1] == normal[2][2] and
            all(normal[r][c] == 0.0 for r in range(3) for c in range(3) if r != c), 'Only positive uniform identity normal matrix profile')
    require(type(row['edges']) is list and row['edges'] and len(row['edges']) <= MAX_CORNERS, 'Bounded edges required')
    for edge in row['edges']:
        require(type(edge) is list and len(edge) == 2, 'Edge pair required')
        for index in edge: integer(index, 0, points - 1)
    require(type(row['corner_edge_indices']) is list and len(row['corner_edge_indices']) == len(loops), 'Corner-edge count differs')
    for index in row['corner_edge_indices']: integer(index, 0, len(row['edges']) - 1)
    require(type(row['faces']) is list and len(row['faces']) * 3 == len(loops), 'Triangle face count differs')
    for i, face in enumerate(row['faces']):
        require(type(face) is dict and set(face) == {'start', 'count', 'material', 'smooth'}, 'Face schema differs')
        require(type(face['smooth']) is bool and integer(face['start'], 0, len(loops)) == 3 * i and integer(face['count'], 3, 3) == 3, 'Exact ordered triangle faces required')
        integer(face['material'], 0, 65535)


def join_saved_point_ids(logical_name, saved, setter_record, current, native_expected):
    """Exact private relation check; native_expected must later come from an independent pinned adapter."""
    require(type(native_expected) is dict and native_expected.get('format') == 'has_independent_native_point_expectation_1', 'Independent expectation schema required')
    require(type(logical_name) is str and logical_name and type(setter_record) is dict, 'Exact logical name and setter record required')
    ids = setter_record.get('source_lod0_vertex_indices')
    require(type(ids) is list and 1 <= len(ids) <= MAX_POINTS and len(set(ids)) == len(ids), 'Unique bounded setter point identities required')
    for value in ids: integer(value, 0, MAX_POINTS - 1)
    points = len(ids)
    native_count = integer(native_expected.get('native_lod0_row_count'), 1, MAX_POINTS)
    raw_count = integer(native_expected.get('native_raw_row_count'), 1, MAX_POINTS)
    require(all(value < native_count for value in ids), 'ID outside independently decoded LOD0 rows')
    raw_ids = setter_record.get('source_raw_vertex_indices')
    require(type(raw_ids) is list and len(raw_ids) == points and len(set(raw_ids)) == points, 'Exact bounded original native raw-row identities required')
    for value in raw_ids: integer(value, 0, raw_count - 1)
    _snapshot(saved, points); _snapshot(current, points)
    require(saved['name'] == current['name'] == native_expected.get('logical_name') == logical_name, 'Exact logical object identity differs')
    for field in SNAPSHOT_FIELDS:
        require(typed(saved[field]) == typed(current[field]), 'Saved/current snapshot differs: ' + field)
    require(f32_words(setter_record.get('initial_vertices'), 3) == f32_words(saved['vertices'], 3) and
            typed(setter_record.get('initial_corner_indices')) == typed(saved['corner_vertex_indices']), 'Setter/saved point-order or loops differ')
    require(typed(native_expected.get('source_lod0_vertex_indices')) == typed(ids) and
            typed(native_expected.get('source_raw_vertex_indices')) == typed(setter_record.get('source_raw_vertex_indices')), 'Independent native row identities differ')
    for field in NATIVE_FIELDS:
        require(field in native_expected and typed(native_expected[field]) == typed(saved[field]), 'Independent native expected component differs: ' + field)
    require(f32_words(native_expected.get('native_normal_words_as_F32'), 3) == f32_words(setter_record.get('setter_payload'), 3) and
            len(setter_record['setter_payload']) == points, 'Original setter payload differs from independent native normal words')
    encoded = b''.join(struct.pack('<I', value) for value in ids)
    return tuple(ids), {'format': 'has_exact_private_saved_point_identity_join_1', 'points': points,
                        'corners': len(saved['corner_vertex_indices']), 'source_ID_order_sha256': hashlib.sha256(encoded).hexdigest(),
                        'exact_components_joined': True, 'nearest_matching_used': False,
                        'native_expected_adapter_independently_qualified': False,
                        'source_unit_conversion_changed': False, 'six_foot_normalization_applied': False,
                        'native_runtime_or_normal_fidelity_qualified': False}
