"""Root-only measured normal gate; pure RAM, no repair or native file reader.

Root supplies authenticated cbb4 native rows, the qualified actual gather
relation, sealed domain reader and actual pre-export identity-frame evidence.
Carrier numbers do not establish identity: they must equal the separate relation.
"""
import hashlib
import json
import math
import struct

THRESHOLD = 2e-5
CARRIER = '_HAS_NATIVE_NORMAL_ID'
MAX_POINTS = 200000
SOURCE_POINTS = 9661
FRAME = dict(format='has_actual_identity_source_to_yup_normal_frame_1',
    mesh_world_identity=True, armature_world_identity=True, mesh_count=2,
    export_yup=True, export_apply=False, signed_axis_permutation=[1, 3, -2],
    source_coordinate_policy='sourceio_mdl49_standalone_01905_identity_standard_vtx7_1',
    source_unit_conversion_changed=False, six_foot_normalization_applied=False)


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok: raise Refusal(code)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def _frame(frame):
    need(type(frame) is dict and set(frame) == set(FRAME), 'EXACT_ACTUAL_NORMAL_FRAME_REQUIRED')
    for key, expected in FRAME.items():
        actual = frame[key]
        need(type(actual) is type(expected) and actual == expected, 'UNSUPPORTED_ACTUAL_NORMAL_FRAME')
        if key == 'signed_axis_permutation':
            need(all(type(value) is int for value in actual), 'EXACT_AXIS_INTEGER_REQUIRED')


def _sources(source):
    need(type(source) is dict and source.get('format') == 'has_private_native_point_source_rows_1',
         'AUTHENTICATED_NATIVE_SOURCE_ROWS_REQUIRED')
    need(type(source.get('checksum')) is int and 0 <= source['checksum'] < 2**32 and
         type(source.get('source_identities')) is dict and len(source['source_identities']) == 3,
         'NATIVE_SOURCE_IDENTITY_PROFILE')
    need(type(source.get('native_lod0_row_count')) is int and
         1 <= source['native_lod0_row_count'] <= MAX_POINTS and
         type(source.get('native_raw_row_count')) is int and
         1 <= source['native_raw_row_count'] <= MAX_POINTS, 'NATIVE_SOURCE_ROW_BUDGET')
    models = source.get('models')
    need(type(models) is dict and len(models) == 2, 'EXACT_TWO_NATIVE_MODELS_REQUIRED')
    expected = {}
    for name, model in models.items():
        need(type(name) is str and 0 < len(name) <= 256 and type(model) is dict,
             'NATIVE_MODEL_SCHEMA')
        ids, rows = model.get('ids'), model.get('rows')
        need(type(ids) is list and type(rows) is list and 0 < len(ids) == len(rows) <= MAX_POINTS,
             'NATIVE_ID_NORMAL_CARDINALITY')
        for identifier, row in zip(ids, rows):
            need(type(identifier) is int and 0 <= identifier < source['native_lod0_row_count'] and
                 identifier not in expected and type(row) is dict, 'UNIQUE_IN_DOMAIN_NATIVE_ID_REQUIRED')
            normal = row.get('normal')
            need(type(normal) in (list, tuple) and len(normal) == 3 and
                 all(type(value) is float and math.isfinite(value) for value in normal),
                 'FINITE_NATIVE_F32_NORMAL_REQUIRED')
            need(all(abs(value) <= 1.000001 and struct.unpack('<f', struct.pack('<f', value))[0] == value
                     for value in normal), 'EXACT_NATIVE_F32_WORDS_REQUIRED')
            need(abs(math.sqrt(sum(value * value for value in normal)) - 1.0) <= 2.5e-7,
                 'NATIVE_UNIT_NORMAL_PROFILE')
            expected[identifier] = (normal[0], normal[2], -normal[1])
    need(len(expected) == SOURCE_POINTS, 'EXACT_9661_NATIVE_SOURCE_COVERAGE_REQUIRED')
    return expected


def _relation(rows, primitive_keys, expected):
    need(type(rows) is list and len(rows) == 4, 'EXACT_FOUR_OBSERVED_PRIMITIVE_RELATIONS_REQUIRED')
    result = {}
    for row in rows:
        need(type(row) is dict and set(row) == {'mesh', 'primitive', 'one_based_source_ids'},
             'EXACT_OBSERVED_RELATION_ROW_REQUIRED')
        mesh, primitive = row['mesh'], row['primitive']
        need(type(mesh) is int and type(primitive) is int and (mesh, primitive) in primitive_keys and
             (mesh, primitive) not in result, 'UNIQUE_ACTUAL_PRIMITIVE_RELATION_REQUIRED')
        ids = row['one_based_source_ids']
        need(type(ids) is list and 0 < len(ids) <= MAX_POINTS and
             all(type(value) is int and 1 <= value <= MAX_POINTS and value - 1 in expected for value in ids),
             'OBSERVED_RELATION_NATIVE_ID_DOMAIN')
        result[(mesh, primitive)] = tuple(ids)
    need(set(result) == primitive_keys, 'COMPLETE_ACTUAL_PRIMITIVE_RELATION_REQUIRED')
    return result


