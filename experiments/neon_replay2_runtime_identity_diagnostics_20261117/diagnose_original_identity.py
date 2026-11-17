"""Read-only diagnostics of the original guard over exactly six approved binaries."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
OUTPUT = Path(__file__).with_name('DIAGNOSTICS.json')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
source_before = sha(SOURCE)
lock_before = sha(LOCK)
assert lock_before == '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
runtime = json.loads(LOCK.read_bytes())['runtime_executables']
assert len(runtime) == 6
spec = importlib.util.spec_from_file_location('unchanged_protected_input_identity_diagnostic', SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
assert sha(SOURCE) == source_before
stamp_names = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink', 'st_file_attributes')

def metadata(info):
    return {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}

rows = []
for round_number in (1, 2):
    for name, expected in runtime.items():
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        start = time.perf_counter_ns()
        row = {'round': round_number, 'path': name, 'expected': expected, 'started_utc': started}
        try:
            observed = audit.identity(Path(name))
        except Exception as error:
            trace = error.__traceback__
            frames = []
            while trace is not None:
                if trace.tb_frame.f_code is audit.identity.__code__:
                    frames.append(trace.tb_frame)
                trace = trace.tb_next
            row.update({'status': 'ORIGINAL_IDENTITY_EXCEPTION', 'exception_type': type(error).__name__,
                        'exception': str(error), 'original_identity_frames': len(frames)})
            assert len(frames) == 1, 'Original identity traceback frame not retained'
            local = frames[0].f_locals
            snapshots = {key: metadata(local[key]) for key in ('before', 'opened', 'after', 'final') if key in local}
            stamps = {key: list(audit.stamp(local[key])) for key in snapshots}
            differences = {}
            if 'before' in snapshots:
                for key in ('opened', 'after', 'final'):
                    if key not in snapshots:
                        continue
                    delta = {}
                    for field in sorted(set(snapshots['before']) | set(snapshots[key])):
                        before = snapshots['before'].get(field)
                        actual = snapshots[key].get(field)
                        if before != actual:
                            item = {'before': before, 'actual': actual}
                            if isinstance(before, (int, float)) and isinstance(actual, (int, float)):
                                item['delta'] = actual - before
                            delta[field] = item
                    differences[key] = delta
            row.update({'original_frame_path': str(local.get('path')),
                        'original_frame_single_link': local.get('single_link'),
                        'all_stat_fields': snapshots, 'original_guard_stamp_fields': list(stamp_names),
                        'original_guard_stamps': stamps, 'deltas_from_before_all_stat_fields': differences,
                        'guard_mismatches': {key: {field: differences[key][field] for field in stamp_names if field in differences[key]}
                                             for key in differences},
                        'digest_captured': 'digest' in local, 'digest': local.get('digest')})
            if 'digest' in local and 'final' in snapshots:
                partial = {'bytes': snapshots['final']['st_size'], 'mtime_ns': snapshots['final']['st_mtime_ns'],
                           'sha256': local['digest']}
                row['captured_content_identity'] = partial
                row['captured_content_identity_matches_lock'] = partial == expected
        else:
            row.update({'status': 'ORIGINAL_IDENTITY_RETURNED', 'observed': observed,
                        'identity_matches_lock': observed == expected,
                        'identity_differences': {key: {'expected': expected.get(key), 'actual': observed.get(key)}
                                                 for key in sorted(set(expected) | set(observed)) if expected.get(key) != observed.get(key)}})
        row['elapsed_ns'] = time.perf_counter_ns() - start
        row['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows.append(row)

assert sha(SOURCE) == source_before and sha(LOCK) == lock_before
assert len(rows) == 12 and {row['path'] for row in rows} == set(runtime)
exceptions = [row for row in rows if row['status'] == 'ORIGINAL_IDENTITY_EXCEPTION']
result = {'format': 'has_original_six_runtime_identity_diagnostics_1',
          'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'execution_context': 'default_tool_context_no_escalation', 'python_executable': sys.executable,
          'source_path': str(SOURCE), 'source_sha256_before_and_after': source_before,
          'lock_path': str(LOCK), 'lock_sha256_before_and_after': lock_before,
          'diagnostic_source_sha256': sha(Path(__file__)), 'runtime_files': 6, 'rounds': 2,
          'identity_calls': 12, 'original_identity_exceptions': len(exceptions),
          'all_successful_returns_match_lock': all(row['identity_matches_lock'] for row in rows if row['status'] == 'ORIGINAL_IDENTITY_RETURNED'),
          'original_two_preflight_refusal_causes': 'UNKNOWN_NOT_CAPTURED',
          'guard_monkeypatch_or_relaxation': False, 'runtime_binaries_executed': False,
          'CIM_or_process_queries': False, 'artist_inputs_opened': False,
          'preflight_or_run_reservation_or_engine_launch': False, 'rows': rows}
with OUTPUT.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps({'report': str(OUTPUT), 'report_sha256': sha(OUTPUT),
                  'source_sha256': source_before, 'identity_calls': 12,
                  'original_identity_exceptions': len(exceptions),
                  'all_successful_returns_match_lock': result['all_successful_returns_match_lock'],
                  'mismatch_fields': sorted({field for row in exceptions for values in row['guard_mismatches'].values() for field in values})}))
