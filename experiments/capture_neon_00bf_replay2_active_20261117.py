"""Dated public startup metadata only; never capture the private canonical log."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051'
PACKET = ROOT / 'experiments/neon_windows_00bf0f9_replay2_20261117-20261117T155709412051'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
state_raw = (RUN / 'state.json').read_bytes()
state = json.loads(state_raw)
assert state['status'] == 'running' and state['source_commit'] == '00bf0f916a549f5e858cb39dd91a149071fd5181'
assert state['pid'] == 19808 and state['process_started'] == '2026-11-17T15:58:55.2656645Z'
before = json.loads((RUN / 'source-before.json').read_bytes())
assert len(before['source_sha256']) == 1029
assert all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before['source_sha256'].items())
target = PACKET / 'active-observation'
target.mkdir(exist_ok=False)
files = []
for name in ('launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'source-before.json', 'preflight-source.json', 'state.json'):
    raw = state_raw if name == 'state.json' else (RUN / name).read_bytes()
    (target / name).write_bytes(raw)
    files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw), 'dated_snapshot_only': name == 'state.json'})
assert (RUN / 'state.json').read_bytes() == state_raw
record = {'observed_utc': datetime.now(timezone.utc).isoformat(), 'result': 'RUNNING_NO_RESULT',
    'state': state, 'functional_sources_unchanged': 1029, 'public_metadata_files': files,
    'root_native_lane': 'exclusive', 'expected_not_pass': {'groups': 158, 'core': 36, 'movies': 21},
    'raw_logs_or_native_model_arrays_included': False, 'redesign_merged': False}
(target / 'OBSERVATION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
paragraph = '''
### November 17, 2026 — unchanged strict host preflight and fresh replay2 active

The identical strict preparation passed in the approved Windows host context:
6runtimes,574SourceIO originals and matching owned copy,120exporter sources,
36native fixtures and additional currentMima/rawVRM identities. No predicate or
lock was relaxed. Separate default-context diagnostics captured one ffprobe
attribute transition0x40020→0x20, with every other stamp field and locked content
identity equal; all6 tools passed the second diagnostic round. This does not
identify the cause of the earlier uncaptured Pythonw/FFmpeg refusals.

Fresh replay2 started using the exact8a1c canonical runner and pinned2a67 PWSH.
Coordinator19808 birth15:58:55.2656645Z; Python8888 birth15:58:55.9596269Z,parent
19808, original tests/verify.py command. CIM.9596260 is metadata, not identity.
All1029 functional bytes remain frozen at00bf; expected158/36/21 is not success.
The new native lane is root-exclusive; no second engine or source/HEAD change.

Correction to the earlier backup-rule note: the actual terminal helper writes
under REVIEW/output/<run>/terminal-audit-attempt1, already excluded by output/.
The redundant experimental-path ignore rule was removed. Raw successful reports,
canonical logs and terminal audits stay private; no such payload was uploaded.
The old interrupted state remains untouched and is not converted into a result.
No full PASS, merge, fresh owner copy or actual startup187 is claimed.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
text = text.replace('CURRENT: old00bf full is INTERRUPTED_NO_TERMINAL_RESULT', 'PRECEDING: old00bf full is INTERRUPTED_NO_TERMINAL_RESULT', 1)
text = text.replace('The exact .gitignore rule protects terminal-audit-attempt* under the00bf helper;\n+only an independently reviewed explicit scalar projection may be selected.'.replace('\n+', '\n'),
                    'Actual terminal audits stay under REVIEW/output, already ignored by output/.\nOnly an independently reviewed explicit scalar projection may be selected.')
intro = f'''
CURRENT dated {record['observed_utc']}: freshsame00bf replay2 RUNNING, notPASS.
Run output/windows-neon-00bf0f9-replay2-20261117T155709412051; coordinator19808
GetProcessbirth15:58:55.2656645Z, Python8888 GetProcessbirth15:58:55.9596269Z,
parent19808; CIM.9596260 metadataonly. Freeze1029functional files/HEAD00bf.
Rootnative lane exclusive; no secondnative/engine. Newcontext-only terminalhelper
is beingprepared; neverreuse interrupted predecessor context. Exactunchanged
strict host preflight6+574original/copy+120+36 and currentMima/rawVRM passed.
Expected158/36/21 are not observedPASS totals. Rawlogs/fullreport/audits private
under REVIEW/output; existing output/ ignore applies. Oldexperimental-path
ignore rule was redundant and removed, without publishing private data.

'''
heading = '# HAS continuation — November 17, 2026\n'
assert text.count(heading) == 1
text = text.replace(heading, heading + intro, 1)
path.write_text(text, encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = json.loads(path.read_bytes())
bench['preceding_interrupted00bf'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = json.loads(path.read_bytes())
ledger['next_actions'][0]['action'] = ('Monitor frozen00bf replay2 full1029 (19808/8888 precise births); native lane root-exclusive. '
    'Unchanged strict host preflight passed6+574original/copy+120+36/currentMima/rawVRM. '
    'Root fresh terminal/source/ownership/closure audit before merge; old interrupted run no terminal/PASS. '
    'Publish source/scalar progress only; raw full/logs/audits private under output. Copy/cold187 inactive; manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'observed_utc': record['observed_utc'], 'full': record['result'], 'source_files': 1029,
    'coordinator': 19808, 'python': 8888, 'raw_logs_copied': False}))
