"""Record the exact completed public-cache operation without a disk-space claim."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads(p.read_bytes())
actual = load(ROOT / 'experiments/public_cache_cleanup_actual_20261117/ACTUAL_RESULT.json')
assert actual['second_attempt'] == 'COMPLETE_EXACT71' and actual['confirmed_deleted_and_currently_absent_files'] == 71
assert actual['confirmed_deleted_logical_bytes'] == 14151060 and actual['new_e8_public_download_caches_retained'] == 27
path = ROOT / 'docs/benchmarks/public_cache_cleanup_2026-11-17.json'
with path.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(actual, stream, indent=2)
    stream.write('\n')
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
start = text.index('Cleanup attempt1 stopped in preflight,0Remove calls/0deleted/uncertainfalse,')
end = text.index('Preceding frozen candidate375ec05', start)
text = text[:start] + '''CLEANUP COMPLETE: first attempt stopped before0remove calls because of a
PowerShell async Git return object. Immutable source/result retained. MinimalV2
suppresses only the unwanted returned value; actual readonlyGit probe passed all
3exactByte[] cases. Root then removed exactly71oldpublic1ce/09fb download caches,
14,151,060logicalbytes, with all predelete/deleted/absence journals independently
checked. This is not a measured free-space claim.27currentE8caches and external
1cefallback remain; no other cleanup authorized. Actual archiveINDEXf97cd275,
RESULTd3ea618c. No further cache action needed; publish this completed record.

''' + text[end:]
text = text.replace('Older public download-cache cleanup71files is being prepared, unexecuted.\nIts originals/models/art/native arrays/oldreviews/tools/current e8cache are excluded.',
    'Oldpublic download-cache cleanup71files is COMPLETE and journaled above.\nOriginals/models/art/native arrays/oldreviews/tools/current e8cache remain excluded.')
path.write_text(text, encoding='utf-8', newline='\n')
paragraph = '''\n### November17 2026 —exact71 public cache cleanup completed\n\nAfter verified publication/readback of1ce/09fb/E8 source and proofs, root removed
only71untracked oldpublic GitHub download caches totaling14,151,060logicalbytes.
The first attempt stopped in preflight with0remove calls and no uncertain effect;
its immutable source/result remain. A one-expression async return suppression
passes actual readonlyGit41byteHEAD/781680byteproof/emptyuntracked Byte[] probes.
The second execution rechecked1402decoded records/proofchain, journaled each file
before/after literal nonrecursive deletion, and observed all71absent. Root then
independently joined every journal/hash/path/absence.27currentE8caches and external
1cefallback remain. No source/private/native/model/review/tool/media paths were
authorized. Actual artifactINDEXf97cd275 and RESULTSHA d3ea618c2438c66554d176a7b164cc84d59999d71625b18d7e8a4ecfbe18cd6d
are retained. No measured disk-free-space gain or whole-PC fresh inventory claim.
Source/application/goal qualifications unchanged; fe9 full continues independently.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['public_cache_cleanup'] = actual
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Monitoractivefe9 full/frozen1029source after actualFoundation167/separate77+96. Rootterminal/source/birth/privateownership audit beforemerge. '
    'Publish fe9reconstruction/completed evidence plus exact71publiccachecleanup(14,151,060logicalB;private/native/source/reviews/tools excluded). '
    'Capture qualifiedmerge proofs then build newreview; normals/PMX/scale scoped/inactive,manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Recorded exact71 cache cleanup; no original/model/tool/review or measured-free-space claim.')
