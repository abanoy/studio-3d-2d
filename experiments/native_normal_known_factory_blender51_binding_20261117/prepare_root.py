"""ROOT ONLY later: prepare private B admission/command, then EXIT; never launch it."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
SUCCESSOR = ROOT / 'experiments/native_normal_known_factory_blender51_resource_20261117'
SUCCESSOR_SHA = '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0'
CASES_PACKET = ROOT / 'experiments/neon_late_stage_cases_source_20261117'
CASES_SHA = '790277ef5e25f78e63d46350dba0304dce6c083c84ad5e010ac478fcea865ea3'
DRIVER = ROOT / 'experiments/run_neon_late_stage_3a_20261117.py'
DRIVER_SHA = '2096f28be4ed5898865c48866e1cf2197eebf1df203911677c45c2eebbb925e2'
REVIEW_COMMIT = '3a3701ab6edfa81dc883759403c170b8555aab07'
FUNCTIONAL_COMMIT = '52f63c944ded7a651da871524d23a345b606424d'
OLD52 = ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json'
OLD52_SHA = '4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7'
CAPTURE = ROOT / 'output/native-normal-B-resource-diagnostic-after-failed-full-20261117-attempt4/PRIVATE_FACTORY_HANDLERS.json'
GIT = Path(r'C:\Program Files\Git\cmd\git.EXE')
GIT_ID = {'bytes': 46480, 'mtime_ns': 1760720930000000000,
          'sha256': '544548de8c9bed98eb90531729a2955f554e7009338788b68777258ea61867e4'}
DEFAULT_PINS = {
    'ROOT-TOOL-TERMINATION.json': 'd3baf201994a70bb62f4bbcf99ed2e7afd97b66ebe40ddb04eb30614b29801b5',
    'verification.json': 'e366426598261c13674aafdd4c8fedc9cb5a350ebfcf8be08bd10906d4011167',
    'TARGETED-COMPLETION.json': '2ed5edd7bed4a83b2a3245ff73da41d52d7cf5c78ba55d83eba88e5b54e0408a',
    'source-before.json': '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc',
    'source-after.json': '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc',
}


def need(value, message):
    if not value: raise ValueError(message)


def utc(value):
    parsed = datetime.datetime.fromisoformat(value)
    need(parsed.tzinfo is not None, 'Aware timestamp required')
    return parsed


def validate_zero_scope(value):
    need(type(value) is dict and type(value.get('owned_count')) is int and value['owned_count'] == 0,
         'Actually closed targeted host scope required')
    need(value.get('termination_issued') is False and value.get('format') == 'has_root_workspace_scope_observation_1',
         'Read-only original targeted scope witness required')
    utc(value['observed_utc'])


def validate_terminal(witness, verification, completion, before, after, receipts, cases, driver_path, python_path,
                      session_id, now, canonical_report):
    """Pure closure join. A closed failed prefix is allowed; no full PASS gate."""
    need(type(witness) is dict and set(witness) == {'format', 'candidate_commit', 'driver_path', 'driver_sha256',
         'tool_session_id', 'observed_utc', 'tool_result'}, 'Exact outer tool-terminal witness required')
    need(witness['format'] == 'has_root_targeted_tool_terminal_observation_1'
         and witness['candidate_commit'] == REVIEW_COMMIT and witness['driver_path'] == driver_path
         and witness['driver_sha256'] == DRIVER_SHA and type(witness['tool_session_id']) is int
         and witness['tool_session_id'] == session_id, 'Exact candidate/driver/tool session required')
    need(utc(witness['observed_utc']) <= now, 'Terminal witness cannot be future-dated')
    tool = witness['tool_result']
    need(type(tool) is dict and 'session_id' not in tool and type(tool.get('exit_code')) is int
         and type(tool.get('output')) is str and type(tool.get('chunk_id')) is str and bool(tool['chunk_id'])
         and type(tool.get('wall_time_seconds')) in (int, float) and tool['wall_time_seconds'] >= 0,
         'Actual terminal tool result required; no outer Popen claim is inferred')
    need(type(before) is dict and before == after and len(before) == 1029, 'Targeted raw source maps differ')
    need(verification.get('format') == 'has_root_workspace_followup_1'
         and verification.get('all_functional_source_unchanged') is True
         and type(verification.get('functional_source_files')) is int and verification['functional_source_files'] == 1029
         and verification.get('host_scopes_closed') is True and verification.get('full_suite_pass_claimed') is False,
         'Closed unchanged targeted host verification required')
    need(completion.get('format') == 'has_targeted_neon_late_stage_completion_1'
         and completion.get('candidate_commit') == REVIEW_COMMIT
         and type(completion.get('expected_wrappers')) is int and completion['expected_wrappers'] == len(cases) == 44
         and completion.get('full_PASS_or_merge_claimed') is False
         and type(completion.get('all44_completed_and_canonical_reports_passed')) is bool,
         'Actual targeted terminal marker required')
    labels = [row[0] for row in cases]
    need(type(receipts) is dict and 0 < len(receipts) <= len(cases)
         and list(receipts) == labels[:len(receipts)], 'Executed retained-wrapper receipts must form the canonical prefix')
    rows = verification.get('rows')
    need(type(rows) is list and len(rows) in (len(receipts), len(receipts) - 1)
         and [row.get('label') for row in rows] == labels[:len(rows)], 'Host rows must join all completed receipts or their final assertion-failed predecessor')
    exits = []
    for index, (label, item) in enumerate(receipts.items()):
        process, start, command = item['process'], item['start'], item['command']
        need(process.get('label') == label and type(process.get('pid')) is int and process['pid'] > 0
             and type(process.get('exit')) is int and process.get('retained_Popen_reaped') is True
             and process.get('timed_out') is False, 'Actual retained wrapper must be terminal and reaped')
        need(type(start.get('pid')) is int and start['pid'] == process['pid'] and start.get('retained_Popen') is True,
             'Wrapper retained-start/process PID join differs')
        need(utc(start['started_utc']) <= utc(witness['observed_utc']), 'Wrapper start must precede tool termination')
        need(command == [python_path, '-B', '-u', str(REVIEW / 'tests' / cases[index][1]), *cases[index][2]],
             'Exact authored wrapper invocation required')
        if index < len(rows):
            for key in ('label', 'pid', 'exit', 'retained_Popen_reaped', 'seconds', 'timed_out'):
                need(type(rows[index].get(key)) is type(process.get(key)) and rows[index][key] == process[key], 'Per-wrapper/host row join differs')
            validate_zero_scope(item['closure'])
        elif 'closure' in item:
            validate_zero_scope(item['closure'])
        exits.append(process['exit'])
    need(all(code == 0 for code in exits[:-1]), 'No wrappers may follow a failed wrapper')
    expected_host_pass = bool(rows) and all(row['exit'] == 0 for row in rows)
    need(type(verification.get('passed')) is bool and verification['passed'] == expected_host_pass, 'Host pass scalar differs from its own rows')
    completed = completion['all44_completed_and_canonical_reports_passed']
    need((tool['exit_code'] == 0) is completed, 'Tool terminal exit and targeted completion disagree')
    need(completion.get('host_return') is None or type(completion['host_return']) is int, 'Host return type differs')
    if completed:
        need(len(rows) == len(receipts) == 44 and all(code == 0 for code in exits)
             and type(completion['host_return']) is int and completion['host_return'] == 0, 'Completed targeted marker lacks all original rows')
        for row in rows: canonical_report(row['label'], row['report'])
    return {'executed_wrappers': len(receipts), 'reported_rows': len(rows), 'targeted_completed': completed,
            'outer_tool_exit': tool['exit_code'], 'outer_Popen_or_birth_claimed': False}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparer-index-sha256', required=True)
    parser.add_argument('--root-lane-closed', action='store_true', required=True)
    parser.add_argument('--cold187-disposition', choices=['NOT_STARTED_CURRENT_CONTEXT'], required=True)
    parser.add_argument('--pose-source', type=Path, required=True)
    parser.add_argument('--transform-source', type=Path, required=True)
    parser.add_argument('--targeted-run', type=Path, default=REVIEW / 'output/neon-late-3a-attempt2')
    parser.add_argument('--tool-session-id', type=int, default=20079)
    parser.add_argument('--closed-pins', type=Path, help='Optional Root-issued exact five metadata pins for another actual closed run')
    parser.add_argument('--label')
    args = parser.parse_args(); need(os.name == 'nt', 'Root Windows preparation only')
    need(hashlib.sha256((SUCCESSOR / 'INDEX.json').read_bytes()).hexdigest() == SUCCESSOR_SHA, 'Exact sealed successor required')
    sys.path.insert(0, str(SUCCESSOR))
    S = module('diagnostic_support', SUCCESSOR / 'diagnostic_support.py'); sys.modules['diagnostic_support'] = S
    S.packet(SUCCESSOR, SUCCESSOR_SHA); S.packet(Path(__file__).resolve().parent, args.preparer_index_sha256)
    S.packet(CASES_PACKET, CASES_SHA)
    A = module('known_factory_binding_late_cases', CASES_PACKET / 'late_cases.py')
    R = module('known_factory_binding_root_driver', SUCCESSOR / 'root_runner.py')
    reader = S.reader()

    def descriptor(path):
        path = S.safe(path)
        return {'path': str(path), **reader.identity(path, single_link=True)}

    def read_stable(path, pin=None, maximum=8 * 1024 * 1024):
        first = descriptor(path); need(first['bytes'] <= maximum and (pin is None or first['sha256'] == pin), 'Bounded exact metadata required')
        value = S.read_json(path, maximum); need(descriptor(path) == first, 'Metadata changed during read')
        return value

    need(reader.identity(S.safe(GIT), single_link=False) == GIT_ID, 'Pinned read-only Git executable differs')
    def git_head(folder):
        result = subprocess.check_output([str(GIT), 'rev-parse', 'HEAD'], cwd=folder, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        need(re.fullmatch('[a-f0-9]{40}', result), 'Exact metadata HEAD required')
        return result
    head = git_head(ROOT); need(git_head(REVIEW) == REVIEW_COMMIT, 'Current corrected Review HEAD differs')
    need(S.digest(DRIVER.read_bytes()) == DRIVER_SHA, 'Targeted driver source changed')
    old = read_stable(OLD52, OLD52_SHA); S.check_snapshot(ROOT, old, FUNCTIONAL_COMMIT, 1019)
    run = S.safe(args.targeted_run); need(run.parent == REVIEW / 'output', 'Direct closed Review/output run required')
    pins = DEFAULT_PINS if args.closed_pins is None else read_stable(args.closed_pins, maximum=65536)
    need(type(pins) is dict and set(pins) == set(DEFAULT_PINS)
         and all(type(pin) is str and re.fullmatch('[a-f0-9]{64}', pin) for pin in pins.values()), 'Exact five actual closed metadata pins required')
    data = {name: read_stable(run / name, pin) for name, pin in pins.items()}
    before, after = data['source-before.json'], data['source-after.json']
    snapshot = {'commit': REVIEW_COMMIT, 'source_sha256': after}
    S.check_snapshot(REVIEW, snapshot, REVIEW_COMMIT, 1029)
    for name in ('before-closure.json', 'after-closure.json'): validate_zero_scope(read_stable(run / name, maximum=65536))
    receipts = {}; gap = False
    for label, *_ in A.CASES:
        if not (run / (label + '-process.json')).exists(): gap = True; continue
        need(not gap, 'Executed wrapper receipt after a gap refused')
        item = {role: read_stable(run / (label + suffix), maximum=65536)
                for role, suffix in (('process', '-process.json'), ('start', '-start.json'), ('command', '-command.json'))}
        closure = run / (label + '-after-closure.json')
        if closure.exists(): item['closure'] = read_stable(closure, maximum=65536)
        receipts[label] = item
    terminal = validate_terminal(data['ROOT-TOOL-TERMINATION.json'], data['verification.json'],
        data['TARGETED-COMPLETION.json'], before, after, receipts, A.CASES, str(DRIVER),
        r'C:\Program Files\Python313\python.exe', args.tool_session_id, datetime.datetime.now(datetime.timezone.utc), A.assert_canonical_report)
    label = args.label or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    need(re.fullmatch('[A-Za-z0-9-]{3,70}', label), 'Bounded destination label required')
    folder = S.safe(ROOT / 'output' / ('PRIVATE-B-known-factory-binding-' + label))
    output = S.safe(ROOT / 'output' / ('native-normal-B-known-factory-' + label))
    need(not folder.exists() and not output.exists(), 'Fresh separate binding and native output destinations required')
    admission = S.read_json(SUCCESSOR / 'ADMISSION.template.json')
    admission.update(root_native_lane_exclusive=True, expected_metadata_head=head, candidate_commit=REVIEW_COMMIT,
        cold187_disposition=args.cold187_disposition, output=str(output),
        sourceio_copy=str(REVIEW / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'))
    for role, row in admission['protected_originals'].items():
        actual = descriptor(row['path']); need(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], 'Known B companion differs')
        admission['protected_originals'][role] = actual
    admission['factory_baseline']['capture'] = descriptor(CAPTURE)
    for role, path in (('POSE_LIBRARY_GUI', args.pose_source), ('COPY_GLOBAL_TRANSFORM', args.transform_source)):
        admission['factory_baseline']['public_sources'][role] = descriptor(path)
    S.H.read_bound_baseline(admission['factory_baseline'], reader, S.safe, ROOT)
    folder.mkdir(exist_ok=False)
    root_snapshot = {'commit': FUNCTIONAL_COMMIT, 'source_sha256': old['source_sha256']}
    for name, value in (('CURRENT_ROOT_FUNCTIONAL_SNAPSHOT.json', root_snapshot), ('CURRENT_REVIEW_FUNCTIONAL_SNAPSHOT.json', snapshot)):
        S.save(folder / name, value)
    admission['proofs']['functional_snapshot'] = descriptor(folder / 'CURRENT_ROOT_FUNCTIONAL_SNAPSHOT.json')
    admission['proofs']['review_functional_snapshot'] = descriptor(folder / 'CURRENT_REVIEW_FUNCTIONAL_SNAPSHOT.json')
    fresh = R.closure(folder, 'fresh-before-binding')  # excludes this helper and its observer PID only.
    need(git_head(ROOT) == head and git_head(REVIEW) == REVIEW_COMMIT, 'HEAD changed during preparation')
    record = S.read_json(SUCCESSOR / 'CURRENT-CLOSED-LANE.template.json')
    record.update(observed_utc=fresh['observed_utc'], root_native_lane_exclusive=True, ui_lane_closed=True,
        all_owned_jobs_desktops_closed=True, source_unchanged=True, current_full_run_active=False,
        current_targeted_run_active=False, cold187_launched=False, termination_issued=False,
        owned_count=0, main_count=0, neon_count=0, root_metadata_head=head, root_functional_commit=FUNCTIONAL_COMMIT,
        root_functional_count=1019, review_commit=REVIEW_COMMIT, review_functional_count=1029,
        root_snapshot_sha256=admission['proofs']['functional_snapshot']['sha256'],
        review_snapshot_sha256=admission['proofs']['review_functional_snapshot']['sha256'], cold187_disposition=args.cold187_disposition)
    record.update(targeted_terminal=terminal, targeted_tool_witness=descriptor(run / 'ROOT-TOOL-TERMINATION.json'),
        targeted_source_before=descriptor(run / 'source-before.json'), targeted_source_after=descriptor(run / 'source-after.json'),
        fresh_scope_observation=descriptor(folder / 'fresh-before-binding-closure.json'), outer_Popen_or_birth_claimed=False)
    S.save(folder / 'CURRENT-CLOSED-LANE.json', record)
    admission['proofs']['closed_lane_root_record'] = descriptor(folder / 'CURRENT-CLOSED-LANE.json')
    issued = datetime.datetime.now(datetime.timezone.utc)
    admission.update(issued_utc=issued.isoformat(), expires_utc=(issued + datetime.timedelta(seconds=600)).isoformat())
    S.validate_admission(admission, issued); S.validate_current_closed_lane(admission, {'closed_lane_root_record': record})
    path = folder / 'ADMISSION.json'; S.save(path, admission)
    # This invokes the unchanged six-tool/574+copy/120/B/source/preservation gate;
    # it performs no Blender load, resource survey or driver launch.
    S.check_inputs(path, S.digest(path.read_bytes()), SUCCESSOR_SHA)
    R.closure(folder, 'fresh-after-binding')
    need(git_head(ROOT) == head and git_head(REVIEW) == REVIEW_COMMIT, 'HEAD changed before command preparation')
    need(reader.identity(S.safe(GIT), single_link=False) == GIT_ID, 'Read-only Git identity changed')
    command = [str(sys.executable), '-B', str(SUCCESSOR / 'root_runner.py'), '--admission', str(path),
        '--admission-sha256', S.digest(path.read_bytes()), '--packet-index-sha256', SUCCESSOR_SHA, '--root-lane-confirmed']
    need(str(S.safe(sys.executable)) in S.read_json(S.LOCK)['runtime_executables']
         and Path(sys.executable).name.lower() == 'python.exe', 'Approved direct root Python required')
    S.save(folder / 'ROOT_COMMAND.json', command)
    result = {'format': 'has_root_known_factory_prepared_only_1', 'prepared_only': True, 'command': command,
        'preparer_must_exit_before_direct_root_launch': True, 'runner_launched': False,
        'outer_tool_terminal_validated': True, 'outer_Popen_or_birth_claimed': False,
        'targeted_terminal': terminal, 'full_suite_pass_claimed': False}
    S.save(folder / 'PREPARED-ONLY.json', result); print(json.dumps(result, sort_keys=True))
    return 0  # No invocation of command, root_runner.main, invoke or Blender.


if __name__ == '__main__': raise SystemExit(main())
