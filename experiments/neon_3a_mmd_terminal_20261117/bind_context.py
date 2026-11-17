"""Bind only root-approved launch/birth/source-before metadata; no terminal reads."""
from pathlib import Path
import calendar
import datetime
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
COMMIT='3a3701ab6edfa81dc883759403c170b8555aab07'
RUN_NAME='windows-neon-3a3701a-mmd-20261117T200622956559'
RUN=REVIEW/'output'/RUN_NAME
COORDINATOR={'pid':21536,'creation_utc':'2026-11-17T20:07:58.6062857Z'}
PYTHON={'pid':2976,'parent_pid':21536,'creation_utc':'2026-11-17T20:07:59.1058242Z',
        'command_line':'"C:\\Program Files\\Python313\\python.exe" -u tests/verify.py'}
RUNNER=MAIN/'experiments/neon_windows_original_20261116/run_canonical_owned.ps1'
RUNNER_SHA='8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4'
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
INPUTS=('source-before.json','launch.json','root-birth-observation.json','root-birth-api-detail.json')


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def typed_same(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(typed_same(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(typed_same(x,y) for x,y in zip(a,b))
    return a==b


def ns(value):
    match=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z',value or '')
    require(match is not None,'Exact UTC required')
    return calendar.timegm(datetime.datetime.strptime(match[1],'%Y-%m-%dT%H:%M:%S').timetuple())*10**9+int((match[2] or '').ljust(9,'0'))


def safe(path):
    path=Path(path).absolute();require('..' not in path.parts,'Traversal refused')
    for item in (path,*path.parents):
        if item.exists():require(not item.is_symlink() and not getattr(item.lstat(),'st_file_attributes',0)&0x400,'Reparse path refused')
    return path.resolve()


def read_input(name):
    require(name in INPUTS,'Only immutable launch/birth/source-before inputs allowed')
    path=safe(RUN/name);require(path.parent==safe(RUN),'Wrong metadata scope')
    before=path.stat();require(before.st_size<=64*1024*1024,'Metadata bound')
    raw=path.read_bytes();after=path.stat()
    require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Metadata changed during read')
    value=json.loads(raw,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite metadata')))
    return value,hashlib.sha256(raw).hexdigest()


def validate(before,launch,birth,api,verifier_sha):
    require(type(before) is dict and before.get('commit')==COMMIT and type(before.get('source_sha256')) is dict and len(before['source_sha256'])==1029,'Exact 3a1029 source manifest required')
    for name,digest in before['source_sha256'].items():
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and type(digest) is str and re.fullmatch('[a-f0-9]{64}',digest),'Malformed source identity')
    require(before['source_sha256'].get('tests/verify.py')==verifier_sha,'Verifier/source-before mismatch')
    require(birth.get('format')=='has_root_neon_corrected_birth_observation_1' and typed_same(birth.get('coordinator'),COORDINATOR) and typed_same(birth.get('python'),PYTHON),'Exact nested root-approved birth differs')
    require(ns(PYTHON['creation_utc'])>=ns(COORDINATOR['creation_utc']),'Child predates parent')
    require(launch.get('format')=='has_root_neon_full_launch_1' and launch.get('source_commit')==COMMIT and type(launch.get('coordinator_pid')) is int and launch['coordinator_pid']==COORDINATOR['pid'] and launch.get('coordinator_creation_utc')==COORDINATOR['creation_utc'],'Exact launch identity differs')
    require(launch.get('run_folder')==str(RUN) and type(launch.get('functional_source_files')) is int and launch['functional_source_files']==1029 and launch.get('runner')==str(RUNNER) and launch.get('runner_sha256')==RUNNER_SHA and launch.get('graphics_lease')=='root-exclusive','Approved runner/run/source/lease differs')
    require(api.get('format')=='has_root_python_birth_api_observation_1' and type(api.get('pid')) is int and api['pid']==PYTHON['pid'] and api.get('get_process_start_time_utc')==PYTHON['creation_utc'] and api.get('terminal_identity_api')=='Get-Process.StartTime, same as pinned creation_utc','Birth API metadata differs')
    ns(api.get('cim_creation_utc'))


def adapt_actual_api_detail(api):
    """Strict projection of the actual new raw schema; raw metadata stays pinned."""
    keys={'format','identity_api','precision','python_pid','python_get_process_birth','python_CIM_birth','CIM_birth_not_used_for_identity'}
    require(type(api) is dict and set(api)==keys,'Exact actual API-detail keys required')
    require(api['format']=='has_root_birth_api_detail_1' and api['identity_api']=='Get-Process.StartTime' and api['precision']=='100ns','Actual API-detail schema/API/precision differs')
    require(type(api['python_pid']) is int and api['python_pid']==PYTHON['pid'] and api['python_get_process_birth']==PYTHON['creation_utc'],'Actual GetProcess identity differs')
    require(api['CIM_birth_not_used_for_identity'] is True and type(api['python_CIM_birth']) is str,'CIM must remain non-identity metadata')
    ns(api['python_CIM_birth'])
    return {'format':'has_root_python_birth_api_observation_1','pid':api['python_pid'],
            'get_process_start_time_utc':api['python_get_process_birth'],
            'cim_creation_utc':api['python_CIM_birth'],
            'terminal_identity_api':'Get-Process.StartTime, same as pinned creation_utc'}


def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    require(not (HERE/'CONTEXT.json').exists() and not (HERE/'BINDING_RECEIPT.json').exists() and not (HERE/'INDEX.json').exists(),'Fresh unsealed binding only')
    registry=json.loads((HERE/'RESULT_REGISTRY.json').read_bytes())
    require(registry['source_commit']==COMMIT and len(registry['expected_result_keys'])==158 and len(registry['expected_core_process_keys'])==36 and len(registry['expected_movie_keys'])==21,'Registry scope differs')
    values={};pins={}
    for name in INPUTS:values[name],pins[name]=read_input(name)
    api_identity=adapt_actual_api_detail(values['root-birth-api-detail.json'])
    validate(values['source-before.json'],values['launch.json'],values['root-birth-observation.json'],api_identity,registry['verifier_sha256'])
    require(sha(REVIEW/'tests/verify.py')==registry['verifier_sha256'],'Current verifier changed')
    require(sha(safe(RUNNER))==RUNNER_SHA and sha(safe(PWSH))==PWSH_SHA,'Approved runner/observer executable changed')
    context={'format':'has_neon_3a_terminal_source_context_1','checkout':str(REVIEW),'run_name':RUN_NAME,'commit':COMMIT,'functional_sources':1029,
        'coordinator_pid':COORDINATOR['pid'],'coordinator_birth':COORDINATOR['creation_utc'],
        'python_pid':PYTHON['pid'],'python_birth':PYTHON['creation_utc'],
        'python_executable':r'C:\Program Files\Python313\python.exe','python_command':PYTHON['command_line'],
        'runner':str(RUNNER),'runner_sha256':RUNNER_SHA,'powershell':str(PWSH),'powershell_sha256':PWSH_SHA,
        'registry_sha256':sha(HERE/'RESULT_REGISTRY.json'),'legacy_result_gates_sha256':sha(HERE/'legacy_result_gates.py'),
        'immutable_run_inputs':pins,'result_groups':158,'core_groups':36,'movie_groups':21,
        'private_job_count':'DERIVE_ACTUAL_NO_ASSUMPTION','birth_identity_api':'Get-Process.StartTime',
        'terminal_state_or_full_report_read_by_preparation':False,'engines_CIM_Git_executed':False}
    for name,digest in pins.items():require(sha(safe(RUN/name))==digest,'Immutable metadata changed before binding')
    save('CONTEXT.json',context)
    save('BINDING_RECEIPT.json',{'status':'ACTUAL_IMMUTABLE_LAUNCH_BINDING_ONLY_TERMINAL_UNREAD',
        'context_sha256':sha(HERE/'CONTEXT.json'),'immutable_run_inputs':pins,
        'root_approved_exact_birth_coordinates':True,'same_GetProcess_birth_API_as_terminal_observer':True,
        'raw_CIM_precision_detail_pinned_without_using_CIM_as_identity':True,
        'run_state_source_after_logs_or_full_report_read':False,'process_query_or_engine_or_Git_run':False})
    print(json.dumps({'context_sha256':sha(HERE/'CONTEXT.json'),'immutable_inputs':len(pins),'terminal_unread':True},indent=2))


if __name__=='__main__':main()
