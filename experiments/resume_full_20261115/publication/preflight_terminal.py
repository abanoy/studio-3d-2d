"""Independent terminal metadata admission; read only, never a runtime/receipt audit."""
from pathlib import Path
import argparse
import json
import re
import publication_gates as Gates

BASE = Path(__file__).resolve().parent
CONTEXT = Gates.load(BASE / 'RUN_EXPECTATIONS.json')
ROOT = Path(CONTEXT['workspace_root'])
RUN = ROOT / 'output' / CONTEXT['run_name']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal-permission', action='store_true', required=True)
    parser.add_argument('--host-proof-sha256', required=True)
    parser.add_argument('--host-raw-sha256', required=True)
    args = parser.parse_args()
    Gates.require(all(re.fullmatch('[0-9a-f]{64}', value) for value in [args.host_proof_sha256, args.host_raw_sha256]), 'Explicit fresh host hashes required')
    # First run metadata gate: never inspect final reports for running/failed jobs.
    state = Gates.load(RUN / 'state.json')
    Gates.require(state['status'] == 'passed' and state['suite_exit'] == 0 and state['source_unchanged'] is True
                  and state['source_commit'] == CONTEXT['source_commit'] and state['pid'] == CONTEXT['coordinator_pid']
                  and state['process_started'] == CONTEXT['coordinator_creation_utc'], 'Exact terminal PASS required')
    Gates.require(Gates.sha(Gates.read(RUN / 'authoritative-host-termination.json')) == args.host_proof_sha256
                  and Gates.sha(Gates.read(RUN / 'authoritative-host-terminal.json')) == args.host_raw_sha256,
                  'Authoritative host bytes differ')
    host = Gates.load(RUN / 'authoritative-host-termination.json')
    Gates.require(host['canonical_run'] == RUN.name and host['source_commit'] == CONTEXT['source_commit']
                  and host['coordinator_pid'] == CONTEXT['coordinator_pid'] and host['python_pid'] == CONTEXT['python_pid']
                  and host['expected_creation_utc'] == CONTEXT['coordinator_creation_utc']
                  and host['expected_python_creation_utc'] == CONTEXT['python_creation_utc']
                  and host['coordinator_absent'] is True and host['python_absent'] is True
                  and host['owned_runtime_command_matches_absent'] is True and host['no_process_killed'] is True
                  and host['coordinator_matches'] == [] and host['owned_runtime_matches'] == [], 'Flat host closure differs')
    Gates.validate_raw_host(RUN, CONTEXT, state, host)
    before = Gates.load(RUN / 'source-before.json')
    Gates.require(before == Gates.load(RUN / 'source-after.json') and len(before['source_sha256']) == 1008
                  and before['commit'] == CONTEXT['source_commit']
                  and Gates.sha(Gates.read(RUN / 'source-before.json')) == CONTEXT['source_before_sha256']
                  and Gates.sha(Gates.read(RUN / 'launch.json')) == CONTEXT['launch_sha256'], 'Frozen source/launch differs')
    expected = Gates.registry(BASE, CONTEXT)
    Gates.require(before['source_sha256'][expected['verifier_relative_path']] == expected['verifier_sha256'], 'Registry verifier pin differs')
    report = ROOT / 'output/verification.json'
    Gates.require(Gates.utc_ns(state['started_utc']) <= report.stat().st_mtime_ns <= Gates.utc_ns(state['finished_utc']), 'Full verification is stale')
    result_raw = Gates.read(report)
    result = json.loads(result_raw)
    Gates.validate_result(result, CONTEXT, expected)
    log = Gates.read(RUN / 'canonical.log').decode('utf-8-sig').replace('\r\n', '\n').rstrip()
    normalized = result_raw.decode('utf-8-sig').replace('\r\n', '\n').rstrip()
    Gates.require(log.endswith(normalized), 'Fresh canonical log/report suffix differs')
    prefix = log[:-len(normalized)]
    Gates.require(all(line.startswith('PASS ') for line in prefix.splitlines() if line.strip()), 'Unexpected canonical log prefix')
    scoped = Gates.validate_scoped(ROOT, CONTEXT, before)
    print(json.dumps({'format': 'has_canonical_bone_binding_terminal_preflight_1', 'passed': True,
                      'source_commit': CONTEXT['source_commit'], 'functional_sources': 1008,
                      'named_result_keys': len(result), 'named_core_groups': 36, 'named_root_movies': 21,
                      'foundation': 167, 'separate_python_crosswalk': 77, 'separate_headless': 96,
                      'actual_editor_audio_driver': result['editor_audio']['audio_driver'],
                      'silent_selection_driver': result['contact_selection']['audio_driver'],
                      'scoped_native_packet': scoped, 'receipt_audit_still_required': True,
                      'publication_created': False, 'process_or_runtime_queries': False}))


if __name__ == '__main__':
    main()
