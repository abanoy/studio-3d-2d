"""Dated running observation; no terminal or whole-product success inference."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-fe9aace-20261117T040348'
PACKET = ROOT / 'experiments/neon_windows_fe9aace_20261117'
load = lambda p: json.loads(p.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
initial = (RUN / 'state.json').read_bytes()
state = json.loads(initial)
assert state['status'] == 'running' and state['source_commit'] == 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
before = load(RUN / 'source-before.json')['source_sha256']
assert len(before) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before.items())
focused = load(REVIEW / 'output/neon-foundation-fe9aace-20261117-attempt1/verification.json')
assert focused['passed'] is True and focused['all_functional_source_unchanged'] is True and focused['host_scopes_closed'] is True
snapshot = PACKET / 'active-observation'
snapshot.mkdir(exist_ok=False)
files = []
for name in ('launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'source-before.json', 'preflight-source.json', 'state.json', 'canonical.log'):
    raw = initial if name == 'state.json' else (RUN / name).read_bytes()
    (snapshot / name).write_bytes(raw)
    files.append({'path': name, 'source_path': str(RUN / name), 'bytes': len(raw), 'sha256': sha(raw), 'snapshot_only': name in ('state.json', 'canonical.log')})
assert load(RUN / 'state.json') == state, 'Terminal changed during active snapshot; do not publish as still-running'
now = datetime.now(timezone.utc).isoformat()
record = {'format': 'has_root_neon_fe9_active_observation_1', 'observed_utc': now, 'state': state, 'files': files,
    'functional_sources_unchanged': 1029, 'focused_foundation_passed': 167, 'separate_crosswalk': 77, 'separate_bindings_headless': 96,
    'expected_not_pass': {'groups': 158, 'core': 36, 'movies': 21}, 'full_result': 'RUNNING_NO_RESULT', 'main_merged': False,
    'review_branch_fe9_upload': 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION', 'main_fe9_reconstruction_publication': 'PENDING',
    'old_public_cache_cleanup_attempt1': 'PREFLIGHT_REFUSAL_ZERO_DELETIONS'}
(snapshot / 'OBSERVATION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
current = f'''CURRENT at {now}:fe9aace complete Windows run is RUNNING, not PASS.
Run output/windows-neon-fe9aace-20261117T040348 started04:04:17.6888552Z.
Coordinator19668 GetProcessbirth04:04:17.2421226Z; Python28396
GetProcessbirth04:04:18.1277602Z,parent19668; CIMrounded.1277600 is metadata only.
Freeze REVIEW1029 functional files and HEADfe9aace; root owns native lane, no
other engine/native launch. Fe9 terminal context is prepared; independently
observe terminal before its reviewed root-only helper. Derive actual ownership/
source/inline/birth/private closure; expected158/36/21 are not PASS totals.

Fixture-only fe9 successor is committed locally: one expression removes CR+LF,
golden bytes/hash and all79+17/wrappers/thresholds unchanged. Actual focused
foundation167+separatecrosswalk77/headless96 PASS12.0645659s, source1029 same,
scopezero/privateUIclosed. Source10+independent10CPU pass; scan found only this
matching multiline golden. New text reconstruction INDEX156772da is prepared,
parent375 already recoverable from verified mainE8; fe9 upload to review branch
was NOT attempted after prior rejection. Publish its source/evidence in main
without merging product. Initial runtime preparation refused a transient ffprobe
stamp; field/cause UNKNOWN, later four stamps/approvedSHA exact, unchanged strict
retry6runtimes+574SourceIOoriginal/copy+120exporter+36fixtures PASS. No guard relaxed.

Cleanup attempt1 stopped in preflight,0Remove calls/0deleted/uncertainfalse,
because a PowerShell async Git helper emitted VoidTaskResult into its byte return.
Old plan/script/result stay immutable; a one-expression source-onlyV2 is being
prepared with an actual readonlyGit probe before freshattempt2. Only71 old public
download caches are eligible; no native/private/current-output/tool/review paths.

'''
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
plan = path.read_text(encoding='utf-8')
anchor = 'Review checkout: C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.\n'
assert plan.count(anchor) == 1
plan = plan.replace(anchor, anchor + '\n' + current, 1)
plan = plan.replace('Latest frozen candidate375ec05', 'Preceding frozen candidate375ec05', 1)
plan = plan.replace('Native lane currently free/root-only.', 'That lane was released; currentfe9 lane is active/root-only.', 1)
plan = plan.replace('NEXT: review the minimal fixture-only CR+LF decoding proposal in', 'Completed source/focused successor (see currentfe9 above): minimal fixture-only CR+LF proposal in', 1)
path.write_text(plan, encoding='utf-8', newline='\n')
paragraph = f'''\n### November17 2026 —fe9 focused Source pass and active full\n\nAt {now}, fe9aace full is RUNNING from04:04:17.6888552Z; root native lane
exclusive, source1029 and HEAD frozen. Coordinator19668 birth04:04:17.2421226Z,
Python28396 birth04:04:18.1277602Z,parent19668 (GetProcess100ns; CIMrounded notID).
The fixture-only CR+LF fix passes actual Foundation167/separate77+96 in12.0645659s,
golden9360bytes/79+17 and wrappers unchanged, sources same/scopes zero. New fe9
text reconstruction is prepared; parent375 is backed by verified mainE8. Review
branchfe9 was not uploaded after prior rejection, product remains unmerged.
Firststrictffprobe preparation refusal had unknown changedfield; later stamps/
SHA exact and exactstrictretry all6+694+36 passes. No guard relaxed. Cleanup
attempt1 refusedbefore0deletions due asyncGit byte-return contamination; immutable
failedresult retained, sourceV2+readonlyprobe pending. ManualDEFERRED;55/62 and
52/54 unchanged. Full expected158/36/21 counts are not successful results.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['preceding_375_terminal'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Monitoractivefe9 full/frozen1029source; fixture-onlyCRLFfix passes actualFoundation167/separate77+96. '
    'Root freshterminal/source/birth/ownership audit beforemerge. Sourcebackup viaexplicitmaincheckpoint; cleanupV2mustpassreadonlyGit probe, previousattempt0deletions. '
    'Native normals/PMX/scale scoped/inactive, manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'observed_utc': now, 'full': 'RUNNING_NO_RESULT', 'source_files': 1029, 'foundation': 167, 'separate_crosswalk': 77, 'separate_headless': 96}))
