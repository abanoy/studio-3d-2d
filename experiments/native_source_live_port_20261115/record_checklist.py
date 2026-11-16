"""Add scoped evidence; preserve stable IDs, statuses and denominators."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'docs/completion_checklist.json'
data = json.loads(path.read_text(encoding='utf-8'))
before = [(r['id'],r['implementation'],r['acceptance_status']) for r in data['requirements']]
for requirement in data['requirements']:
    if requirement['id'] in ['IMPORT-02','IMPORT-03','PHYS-01']:
        reference = {'kind':'test_result','path':'docs/benchmarks/native_source_live_2026-11-15.json',
                     'scope':'Working-source native8 FrontHair1 only:96 actual private UI/fan/Off/Record/Undo/cold-HAS/PNG-export checks; later header/complete-binding guard separately180headless lifecycle checks on3actualinstances. One of49rules; rawmetadata unchanged. Earlier74/2fixture failure and parse refusal retained. Same-actor active ragdoll, wider chains, artist/SDK fidelity and current complete-default remain unqualified; oldfullf0dd is separate. No acceptance status change.'}
        assert not any(e.get('path')==reference['path'] for e in requirement['evidence'])
        requirement['evidence'].append(reference)
for action in data['next_actions']:
    if action['requirement']=='IMPORT-02':
        action['action']='Extend native Source parent-child ordering17→18/26→27 from the bounded native8 product integration:96actual UI/fan/Off/Record/Undo/HAS/export checks plus180headless lifecycle/stale-binding checks. Only1of49rules is active on the exact qualified Junko profile; current complete Windows default and updated owner review are pending. Earlier fullf0dd/review passes are separate. Preserve normal-fidelity failure and SDK/artist/same-actor ragdoll limits; deferred manual observations do not block independent work.'
assert before == [(r['id'],r['implementation'],r['acceptance_status']) for r in data['requirements']]
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
benchmark = ROOT / 'docs/benchmarks/native_source_readiness_2026-11-15.json'
record = json.loads(benchmark.read_text(encoding='utf-8'))
assert 'latest_product_increment' not in record
record['latest_product_increment']={'path':'docs/benchmarks/native_source_live_2026-11-15.json','scope':'One rule product GUI96 then later state180; old experiments above remain scoped to their earlier source; fresh current full-default pending'}
benchmark.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Scoped evidence added; all stable IDs and status pairs preserved.')
