"""Record a dated running observation without promoting expected counts to PASS."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-4ed3a63-20261117T030209'
TARGET = ROOT / 'experiments/neon_windows_4ed3a63_20261117'
load = lambda path: json.loads(path.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
state = load(RUN / 'state.json')
assert state['status'] == 'running' and state['source_commit'] == '4ed3a63b716f696daa1699a76443d6f1abb9b096'
before = load(RUN / 'source-before.json')
assert len(before['source_sha256']) == 1029
assert all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before['source_sha256'].items())
main_before = load(ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json')
assert len(main_before['source_sha256']) == 1019
assert all(sha((ROOT / name).read_bytes()) == pin for name, pin in main_before['source_sha256'].items())
observed = datetime.now(timezone.utc).isoformat()
snap = TARGET / 'active-observation'
snap.mkdir(exist_ok=False)
bindings = []
for name in ('launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'source-before.json', 'preflight-source.json', 'state.json', 'canonical.log'):
    raw = (RUN / name).read_bytes()
    with (snap / name).open('xb') as stream:
        stream.write(raw)
    bindings.append({'source_path': str(RUN / name), 'path': name, 'bytes': len(raw), 'sha256': sha(raw),
                     'snapshot_only_not_terminal': name in ('state.json', 'canonical.log')})
observation = {'format': 'has_neon_4ed_active_root_observation_1', 'observed_utc': observed,
    'candidate': state['source_commit'], 'state': state, 'files': bindings,
    'functional_sources_unchanged_at_observation': 1029, 'main_functional_unchanged': 1019,
    'expected_groups_not_pass': 158, 'expected_core_groups_not_pass': 36, 'expected_movie_checks_not_pass': 21,
    'focused_scene_checks': 106, 'focused_scene_failures': 0,
    'full_result': 'RUNNING_NO_RESULT', 'main_merged': False, 'installed_studio_replaced': False,
    'manual_owner_result': 'DEFERRED_NO_RESULT'}
(snap / 'OBSERVATION.json').write_text(json.dumps(observation, indent=2) + '\n', encoding='utf-8', newline='\n')

plan = f'''# HAS continuation — November 17, 2026

Continue independently without manual questions. Main09fb70ed retains the52f
functional1019-file source. All837 checkpoint files were independently fetched
and exactly verified against remote Git blobs (6,516,391 bytes,4 working-byte
recipes); proof is experiments/neon_followup_checkpoint_remote_20261117.

Review checkout: C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.
Candidate4ed3a63b716f696daa1699a76443d6f1abb9b096 is backed up on
codex/neon-windows-review-20261116. All4 changed remote files independently match.
No main merge, installed replacement or owner observation has occurred.

At {observed}, the complete Windows run is RUNNING, not PASS:
output/windows-neon-4ed3a63-20261117T030209, started03:02:32.7909825Z.
Coordinator22224 birth03:02:32.4796950Z; Python1820 birth03:02:33.0241444Z,
parent22224, both GetProcess exact100ns. Source1029 unchanged at observation.
Root owns the graphics lane exclusively; do not edit candidate functional files
or HEAD or start another native/engine test while this full run is active.
Expected158groups/36core/21movies are not observed successful totals.

Root must independently observe terminal state before invoking the sealed
experiments/neon_4ed3_terminal_20261117/close_terminal.py with
--root-terminal-confirmed --release-closed in approved host context. Check actual
jobs, exact inline joins, source before/after/current, source commit and birth
precision, stale report refusal, both process scopes and closed private desktops.
Helper INDEXf68b5d73d9c7f86792238cda27d964a5e0f5a0f2726a14fed642ed4b351c6cf3.
Do not assume any prior run's job count or infer PASS from a stale final report.

Focused checks PASS: controls48, Neon12504 (12384/32/14/45/29), resize, docking,
nested, separate32 withheld-control transaction; new scene106/0 plus unit.
Scene106 retains original102 checks and thresholds on analytically unblended
display, adds4 raw-viewport forward-composite checks with fixed2/255 write bound,
and refuses unsupported rendering profiles. Approved Neon62percent outside-frame
mask and product code remain unchanged. Old ffcf102/4 failure is retained.
Historical CANDIDATE_COMMIT/PREPARATION UNRUN records describe earlier preparation;
the dated active observation supersedes them, not a terminal result.

Previous full runs remain FAILED and closed: originalc2 object_timing28/2;
381 animated47/1; f387 font diagnostics; ffcf scene102/4. All36core and workspace
checks passed in ffcf,48 unique physical jobs closed, source1029 exact.
Fonts now cache the original two profiles; World commits presentation only after
acceptance and refreshes after floating. Keep every failed predecessor and raw log.
Earlier after-free timing and old regex-overescape suspicions were retracted from
ordered output/exact AST; neither correction changes real receipts/closure.

After a fresh full PASS and terminal audit, review/merge the qualified redesign,
preserve both LLM append histories and Neon styling in app.gd, and build a fresh
owner review. Preserve installed Studio and old owner reviews. If full fails,
close/audit it first, diagnose the actual cause, retain it and qualify a successor.

PMX direct read-only2.0 reader prototype is sealed (INDEX9946bf2b),33 CPU methods
pass including720 prefix layouts, exact339-byte independent oracle, mixed index
roles, exhaustive truncations and guard negatives. Physics words/refs/offsets
are exact on synthetic sources, with nonfinite words opaque/classified. Source
cap128MiB and metadata cap2MiB are explicit; this is bounded layout traversal,
not complete PMX validation. No real native source, decoded join, portable save,
HAS integration or PMX solver is qualified. Decoded capture22+peer6 remains
separate. Six-foot480+21 prototypes pass but normalization/classification/schema9/
PMX reconstruction/rebasing remain inactive. Master roadmap retains owner scope.

Normal fidelity remains FAILED_UNQUALIFIED (8364/9661 above2e-5). Native input to
setter is exact, immediate Blender readback differs; untouched replay equals saved
B. Protect original material-preserving B and private15MB arrays. Carrier16,
non-NORMAL semantic26, boundary7 and probe20 CPU checks are not native repair.
Source-only resource survey/export provenance protocol is being prepared; exact
packed/file image inventory, export branch/options, independent ID binding and
input domain remain prerequisites. No guesses, normal-nearest mapping, overwrite
or adoption. Any newGLB requires69bones/fivejoints/HAS/cold/render requalification.

Publish compact completed source/evidence and verify remote before exact owned
cleanup. Original assets, native arrays, private deliverables, old reviews and
installed tools remain protected. No cleanup yet. Manual checks DEFERRED; formal
ledger55/62 acceptance and52/54 implementation unchanged.
'''
(ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md').write_text(plan, encoding='utf-8', newline='\n')
paragraph = f'''\n### November17 2026 —4ed active Windows successor and PMX reader prototype\n\nAt {observed}, candidate4ed3a63 is running the complete Windows default in
output/windows-neon-4ed3a63-20261117T030209, started03:02:32.7909825Z.
Root rechecked1029 candidate files and1019 main functional files unchanged.
Expected158groups/36core/21movies are not PASS totals. Root owns the native lane;
no functional/HEAD mutation or concurrent engine is allowed until terminal audit.
Focused Scene106 passes with all original102 predicates/thresholds preserved and
four independent forward-composite checks. The approved Neon mask/look and product
source are unchanged; old102/4 failure is retained. Candidate4changed remote files
and all837 files of main09fb independently match Git blobs. PMX2.0 source-only
reader33 CPU methods pass; actual native reads, joins, portable save and solver
remain unqualified. Main merge, owner review replacement and cleanup not done.
Manual observations DEFERRED; formal55/62 and52/54 unchanged. See current pickup.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
record = load(path)
record['latest_observation'] = {'observed_utc': observed, 'candidate': state['source_commit'], 'full': 'RUNNING_NO_RESULT',
    'run_folder': str(RUN), 'source_files_unchanged': 1029, 'focused_scene': '106/0',
    'standard_neon_group': '12504/0', 'waveform_successor': '15/0_NEON_AND_CLASSIC',
    'independent_remote_candidate_files': 4, 'independent_remote_main09fb_files': 837,
    'main_merged': False, 'manual_owner_result': 'DEFERRED_NO_RESULT'}
path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Monitor active4ed complete Windows default, frozen1029 source; Scene106 and Neon12504 focused pass. '
    'Root terminal audit fresh158groups/36core/21movies and actual private jobs/source/birth closure before merge. '
    'Previous failed full runs retained. PMX33 CPU is inactive; native normals unqualified; owner manual checks deferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'observed_utc': observed, 'full': state['status'], 'candidate_files': 1029, 'main_files': 1019, 'main_merged': False}))
