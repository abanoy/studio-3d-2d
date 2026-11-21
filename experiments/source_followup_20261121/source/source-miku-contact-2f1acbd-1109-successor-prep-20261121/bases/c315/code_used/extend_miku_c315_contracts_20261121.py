"""Author pure negative controls without importing/running candidate code."""
from pathlib import Path
import ast
OUT=Path(__file__).resolve().parent
OLD=OUT/'source-miku-contact-1102-successor-prep-20261121'
NEW=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
s=(OLD/'test_source1102_contracts.py').read_text()
s=s.replace('source1102','source1103').replace('1102','1103').replace('435','c315')
s=s.replace("assert checks==24,checks\nprint('SOURCE1103_CONTRACTS '+str(checks)+' authored controls completed')",'')
tail='''
# Explicit Full/movies/receipt/isolated-launch controls use synthetic JSON only.
new_report={name:{'status':'PASS','checks':count,'all_admitted_sources_unchanged':True,
              **({'generated_fixture_preserved':True} if name.startswith('editor_controls_') else {})}
            for name,count in S.NEW_GROUPS.items()}
for i in range(21):new_report['contract_'+str(i)+'_video']={}
for i in range(182-len(new_report)):new_report['legacy_'+str(i)]={}
groups={'format':'has_exact_full182_group_contract_1','revision':S.REVISION,
        'expected_group_keys':list(new_report),'new_groups':S.NEW_GROUPS.copy(),
        'movie_groups':[n for n in new_report if n.endswith('_video')]}
done=copy.deepcopy(completion);done['movie_groups']=groups['movie_groups'].copy()
accept(lambda:S.exact_group_contract(done,new_report,groups),'exact182 keys626 checks21 movie keys')
bad=copy.deepcopy(new_report);bad['substitute']=bad.pop('legacy_0')
refuse(lambda:S.exact_group_contract(done,bad,groups),'same182 length cannot substitute an old group')
bad=copy.deepcopy(done);bad['movie_groups'].pop()
refuse(lambda:S.exact_group_contract(bad,new_report,groups),'missing movie refuses admission')
bad=copy.deepcopy(done);bad['movie_groups'][0]=bad['movie_groups'][1]
refuse(lambda:S.exact_group_contract(bad,new_report,groups),'duplicate movie cannot satisfy21')
bad=copy.deepcopy(done);bad['movie_groups'][0]='unrelated_video'
refuse(lambda:S.exact_group_contract(bad,new_report,groups),'same21 count cannot substitute movie identity')
bad=copy.deepcopy(groups);bad['revision']='435dc02426a7cdd313e43fe674c9008520845428'
refuse(lambda:S.exact_group_contract(done,new_report,bad),'historical435 group document refused')
bad=copy.deepcopy(groups);bad['new_groups']['editor_controls_geometry']=36
refuse(lambda:S.exact_group_contract(done,new_report,bad),'new626 assertion identities cannot drift')
receipt={'format':'studio_private_desktop_1','desktop':'HAS_synthetic_1','child_pid':10,'exit':0,
 'seconds':1,'job_closed':True,'desktop_closed':True,'child_desktop_confirmed':True,
 'foreground_child_observed':False,'desktop_switch_requested':False}
accept(lambda:S.physical_receipt_contract(receipt),'actual typed closed isolated receipt')
for key,value in [('child_pid',True),('exit',False),('job_closed',False),('desktop_closed',False),
                  ('child_desktop_confirmed',False),('foreground_child_observed',True),('desktop_switch_requested',True)]:
 bad=copy.deepcopy(receipt);bad[key]=value
 refuse(lambda:S.physical_receipt_contract(bad),'private physical refusal '+key)
cancel=copy.deepcopy(receipt);cancel.update(desktop='HAS_synthetic_cancel',exit=2,cancelled=True,error='Owned converter cancelled')
accept(lambda:S.physical_receipt_contract(cancel),'exact expected converter cancellation')
bad=copy.deepcopy(cancel);bad['error']='some unrelated failure'
refuse(lambda:S.physical_receipt_contract(bad),'cancellation code alone cannot hide failure')
rows=[{'path':'output/receipt'+str(i)+'.json','sha256':str(i)*64,'value':v} for i,v in enumerate((receipt,cancel))]
classified={'current':rows,'conflicts':[],'changed_original_archives':[]}
closed={'current_jobs':copy.deepcopy(rows),'unique_current_private_jobs':2,'new_receipt_paths':2,
        'nonzero_private_jobs':[copy.deepcopy(rows[1])]}
accept(lambda:S.receipt_contract(closed,classified),'complete current jobs with exactlyone expected cancellation')
bad=copy.deepcopy(classified);bad['conflicts']=[{'kind':'unknown prior bytes'}]
refuse(lambda:S.receipt_contract(closed,bad),'receipt provenance conflict refused')
bad=copy.deepcopy(classified);bad['changed_original_archives']=[{'kind':'missing'}]
refuse(lambda:S.receipt_contract(closed,bad),'changed old archive cannot disappear from current proof')
bad=copy.deepcopy(closed);bad['unique_current_private_jobs']=True
refuse(lambda:S.receipt_contract(bad,classified),'boolean private job count refused')
bad=copy.deepcopy(closed);bad['current_jobs'].pop()
refuse(lambda:S.receipt_contract(bad,classified),'omitted current job refused')
bad=copy.deepcopy(closed);bad['nonzero_private_jobs']=[]
refuse(lambda:S.receipt_contract(bad,classified),'expected cancellation must actually be accounted')
bad=copy.deepcopy(classified);bad['current'][0]['value']['foreground_child_observed']=True
refuse(lambda:S.receipt_contract(closed,bad),'current actual receipt flags checked independently')
clone=Path('synthetic')/S.FULL_CLONE;outer=clone/'output/root-full-launch-synthetic'
launch={'format':'has_import_off_full_outer_launch_1','revision':S.REVISION,'checkout':str(clone),'pid':11,
 'started_ns':1,'coordinator_sha256':'a'*64,'parent_environment_changed':False,'hidden_console':True,
 'graphical_tests_must_use_private_desktops':True,'child_environment':{
 k:str(outer/'User'/leaf) for k,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]}}
launch['child_environment']['PYTHONDONTWRITEBYTECODE']='1'
outerdone={'format':'has_import_off_full_outer_completion_1','exit':0,'pid':11,'launch':copy.deepcopy(launch),
 'child_reaped':True,'parent_environment_unchanged':True,'coordinator_source_unchanged':True,'revision_unchanged':True}
accept(lambda:S.outer_contract(launch,outerdone,clone,outer,'a'*64),'completed isolated outer Full contract')
for key,value in [('exit',False),('child_reaped',False),('parent_environment_unchanged',False),
                  ('coordinator_source_unchanged',False),('revision_unchanged',False),('pid',12)]:
 bad=copy.deepcopy(outerdone);bad[key]=value
 refuse(lambda:S.outer_contract(launch,bad,clone,outer,'a'*64),'unfinished or mismatched outer '+key)
bad=copy.deepcopy(launch);bad['child_environment']['APPDATA']=str(clone/'shared-profile')
refuse(lambda:S.outer_contract(bad,outerdone,clone,outer,'a'*64),'shared owner profile refused')
bad=copy.deepcopy(launch);bad['child_environment']['TMP']=str(outer/'other-temp')
refuse(lambda:S.outer_contract(bad,outerdone,clone,outer,'a'*64),'allfour isolated directories required')
bad=copy.deepcopy(launch);bad['revision']='435dc02426a7cdd313e43fe674c9008520845428'
refuse(lambda:S.outer_contract(bad,outerdone,clone,outer,'a'*64),'435 failure never qualifies c315 native test')
refuse(lambda:S.outer_contract(launch,outerdone,clone,outer,'b'*64),'actual unchanged coordinator source pin required')
originals=copy.deepcopy((done,new_report,groups,receipt,cancel,rows,classified,closed,launch,outerdone))
S.exact_group_contract(done,new_report,groups);S.receipt_contract(closed,classified)
S.outer_contract(launch,outerdone,clone,outer,'a'*64)
accept(lambda:None if originals==(done,new_report,groups,receipt,cancel,rows,classified,closed,launch,outerdone)
       else (_ for _ in ()).throw(AssertionError('mutated admission data')),'pure gates preserve all inputs')
assert checks==60,checks
print('SOURCE1103_CONTRACTS '+str(checks)+' controls completed')
'''
s+=tail;ast.parse(s);p=NEW/'test_source1103_contracts.py';assert not p.exists();p.write_text(s,encoding='utf-8')
print('Authored source contracts; not executed')
