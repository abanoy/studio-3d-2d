"""Record actual failed-full closure as scalar evidence, without raw model data."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT.parent / 'has-neon-review-20261116-c2d52ff/output/windows-neon-00bf0f9-replay2-20261117T155709412051'
load = lambda p: json.loads(p.read_bytes())
state = load(RUN / 'state.json')
release = load(RUN / 'graphics-lease-closed.json')
inventory = load(RUN / 'terminal-audit-attempt1/receipt-inventory.json')
assert state['status'] == 'failed' and state['suite_exit'] == 1 and state['source_unchanged'] is True
assert release['released'] is True and release['full_suite_passed'] is False
assert release['receipt_inventory_sha256'] == 'acd509905aed7330636e0300d6ed48b9453ec1d1ed3a121130dba7509b888328'
assert inventory['physical_receipt_files'] == inventory['unique_physical_jobs'] == 92
assert inventory['normal_exit0'] == 90 and inventory['registered_cancel_exit2'] == inventory['failed_partial_nonzero'] == 1
assert inventory['all_collected_jobs_desktops_closed_private'] is True and inventory['all_inline_exact_physical_matches'] is True
record = {'observed_utc': datetime.now(timezone.utc).isoformat(), 'state': state,
    'result': 'FAILED_CAMERA_ADVANCED_VISIBILITY', 'camera_report': {'checks': 60, 'failures': 1, 'native_models': 5},
    'failure_label': 'Advanced exposes editable view-distance controls in camera mode',
    'source_only_diagnosis_not_yet_GPU_verified': 'refresh_workspace does not synchronously refresh the inner Camera details parent after changing Advanced mode.',
    'physical_jobs': 92, 'normal_exit0': 90, 'registered_Krita_cancel_exit2': 1, 'failed_partial_nonzero': 1,
    'inline_exact_matches': 11, 'phase_documents': 64, 'functional_sources_unchanged': 1029,
    'released_utc': release['released_utc'], 'inventory_sha256': release['receipt_inventory_sha256'],
    'raw_report_logs_phase_native_arrays_included': False, 'full_pass_claimed': False, 'product_merged': False,
    'new_camera_product_patch_applied': False, 'actual_cold187_started': False}
folder = ROOT / 'experiments/neon_replay2_camera_failure_20261117'
folder.mkdir(exist_ok=False)
(folder / 'OBSERVATION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
paragraph = '''
### November 17, 2026 — replay2 camera control regression and actual closure

The unchanged00bf replay2 full FAILED16:28:42.8760718Z at camera_range60/1:
Advanced view-distance controls were not visible immediately in camera mode.
Its five native fixtures, projection/Undo/recovery/portable/render checks otherwise
passed. Static source diagnosis identifies the hidden Camera details parent:
refresh_workspace changes Advanced children/outer sections, while its inner
inspector refresh previously waited for _process. A one-call synchronous refresh
proposal preserves values/signals and all original test predicates; not applied
or graphically verified at this observation.

Root executed the context-bound strict terminal audit:92actual private jobs
(90exit0,one registeredKrita cancel2,one failed camera process),11exact inline
matches and64phase documents. Source1029unchanged, exact process births/scopes
closed; release16:29:46.0233172Z, inventoryacd509905aed7330636e0300d6ed48b9453ec1d1ed3a121130dba7509b888328.
This is an actual closed failed full, unlike the earlier OS-interrupted run.
All raw logs/reports/phase data stay private. No fullPASS/merge/copy/cold187 claim.
Acceptance55/62 and implementation52/54 stay unchanged; human review deferred.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8').replace('CURRENT dated 2026-11-17T16:01:00.667636+00:00:', 'HISTORICAL running snapshot dated 2026-11-17T16:01:00.667636+00:00:', 1)
intro = '''
CURRENT: replay2 actual full FAILED16:28:42.8760718Z camera_range60/1. Only
failure: Advanced near/far controls hidden until next inspector refresh. Other
five-native/projection/portable/movie cases pass. Source1029unchanged; root9a7
terminal audit closed92private jobs90exit0+Krita2+cameraexit1,11inline/64phases;
released16:29:46.0233172Z inventoryacd50990. Native lane now free/root-exclusive;
do not run terminalhelper again on the same attempt. All raw evidence PRIVATE.
One-call synchronous refresh_camera_inspector proposal9b5cac0b is source-reviewed
but not applied/GPU-qualified yet. Both manifest app pins need exact refresh.
Complete actualfocusedcamera and appropriateNeon controls, then newfrozenfull.
No merge or cold187. A separate authorized read-only B resource diagnostic may
run after fresh admission while source-only camera work continues; no normals
repair/carrier/adoption/fidelity or pre-load filesystem confinement follows.

'''
heading = '# HAS continuation — November 17, 2026\n'
assert text.count(heading) == 1
path.write_text(text.replace(heading, heading + intro, 1), encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['preceding_replay2_running'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Closed replay2FAILEDcamera60/1,source1029unchanged/92privatejobs/11inline/releasedacd50990. '
    'Applyminimal synchronousCameraInspector visibilityfix+exactapp pins afterrootnative lane free; originaltests retained. '
    'Actualfocusedcamera/Neon followed bynewfrozenfull beforemerge/copy/cold187. '
    'Separate read-only Bmetadata diagnostic closure-only context honest, nofidelity/adoption; humanchecksdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'result': record['result'], 'source_unchanged': 1029, 'physical_jobs_closed': 92,
    'graphics_lane_released': True, 'raw_model_data_copied': False}))
