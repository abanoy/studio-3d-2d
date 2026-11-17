"""Record the owner's redesign priority without changing application sources."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
note='''\n## 2026-11-16 — Owner-requested Neon Pro review in progress

Owner identified claude/studio-redesign and approved the Midnight Neon / Iridescent
Pro mock, asking for review and Windows verify.py before merge. Fetched exact
c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2 into a separate detached checkout:
C:\\a\\Programming\\cloudflare\\has-neon-review-20261116-c2d52ff.
Its29-file delta against52f contains no test edits. Do not modify frozen source
while the current full verifier runs. Preserve the theme when fixing behaviour.

Original-branch full Windows run started2026-11-17T00:09:14.2629655Z in
output/windows-neon-c2d52ff-20261117T000859 under that checkout; root coordinator
21008 was born00:09:13.8701953Z. Prior owned graphics workers were absent. Graphics
remain exclusively on private desktops. This is RUNNING, not a Windows pass.
Source review has identified hidden Simple simulation entry points, F11 shortcut
precedence and an invisible fading-toast mouse target; these are under review,
not fixes applied to the running candidate. The unchanged wind manifest also
pins pre-redesign app/pose bytes; any successor requires explicit source review
and keeps all original predicates. Do not bypass it to manufacture a pass.

Completed native-five full/review/normal evidence was published as
2ca4b663edf17eb7837c7166a8f3db602df58ec6. Independently fetched three critical
progress files match raw bytes and Git blob hashes. No cleanup yet; original
assets, shared tools and both previous owner reviews remain protected.

The next normal setter probe is sealed/source-audited (38 CPU methods), but
Blender execution waits behind this redesign run. Six-foot corrected JSON
transport is likewise source-only: root's first successor setup refused CIM
access before engines or source staging, leaving attempt2 reserved. Keep the
444/7 actual failure and this setup refusal distinct; later execution needs a
fresh attempt under the approved host context. No normalization is activated.
No manual result or acceptance-score change is inferred.
'''
for name in ('LLM.md','docs/progress_memo.md'):
    p=ROOT/name
    if '## 2026-11-16 — Owner-requested Neon Pro review in progress' not in p.read_text(encoding='utf-8'):
        with p.open('a',encoding='utf-8',newline='\n') as f:f.write(note)
p=ROOT/'docs/NEXT_SESSION_PLAN_2026-11-16.md';body=p.read_text(encoding='utf-8')
if 'Current priority: review the owner-approved Neon Pro branch' not in body:
    body=body.replace('Continue independent work.', 'Current priority: review the owner-approved Neon Pro branch before merge and\nrun its Windows verifier. See the appended history and\n`experiments/neon_windows_original_20261116/PREPARATION.json`.\n\nContinue independent work.',1)
p.write_text(body,encoding='utf-8',newline='\n')
p=ROOT/'docs/completion_checklist.json';doc=json.loads(p.read_bytes())
before={r['id']:{k:v for k,v in r.items() if k not in ('remaining','evidence')} for r in doc['requirements']}
for row in doc['requirements']:
    if row['id']=='IMPORT-02':row['remaining']='Main five-rule subset has266state/102GUI and complete Windows157-group PASS on52f;187software review checks pass. Preserve broader49/SDK/shader/artist limits and the original native-normal failure. Current owner-requested Neon Pro branch must pass its independent Windows review before merge; human review remains deferred.'
    if row['id']=='IMPORT-03':row['remaining']='Continue native fidelity and standardization independently: five native joints are qualified and full Windows52f passes. Remaining44rules/SDK/shader/artist fidelity, raw normals, active six-foot classification/runtime/helper integration, PMX physics reconstruction and capability audit remain unfinished. Human observation remains deferred.'
doc['next_actions'][0]['action']='Review owner-approved claude/studio-redesign atc2d52ff in the separate checkout, fix evidenced regressions preserving neon layout, run complete Windows verify.py before merge, publish compact results. Preserve original52f fullPASS, native-normal failure, inactive six-foot prototypes and all deferred human checks.'
assert before=={r['id']:{k:v for k,v in r.items() if k not in ('remaining','evidence')} for r in doc['requirements']}
p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Recorded Neon review priority; all stable statuses/dependencies unchanged.')
