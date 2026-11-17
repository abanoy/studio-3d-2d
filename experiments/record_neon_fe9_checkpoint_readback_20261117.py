"""Record only the independently recovered public checkpoint, without a product merge."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '4ec7b57334ca04aab42d3d4e8a62c12df4858d8c'
PROOF = ROOT / 'experiments/neon_fe9_checkpoint_remote_20261117/COMPLETE_READBACK.json'
raw = PROOF.read_bytes()
proof = json.loads(raw)
assert proof['commit'] == COMMIT and proof['file_count'] == 694
assert proof['bytes'] == 7829487
assert all(row['independent_remote_bytes_exact'] for row in proof['files'])
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == COMMIT
source = json.loads((ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json').read_bytes())['source_sha256']
assert len(source) == 1019
assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == pin for name, pin in source.items())
record = {
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'commit': COMMIT, 'independent_remote_exact_files': 694, 'git_bytes': 7829487,
    'working_EOL_recipes': 2, 'proof_sha256': hashlib.sha256(raw).hexdigest(),
    'main_functional_unchanged': 1019, 'product_redesign_merged': False,
    'review_branch_upload_retried': False, 'new_cleanup_performed': False,
}
target = ROOT / 'experiments/neon_fe9_checkpoint_remote_20261117/ROOT_OBSERVATION.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
paragraph = '''
### November 17, 2026 — Windows source and evidence recovered from GitHub

Checkpoint 4ec7b57334ca04aab42d3d4e8a62c12df4858d8c is pushed to main.
All 694 public files were independently fetched through the GitHub connector
and matched their exact Git blobs: 7,829,487 bytes, with two recorded working
line-ending recipes. This saves the fe9 and 00bf test fixes/reconstruction,
closed failures, focused foundation results, historical 52f source witness,
inactive owner-copy executor and exact 71-cache cleanup record. Private native
models, geometry, artwork and media are excluded. The independent final selection
audit remains outside that checkpoint and will be saved in the next increment.
Main's 1019 functional files still match the qualified 52f baseline. The neon
redesign is not merged, the optional review-branch upload was not retried, and
this publication is not a full Windows pass. The 00bf native lane remains under
root ownership until its actual terminal audit. No further cleanup occurred.
Acceptance 55/62 and implementation 52/54 remain unchanged; human checks deferred.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
heading = '# HAS continuation — November 17, 2026\n'
assert text.count(heading) == 1
current = '''
Latest retrieval checkpoint: main4ec7b57334ca04aab42d3d4e8a62c12df4858d8c.
All694 public files independently fetched/exact Git blobs (7,829,487bytes;
2working-EOL recipes). Proof experiments/neon_fe9_checkpoint_remote_20261117/
COMPLETE_READBACK.json is saved locally for the next checkpoint. This preserves
fe9/00bf source, failure archives, historical52witness, inactive copy executor
and the completed71public-cache cleanup. Main1019 still equals qualified52f;
redesign remains UNMERGED. No additional cleanup or review-branch push occurred.

'''
text = text.replace(heading, heading + current, 1)
text = text.replace('00bf four-text-file reconstructione6837fe4 and parentfe9packet awaitmaincheckpoint.',
                    '00bf four-text-file reconstructione6837fe4 and parentfe9packet are recovered frommain4ec7b57.', 1)
text = text.replace('Main e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a is pushed;',
                    'Earlier checkpoint e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a is pushed;', 1)
path.write_text(text, encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = json.loads(path.read_bytes())
bench['latest_public_checkpoint'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
