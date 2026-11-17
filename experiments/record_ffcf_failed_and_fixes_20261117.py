"""Record completed software evidence and the actual closed failed full run."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-ffcf4c5-20261117T021833'
state = json.loads((RUN / 'state.json').read_bytes())
release = json.loads((RUN / 'graphics-lease-closed.json').read_bytes())
assert state['status'] == 'failed' and state['suite_exit'] == 1 and state['source_unchanged'] is True
assert release['released'] is True and release['physical_jobs'] == 48 and release['final_full_report_used'] is False
assert release['receipt_inventory_sha256'] == '2c334aab837768ee17b2c13be0ad6ac26fa203a9e8815cd991b24a2de3386704'

note = '''
## 2026-11-17 — Font/dock fixes qualify; ffcf full reaches scene-view check

Candidateffcf4c54ab9ab7af7cb01329a5b3b5b6f4589865 is committed and backed up on
the separate review branch. All9 changed files were independently retrieved and
matched byte-for-byte and by Git blob. Main1ce433bd's565-file checkpoint was also
fully read back (4,982,585 bytes,6 working-byte recipes). Main functional1019
remains the completed52f reference; no redesign merge or installation occurred.

Actual focused Windows verification passes controls48, integratedNeon12504
(inset12384,behavior32,compact14,rail45,lifecycle29), resize, docking and nested
wrappers. Source1029 is unchanged and all private jobs/scopes close. The separate
32-check transaction extension also passes: an unavailable held control refuses,
both caches remain unchanged, and restoring the same control/index permits one
refresh to the correct full list. It does not inflate the formal12504 group.

The fix retains original Neon/classic Tree fonts to avoid invalidating resources
during live restyling. Font families/weight/Japanese fallback remain unchanged.
Lifecycle guards alone were insufficient; their48/0-plus-diagnostics failure is
kept. Guards then exposed a floating World45/1 mismatch: the setter now returns
acceptance, the layout commits only after success and a single deferred refresh
finishes detachment. All45 original rail assertions pass. Inset/Compact use one
full-precision JSON string for file and log, preserving every numeric threshold
and strict equality. Six explicit WeakRef types resolve the original fixture's
parser warnings while preserving its29 predicates. Failed observations remain.

Two interpretation corrections are explicit. Ordered engine output puts the font
error during live resize/docking; concatenated stdout/stderr did not establish
after-free timing. Also, AST decoding of exact9f604060 old helper source proves
the same valid native regex: the suspected overescape was a source-display
misreading. No earlier native zero count is invalidated by a nonexistent regex
defect. New root observations additionally cover selected helpers/coordinators
and execute4positive/3negative matcher cases; physical receipts are independent.

The complete ffcf run started02:22:31.5782448Z and FAILED02:34:45.1241655Z at
scene-view102/4. It passed all36 core groups, controls, Neon12504, resizing,
docking, nested layout and rotation before stopping. All4 failures are the same
off-frame screen-color threshold across wide/tall and rolled/unrolled cases.
Selection, pose, Undo, projection/unit and unchanged native-output checks pass.
The approved Neon presentation draws a source-declared62percent dim mask outside
the camera frame; saved images show the model correctly aligned but dimmed.
An exact source-pinned mask/composite fixture is being prepared; no threshold,
guide bound, product look or render output has been changed or qualified by it.

Root's strict ffcf terminal helper audited48 unique physical jobs:46 exit0,
1registered Krita cancel2 and1scene assertion exit1. Sources1029 remain exact,
all inline receipts join physical receipts, both original process identities and
owned runtime scopes are absent, and the failed-only lease released
02:36:25.0277413Z. Inventory2c334aab837768ee17b2c13be0ad6ac26fa203a9e8815cd991b24a2de3386704.
No stale final full report was read. Root observed both births at launch using
the same GetProcess API used at closure; CIM precision detail is retained.

Compact completed fix archivee8a7f25e has305payloads/417 exact original bindings
and23 private jobs. Standalone32 appenddb32fd93 has36payloads/33 bindings and
1 closed job. Root independently checked every exact payload/decompressed source.
These24 jobs are separate from the48 failed-full jobs. Private arrays/art/media
are excluded. The earlier failedf387 archive remains immutable with its timing
interpretation explicitly retracted in the later correction packet.

Source-only model progress remains scoped: decoded PMX field preservation passes
22 synthetic checks plus6 independent boundaries, but native-file joining stays
UNQUALIFIED and no PMX solver or portable table is active. The installed reader's
negative-reference collapse, truncation fallback, string replacement and2.1 limits
are disclosed. Exact-ID carrier16, non-NORMAL semantic comparison26 and boundary7
CPU checks do not qualify native correspondence, input validity or NORMAL output.
Original normal fidelity remains FAILED_UNQUALIFIED; private B/15MB arrays stay
protected. Six-foot normalization/classification/schema9/PMX reconstruction and
rebasing remain inactive. Future source preparation does not imply deployment.

Next qualify the exact scene-presentation fixture, back up the resulting candidate
and rerun the complete Windows default before merge. Preserve all failures,
approved Neon, concurrent main history, installed Studio and prior owner reviews.
Manual owner observations remain DEFERRED. Formal55/62 and52/54 are unchanged.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    path = ROOT / name
    assert '## 2026-11-17 — Font/dock fixes qualify; ffcf full reaches scene-view check' not in path.read_text(encoding='utf-8')
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(note)

plan = '''# HAS continuation — November 17, 2026

Continue independently without manual questions. Latest pushed main1ce433bd has
completed public source/evidence; all565 files independently retrieved/exact
(4,982,585 bytes,6 working-byte recipes). Main functional1019 remains52f.

Review checkout: C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.
Candidateffcf4c54ab9ab7af7cb01329a5b3b5b6f4589865 is backed up on
codex/neon-windows-review-20261116; all9 changed remote files match. Source1029.
No main merge, installed replacement or owner observation has occurred.

Actual focused checks PASS: controls48, Neon12504 (12384/32/14/45/29), resize,
docking, nested, separate32 withheld-control transaction. Original thresholds,
predicates and diagnostic refusal remain. Fonts are cached with original profiles;
World commits presentation mode only after acceptance and refreshes once after
floating. Original font/lifecycle48 failures, rail45/1, parser warnings and JSON
precision mismatch remain retained with successful successors.

The ffcf full FAILED at scene-view102/4 after all36 core groups and the workspace
stages above. Run output/windows-neon-ffcf4c5-20261117T021833,02:22:31–02:34:45Z.
All4 failures are the off-frame displayed-color threshold; the approved Neon
mask dims outside the camera frame62percent. Alignment/selection/pose/Undo/native
output checks pass. Parent is preparing a source-pinned analytical mask/composite
fixture; product colors/look, guide bounds and numeric thresholds must not weaken.
Keep the old102/4 result; a fixture draft is not a successful full run.

Root terminal audit closed48 unique jobs (46exit0,1Krita cancel2,1scene assert1)
and source1029 unchanged; inline physical joins exact, no stale final report.
Lease released02:36:25.0277413Z, inventory2c334aab837768ee17b2c13be0ad6ac26fa203a9e8815cd991b24a2de3386704.
Coordinator27512 born02:22:31.2361797Z; Python27124 born02:22:31.8526561Z,
parent27512, both GetProcess times. Four immutable metadata inputs/API precision
detail are pinned by terminal packet22e0c12e4a1ee55b079571a4befa01f7c3d75902a151d2a0c918dee5986e7317.
Current lane is free; root alone may launch the next reviewed native test.

After focused scene qualification, commit/back up candidate and run the whole
158-group/36core/21movie default again. Derive fresh physical counts, source and
birth closure; never reuse stale reports or assume192 jobs. Merge only a qualified
reviewed redesign, reconcile LLM append histories and retain Neon in app.gd.
Build a fresh owner review without replacing older reviews/installed Studio.

Completed sequence archivee8a7f25e:305payloads/417 exact bindings/23 jobs.
Standalone32 appenddb32fd93:36payloads/33 bindings/1 job. Root exact audits pass.
The earlier after-free timing inference is retracted by ordered engine output;
the old regex-overescape suspicion is also retracted by exact AST decoding.
Neither correction changes actual receipts or independently observed closure.

Normal fidelity remains FAILED_UNQUALIFIED (original8364/9661 above2e-5).
Setter input is exact, immediate Blender readback differs, validation unchanged,
untouched replay equals saved B. Keep original B and private15MB arrays. Carrier
16, semantic26 and boundary7 CPU checks are not native qualification. Agent is
preparing a bounded carrier probe/independent ID mapping/resource survey protocol;
packed/file image inventory and exact original export branch remain prerequisites.
No guessed options, normal-nearest mapping, original overwrite or automatic adoption.
New GLB needs source69-bone/five-joint/HAS/cold/render qualification.

PMX decoded capture22+peer6 synthetic pass, native join UNQUALIFIED/no solver or
portable table. Direct bounded PMX reader is source-only future work. Six-foot
480+21 pass as inactive prototypes; normalization/classification/schema9/PMX
reconstruction/rebasing unfinished. Master roadmap retains prior owner requests.

Push compact completed work and verify remote before exact owned cleanup. Native
originals, private deliverables, prior reviews and installed tools are protected.
Manual observations DEFERRED; ledger55/62 acceptance and52/54 implementation unchanged.
'''
(ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md').write_text(plan, encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
record = json.loads(path.read_bytes())
record.update(candidate=state['source_commit'], standard_Neon_12504='PASS_ALL5_CASES',
              all5_workspace_wrappers='PASS', transaction_standalone32='PASS',
              next_full='FAILED_FFCF_SCENE_VIEW102_4', next_full_state=state,
              next_full_closed_jobs=48, next_full_inventory_sha256=release['receipt_inventory_sha256'],
              main_merged=False, old_regex_overescape_inference='RETRACTED_PATTERN_VALID')
path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
path = ROOT / 'docs/completion_checklist.json'
ledger = json.loads(path.read_bytes())
ledger['next_actions'][0]['action'] = ('Qualify the source-pinned Neon off-frame mask/composite fixture after closed ffcf scene-view102/4 failure; '
    'all36core and focused48/12504/32/resize/docking/nested pass. Preserve original predicates/thresholds and mask/look. '
    'Back up candidate and rerun complete158 Windows groups before merge. Native normals/PMX/six-foot remain scoped or inactive; manual checks deferred.')
for row in ledger['requirements']:
    for evidence in row.get('evidence', []):
        if evidence.get('path') == 'docs/benchmarks/neon_review_2026-11-17.json':
            evidence['scope'] = 'Focused Windows12504 plus48/32/layout wrappers pass; ffcf full stops at scene-view102/4 under approved dim mask. Failed full48jobs closed/source1029 exact; no full PASS, merge or owner observation.'
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Recorded truthful closed failed ffcf and completed focused/model prototype evidence; no merge/full PASS.')
