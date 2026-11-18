"""Record the actual review copy and two incomplete cold attempts, without promoting them."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PACKET = 'experiments/neon_owner_973039e_closed_attempts_projection_20261118'
MARKER = '## 2026-11-17 — Neon merged; review copy built; cold runner incomplete'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projection-index-sha256', required=True)
    args = parser.parse_args()
    index = ROOT / PACKET / 'INDEX.json'
    assert hashlib.sha256(index.read_bytes()).hexdigest() == args.projection_index_sha256
    record = {
        'format': 'has_neon_owner_copy_and_incomplete_cold_summary_1',
        'qualified_merge_commit': 'c4126dec6083e52fb856e5cad5442227133b3c05',
        'review_source_checkpoint': '973039e40622ac20600e6d297d712de419877eda',
        'prior_checkpoint_independently_read_back_files': 179,
        'prior_COMPLETE_sha256': 'bf2400bc8b230d1cf785a8bbb5a619b86703fe216b5487f892f8e698cfe3750c',
        'projection_INDEX': PACKET + '/INDEX.json',
        'projection_INDEX_sha256': args.projection_index_sha256,
        'copy': {
            'status': 'PASSED',
            'directory': 'HAS-Review-Neon-973039e-native',
            'source_files': 10819, 'functional_files': 1029,
            'native_files': 495, 'native_bytes': 451266730,
            'private_BUILD_sha256': '23131d6ef73cc57146b514436755cdfb62447ccc02bfecb944c7389b91981c9e',
            'original_inputs_tools_and_prior_reviews_preserved_at_copy': True,
        },
        'cold_attempts': [],
        'archive_between_attempts': {
            'status': 'PASSED', 'generated_files': 10, 'logical_bytes': 215197,
            'file_identities_preserved': True,
            'source_absent_immediately_after_move': True,
            'script_sha256': '5d2728da62f30b58d4bc6f1a86b0d92ab10dae93d78c7286b68f0f4939f7169d',
            'plan_sha256': 'dd861256a348a2fd79b0c42d63ad1ad477771256650e1d2beb0377ca00469724',
        },
        'current_review_generated_output': {'files': 10, 'retained_private': True, 'godot_cache_present': False},
        'overall_cold_validation': 'INCOMPLETE_NOT_PASS',
        'external_interruption_cause': 'UNOBSERVED',
        'third_cold_attempt_launched': False,
        'native_normal_fidelity': 'FAILED_UNQUALIFIED',
        'human_acceptance': 'DEFERRED',
        'raw_BUILD_runtime_reports_receipts_native_arrays_logs_and_media_included': False,
        'cleanup_performed': False,
    }
    for name, audit in (
        ('attempt1', 'ac5130c09499d7cb55b7e4e40c9a8779d6ab0f2d8760b3e7cd66a6efa24d6123'),
        ('attempt2', '5d55335d4f23354e067f501194da54af4daa2518008b73a15aec911842c22178'),
    ):
        record['cold_attempts'].append({
            'name': name, 'status': 'INCOMPLETE_NOT_PASS', 'cases': 4,
            'observed_checks': 187, 'all_four_case_processes_exit0_reaped_not_timed_out': True,
            'all_four_physical_private_jobs_and_desktops_closed': True,
            'foreground_or_desktop_switch_observed': False,
            'coordinator_terminal_receipt_present': False, 'final_verification_present': False,
            'original_after_scope_report_present': False,
            'independent_recovery_scope_counts': {'owned': 0, 'main': 0, 'neon': 0},
            'private_recovery_audit_sha256': audit,
        })
    entry = f'''
{MARKER}

Neon Pro is merged in c4126dec, followed by source checkpoint 973039e. The
complete Windows run remains PASSED: 158 groups, 36 core groups, 21 movies,
native MMD pose 45, Neon 12504, camera 60 and color 44. The 179-file remote
readback of 973039e passed; its COMPLETE proof is bf2400bc. The earlier
157-group run remains unqualified. These observations have separate scopes.

The compatible admission core f8da restores the required payloads INDEX API;
the original core code and all thirteen predecessor payloads are byte-identical.
The earlier KeyError refusal is preserved. The final compatible activation
built HAS-Review-Neon-973039e-native successfully: 10,819 source files, including
1,029 tested functional files, and 495 native files. The private BUILD report
has SHA256 23131d6e. Inputs, installed tools and four prior reviews were preserved
at copy completion. The installed Studio was not replaced.

Both subsequent cold attempts are INCOMPLETE_NOT_PASS. In each, all four cases
recorded 44 + 46 + 56 + 41 = 187 passed checks. Independent audits confirmed four
exit-zero, reaped, non-timed-out private launchers with closed jobs and desktops,
and no foreground or desktop switch. Neither attempt saved its coordinator's
terminal receipt, final verification report or original after-scope report.
Recovery observers later found zero owned/Main/Neon processes. The second recorded
PID had been reused by an unrelated system process and was left untouched.
The external interruption cause is unobserved; do not claim compaction caused it.
Case passes and later recovery closure do not replace missing final preservation
and retained-coordinator completion. No third cold attempt was launched.

Between attempts, an independently reviewed, exact move preserved ten generated
Studio/output files (215,197 bytes) in a private archive. The unchanged validator
requires that output to be empty. The ten files generated by attempt two remain
private in the new review copy; .godot is absent. Preserve both attempts, their
receipts, this archive and the review deliverable. Raw BUILD/runtime reports,
native data, logs and media stay local. Public source, scalars and proof hashes:
{PACKET}/RESULT.json (INDEX {args.projection_index_sha256}).

Next: investigate the lost runner lifetime before another cold attempt. Reuse
the unchanged validator or review a concrete correction; preserve all assertions.
Any retry needs fresh destinations and provenance-preserved generated output,
or a fresh copy. A manual owner exercise is deferred and must not block other
Source work. Continue the read-only B metadata classifier: identify unused Viewer
image ownership/reachability and the unclassified reference's owning datablock,
type and path. Preserve all six refusal rows; do not infer a brush role from a
filename. A native B rerun needs the tested-1029 context successor, not the old
52f guard. Keep the strict native-normal tolerance and failed observations.
PMX reconstruction, solver integration, six-foot normalization, lighting and
Discovery remain separate unfinished work. Formal implementation 52/54 and
acceptance 55/62 remain unchanged. No tool installation or cleanup occurred.
'''
    for name in ('LLM.md', 'docs/progress_memo.md', 'docs/RESUME_MASTER_PLAN.md'):
        path = ROOT / name
        raw = path.read_bytes()
        assert MARKER.encode() not in raw, name
        newline = '\r\n' if raw.count(b'\n') == raw.count(b'\r\n') else '\n'
        with path.open('ab') as stream:
            stream.write(entry.replace('\n', newline).encode())
    path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
    benchmark = json.loads(path.read_bytes())
    assert 'owner_copy_and_incomplete_cold_20261117' not in benchmark
    benchmark['owner_copy_and_incomplete_cold_20261117'] = record
    path.write_text(json.dumps(benchmark, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    path = ROOT / 'docs/completion_checklist.json'
    ledger = json.loads(path.read_bytes())
    statuses = lambda value: [(r['id'], r['implementation'], r['verification'], r['acceptance_status']) for r in value['requirements']]
    before = statuses(ledger)
    ledger['next_actions'][0]['action'] = (
        'Neon merged after complete Windows158/core36/movie21 PASS; 973039e independently read back179 files. '
        'Owner copy passed with10819 source/495 native files. Two cold attempts each passed187 checks '
        'and four physical private closures but are INCOMPLETE_NOT_PASS: coordinator terminal, final report '
        'and original final scope/preservation are missing. Recovery scopes zero; preserve both attempts '
        'and generated output. Diagnose runner lifetime before a third attempt. Continue independent B '
        'resource ownership/reachability classification with a tested1029 context successor; preserve all '
        'normal-fidelity failures. Human review deferred; formal statuses unchanged.')
    next(r for r in ledger['requirements'] if r['id'] == 'UI-01')['evidence'].append({
        'kind': 'recorded_report', 'path': PACKET + '/RESULT.json',
        'scope': 'Actual qualified Neon merge and owner copy PASS. Each of two cold attempts records187 checks and4 private physical closures, but missing coordinator/final preservation reports make both overall INCOMPLETE_NOT_PASS. Recovery scopes zero; no human acceptance claimed.'})
    old = "Current owner-requested Neon Pro branch must pass its independent Windows review before merge; human review remains deferred."
    affected = [r for r in ledger['requirements'] if old in r.get('remaining', '')]
    assert len(affected) == 1
    affected[0]['remaining'] = affected[0]['remaining'].replace(old,
        'Neon Pro merged after its complete Windows PASS; the owner copy passed. Both final cold attempts remain incomplete despite187 case checks each; human review remains deferred.')
    assert statuses(ledger) == before
    path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print('Recorded copy PASS and both incomplete cold attempts; requirement statuses unchanged.')


if __name__ == '__main__':
    main()
