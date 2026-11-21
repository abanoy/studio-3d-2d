"""Root-invoked, RAM-only join of one exact native family to retained B observations.

No Blender/SourceIO import, conversion, exporter, subprocess, network or Git API.
All native arrays remain in memory. The only write is a fresh compact report in
this owned directory. A match does not qualify current Blender storage or export.
"""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import struct
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OLD_ROOT = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111')
FAMILY_REL = Path('output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685')
SAVED_REL = Path('output/normal-boundary-20261116-attempt2/capture')
SETTER_REL = Path('output/normal-setter-boundary-20261116-attempt1/capture')

PINS = {
    'mdl': (FAMILY_REL / 'native/junko hair.mdl', 37644, '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': (FAMILY_REL / 'native/junko hair.vvd', 618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': (FAMILY_REL / 'native/junko hair.dx90.vtx', 173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
    'blend': (FAMILY_REL / 'editable.blend', 2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6'),
    'glb': (FAMILY_REL / 'scene.glb', 2322644, '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'),
    'parameters': (FAMILY_REL / 'parameters.json', 159684, 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'),
    'saved': (SAVED_REL / 'PRIVATE_NORMALS.json', 17627667, '0ef144f3ffe093d6c01f31e5e6fadf98e87a5c7de2b4013c27d42809dabd6921'),
    'saved_public': (SAVED_REL / 'PUBLIC_CAPTURE.json', 2786, 'a5e1c42e704dc7221de033d98ae1863db24a2e1371ae8dac81c588d9176d5e04'),
    'setter': (SETTER_REL / 'PRIVATE_SETTER.json', 15172535, 'e3c99ef2a51ea6058b9d243255ec6c49fdd658435bfb764e225d289f70275a38'),
    'setter_public': (SETTER_REL / 'PUBLIC_SETTER.json', 3463, '86126f272e52b60323e9a49443df7d320472c61cfae2eada3f88b90c57dd262b'),
    'sourceio_rule': (Path('output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647/blender_bindings/models/mdl49/import_mdl.py'), 12880, '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b'),
}
HELPERS = {
    'native': (Path('experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py'), 27615, 'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d'),
    'snapshot': (Path('experiments/native_normal_carrier_probe_20261117/exact_point_join.py'), 8826, 'c3a5ac1acc6b6a2988020d924313f27fedaa371281bfeae5f6871a545d54d85d'),
}
MODELS = {'hair.smd': (8011, 34332), 'Hat.smd': (1650, 8370)}
MAX_BYTES = 96 * 1024 * 1024


class Refusal(Exception):
    """Only controlled, non-array codes may enter the compact public report."""


def need(value, code):
    if not value:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_regular(path):
    path = Path(path).absolute()
    need('..' not in path.parts, 'INPUT_PARENT_TRAVERSAL')
    for part in (path, *path.parents):
        info = part.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'INPUT_LINK_OR_REPARSE')
    need(path.is_file(), 'INPUT_NOT_REGULAR')
    return path


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def pinned_read(path, count, digest):
    path = safe_regular(path)
    before = path.stat()
    need(type(count) is int and 0 < count <= MAX_BYTES and before.st_size == count,
         'INPUT_SIZE_DIFFERS')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        need(stamp(opened) == stamp(before), 'INPUT_CHANGED_BEFORE_OPEN')
        raw = stream.read(count + 1)
        after_open = os.fstat(stream.fileno())
    after = path.stat()
    need(stamp(before) == stamp(after_open) == stamp(after), 'INPUT_CHANGED_DURING_READ')
    need(len(raw) == count and sha(raw) == digest, 'INPUT_HASH_DIFFERS')
    return raw, stamp(after)


def json_body(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'JSON_DUPLICATE_KEY')
            result[key] = value
        return result
    def invalid(_value):
        raise Refusal('JSON_NONFINITE')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def load_helper(role, raw):
    # Execute only the separately hash-verified pure stdlib helper. Native
    # extraction is invoked below; no installed SourceIO/Blender code is loaded.
    path = PROJECT / HELPERS[role][0]
    need(len(raw) == HELPERS[role][1] and sha(raw) == HELPERS[role][2], 'HELPER_SOURCE_HASH_DIFFERS')
    spec = importlib.util.spec_from_file_location('saved_B_join_' + role, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def f32_word(value):
    need(type(value) is float and math.isfinite(value), 'FINITE_FLOAT_REQUIRED')
    raw = struct.pack('<f', value)
    need(struct.unpack('<f', raw)[0] == value, 'NON_F32_VALUE')
    return raw


def vector_words(row, width):
    need(type(row) in (list, tuple) and len(row) == width, 'VECTOR_SCHEMA')
    return b''.join(f32_word(value) for value in row)


def row_mismatches(left, right, width):
    need(type(left) is list and type(right) is list and len(left) == len(right), 'ROW_COUNT_DIFFERS')
    return sum(vector_words(a, width) != vector_words(b, width) for a, b in zip(left, right))


def ids_hash(values):
    need(type(values) is list and all(type(value) is int and 0 <= value < 200000 for value in values), 'SOURCE_ID_SCHEMA')
    return sha(b''.join(struct.pack('<I', value) for value in values))


def corner_indices(values, points, count):
    need(type(values) is list and len(values) == count and
         all(type(value) is int and 0 <= value < points for value in values),
         'EXACT_BOUNDED_CORNER_INDICES_REQUIRED')
    return values


def stored_weight_words(row, groups):
    need(type(row) is list and len(row) <= 3, 'STORED_WEIGHT_ROW_SCHEMA')
    seen, result = set(), bytearray()
    for pair in row:
        need(type(pair) is list and len(pair) == 2, 'STORED_WEIGHT_PAIR_SCHEMA')
        group, value = pair
        need(type(group) is int and 0 <= group < groups and group not in seen, 'STORED_WEIGHT_GROUP_SCHEMA')
        need(type(value) is float and 0. < value <= 1., 'STORED_POSITIVE_WEIGHT_SCHEMA')
        seen.add(group)
        result.extend(struct.pack('<I', group));result.extend(f32_word(value))
    return bytes(result)


def compare_model(native, saved, setter, groups, native_module, snapshot_module):
    """Return counts/hashes only. Never return point, UV, normal or weight rows."""
    points = len(native['rows'])
    snapshot_module._snapshot(saved, points)
    need(len(native['ids']) == len(native['raw_ids']) == points, 'NATIVE_POINT_COUNT')
    need(set(setter.get('stages', {})) == {'after_setter', 'before_validate', 'after_validate'}, 'SETTER_STAGES')
    need(len(saved['vertices']) == len(setter.get('initial_vertices', [])) == points, 'POINT_CARDINALITY')
    need(len(saved['vertex_weights']) == points, 'WEIGHT_CARDINALITY')
    source_ids = setter.get('source_lod0_vertex_indices')
    raw_ids = setter.get('source_raw_vertex_indices')
    need(type(source_ids) is list and type(raw_ids) is list and len(source_ids) == len(raw_ids) == points,
         'SETTER_ID_CARDINALITY')
    need(len(set(source_ids)) == len(set(raw_ids)) == points, 'SETTER_ID_ALIAS')
    # Neither geometric proximity nor any normal value selects an identity.
    # The SourceIO-observed integer order must equal the independent VTX order.
    need(source_ids == native['ids'] and raw_ids == native['raw_ids'], 'NATIVE_SETTER_ID_ORDER_DIFFERS')
    counters = Counter()
    positions = [[native_module.f32(value * native_module.F32_SCALE) for value in row['position']]
                 for row in native['rows']]
    counters['native_to_saved_position_rows'] = row_mismatches(positions, saved['vertices'], 3)
    counters['setter_to_saved_position_rows'] = row_mismatches(setter['initial_vertices'], saved['vertices'], 3)
    counters['native_to_setter_normal_input_rows'] = row_mismatches(
        [list(row['normal']) for row in native['rows']], setter.get('setter_payload', []), 3)
    corner_count = len(native['corners'])
    native_corners = corner_indices(native['corners'], points, corner_count)
    saved_corners = corner_indices(saved['corner_vertex_indices'], points, corner_count)
    initial_corners = corner_indices(setter.get('initial_corner_indices'), points, corner_count)
    counters['native_to_saved_corner_indices'] = sum(a != b for a, b in zip(native_corners, saved_corners))
    counters['setter_to_saved_corner_indices'] = sum(a != b for a, b in zip(initial_corners, saved_corners))
    counters['native_to_saved_group_names'] = int(groups != saved['vertex_groups'])
    uv_points = [[row['uv'][0], native_module.f32(1. - row['uv'][1])] for row in native['rows']]
    corners_uv = [uv_points[index] for index in native['corners']]
    counters['native_to_saved_uv_rows'] = row_mismatches(corners_uv, saved['corner_uv_active'], 2)
    for field, width in [('object_matrix_world', 4), ('armature_matrix_world', 4), ('normal_transform', 3)]:
        identity = [[float(row == column) for column in range(width)] for row in range(width)]
        counters[field + '_rows'] = row_mismatches(identity, saved[field], width)
    histogram, positive_calls = Counter(), 0
    for source, observed in zip(native['rows'], saved['vertex_weights']):
        writes = source['positive_weight_writes']
        # This is a candidate event replay, not an assumed Blender rule. Every
        # resulting ordered word row is checked against authenticated saved RNA.
        expected = native_module.replay_replace_weight_writes(writes)
        positive_calls += len(writes)
        histogram[len(expected)] += 1
        expected_words = stored_weight_words(expected, len(groups))
        observed_words = stored_weight_words(observed, len(groups))
        counters['ordered_stored_weight_rows'] += expected_words != observed_words
        counters['stored_weight_group_order_rows'] += [pair[0] for pair in expected] != [pair[0] for pair in observed]
        counters['stored_weight_value_rows'] += dict(expected) != dict(observed)
    for stage in ('after_setter', 'before_validate', 'after_validate', 'unobserved_control'):
        captured = setter['unobserved_control'] if stage == 'unobserved_control' else setter['stages'][stage]
        counters[stage + '_position_rows'] = row_mismatches(setter['initial_vertices'], captured['vertices'], 3)
        captured_corners = corner_indices(captured['corner_vertex_indices'], points, corner_count)
        counters[stage + '_corner_indices'] = sum(a != b for a, b in zip(saved_corners, captured_corners))
    return {'points': points, 'corners': len(native['corners']), 'positive_source_calls': positive_calls,
            'distinct_positive_group_histogram': {str(key): value for key, value in sorted(histogram.items())},
            'source_id_order_sha256': ids_hash(source_ids), 'raw_id_order_sha256': ids_hash(raw_ids),
            'mismatches': dict(sorted(counters.items())), 'all_exact': not any(counters.values())}


def authenticate(saved, saved_public, setter, setter_public):
    need(saved.get('format') == 'has_private_blender_normal_intermediates_2' and
         saved_public.get('format') == 'has_blender_normal_capture_2', 'SAVED_CAPTURE_FORMAT')
    need(saved_public.get('private_sha256') == PINS['saved'][2] and saved_public.get('private_bytes') == PINS['saved'][1], 'SAVED_PUBLIC_PRIVATE_JOIN')
    need(saved_public.get('inputs_unchanged') is True and saved_public.get('installed_sources_modified') is False and
         saved_public.get('original_blend_saved') is False and saved_public.get('exporter_invoked') is False, 'SAVED_OBSERVATION_SCOPE')
    for role in ('blend', 'mdl', 'vvd', 'glb', 'parameters'):
        need(saved_public.get('input_hashes', {}).get(role) == PINS[role][2], 'SAVED_INPUT_PROVENANCE')
    need(saved_public.get('input_hashes', {}).get('sourceio_import') == PINS['sourceio_rule'][2], 'SAVED_SOURCEIO_PROVENANCE')
    need(setter.get('format') == 'has_private_sourceio_setter_probe_1' and setter.get('error') is None and
         setter_public.get('format') == 'has_sourceio_setter_boundary_probe_1', 'SETTER_CAPTURE_FORMAT')
    need(setter_public.get('status') == 'SETTER_BOUNDARIES_MEASURED' and setter_public.get('files_unchanged') is True and
         setter_public.get('SourceIO_import_executed') is True and setter_public.get('original_importer_patched_on_disk') is False and
         setter_public.get('GLB_exported') is False and setter_public.get('blend_saved') is False, 'SETTER_OBSERVATION_SCOPE')
    need(setter_public.get('private_sha256') == PINS['setter'][2] and setter_public.get('private_bytes') == PINS['setter'][1], 'SETTER_PUBLIC_PRIVATE_JOIN')
    need(setter.get('ast_proof') == setter_public.get('ast_observer_inverse') and
         setter_public.get('ast_observer_inverse', {}).get('original_function_AST_restored') is True, 'SETTER_AST_PROVENANCE')
    need(type(saved.get('objects')) is list and len(saved['objects']) == 2 and
         type(setter.get('models')) is dict and set(setter['models']) == set(MODELS), 'EXACT_CAPTURE_OBJECT_DOMAIN')
    by_name = {row.get('name'): row for row in saved['objects']}
    need(len(by_name) == 2 and set(by_name) == set(MODELS), 'SAVED_LOGICAL_OBJECT_DOMAIN')
    for name, (points, corners) in MODELS.items():
        summary = setter_public.get('models', {}).get(name, {})
        need(summary.get('vertices') == points and summary.get('corners') == corners and
             summary.get('setter_input_word_exact') is True and summary.get('saved_geometry_exact') is True and
             summary.get('observer_control_geometry_exact') is True and summary.get('observer_control_normals_word_exact') is True,
             'SETTER_LOGICAL_PROFILE_PROVENANCE')
    return by_name


def report_path(value):
    path = Path(value).absolute()
    need('..' not in path.parts and path != HERE and path.is_relative_to(HERE) and not path.exists(), 'REPORT_NOT_FRESH_OWNED')
    need(path.suffix == '.json' and path.parent.is_dir(), 'REPORT_PARENT_OR_SUFFIX')
    for part in path.parents:
        info = part.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'REPORT_LINK_OR_REPARSE')
        if part == HERE:
            break
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-root', type=Path, default=OLD_ROOT)
    parser.add_argument('--script-sha256', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    # Resolve the only output before private reads. Never overwrite an earlier result.
    target = report_path(args.report)
    result = {'format': 'has_pinned_saved_B_weight_point_join_1', 'status': 'REFUSED',
              'scope': 'Historical ordered numeric relation: exact native-family writes versus authenticated saved B observations only.',
              'numeric_index_correspondence_only': True,
              'historical_saved_B_vertex_causality_qualified': False,
              'full_saved_mesh_or_appearance_equivalence_qualified': False,
              'full_saved_vs_current_mesh_observed': False,
              'current_Blender_state_observed': False, 'current_weight_API_calls_observed': False,
              'general_Blender_weight_storage_qualified': False,
              'native_expected_adapter_independently_qualified': False,
              'normal_fidelity_qualified': False, 'carrier_or_exporter_binding_qualified': False,
              'native_arrays_written_or_published': False, 'new_native_process_launched': False,
              'nearest_matching_used': False, 'numeric_tolerance_used': False,
              'original_normal_fidelity': 'FAILED_UNQUALIFIED; original2e-5 gate unchanged.'}
    reads, buffers, phase = {}, {}, 'SELF_SOURCE'
    try:
        need(re.fullmatch('[0-9a-f]{64}', args.script_sha256) is not None, 'SCRIPT_SHA_SCHEMA')
        own_path = Path(__file__).absolute()
        own, own_stamp = pinned_read(own_path, own_path.stat().st_size, args.script_sha256)
        reads['script'] = (own_path, len(own), args.script_sha256, own_stamp)
        result['script_sha256'] = sha(own)
        phase = 'PINNED_INPUT_READS'
        for role, (relative, count, digest) in PINS.items():
            path = args.old_root / relative
            buffers[role], before = pinned_read(path, count, digest)
            reads[role] = (path, count, digest, before)
        for role, (relative, count, digest) in HELPERS.items():
            path = PROJECT / relative
            buffers[role], before = pinned_read(path, count, digest)
            reads[role] = (path, count, digest, before)
        phase = 'AUTHENTICATE_RETAINED_OBSERVATIONS'
        saved = json_body(buffers['saved']);setter = json_body(buffers['setter'])
        by_name = authenticate(saved, json_body(buffers['saved_public']), setter, json_body(buffers['setter_public']))
        phase = 'INDEPENDENT_NATIVE_DERIVATION'
        native_module = load_helper('native', buffers['native'])
        snapshot_module = load_helper('snapshot', buffers['snapshot'])
        native = native_module.derive_native_point_rows({role: {'raw': buffers[role], 'bytes': PINS[role][1], 'sha256': PINS[role][2]} for role in ('mdl', 'vvd', 'vtx')})
        need(set(native['models']) == set(MODELS) and native['native_lod0_row_count'] == native['native_raw_row_count'] == 9661 and len(native['vertex_groups']) == 69,
             'NATIVE_EXACT_FAMILY_DOMAIN')
        phase = 'EXACT_SAVED_WEIGHT_POINT_JOIN'
        models = {}
        all_ids = []
        for name, (points, corners) in MODELS.items():
            model = native['models'][name]
            need(len(model['rows']) == points and len(model['corners']) == corners, 'NATIVE_LOGICAL_CARDINALITY')
            models[name] = compare_model(model, by_name[name], setter['models'][name], native['vertex_groups'], native_module, snapshot_module)
            all_ids.extend(model['ids'])
        need(len(all_ids) == len(set(all_ids)) == 9661 and set(all_ids) == set(range(9661)), 'NATIVE_GLOBAL_ID_COVERAGE')
        result['models'] = models
        result['native_points'] = 9661;result['native_corners'] = 42702;result['native_groups'] = 69
        result['exact_saved_B_weight_point_relation_matched'] = all(row['all_exact'] for row in models.values())
        result['status'] = 'MATCHED_PINNED_SAVED_B_WEIGHT_POINT_JOIN' if result['exact_saved_B_weight_point_relation_matched'] else 'SAVED_B_WEIGHT_POINT_JOIN_MISMATCH'
    except BaseException as error:
        # Do not publish exception repr/tracebacks: a third-party parser's error
        # could include private values. Controlled Refusal codes contain no arrays.
        result['status'] = 'REFUSED'
        result['phase'] = phase
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if isinstance(error, Refusal) else 'PINNED_HELPER_OR_SCHEMA_REFUSAL'
    finally:
        unchanged = True
        for role, (path, count, digest, before) in reads.items():
            try:
                _raw, after = pinned_read(path, count, digest)
                unchanged = unchanged and after == before
            except BaseException:
                unchanged = False
        result['all_read_inputs_hash_size_stamp_unchanged'] = unchanged and len(reads) == len(PINS) + len(HELPERS) + 1
        result['input_identities'] = {role: {'bytes': count, 'sha256': digest} for role, (_path, count, digest, _before) in sorted(reads.items())}
        if not result['all_read_inputs_hash_size_stamp_unchanged']:
            result['status'] = 'REFUSED_INPUT_PRESERVATION'
        encoded_report = (json.dumps(result, allow_nan=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
        need(len(encoded_report) <= 64 * 1024, 'COMPACT_REPORT_BUDGET')
        with target.open('xb') as stream:
            stream.write(encoded_report)
    print('SOURCE_WEIGHT_JOIN ' + json.dumps({'status': result['status'], 'report': str(target)}))
    return 0 if result['status'] == 'MATCHED_PINNED_SAVED_B_WEIGHT_POINT_JOIN' else 1


if __name__ == '__main__':
    raise SystemExit(main())
