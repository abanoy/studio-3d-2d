"""Add scoped evidence without changing stable requirements or scores."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / 'docs/completion_checklist.json'
data = json.loads(path.read_text(encoding='utf-8'))
before = [(r['id'], r['implementation'], r['verification'], r['acceptance_status']) for r in data['requirements']]
full = {'kind': 'test_result',
        'path': 'experiments/windows_bone_binding_full_actual_20261115/BENCHMARK.json',
        'commit': 'f0dd57a2e568089d396fecba819ab987da658bf0',
        'scope': 'Fresh complete configured-Windows default PASS:157named results/36core groups/21movie metadata groups, both decoded audio onsets1.0s;1008functional files/HEAD exact;192closed private jobs(191exit0,one registered Krita cancel2). Actual receipt/report reconciliation and root closure; prior failed/interrupted runs remain separate. Not artist/novice/device/clean-install or native Source dynamics certification.'}
review = {'kind': 'test_result',
          'path': 'experiments/sfm_review_actual_20261115/BENCHMARK.json',
          'commit': 'f0dd57a2e568089d396fecba819ab987da658bf0',
          'scope': 'Fresh separate four-example SFM review PASS180checks(44/46/49/41),4closed private jobs,9preservation gates,8native reference frame matches and12strict state/audio-cache comparisons. First failed cache/portable-state comparison is retained; successor independently proves decoded PCM cache bindings before projection. Installed Studio/originals/prior reviews unchanged. Not native solver/artist parity or manual acceptance.'}
readiness = {'kind': 'test_result',
             'path': 'docs/benchmarks/native_source_readiness_2026-11-15.json',
             'commit': 'f0dd57a2e568089d396fecba819ab987da658bf0',
             'scope': 'Actual unchanged Model/SceneIO native pose/tip transport41588checks/220configurations at one source conversion0.01905 with root scales1/2; standalone scalar64 Godot math8994checks/1440synthetic ticks. Scoped experiment only; source coefficients stay inactive. No full Source SDK/artist/GUI/fan/body/Record/HAS/render qualification, native normal gate remains failed. No status/denominator changes.'}
for row in data['requirements']:
    additions = [full, review, readiness] if row['id'] in ['IMPORT-02', 'IMPORT-03'] else []
    for evidence in additions:
        assert (root / evidence['path']).is_file()
        assert all(e['path'] != evidence['path'] for e in row['evidence'])
        row['evidence'].append(evidence.copy())
for action in data['next_actions']:
    if action['requirement'] == 'IMPORT-02':
        action['action'] = ('Fresh complete Windows default and180-check four-example SFM review now pass. Continue independent native Source dynamics readiness: actual joint transport and standalone math are qualified separately; integrate only a proved subset with existing overlays/fan/Off/Record/HAS after bounded geometry and hierarchy checks. Keep native normals, SDK/artist parity and wider profiles explicitly unqualified. Deferred manual artist observations do not block this independent work.')
    if action['requirement'] == 'IMPORT-03':
        action['action'] = ('Preserve source-specific data in one richer HAS model contract. Native normal-fidelity gate remains failed; two actual conversion scales, native solver/GUI/render fidelity and original artist comparison remain separate. Implement six-foot human normalization at user scale1 as a derived import basis, not current optional root-scale fitting; PMX physics/reconstruction and roughly200capability checks remain planned. No automatic acceptance credit from experiment tests.')
after = [(r['id'], r['implementation'], r['verification'], r['acceptance_status']) for r in data['requirements']]
assert before == after and len(after) == 62
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Scoped evidence added; all62stable requirement statuses unchanged')
