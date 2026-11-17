"""Record actual focused results and the independently observed full-run launch."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_windows_f387d0e_20261117'
prep = json.loads((PACKET / 'PREPARATION.json').read_bytes())
run = Path(prep['run_folder'])
launch = json.loads((run / 'launch.json').read_bytes())
birth = json.loads((run / 'root-birth-observation.json').read_bytes())
state = json.loads((run / 'state.json').read_bytes())
assert launch['source_commit'] == prep['revision'] == 'f387d0e9ddfb099140c0699d9f7ed430f5d7b949'
assert state['source_commit'] == prep['revision'] and state['status'] == 'running'
assert birth['coordinator']['pid'] == launch['coordinator_pid'] == 25388
assert birth['python']['pid'] == 23904 and birth['python']['parent_pid'] == 25388
for name in ('launch.json', 'root-birth-observation.json'):
    destination = PACKET / name
    assert not destination.exists()
    destination.write_bytes((run / name).read_bytes())

note = '''
## 2026-11-17 — Focused Windows successors pass; f387 full run started

The reviewed fixture follow-up is committed and backed up on the separate
codex/neon-windows-review-20261116 branch at
f387d0e9ddfb099140c0699d9f7ed430f5d7b949. Production app/workspace code and the
approved Neon palette are unchanged from the reviewed381 candidate. The native
channel successor passes48/0 across MMD, GMod and SFM; both movement profiles
pass34 UI and13 unit checks each. All old predicates and failed observations stay.

The final waveform fixture passes15/0 in both Neon and Classic, with four bars
and the original RGB tolerance.02. Its fractional-edge expectation is derived
from the pinned Godot4.6 StyleBoxFlat AA geometry and source theme; no observed
pixel is used as its own oracle. Earlier13/1,14/1 and stale movement API/watchdog
results remain retained. Product geometry, colors and waveform data did not change.

Root started a fresh full Windows verifier at2026-11-17T01:27:36.5856364Z in
output/windows-neon-f387d0e-20261117T012410. Coordinator25388 was born
01:27:36.0890696Z; Python23904 was born01:27:37.1616850Z, parent25388. Their
births were observed immediately. Source1028 and all approved input/runtime
identities were checked before launch. Expected158 groups,36 core and21 movie
checks are not a PASS claim. The native/graphics lane remains root-exclusive.
Do not edit that checkout or launch another engine until terminal closure.

Independent root audits checked all35 setter-archive payloads/25 original
bindings and52 failed381 payloads/42 original bindings, including decompressed
bytes against actual originals. No private normal arrays, art or media are copied.
Exact-ID normal repair has16 synthetic CPU checks, but no native correction,
new GLB, fidelity PASS or live-model adoption. The original normal failure remains.
The actual setter diagnostic and six-foot transport results remain scoped as
documented; production normalization/PMX reconstruction is still inactive.

No redesign merge or installed-app replacement has occurred. Owner checks remain
DEFERRED. Formal ledger denominators/statuses remain55/62 and52/54. After fresh
full verification, audit actual receipts and process births, then merge only the
qualified redesign while preserving main history. Continue other independent work.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    path = ROOT / name
    assert '## 2026-11-17 — Focused Windows successors pass; f387 full run started' not in path.read_text(encoding='utf-8')
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(note)

plan = '''# HAS continuation — November 17, 2026

Continue independently without manual questions. Main remains the52f functional
reference plus592fe4f metadata; the approved Neon redesign is separate and unmerged.

The current candidate is f387d0e9ddfb099140c0699d9f7ed430f5d7b949 on the backed-up
codex/neon-windows-review-20261116 branch, in
C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.
Its full Windows verifier is ACTIVE in output/windows-neon-f387d0e-20261117T012410.
Coordinator25388 birth2026-11-17T01:27:36.0890696Z; Python23904 birth
01:27:37.1616850Z, parent25388. Root captured both. Source1028; expected158 groups,
36 core,21 movies. These are expected counts, not a completed result. No other
engines/native jobs or edits to that checkout until terminal and physical closure.

The original c2 full failed object timing28/2; the381 full failed animated
channels47/1. Their24 and27 physical jobs respectively are closed and source
unchanged. Failed evidence and exact receipts are retained in compact archives.
Root independently checked228/217 original review payloads/bindings,35/25 setter
and52/42 failed381. No private arrays/art/media were uploaded.

Focused actual Windows checks: behavior32, inset12384, compact timeline14,
rail placement45 and existing UI23 pass. Native channel48 passes across the
three retained MMD/GMod/SFM projects. Movement legacy/component each34 UI+13
unit pass. Final waveform15 passes in both Neon and Classic with four bars,
unchanged.02 RGB tolerance and a source-derived AA boundary expectation.
Earlier failures/watchdog remain. These scoped checks do not replace the full run.

When the full finishes, audit its fresh report/physical receipts, inline jobs,
exact source hashes and process births. Derive counts; never assume the prior
192 jobs. Diagnose failures without relaxing assertions. Only after qualification
merge the reviewed redesign, reconcile main history, and keep Neon in app.gd.
Build a fresh owner review; preserve both older reviews and installed Studio.
Manual owner observations remain DEFERRED and must not block independent work.

The normal-setter diagnostic completed24.179 seconds with private closure and
all26 roles/full52 source preserved. Correct native input changes immediately
at Blender readback; validation leaves it unchanged and untouched replay matches
saved B exactly. See source_normal_setter_2026-11-17 benchmark. Private15MB arrays
stay output-only. Original GLB failure8364/9661 above2e-5, max.00121654672362075
remains FAILED_UNQUALIFIED. Exact-ID carrier prototype has16 synthetic checks;
next isolate an export from the original material-preserving B scene, qualify an
independent per-primitive identity map and preserve all non-NORMAL channels.
A new GLB requires fresh69-bone/five-joint/HAS/cold/render/export qualification.
Never replace original B or infer native correctness from source-only tests.

Six-foot domain480+boundary21 pass, original encoder/oracle preserved, seven
historical int/float false differences retained. Active normalization, production
schema9, classification, PMX reconstruction/rebasing remain unfinished. The master
roadmap and prior November16 plan retain other owner requests/protected paths.

Push each compact completed increment and verify remote bytes before exact owned
cleanup. Native originals, private deliverables, old reviews and installed tools
are protected. Stable ledger55/62 acceptance and52/54 implementation is unchanged.
'''
(ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md').write_text(plan, encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
record = json.loads(path.read_bytes())
record.update(candidate=prep['revision'], third_full='ACTIVE_ROOT_OBSERVED',
              third_full_context={'run_folder': prep['run_folder'], 'started_utc': state['started_utc'],
                                  'source_files': 1028, 'expected_groups': 158, 'core_groups': 36,
                                  'movie_checks': 21, 'birth_observation': birth},
              waveform_final={'classic': '15/0', 'neon': '15/0', 'bars_each': 4,
                              'rgb_tolerance': 0.02, 'oracle': 'source-derived StyleBoxFlat AA',
                              'old_failures_retained': True})
path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
path = ROOT / 'docs/completion_checklist.json'
ledger = json.loads(path.read_bytes())
before = {row['id']: {k: v for k, v in row.items() if k not in ('evidence', 'remaining')}
          for row in ledger['requirements']}
for row in ledger['requirements']:
    for evidence in row.get('evidence', []):
        if evidence.get('path') == 'docs/benchmarks/neon_review_2026-11-17.json':
            evidence['scope'] = ('Approved Neon review and focused Windows checks pass; original c2/381 full failures are retained and closed. '
                                 'The f387 full run is active, not passed or merged. No owner observation is inferred.')
ledger['next_actions'][0]['action'] = ('Audit the active f387 full Windows run and fresh closure before merging the reviewed Neon redesign. '
    'Focused native channels48, movement34+13 in both profiles, waveform15 in both themes pass; preserve prior failures. '
    'Native normal setter loss is measured; exact-ID repair remains synthetic and unqualified. Keep private arrays/original B and manual deferrals.')
assert before == {row['id']: {k: v for k, v in row.items() if k not in ('evidence', 'remaining')}
                  for row in ledger['requirements']}
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'recorded': 'ACTIVE, not PASS', 'candidate': prep['revision'], 'source_files': 1028,
                  'main_merged': False, 'formal_statuses_unchanged': True}))
