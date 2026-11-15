"""Index this new output only. Never modifies Git, cleanup roots or prior-v1 evidence."""
from pathlib import Path
import hashlib,json
HOME=Path(__file__).absolute().parent
assert HOME==Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\sfm-v2-code-cleanup-executor-20261113-v2')
OLD=HOME.with_name('sfm-v2-code-cleanup-executor-20261113')
OLD_SHA='dd9d3cc1cb001890d1bbd93207187e4078d691e88c2a22d41c6d47b03c48873a'
RECEIPT='receipt-20261113T1840164784783Z-5b2026675bf345d4a7b781b14a48ce88.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def identity(path):
    raw=path.read_bytes()
    return {'path':path.relative_to(HOME).as_posix(),'bytes':len(raw),'sha256':sha(raw)}
def verify_rows(folder,packet):
    for row in packet['files']:
        raw=(folder/row['path']).read_bytes()
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256'],row['path']
def main():
    raw=(OLD/'PACKET.json').read_bytes()
    assert sha(raw)==OLD_SHA and raw==(HOME/'prior-v1/PACKET.json').read_bytes()
    old=json.loads(raw);verify_rows(OLD,old);verify_rows(HOME/'prior-v1',old)
    executor=identity(HOME/'execute-sfm-v2-cleanup.ps1');helper=identity(HOME/'verify-git.py')
    host=read(HOME/RECEIPT)
    assert host['mode']=='DRY_RUN' and host['executor_sha256']==executor['sha256'] and host['helper_sha256']==helper['sha256']
    assert host['candidate_files_checked']==4308 and host['retained_files_checked']==2613
    assert host['file_preflight_passed'] and host['preflight_membership_passed'] and host['retained_recheck_passed']
    assert host['status']=='PREFLIGHT_FAILED_NO_DELETION' and not host['deletion_invoked'] and host['deleted_files']==host['deleted_bytes']==0
    process=host['last_process_check'];unknown=process['unknown_live_owned_or_runtime_processes']
    assert len(process['matching_processes'])==0 and len(unknown)==199
    tests=read(HOME/'synthetic-v2-35-final.stdout.json')
    assert tests['passed'] and tests['tests']==35 and tests['executor_sha256']==executor['sha256']
    assert tests['test_source_sha256']==identity(HOME/'test-safety.ps1')['sha256']
    tests_path=Path(tests['fixture_root'])/'TESTS.json'
    assert tests_path.is_relative_to(HOME) and read(tests_path)==tests
    preload=[]
    for name,case in (('native-preload-forged-final.json','Forged'),('native-preload-legitimate-reuse-final.json','LegitimateReuse')):
        value=read(HOME/name)
        assert value['passed'] and value['expected_refusal'] and value['case']==case and not value['execute_invoked']
        assert value['executor_sha256']==executor['sha256'] and value['test_source_sha256']==identity(HOME/'test-native-preload.ps1')['sha256']
        assert '-NoProfile' in value['command_line'] and value['process_id']>0 and value['process_creation_ticks']>0
        preload.append(identity(HOME/name)|value)
    tools=[]
    for path in (Path(r'C:\Program Files\Python313\python.exe'),Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'),Path(r'C:\Program Files\Git\cmd\git.exe')):
        data=path.read_bytes();tools.append({'path':str(path),'bytes':len(data),'sha256':sha(data)})
    result={
      'format':'has_sfm_v2_cleanup_executor_v2_preparation_results_1',
      'status':'READ_ONLY_FILE_GATES_PASS_NONUSE_REFUSED_EXECUTE_UNRUN',
      'executor':executor,'git_helper':helper,'deletes_moves_kills_or_git_mutation':False,
      'prior_v1':{'original_packet_sha256':OLD_SHA,'original_packet_and_all12_indexed_files_byte_unchanged':True,'compact_packet_exact_copy':'prior-v1/PACKET.json','initial_failures_and_prior_results_retained_exactly':True},
      'changes_from_v1':[
        'Every live unresolved owner is unknown regardless of session. Unknown SID cannot establish another account.',
        'SfmCleanupNativeV2 refuses any preloaded type before Add-Type, including legitimate prior loads. A fresh process is required.',
        'Paths target this separate v2 output. No target scope, process exception, tolerance or Execute bypass was added.'],
      'synthetic_controls':identity(tests_path)|{'passed':True,'tests':35,'executor_sha256':tests['executor_sha256'],'test_source_sha256':tests['test_source_sha256']},
      'fresh_noprofile_preloaded_type_process_negatives':preload,'raw_git_proof':read(HOME/'git-local-proof-final.json'),
      'actual_fresh_host_default_preflight':identity(HOME/RECEIPT)|{k:host.get(k) for k in ('mode','status','executor_sha256','helper_sha256','started_utc','finished_utc','candidate_files_checked','retained_files_checked','file_preflight_passed','preflight_membership_passed','retained_recheck_passed','deletion_invoked','deleted_files','deleted_bytes','publication_status','errors','unrun')},
      'actual_host_process_gate':{'processes':process['processes_in_snapshot'],'observed_uses':len(process['matching_processes']),'unknowns':len(unknown),'inaccessible':len(process['inaccessible_processes']),'unknown_confirmed_owned':sum(bool(x['owner_checked'] and x['owned']) for x in unknown),'unknown_owner_unresolved':sum(not x['owner_checked'] for x in unknown),'exceptions_added':False,'all_open_file_handles_enumerated':False,'local_full_receipt_not_in_compact_publication':True},
      'runtime_executable_files':tools,'runtime_hash_limit':'Executable files only; complete installed dependency trees are not hashed.',
      'separate_source_counterfactuals':{
        'status':'SOURCE_ANALYSIS_ONLY_NOT_A_CLEANUP_OR_HOST_NONUSE_RESULT',
        'v1_other_session_case':'V1 omits owner-unresolved non-runtime identities outside the current session. V2 synthetic live-current-PID/wrong-creation/different-session row becomes unknown and refuses.',
        'v1_preloaded_type_case':'V1 skips Add-Type when a same-named type exists. V2 actual fresh-process controls separately reject forged and legitimately loaded resident types.',
        'v1_counterfactual_executor_invocation':'UNRUN; no old executor Execute or cleanup was invoked.'},
      'limits_and_unrun':[
        'No Execute invocation or successful overall preflight.199 current unknown identities remain blockers; no usable cleanup authorization is claimed.',
        'Exact remote publication/checkpoint gates remain unrun until root supplies reviewed published values.',
        'No inaccessible owner/system/helper process is excluded or bypassed. No process is killed.',
        'Per-file full audits may take hours during Execute; gates were not weakened for speed.',
        'Original directory IDs were not captured by the frozen plan; IDs are pinned per invocation.',
        'Path-based checks/removal are not atomic against hostile concurrent changes; arbitrary handle freedom is not proven.',
        'Post-deletion proof and all actual deletion behavior remain unrun.']}
    (HOME/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    names=['README.md','HANDOFF.md','RESULTS.json','execute-sfm-v2-cleanup.ps1','verify-git.py','test-safety.ps1','test-native-preload.ps1','audit-processes-only.ps1','freeze-v2-packet.py','git-local-proof-final.json','native-preload-forged-final.json','native-preload-legitimate-reuse-final.json',tests_path.relative_to(HOME).as_posix(),'prior-v1/PACKET.json']
    names.extend('prior-v1/'+x['path'] for x in old['files'])
    files=[identity(HOME/name) for name in names]
    packet={'format':'has_sfm_v2_cleanup_executor_v2_packet_1','status':result['status'],'files':files,'total_bytes':sum(x['bytes'] for x in files),'execute_invoked':False,'local_full_process_receipt_and_synthetic_fixture_payloads_excluded_from_publication':True,'v1_packet_preserved_sha256':OLD_SHA}
    (HOME/'PACKET.json').write_text(json.dumps(packet,indent=2)+'\n',encoding='utf-8',newline='\n')
    verify_rows(HOME,packet)
    print(json.dumps({'packet':identity(HOME/'PACKET.json'),'files':len(files),'bytes':packet['total_bytes'],'executor':executor,'helper':helper,'host_unknowns':199,'synthetic_controls':35}))
if __name__=='__main__':main()
