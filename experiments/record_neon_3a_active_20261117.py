"""Publish only dated boot/source metadata; full logs and native arrays stay private."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
RUN=REVIEW/'output/windows-neon-3a3701a-20261117T185401541257';PACKET=ROOT/'experiments/neon_windows_3a3701a_20261117'
load=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest()
raw=(RUN/'state.json').read_bytes();state=json.loads(raw)
assert state['status']=='running' and state['source_commit']=='3a3701ab6edfa81dc883759403c170b8555aab07'
assert state['pid']==19500 and state['process_started']=='2026-11-17T18:59:01.8851457Z'
before=load(RUN/'source-before.json')['source_sha256'];assert len(before)==1029
assert all(digest((REVIEW/n).read_bytes())==v for n,v in before.items())
api=load(RUN/'root-birth-api-detail.json');assert api['python_pid']==3592 and api['python_get_process_birth']=='2026-11-17T18:59:02.3970713Z'
scope=load(RUN/'prelaunch-owned-scope.json');assert scope['owned_count']==0 and not scope['termination_issued']
dest=PACKET/'active-observation';dest.mkdir(exist_ok=False);files=[]
for name in ('launch.json','root-birth-observation.json','root-birth-api-detail.json','source-before.json','preflight-source.json','prelaunch-owned-scope.json','state.json'):
 content=raw if name=='state.json' else (RUN/name).read_bytes();(dest/name).write_bytes(content)
 files.append({'path':name,'bytes':len(content),'sha256':digest(content),'dated_snapshot_only':name=='state.json'})
assert (RUN/'state.json').read_bytes()==raw
record={'observed_utc':datetime.now(timezone.utc).isoformat(),'result':'RUNNING_NO_RESULT','state':state,'functional_sources_unchanged':1029,
 'actual_focused':{'color_checks':44,'color_failures':0,'late_wrappers':44,'late_failed_wrappers':0},
 'ancestor696_not_fresh3a':{'camera':60,'native_models':5,'neon':12504,'controls':48},'public_metadata_files':files,
 'expected_not_pass':{'groups':158,'core':36,'movies':21},'root_native_lane':'exclusive','raw_native_report_or_logs_included':False,'product_merged':False}
(dest/'OBSERVATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
paragraph='''
### November 17, 2026 — 3a full Windows verification active

Fresh3a preflight passed the original6runtimes,574SourceIO original+copy,
120exporter,36nativefixture,currentMima/rawVRM and unchanged8a1c/Pwsh guards.
Focused color44/0 and the exact44 later wrappers/canonical extra checks passed;
ancestor696camera/neon/controls remain separately labeled historical evidence.

Root launched the pinned hidden coordinator at18:59:01UTC. Run is
windows-neon-3a3701a-20261117T185401541257: coordinator19500 GetProcessbirth
2026-11-17T18:59:01.8851457Z; Python3592 GetProcessbirth18:59:02.3970713Z,
parent19500. CIM birth.3970710 is metadata only. Source1029/HEAD3a are frozen;
the native/graphics lane is Root-exclusive. Expected158/core36/movie21 is not
a result. Root terminal audit/actual closure still precedes merge/copy/cold187.

B inspection was deferred: its preparation refused the installed Git tool's
existing2links despite exact approved46480B/mtime/SHA5445 identity. No B engine
or admission was started. A narrow Git-only source successor is in preparation;
do not change installed tools or model-file link checks. PMX oracle phase closed
with1/4 witnesses and3 table-budget refusals; no candidate phase ran. Source-only
diagnostics continue while this full runs. All private/native data stay out of Git.
'''
for name in ('LLM.md','docs/progress_memo.md'):
 with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(paragraph)
path=ROOT/'docs/NEXT_SESSION_PLAN_2026-11-17.md';text=path.read_text(encoding='utf-8')
intro='''
LATEST CURRENT:3a fullRUNNING from18:59UTC. RUN=Review/output/windows-neon-3a3701a-20261117T185401541257.
Coordinator19500 birth2026-11-17T18:59:01.8851457Z; Python3592 birth2026-11-17T18:59:02.3970713Z,parent19500;
CIM.3970710 metadataonly. Freeze1029/HEAD3a. Native/graphicslaneRoot-exclusive:
NOotherengine/nativejob orReviewfunctional/HEAD mutation until actualterminal.
Fullpreflightpassed; color44/0 andTail44 actualPASS; expected158/36/21 NOTresult.
Newcontext-only terminalhelper beingprepared fromeecf. OnlyRootobservesactual
terminal/closesreceipts/releases; do not reuse696/00bf context. No merge/copy/187.
NativePMXoracle1/4,3table-budgetrefusals,preserved4/4,allchildrenclosed; candidate
comparisonblocked. Bneverlaunched: preparerGit-onlysingle-linkpolicyrefusal
(tool2links/exactapprovedidentity). Sourcefix/diagnostics maycontinue, noactual
nativeobservations until fullclosed. Main855retrievable67files; functionalMain52.

Everything below is dated historical context superseded by this active snapshot.

'''
heading='# HAS continuation — November 17, 2026\n';assert text.count(heading)==1
path.write_text(text.replace(heading,heading+intro,1),encoding='utf-8',newline='\n')
path=ROOT/'docs/benchmarks/neon_review_2026-11-17.json';bench=load(path);bench['preceding_tail44_pass']=bench['latest_observation'];bench['latest_observation']=record
path.write_text(json.dumps(bench,indent=2)+'\n',encoding='utf-8',newline='\n')
path=ROOT/'docs/completion_checklist.json';ledger=load(path);ledger['next_actions'][0]['action']='Monitor frozen3a full1029/coordinator19500+Python3592 actualGetProcessbirths/rootexclusive lane; expected158/36/21 notPASS. Strict6+574original/copy+120+36+Mima/rawVRM preflightPASS;color44/Tail44 focusedPASS. Actualterminalaudit/receipt/source/processclosure beforemerge/newreview/cold187. Keepprivatearrays/logsoutofGit. Source-only PMXbudget/BGit-tool fixes continue; noothernativejob.'
path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'result':record['result'],'source_files':1029,'coordinator':19500,'python':3592,'private_arrays_copied':False}))
