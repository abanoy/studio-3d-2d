"""Independent artifact-only verifier; no original paths, checker or builder imports."""
from pathlib import Path, PureWindowsPath
import gzip
import hashlib
import io
import json
import re

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / 'neon_catalogue_00bf_actual_packet_20261117'
INPUTS_SHA = '1d4278e2655f11bd63a001cdfaa72baa2f1196959afdde61782e01a68fb5d927'
R = 'output/neon-catalogue-00bf0f9-20261117-attempt1/'
LABELS = ['MMD', 'GMod', 'SFM', 'VRM1.0', 'VRM0.x', 'Supplied Mima']
CASES = [('catalogue', 130, 37.6931239, 'output/shape-catalog/', 2), ('comparison', 94, 43.6109725, 'output/shape-comparison-tests/', 3), ('height', 105, 48.1988992, 'output/character-height/', 3)]


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()


def equal(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def parse(data):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'Duplicate JSON key'); value[key] = item
        return value
    return json.loads(data, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def integer(value, expected): return type(value) is int and value == expected


def relative(value, root):
    need(type(value) is str and type(root) is str, 'Typed recorded path')
    path = PureWindowsPath(value); base = PureWindowsPath(root)
    need(path.is_absolute() and '..' not in path.parts, 'Recorded absolute Windows path')
    return path.relative_to(base).as_posix()


def semantics(raw, review):
    """Pure scalar/receipt joins. Input payloads already have frozen byte identities."""
    def obj(name): return parse(raw['REVIEW:' + name])
    def marked(name, prefix):
        lines = [line[len(prefix):] for line in raw['REVIEW:' + name].splitlines() if line.startswith(prefix)]
        need(len(lines) == 1, 'Exactly one saved scalar marker'); return parse(lines[0])
    root = obj(R + 'verification.json'); before = obj(R + 'source-before.json')
    need(root['format'] == 'has_root_workspace_followup_1' and root['passed'] is True and root['full_suite_pass_claimed'] is False and root['all_functional_source_unchanged'] is True and root['host_scopes_closed'] is True and integer(root['functional_source_files'], 1029), 'Root scoped success flags')
    need(len(before) == 1029 and equal(before, obj(R + 'source-after.json')), 'Exact1029 source map')
    for name, digest in [('tests/verify_shape_catalog.py', '54431c2c486bce9828ec47ebe046da9f413b3854e8c0290829c24183fe72e057'), ('tests/verify_character_height.py', 'cccfb7d472b5d552cbd3cfc07dc9058c1789b9c1947f6a1a548c924dd38a3f79')]:
        need(before[name] == digest, 'Reviewed selector source identities')
    for label in ('before', 'catalogue-after', 'comparison-after', 'height-after', 'after'):
        scope = obj(R + label + '-closure.json')
        need(scope['format'] == 'has_root_workspace_scope_observation_1' and integer(scope['owned_count'], 0) and scope['owned_matches'] == [] and scope['termination_issued'] is False and integer(scope['matcher_positive_cases'], 4) and integer(scope['matcher_negative_cases'], 3), 'Five recorded zero scopes')
    need(type(root['rows']) is list and [row['label'] for row in root['rows']] == [case[0] for case in CASES], 'Three ordered cases')
    reports, folders, jobs, paths = {}, {}, set(), []
    for row, (label, count, seconds, prefix, job_count) in zip(root['rows'], CASES, strict=True):
        need(integer(row['exit'], 0) and row['retained_Popen_reaped'] is True and row['timed_out'] is False and equal(row['seconds'], seconds), 'Root retained process gates')
        need(equal({k: v for k, v in row.items() if k != 'report'}, obj(R + label + '-process.json')), 'Direct process metadata')
        start = obj(R + label + '-start.json'); need(equal(start['pid'], row['pid']) and start['retained_Popen'] is True, 'Recorded Popen start')
        report = row['report']; need(equal(report, obj(R + label + '-report.json')) and integer(report['checks'], count) and integer(report['failures'], 0), 'Case count/failure/direct report')
        child = relative(report['folder'], review) + '/'; need(child.startswith(prefix), 'Recorded child folder domain')
        result = obj(child + 'result.json'); need(type(result) is dict and all(key in report and equal(value, report[key]) for key, value in result.items()), 'Raw child result subset')
        need(type(report['private_receipts']) is list and len(report['private_receipts']) == job_count, 'Exact physical membership')
        for path in report['private_receipts']:
            name = relative(path, review); need(name.startswith('output/private-desktop/') and name not in paths, 'Distinct physical receipt paths')
            receipt = obj(name)
            for key, expected in {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True, 'child_desktop_confirmed': True, 'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}.items():
                need(equal(receipt.get(key), expected), 'Typed physical placement/closure')
            need(type(receipt['desktop']) is str and type(receipt['child_pid']) is int, 'Actual physical identity types')
            identity = (receipt['desktop'], receipt['child_pid']); need(identity not in jobs, 'Distinct physical jobs'); jobs.add(identity); paths.append(name)
        reports[label], folders[label] = report, child
    need(len(jobs) == len(paths) == 8, 'Eight actual private jobs; no headless job invented')
    catalogue, child = reports['catalogue'], folders['catalogue']
    need(equal(catalogue['plans'], ['Authored fixture'] + LABELS) and integer(catalogue['unit_checks'], 34), 'Seven catalogue cases and unit34')
    need(equal(marked(child + 'shape_catalog_unit.log', b'SHAPE_CATALOG_UNIT '), {'checks': 34, 'failures': 0}), 'Headless unit34 saved marker')
    need(equal(catalogue['reader'], {'checks': 5, 'failures': 0}) and equal(catalogue['reader'], obj(child + 'reader-result.json')), 'Catalogue cold reader5')
    comparison, child = reports['comparison'], folders['comparison']
    need([model['label'] for model in comparison['models']] == ['Authored fixture'] + LABELS and integer(comparison['native_models_tested'], 6), 'All six native comparison cases')
    need(equal(comparison['teardown'], {'actual_readback_pending': True, 'checks': 2, 'failures': 0, 'released_after_app_free': True}) and equal(comparison['teardown'], obj(child + 'teardown-result.json')), 'Teardown2 raw result')
    need(equal(comparison['draft_recovery'], {'checks': 4, 'failures': 0}) and equal(comparison['draft_recovery'], obj(child + 'draft-reader.json')), 'Supplied Mima draft recovery4')
    height, child = reports['height'], folders['height']
    need(integer(height['native_models'], 6) and [model['label'] for model in height['models']] == ['Authored figure'] + LABELS + ['Short legs', 'Long legs', 'Head with full rig'], 'Height native and diagnostic membership')
    need(equal(height['reader'], {'checks': 4, 'failures': 0}) and equal(height['native_import'], {'checks': 9, 'failures': 0}), 'Cold height4 plus raw VRM9')
    need(equal(height['reader'], marked(child + 'reader.log', b'CHARACTER_HEIGHT_READER ')) and equal(height['native_import'], marked(child + 'native.log', b'HEIGHT_IMPORT_NATIVE ')), 'Height scalar log joins')
    for filename, receipt in zip(('command.json', 'reader-command.json', 'native-command.json'), height['private_receipts'], strict=True):
        saved = obj(child + filename); need(integer(saved['exit'], 0) and type(saved['args']) is list, 'Saved height process')
        args = saved['args']; need(args.count('--receipt') == 1 and args.index('--receipt') + 1 < len(args) and PureWindowsPath(args[args.index('--receipt') + 1]) == PureWindowsPath(receipt), 'Available argv to physical receipt join')
    prepared = parse(raw['MAIN:experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json'])
    need(prepared['descriptor_sha256'] == '05bd6d4ba63e481cf3488f9bf0082d662812d3bf8bb861796860f42fcb3e2310' and integer(prepared['scene']['bytes'], 7830992) and prepared['scene']['sha256'] == 'e9b21ab5f1171b21d0a7d3e3f83e5341f6b297516d09582e49c0283dfe10d8da' and prepared['prior_plan_exact_current_bundle_path'] is True and prepared['historical_b577_glb_substituted_or_recovered'] is False and prepared['raw_descriptor_native_arrays_model_or_media_included'] is False, 'Current Mima scalar provenance; no payload read')
    for name, data in raw.items():
        if name.startswith('REVIEW:') and name[7:] in before: need(sha(data) == before[name[7:]], 'Selected tested source body identity')
    return {'catalogue': 130, 'unit': 34, 'catalogue_cases': 7, 'comparison': 94, 'comparison_native': 6, 'height': 105, 'height_native': 6, 'raw_VRM': 9, 'private_jobs': len(jobs), 'available_height_argv_joins': 3, 'source_entries': 1029}


def verify_envelope(files, spec_raw, expected_spec_sha, code_pins):
    """RAM-only verifier. The filesystem entry point fixes the manifest/code pins."""
    need(sha(spec_raw) == expected_spec_sha, 'Frozen input manifest identity'); spec = parse(spec_raw)
    need(spec['format'] == 'has_catalogue_00bf_closed_text_archive_recipe_1', 'Frozen input format')
    idx = parse(files['INDEX.json'])
    need(idx['format'] == 'has_catalogue_00bf_compact_exact_actual_packet_1' and idx['recipe_inputs_sha256'] == expected_spec_sha, 'Envelope format/recipe pin')
    need(all(idx[key] == value for key, value in code_pins.items()), 'Exact code pins')
    need(idx['full_suite_pass_claimed'] is False and idx['native_fidelity_claimed'] is False and idx['upcoming_full_output_read'] is False and idx['decoded_art_models_media_native_arrays_included'] is False and integer(idx['real_private_jobs'], 8), 'Bounded claim domain')
    need(type(idx['objects']) is list and len(idx['objects']) <= 69, 'Object count cap')
    expected, decoded = {'INDEX.json'}, {}
    for row in idx['objects']:
        name = row['path']; need(type(name) is str and re.fullmatch(r'objects/[a-f0-9]{64}\.gz', name) and name not in expected, 'Closed object path/name')
        need(type(row['decoded_bytes']) is int and 0 <= row['decoded_bytes'] <= 2 * 1024 * 1024 and type(row['bytes']) is int and 0 <= row['bytes'] <= 4 * 1024 * 1024, 'Bounded stored/decoded sizes')
        packed = files[name]; need(len(packed) == row['bytes'] and sha(packed) == row['sha256'], 'Compressed identity')
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream: data = stream.read(row['decoded_bytes'] + 1)
        need(len(data) == row['decoded_bytes'] and sha(data) == row['decoded_sha256'] and name == 'objects/' + sha(data) + '.gz', 'Exact decoded bytes and name')
        need(sha(data) not in decoded and b'\0' not in data, 'Unique text objects'); data.decode('utf-8-sig')
        decoded[sha(data)] = data; expected.add(name)
    need(integer(idx['unique_decoded_objects'], len(decoded)), 'Unique decoded count')
    for row in idx['files']:
        name = row['path']; need(name in ('BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md') and name not in expected, 'Three plain file domain')
        data = files[name]; need(integer(row['bytes'], len(data)) and sha(data) == row['sha256'], 'Plain exact identity'); expected.add(name)
    need({'BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md'} <= expected and set(files) == expected, 'Exact complete envelope membership')
    bindings = parse(files['BINDINGS.json'])
    need(equal(bindings, {'format': 'has_catalogue_00bf_original_text_bindings_1', 'roots': spec['roots'], 'bindings': spec['inputs']}), 'Exact frozen aliases and original root/path/time/hash bindings')
    need(integer(idx['original_bindings'], 69) and len(spec['inputs']) == 69 and len({(r['root'], r['path']) for r in spec['inputs']}) == 69, 'Exact69 distinct original aliases')
    raw, total = {}, 0
    for row in spec['inputs']:
        need(row['root'] in ('MAIN', 'REVIEW') and type(row['path']) is str and not PureWindowsPath(row['path']).is_absolute() and '..' not in PureWindowsPath(row['path']).parts, 'Recorded original alias domain')
        data = decoded[row['sha256']]; need(integer(row['bytes'], len(data)), 'Original decoded size'); total += len(data); raw[row['root'] + ':' + row['path']] = data
    need(set(decoded) == {r['sha256'] for r in spec['inputs']} and integer(idx['uncompressed_original_bytes'], total) and total <= 16 * 1024 * 1024, 'Every object bound and total capped')
    result = parse(files['ACTUAL_RESULT.json']); need(equal(result, spec['expected_summary']) and result['full_suite_pass_claimed'] is False and result['native_roundtrip_fidelity_or_main_merge_claimed'] is False and result['model_media_original_native_arrays_or_generated_fixture_payloads_included'] is False, 'Exact scoped public result')
    actual = semantics(raw, spec['roots']['REVIEW'])
    return {'passed': True, 'original_bindings': len(raw), 'unique_objects': len(decoded), **actual, 'full_suite_passed': False, 'original_paths_or_native_inputs_opened': False, 'INDEX_sha256': sha(files['INDEX.json'])}


def regular(path):
    for item in (path, *path.parents):
        need(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400, 'Artifact reparse refused')


def verify(folder=PACKET):
    regular(folder)
    need({p.name for p in folder.iterdir()} == {'INDEX.json', 'objects', 'BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md'}, 'Closed top-level artifact membership')
    for path in folder.iterdir(): regular(path)
    files = {}
    for path in folder.iterdir():
        if path.name != 'objects':
            need(path.is_file() and path.stat().st_size <= 2 * 1024 * 1024, 'Bounded plain artifact file'); files[path.name] = path.read_bytes()
    need((folder / 'objects').is_dir(), 'Object directory required')
    members = list((folder / 'objects').iterdir()); need(len(members) <= 69, 'Physical object count cap')
    total = 0
    for path in members:
        regular(path); need(path.is_file() and re.fullmatch(r'[a-f0-9]{64}\.gz', path.name) and path.stat().st_size <= 4 * 1024 * 1024, 'Bounded regular object domain')
        data = path.read_bytes(); total += len(data); need(total <= 16 * 1024 * 1024, 'Total compressed artifact cap'); files['objects/' + path.name] = data
    pins = {key: sha((HERE / name).read_bytes()) for key, name in [('builder_sha256', 'build_packet.py'), ('verifier_sha256', 'verify_packet.py'), ('check_source_sha256', 'archive_checks.py')]}
    return verify_envelope(files, (HERE / 'INPUTS.json').read_bytes(), INPUTS_SHA, pins)


if __name__ == '__main__': print(json.dumps(verify(), indent=2))
