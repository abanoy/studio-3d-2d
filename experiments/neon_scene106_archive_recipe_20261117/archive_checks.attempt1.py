"""Scalar/command/receipt joins for the two explicitly completed scene runs."""
import datetime
import json
import re

DIAG='output/neon-scene-mask-diagnostic-20261117-attempt1/'
PASS='output/neon-scene-view106-20261117-attempt1/'
CHILD='output/scene-view/1794884325741516800/'
DREC='output/private-desktop/scene_view_diagnostic_0ed86dca87e24d778e9be683015de1ad.json'
PREC='output/private-desktop/scene_view_smoke_d2e3009fb20f4ffa816db464d6a477e1.json'

def require(ok,message):
    if not ok:raise ValueError(message)

def typed_same(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(typed_same(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(typed_same(x,y) for x,y in zip(a,b))
    return a==b

def load(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'Duplicate JSON key');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))

def utc_ns(value):
    match=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(?:Z|\+00:00)',value)
    require(match is not None,'Exact UTC expected')
    stamp=datetime.datetime.strptime(match[1],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    return int(stamp.timestamp())*10**9+int((match[2] or '').ljust(9,'0'))

def check(raw,bindings,review):
    def read(path):return load(raw['REVIEW:'+path])
    def scope(path):
        value=read(path)
        require(value['format']=='has_root_workspace_scope_observation_1' and type(value['owned_count']) is int and value['owned_count']==0 and value['owned_matches']==[] and value['termination_issued'] is False and value['matcher_positive_cases']==4 and value['matcher_negative_cases']==3,'Closed host scope differs '+path)
        return utc_ns(value['observed_utc'])
    def receipt(path,exit_code):
        value=read(path)
        for key,wanted in {'format':'studio_private_desktop_1','desktop_switch_requested':False,'private_window_seen':True,'child_desktop_confirmed':True,'foreground_child_observed':False,'exit':exit_code,'job_closed':True,'desktop_closed':True}.items():
            require(typed_same(value.get(key),wanted),'Strict private receipt differs '+key)
        require(type(value['child_pid']) is int and value['child_pid']>0 and type(value['desktop']) is str and value['desktop'].startswith('HAS_Test_'),'Receipt identity missing')
        return value
    def direct(command,path):
        require(type(command) is list and command.count('--receipt')==1,'Direct receipt command missing')
        require(command[command.index('--receipt')+1]==review+'\\'+path.replace('/','\\'),'Receipt command ownership differs')
    d=read(DIAG+'verification.json');p=read(PASS+'verification.json')
    require(d['format']=='has_root_scene_mask_diagnostic_1' and type(d['process_exit']) is int and d['process_exit']==1 and d['reaped'] is True and d['source_unchanged'] is True and d['full_pass_claimed'] is False,'Diagnostic status differs')
    require(d['report']['checks']==102 and d['report']['failures']==4 and len(d['report']['cases'])==4 and len(d['samples'])==4,'Diagnostic failure evidence differs')
    require(typed_same(d['report'],read(DIAG+'case/result.json')),'Diagnostic raw result differs')
    require(p['format']=='has_root_workspace_followup_1' and p['passed'] is True and p['all_functional_source_unchanged'] is True and p['functional_source_files']==1029 and p['host_scopes_closed'] is True and p['full_suite_pass_claimed'] is False and len(p['rows'])==1,'Scoped PASS status differs')
    row=p['rows'][0]
    require(row['label']=='scene' and type(row['exit']) is int and row['exit']==0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False and row['seconds']==14.1473874,'Retained wrapper result differs')
    require(typed_same({k:v for k,v in row.items() if k!='report'},read(PASS+'scene-process.json')),'Raw process record differs')
    report=read(PASS+'scene-report.json');require(typed_same(row['report'],report) and typed_same(load(raw['REVIEW:'+PASS+'scene-stdout.log']),report),'Raw wrapper report/stdout differs')
    smoke=report['scene_view_smoke'];unit=report['scene_view_unit']
    require(type(smoke['checks']) is int and smoke['checks']==106 and type(smoke['failures']) is int and smoke['failures']==0 and len(smoke['cases'])==4,'Scene106 result differs')
    for case in smoke['cases']:
        require(case['display_composition']['supported'] is True and case['display_composition']['composite_ok'] is True and case['display_composition']['profile']=='neon','Actual composite result differs')
    require(unit['cases']==144 and unit['checks']==12830 and unit['failures']==0 and typed_same(unit,read(CHILD+'unit.json')),'Headless unit result differs')
    smoke_raw={k:v for k,v in smoke.items() if k not in ('private_receipt','private_receipt_path')}
    require(typed_same(smoke_raw,read(CHILD+'result.json')),'Raw smoke result differs')
    before=read(PASS+'source-before.json');after=read(PASS+'source-after.json')
    require(len(before)==1029 and typed_same(before,after),'Exact1029 source preservation differs')
    frozen=read(CHILD+'source-sha256.json')
    require(typed_same(frozen,report['source_sha256']) and len(frozen)==203,'Wrapper203 source map differs')
    for path,digest in frozen.items():require(before[path.replace('\\','/')]==digest,'Wrapper source not in full source manifest')
    require(report['folder']==review+'\\'+CHILD.rstrip('/').replace('/','\\'),'Saved child folder differs')
    dr=receipt(DREC,1);pr=receipt(PREC,0)
    require(raw['REVIEW:'+DREC]==raw['REVIEW:'+DIAG+'private-receipt.json'],'Diagnostic physical receipt copy differs')
    require(typed_same(pr,smoke['private_receipt']) and smoke['private_receipt_path']==review+'\\'+PREC.replace('/','\\'),'PASS inline physical receipt differs')
    direct(read(DIAG+'command.json'),DREC);direct(read(CHILD+'scene_view_smoke-command.json'),PREC)
    unit_cmd=read(CHILD+'scene_view_unit-command.json')
    require('--headless' in unit_cmd and '--receipt' not in unit_cmd,'Unit headless/no-receipt domain differs')
    require(dr['desktop']!=pr['desktop'] and dr['child_pid']!=pr['child_pid'],'Separate owned job identities collide')
    phase=[]
    for prefix,rec in ((DIAG,DREC),(PASS,PREC)):
        lo=scope(prefix+'before-closure.json');hi=scope(prefix+'after-closure.json')
        require(lo<hi,'Host observation order differs')
        mtime=bindings['REVIEW:'+rec]['mtime_ns'];require(lo<=mtime<=hi,'Original physical receipt mtime outside scoped observations')
        phase.append({'scope':prefix.rstrip('/'),'physical_receipt':rec,'physical_mtime_ns':mtime,'before_observation_ns':lo,'after_observation_ns':hi,'mtime_evidence':'Read-only original-filesystem observation captured during recipe preparation; not embedded in original receipt bytes'})
    scope(PASS+'scene-after-closure.json')
    for label,prefix,marker,count,failed in [('diagnostic',DIAG,'SCENE_VIEW ',102,4),('scene106',CHILD,'SCENE_VIEW ',106,0)]:
        name=prefix+('ordered-engine.log' if label=='diagnostic' else 'scene_view_smoke-engine.log')
        text=raw['REVIEW:'+name].decode('utf-8-sig')
        require(text.count(marker)==1 and text.count('\nFAIL ')==failed,'Ordered raw failure count differs')
        marked=load(next(line[len(marker):] for line in text.splitlines() if line.startswith(marker)))
        require(marked['checks']==count and marked['failures']==failed,'Ordered engine result differs')
    return {'format':'has_scene106_compact_actual_summary_1','qualification':'TWO_SCOPED_COMPLETED_RUNS_ONLY_NO_FULL_SUITE_OR_NATIVE_ASSET_CLAIM','diagnostic':{'checks':102,'failures':4,'process_exit':1,'reaped':True,'ordered_engine_log_retained':True},'scene106':{'checks':106,'failures':0,'unit_checks':12830,'unit_cases':144,'wrapper_seconds':row['seconds'],'process_exit':0,'reaped':True,'source_entries_unchanged':1029,'wrapper_frozen_sources':203,'ordered_engine_logs_retained':True},'physical_receipt_files':3,'unique_physical_jobs':2,'private_jobs_all_closed_no_switch_no_foreground':True,'unit_headless_without_private_receipt':True,'receipt_phase_metadata_observations':phase,'full_suite_pass_claimed':False,'main_merged_claimed':False,'native_asset_geometry_media_included':False,'active_full_output_read':False}
