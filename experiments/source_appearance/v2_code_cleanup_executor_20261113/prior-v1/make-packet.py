"""Index this owned preparation output only. Does not touch source, Git or cleanup roots."""
from pathlib import Path
import hashlib, json

HOME = Path(__file__).absolute().parent
EXPECTED = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\sfm-v2-code-cleanup-executor-20261113')
assert HOME == EXPECTED

def identity(path):
    raw = path.read_bytes()
    return {'path':path.relative_to(HOME).as_posix(), 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}

def read(path):
    return json.loads(path.read_bytes())

def main():
    runtime_files = []
    for runtime in (Path(r'C:\Program Files\Python313\python.exe'),
                    Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'),
                    Path(r'C:\Program Files\Git\cmd\git.exe')):
        raw = runtime.read_bytes()
        runtime_files.append({'path':str(runtime),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    receipts = []
    for path in sorted(HOME.glob('receipt-*.json')):
        value = read(path)
        receipts.append(identity(path) | {key:value.get(key) for key in (
            'status','mode','executor_sha256','helper_sha256','started_utc','finished_utc',
            'candidate_files_checked','retained_files_checked','file_preflight_passed',
            'preflight_membership_passed','retained_recheck_passed','post_membership_passed',
            'publication_status','deletion_invoked','deleted_files','deleted_bytes','errors','unrun')}
            | {'process_audit_count':value.get('process_audit_count',0),
               'last_process_matches':len((value.get('last_process_check') or {}).get('matching_processes',[])),
               'last_process_unknowns':len((value.get('last_process_check') or {}).get('unknown_live_owned_or_runtime_processes',[]))})
    controls = []
    for path in sorted(HOME.glob('synthetic-*/TESTS.json')):
        value = read(path)
        controls.append(identity(path) | {key:value.get(key) for key in ('passed','tests','executor_sha256','test_source_sha256','production_execute_invoked')})
    audits = []
    for path in sorted(HOME.glob('nonuse-host-*.json')):
        value = read(path)
        audits.append(identity(path) | {'utc':value['utc'], 'processes':value['processes_in_snapshot'],
            'matches':len(value['matching_processes']), 'unknowns':len(value['unknown_live_owned_or_runtime_processes']),
            'inaccessible':len(value['inaccessible_processes']), 'exceptions_used':value['stale_pid_exceptions_used']})
    result = {
        'format':'has_sfm_v2_cleanup_executor_preparation_results_1',
        'status':'PREPARATION_ONLY_EXECUTE_UNRUN_NO_CLEANUP',
        'deletes_moves_kills_or_git_mutation':False,
        'frozen_plan':{'packet_sha256':'847609fa241f70f89c711a93ed0035a8a1fe69cf34bd998b9d418630db1cb70a',
            'gzip_sha256':'c772ec391c36db95b8a016125e41bc1588cdbc14ae542d6a64e66d66136f55a4',
            'raw_sha256':'e65b408acdf63eade874709b6dc37de43b6c244ff3f9fe5fc11cab222c43fa8a',
            'raw_bytes':7532146,'candidate_files':4308,'candidate_bytes':33607832,'retained_files':2613,'retained_bytes':68376831},
        'current_executor':identity(HOME/'execute-sfm-v2-cleanup.ps1'),
        'current_git_helper':identity(HOME/'verify-git.py'),
        'runtime_executable_files':runtime_files,
        'runtime_hash_limit':'Executable files only; no complete installed dependency-tree hash is asserted.',
        'local_git_proof':read(HOME/'git-local-proof-final.json'),
        'synthetic_controls':controls,
        'real_dry_run_receipts_local_only':receipts,
        'supplemental_process_audits_local_only':audits,
        'preserved_preparation_failures':[
            {'case':'first full dry-run', 'outcome':'FAILED_NO_DELETION_AFTER11_CANDIDATES',
             'reason':'Native file-ID reader lacked extended literal-path prefix for long Windows paths.',
             'exact_source':identity(HOME/'failed-long-path-first-dry-run/execute-sfm-v2-cleanup.ps1')},
            {'case':'first supplemental host process audit','outcome':'FAILED_BEFORE_REPORT_NO_DELETION',
             'reason':'PowerShell automatic $Matches variable replaced the audit list during regex matching. Corrected to usageMatches.',
             'exact_source':identity(HOME/'failed-process-automatic-variable/execute-sfm-v2-cleanup.ps1')},
            {'case':'restricted process inspection','outcome':'ACCESS_DENIED_NO_DELETION',
             'reason':'Get-CimInstance unavailable in restricted context. Approved host audit used instead; full restricted dry-run receipt retained.'},
            {'case':'prior Get-Process creation acquisition','outcome':'STRICT_NONUSE_GATE_REFUSED13_UNKNOWN',
             'reason':'Native retained-handle owner/creation now replaces nullable Get-Process.StartTime. Access-limited records remain blockers.',
             'exact_source':identity(HOME/'prior-getprocess-identity/execute-sfm-v2-cleanup.ps1')},
        ],
        'unrun':[
            'No Execute invocation, deletion, move, process termination or post-deletion proof.',
            'Published exact checkpoint/artifact and actual remote ancestry gates until root supplies reviewed publication values.',
            'No root-reviewed inaccessible-process exception mechanism is included or implicitly authorized.',
        ],
        'limits':[
            'Fresh inaccessible owned/runtime identities refuse. Other-account/non-runtime and arbitrary handle access are explicitly limited.',
            'WMI has microsecond precision; native owner handle acquires full100ns creation, then native CWD reads require exact full creation.',
            'Directory IDs are initially pinned per invocation because the frozen plan did not record original directory IDs.',
            'Path-based rechecks/removal are not atomic against hostile concurrent changes.',
            'Full per-file process audits are intentionally expensive; no scope-broadening retry exists.',
            'Local full process-audit receipts and all authored synthetic fixture files remain retained outside the compact publication selection.',
        ],
    }
    (HOME/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    names = ['README.md','RESULTS.json','execute-sfm-v2-cleanup.ps1','verify-git.py','test-safety.ps1',
             'audit-processes-only.ps1','make-packet.py','git-local-proof-final.json',
             'failed-long-path-first-dry-run/execute-sfm-v2-cleanup.ps1',
             'failed-process-automatic-variable/execute-sfm-v2-cleanup.ps1',
             'prior-getprocess-identity/execute-sfm-v2-cleanup.ps1']
    latest = read(HOME/'synthetic-run-31-final.stdout.json')
    test_path = HOME/Path(latest['fixture_root']).relative_to(HOME)/'TESTS.json'
    names.append(test_path.relative_to(HOME).as_posix())
    files = [identity(HOME/name) for name in names]
    packet = {'format':'has_sfm_v2_cleanup_executor_packet_1','status':'PREPARATION_ONLY_EXECUTE_UNRUN_NO_CLEANUP',
              'files':files,'total_bytes':sum(x['bytes'] for x in files),
              'local_full_receipts_and_fixture_payloads_excluded_from_publication':True,
              'execute_invoked':False}
    (HOME/'PACKET.json').write_text(json.dumps(packet,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'packet':identity(HOME/'PACKET.json'),'files':len(files),'bytes':packet['total_bytes'],
                      'executor':result['current_executor'],'git_helper':result['current_git_helper']}))

if __name__ == '__main__':
    main()
