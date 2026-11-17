"""Record exact remote recovery of the public checkpoint, without a merge claim."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'experiments/neon_restart_source_checkpoint_remote_20261117/COMPLETE_READBACK.json'
raw = path.read_bytes()
proof = json.loads(raw)
assert proof['commit'] == 'a41a204bffb98614abfa80e0e6340078b1d719f1'
assert proof['file_count'] == 195 and proof['bytes'] == 4439113
assert all(row['independent_remote_bytes_exact'] for row in proof['files'])
assert sum(row['working_recipe']['kind'] != 'exact' for row in proof['files']) == 4
record = {'observed_utc': datetime.now(timezone.utc).isoformat(), 'commit': proof['commit'],
    'independent_remote_exact_files': 195, 'Git_bytes': 4439113, 'working_EOL_recipes': 4,
    'proof_sha256': hashlib.sha256(raw).hexdigest(), 'product_redesign_merged': False,
    'new_cleanup_performed': False, 'review_branch_upload_retried': False}
with (path.parent / 'ROOT_OBSERVATION.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
paragraph = '''
### November 17, 2026 — restart/source checkpoint recovered from GitHub

Maina41a204bffb98614abfa80e0e6340078b1d719f1 is pushed. Every195 selected
public file was independently fetched and exactly matched its Git blob:
4,439,113bytes with4 working-EOL recipes. It preserves the interrupted-run
source/scalar recovery, actual strict-preflight findings, R2 startup metadata,
inactive cold187 adapter, PMX integration map and public-projection source.
The independent selection peer remains outside that checkpoint for the next
increment. No private full report/log/native model/media was published. No new
cleanup or review-branch retry occurred. Main functional1019 still equals52f;
the actual R2 full remains a separate frozen00bf qualification, not a merge.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
text = text.replace('Latest retrieval checkpoint: main4ec7b57334ca04aab42d3d4e8a62c12df4858d8c.',
    'Latest retrieval checkpoint: maina41a204bffb98614abfa80e0e6340078b1d719f1.\nAll195 selected public files independently recovered/exact Git blobs\n(4,439,113bytes/4working-EOL recipes). Proof is in the local\nneon_restart_source_checkpoint_remote_20261117 folder for the next increment.\nThe earlier main4ec7b57 checkpoint was also independently recovered:', 1)
path.write_text(text, encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = json.loads(path.read_bytes())
bench['latest_public_checkpoint'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
