"""Prepare exact metadata/source pins only; never inspect this active run's terminal state."""
from pathlib import Path
import ast
import copy
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
RUN=REVIEW/'output/windows-neon-f387d0e-20261117T012410'
OLD=MAIN/'experiments/current_full_receipts_20261116'
COMMIT='f387d0e9ddfb099140c0699d9f7ed430f5d7b949'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def main():
    assert not (HERE/'INDEX.json').exists()
    old_registry=json.loads((OLD/'RESULT_REGISTRY.json').read_bytes())
    old_source=MAIN/'tests/verify.py';new_source=REVIEW/'tests/verify.py'
    assert sha(old_source)==old_registry['verifier_sha256']
    old_ast=ast.parse(old_source.read_bytes());new_ast=ast.parse(new_source.read_bytes())
    stripped=copy.deepcopy(new_ast)
    node=next(node for node in stripped.body if isinstance(node,ast.FunctionDef) and node.name=='main')
    removed=[child for child in node.body if 149<=child.lineno<=158]
    assert len(removed)==10
    node.body=[child for child in node.body if child not in removed]
    assert ast.dump(stripped,include_attributes=False)==ast.dump(old_ast,include_attributes=False),'Any change beyond the exact Neon group needs new review'
    def constants(tree):
        return {item.slice.value for item in ast.walk(tree) if isinstance(item,ast.Subscript) and isinstance(item.value,ast.Name) and item.value.id=='results' and isinstance(item.slice,ast.Constant) and type(item.slice.value) is str}
    assert constants(new_ast)-constants(old_ast)=={'neon_workspace'} and len(constants(new_ast))==78
    registry=copy.deepcopy(old_registry)
    registry.update({'source_commit':COMMIT,'verifier_sha256':sha(new_source),'derivation':'All original registry keys/36 core/21 movies preserved by exact AST inverse of the10-statement Neon group; add only neon_workspace. Native MMD and both posed movie groups remain required.'})
    registry['expected_result_keys']=sorted([*old_registry['expected_result_keys'],'neon_workspace'])
    assert len(registry['expected_result_keys'])==len(set(registry['expected_result_keys']))==158
    assert len(registry['expected_core_process_keys'])==36 and len(registry['expected_movie_keys'])==21
    save('RESULT_REGISTRY.json',registry)
    gates=(OLD/'publication_gates.py').read_bytes()
    with (HERE/'legacy_result_gates.py').open('xb') as stream:stream.write(gates)
    before=json.loads((RUN/'source-before.json').read_bytes())
    assert before['commit']==COMMIT and len(before['source_sha256'])==1028
    assert before['source_sha256']['tests/verify.py']==sha(new_source)
    birth=json.loads((RUN/'root-birth-observation.json').read_bytes())
    assert birth['format']=='has_root_neon_corrected_birth_observation_1'
    assert birth['coordinator']=={'pid':25388,'creation_utc':'2026-11-17T01:27:36.0890696Z'}
    assert birth['python']=={'pid':23904,'parent_pid':25388,'creation_utc':'2026-11-17T01:27:37.1616850Z','command_line':'"C:\\Program Files\\Python313\\python.exe" -u tests/verify.py'}
    launch=json.loads((RUN/'launch.json').read_bytes())
    assert launch['source_commit']==COMMIT and launch['coordinator_pid']==25388 and launch['functional_source_files']==1028
    context={'format':'has_neon_f387_terminal_source_context_1','checkout':str(REVIEW),'run_name':RUN.name,'commit':COMMIT,'functional_sources':1028,
             'coordinator_pid':25388,'coordinator_birth':birth['coordinator']['creation_utc'],'python_pid':23904,'python_birth':birth['python']['creation_utc'],
             'python_executable':r'C:\Program Files\Python313\python.exe','python_command':birth['python']['command_line'],
             'runner':launch['runner'],'runner_sha256':launch['runner_sha256'],
             'powershell':r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe',
             'powershell_sha256':'2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233',
             'registry_sha256':sha(HERE/'RESULT_REGISTRY.json'),'legacy_result_gates_sha256':sha(HERE/'legacy_result_gates.py'),
             'immutable_run_inputs':{name:sha(RUN/name) for name in ('source-before.json','launch.json','root-birth-observation.json')},
             'result_groups':158,'core_groups':36,'movie_groups':21,'private_job_count':'DERIVE_ACTUAL_NO_ASSUMPTION',
             'terminal_state_or_full_report_read_by_preparation':False,'engines_CIM_Git_executed':False}
    assert sha(Path(context['runner']))==context['runner_sha256']
    save('CONTEXT.json',context)
    save('SOURCE_DERIVATION.json',{'format':'has_neon_f387_terminal_source_derivation_1','old_registry_sha256':sha(OLD/'RESULT_REGISTRY.json'),
        'old_verifier_sha256':sha(old_source),'current_verifier_sha256':sha(new_source),'old_registry_keys':157,'current_registry_keys':158,
        'only_added_key':'neon_workspace','old_core36_movie21_named_sets_unchanged':True,'Neon_group_10_statement_AST_inverse_exact':True,
        'legacy_publication_gates_entire_file_byte_exact':sha(OLD/'publication_gates.py')==sha(HERE/'legacy_result_gates.py'),
        'source_manifest_entries':1028,'birth_and_launch_schemas_read_exactly':True,'run_state_after_report_or_log_read':False,'engines_CIM_Git_executed':False})
    print(json.dumps({'context_sha256':sha(HERE/'CONTEXT.json'),'registry_sha256':context['registry_sha256'],'source_only':True}))


if __name__=='__main__':main()
