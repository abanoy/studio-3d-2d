"""Apply exactly the reviewed one-call fix and two app-only manifest pin rows."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_camera_details_visibility_proposal_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert sha((PACKET / 'INDEX.json').read_bytes()) == '9b5cac0bad22877ac840c578253e694b44e65ebc4d77ec5a0fef3dfb0a232ccd'
index = json.loads((PACKET / 'INDEX.json').read_bytes())
for row in index.get('files', index.get('payloads')):
    raw = (PACKET / row['path']).read_bytes()
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
closed = json.loads((ROOT / 'output/native-normal-B-resource-diagnostic-after-failed-full-20261117-attempt4/ROOT_RESULT.json').read_bytes())
assert closed['root_fresh_scopes_closed'] is True and closed['input_source_tool_context_preserved'] is True
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW).strip() == b'00bf0f916a549f5e858cb39dd91a149071fd5181'
baseline = json.loads((REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051/source-after.json').read_bytes())['source_sha256']
assert len(baseline) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in baseline.items())
spec = importlib.util.spec_from_file_location('reviewed_exact_camera_patch', PACKET / 'render_proposal.py')
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)
before = {name: (REVIEW / name).read_bytes() for name in ('src/app.gd', *render.MANIFESTS)}
after = {'src/app.gd': render.render_app(before['src/app.gd'])}
for name in render.MANIFESTS:
    after[name] = render.render_manifest(name, before[name], before['src/app.gd'], after['src/app.gd'])
proposal = json.loads((PACKET / 'PROPOSAL.json').read_bytes())
assert all(sha(after[name]) == proposal['source_hashes'][name]['proposed_sha256'] for name in after)
assert sha((REVIEW / 'tests/camera_range_smoke.gd').read_bytes()) == proposal['camera_range_smoke_sha256']
for name, raw in after.items():
    assert (REVIEW / name).read_bytes() == before[name]
    (REVIEW / name).write_bytes(raw)
current = {name: sha((REVIEW / name).read_bytes()) for name in baseline}
assert {name for name in current if current[name] != baseline[name]} == set(after)
paragraph = '''
## Windows immediate Camera details visibility — November 17, 2026

The unchanged00bf replay2 full failed camera_range60/1 because Advanced near/far
controls were checked before the next process frame. Its parent Camera details
visibility was only refreshed per-frame. One call to the existing guarded
refresh_camera_inspector in refresh_workspace now synchronizes it with Advanced
and mode changes. Values, signals, controls and original test predicates remain
unchanged; classic's empty-inspector guard stays exact. The two reviewed app hash
rows are refreshed in the existing wind/helper manifests; all other rows and
memberships remain exact. Root closed92private jobs/source1029 unchanged before
this patch. Focused graphics and a new complete frozen verifier are still UNRUN.
No full PASS or product merge is claimed.
'''
for name in ('LLM.md', 'docs/REDESIGN-PORT.md'):
    with (REVIEW / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
record = {'observed_utc': datetime.now(timezone.utc).isoformat(), 'baseline_commit': '00bf0f916a549f5e858cb39dd91a149071fd5181',
    'functional_files': 1029, 'sole_functional_changes': {name: {'before': sha(before[name]), 'after': sha(after[name])} for name in after},
    'camera_assertions_unchanged': True, 'actual_post_fix_GPU': 'UNRUN', 'full_PASS_or_merge': False}
target = ROOT / 'experiments/neon_camera_visibility_root_application_20261117.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps(record))
