"""Fixture-only candidate/pin+epoch port; all host validation/worker APIs unchanged."""
from pathlib import Path
import hashlib,json,ast,shutil
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-scratch-v5-root-driver-prep-20261121'
C=R/'output/source-junko-scratch-rest-representation-v2-prep-20261121'
D=R/'output/source-junko-scratch-v6-root-driver-prep-20261121'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert pin((S/'SOURCE_PINS.json').read_bytes())['sha256']=='5140f53058ab4dddaedccd2f3428b0ead4af7a97fb009f43d143150b2980b20a'
assert pin((C/'SOURCE_PINS.json').read_bytes())['sha256']=='da54d107aaeddc2684042b9dd0524db0fbcb24ade9235ece108e9a443348054e'
assert not D.exists();D.mkdir()
for path in S.rglob('*'):
 if path.is_file():
  target=D/'bases/v5'/path.relative_to(S);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
for name in ('root_native_job.py','approved_job_layout.py','BASELINE_SOURCE1109.json','gated_converter_worker.py'):(D/name).write_bytes((S/name).read_bytes())
for name in ('SOURCE_PINS.json','ROOT_PROTOCOL.md'):(D/('CANDIDATE_'+name)).write_bytes((C/name).read_bytes())
source=(S/'run_scratch.py').read_text()
changes=[('source-junko-scratch-rest-representation-prep-20261121','source-junko-scratch-rest-representation-v2-prep-20261121'),('9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015','da54d107aaeddc2684042b9dd0524db0fbcb24ade9235ece108e9a443348054e'),('has_junko_scratch_rest_v5_root_1','has_junko_scratch_rest_v6_root_1'),('has-junko-scratch-rest-v5-','has-junko-scratch-rest-v6-'),('junko-scratch-rest-v5.lock','junko-scratch-rest-v6.lock')]
for before,after in changes:assert source.count(before)==1,(before,source.count(before));source=source.replace(before,after)
ast.parse(source);(D/'run_scratch.py').write_text(source,encoding='utf-8')
previous=ast.parse((S/'run_scratch.py').read_text());current=ast.parse(source)
old={n.name:ast.dump(n,include_attributes=False) for n in previous.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};new={n.name:ast.dump(n,include_attributes=False) for n in current.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert set(old)==set(new) and all(old[k]==new[k] for k in old if k!='main')
(D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'README.md').write_text('''# Scratch v6 fixture-only successor

SOURCE ONLY UNRUN. The actual v5 failed0 batch is preserved: one synthetic fake
close callback compared tuple-rest to list-reference;11 individual OK lines are
not batch credit and Blender never started. Candidate v2da54 changes ONLY two
test callbacks to tuple(a)==tuple(b), making positive/negative sequence-content
tests meaningful. Helper10395, native baseline, immutable C.close and22scratch
measurement algorithms remain byte-exact. No production/model/tolerance fix.

Host v6 changes only candidatefolder/pin and stage/format/locklabels. Worker7747,
RootJob/layout and all non-main host functions are byte/AST exactv5. Main still
1109 at exact2f1/23ea baseline. TwoJobs pure12 then one background scratchBlender;
all lifecycle/input/native64/installedAPI/cleanup/exactbaseline/private recompute
gates stay intact. SDK/native models/Godot/app/Full/ownerdata never loaded.

Root source-peer before running pinnedPython-I-S-B run_scratch.py --self-sha256
<driverSHA> --source-manifest-sha256 <manifestSHA> --revision
2f1acbd7867087d9f18cfbc1122cc0c883c5f788 --root-cpu-component-confirmed.

No authorruntime. Originalv5source/actualFAIL0 remainunchanged. No native model
repair/export/54-binding/physics/fidelity or Full qualification is inferred.
''',encoding='utf-8')
(D/'CORRECTION.json').write_text(json.dumps({'status':'SOURCE_ONLY_UNRUN_PENDING_PEER','actual_v5':'FAIL0; oneof12unitfailed; noBlenderstarted','candidate_fix':'Two syntheticcallbacks compare sequencecontents across tuple/list, not container-type equality','candidate_source_sha256':'da54d107aaeddc2684042b9dd0524db0fbcb24ade9235ece108e9a443348054e','all_nonmain_host_functions_AST_identical':True,'worker_and_approved_job_layout_byte_exact':True,'actual_model_algorithm_or_tolerance_changes':False,'pure_count':12,'scratch_measurements':22},indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file() and p!=D/'SOURCE_PINS.json']
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_scratch_v6_fixture_port_source_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':rows},indent=2)+'\n',encoding='utf-8')
assert {r['path'] for r in rows}|{'SOURCE_PINS.json'}=={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}
for row in rows:assert pin((D/row['path']).read_bytes())=={'bytes':row['bytes'],'sha256':row['sha256']}
print(json.dumps({'files':len(rows)+1,'payload_bytes':sum(r['bytes'] for r in rows),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'host':pin((D/'run_scratch.py').read_bytes()),'worker':pin((D/'gated_converter_worker.py').read_bytes()),'CPU_AST_nonmain_reverse_and_exact_closure':'PASS'},indent=2))
