"""Record the closed later failure; never promote a partial full run to PASS."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-fe9aace-20261117T040348'
load = lambda p: json.loads(p.read_bytes())
state = load(RUN / 'state.json')
release = load(RUN / 'graphics-lease-closed.json')
assert state['status'] == 'failed' and state['source_unchanged'] is True and release['released'] is True
assert release['physical_jobs'] == 68 and release['receipt_inventory_sha256'] == hashlib.sha256((RUN / 'terminal-audit-attempt1/receipt-inventory.json').read_bytes()).hexdigest() == '90a3c1b10a5fc4fed2196be7c720e26ff899b41b0b47b0a12248dddfe7729cb6'
inventory = load(RUN / 'terminal-audit-attempt1/receipt-inventory.json')
assert (inventory['normal_exit0'], inventory['registered_cancel_exit2'], inventory['failed_partial_nonzero']) == (67, 1, 0)
current = '''LATEST: fe9 complete default FAILED04:27:26.4771603Z, source1029 unchanged.
Root closed68private jobs(67exit0+Krita cancel2), exact inline/birth/source/scopes,
released04:29:31.8232736Z; inventory90a3c1b10a5fc4fed2196be7c720e26ff899b41b0b47b0a12248dddfe7729cb6.
The full passed the formerly failing Source foundation, imported shapes/base
shapes/animated shapes, helper save/export, shortcut/camera/import stages before
verify_shape_catalog.py referenced a dead old-worktree Mima bundle. Its existing
fixture_output() import is used for VRM but bypassed by face=ROOT/output. Root's
retained sfm-face-pilot descriptor points to the current valid prepared Mima;
the stale historical descriptor is preserved, not silently rewritten/substituted.

NEXT: review the minimal fixture_output() source successor and scan for the same
descriptor bypass in later wrappers. Preserve all native cases/assertions. Root
must qualify the actual current Mima descriptor/bundle against its recorded hashes
and prior52 inputs, then run actual focused shape catalogue plus affected later
wrappers before another full. Native lane free/root-only; no product merge.
The prior fixture-only CRLF correction remains qualified167/separate77+96; no
application source changed since the reviewed Neon fixes. Contextfe9 terminal
helper was executed already; never reuse it for a successor run.

'''
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
text = text.replace('# HAS continuation — November 17, 2026\n', '# HAS continuation — November 17, 2026\n\n' + current, 1)
text = text.replace('CURRENT at ', 'HISTORICAL RUNNING OBSERVATION at ', 1)
path.write_text(text, encoding='utf-8', newline='\n')
paragraph = '''\n### November17 2026 —fe9 full closed at stale SFM descriptor path\n\nThe fe9 default stopped04:27:26.4771603Z with1029source unchanged, after Source
foundation/shapes/base/animation and all preceding reviewed stages passed.
verify_shape_catalog.py uses fixture_output() for VRM inputs but still reads its
Mima face descriptor fromlocaloutput, selecting a stale old-worktree path. Root
has the retained current Mima preparation used by the prior52 route; a minimal
fixture-root source correction and broader bypass scan are being prepared. No
native geometry/file replacement or full PASS is inferred. Root audited68private
jobs(67exit0+Krita cancel2), exact inline/source/birth/scopes and closed desktops,
released04:29:31.8232736Z; inventory90a3c1b10a5fc4fed2196be7c720e26ff899b41b0b47b0a12248dddfe7729cb6.
No failed private job is invented for the missing-file exception before catalogue
unit/GPU launch. Previous CRLF fixture success remains167/separate77+96. MainE8
backup/readback and exact71publiccachecleanup remain recorded. Product unmerged;
manualDEFERRED,55/62 and52/54 unchanged. Current pickup gives the concrete next task.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['historical_fe9_active'] = bench['latest_observation']
bench['latest_observation'] = {'state': state, 'full': 'FAILED_STALE_LOCAL_MIMA_DESCRIPTOR_PATH', 'source_files_unchanged': 1029,
    'closed_physical_private_jobs': 68, 'normal_exit0': 67, 'Krita_cancel_exit2': 1, 'failed_private_jobs': 0,
    'released_utc': release['released_utc'], 'inventory_sha256': release['receipt_inventory_sha256'],
    'product_source_changed': False, 'main_merged': False, 'manual_owner_result': 'DEFERRED_NO_RESULT'}
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Closedfe9 fullfails staleMima descriptorlocalpath afterSource foundation/shapes/base/animation passes; source1029/68privatejobsclosed. '
    'Reviewfixture_output() minimalfix+remainingwrapper scan, qualifyretainedMima actualinputs andfocusedcatalogue beforefullsuccessor/merge. '
    'Publishcompletedsource/evidence/cleanup; normals/PMX/scale scoped/inactive,manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Recorded closedfe9 stale-fixture failure; no full PASS or merge.')
