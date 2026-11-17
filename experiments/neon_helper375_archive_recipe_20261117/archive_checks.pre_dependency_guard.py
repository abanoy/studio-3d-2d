"""Pure scalar/source/private-job joins for the completed375 helper followup."""
import hashlib
import json
from pathlib import PureWindowsPath

ROOT_RUN='output/neon-helper-375ec05-20261117-attempt1/'
REVISION='375ec05e925159850ff3b0abf2e8f98f9d2ce129'
def require(ok,message):
    if not ok:raise ValueError(message)
def typed_same(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(typed_same(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(typed_same(x,y) for x,y in zip(a,b))
    return a==b
def load(raw):
    def pairs(rows):
        out={}
        for k,v in rows:require(k not in out,'Duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def check(raw,bindings,review):
    def obj(path):return load(raw['REVIEW:'+path])
    result=obj(ROOT_RUN+'verification.json')
    require(result['format']=='has_root_neon_helper_followup_1' and result['revision']==REVISION and result['passed'] is True and result['full_suite_pass_claimed'] is False and result['all_functional_source_unchanged'] is True and result['functional_source_files']==1029 and result['host_scopes_closed'] is True,'Root scoped result differs')
    before=obj(ROOT_RUN+'source-before.json');require(len(before)==1029 and typed_same(before,obj(ROOT_RUN+'source-after.json')),'Exact1029 functional preservation differs')
    scopes=[]
    for label in ('before','cpu-after','graphical-after','after'):
        for suffix,fmt,negative in (('-closure.json','has_root_workspace_scope_observation_1',3),('-worker-closure.json','has_root_neon_helper_worker_scope_1',2)):
            v=obj(ROOT_RUN+label+suffix)
            require(v['format']==fmt and type(v['owned_count']) is int and v['owned_count']==0 and v['owned_matches']==[] and v['termination_issued'] is False and v['matcher_positive_cases']==4 and v['matcher_negative_cases']==negative,'Recorded zero-scope observation differs')
        scopes.append(label)
    require([r['mode'] for r in result['rows']]==['cpu','graphical'],'Mode membership/order differs')
    jobs=[];launches=[];outcomes=[];missing=[];cases=[];source_sets=[]
    for row,expected_cases,total,seconds in zip(result['rows'],[ [('transport',11),('adapter',128),('host',69)], [('focused',221),('peers',45)] ],[208,266],[41.7605826,102.8179396]):
        mode=row['mode'];require(type(row['exit']) is int and row['exit']==0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False and row['seconds']==seconds and row['root_exact_suite_assertions_passed'] is True,'Root mode exact gates differ')
        report=obj(ROOT_RUN+mode+'-report.json');require(typed_same(report,row['report']),'Root report copy differs')
        child=PureWindowsPath(row['report_path']).parent.relative_to(PureWindowsPath(review)).as_posix()+'/'
        require(child.startswith('output/helper-preview/'+mode+'-') and typed_same(report,obj(child+'verification.json')),'Fresh child report join differs')
        require(report['format']=='has_helper_preview_main_verification_1' and report['passed'] is True and report['error'] is None and report['mode']==mode and report['source_context']=='main_source_snapshot' and report['source_state']['revision']==REVISION and report['source_state']['working_status']==[] and report['overlay_files']==0 and report['native_requested'] is False and report['native_inputs_checked'] is False and report['native_fidelity'] is False and report['gpu_used'] is (mode=='graphical') and report['graphical_process_attempted'] is (mode=='graphical'),'Child source/native scope differs')
        require(report['main_root']==review and PureWindowsPath(report['actual_res_root'])==PureWindowsPath(review)/PureWindowsPath(child)/'Studio','Main/snapshot path binding differs')
        require(type(report['checks']) is int and report['checks']==total and [(c['label'],c['checks']) for c in report['results']]==expected_cases,'Mode exact cases/counts differ')
        require(set(report['preservation'])=={'main_sources','runtimes','head','native_originals','staged_native_inputs','published_requests','snapshot_sources','snapshot_extras','fixtures'} and all(x is True for x in report['preservation'].values()),'Child preservation differs')
        original=obj(child+'main-source-before.json');require(typed_same(original,obj(child+'main-source-after.json')) and typed_same(original,obj(child+'snapshot-source-before.json')),'Snapshot exact source identities differ')
        require(len(original)==1030 and all(original[n]['sha256']==d for n,d in before.items()),'Snapshot/root source hash join differs')
        source_sets.append(len(original))
        for case,(_,count) in zip(report['results'],expected_cases):
            label=case['label'];base=child+'Studio/output/helper-preview-qa/'+label+'/'
            require(case['passed'] is True and case['exit']==0 and case['retained_Popen_reaped'] is True and case['timed_out'] is False and case['error_markers']==[] and case['result_source_context_bound'] is True,'Case runtime gate differs')
            actual=obj(base+'result.json');actual_count=len(actual['checks']) if type(actual['checks']) is list else actual['checks']
            require(type(actual_count) is int and actual_count==count and actual['failures'] in ([],0),'Raw case count/failures differ')
            metrics=actual.get('metrics',actual);require(metrics['source_context']=='main_source_snapshot' and metrics['main_revision']==REVISION and metrics['source_manifest_sha256']==hashlib.sha256((json.dumps(original,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()).hexdigest(),'Raw case source context differs')
            cmd=obj(base+'command.json')
            if mode=='graphical':
                receipt=obj(base+'private-receipt.json')
                require(typed_same(receipt,case['private_receipt']) and case['clean_private_receipt'] is True and cmd.count('--receipt')==1 and PureWindowsPath(cmd[cmd.index('--receipt')+1])==PureWindowsPath(review)/PureWindowsPath(base)/'private-receipt.json','Direct/inline private receipt join differs')
                for key,value in {'format':'studio_private_desktop_1','exit':0,'private_window_seen':True,'child_desktop_confirmed':True,'foreground_child_observed':False,'desktop_switch_requested':False,'job_closed':True,'desktop_closed':True}.items():require(typed_same(receipt.get(key),value),'Private closure differs')
                jobs.append((receipt['desktop'],receipt['child_pid']))
            else:require('--receipt' not in cmd and (label=='transport' or '--headless' in cmd),'CPU headless/private domain differs')
            cases.append({'mode':mode,'label':label,'checks':count,'raw_result_path':base+'result.json'})
        qa=child+'Studio/output/helper-preview-qa/'
        for key,data in raw.items():
            if not key.startswith('REVIEW:'+qa) or not key.endswith('/owned-launch.json'):continue
            launch=load(data);launches.append(key);require(launch['job_assigned'] is True and launch['kill_on_close'] is True and launch['no_window'] is True and launch['active_process_limit']==1,'Worker launch ownership differs')
            owner=launch['owner'];require(type(owner['pid']) is int and type(owner['created_100ns']) is str and owner['created_100ns'].isdigit(),'Exact worker owner identity differs')
            outcome_key=key.removesuffix('owned-launch.json')+'owned-outcome.json'
            if outcome_key in raw:
                outcome=load(raw[outcome_key]);require(typed_same(owner,outcome['owner']) and typed_same(launch['python'],outcome['python']) and typed_same(launch['source_sha256'],outcome['source_sha256']) and outcome['exit']==0 and outcome['state']=='prepared_hidden' and outcome['error']=='' and outcome['job_closed'] is True and outcome['process_handle_closed'] is True,'Completed worker ownership/outcome differs');outcomes.append(outcome_key)
            else:missing.append(key)
    require(len(set(jobs))==len(jobs)==2 and len(launches)==21 and len(outcomes)==17 and len(missing)==4,'Physical/worker metadata totals differ')
    require(all('/focused/worker-'+name+'-helper-work/' in next(k for k in missing if '/focused/worker-'+name+'-helper-work/' in k) for name in ('seek','save','off','close')),'Four launch-only scenario identities differ')
    return {'format':'has_helper375_compact_actual_summary_1','qualification':'SCOPED_ORIGINAL_HELPER_CPU_AND_GRAPHICAL_NO_FULL_SUITE_OR_NATIVE_ASSET_FIDELITY','revision':REVISION,'cpu_checks':208,'graphical_checks':266,'cases':cases,'root_seconds':{'cpu':41.7605826,'graphical':102.8179396},'functional_source_entries_unchanged':1029,'snapshot_identity_entries_each':source_sets,'real_private_desktop_jobs':2,'private_desktops_closed_no_foreground_or_switch':True,'headless_CPU_desktop_receipts_fabricated':False,'worker_launch_records':21,'worker_completed_outcome_records':17,'worker_launch_only_records':missing,'retained_zero_base_and_worker_scope_pairs':scopes,'launch_only_scope':'Four focused cancellation/seek/save/off/close scenarios have launch metadata without owned-outcome; retain passing test/source/log evidence and later zero-worker observations, never fabricate outcome receipts.','full_suite_pass_claimed':False,'native_fidelity_claimed':False,'main_merged_claimed':False,'media_models_or_native_configuration_arrays_included':False,'active_full_output_read':False}
