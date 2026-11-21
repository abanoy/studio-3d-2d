"""Root-only, unrun capture: require the closed successful 360 Full first.

Read-only to source, generated outputs and process handles. Writes only a fresh
metadata baseline in an exclusively created ignored output directory.
"""
from pathlib import Path, PurePosixPath
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import re
import stat
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
REVISION = '36044471151a6e561d6d3a404859e76ddd05738d'
FULL = ROOT / 'output/windows-reference-body-1795233568436471500'
OLD = ROOT / 'output/source-carrier-preserved-tracked-output-baseline-20261120.json'
OLD_SHA = 'c40dfc182df6907acf1be74f46f49441e0c2a5f1ee388bb3a4e0c246f1b448e3'
INTERMEDIATE = ROOT / 'output/post-failed-full-output-preservation-20261120/GENERATED_OUTPUT_BASELINE.json'
INTERMEDIATE_SHA = '022827d1938f6b6b46f99061cbccd7d5020ffc5ebde8d1cbd0e5aefc7b290535'
LIMIT = 16 * 1024 * 1024


def need(value, message):
    if not value:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(values):
    result = {}
    for key, value in values:
        need(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def parse(raw):
    def nonfinite(value):
        raise ValueError('Nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_mode, info.st_nlink,
            getattr(info, 'st_file_attributes', 0) & ~0x40000)


def read(path, expected=None):
    path = Path(path)
    need(path.is_absolute() and path.is_relative_to(ROOT), 'Read outside Root')
    current = path
    while current != ROOT.parent:
        info = current.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Alias or reparse path')
        current = current.parent
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= LIMIT,
         'Bounded ordinary file required')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'File changed before read')
        raw = stream.read(before.st_size + 1)
        opened = os.fstat(stream.fileno())
    need(len(raw) == before.st_size and stamp(before) == stamp(opened) == stamp(path.lstat()),
         'File changed while reading')
    if expected is not None:
        need(digest(raw) == expected, 'Unexpected file digest: ' + path.name)
    return raw, stamp(before)


