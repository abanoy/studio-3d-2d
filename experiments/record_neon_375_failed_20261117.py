"""Truthful terminal pickup after the closed375 authored-fixture CRLF failure."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-375ec05-20261117T033037'
load = lambda p: json.loads(p.read_bytes())
state = load(RUN / 'state.json')
release = load(RUN / 'graphics-lease-closed.json')
assert state['status'] == 'failed' and state['source_unchanged'] is True and state['suite_exit'] == 1
assert release['released'] is True and release['physical_jobs'] == 51 and release['full_suite_passed'] is False
assert release['receipt_inventory_sha256'] == hashlib.sha256((RUN / 'terminal-audit-attempt1/receipt-inventory.json').read_bytes()).hexdigest() == '0bd04488ed3f67cb8cdfdac4952736c3c5008e3defe15bbbd531412f67b7f1bd'
remote = load(ROOT / 'experiments/neon_375_checkpoint_remote_20261117/COMPLETE_READBACK.json')
assert remote['commit'] == 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a' and remote['file_count'] == 534
plan = '''# HAS continuation — November 17, 2026

Continue independently without manual questions. Full owner scope/backlog:
[RESUME_MASTER_PLAN.md](RESUME_MASTER_PLAN.md). Later explicit resume overrides
historical pause notes. Do not ask for lost backups or owner checks while busy.

Main e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a is pushed; all534 public files
independently retrieved/exactGitblobs (5,857,844bytes,2working-EOL recipes).
Main functional1019 still equals qualified52f; redesign is UNMERGED. The optional
review-branch375 upload was auto-review rejected and NOT retried. Explicit goal
main source/evidence publication succeeded: main carries complete375 text-only
reconstruction from remote4ed (3blobs/patch/commit/tree/EOL recipes), independently
reconstructed exactly. Remote review branch remains4ed; Claude remainsc2d52ff.
Installed Studio, prior owner reviews, native originals and tools are preserved.

Review checkout: C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.
Latest frozen candidate375ec05e925159850ff3b0abf2e8f98f9d2ce129 full FAILED,
run output/windows-neon-375ec05-20261117T033037,03:31:04.1329319–03:50:19.3986079Z.
Source1029 unchanged. Core36,Neon12504,scene106+unit12830,helper208CPU/266GPU,
background snapshot/save/cancel/offline reads and middle-click/editing panels pass.
SourceChoice foundation then fails authored source_bone_bindings_unit.gd40/40:
the CRLF working fixture leaves103 carriage returns after its LF-only base64
strip. Canonical Git/main52 LF content is identical; CR+LF removal decodes exact
9360-byte goldenSHA39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1.
This is a synthetic test-data portability failure, not a native model result.
Foundation167 as a whole and subsequent helper17 within that failed96-wrapper
remain UNRUN; wrapper credited0checks, its failed script actually ran40.

Root closed/audited51physical jobs (50exit0+registeredKrita cancel2), all inline
joins exact, source/birth/scopes/private desktops closed; no private job failure
or fabricated headless desktop. Headless failingPID26908 exit1/no timeout.
Released03:51:37.9325174Z, inventory0bd04488ed3f67cb8cdfdac4952736c3c5008e3defe15bbbd531412f67b7f1bd.
Coordinator3032 birth03:31:03.8129380Z; Python26304 birth03:31:04.3344666Z,
parent3032 (GetProcess100ns; CIM.3344660 is notidentity). Root issued no termination.
The sealed375 terminal helper was already executed; do not reuse its context for
a successor. Native lane currently free/root-only. Closed failure archive
neon_failed_375_actual_packet_20261117 INDEX422d7311 preserves78exact originals.

NEXT: review the minimal fixture-only CR+LF decoding proposal in
experiments/neon_source_binding_b64_fixture_20261117. Preserve literal golden
bytes/constants, all79+17 assertions/wrapper/strict diagnostics/timeouts. Check
the full source scan for other LF-only embedded goldens. Commit a clean successor,
run actual SourceChoice foundation167 plus its separate77crosswalk/96headless
checks, then freeze/back up its text reconstruction and rerun all158 Windows
groups/36core/21movies. Expected counts are not a full PASS. No merge until a
fresh complete PASS and root source/receipt/birth/ownership terminal audit.

The preceding375 minimal helper-manifest fix changes4app/pose hash values only;
membership25/23otherrows/driver/assertions unchanged. Source18+independent18tamper
methods and actual208/266 focused/full profiles PASS. Scene106 preserves original
102checks/thresholds under the approved62percent mask, adds4independent forward
composites with fixed2/255 bound; product look/code unchanged. All previous failed
fulls(c2/381/f387/ffcf/4ed/375) remain distinct/preserved. Retracted teardown timing
and regex-overescape hypotheses stay corrected. Do not weaken tests for Neon.

Prepare a concrete copy-only fresh-owner-review successor while testing. Actual
builder activation waits for fullPASS/root release, oldnative→52 byte witness,
explicit52→qualifiedcandidate delta and merged canonical-Git bridge. Copy exact
candidate-tested raw Studio bytes, separately prove merged equivalence. No old
review/profile/tool replacement, install, private-art upload or premature build.

PMX2.0 direct reader33CPU and decoded capture22+peer6 are isolated prototypes.
They retain raw words/refs on synthetic inputs; no actual native join, complete
PMX validity, portable table, HAS integration or PMX solver is qualified. Future
native-read protocol is NOT_EXECUTABLE pending witnesses/comparator/stable reader/
bounded execution/context gates. Six-foot480+21 inactive; normalization, human
classification, schema9, PMX reconstruction/rebasing unfinished.200checkstandard
and lighting/discovery requests remain in the master plan, not falsely complete.

Native normal fidelity remains FAILED_UNQUALIFIED (8364/9661 above2e-5). Setter
input is exact, immediate Blender readback differs; untouched replay equals B.
Protect original material-preservingB/private15MB arrays. Carrier16,semantic26,
boundary7,probe20 and resource-survey31CPU checks are source-only. Survey still
needs actual known-B load admission/current-context/native host; historical export
branch can remain UNKNOWN for honest metadata discovery. No guessed options,
nearest-normal matching, overwrite or adoption. NewGLB needs69bones/fivejoints/
HAS/cold/render/export requalification.

Publish new compact completed evidence and verify remote before exact owned
cleanup. Older public download-cache cleanup71files is being prepared, unexecuted.
Its originals/models/art/native arrays/oldreviews/tools/current e8cache are excluded.
Manual observations DEFERRED; stable55/62 acceptance,52/54 implementation unchanged.
'''
(ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md').write_text(plan, encoding='utf-8', newline='\n')
paragraph = '''\n### November17 2026 —375 full closed at authored CRLF golden fixture\n\nFrozen375 full stopped03:50:19.3986079Z after core36/Neon12504/scene106+12830/
helper208+266 and snapshot/editing stages passed. SourceChoice authored bone unit
fails40/40 because its LF-only base64 strip leaves CR in the CRLF source literal.
Main52/GitLF body is identical; independent CR+LF decode yields original9360-byte
goldenSHA39637fa3. Minimal fixture-only successor is being prepared; all79+17,
constants, wrappers and strict error policy must remain. No native model failure
or full PASS is inferred. Root audited51physical jobs(50exit0+Krita cancel2), exact
inline/source1029/birth/scopes and closed desktops, released03:51:37.9325174Z.
Inventory0bd04488ed3f67cb8cdfdac4952736c3c5008e3defe15bbbd531412f67b7f1bd;
separate failing headlessPID26908 exit1/no timeout, not an invented private job.
Main e8cf93c public checkpoint is independently exact534files/5,857,844Gitbytes;
375 reconstruction is recoverable there while redesign remains unmerged. Branch
upload rejection was not retried; explicitly authorized main route succeeded.
No cleanup yet. Native normals/PMX/scale still scoped/inactive; manualDEFERRED,
55/62 and52/54 unchanged. Current pickup supersedes dated active observations.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['historical_375_active_observation'] = bench['latest_observation']
bench['latest_observation'] = {'candidate': state['source_commit'], 'state': state, 'full': 'FAILED_AUTHORED_BONE_GOLDEN_CRLF_BASE64',
    'fixture_checks': 40, 'fixture_failures': 40, 'bindings_wrapper_credited_checks': 0, 'foundation_whole_pass': False,
    'helper_cpu': 208, 'helper_graphical': 266, 'private_physical_jobs_closed': 51, 'normal_exit0': 50, 'Krita_cancel_exit2': 1,
    'failed_headless_pid': 26908, 'inventory_sha256': release['receipt_inventory_sha256'], 'released_utc': release['released_utc'],
    'main_e8cf_remote_files_exact': 534, 'main_e8cf_remote_Git_bytes': 5857844, 'main_merged': False, 'manual_owner_result': 'DEFERRED_NO_RESULT'}
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Closed375 full fails authored bone golden CRLF decode40/40 after helper208/266PASS; source1029/51privatejobsclosed exact. '
    'Review fixture-only CR+LF normalization, preservegolden/79+17; run actualFoundation167/separate77+96 before full158 successor andmerge. '
    'Main e8cf source/evidence exact534remote files; private models protected; manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Recorded closed375 CRLF fixture failure, verified e8cf checkpoint and concrete next task.')
