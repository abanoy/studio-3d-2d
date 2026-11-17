"""Record focused success and dated active startup metadata; raw logs stay private."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-696ca7f-20261117T170720480423'
PACKET = ROOT / 'experiments/neon_windows_696ca7f_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda p: json.loads(p.read_bytes())
state_raw = (RUN / 'state.json').read_bytes()
state = json.loads(state_raw)
assert state['status'] == 'running' and state['source_commit'] == '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
assert state['pid'] == 12740 and state['process_started'] == '2026-11-17T17:07:54.3896834Z'
before = load(RUN / 'source-before.json')['source_sha256']
assert len(before) == 1029 and all(sha((REVIEW / n).read_bytes()) == pin for n, pin in before.items())
focus_path = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1/verification.json'
assert sha(focus_path.read_bytes()) == '9a0a959734ae56925af31a63207ba711ff6443fe44b38ef8f14425f64aa6bb4c'
focus = load(focus_path)
assert focus['passed'] and focus['all_functional_source_unchanged'] and focus['host_scopes_closed']
target = PACKET / 'active-observation'
target.mkdir(exist_ok=False)
files = []
for name in ('launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'source-before.json', 'preflight-source.json', 'state.json'):
    raw = state_raw if name == 'state.json' else (RUN / name).read_bytes()
    (target / name).write_bytes(raw)
    files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw), 'dated_snapshot_only': name == 'state.json'})
assert (RUN / 'state.json').read_bytes() == state_raw
record = {'observed_utc': datetime.now(timezone.utc).isoformat(), 'result': 'RUNNING_NO_RESULT', 'state': state,
    'functional_sources_unchanged': 1029, 'actual_focused': {'camera': 60, 'native_models': 5, 'neon': 12504, 'controls': 48},
    'focused_sha256': sha(focus_path.read_bytes()), 'public_metadata_files': files,
    'expected_not_pass': {'groups': 158, 'core': 36, 'movies': 21}, 'root_native_lane': 'exclusive',
    'raw_native_report_or_logs_included': False, 'product_merged': False}
(target / 'OBSERVATION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
paragraph = '''
### November 17, 2026 — camera fix focused PASS and696 full active

Root applied exactly one existing refresh_camera_inspector call plus two app
hash rows and committed localcandidate696ca7f1491a43b1a2267a53f8ca0f62b7c211a9.
Actual original camera60/0 with5native models, Neon12504/0 andcontrols48/0 pass:
29.1665295s,51.0870301s,14.5917301s. All1029 source bytes and host scopes preserved.
Focused verification9a0a9597 is retained. No camera assertion or native threshold
was weakened. Five-public-text reconstruction94a74d55 is prepared for main backup;
the app Git blob is already CRLF/exact, four other files use explicit EOL recipes.

Fresh full696 started17:07:54Z with coordinator12740 birth.3896834 andPython5384
birth.8423868,parent12740 (GetProcess); CIM.8423860 is metadata only. Exact8a1c
runner/2a67PWSH and unchanged strict6runtimes/574SourceIOoriginal+copy/120exporter/
36fixtures/currentMima/rawVRM pass. Native lane root-exclusive, source1029/HEAD696
frozen. Expected158/36/21 remains NOT a result. No merge/copy/cold187 is claimed.

Separate read-only B diagnostics remain unqualified: first scope refusal had no
native launch, second stopped at missing support import, third stopped before B
at an unexpected factory handler. The final intentional observation captured
3factory callbacks across11lists to a2005-byte PRIVATE metadata file bf55509b,
without invoking callbacks/openingB/collecting model resources. Its wrapper is
not a resource/private-placement PASS; after-scope0 and tool/input preservation
were observed. No further B native run precedes the UI/full work. All originals
and prior reviews remain protected; Source normal error/2e-5 threshold unchanged.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8').replace('CURRENT: replay2 actual full FAILED', 'PRECEDING: replay2 actual full FAILED', 1)
intro = f'''
CURRENT dated {record['observed_utc']}: candidate696ca7f fullRUNNING, notPASS.
Run output/windows-neon-696ca7f-20261117T170720480423; coordinator12740 birth
2026-11-17T17:07:54.3896834Z; Python5384 GetProcessbirth17:07:54.8423868Z,parent
12740; CIM.8423860 metadataonly. FreezeReview1029files/HEAD696; native lane ROOT
exclusive, no secondengine/native run or source change. Newcontext-only terminal
helper is being prepared; never use00bf/R2 context. Expected158/36/21 NOTsuccess.
Actualfocused camera60/native5,Neon12504,controls48 all0fail with source/scopes
preserved,9a0a9597; originaltests unchanged. Strict fresh6+574original/copy+120+36
and currentMima/rawVRM identities pass. Product/sourcefixonecall+2appmanifestrows.
Five-text-source reconstruction94a74d55 prepared; appGitblobexactCRLF,4LFbridges.

Read-only B before-model factory observation captured3callbacks/11lists without
openingB; allBresources/export/carrier/repair/fidelity remainUNQUALIFIED. Detailed
startup metadata staysPRIVATE; no furtherBnative beforethisfull/copywork closes.
Mainlatestpusheda41a204/runtime1019unchanged; no productmerge/owner-copy/cold187.

'''
heading = '# HAS continuation — November 17, 2026\n'
assert text.count(heading) == 1
path.write_text(text.replace(heading, heading + intro, 1), encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['preceding_replay2_failed'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Monitor frozen696 full1029/12740+5384 actual births; root native lane exclusive. '
    'Camera60/native5+Neon12504+controls48 focusedPASS after onecall+2manifest app rows, predicatesunchanged. '
    'Fresh strict preflight passed. Rootactual terminal/ownership/closure beforemerge/copy/cold187; no result fromexpected158/36/21. '
    'Publish newsource/compactmetadata; rawlogs/arrays private. Bfactory observationonly, no modelresource/fidelity/adoption.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'observed_utc': record['observed_utc'], 'result': record['result'], 'focused_passed': True, 'source_files': 1029}))
