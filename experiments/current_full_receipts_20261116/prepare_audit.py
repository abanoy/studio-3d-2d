"""Prepare a current-run CPU audit without altering historical schemas or evidence."""
from pathlib import Path
import ast,datetime,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=ROOT/'experiments/resume_full_20261115/publication'
RUN=ROOT/'output/windows-canonical-bone-binding-20261116T041518335'
COMMIT='52f63c944ded7a651da871524d23a345b606424d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,value):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
state=load(RUN/'state.json');birth=load(RUN/'root-birth-observation.json')
assert state['source_commit']==COMMIT and state['status']=='passed' and state['suite_exit']==0 and state['source_unchanged']
assert state['pid']==birth['coordinator_pid']==79488 and birth['python_pid']==91024
source=load(RUN/'source-before.json');assert source==load(RUN/'source-after.json') and len(source['source_sha256'])==1019
registry=load(OLD/'RESULT_REGISTRY.json');registry['source_commit']=COMMIT
save(HERE/'RESULT_REGISTRY.json',registry)
context={'format':'has_current_full_receipt_expectations_1','workspace_root':str(ROOT),'source_commit':COMMIT,'run_name':RUN.name,
    'functional_source_entries':1019,'source_before_sha256':sha(RUN/'source-before.json'),'launch_sha256':sha(RUN/'launch.json'),
    'birth_observation_sha256':sha(RUN/'root-birth-observation.json'),'birth_observation_format':birth['format'],'birth_observation_checked_utc':birth['observed_utc'],
    'expected_result_entries':157,'expected_core_process_groups':36,'expected_root_movie_count':21,
    'coordinator_pid':birth['coordinator_pid'],'coordinator_creation_utc':birth['coordinator_birth'],
    'python_pid':birth['python_pid'],'python_creation_utc':birth['python_birth'],'suite_python_command':birth['python_command'],
    'result_registry_sha256':sha(HERE/'RESULT_REGISTRY.json'),'receipt_counts':'Discover this exact run; no historical total assumed. Exactly one registered Krita cancellation remains required.',
    'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_state_at_preparation':state['status']}
save(HERE/'RUN_EXPECTATIONS.json',context)
old=(OLD/'audit_receipts.py').read_text(encoding='utf-8');audit=old
assert audit.count('coordinator-children-observed.json')==3 and audit.count('children_observation_sha256')==1
audit=audit.replace('coordinator-children-observed.json','root-birth-observation.json').replace('children_observation_sha256','birth_observation_sha256')
assert audit.count("default=TASK/'receipt-audit'")==1
audit=audit.replace("default=TASK/'receipt-audit'","default=ROOT/'output/current-full-receipts-20261116-attempt1'")
audit=audit.replace('assert OUT.parent==TASK and not OUT.exists()',"assert OUT.parent==(ROOT/'output').resolve() and not OUT.exists()")
anchor="result=load(resultpath);Gates.validate_result(result,CONTEXT,REGISTRY)\nOUT.mkdir(exist_ok=False)"
assert audit.count(anchor)==1
extra="""result=load(resultpath);Gates.validate_result(result,CONTEXT,REGISTRY)
normalized=Gates.read(resultpath).decode('utf-8-sig').replace('\\r\\n','\\n').rstrip()
canonical_log=Gates.read(RUN/'canonical.log').decode('utf-8-sig').replace('\\r\\n','\\n').rstrip()
assert canonical_log.endswith(normalized),'Exact normalized canonical log/report suffix required'
assert all(not line.strip() or line.startswith('PASS ') for line in canonical_log[:-len(normalized)].splitlines()),'Unexpected canonical log prefix'
current={p.relative_to(ROOT).as_posix() for name in ('src','tests','tools','data','examples') for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
current.update(('project.godot','main.tscn','run.py','launch.pyw'))
assert current==set(before['source_sha256']),'Current functional source membership differs'
for name,digest in before['source_sha256'].items():
 p=(ROOT/name).resolve();assert p.is_relative_to(ROOT.resolve()) and hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Current functional source bytes differ: '+name
OUT.mkdir(exist_ok=False)"""
audit=audit.replace(anchor,extra)
gates=(OLD/'publication_gates.py').read_text(encoding='utf-8')
start=gates.index('def validate_live(');end=gates.index('\n\ndef validate_raw_host',start)
new_live='''def validate_live(run, context):
    """Validate the actual new flat root-birth observation, never a fake old alias."""
    raw = read(run / 'root-birth-observation.json')
    require(sha(raw) == context['birth_observation_sha256'], 'Root birth identity observation changed')
    value = json.loads(raw)
    require(value['format'] == context['birth_observation_format'] == 'has_root_full_child_birth_observation_1'
            and value['source_commit'] == context['source_commit']
            and value['coordinator_pid'] == context['coordinator_pid']
            and value['coordinator_birth'] == context['coordinator_creation_utc']
            and value['python_pid'] == context['python_pid'] and value['python_parent'] == context['coordinator_pid']
            and value['python_birth'] == context['python_creation_utc']
            and value['python_command'] == context['suite_python_command']
            and value['observed_utc'] == context['birth_observation_checked_utc']
            and Path(value['run_folder']) == run, 'Exact current coordinator/Python birth observation differs')
'''
gates=gates[:start]+new_live+gates[end:]
needle="    validate_live(run, context)\n    return value"
assert gates.count(needle)==1
gates=gates.replace(needle,"""    require(value['root_birth_observation_sha256'] == context['birth_observation_sha256']
            and value['functional_source_entries'] == context['functional_source_entries']
            and value['source_before_after_and_current_exact'] is True
            and value['root_observer_issued_no_termination'] is True, 'Current raw host/source/birth binding differs')
    require(flat['functional_source_entries'] == context['functional_source_entries']
            and flat['source_before_after_and_current_exact'] is True
            and flat['root_observer_issued_no_termination'] is True, 'Current flat host/source binding differs')
    validate_live(run, context)
    return value""")
for name,text in [('audit_receipts.py',audit),('publication_gates.py',gates)]:
    ast.parse(text);(HERE/name).write_text(text,encoding='utf-8',newline='\n')
save(HERE/'PREPARATION.json',{'format':'has_current_full_receipt_audit_preparation_1','source_only':True,'historical_audit_sha256':sha(OLD/'audit_receipts.py'),'historical_gates_sha256':sha(OLD/'publication_gates.py'),
    'audit_sha256':sha(HERE/'audit_receipts.py'),'gates_sha256':sha(HERE/'publication_gates.py'),'registry_named_sets_unchanged':{k:registry[k]==load(OLD/'RESULT_REGISTRY.json')[k] for k in ('expected_result_keys','expected_core_process_keys','expected_movie_keys')},
    'adaptation':'Bind actual flat root-birth schema and observed current context; keep all original result/receipt/isolation/Krita checks. Add log suffix/current membership+byte gates; write output only inside owned output.',
    'actual_runtime_or_CIM_or_Git_performed':False,'CPU_audit_executed_by_preparation':False})
print(json.dumps({'prepared':str(HERE),'audit_sha256':sha(HERE/'audit_receipts.py'),'gates_sha256':sha(HERE/'publication_gates.py')}))