def measure_native_normal_gate(carrier_raw, private_relation_rows, native_source_rows, frame, domain_module):
    """Measure raw Euclidean vector distance to source (x,z,-y), unchanged gate.

    Refuse malformed, unmatched or unsupported inputs. A well-formed measured
    error above threshold returns passed=False, preserving the measured error.
    Root combines this result with provenance and independent non-NORMAL proof.
    """
    _frame(frame)
    expected = _sources(native_source_rows)
    document, binary = domain_module.read_semantic_glb(carrier_raw)
    snapshot = domain_module.Snapshot(document, binary, carrier=True)
    meshes = document.get('meshes')
    need(type(meshes) is list and len(meshes) == 2 and
         all(type(mesh) is dict and type(mesh.get('primitives')) is list and
             0 < len(mesh['primitives']) <= 4 for mesh in meshes), 'EXACT_TWO_CARRIER_MESHES_REQUIRED')
    keys = {(mi, pi) for mi, mesh in enumerate(meshes) for pi, _ in enumerate(mesh['primitives'])}
    need(len(keys) == 4, 'EXACT_FOUR_CARRIER_PRIMITIVES_REQUIRED')
    relation = _relation(private_relation_rows, keys, expected)
    seen, maximum, maximum_component, total = set(), 0.0, 0.0, 0
    for mi, pi in sorted(keys):
        primitive = meshes[mi]['primitives'][pi]
        need(type(primitive) is dict and type(primitive.get('mode', 4)) is int and primitive.get('mode', 4) == 4,
             'TRIANGLE_PRIMITIVE_PROFILE_REQUIRED')
        attrs = primitive.get('attributes')
        need(type(attrs) is dict and all(type(key) is str for key in attrs) and
             all(key in attrs for key in ('POSITION', 'NORMAL', CARRIER)) and
             [key for key in attrs if key.casefold() == CARRIER.casefold()] == [CARRIER],
             'EXACT_POSITION_NORMAL_AND_CARRIER_CHANNELS_REQUIRED')
        position, _ = snapshot.channel(attrs['POSITION'], {5126}, {'VEC3'})
        normal, normal_token = snapshot.channel(attrs['NORMAL'], {5126}, {'VEC3'}, position['count'])
        carrier, carrier_token = snapshot.channel(attrs[CARRIER], {5126}, {'SCALAR'}, position['count'])
        need(all(accessor.get('normalized', False) is False for accessor in (position, normal, carrier)),
             'RAW_F32_CHANNELS_REQUIRED')
        ids = relation[(mi, pi)]
        need(len(ids) == normal['count'] and sum(len(value) for value in relation.values()) <= MAX_POINTS,
             'EXPORTED_NORMAL_AND_RELATION_CARDINALITY')
        actual_ids = tuple(value[0] for value in struct.iter_unpack('<f', carrier_token['component_bytes']))
        need(len(actual_ids) == len(ids) and all(actual == observed for actual, observed in zip(actual_ids, ids)),
             'CARRIER_WORDS_DIFFER_FROM_INDEPENDENT_OBSERVED_RELATION')
        normals = struct.iter_unpack('<3f', normal_token['component_bytes'])
        for identifier, actual in zip(ids, normals):
            target = expected[identifier - 1]
            delta = tuple(a - b for a, b in zip(actual, target))
            maximum = max(maximum, math.sqrt(sum(value * value for value in delta)))
            maximum_component = max(maximum_component, *(abs(value) for value in delta))
            seen.add(identifier - 1)
            total += 1
    need(seen == set(expected), 'UNMATCHED_OR_MISSING_NATIVE_NORMAL_SOURCE_IDS')
    return dict(format='has_exact_carrier_native_normal_measurement_1', passed=maximum <= THRESHOLD,
        source_normal_threshold=THRESHOLD, source_normal_max_euclidean_error=maximum,
        source_normal_metric='raw_unnormalized_euclidean_vector_distance',
        source_normal_max_component_error=maximum_component,
        source_points=len(expected), primitives=len(keys), exported_normal_rows=total,
        compared_components=3 * total, unmatched_source_points=0,
        carrier_words_equal_independent_observed_relation=True,
        all_native_source_points_covered=True, signed_axis_permutation=[1, 3, -2],
        frame_sha256=_digest(frame), native_source_identity_sha256=_digest(native_source_rows['source_identities']),
        carrier_sha256=hashlib.sha256(carrier_raw).hexdigest(), measured=True,
        normalization_or_repair_applied=False, nearest_or_numeric_identity_matching_used=False,
        current_or_historical_B_identity_inferred=False, application_adoption_qualified=False,
        generic_source_or_renderer_fidelity_qualified=False)
