"""Record terminal facts; keep the earlier dated active observation historical."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-4ed3a63-20261117T030209'
load = lambda path: json.loads(path.read_bytes())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
state = load(RUN / 'state.json')
release = load(RUN / 'graphics-lease-closed.json')
assert state['status'] == 'failed' and state['source_unchanged'] is True and state['suite_exit'] == 1
assert release['released'] is True and release['full_suite_passed'] is False and release['physical_jobs'] == 49
assert release['receipt_inventory_sha256'] == sha(RUN / 'terminal-audit-attempt1/receipt-inventory.json') == '6b8c57667a3c553152396711a6b755faf7f923714ad6724eddba06bf123ad87d'
before = load(RUN / 'source-before.json')
after = load(RUN / 'source-after.json')
assert before['source_sha256'] == after['source_sha256'] and len(before['source_sha256']) == 1029
helper = load(REVIEW / 'output/helper-preview/cpu-1794885569749222100-140852bb/verification.json')
assert helper['checks'] == 0 and helper['error'] == 'RuntimeError: Unreviewed helper main bytes: src/app.gd'
plan = '''# HAS continuation — November 17, 2026

Continue independently without manual questions. Main09fb70ed keeps52f functional
1019 source files; all837 checkpoint files independently match GitHub blobs
(6,516,391 bytes,4 working-byte recipes). Candidate4ed3a63 is backed up on
codex/neon-windows-review-20261116; all4 changed remote files independently match.
Review checkout: C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.
No redesign merge, installed replacement or owner observation has occurred.

LATEST FULL FAILED: output/windows-neon-4ed3a63-20261117T030209 ran
03:02:32.7909825–03:19:31.3363666Z. Source1029 unchanged; all36core,Neon12504,
workspace controls/resize/docking/nested, rotation, scene106+unit12830, native
readback lifecycle, World teardown, fan flutter and wind stages reached/pass
before helper-preview CPU refused its stale app.gd manifest. Helper ran0checks,
attempted no graphical process; do not call this a helper behavior test failure.
The underlying explicit review gate worked. Refresh only independently reviewed
runtime rows, preserve all other rows/membership/hash gates and original208CPU/
266graphical assertions; run tamper negatives and both actual focused profiles
before freezing/backing up a successor and rerunning complete158groups/36core/
21movies. Expected totals are not a full PASS. Root alone owns native execution.

Root audited49 actual physical jobs (48exit0+Krita cancel2); all exact inline joins,
private desktops and process scopes closed. Released03:19:55.1591793Z, inventory
6b8c57667a3c553152396711a6b755faf7f923714ad6724eddba06bf123ad87d.
Coordinator22224 birth03:02:32.4796950Z; Python1820 birth03:02:33.0241444Z,
parent22224 (GetProcess100ns). Both original births absent; no termination issued.
Current graphics lane is free. No stale full report used. Compact failure packet
experiments/neon_failed_4ed_actual_packet_20261117 preserves71 exact originals.
Earlier active observations/UNRUN preparation are historical, not current status.

Focused UI passes retain all predicates/thresholds. Scene106 keeps original102,
analytically handles the approved62percent off-frame mask and adds4 independent
forward-composite checks under explicit raster guards/fixed2/255 bound. Product
code/look unchanged. Compact Scene106 archive retains both old102/4 diagnostic
and106/0 successor with12830 headless unit checks;2 real private jobs, no invented
headless receipt. Original c2,381,f387,ffcf and4ed full failures remain preserved.
Fonts cache original profiles; World commits mode only after styling acceptance.
Ordered-log/regex source corrections are documented; do not repeat retracted
after-free attribution or escaped-regex suspicion. Strict diagnostics stay enabled.

Only after a successful fresh complete default and terminal/source/ownership
audit, merge the reviewed redesign, preserve both LLM append histories and Neon
styling in app.gd, then make a fresh owner review. Preserve old reviews/installed
Studio. A source-only successor review builder is being prepared; no build yet.

PMX2.0 reader prototype INDEX9946bf2b passes33 CPU methods including720 prefix
layouts, independent339-byte oracle, mixed index roles and exhaustive truncation.
It preserves raw physics refs/words/offsets on synthetic streams, classifies
opaque nonfinite words, and uses128MiB source/2MiB metadata caps. It is bounded
layout traversal, not complete PMX validity or native/decoded/HAS/portable/solver
qualification. Future native recipe INDEXc36c2992 is explicitly NOT_EXECUTABLE
until its witness/comparator/stable reader/resource/context gates exist. No actual
PMX asset read. Decoded22+peer6 separate; six-foot480+21 prototypes inactive.
Normalization/classification/schema9/PMX reconstruction/rebasing remain unfinished.

Normal fidelity remains FAILED_UNQUALIFIED (8364/9661 above2e-5). Native input
to Blender setter is exact; immediate readback differs; untouched replay equals
savedB. Protect original material-preservingB and private15MB arrays. Carrier16,
semantic26,boundary7,probe20 CPU checks do not qualify a native repair. Read-only
resource survey is in preparation; original image resources, exact export branch,
independent ID binding/input domain and bounded current-context native runner
remain gates. No guessed defaults/nearest-normal mapping/overwrite/adoption.
Any changedGLB requires69bone/fivejoint/HAS/cold/render/export requalification.

Publish compact completed public evidence and verify remote before exact owned
cleanup. Native originals, art, private arrays/deliverables, old reviews and tools
remain protected. No cleanup yet. Manual observations DEFERRED; formal ledger
55/62 acceptance and52/54 implementation unchanged. Master roadmap retains all
owner lighting/discovery/standardization/200check/six-foot and earlier requests.
'''
(ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md').write_text(plan, encoding='utf-8', newline='\n')
paragraph = '''\n### November17 2026 —4ed full closed at helper source admission\n\nThe frozen4ed full stopped03:19:31.3363666Z with1029 source files unchanged.
All36core,Neon12504,scene106+unit12830 and subsequent native readback/teardown/
fan/wind stages reached/pass; helper-preview CPU refused stale reviewed app.gd
before0checks/no graphical attempt. Exact review gating remains enabled; its
minimal reviewed manifest successor is being prepared, not yet executed. Root
audited49physical jobs48exit0+registeredKrita cancel2, exact inline receipts and
both original births/scopes absent, then released03:19:55.1591793Z. Inventory
6b8c57667a3c553152396711a6b755faf7f923714ad6724eddba06bf123ad87d.
All failed/full/scoped evidence remains distinct. No complete PASS, merge, owner
observation or native-normal/PMX/scale qualification. Manual DEFERRED,55/62 and
52/54 unchanged. Current pickup supersedes the earlier dated running observation.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
record = load(path)
record['latest_observation'] = {'candidate': state['source_commit'], 'full': 'FAILED_HELPER_PREVIEW_STALE_REVIEW_MANIFEST',
    'state': state, 'source_files_unchanged': 1029, 'helper_checks': 0, 'helper_graphical_attempt': False,
    'helper_error': helper['error'], 'closed_physical_jobs': 49, 'normal_exit0': 48, 'Krita_cancel_exit2': 1,
    'inventory_sha256': release['receipt_inventory_sha256'], 'released_utc': release['released_utc'],
    'focused_scene': '106/0_AND_UNIT12830/0', 'standard_neon_group': '12504/0',
    'independent_remote_candidate_files': 4, 'independent_remote_main09fb_files': 837,
    'main_merged': False, 'manual_owner_result': 'DEFERRED_NO_RESULT'}
path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Closed4ed full failed helper stale app review manifest before0checks/no graphical attempt;49jobs closed/source1029 exact. '
    'Review minimal manifest-only refresh preserving all other pins/gates/assertions, run focused208CPU/266graphical+tamper negatives, '
    'then freeze/back up successor and rerun complete158 Windows groups before merge. PMX33 CPU inactive; native normals unqualified; manual deferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Recorded closed4ed source-manifest refusal; no full PASS/merge claimed.')
