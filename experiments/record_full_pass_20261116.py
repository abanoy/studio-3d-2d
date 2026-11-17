"""Record the completed full run without changing functional source or HEAD."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
packet=ROOT/'experiments/native_five_full_actual_20261116'
def load(p):return json.loads(p.read_bytes())
assert hashlib.sha256((packet/'INDEX.json').read_bytes()).hexdigest()=='757146330ae801d5a2bd11d2f9b594babd665c64291f61f33b0115f048cedd1e'
benchmark=load(packet/'BENCHMARK.json')
assert benchmark['status']=='PASSED_COMPLETE_DEFAULT_AND_ROOT_GRAPHICS_RELEASE' and benchmark['private_jobs']==192 and benchmark['functional_source_files']==1019
target=ROOT/'docs/benchmarks/native_five_full_2026-11-16.json'
with target.open('xb') as f:f.write((packet/'BENCHMARK.json').read_bytes())
entry='''

## 2026-11-16 — Complete Windows regression passes on five-joint main

Source52f63c944ded7a651da871524d23a345b606424d passes the complete default:
157result groups,36core groups and21movie groups in3122.8353009seconds.
All1019functional sources and HEAD remain exact. The earlier dbf timeout stays
failed; the bounded snapshot fix passes its unchanged28checks inside this full.
Exact owned coordinator79488 and Python91024 births are observed absent by root
at23:24:54Z. Actual receipt audit derives192unique private jobs:191exit0 and one
exact source-registered Krita cancellation exit2. Every job/desktop is closed;
all inline receipts match. Root strict graphics release passes23:28:46Z.
The observer issued no termination; controlled test cancellation is separate.

Compact public archive experiments/native_five_full_actual_20261116 is sealed
with INDEX757146330ae801d5a2bd11d2f9b594babd665c64291f61f33b0115f048cedd1e.
It contains192physical receipts and safe157/36/21 extracts; raw full report,
models/media and native arrays remain in private output. Root separately passes
690archive checks plus4privacy negative controls; these are not product tests.
All757changed checkpoint files have already been read back from GitHub exactly.

On resumption, normal-probe preflight first refuses a transient ffmpeg file-stamp
change before creating a stage. Cause remains UNDETERMINED. Three subsequent
before/open/after/final observations match every stamp and approved SHA; the
unchanged complete preflight then passes. No identity gate or runtime changed.
The first background Blender capture completes2meshes/9661vertices/42702corners,
but its private wrapper exits2 for unverified desktop placement (no GUI window).
The job/desktop are physically closed and root-owned native processes absent.
That probe remains failed and comparison unrun. An isolated hidden placement
sentinel is being source-reviewed; original capture/math and wrapper gates stay
unchanged. No normal-fidelity improvement or causal attribution is claimed.

New owner review preparation proposes187 checks and a fresh sibling folder;
its copy-only builder is in progress, not yet a qualified deliverable. Old review
and owner work remain protected. Six-foot contract/GDScript/boundary prototypes
and their independent reviews remain isolated and inactive. Formal55/62 and
implementation52/54 stay unchanged; owner manual review remains DEFERRED/noresult.
'''
for name in ('LLM.md','docs/progress_memo.md'):
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as f:f.write(entry)
p=ROOT/'docs/completion_checklist.json';d=load(p)
stable=[(x['id'],x['implementation'],x['acceptance_status'],x['external_dependencies']) for x in d['requirements']]
for row in d['requirements']:
    if row['id'] in ('IMPORT-02','IMPORT-03'):
        row['evidence'].append({'kind':'test_result','path':'docs/benchmarks/native_five_full_2026-11-16.json','scope':'Complete Windows default passes on52f source1019:157groups/36core/21movies,192closed privatejobs; bounded native5 qualification remains separate, original normal gate and deferred human result unchanged.'})
d['next_actions'][0]={'priority':0,'requirement':'IMPORT-03','action':'Complete the independently staged normal diagnostic and new187-check review after actual full52f PASS/closure. Preserve failed background placement attempt; qualify sentinel placement before using capture. Publish all completed compact evidence/source, verify remote, then review exact disposable cleanup. Keep six-foot normalization isolated until domain/runtime/helper parity passes; do not wait on parked manual checks.'}
assert stable==[(x['id'],x['implementation'],x['acceptance_status'],x['external_dependencies']) for x in d['requirements']]
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'benchmark':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'full_pass_recorded':True}))
