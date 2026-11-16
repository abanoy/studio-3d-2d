"""Preserve the actual full failure; late successful child is not a full PASS."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'output/windows-canonical-bone-binding-20261116T022132132'
CASE=ROOT/'output/world-selection-teardown/1794796856711017300'
def load(p):return json.loads(p.read_bytes())
def pin(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

state=load(RUN/'state.json'); proof=load(CASE/'provenance.json'); actual=load(CASE/'result.json')
assert state['status']=='failed' and state['suite_exit']==1 and state['source_unchanged'] is True
assert actual['checks']==28 and actual['failures']==0 and len(actual['cases'])==4
before=load(RUN/'source-before.json');after=load(RUN/'source-after.json')
assert before==after and len(before['source_sha256'])==1014
commands={phase:load(CASE/(phase+'-command.json')) for phase in ['normal-startup','process']}
receipts={}
for phase,command in commands.items():
    path=Path(command[command.index('--receipt')+1]).resolve()
    assert path.is_relative_to(CASE.resolve())
    receipt=load(path)
    assert receipt['exit']==0 and receipt['job_closed'] is True and receipt['desktop_closed'] is True
    assert receipt['child_desktop_confirmed'] is True and receipt['foreground_child_observed'] is False
    receipts[phase]={'file':pin(path),'seconds':receipt['seconds'],'child_pid':receipt['child_pid'],
                     'job_closed':True,'desktop_closed':True,'exit':0,'mtime_utc':datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat()}
files=proof['source_sha256']
record={'format':'has_windows_native_leaf_full_timeout_1','status':'FAILED_OUTER_180_SECOND_TIMEOUT',
        'source_commit':state['source_commit'],'state':pin(RUN/'state.json'),'source_before':pin(RUN/'source-before.json'),
        'source_after':pin(RUN/'source-after.json'),'canonical_log':pin(RUN/'canonical.log'),
        'host_closure':pin(RUN/'authoritative-host-termination.json'),
        'elapsed_seconds':(datetime.datetime.fromisoformat(state['finished_utc'])-datetime.datetime.fromisoformat(state['started_utc'])).total_seconds(),
        'core_groups_passed':36,'current_complete_default_passed':False,'functional_source_files':1014,'functional_source_and_HEAD_unchanged':True,
        'failed_command':'tests/verify_world_selection_teardown.py','outer_timeout_seconds':180,'inner_startup_timeout_seconds':60,'inner_teardown_timeout_seconds':110,
        'actual_late_teardown_result':pin(CASE/'result.json'),'actual_late_checks':28,'actual_late_failures':0,'private_receipts':receipts,
        'snapshot_domain':{'files':len(files),'experiment_files':sum(p.startswith('experiments/') for p in files),'docs_files':sum(p.startswith('docs/') for p in files)},
        'observed_timing':'About70 seconds freezing archive,11 seconds successful startup,97 seconds rehashing/provenance; outer deadline then killed wrapper about4 seconds into an11.324-second successful private teardown child.',
        'failure_classification':'Snapshot/hash workload exhausts aggregate wrapper budget; no failing selection/teardown assertion or native-motion regression demonstrated.',
        'process_termination_scope':{'root_host_observation_helper_issued_no_termination':True,
              'outer_subprocess_run_timeout_terminates_its_owned_wrapper':'Inferred from exact traceback and local stdlib implementation; wrapper PID not separately captured',
              'late_private_Godot_child_completed_normally':True,'global_no_process_termination_claimed':False},
        'graphics_lease_release':'PENDING_FRESH_FAILED_RUN_CLOSED_RECEIPT_AUDIT',
        'next_fix':'Opt-in functional runtime snapshot only for automated teardown; preserve owner archive default, actual28 checks and timeouts. Then scoped retry and fresh complete default.',
        'manual_hair_click_check':'OWNER_DEFERRED_BUSY_CONTINUE_INDEPENDENTLY_NO_RESULT',
        'formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED'}
target=ROOT/'docs/benchmarks/windows_native_leaf_full_timeout_2026-11-15.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
entry='''

## 2026-11-15 — Full dbf retry failed on archive snapshot overhead

Committed/pushed dbf0bc1145f74b5bbff814ec6a417ccd23ce0885 contains the bounded
native8 increment and its separately scoped96UI/180state/21087experimental
pair evidence. GitHub ownership and explicit goal upload authorization were
verified after the first automatic review rejection; the same non-force push
then succeeded. Remote commit205-file list and two critical blobs match; full
205-file readback is still partial(42verified), so do not claim it complete or
use it as blanket cleanup authority.

Fresh complete default output/windows-canonical-bone-binding-20261116T022132132
FAILED after1346.822071seconds on verify_world_selection_teardown.py's outer
180second timeout. All36coregroups passed;1014functional hashes andHEAD remain
exact. The actual private shutdown child subsequently passes28checks/all4cases,
exit0, job/desktopclosed in11.324seconds. Its receipt is later than the failed
full terminal timestamp and does not turn the full run into a PASS. Default
output/verification.json remains old evidence and must not be substituted.

Stage timing shows about70seconds copying6023snapshotfiles(4551experiments,
436docs),11seconds normal startup, then97seconds rehashing/archive provenance.
The outer deadline expired about4seconds into a healthy11-second test child.
Root host observations at02:47:42.3887530Z confirm exact coordinator87384/
Python86984 absent, no owned native commands, current1014source/HEADexact.
The host observer issued no process termination; Python's outer timeout branch
automatically terminates its owned wrapper by stdlib policy(source/trace
inference), so no global "no process killed" claim is made. Preserve raw proofs.

Next: close/audit all failed-run private helpers/receipts, then implement an
opt-in functional-runtime snapshot for this automated teardown only. Keep the
owner builder's archive default, old revision behavior, timeout and28assertions.
Run a fresh scoped replay and complete default; do not weaken gates or relabel
this failure. Benchmark: docs/benchmarks/windows_native_leaf_full_timeout_2026-11-15.json.

Owner withdrew the volunteered hair-click exercise because busy and explicitly
asked continued independent work. Record DEFERRED/no human result; ask no new
manual questions. Existing f0dd57a review remains separate and unchanged.
Native five-rule/deeper-chain and six-foot import work are experiment drafts,
not current production or qualification. Formal55/62and52/54 remain unchanged.
'''
for name in ['LLM.md','docs/progress_memo.md']:
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(entry)
print(json.dumps({'recorded':pin(target),'snapshot_files':len(files),'full_passed':False}))
