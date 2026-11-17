"""Independent artifact-only foundation verifier. Never imports builder/checker."""
from pathlib import Path, PureWindowsPath
import gzip
import hashlib
import io
import json
import re

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / 'neon_foundation_fe9_actual_packet_20261117'
INPUTS_SHA = 'd1f896070f114f78d72ede167d3056b3e22f0e81d8def63e80c07c2f1f27f2f6'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'Duplicate JSON key'); value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def equal(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def regular(path):
    need(not path.is_symlink() and not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400, 'Archive reparse refused')


def verify(folder=PACKET):
    regular(folder)
    frozen = (HERE / 'INPUTS.json').read_bytes(); need(sha(frozen) == INPUTS_SHA, 'Frozen recipe identity')
    spec = parse(frozen); idx_raw = (folder / 'INDEX.json').read_bytes(); idx = parse(idx_raw)
    need(idx['format'] == 'has_foundation_fe9_compact_exact_actual_packet_1' and idx['recipe_inputs_sha256'] == INPUTS_SHA, 'Artifact recipe binding')
    for key, name in [('builder_sha256', 'build_packet.py'), ('verifier_sha256', 'verify_packet.py'), ('check_source_sha256', 'archive_checks.py')]:
        need(idx[key] == sha((HERE / name).read_bytes()), 'Pinned source differs')
    expected = {'INDEX.json'}; decoded = {}
    for row in idx['objects']:
        name = row['path']; need(re.fullmatch(r'objects/[a-f0-9]{64}\.gz', name) and name not in expected, 'Object name/membership')
        need(type(row['decoded_bytes']) is int and 0 <= row['decoded_bytes'] <= 2 * 1024 * 1024, 'Decoded bound')
        path = folder / name; regular(path); packed = path.read_bytes()
        need(type(row['bytes']) is int and len(packed) == row['bytes'] and sha(packed) == row['sha256'], 'Compressed identity')
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream: data = stream.read(row['decoded_bytes'] + 1)
        need(len(data) == row['decoded_bytes'] and sha(data) == row['decoded_sha256'] and name == 'objects/' + sha(data) + '.gz', 'Decoded identity')
        need(b'\0' not in data and sha(data) not in decoded, 'Unique text object'); data.decode('utf-8-sig')
        decoded[sha(data)] = data; expected.add(name)
    need(len(decoded) == idx['unique_decoded_objects'], 'Unique decoded count')
    for row in idx['files']:
        need(row['path'] in ('BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md') and row['path'] not in expected, 'Plain member domain')
        path = folder / row['path']; regular(path); data = path.read_bytes()
        need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'Plain identity'); expected.add(row['path'])
    need(expected == {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}, 'Closed exact artifact set')
    for path in folder.rglob('*'): regular(path)
    bindings = parse((folder / 'BINDINGS.json').read_bytes())
    need(equal(bindings['roots'], spec['roots']) and equal(bindings['bindings'], spec['inputs']), 'Exact original input bindings')
    need(len({(r['root'], r['path']) for r in spec['inputs']}) == len(spec['inputs']) == idx['original_bindings'] == 77, 'Exact77 original aliases')
    raw = {}
    for row in bindings['bindings']:
        need(row['root'] in ('MAIN', 'REVIEW') and not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts, 'Original alias domain')
        data = decoded[row['sha256']]; need(len(data) == row['bytes'], 'Original object byte join'); raw[row['root'] + ':' + row['path']] = data
    need(set(decoded) == {r['sha256'] for r in bindings['bindings']}, 'Every object is bound')
    R = 'output/neon-foundation-fe9aace-20261117-attempt1/'; REV = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
    def obj(name): return parse(raw['REVIEW:' + name])
    root = obj(R + 'verification.json'); before = obj(R + 'source-before.json')
    need(root['passed'] is True and root['full_suite_pass_claimed'] is False and root['all_functional_source_unchanged'] is True and root['functional_source_files'] == 1029
         and root['host_scopes_closed'] is True and len(before) == 1029 and equal(before, obj(R + 'source-after.json')), 'Root scoped preservation')
    need(before['tests/source_bone_bindings_unit.gd'] == '80764dea7982a11f1d42a9bcbfb36b74c44edb6e620ddb585fa37dc1c8ab1e09', 'Exact reviewed fixture source')
    need(len(root['rows']) == 1, 'One focused root case'); run = root['rows'][0]
    need(run['label'] == 'foundation' and type(run['exit']) is int and run['exit'] == 0 and run['retained_Popen_reaped'] is True and run['timed_out'] is False and run['seconds'] == 12.0645659, 'Owned root process')
    need(equal({k: v for k, v in run.items() if k != 'report'}, obj(R + 'foundation-process.json')), 'Root process direct join')
    report = run['report']; C = PureWindowsPath(report['folder']).relative_to(PureWindowsPath(spec['roots']['REVIEW'])).as_posix() + '/'
    need(C == R + 'source-choices/' and equal(report, obj(C + 'verification.json')) and equal(report, obj(R + 'foundation-report.json')), 'Original report copies')
    need(report['format'] == 'has_source_choice_foundation_1' and report['passed'] is True and type(report['checks']) is int and report['checks'] == 167 and report['source_unchanged'] is True and report['native_conversion'] is False, '167 authored foundation scope')
    need(equal(report['separate_checks'], {'crosswalk_cpu': 77, 'bone_bindings_headless': 96}), 'Separate77/96 ledger')
    parts = report['reports']; need(parts['catalogue']['tests'] == 53 and parts['appearance']['tests'] == 29 and parts['unit']['checks'] == 65 and parts['ui']['result']['checks'] == 20, '167 four-part ledger')
    need(equal([parts['resource_write']['tests'], parts['resource_write']['passed'], parts['resource_write']['skipped']], [7, 6, 1])
         and parts['bridge_bootstrap']['tests'] == parts['bridge_bootstrap']['passed'] == 2 and parts['jiggle_cpu']['checks'] == 66, 'Additional controls/explicit skip')
    for label, count in [('jiggle_cpu', 66), ('crosswalk_cpu', 77)]:
        need(parts[label]['passed'] is True and parts[label]['checks'] == count and parts[label]['native_conversion'] is False and parts[label]['source_unchanged'] is True
             and equal(parts[label], obj(C + label.replace('_', '-') + '/verification.json')), 'Separate CPU copy')
    B = C + 'bindings-headless/'; headless = obj(B + 'verification.json')
    need(equal(headless, parts['bone_bindings_headless']) and headless['passed'] is True and headless['source_revision'] == REV and headless['checks'] == 96
         and headless['headless'] is True and headless['graphics'] is False and headless['native_conversion'] is False and headless['native_simulation'] is False, 'Authored headless scope')
    identity = obj(B + 'source-before.json')
    need(equal(identity, obj(B + 'source-after.json')) and identity['commit'] == REV and set(identity['files']) == set(before)
         and all(identity['files'][n]['sha256'] == d for n, d in before.items()), 'Headless exact source map')
    for name, count in [('bindings', 79), ('helper', 17)]:
        entry = headless['reports'][name]; need(entry['checks'] == count and entry['failures'] == 0 and equal(entry['result'], obj(B + name + '/verified.json')), 'Original79/17 results')
        for stage in ('parse', 'run'):
            base = B + name + '/'; process = obj(base + stage + '-process.json'); command = obj(base + stage + '-command.json')
            need(equal(process, entry[stage]) and process['headless'] is True and process['graphics'] is False and type(process['exit']) is int and process['exit'] == 0 and process['timed_out'] is False and '--headless' in command and '--receipt' not in command, 'Headless saved processes/no fake private job')
            for key, suffix in [('console', '-console.log'), ('engine_log', '-engine.log')]:
                data = raw['REVIEW:' + base + stage + suffix]; need(len(data) == process[key]['bytes'] and sha(data) == process[key]['sha256'], 'Ordered console/engine log identity')
    need(headless['reports']['bindings']['result']['fixture_glb_sha256'] == '39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1', 'Authored golden digest')
    ui = parts['ui']; need(equal(ui, obj(C + 'ui/verification.json')) and equal(ui['result'], obj(C + 'ui/result.json')), 'UI direct reports')
    receipt_path = PureWindowsPath(ui['private_receipt']).relative_to(PureWindowsPath(spec['roots']['REVIEW'])).as_posix()
    receipt = obj(receipt_path); need(equal(receipt, ui['receipt']) and PureWindowsPath(report['private_receipt']) == PureWindowsPath(ui['private_receipt']), 'One direct/inline physical receipt')
    command = obj(C + 'ui/command.json'); need(command.count('--receipt') == 1 and PureWindowsPath(command[command.index('--receipt') + 1]) == PureWindowsPath(ui['private_receipt']), 'Saved physical receipt command')
    for key, value in {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True, 'child_desktop_confirmed': True,
                       'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}.items(): need(equal(receipt.get(key), value), 'Strict physical placement/closure')
    phases = ui['result']['actual_metadata_children']; need([p['phase'] for p in phases] == ['success', 'cancel', 'refusal'] and 'exit' not in phases[1], 'No invented cancellation exit')
    for label in ('before', 'foundation-after', 'after'):
        scope = obj(R + label + '-closure.json'); need(type(scope['owned_count']) is int and scope['owned_count'] == 0 and scope['owned_matches'] == [] and scope['termination_issued'] is False, 'Recorded main/review zero scopes')
    for key, data in raw.items():
        if key.startswith('REVIEW:') and key[7:] in before: need(sha(data) == before[key[7:]], 'Selected tested source body')
    summary = parse((folder / 'ACTUAL_RESULT.json').read_bytes()); need(equal(summary, spec['expected_summary']) and summary['full_suite_pass_claimed'] is False
         and summary['real_private_desktop_jobs'] == 1 and summary['decoded_golden_model_art_media_or_native_arrays_included'] is False, 'Public scoped summary')
    return {'passed': True, 'original_bindings': len(raw), 'unique_objects': len(decoded), 'foundation_checks': 167, 'crosswalk_separate': 77, 'bindings_separate': 96,
            'private_jobs': 1, 'headless_parse_run_records': 4, 'source_preserved': 1029, 'explicit_resource_skip_preserved': 1,
            'originals_or_upcoming_full_outputs_read': False, 'INDEX_sha256': sha(idx_raw)}


if __name__ == '__main__': print(json.dumps(verify(), indent=2))
