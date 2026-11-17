from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
EXP=HERE.parent;OLD=EXP/'neon_ffcf_terminal_20261117';NEW=EXP/'neon_4ed3_terminal_20261117'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['close_terminal.py','legacy_result_gates.py','test_terminal.py']:
 assert (NEW/name).read_bytes()==(OLD/name).read_bytes(),name
old=json.loads((OLD/'RESULT_REGISTRY.json').read_bytes());new=json.loads((NEW/'RESULT_REGISTRY.json').read_bytes())
assert old.pop('source_commit')=='ffcf4c54ab9ab7af7cb01329a5b3b5b6f4589865';assert new.pop('source_commit')=='4ed3a63b716f696daa1699a76443d6f1abb9b096';assert old==new
pairs={'ffcf4c54ab9ab7af7cb01329a5b3b5b6f4589865':'4ed3a63b716f696daa1699a76443d6f1abb9b096','windows-neon-ffcf4c5-20261117T021833':'windows-neon-4ed3a63-20261117T030209','27512':'22224','27124':'1820','2026-11-17T02:22:31.2361797Z':'2026-11-17T03:02:32.4796950Z','2026-11-17T02:22:31.8526561Z':'2026-11-17T03:02:33.0241444Z','Exact ffcf1029':'Exact 4ed31029','has_neon_ffcf_terminal_source_context_1':'has_neon_4ed3_terminal_source_context_1'}
text=(NEW/'bind_context.py').read_text(encoding='utf-8')
for a,b in pairs.items():assert b in text; text=text.replace(b,a)
assert text==(OLD/'bind_context.py').read_text(encoding='utf-8')
pairs={'2026-11-17T02:22:31.8526560Z':'2026-11-17T03:02:33.0241443Z','2026-11-17T02:22:31.2361790Z':'2026-11-17T03:02:32.4796940Z'}
text=(NEW/'test_bind_context.py').read_text(encoding='utf-8')
for a,b in pairs.items():assert b in text; text=text.replace(b,a)
assert text==(OLD/'test_bind_context.py').read_text(encoding='utf-8')
context=json.loads((NEW/'CONTEXT.json').read_bytes())
assert context['commit']=='4ed3a63b716f696daa1699a76443d6f1abb9b096' and context['functional_sources']==1029
assert context['coordinator_pid']==22224 and context['coordinator_birth']=='2026-11-17T03:02:32.4796950Z'
assert context['python_pid']==1820 and context['python_birth']=='2026-11-17T03:02:33.0241444Z'
assert context['private_job_count']=='DERIVE_ACTUAL_NO_ASSUMPTION'
run=Path(context['checkout'])/'output'/context['run_name']
assert set(context['immutable_run_inputs'])=={'source-before.json','launch.json','root-birth-observation.json','root-birth-api-detail.json'}
for name,digest in context['immutable_run_inputs'].items():assert sha(run/name)==digest
for key,name in [('registry_sha256','RESULT_REGISTRY.json'),('legacy_result_gates_sha256','legacy_result_gates.py')]:assert context[key]==sha(NEW/name)
assert sha(Path(context['checkout'])/'tests/verify.py')==new['verifier_sha256']
source_pins={name:sha(NEW/name) for name in ['close_terminal.py','legacy_result_gates.py','test_terminal.py','bind_context.py','test_bind_context.py','RESULT_REGISTRY.json','CONTEXT.json']}
r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(NEW),'-p','test_*.py','-v'],capture_output=True)
(HERE/'CPU_TESTS.log').write_bytes(r.stdout+r.stderr)
assert r.returncode==0 and b'Ran 25 tests' in r.stderr and b'OK' in r.stderr
assert all(sha(NEW/name)==digest for name,digest in source_pins.items())
report={'format':'has_neon_4ed3_terminal_independent_source_peer_1','status':'PASS_SOURCE_CPU_ONLY','reviewed_sources':source_pins,'immutable_inputs_verified':context['immutable_run_inputs'],'all_other_active_run_reads':False,'source_only_exact_inverses':True,'test_methods':25,'test_failures':0,'cpu_log_sha256':sha(HERE/'CPU_TESTS.log'),'helper_output_labels_inherited_ffcf_no_weakening':True,'process_observers_CIM_engines_Git_run':False,'preliminary_audit_correction':'First ad hoc read used nonexistent test_bind.py and stopped before context checks. Corrected actual name test_bind_context.py, reran complete independent proof; no terminal/runtime or false closure conclusion occurred.'}
(HERE/'CPU_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
