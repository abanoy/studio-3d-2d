"""Dated root observation of the next full, without a fabricated terminal result."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-375ec05-20261117T033037'
PACKET = ROOT / 'experiments/neon_windows_375ec05_20261117'
load = lambda p: json.loads(p.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
state = load(RUN / 'state.json')
assert state['status'] == 'running' and state['source_commit'] == '375ec05e925159850ff3b0abf2e8f98f9d2ce129'
source = load(RUN / 'source-before.json')['source_sha256']
assert len(source) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in source.items())
focused = load(REVIEW / 'output/neon-helper-375ec05-20261117-attempt1/verification.json')
assert focused['passed'] is True and focused['all_functional_source_unchanged'] is True and focused['host_scopes_closed'] is True
now = datetime.now(timezone.utc).isoformat()
snapshot = PACKET / 'active-observation'
snapshot.mkdir(exist_ok=False)
bindings = []
for name in ('launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'source-before.json', 'preflight-source.json', 'state.json', 'canonical.log'):
    raw = (RUN / name).read_bytes()
    (snapshot / name).write_bytes(raw)
    bindings.append({'path': name, 'source_path': str(RUN / name), 'bytes': len(raw), 'sha256': sha(raw), 'snapshot_only': name in ('state.json', 'canonical.log')})
record = {'format': 'has_root_neon_375_active_observation_1', 'observed_utc': now, 'state': state, 'files': bindings,
    'functional_sources_unchanged': 1029, 'helper_focused': {'cpu': 208, 'graphical': 266, 'passed': True},
    'expected_not_pass': {'groups': 158, 'core': 36, 'movies': 21}, 'full_result': 'RUNNING_NO_RESULT', 'main_merged': False,
    'review_branch_375_upload': 'AUTO_REVIEW_REJECTED_NOT_RETRIED', 'main_reconstruction_publication': 'PENDING'}
(snapshot / 'OBSERVATION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
current = f'''CURRENT RUN at {now}:375ec05 complete Windows verification is RUNNING,
not PASS. Run output/windows-neon-375ec05-20261117T033037 started03:31:04Z.
Coordinator3032 GetProcessbirth03:31:03.8129380Z; Python26304
GetProcessbirth03:31:04.3344666Z,parent3032. CIM's rounded.3344660 is not the
identity timestamp. Root owns the native lane; freeze REVIEW1029 functional files
and HEAD375ec05, no second native/engine launch. Context-only terminal helper is
being prepared; root must independently observe terminal before using it.
Expected158groups/36core/21movies are not observed successful totals.

The minimal helper-manifest successor is committed locally375ec05: only4hash
values in app/pose rows,25members/23otherrows/driver/assertions unchanged. Actual
focused original208CPU+266graphical PASS, source1029 same/no overlays, exact main
snapshot context, all native/coordinator+worker scope observations zero; private
graphical jobs closed. CPU41.7605826s/GPU102.8179396s. Read-only source18tamper
methods and independent18 pass. The review-branch upload was rejected by automatic
approval review and was not retried. The project explicitly requires main source/
evidence checkpoints; a complete375 reconstruction packet (three public text blobs,
patch, commit/tree/EOL recipe) is being published there without merging the product.
Do not claim375 is on the review remote until that is independently established.

'''
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
plan = path.read_text(encoding='utf-8')
assert 'LATEST FULL FAILED:' in plan
plan = plan.replace('LATEST FULL FAILED:', 'PRECEDING FULL FAILED:', 1)
plan = plan.replace('Current graphics lane is free.', 'That preceding lane was released; current375 lane is active.', 1)
plan = plan.replace('No redesign merge, installed replacement or owner observation has occurred.\n', 'No redesign merge, installed replacement or owner observation has occurred.\n\n' + current, 1)
path.write_text(plan, encoding='utf-8', newline='\n')
paragraph = f'''\n### November17 2026 —375 helper qualification and active full successor\n\nAt {now}, frozen375ec05 complete Windows run is active from03:31:04Z,
output/windows-neon-375ec05-20261117T033037. Coordinator3032 birth03:31:03.8129380Z,
Python26304 birth03:31:04.3344666Z,parent3032, exactGetProcess100ns. Source1029
unchanged. Only functional change from4ed is the reviewed helper manifest's four
app/pose hash strings;25members/23otherrows/driver/assertions unchanged. Actual
focused208CPU(41.7605826s)+266graphical(102.8179396s) pass on exact committed
snapshot with no overlay, sources unchanged and native/worker scopes zero/private
jobs closed. Branch upload375 was auto-review rejected and not retried. Explicit
goal main source/evidence checkpoint will carry a reconstructable text-only375
packet without product merge. No full PASS or cleanup claimed. Native normals,
PMX solver and six-foot activation remain unqualified/inactive. ManualDEFERRED,
55/62 and52/54 unchanged; current pickup records exact active lane.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['preceding_4ed_observation'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Monitor active375 complete Windows run, frozen1029source/HEAD; original helper208CPU/266GPU now pass, manifest-only4hash refresh. '
    'Root must audit fresh terminal groups/source/birth/actualprivatejobs beforemerge. Explicit main checkpoint carries reconstructable publictext375packet; '
    'reviewbranch375upload auto-review rejected/not retried. Native normals/PMX/scale remain scoped/inactive; manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'observed_utc': now, 'full': 'RUNNING_NO_RESULT', 'source_files': 1029, 'helper_cpu': 208, 'helper_graphical': 266}))
