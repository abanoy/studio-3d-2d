"""Root CPU-only conditional derivative. Author never runs native inputs/tests.

Only a closed successful raw export with passing strict non-NORMAL and a
measured raw-L2 failure is eligible. No native process, re-export or adoption.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
MAX = 128 * 1024 * 1024
HEAD = 'ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b'
CLOSED_STAGE = 'source-material-carrier-run-1795228448950398100'
RAW_CARRIER = (2361932, '44d6c00f80068a83b43cb9007de40a729418ed10b553f92738aa32e6b1dc67a5')
METRIC = 'raw_unnormalized_euclidean_vector_distance'
THRESHOLD = 2e-5
HELPERS = {
    'vvd_normals': ('experiments/native_normal_carrier_strategy_20261117/vvd_normals.py', 4184, 'f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb'),
    '_closed_corrector': ('experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py', 17632, '37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08'),
    'semantic_compare': ('experiments/carrier_semantic_preservation_20261117/semantic_compare.py', 22754, 'c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00'),
    '_closed_domain': ('experiments/carrier_input_domain_20261118/input_domain.py', 16109, 'c679d873aa45aac4fad553f014e83c8e42a9a458c8189151e9e3695072be8c74'),
    '_closed_native': ('experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py', 27615, 'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d'),
    '_closed_raw_gate': ('experiments/source_material_carrier_20261120/code_used/v5/normal_gate.py', 9093, '0992c58c53be60712bc14668229959dcfffebf404d4d26db0374abf33ce3288c'),
}
NATIVE = {
    'mdl': (37644, '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': (618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': (173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
}
BASELINE = (2322644, '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d')
READS = {}


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def invalid(_):
        raise Refusal('NONFINITE_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def safe(path, exists=True):
    path = Path(path).absolute()
    need('..' not in path.parts, 'DOT_DOT_PATH')
    for part in reversed((path, *path.parents)):
        if not part.exists() and not part.is_symlink():
            need(not exists or part != path, 'MISSING_PATH')
            continue
        info = part.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'REPARSE_OR_LINK_PATH')
        if stat.S_ISREG(info.st_mode):
            need(info.st_nlink == 1, 'HARDLINK_PATH')
    return path


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, getattr(info, 'st_file_attributes', 0) & ~0x40000)


def read(path, expected=None, limit=MAX, role=None):
    path = safe(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, 'FILE_DOMAIN')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'FILE_CHANGED_BEFORE_READ')
        raw = stream.read(before.st_size + 1)
        after_open = os.fstat(stream.fileno())
    need(len(raw) == before.st_size and stamp(after_open) == stamp(before) == stamp(path.lstat()),
         'FILE_CHANGED_DURING_READ')
    if expected is not None:
        need(len(raw) == expected[0] and sha(raw) == expected[1], 'PIN_DIFFERS')
    if role is not None:
        need(role not in READS, 'READ_ROLE_REUSED')
        READS[role] = (path, stamp(before), len(raw), sha(raw))
    return raw, before


def check_reads():
    for path, before, count, digest in READS.values():
        raw, info = read(path, (count, digest))
        need(stamp(info) == before, 'INPUT_OR_HELPER_STAMP_CHANGED')
    return True


def load(name, relative, count, digest):
    need(name not in sys.modules, 'FRESH_MODULE_NAMESPACE_REQUIRED')
    path = ROOT / relative
    raw, _ = read(path, (count, digest), limit=1024 * 1024, role='helper:' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module


def input_role(role, row):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256', 'mtime_ns'} and
         type(row['path']) is str and type(row['bytes']) is int and 0 <= row['bytes'] <= MAX and
         type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']) and
         type(row['mtime_ns']) is int and row['mtime_ns'] > 0, 'REQUEST_INPUT_ROW')
    raw, info = read(row['path'], (row['bytes'], row['sha256']), role='input:' + role)
    need(info.st_mtime_ns == row['mtime_ns'], 'REQUEST_INPUT_NS_MTIME_DIFFERS')
    return raw


def write_fresh(path, raw):
    path = safe(path, False)
    need(not path.exists() and type(raw) is bytes and len(raw) <= MAX, 'FRESH_BOUNDED_OUTPUT')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    verified, _ = read(path, (len(raw), sha(raw)))
    need(verified == raw, 'OUTPUT_READBACK_DIFFERS')


def measure_final(corrected, relation, source, raw_gate, corrector):
    # The sealed derivative deliberately retains old unused storage/provenance.
    # Do not claim the closed raw-carrier Snapshot accepts this derivative.
    expected = raw_gate._sources(source)
    document, binary = corrector.parse_glb(corrected)
    keys = {(mi, pi) for mi, mesh in enumerate(document['meshes']) for pi, _ in enumerate(mesh['primitives'])}
    need(len(document['meshes']) == 2 and len(keys) == 4 and keys == set(relation), 'CORRECTED_PRIMITIVE_DOMAIN')
    seen, count, maximum = set(), 0, 0.0
    for mi, pi in sorted(keys):
        attributes = document['meshes'][mi]['primitives'][pi]['attributes']
        need(not any(key.casefold() == raw_gate.CARRIER.casefold() for key in attributes), 'CARRIER_NOT_STRIPPED')
        rows = corrector._float_accessor(document, binary, attributes['NORMAL'], 'VEC3')
        need(len(relation[(mi, pi)]) == len(rows), 'CORRECTED_NORMAL_DOMAIN')
        for identifier, actual in zip(relation[(mi, pi)], rows):
            need(type(identifier) is int and identifier - 1 in expected, 'CORRECTED_SOURCE_ID_DOMAIN')
            target = expected[identifier - 1]
            delta = tuple(a - b for a, b in zip(actual, target))
            need(all(math.isfinite(value) for value in delta), 'CORRECTED_NORMAL_NONFINITE')
            maximum = max(maximum, math.sqrt(sum(value * value for value in delta)))
            count += 1
            seen.add(identifier - 1)
    need(seen == set(expected), 'CORRECTED_SOURCE_COVERAGE')
    return dict(source_normal_metric=METRIC, source_normal_threshold=THRESHOLD,
                source_normal_max_euclidean_error=maximum, passed=maximum <= THRESHOLD,
                source_points=len(seen), normal_rows=count, compared_components=3 * count,
                measurement_normalization_or_repair_applied=False)


def execute(request):
    need(type(request) is dict and set(request) == {'format', 'source_head', 'closed_stage', 'output',
         'root_cpu_lane_confirmed', 'root_coordinator_reaped', 'wrapper', 'files'}, 'REQUEST_SCHEMA')
    need(request['format'] == 'has_closed_carrier_normal_correction_request_1' and request['source_head'] == HEAD and
         request['root_cpu_lane_confirmed'] is True and request['root_coordinator_reaped'] is True,
         'ROOT_CLOSED_CONTEXT_REQUIRED')
    wrapper = request['wrapper']
    need(type(wrapper) is dict and set(wrapper) == {'bytes', 'sha256'}, 'WRAPPER_PIN_REQUIRED')
    read(Path(__file__), (wrapper['bytes'], wrapper['sha256']), role='wrapper')
    stage = safe(request['closed_stage'])
    need(stage.parent == ROOT / 'output' and stage.name == CLOSED_STAGE,
         'EXACT_CLOSED_STAGE_DOMAIN')
    files = request['files']
    need(type(files) is dict and set(files) == {'audit', 'worker', 'desktop', 'comparisons', 'carrier', 'relation',
                                             'baseline', 'mdl', 'vvd', 'vtx'}, 'EXACT_INPUT_ROLES')
    fixed = dict(audit=stage / 'PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json',
                 worker=stage / 'result/PUBLIC_CARRIER_EXPORT.json', desktop=stage / 'private-desktop.json',
                 comparisons=stage / 'STRICT_CARRIER_COMPARISONS.json', carrier=stage / 'result/carrier.glb',
                 relation=stage / 'result/PRIVATE_PRIMITIVE_IDS.json')
    for key, path in fixed.items():
        need(Path(files[key]['path']).absolute() == path, 'CLOSED_STAGE_FILE_LOCATION')
    for key in NATIVE:
        need(Path(files[key]['path']).absolute().parent == stage / 'inputs', 'STAGED_NATIVE_LOCATION')
        need((files[key]['bytes'], files[key]['sha256']) == NATIVE[key], 'EXACT_NATIVE_FAMILY_REQUIRED')
    need((files['baseline']['bytes'], files['baseline']['sha256']) == BASELINE, 'EXACT_ORIGINAL_BASELINE_REQUIRED')
    need((files['carrier']['bytes'], files['carrier']['sha256']) == RAW_CARRIER, 'EXACT_V11_RAW_CARRIER_REQUIRED')
    data = {role: input_role(role, row) for role, row in files.items()}
    audit, worker, desktop, previous = (parse(data[key]) for key in ('audit', 'worker', 'desktop', 'comparisons'))
    need(audit.get('format') == 'has_carrier_export_failed_run_preservation_1' and
         audit.get('status') == 'UNQUALIFIED_FAILED_RUN' and audit.get('primary_error_code') == 'STRICT_CARRIER_COMPARISON_GATES_FAILED' and
         audit.get('all_attempted_checks_passed') is True and audit.get('owned_launcher_reaped') is True and
         audit.get('physical_closure_confirmed') is True and audit.get('owned_lock_retained') is False and
         audit.get('owned_lock_cleanup_refused') is False, 'CLOSED_FAILED_NORMAL_AUDIT_REQUIRED')
    checks = audit.get('checks')
    need(type(checks) is dict and 42 <= len(checks) <= 128 and all(value is True for value in checks.values()) and
         all(checks.get(key) is True for key in ('functional_source', 'head_and_committed_source', 'approved_runtime')),
         'PRESERVATION_CHECKS_REQUIRED')
    closure = audit.get('physical_closure')
    need(type(closure) is dict and type(closure.get('owned_processes')) is int and closure['owned_processes'] == 0 and
         closure.get('full_pids_absent') is True, 'PHYSICAL_CLOSURE_REQUIRED')
    need(desktop.get('job_closed') is True and desktop.get('desktop_closed') is True and
         desktop.get('foreground_child_observed') is False and desktop.get('desktop_switch_requested') is False and
         type(desktop.get('exit')) is int and desktop['exit'] == 0, 'SUCCESSFUL_PRIVATE_RAW_EXPORT_REQUIRED')
    need(worker.get('status') == 'MATCHED_FRESH_NATIVE_IDS_OWNED_MATERIALS_AND_CARRIER_EXPORT' and
         worker.get('all_read_inputs_hash_size_stamp_unchanged') is True and
         worker.get('exact_authenticated_reads') == 605 and worker.get('scene_or_registration_restoration_failed') is False and
         worker.get('carrier_written') is True, 'GENUINE_RAW_WORKER_REQUIRED')
    exported = worker['carrier_export']; binding = exported['export_observation']['actual_export_binding']
    need(exported['ordinary_operator_finished'] is True and exported['operator_invocations'] == 1 and
         (len(data['carrier']), sha(data['carrier'])) == (exported['carrier_glb_bytes'], exported['carrier_glb_sha256']) and
         binding['passed'] is True and binding['meshes'] == 2 and binding['primitives'] == 4 and binding['source_ids'] == 9661 and
         binding['carrier_glb_sha256'] == sha(data['carrier']), 'RAW_EXPORT_AND_BINDING_PINS')
    rows = parse(data['relation'])
    canonical = json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()
    need(sha(data['relation']) == exported['private_relation_sha256'] and
         sha(canonical) == binding['private_relation_sha256'], 'INDEPENDENT_RELATION_AUTHENTICATION')
    modules = {name: load(name, *pin) for name, pin in HELPERS.items()}
    corrector, domain, native_module, raw_gate = (modules[key] for key in
        ('_closed_corrector', '_closed_domain', '_closed_native', '_closed_raw_gate'))
    native_source = native_module.derive_native_point_rows({key: dict(raw=data[key], bytes=len(data[key]), sha256=sha(data[key]))
                                                          for key in NATIVE})
    strict = domain.compare_qualified_non_normal(data['baseline'], data['carrier'])
    measured = raw_gate.measure_native_normal_gate(data['carrier'], rows, native_source,
                                                 worker['normal_transport_frame'], domain)
    need(previous.get('non_NORMAL_passed') is True and previous.get('raw_normal_passed') is False and
         previous.get('passed') is False and corrector.typed_same(previous['non_NORMAL'], strict) and
         corrector.typed_same(previous['raw_normal'], measured), 'CLOSED_COMPARISON_REPLAY_DIFFERS')
    need(measured.get('measured') is True and measured.get('source_normal_metric') == METRIC and
         type(measured.get('source_normal_threshold')) is float and measured['source_normal_threshold'] == THRESHOLD and
         measured.get('passed') is False and type(measured.get('source_normal_max_euclidean_error')) is float and
         math.isfinite(measured['source_normal_max_euclidean_error']) and
         measured['source_normal_max_euclidean_error'] > THRESHOLD, 'ONLY_MEASURED_RAW_NORMAL_FAILURE_ELIGIBLE')
    expected = raw_gate._sources(native_source)
    parsed_document, _ = domain.read_semantic_glb(data['carrier'])
    keys = {(mi, pi) for mi, mesh in enumerate(parsed_document['meshes']) for pi, _ in enumerate(mesh['primitives'])}
    relation = raw_gate._relation(rows, keys, expected)
    native = corrector.source_from_vvd(data['vvd'], NATIVE['vvd'][1], native_source['checksum'])
    corrected, correction_report = corrector.correct_glb(data['carrier'], native, sha(data['carrier']),
        [identifier + 1 for identifier in sorted(expected)], (1, 3, -2), expected_native_sha256=NATIVE['vvd'][1],
        verified_primitive_identity_order=relation)
    need(corrector.preservation_contract(data['carrier'], corrected) is True and
         corrector.corrected_normal_contract(corrected, native, relation, (1, 3, -2)) is True, 'UNCHANGED_CORRECTION_CONTRACTS_REQUIRED')
    before, _ = corrector.parse_glb(data['carrier']); after, _ = corrector.parse_glb(corrected)
    need(all(corrector.typed_same(before.get(key), after.get(key)) for key in ('scene', 'scenes', 'nodes', 'skins')),
         'SCENE_NODE_SKIN_DATA_CHANGED')
    final_measure = measure_final(corrected, relation, native_source, raw_gate, corrector)
    need(final_measure['passed'] is True, 'ORIGINAL_FINAL_L2_THRESHOLD_REQUIRED')
    check_reads()
    output = safe(request['output'], False)
    need(output.parent == ROOT / 'output' and re.fullmatch('source-native-normal-correction-[0-9]{19}', output.name) and
         not output.exists(), 'FRESH_OWNED_CORRECTION_DIRECTORY_REQUIRED')
    output.mkdir()
    write_fresh(output / 'corrected-native-normals.glb', corrected)
    need(check_reads(), 'PRESERVATION_REQUIRED')
    result = dict(format='has_conditional_native_normal_derivative_result_1', status='CPU_DERIVATIVE_CONTRACTS_PASSED_UNADOPTED',
        raw_carrier_sha256=sha(data['carrier']), raw_carrier_bytes=len(data['carrier']),
        corrected_sha256=sha(corrected), corrected_bytes=len(corrected), raw_normal=measured, corrected_normal=final_measure,
        original_to_raw_strict_non_NORMAL_replayed=True, raw_to_corrected_unchanged_preservation_contract=True,
        corrected_exact_native_words_contract=True, correction_report=correction_report,
        corrected_closed_semantic_comparator_claimed=False, compositional_non_NORMAL_proof_only=True,
        scene_nodes_skins_type_exact=True, inputs_and_helpers_hash_size_nsmtime_identity_unchanged=True,
        raw_input_preserved=True, native_originals_written=False, native_or_exporter_process_launched=False,
        bone_physics_binding_requalification_required=True, application_adoption_qualified=False,
        private_arrays_or_artifact_bytes_published=False)
    write_fresh(output / 'PUBLIC_CORRECTION.json', (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
    print(json.dumps(dict(status=result['status'], corrected_sha256=sha(corrected), corrected_bytes=len(corrected))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args()
    need(not sys.flags.optimize and sys.version_info[:2] == (3, 13), 'UNOPTIMIZED_APPROVED_PYTHON_REQUIRED')
    need(re.fullmatch('[0-9a-f]{64}', args.request_sha256), 'REQUEST_SHA256_REQUIRED')
    raw, _ = read(args.request, limit=1024 * 1024, role='request')
    need(sha(raw) == args.request_sha256, 'REQUEST_SHA256_DIFFERS')
    try:
        execute(parse(raw))
    finally:
        check_reads()


if __name__ == '__main__':
    main()
