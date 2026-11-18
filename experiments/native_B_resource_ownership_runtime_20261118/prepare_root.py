"""ROOT ONLY later: bind the fixed tested1029/dcb context, write command, EXIT."""
from pathlib import Path
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import diagnostic_support as S
from current_context import EXPECTED_METADATA_HEAD
from qualified_context import TESTED, check_qualified_context, SOURCE_SHA, FULL_SHA, REVIEWED_SHA

HERE = Path(__file__).resolve().parent
CAPTURE = S.ROOT / 'output/native-normal-B-resource-diagnostic-after-failed-full-20261117-attempt4/PRIVATE_FACTORY_HANDLERS.json'
GIT = Path(r'C:\Program Files\Git\cmd\git.EXE')
GIT_ID = {'bytes': 46480, 'mtime_ns': 1760720930000000000,
          'sha256': '544548de8c9bed98eb90531729a2955f554e7009338788b68777258ea61867e4'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-index-sha256', required=True)
    parser.add_argument('--root-lane-closed', action='store_true', required=True)
    parser.add_argument('--cold187-disposition', choices=['NOT_STARTED_CURRENT_CONTEXT'], required=True)
    parser.add_argument('--pose-source', type=Path, required=True)
    parser.add_argument('--transform-source', type=Path, required=True)
    parser.add_argument('--label')
    args = parser.parse_args(); S.need(os.name == 'nt', 'Root Windows preparation only')
    S.packet(HERE, args.packet_index_sha256)
    from root_runner import closure
    reader = S.reader()

    def descriptor(path):
        path = S.safe(path)
        return {'path': str(path), **reader.identity(path, single_link=True)}

    S.need(reader.identity(S.safe(GIT), single_link=False) == GIT_ID, 'Pinned read-only Git executable differs')
    def git_head(folder):
        value = subprocess.check_output([str(GIT), 'rev-parse', 'HEAD'], cwd=folder,
                                       creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        S.need(re.fullmatch('[a-f0-9]{40}', value), 'Exact metadata HEAD required')
        return value

    S.need(git_head(S.ROOT) == EXPECTED_METADATA_HEAD and git_head(S.REVIEW) == TESTED,
           'Exact dcb Main and tested3a Review metadata checkpoints required')
    snapshot = check_qualified_context()
    S.check_snapshot(S.ROOT, snapshot, TESTED, 1029)
    S.check_snapshot(S.REVIEW, snapshot, TESTED, 1029)
    label = args.label or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    S.need(re.fullmatch('[A-Za-z0-9-]{3,70}', label), 'Bounded destination label required')
    folder = S.safe(S.ROOT / 'output' / ('PRIVATE-B-ownership-binding-' + label))
    output = S.safe(S.ROOT / 'output' / ('native-normal-B-ownership-' + label))
    S.need(not folder.exists() and not output.exists(), 'Fresh separate binding and native output destinations required')
    admission = S.read_json(HERE / 'ADMISSION.template.json')
    admission.update(root_native_lane_exclusive=True, cold187_disposition=args.cold187_disposition,
        output=str(output), sourceio_copy=str(S.REVIEW / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'))
    for role, row in admission['protected_originals'].items():
        actual = descriptor(row['path'])
        S.need(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], 'Known B companion differs')
        admission['protected_originals'][role] = actual
    admission['factory_baseline']['capture'] = descriptor(CAPTURE)
    for role, path in (('POSE_LIBRARY_GUI', args.pose_source), ('COPY_GLOBAL_TRANSFORM', args.transform_source)):
        admission['factory_baseline']['public_sources'][role] = descriptor(path)
    S.H.read_bound_baseline(admission['factory_baseline'], reader, S.safe, S.ROOT)
    folder.mkdir(exist_ok=False)
    for name in ('CURRENT_ROOT_FUNCTIONAL_SNAPSHOT.json', 'CURRENT_REVIEW_FUNCTIONAL_SNAPSHOT.json'):
        S.save(folder / name, snapshot)
    admission['proofs']['functional_snapshot'] = descriptor(folder / 'CURRENT_ROOT_FUNCTIONAL_SNAPSHOT.json')
    admission['proofs']['review_functional_snapshot'] = descriptor(folder / 'CURRENT_REVIEW_FUNCTIONAL_SNAPSHOT.json')
    fresh = closure(folder, 'fresh-before-binding')
    S.need(git_head(S.ROOT) == EXPECTED_METADATA_HEAD and git_head(S.REVIEW) == TESTED,
           'Metadata checkpoints changed during preparation')
    record = S.read_json(HERE / 'CURRENT-CLOSED-LANE.template.json')
    record.update(observed_utc=fresh['observed_utc'], root_native_lane_exclusive=True, ui_lane_closed=True,
        all_owned_jobs_desktops_closed=True, source_unchanged=True, current_full_run_active=False,
        current_targeted_run_active=False, cold187_launched=False, termination_issued=False,
        owned_count=0, main_count=0, neon_count=0, root_metadata_head=EXPECTED_METADATA_HEAD,
        root_functional_commit=TESTED, root_functional_count=1029, review_commit=TESTED, review_functional_count=1029,
        root_snapshot_sha256=admission['proofs']['functional_snapshot']['sha256'],
        review_snapshot_sha256=admission['proofs']['review_functional_snapshot']['sha256'],
        cold187_disposition=args.cold187_disposition,
        immutable_tested1029_source_sha256=SOURCE_SHA, qualified_full_INDEX_sha256=FULL_SHA,
        reviewed39_delta_sha256=REVIEWED_SHA, historical_full_qualification_is_not_fresh_scope_authority=True,
        fresh_scope_observation=descriptor(folder / 'fresh-before-binding-closure.json'),
        outer_Popen_or_birth_claimed=False)
    S.save(folder / 'CURRENT-CLOSED-LANE.json', record)
    admission['proofs']['closed_lane_root_record'] = descriptor(folder / 'CURRENT-CLOSED-LANE.json')
    issued = datetime.datetime.now(datetime.timezone.utc)
    admission.update(issued_utc=issued.isoformat(), expires_utc=(issued + datetime.timedelta(seconds=600)).isoformat())
    S.validate_admission(admission, issued)
    S.validate_current_closed_lane(admission, {'closed_lane_root_record': record})
    path = folder / 'ADMISSION.json'; S.save(path, admission)
    # Retains the six-tool/574+copy/120/B/source/preservation admission gate.
    S.check_inputs(path, S.digest(path.read_bytes()), args.packet_index_sha256)
    closure(folder, 'fresh-after-binding')
    S.need(git_head(S.ROOT) == EXPECTED_METADATA_HEAD and git_head(S.REVIEW) == TESTED,
           'Metadata checkpoints changed before command preparation')
    S.need(reader.identity(S.safe(GIT), single_link=False) == GIT_ID, 'Read-only Git identity changed')
    command = [str(sys.executable), '-B', str(HERE / 'root_runner.py'), '--admission', str(path),
        '--admission-sha256', S.digest(path.read_bytes()), '--packet-index-sha256', args.packet_index_sha256,
        '--root-lane-confirmed']
    S.need(str(S.safe(sys.executable)) in S.read_json(S.LOCK)['runtime_executables']
           and Path(sys.executable).name.lower() == 'python.exe', 'Approved direct root Python required')
    S.save(folder / 'ROOT_COMMAND.json', command)
    result = {'format': 'has_root_ownership_prepared_only_1', 'prepared_only': True, 'command': command,
        'preparer_must_exit_before_direct_root_launch': True, 'runner_launched': False,
        'source_context': 'IMMUTABLE_TESTED1029_AT_DCB', 'full_suite_pass_claimed': False,
        'outer_Popen_or_birth_claimed': False}
    S.save(folder / 'PREPARED-ONLY.json', result); print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__': raise SystemExit(main())
