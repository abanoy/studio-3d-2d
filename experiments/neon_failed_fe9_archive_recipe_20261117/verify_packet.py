"""Artifact-only verifier; never imports builder/checker or opens original paths."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import re

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / 'neon_failed_fe9_actual_packet_20261117'
INPUTS_SHA = 'a0b2ecdcd8db87363384188a927eb1f58f071250ca6bba34e952e8a40d07f230'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def same(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def parse(data):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'Duplicate JSON key'); result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def regular(path):
    need(not path.is_symlink() and not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400, 'Archive reparse refused')


def verify(folder=PACKET):
    regular(folder)
    regular(folder / 'INDEX.json')
    regular(folder / 'objects')
    spec_raw = (HERE / 'INPUTS.json').read_bytes(); need(sha(spec_raw) == INPUTS_SHA, 'Frozen manifest binding')
    spec = parse(spec_raw); idx_raw = (folder / 'INDEX.json').read_bytes(); idx = parse(idx_raw)
    need(idx['format'] == 'has_fe9_closed_failure_exact_archive_1' and idx['recipe_inputs_sha256'] == INPUTS_SHA and idx['full_suite_passed'] is False and idx['native_art_arrays_copied'] is False, 'Archive identity/domain')
    for key, name in [('builder_sha256', 'build_packet.py'), ('checker_sha256', 'archive_checks.py'), ('verifier_sha256', 'verify_packet.py')]:
        need(idx[key] == sha((HERE / name).read_bytes()), 'Pinned code changed')
    expected, decoded = {'INDEX.json'}, {}
    need(len(idx['objects']) <= 85, 'Bounded object count')
    for row in idx['objects']:
        name = row['path']; need(type(name) is str and re.fullmatch('objects/[a-f0-9]{64}\\.gz', name) and name not in expected, 'Object path domain')
        need(type(row['decoded_bytes']) is int and 0 <= row['decoded_bytes'] <= 2 * 1024 * 1024, 'Per-object decoded cap')
        path = folder / name; regular(path); packed = path.read_bytes()
        need(type(row['bytes']) is int and len(packed) == row['bytes'] and sha(packed) == row['sha256'], 'Compressed bytes/hash')
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
            data = stream.read(row['decoded_bytes'] + 1)
        need(len(data) == row['decoded_bytes'] and sha(data) == row['decoded_sha256'] and name == 'objects/' + sha(data) + '.gz', 'Decoded exact bytes/hash')
        need(sha(data) not in decoded and b'\0' not in data, 'Unique bounded text object'); data.decode('utf-8-sig')
        decoded[sha(data)] = data; expected.add(name)
    need(len(decoded) == idx['unique_objects'], 'Unique object total')
    for row in idx['files']:
        need(row['path'] in ('BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md') and row['path'] not in expected, 'Plain member domain')
        path = folder / row['path']; regular(path); data = path.read_bytes()
        need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'Plain member identity'); expected.add(row['path'])
    need({'BINDINGS.json', 'ACTUAL_RESULT.json', 'README.md'} <= expected and expected == {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}, 'Exact archive membership')
    for path in folder.rglob('*'): regular(path)
    bindings = parse((folder / 'BINDINGS.json').read_bytes())
    need(same(bindings, {'format': 'has_fe9_closed_failure_bindings_1', 'roots': spec['roots'], 'inputs': spec['inputs']}), 'Exact original path/size/mtime/hash bindings')
    need(len(spec['inputs']) == idx['original_bindings'] == 85 and len({r['alias'] for r in spec['inputs']}) == 85, 'Exact85 aliases')
    raw = {r['alias']: decoded[r['sha256']] for r in spec['inputs']}
    need(all(len(raw[r['alias']]) == r['bytes'] for r in spec['inputs']) and set(decoded) == {r['sha256'] for r in spec['inputs']}, 'Every original/object byte joined')
    need(sum(len(data) for data in raw.values()) == idx['decoded_total_bytes_including_aliases'] <= 16 * 1024 * 1024, 'Exact total bounded text')
    state, release, inv = [parse(raw[n]) for n in ('state.json', 'graphics-lease-closed.json', 'receipt-inventory.json')]
    need(state['status'] == 'failed' and state['suite_exit'] == 1 and state['source_unchanged'] is True and state['source_commit'] == 'fe9aace86f7a349c90a951ff26d76f746d1e4701', 'Closed failed source domain')
    need(raw['source-before.json'] == raw['source-after.json'], 'Raw before/after bytes exact')
    source = parse(raw['source-before.json']); need(source['commit'] == state['source_commit'] and len(source['source_sha256']) == 1029, 'Source1029 identity')
    need(sha(raw['original-verify_shape_catalog.py']) == source['source_sha256']['tests/verify_shape_catalog.py'] == '9792946c73c594e7ff93a8504f842a045f6823d20b789a7b88b9a550deb589fe', 'Exact failing wrapper source')
    need(release['released'] is True and release['release_kind'] == 'closed_failed_partial_run' and release['source_commit'] == state['source_commit'] and release['terminal_state_sha256'] == sha(raw['state.json']), 'Release/state identity')
    need(release['receipt_inventory_sha256'] == sha(raw['receipt-inventory.json']) == '90a3c1b10a5fc4fed2196be7c720e26ff899b41b0b47b0a12248dddfe7729cb6' and release['full_suite_passed'] is False and release['final_full_report_used'] is False, 'Exact inventory and no stale final report')
    need(same([inv[k] for k in ('physical_receipt_files', 'unique_physical_jobs', 'normal_exit0', 'registered_cancel_exit2', 'failed_partial_nonzero')], [68, 68, 67, 1, 0]) and len(inv['rows']) == 68, '68 private physical receipts')
    receipts, jobs = [], set()
    for n, row in enumerate(inv['rows']):
        data = raw['receipts/%03d.json' % n]; need(sha(data) == row['source_sha256'], 'Raw physical receipt hash')
        receipt = parse(data); need(same(receipt, row['receipt']) and receipt['desktop'] not in jobs, 'Typed exact physical receipt/unique job')
        jobs.add(receipt['desktop'])
        for key, expected_value in {'format': 'studio_private_desktop_1', 'private_window_seen': True, 'child_desktop_confirmed': True, 'foreground_child_observed': False, 'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}.items():
            need(same(receipt.get(key), expected_value), 'Physical private placement/closure')
        need(type(receipt['exit']) is int and receipt['exit'] == (2 if row['classification'] == 'registered_Krita_cancel_exit2' else 0), 'Registered receipt exit domain')
        receipts.append(receipt)
    for inline in inv['inline_receipts']: need(any(same(inline['receipt'], item) for item in receipts), 'All recorded inline receipts join physical')
    need(same(parse(raw['host-observation.json']), inv['process_observation']), 'Root observation direct join')
    log = raw['canonical.log'].decode('utf-8')
    need('FileNotFoundError: [Errno 2]' in log and 'tests/verify_shape_catalog.py' in log and 'prepared-head' in log and sum(line.startswith('PASS ') for line in log.splitlines()) == 50, 'Exact retained failure and50 preceding PASS lines')
    result = parse((folder / 'ACTUAL_RESULT.json').read_bytes()); need(same(result, spec['expected_summary']) and result['full_suite_passed'] is False and result['physical_jobs'] == 68 and result['raw_face_descriptor_models_media_native_arrays_copied'] is False, 'Frozen scoped public summary')
    return {'passed': True, 'original_bindings': 85, 'unique_objects': len(decoded), 'physical_receipts': len(receipts), 'recorded_inline_joins': len(inv['inline_receipts']), 'full_suite_passed': False, 'source_unchanged': 1029, 'original_paths_or_native_inputs_opened': False, 'INDEX_sha256': sha(idx_raw)}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