def process_closed(pid):
    need(type(pid) is int and 0 < pid < 2**32, 'Process identity required')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenProcess.restype = wintypes.HANDLE
    api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    api.WaitForSingleObject.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    handle = api.OpenProcess(0x100000 | 0x1000, False, pid)
    if not handle:
        need(ctypes.get_last_error() == 87, 'Cannot establish verifier process closure')
        return True
    try:
        return api.WaitForSingleObject(handle, 0) == 0
    finally:
        need(api.CloseHandle(handle), 'Cannot close owned query handle')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('completion', 'launch', 'source-before', 'source-after'):
        parser.add_argument('--' + field + '-sha256', required=True)
    parser.add_argument('--root-lane-quiescent', action='store_true', required=True)
    options = parser.parse_args()
    need(os.name == 'nt' and options.root_lane_quiescent, 'Closed exclusive Windows lane required')
    files = {}
    identities = {}
    for field in ('completion', 'launch', 'source-before', 'source-after'):
        pin = getattr(options, field.replace('-', '_') + '_sha256')
        need(re.fullmatch('[0-9a-f]{64}', pin) is not None and pin != '0' * 64, 'Real proof digest required')
        raw, identity = read(FULL / (field + '.json'), pin)
        files[field] = (raw, parse(raw))
        identities[str(FULL / (field + '.json'))] = (pin, identity)
    completion = files['completion'][1]
    launch = files['launch'][1]
    need(completion.get('format') == 'has_reference_body_full_coordinator_1'
         and completion.get('revision') == launch.get('revision') == REVISION
         and type(completion.get('exit')) is int and completion['exit'] == 0
         and completion.get('functional_source_count') == 1084, 'Fresh exact Full did not pass')
    for key in ('whole_verifier_pass', 'child_reaped', 'functional_sources_unchanged', 'revision_unchanged',
                'fresh_final_report', 'all_private_jobs_isolated_closed',
                'nonzero_jobs_are_expected_cancellations', 'receipt_provenance_verified'):
        need(completion.get(key) is True, 'Full proof missing: ' + key)
    need(process_closed(launch.get('pid')) and process_closed(launch.get('coordinator_pid')),
         'Full process still live or closure unproven')
    before, after = files['source-before'][1], files['source-after'][1]
    need(type(before) is dict and len(before) == 1084 and before == after, 'Functional catalogue differs')
    for name, row in before.items():
        path = PurePosixPath(name)
        need(path.as_posix() == name and not path.is_absolute() and '..' not in path.parts
             and '\\' not in name and ':' not in name, 'Source path scope')
        raw, identity = read(ROOT / name, row['sha256'])
        need(len(raw) == row['bytes'] and identity[3] == row['mtime_ns'], 'Functional source changed')
        identities[str(ROOT / name)] = (row['sha256'], identity)
    old_raw, old_identity = read(OLD, OLD_SHA)
    intermediate_raw, intermediate_identity = read(INTERMEDIATE, INTERMEDIATE_SHA)
    old, intermediate = parse(old_raw), parse(intermediate_raw)
    need(old.get('format') == 'has_preserved_preexisting_tracked_output_baseline_1'
         and old.get('files') == 171 and len(old.get('entries', {})) == 171, 'Original path catalogue required')
    need(set(intermediate.get('entries', {})) == set(old['entries']), 'Intermediate path set differs')
    identities[str(OLD)] = (OLD_SHA, old_identity)
    identities[str(INTERMEDIATE)] = (INTERMEDIATE_SHA, intermediate_identity)
    entries = {}
    output_identities = {}
    for name in sorted(old['entries']):
        path = PurePosixPath(name)
        need(path.as_posix() == name and len(path.parts) > 1 and path.parts[0] == 'output'
             and '..' not in path.parts and '\\' not in name and ':' not in name, 'Generated path scope')
        raw, identity = read(ROOT / name)
        entries[name] = dict(bytes=len(raw), mtime_ns=str(identity[3]), sha256=digest(raw))
        output_identities[name] = identity
    for name, row in entries.items():
        raw, identity = read(ROOT / name, row['sha256'])
        need(len(raw) == row['bytes'] and identity == output_identities[name], 'Complete output set did not stay stable')
    for path, (pin, identity) in identities.items():
        need(read(Path(path), pin)[1] == identity, 'Source or proof changed during complete capture')
    need(process_closed(launch['pid']) and process_closed(launch['coordinator_pid']), 'Verifier restarted or PID reused')
    captured = time.time_ns()
    original_completion_identity = identities[str(FULL / 'completion.json')][1]
    need(captured >= original_completion_identity[3], 'Capture predates completion')
    result = dict(format='has_post_full_authorized_generated_output_baseline_1', revision=REVISION,
        old_baseline_sha256=OLD_SHA, intermediate_baseline_sha256=INTERMEDIATE_SHA,
        closed_full_completion_sha256=options.completion_sha256,
        authorizing_full_launch_sha256=options.launch_sha256,
        full_source_after_sha256=options.source_after_sha256,
        original_completion_path=(FULL / 'completion.json').relative_to(ROOT).as_posix(),
        original_completion_mtime_ns=str(original_completion_identity[3]), captured_at_ns=str(captured),
        closed_process_point=dict(verifier_pid=launch['pid'], verifier_reaped=True, all_private_jobs_closed=True,
            root_exclusive_lane_quiescent=True, owned_processes_remaining=0),
        paths=171, complete_set_reread_stable=True, logical_bytes=sum(row['bytes'] for row in entries.values()),
        entries=entries, source_or_owner_inputs_modified_by_capture=False,
        preservation_scope='Final owned generated outputs after authorized Full refresh; not original171 byte preservation.')
    stage = ROOT / 'output' / ('post-full-output-preservation-' + str(captured))
    stage.mkdir(exist_ok=False)
    target = stage / 'POST_FULL_GENERATED_OUTPUT_BASELINE.json'
    raw = (json.dumps(result, indent=2) + '\n').encode('utf-8')
    with target.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    need(read(target, digest(raw))[0] == raw, 'Capture writeback differs')
    print(json.dumps(dict(path=str(target), bytes=len(raw), sha256=digest(raw), paths=171,
                          logical_bytes=result['logical_bytes'], current_functional_files=1084)))


if __name__ == '__main__':
    main()
