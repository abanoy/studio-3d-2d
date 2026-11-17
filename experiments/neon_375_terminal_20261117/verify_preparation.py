"""Source/context inverse proof only; no terminal reads or observers."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'neon_4ed3_terminal_20261117'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((HERE/'SOURCE_DERIVATION.json').read_bytes())
for name in ['close_terminal.py','legacy_result_gates.py','test_terminal.py']:assert (HERE/name).read_bytes()==(OLD/name).read_bytes()
text=(HERE/'bind_context.py').read_text(encoding='utf-8')
adapter=proof['adapter_inverse'];assert text.count(adapter['remove_exact_function_source'])==1
text=text.replace(adapter['remove_exact_function_source'],'')
assert text.count(adapter['main_replacement_to'])==1;text=text.replace(adapter['main_replacement_to'],adapter['main_replacement_from'])
for old,new in reversed(tuple(proof['binder_literal_replacements'].items())):assert new in text;text=text.replace(new,old)
assert text==(OLD/'bind_context.py').read_text(encoding='utf-8')
text=(HERE/'test_bind_context.py').read_text(encoding='utf-8')
for old,new in reversed(tuple(proof['binding_tests_replacements'].items())):assert new in text;text=text.replace(new,old)
assert text==(OLD/'test_bind_context.py').read_text(encoding='utf-8')
old_registry=(OLD/'RESULT_REGISTRY.json').read_bytes();new_registry=(HERE/'RESULT_REGISTRY.json').read_bytes()
assert new_registry.replace(proof['source_commit'].encode(),b'4ed3a63b716f696daa1699a76443d6f1abb9b096')==old_registry
context=json.loads((HERE/'CONTEXT.json').read_bytes());receipt=json.loads((HERE/'BINDING_RECEIPT.json').read_bytes())
assert context['commit']==proof['source_commit'] and context['functional_sources']==1029 and context['result_groups']==158 and context['core_groups']==36 and context['movie_groups']==21
assert context['coordinator_pid']==3032 and context['coordinator_birth']=='2026-11-17T03:31:03.8129380Z'
assert context['python_pid']==26304 and context['python_birth']=='2026-11-17T03:31:04.3344666Z'
assert context['registry_sha256']==sha(HERE/'RESULT_REGISTRY.json') and context['legacy_result_gates_sha256']==sha(HERE/'legacy_result_gates.py')
assert receipt['context_sha256']==sha(HERE/'CONTEXT.json') and receipt['immutable_run_inputs']==context['immutable_run_inputs']
assert set(context['immutable_run_inputs'])=={'source-before.json','launch.json','root-birth-observation.json','root-birth-api-detail.json'}
print(json.dumps({'source_inverses':True,'helper_sha256':sha(HERE/'close_terminal.py'),'context_sha256':sha(HERE/'CONTEXT.json'),'terminal_or_process_observation':False},indent=2))
