"""Record the actual focused native passes and a dated running full observation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-00bf0f9-20261117T044200'
PACKET = ROOT / 'experiments/neon_windows_00bf0f9_20261117'
load = lambda p: json.loads(p.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
initial = (RUN / 'state.json').read_bytes()
state = json.loads(initial)
assert state['status'] == 'running' and state['source_commit'] == '00bf0f916a549f5e858cb39dd91a149071fd5181'
before = load(RUN / 'source-before.json')['source_sha256']
assert len(before) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before.items())
focused = load(REVIEW / 'output/neon-catalogue-00bf0f9-20261117-attempt1/verification.json')
assert focused['passed'] is True and focused['all_functional_source_unchanged'] is True and focused['host_scopes_closed'] is True
assert [(row['label'], row['report']['checks']) for row in focused['rows']] == [('catalogue', 130), ('comparison', 94), ('height', 105)]
assert focused['rows'][2]['report']['native_import'] == {'checks': 9, 'failures': 0}
snapshot = PACKET / 'active-observation'
snapshot.mkdir(exist_ok=False)
files = []
for name in ('launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'source-before.json', 'preflight-source.json', 'state.json', 'canonical.log'):
    raw = initial if name == 'state.json' else (RUN / name).read_bytes()
    (snapshot / name).write_bytes(raw)
    files.append({'path': name, 'source_path': str(RUN / name), 'bytes': len(raw), 'sha256': sha(raw), 'snapshot_only': name in ('state.json', 'canonical.log')})
assert load(RUN / 'state.json') == state, 'Terminal changed during active observation'
now = datetime.now(timezone.utc).isoformat()
record = {'format': 'has_root_neon_00bf_active_observation_1', 'observed_utc': now, 'state': state, 'files': files,
    'functional_sources_unchanged': 1029, 'actual_focused_checks': {'catalogue': 130, 'unit': 34, 'comparison': 94, 'height': 105, 'raw_VRM': 9},
    'expected_not_pass': {'groups': 158, 'core': 36, 'movies': 21}, 'full_result': 'RUNNING_NO_RESULT', 'main_merged': False,
    'review_branch_upload': 'NOT_ATTEMPTED_AFTER_PRIOR_REJECTION', 'main_reconstruction_publication': 'PENDING'}
(snapshot / 'OBSERVATION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
current = f'''CURRENT at {now}:00bf0f9 complete Windows run is RUNNING, not PASS.
Run output/windows-neon-00bf0f9-20261117T044200 started04:42:33Z. Coordinator21216
GetProcessbirth04:42:33.4387679Z; Python16808 GetProcessbirth04:42:33.9446445Z,
parent21216; CIMrounded.9446440 is metadata only. Freeze Review1029 functional
files and HEAD00bf0f9; native lane root-exclusive, no second native/engine launch.
Context-only terminal helper is being prepared. Independently observe terminal,
then audit fresh full/report/source/actualjobs/inline/birth/private closure. Do
not assume any prior job count or158/36/21 expected totals are successful results.

The two test selectors are committed: catalogue uses existing fixture_output()
forMima; height imports it for its rawVRM descriptor. No product source changes,
no predicate/native-case/threshold removal. Two11-method CPU reviews pass;303file
source scan found no other registered input bypass. Actual catalogue130+unit34
passes all7plans including SuppliedMima; comparison94/6native andheight105/6native
plusrawVRM9 pass. Times37.6931239/43.6109725/48.1988992s, source1029 same/scopeszero.
CurrentMima7,830,992B/e9b21 matches retaineddescriptor and exact priorMain52 plan;
the missing different historicalb577 bundle is not substituted. Strict fresh6
runtimes/574SourceIOoriginal+copy/120exporter/36fixtures pass; extra currentMima,
descriptors/rawVRM identities are pinned. Review-branch upload not attempted;
00bf four-text-file reconstructione6837fe4 and parentfe9packet awaitmaincheckpoint.

''' 
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
text = text.replace('# HAS continuation — November 17, 2026\n', '# HAS continuation — November 17, 2026\n\n' + current, 1)
text = text.replace('LATEST: fe9 complete default FAILED', 'PRECEDING: fe9 complete default FAILED', 1)
text = text.replace('NEXT: review the minimal fixture_output()', 'Completed source/focused correction (current00bf above): minimal fixture_output()', 1)
path.write_text(text, encoding='utf-8', newline='\n')
paragraph = f'''\n### November17 2026 —00bf native catalogue/height passes and active full\n\nAt {now}, frozen00bf0f9 full is RUNNING from04:42:33Z. Coordinator21216
birth04:42:33.4387679Z; Python16808 birth04:42:33.9446445Z,parent21216(GetProcess;
CIMrounded notID). Source1029 unchanged/root native lane exclusive. Only two
test fixture selectors differ fromfe9, no product or assertions change. Actual
catalogue130+unit34/all7plans includingMima, comparison94/6native, height105/6native
andrawVRM9 pass with sources same/scopesclosed. CurrentMima identity matches its
retaineddescriptor and prior52plan, not a historicalb577 substitution. Fresh
6runtimes+694support+36fixtures and additionaldescriptor/Mima/rawVRM identities
pass.00bf reconstructionpacket is prepared for main publication; no review-branch
push attempted, full expected158/36/21 not success. Installed/oldreviews/assets
preserved, no merge. Cleanup71complete; source witness/copyexecutor remain scoped
and inactive. ManualDEFERRED;55/62 and52/54 unchanged.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = load(path)
bench['preceding_fe9_terminal'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = load(path)
ledger['next_actions'][0]['action'] = ('Monitoractive00bf full/frozen1029source after actualcatalogue130/unit34/comparison94/height105/rawVRM9 passes; testselectorsonly. '
    'Rootfreshterminal/source/birth/privateownership audit beforemerge. Publish00bf+fe9reconstruction/closedfailures/scopedevidence/cleanup71; '
    'actualold52witness andcopyexecutor readybutinactiveuntilqualifiedmerge. Native normals/PMX/scale scoped,manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'observed_utc': now, 'full': 'RUNNING_NO_RESULT', 'source_files': 1029, 'focused_all3_passed': True}))
