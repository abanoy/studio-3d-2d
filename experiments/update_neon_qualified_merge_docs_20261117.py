"""Record the actual accepted Windows full and current qualified merge preparation."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
record = json.loads((ROOT / 'experiments/neon_3a_mmd_full_pass_actual_20261117/RESULT.json').read_bytes())
assert record['full_suite_passed'] is True and record['result_groups'] == 158
entry = '''
## 2026-11-17 — complete native Windows Neon PASS and qualified merge

The restored-MMD full finished21:00:57.9135725Z, verifier exit0, with all158 result
groups,36 core groups,21 movies, actualMMD45, Neon12504, camera60 and color44.
Root's unchanged strictf223 audit PASSED;196 physical private jobs closed
(195 exit0, one registered Krita cancellation). Source1029 remained exact.
Inventory a4b47b3b; public scalar packet941e9aea. Original157-group run stays
UNQUALIFIED. Runtimes6, SourceIO574 original+copy, exporter120, original36fixtures
and41 additional pinned inputs were unchanged in the post-run audit.

Before merging, corrected B runtime8272/eacc completed7.527s exit0/reaped with
source/input/tool preservation and zero scopes. Its resource profile correctly
remains refused: two unused internal Viewer images account for four issues and
one repeated unclassified reference accounts for two. Reference owner/type/content
remain unobserved. Export branch UNKNOWN; no normal repair/fidelity/adoption.
Future inspection needs the tested1029 Main bridge after this merge, not old52.

Root reviewed the supplied mock/app images and39 canonical source changes, then
prepared the nonfastforward merge of3a3701a into Mainf21b9ec. All31 new ancestral
commits/152 novel blobs were inspected by path scope: no private/native/media
payload; seven PNG versions are the already approved mock/app screenshots.
Only LLM conflicted; both conflict additions were retained, and both complete
parent versions remain available through merge ancestry. Exact tested raw1029
bytes were restored under the explicit Git/EOL bridge (113 text files); originals,
old output/cache dirt and all Git shell-script LF blobs were preserved.

Build admission needs a narrow source-only EOL successor: three declared Linux
scripts are testedCRLF on Windows and committedLF for Linux. Add only those three
text paths, rederive only their canonical delta hashes, retain all39 raw changes
and reasons, strictfull gates and binary/content refusals. Studio source/tests
are unchanged. Qualified owner copy and actual cold187 remain UNRUN; preserve
the final merged HEAD unchanged through activation/copy/cold validation.

Mainf21b9ec was independently retrieved:113 exact public files,3,213,295 Git bytes,
3,234,655 working bytes, three EOL recipes; COMPLETE proofca28ba8c. The initial
empty oversize progress response was refused; actual Git-blob endpoint retrieval
corrected only that cached fallback. Raw native reports/counts/art remain private.
Source-only copy/validator preparation607c/8fc4 and proposals e717/dabd/b2df are
ready for the next checkpoint. Human acceptance remains deferred; stable52/54
implementation and55/62 acceptance stay unchanged. No new cleanup or installation.
'''
for name in ('LLM.md', 'docs/progress_memo.md', 'docs/RESUME_MASTER_PLAN.md'):
    path = ROOT / name
    raw = path.read_bytes()
    assert b'complete native Windows Neon PASS and qualified merge' not in raw
    newline = '\r\n' if raw.count(b'\n') == raw.count(b'\r\n') else '\n'
    with path.open('ab') as stream: stream.write(entry.replace('\n', newline).encode('utf-8'))
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
value = json.loads(path.read_bytes())
assert 'qualified_native_full_20261117' not in value
value['qualified_native_full_20261117'] = record
path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
value = json.loads(path.read_bytes())
before = [(r['id'], r['implementation'], r['verification'], r['acceptance_status']) for r in value['requirements']]
value['next_actions'][0]['action'] = 'Actual restored-MMD Neon full PASSED158/core36/movie21, MMD45/Neon12504; strictf223 audit closed196 jobs/source1029 exact (public941e9aea). Qualified Main merge prepared with both histories and exact tested1029 raw bytes. Complete the narrow three-script EOL admission chain, actual fresh owner copy and cold187 while keeping finalmergedHEAD fixed. B8272 diagnostic completed but resource profile refused; future B work needs tested1029 context bridge. Native-normal fidelity/human acceptance remain unqualified/deferred.'
next(r for r in value['requirements'] if r['id'] == 'UI-01')['evidence'].append({
    'kind': 'test_result', 'path': 'experiments/neon_3a_mmd_full_pass_actual_20261117/RESULT.json',
    'scope': 'Actual complete Windows158/36/21 and nativeMMD45 passed, Neon12504, camera60/color44. Strict196 private job/source/process closure and protected inputs pass. Qualified merge/build preparation is separate from unrun owner-copy/cold187 and deferred human observation.'})
assert before == [(r['id'], r['implementation'], r['verification'], r['acceptance_status']) for r in value['requirements']]
path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
print('Recorded full PASS and qualified merge preparation; requirement statuses unchanged.')
