from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
qualified=json.loads((OUT/'IMPORT_OFF_FOLLOWUP_QUALIFIED_20261121.json').read_bytes())
benchmark=ROOT/'docs/benchmarks/import_off_followup_2026-11-21.json'
assert not benchmark.exists();benchmark.write_text(json.dumps(qualified,indent=2)+'\n',encoding='utf-8')
ledger=ROOT/'docs/completion_checklist.json';old=ledger.read_bytes();before=json.loads(old)
key='latest_default_off_followup_20261121';assert key not in before
record={'source_base':'435dc02426a7cdd313e43fe674c9008520845428','functional_sources':1103,
 'scope':'Default-Off imports and explicit-On lesson/height/scenario routes; exact sample-wire test-only correction.',
 'status':'Scoped routes pass; canonical435 Full failed and new committed1103 Full remains required.',
 'evidence':'docs/benchmarks/import_off_followup_2026-11-21.json',
 'new_software_observations':'height native15; importphysics54; completefirstmovie/resume; scenarioD28pure+30writer+4cold/49physicalframes/exactmoviePCM.',
 'full435':'FAIL1961.792s;1102source+HEADunchanged;113privatejobsclosed; new626editor/camera checks pass before old default-On expectation.',
 'experiments':'Easing69+96headless; bounds43; weights171; admission24. Not adopted or native-qualified. Junko105 preflight refused before execution; old native435hosts gated.',
 'formal_status_changed':False,'scores':'52/54 implementation;55/62 acceptance','human_device_observations_substituted':False}
insertion=json.dumps({key:record},indent=2)[1:-2].encode('utf-8')
new=b'{'+insertion+b','+old[1:]
parsed=json.loads(new);assert all(parsed[k]==v for k,v in before.items())
assert parsed['requirements']==before['requirements'] and len(parsed['requirements'])==62
ledger.write_bytes(new);assert ledger.read_bytes().endswith(old[1:])
path=ROOT/'docs/windows_acceptance_followup.md';raw=path.read_bytes()
anchor=b'This configured development PC is not a clean-install result.'
assert raw.count(anchor)==1
append='''

## Windows retrieval note — 2026-11-21

Use a new session-owned checkout with local Git options `core.autocrlf=false`
and `core.longpaths=true` set before checkout. The accumulated historical source
archive includes paths beyond Windows Git's default path limit. Do not change
the owner's global Git settings. For example:

    git -c core.autocrlf=false -c core.longpaths=true clone --config core.autocrlf=false --config core.longpaths=true https://github.com/abanoy/studio-3d-2d.git C:/a/Programming/cloudflare/has-new-session

The configured-PC Full at435dc024 failed an old native-height expectation of
automatic Physics On. It preserved1102 functional sources/HEAD and closed all113
private jobs; its626 new editor/camera checks passed. Imports correctly default
Off. The follow-up explicitly teaches/tests On then Off, preserves old failures,
fixes the scenario test's variable-size selection coordinates, and adds28 exact
sample-wire controls. Scoped height/import/lesson/scenario routes pass. A fresh
committed1103-source Full is still required; no new human/device or clean-install
acceptance is inferred. See the current ledger and follow-up benchmark.
'''.replace('\n','\r\n').encode()
with path.open('ab') as stream:stream.write(append)
assert path.read_bytes()==raw+append
section='''
## 2026-11-21 scoped follow-up qualified; fresh1103 Full next

Current source has1103 functional files: one production change clarifies the beginner Physics On/Off instruction, five existing functional files updated overall and one new28-control sample-wire test. Import/simulator/persistence behavior and numeric/pixel/contact thresholds are unchanged. Exact current source catalogue is output/IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json. Four scoped routes now pass in composed, explicitly recorded runs: height105writer+native15+cold; importphysics54/five native models; completefirstmovie and freshresume/media; scenarioD28pure+30writer+4cold with all49sampleframes and49physical states checked. Final D contactsLocal12/World6, horizontalmovement1.48990666866302m, exact GPU/movie/PCM and offline-writer-cache cold replay pass. All executed private jobs close; old failed batches remain.

The D raw47 scale string differed by one f64 step but all7399 values preserve originalf32 bits and equalparse domains are bit-identical across49. The new test-only oracle compares exact canonical text plus independent f32/structure/identity, evaluates all49 without shortcircuit, and has28 negative controls including samef32/differentcanonicalf64 refusal. No epsilon was added and no production sampler/parser was changed. Source/runtime peer and structural proof are in output/source-scenario-d-wire-prep-20261121 (227d1bf5f140ae559495e9654e21de173fcef9829899d3faeef542c52de7db3a). Current3otherx2testhelpers intentionally use Camera Focus or Draw, independently audited; leave them unchanged.

Historical435 Full remains FAIL1961.792s, no fresh aggregate. Newsource requires commit/push, exact remote verification, fresh isolated longpath-enabled/autocrlf-disabled checkout,13staged fixture inputs, private per-run user dirs and unchanged canonical Full182. Newbenchmark docs/benchmarks/import_off_followup_2026-11-21.json and newledger record retain stable62IDs/52of54implementation/55of62acceptance. Do not admit private Miku/face native435hosts with the failed proof; port their source/revision/catalogues explicitly after a new successful Full. Easing69+96, bounds43, weights171 and admission24 remain separate experiments, no Main adoption.

Root's first Junko105 runtime attempt refused preflight before Job/Godot/any assertion because Node's recorded32-bit volume ID differs from Python's native64-bit ID for identical files. All3327 runtime bytes and five other identity fields match; both executable hashes match and Python infers executable mode bits. Original seal/refusal are preserved. A new explicit producer-identity bridge with independent native64/raw-mode before/after checks is being source-reviewed; no guard waiver or originalseal rewrite. The sealed435 synthetic prototype is independent of CurrentMain and native6part alignment remains unrun. Keep earlier review/private native inputs protected; prepared435 review is not qualified and has old lesson instructions. No owner prompts.
'''.replace('\n','\r\n').encode()
rows=[]
for name in ('LLM.md','docs/progress_memo.md','docs/RESUME_MASTER_PLAN.md','docs/NEXT_SESSION_PLAN_2026-11-20.md'):
    p=ROOT/name;prefix=p.read_bytes();assert b'scoped follow-up qualified; fresh1103 Full next' not in prefix
    with p.open('ab') as stream:stream.write(section)
    assert p.read_bytes()==prefix+section
    rows.append({'path':name,'prefix_bytes':len(prefix),'prefix_sha256':hashlib.sha256(prefix).hexdigest(),'appended_bytes':len(section)})
(OUT/'IMPORT_OFF_DOCS_AND_LEDGER_20261121.json').write_text(json.dumps({'format':'has_followup_docs_1','status':'RECORDED_SCOPED_PASS_FULL_REQUIRED',
 'prior_ledger_suffix_preserved':True,'all62requirement_records_unchanged':True,'history_prefixes':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'DOCUMENTED_SCOPED_PASS_NEW_FULL_REQUIRED','functional_sources':1103,'formal_scores_unchanged':True}))
