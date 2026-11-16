"""Record the completed scoped repair; full retry is still required."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
RUN='output/runtime-snapshot-scope-20261116T030539570843'
def pin(name):return {'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}
def load(name):return json.loads((ROOT/name).read_bytes())
v=load(RUN+'/verification.json')
assert v['passed'] and v['checks_observed']==28 and v['failures_observed']==0 and v['snapshot_files']==1024
assert v['source_and_runtime_preserved'] and v['runtime_lease_released'] and len(v['receipts'])==2
release='output/windows-canonical-bone-binding-20261116T022132132/graphics-lease-closed-after-failure.json'
r=load(release);assert r['released'] and not r['full_suite_passed'] and r['observed_partial_private_jobs']==46
record={'format':'has_world_selection_runtime_snapshot_repair_1','status':'PASSED_SCOPED_REPAIR_FULL_RETRY_REQUIRED',
        'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'draft_index':pin('experiments/world_selection_runtime_snapshot_v2_20261115/INDEX.json'),
        'application':pin('output/runtime-snapshot-v2-applied.json'),
        'actual_replay':pin(RUN+'/verification.json'),'actual_process':pin(RUN+'/process.json'),
        'source_before':pin(RUN+'/source-before.json'),'source_after':pin(RUN+'/source-after.json'),
        'actual_runtime_closure':pin(RUN+'/after-runtime-closure.json'),'failed_full_release':pin(release),
        'CPU':{'checks':27,'exit':0,'seconds':4.146,'evidence_basis':'Root exec_command completed tests/test_owner_review_snapshot.py; original7 real-Git fixtures plus20 runtime-scope mock cases.',
               'expected_negative_diagnostic':'fatal: Needed a single revision is the intentional bad-revision case; suite ended OK.',
               'test_source':pin('tests/test_owner_review_snapshot.py'),'builder_source':pin('tools/build_owner_review_snapshot.py')},
        'actual_UI_checks':28,'actual_UI_failures':0,'actual_private_jobs':2,'closed_private_jobs':2,
        'elapsed_seconds':v['process']['seconds'],'outer_timeout_seconds':180,'startup_timeout_seconds':60,'teardown_timeout_seconds':110,
        'snapshot_files':1024,'original_failed_archive_snapshot_files':6023,
        'scope':'Opt-in exact runtime trees, entrypoints, optional dependency config/notices and catalogue-bound transitive quoted res resources. Validate all candidate names/collisions before reads; resolve only retained destinations.',
        'default_owner_archive_and_exact_revision_behavior_preserved':True,'teardown_GDScript_and_all28_assertions_unchanged':True,
        'full_default_passed':False,'manual_hair_check':'OWNER_DEFERRED_NO_RESULT','formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED'}
target=ROOT/'docs/benchmarks/world_selection_runtime_snapshot_2026-11-15.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
old_path=ROOT/'docs/benchmarks/windows_native_leaf_full_timeout_2026-11-15.json'
old=json.loads(old_path.read_bytes());old['graphics_lease_release']={'status':'CLOSED_FAILED_PARTIAL_RUN','proof':pin(release),'private_jobs':46,'all_closed':True}
old['scoped_repair']=pin('docs/benchmarks/world_selection_runtime_snapshot_2026-11-15.json')
old_path.write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
entry='''

## 2026-11-15 — Bounded runtime snapshot fixes the shutdown-test timeout

After actualfailed-runleaseclosure, applied the reviewed v2 opt-in snapshot
change to tools/build_owner_review_snapshot.py and its teardown driver. Default
owner archives and explicit old-revision byte behavior remain unchanged.
All candidate Windows names/collisions are checked before any source read;
only retained runtime destinations incur filesystem resolution. Runtime keeps
the five functional trees/four entrypoints, optional dependencies/notices and
exact catalogue-bound quoted-resource closure. Output/cache/private and
unreferenced research evidence stay outside this automated snapshot.

All27CPU tests pass(original7 real-Git cases plus20 mocked runtime cases).
The intentional bad-revision diagnostic is expected; suiteexit0/OK in4.146s.
Fresh actual scoped shutdown replay passes the SAME28checks/all4cases in
21.763778seconds under the unchanged180second outer limit(60startup/110test).
Snapshot contains1024files instead of6023. Both actual private jobs exit0,
closejob/desktop, never foreground; source/runtime preservation and root fresh
owned-command absence pass. No wrapper termination or timeout occurred.
Source: output/runtime-snapshot-scope-20261116T030539570843. Benchmark:
docs/benchmarks/world_selection_runtime_snapshot_2026-11-15.json.

The first source-application helper refused before any write because it treated
the packet's dictionary index as a list; corrected to its exact dictionary
schema, then applied only the three reviewed bytes/hash targets. That setup
error is separate from the earlier actual full timeout. Old source drafts and
first mocked CRLF-preparation failures remain preserved. No runtime assertion,
timeout, path guard or full verification scope is relaxed. The original dbf
full remains FAILED; commit/retry a fresh complete default next. No human
result or broad Source/artist acceptance is inferred;55/62and52/54stay unchanged.
'''
for name in ['LLM.md','docs/progress_memo.md']:
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(entry)
print(json.dumps({'benchmark':pin('docs/benchmarks/world_selection_runtime_snapshot_2026-11-15.json'),'scoped_passed':True,'full_passed':False}))
