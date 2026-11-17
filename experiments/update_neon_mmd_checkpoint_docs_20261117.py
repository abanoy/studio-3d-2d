"""Append the actual MMD recovery checkpoint without changing any acceptance score."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
evidence = json.loads((ROOT / 'experiments/neon_mmd_fixture_recovery_actual_20261117/RESULT.json').read_bytes())
assert evidence['prior_full']['full_suite_passed'] is False
assert evidence['fresh_full']['status_at_observation'] == 'RUNNING'
entry = '''
## 2026-11-17 — restored native MMD coverage; fresh Neon full running

The first3a full completed with verifier exit0 and1029 unchanged functional files,
but strict qualification correctly refused:157 groups/20 movies, actual MMD false,
and missing posed_model_video_1. Its196 private jobs closed (195 exit0, one registered
Krita cancellation). Separate closure-only evidence always labels it UNQUALIFIED.
The original158/36/21/MMD acceptance gates remain unchanged.

Root restored the exact18-file prepared MMD bundle (2,648,542 bytes), preserving
originals. The unchanged canonical pose command then passed45 checks, actual MMD,
save/reopen and two independently probed48-frame movies; source and process scopes
closed. Preflight first refused the two project metadata files intentionally saved
by that test. Those exact owned outputs were preserved and explicitly declared;
all36 Root originals, other34 Review copies and18 prepared originals/copies stay
checked. No general pin refresh or content threshold change was introduced.

Freshfull windows-neon-3a3701a-mmd-20261117T200622956559 started20:07:58 UTC at
frozen3a3701a/1029. Coordinator21536/Python2976 use actual GetProcess births;
CIM is separate metadata. It is RUNNING, Root-exclusive, not a PASS or merge.
Strict terminal source INDEXf223587f retains original observer/legacy/158 gates.
After actual PASS/closure: preserve both histories in the qualified merge, copy
the exact tested bytes, then execute the fresh owner-copy and cold187 route.

The independent B inspection loaded the real model and passed known-factory
handler metadata, then failed the helper's incorrect bpy.blend_paths call. Its
private job closed and all inputs/tools/source stayed unchanged. API9f8e24d0
corrects the namespace to bpy.utils.blend_paths;38 CPU checks and source peer pass.
Native rerun/integration remain separate; native-normal fidelity is still failed.
PMX passive diagnostics completed4/4 with originals/copies/source unchanged and
children reaped. Three original oracle refusals are at the joint table limit;
one traversed fully. Counts remain private, limits unchanged, prefix correctness
and candidate/archive/simulation/production adoption unqualified.

Scalar evidence: experiments/neon_mmd_fixture_recovery_actual_20261117 (INDEXe9fc98b5).
Main remains52f functional/1019; stable implementation52/54 and acceptance55/62
remain unchanged. Human checks deferred; no owner interruption, installed-tool
replacement, artwork upload, review overwrite or additional cleanup.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    path = ROOT / name
    original = path.read_bytes()
    assert b'restored native MMD coverage; fresh Neon full running' not in original
    newline = '\r\n' if original.count(b'\n') == original.count(b'\r\n') else '\n'
    with path.open('ab') as stream: stream.write(entry.replace('\n', newline).encode('utf-8'))
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
value = json.loads(path.read_bytes())
assert 'restored_MMD_20261117' not in value
value['restored_MMD_20261117'] = evidence
path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
value = json.loads(path.read_bytes())
before = [(row['id'], row['implementation'], row['verification'], row['acceptance_status']) for row in value['requirements']]
value['next_actions'][0]['action'] = 'Monitor fresh unchanged3a/1029 full windows-neon-3a3701a-mmd-20261117T200622956559, coordinator21536/Python2976, Root-exclusive. Prior157/20 software exit0 is UNQUALIFIED missing actualMMD/posed1;196 jobs closed. Exact18 MMD fixture restored and canonical45/native/two movies passed. Strict158/36/21 gates unchanged; actualterminalaudit and physical/source/processclosure before merge/newreview/cold187. Public scalar evidence INDEXe9fc98b5, strict context INDEXf223587f. No other native job while full active; human checks deferred.'
ui = next(row for row in value['requirements'] if row['id'] == 'UI-01')
ui['evidence'].append({'kind': 'recorded_report',
    'path': 'experiments/neon_mmd_fixture_recovery_actual_20261117/RESULT.json',
    'scope': 'Prior3a software completed/Neon12504 but nativeMMD skipped, explicitly unqualified. Exact fixture restored; native pose45 and two movies pass separately. Fresh complete rerun RUNNING; no qualified merge or owner result.'})
assert before == [(row['id'], row['implementation'], row['verification'], row['acceptance_status']) for row in value['requirements']]
path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/RESUME_MASTER_PLAN.md'
original = path.read_bytes()
newline = '\r\n' if original.count(b'\n') == original.count(b'\r\n') else '\n'
with path.open('ab') as stream:
    stream.write(('\n\n2026-11-17 pickup: the passive PMX count diagnostic has now completed for all four\n'
        'stable source/copy pairs; the three original refusals are at the joint table\n'
        'limit. Counts stay private; unchanged limits do not yet prove prefix parsing\n'
        'or native protocol correctness. Candidate comparison/archive/simulation remain\n'
        'unqualified. Source B finally loaded; its resource collector then hit the\n'
        'wrong Blender API namespace. Sealed API9f8 fixes that one call with38 CPU\n'
        'checks; actual integrated rerun remains pending. Neon first3a software exit0\n'
        'was unqualified for missing nativeMMD; exact18 fixture restoration and\n'
        'canonical45/two movies passed. Fresh frozen3a full at20:07 UTC is RUNNING,\n'
        'Root-exclusive. Use strict contextf223 and actual eventual closure; never\n'
        'activate merge/copy/cold187 from the old incomplete157-group result.\n').replace('\n', newline).encode('utf-8'))
print('Updated five progress documents; every stable requirement status preserved.')
