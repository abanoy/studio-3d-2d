"""Root-only later: two separate CPU phases, retained child and60s/case deadline."""
from pathlib import Path
import argparse
import json
import math
import os
import subprocess
import sys
import time
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as S

RETAINED_UNCONFIRMED = []


class UnconfirmedClosure(RuntimeError):
    """Retains the exact owned Popen for API callers; never a PID-kill authority."""
    def __init__(self, process, case, record):
        super().__init__('owned child closure unconfirmed; Root intervention required')
        self.process = process; self.case = case; self.record = record


def reaped(process):
    try: return process.poll() is not None
    except BaseException: return False


def run_child(command, case, timeout=60):
    """Terminate only this retained Popen on deadline; never search/kill PIDs."""
    started = time.perf_counter(); process = None; timed_out = False; failure = None
    out_path = case / 'PRIVATE_STDOUT.log'; err_path = case / 'PRIVATE_STDERR.log'
    with out_path.open('xb') as out, err_path.open('xb') as err:
        try:
            process = subprocess.Popen(command, cwd=case, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            try: process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True; process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
        except BaseException as error:
            failure = error
        finally:
            if process is not None and not reaped(process):
                timed_out = True
                try: process.kill(); process.wait(timeout=5)
                except BaseException as error: failure = failure or error
    if process is None:
        if failure is not None: raise failure
        raise S.Refusal('CPU child was not created')
    closed = reaped(process)
    result = {'exit': process.returncode, 'timed_out': timed_out, 'retained_Popen_reaped': closed,
              'parent_wall_seconds': time.perf_counter() - started, 'child_deadline_seconds': timeout,
              'stream_acceptance_cap_passed': False, 'stream_size_observation_completed': False,
              'hard_memory_enforcement': False, 'native_protocol_qualified': False}
    if not closed:
        unconfirmed = UnconfirmedClosure(process, case, result)
        RETAINED_UNCONFIRMED.append(unconfirmed)
        ownership = {'format': 'has_private_retained_CPU_child_unconfirmed_closure_1',
                     'child_pid': process.pid, 'argv': command, 'process': result,
                     'failure_type': type(failure).__name__ if failure is not None else None,
                     'batch_must_stop': True, 'Root_ownership_intervention_required': True,
                     'lane_closed': False, 'arbitrary_PID_kill_authorized': False,
                     'native_protocol_qualified': False}
        try: S.save(case / 'PRIVATE_OWNERSHIP_FAILURE.json', ownership)
        except BaseException as error: result['ownership_record_write_failure_type'] = type(error).__name__
        try: S.save(case / 'PRIVATE_PROCESS.json', result)
        except BaseException as error: result['process_record_write_failure_type'] = type(error).__name__
        raise unconfirmed from failure
    result['stream_acceptance_cap_passed'] = (out_path.stat().st_size <= 4 * 1024 * 1024
                                             and err_path.stat().st_size <= 4 * 1024 * 1024)
    result['stream_size_observation_completed'] = True
    S.save(case / 'PRIVATE_PROCESS.json', result)
    if failure is not None: raise failure
    return result


def project(phase, cases, synthetic):
    """Procedural scalars only: no artist names, paths, inputs or table payloads."""
    return {'format': 'has_pmx_CPU_observation_public_scalars_1', 'phase': phase, 'synthetic_inputs': synthetic, 'cases': len(cases),
            'completed_cases': sum(row['completed'] is True for row in cases),
            'preserved_cases': sum(row['preserved'] is True for row in cases),
            'timed_out_cases': sum(row['process'].get('timed_out') is True for row in cases),
            'unstarted_cases': sum(row.get('unstarted') is True for row in cases),
            'unconfirmed_child_closure_cases': sum(row.get('unconfirmed_child_closure') is True for row in cases),
            'Root_ownership_intervention_required': any(row.get('unconfirmed_child_closure') is True for row in cases),
            'parent_wall_measured_cases': sum('parent_wall_seconds' in row['process'] for row in cases),
            'max_parent_wall_seconds': max((row['process']['parent_wall_seconds'] for row in cases if 'parent_wall_seconds' in row['process']), default=None),
            'python_allocation_measured_cases': sum(type(row.get('python_tracemalloc_peak_bytes')) is int for row in cases),
            'max_observed_python_allocation_peak_bytes': max((row['python_tracemalloc_peak_bytes'] for row in cases if type(row.get('python_tracemalloc_peak_bytes')) is int), default=None),
            'Windows_peak_RSS_measured': False, 'hard_memory_enforcement': False, 'IO_confinement_claimed': False,
            'actual_model_conversion_or_HAS_retention': False, 'native_protocol_qualified': False,
            'simulation_or_production_adoption': False}


def checked_receipt(value, phase, index):
    S.need(type(value) is dict and value.get('format') == 'has_private_pmx_readonly_CPU_case_receipt_1'
           and value.get('phase') == phase and type(value.get('case_index')) is int and value['case_index'] == index
           and type(value.get('completed')) is bool and type(value.get('preserved')) is bool
           and value.get('native_protocol_qualified') is False and value.get('hard_memory_enforcement') is False
           and value.get('denied_write_delete_handles_or_IO_confinement') is False
           and value.get('simulation_or_production_adoption') is False
           and value.get('windows_peak_RSS_bytes') is None
           and type(value.get('child_wall_seconds')) is float and math.isfinite(value['child_wall_seconds']) and value['child_wall_seconds'] >= 0
           and type(value.get('python_tracemalloc_peak_bytes')) is int and value['python_tracemalloc_peak_bytes'] >= 0,
           'exact unqualified measured child receipt required')
    if value['completed']:
        S.need(value['preserved'] and type(value.get('detail')) is dict, 'completed child preservation/detail required')
        detail = value['detail']
        if phase == 'oracle':
            S.need(type(detail.get('witness_bytes')) is int and 0 < detail['witness_bytes'] <= 8 * 1024 * 1024
                   and type(detail.get('witness_sha256')) is str and S.re.fullmatch('[a-f0-9]{64}', detail['witness_sha256'])
                   and detail.get('candidate_or_archive_imported') is False, 'independent bounded witness receipt required')
        else:
            S.need(detail.get('declaration_correspondence_observed') is True and detail.get('archive_exact_roundtrip_observed') is True
                   and detail.get('archive_carrier_is_authored_empty_GLB') is True
                   and detail.get('actual_model_GLTF_or_HAS_retention_observed') is False, 'bounded declaration-only roundtrip receipt required')
    return value


def run_batch(phase, ctx, output, *, harness_sha=None, root_closed=False,
              oracle_manifest=None, oracle_sha=None, root_frozen=False):
    S.need(all(reaped(row.process) for row in RETAINED_UNCONFIRMED), 'Root must resolve previous owned child closure first')
    S.need(phase in ('oracle', 'compare') and (ctx['synthetic'] or root_closed is True), 'Root closed-lane CPU phase required')
    S.need(ctx['synthetic'] or os.name == 'nt', 'actual Root observation is Windows-only')
    S.need(Path(sys.executable).resolve() == ctx['python'] and S.sha(ctx['python'].read_bytes()) == ctx['python_sha'], 'approved Python parent required')
    binding = S.code_binding()
    base_request = {'synthetic_root': str(ctx['copy_root'].parent) if ctx['synthetic'] else None,
                    'synthetic_provenance_sha256': ctx['provenance_sha'] if ctx['synthetic'] else None,
                    'harness_index_sha256': harness_sha, 'code_binding': binding,
                    'root_graphics_lane_closed': root_closed, 'phase': phase,
                    'root_witness_frozen': root_frozen,
                    'oracle_manifest': str(oracle_manifest) if oracle_manifest is not None else None,
                    'oracle_manifest_sha256': oracle_sha}
    S.verify_code(base_request)
    provenance = S.load_provenance(ctx)
    if phase == 'compare':
        S.need(root_frozen is True and type(oracle_sha) is str, 'Root must independently freeze oracle manifest before candidate phase')
        S.frozen_manifest(ctx, oracle_manifest, oracle_sha, harness_sha, binding)
    target = S.output_path(ctx, output); S.need(not target.exists(), 'fresh private phase directory required')
    target.mkdir()
    cases = []
    for i in range(4):
        case = target / ('case-' + str(i)); case.mkdir()
        request = dict(base_request, case_index=i, batch_output=str(target))
        S.save(case / 'PRIVATE_REQUEST.json', request)
        command = [str(ctx['python']), '-I', '-S', '-B', '-X', 'utf8', str(S.HERE / 'worker.py'),
                   '--request', str(case / 'PRIVATE_REQUEST.json'), '--request-sha256', S.sha(S.canonical(request))]
        S.save(case / 'PRIVATE_COMMAND.json', {'argv': command})
        process = {}; receipt = {}; completed = preserved = False; unconfirmed = False
        try:
            process = run_child(command, case)
            if not process['timed_out'] and process['retained_Popen_reaped']:
                receipt = checked_receipt(S.read_json(case / 'PRIVATE_RECEIPT.json', 128 * 1024), phase, i)
                preserved = receipt['preserved'] is True
                completed = (process['exit'] == 0 and process['stream_acceptance_cap_passed']
                             and receipt['completed'] is True and preserved)
        except UnconfirmedClosure as error:
            # Keep the exact Popen reachable for the API caller; never launch another case.
            if error not in RETAINED_UNCONFIRMED: RETAINED_UNCONFIRMED.append(error)
            process = error.record; unconfirmed = True
        except BaseException as error:
            (case / 'PRIVATE_PARENT_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
            if isinstance(error, (KeyboardInterrupt, SystemExit)): raise
        row = {'case_index': i, 'completed': completed, 'preserved': preserved, 'process': process,
               'unstarted': False, 'unconfirmed_child_closure': unconfirmed,
               'python_tracemalloc_peak_bytes': receipt.get('python_tracemalloc_peak_bytes')}
        if completed and phase == 'oracle':
            detail = receipt['detail']; row.update(witness_bytes=detail['witness_bytes'], witness_sha256=detail['witness_sha256'])
        if completed and phase == 'compare':
            row.update(declaration_correspondence_observed=receipt['detail']['declaration_correspondence_observed'],
                       archive_exact_roundtrip_observed=receipt['detail']['archive_exact_roundtrip_observed'])
        cases.append(row)
        if unconfirmed:
            cases.extend({'case_index': j, 'completed': False, 'preserved': False, 'process': {},
                          'unstarted': True, 'unconfirmed_child_closure': False,
                          'python_tracemalloc_peak_bytes': None} for j in range(i + 1, 4))
            S.save(target / 'PRIVATE_BATCH_STOPPED.json',
                   {'reason': 'retained_child_closure_unconfirmed', 'case_index': i,
                    'unstarted_case_indices': list(range(i + 1, 4)), 'lane_closed': False,
                    'Root_ownership_intervention_required': True, 'arbitrary_PID_kill_authorized': False})
            break
    manifest = {'format': 'has_private_pmx_oracle_observation_phase_1' if phase == 'oracle' else 'has_private_pmx_candidate_observation_phase_1',
                'phase': phase, 'cases': cases, 'all_cases_completed_and_preserved': all(row['completed'] and row['preserved'] for row in cases),
                'provenance_sha256': ctx['provenance_sha'], 'harness_index_sha256': harness_sha, 'code_binding': binding,
                'source_indexes': {key: value[1] for key, value in S.PACKETS.items()},
                'oracle_manifest_sha256_frozen_by_Root': oracle_sha if phase == 'compare' else None,
                'ordinary_readonly_observed_stability_only': True, 'native_protocol_qualified': False}
    S.save(target / ('PRIVATE_ORACLE_PHASE.json' if phase == 'oracle' else 'PRIVATE_CANDIDATE_PHASE.json'), manifest)
    return manifest, project(phase, cases, ctx['synthetic'])


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=('oracle', 'compare'), required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--harness-index-sha256')
    parser.add_argument('--root-graphics-lane-closed', action='store_true')
    parser.add_argument('--oracle-manifest', type=Path); parser.add_argument('--oracle-manifest-sha256')
    parser.add_argument('--root-witness-frozen', action='store_true')
    parser.add_argument('--synthetic-root', type=Path); parser.add_argument('--synthetic-provenance-sha256')
    args = parser.parse_args(); target = None
    try:
        ctx = S.context(args.synthetic_root, args.synthetic_provenance_sha256)
        _manifest, public = run_batch(args.phase, ctx, args.output, harness_sha=args.harness_index_sha256,
            root_closed=args.root_graphics_lane_closed, oracle_manifest=args.oracle_manifest,
            oracle_sha=args.oracle_manifest_sha256, root_frozen=args.root_witness_frozen)
        if public['Root_ownership_intervention_required']:
            public['format'] = 'has_pmx_CPU_observation_unconfirmed_closure_failure_1'
        print(json.dumps(public, sort_keys=True, allow_nan=False))
        return 0 if public['completed_cases'] == public['cases'] == 4 else 1
    except BaseException as error:
        # No exception values/paths are echoed to the parent's public channel.
        unresolved = any(not reaped(row.process) for row in RETAINED_UNCONFIRMED)
        print(json.dumps({'format': 'has_pmx_CPU_observation_unconfirmed_closure_failure_1' if unresolved else 'has_pmx_CPU_observation_public_refusal_1',
                          'completed': False, 'error_type': type(error).__name__,
                          'Root_ownership_intervention_required': unresolved, 'lane_closed': False,
                          'native_protocol_qualified': False}))
        return 1


if __name__ == '__main__': raise SystemExit(main())
