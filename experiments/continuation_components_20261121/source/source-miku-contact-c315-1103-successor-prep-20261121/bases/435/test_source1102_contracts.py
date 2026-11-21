"""Pure synthetic provenance contracts; authored UNRUN. No filesystem/native jobs."""
import copy
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('_source1102_contracts',Path(__file__).with_name('source1102.py'))
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
checks=0

def accept(action,label):
    global checks
    action();checks+=1;print('PASS '+label)

def refuse(action,label):
    global checks
    try:action()
    except (ValueError,TypeError):checks+=1;print('PASS '+label);return
    raise AssertionError('Unexpected admission: '+label)

completion={'format':'has_reference_body_full_coordinator_1','revision':S.REVISION,'exit':0,
            'functional_source_count':1102,'result_groups':182,**{key:True for key in S.FLAGS}}
accept(lambda:S.completion_contract(completion),'exact completed435 Full1102 contract')
for key in S.FLAGS:
    bad=copy.deepcopy(completion);bad[key]=False
    refuse(lambda:S.completion_contract(bad),'unfinished or false qualification flag '+key)
bad=copy.deepcopy(completion);bad['revision']='e0879c7df74bc3704902bfdaf4ff74eee40c3aea'
refuse(lambda:S.completion_contract(bad),'historical revision cannot admit new1102 runtime')
bad=copy.deepcopy(completion);bad['exit']=False
refuse(lambda:S.completion_contract(bad),'boolean false is not integer zero exit')
bad=copy.deepcopy(completion);bad['functional_source_count']=1086
refuse(lambda:S.completion_contract(bad),'old1086 source domain is not broadened')
bad=copy.deepcopy(completion);bad['result_groups']=181
refuse(lambda:S.completion_contract(bad),'missing Full group refused')
report={name:{'status':'PASS','checks':count,'all_admitted_sources_unchanged':True,
              **({'generated_fixture_preserved':True} if name.startswith('editor_controls_') else {})}
        for name,count in S.NEW_GROUPS.items()}
for i in range(182-len(report)):report['prior_group_'+str(i)]={}
accept(lambda:S.report_contract(report),'all twelve new groups coexist in182-group result')
bad=copy.deepcopy(report);bad.pop('camera_interactions_pure');bad['unrelated']={}
refuse(lambda:S.report_contract(bad),'same group count cannot hide missing new camera group')
bad=copy.deepcopy(report);bad['editor_controls_handles']['checks']=27
refuse(lambda:S.report_contract(bad),'historical handle27 cannot stand in for current38')
bad=copy.deepcopy(report);bad['camera_interactions_pure']['checks']=True
refuse(lambda:S.report_contract(bad),'boolean assertion count refused')
bad=copy.deepcopy(report);bad['editor_controls_face']['generated_fixture_preserved']=False
refuse(lambda:S.report_contract(bad),'face fixture preservation required independently')
baseline={};catalogue={}
for i in range(1102):
    name='src/contract_'+str(i)+'.gd';baseline[name]={'bytes':1,'sha256':'a'*64,'git_sha1':'b'*40,'main_mtime_ns':'1'}
    catalogue[name]={'bytes':1,'sha256':'a'*64,'git_sha1':'b'*40,'mtime_ns':2}
accept(lambda:S.source_contract(baseline,catalogue),'equal source bytes admit independently preserved clone timestamps')
bad=copy.deepcopy(catalogue);bad['src/foreign.gd']=bad.pop('src/contract_0.gd')
refuse(lambda:S.source_contract(baseline,bad),'same-sized different source domain refused')
bad=copy.deepcopy(catalogue);bad['src/contract_0.gd']['git_sha1']='c'*40
refuse(lambda:S.source_contract(baseline,bad),'different immutable Git source blob refused')
bad=copy.deepcopy(catalogue);bad['src/contract_0.gd']['bytes']=True
refuse(lambda:S.source_contract(baseline,bad),'boolean source byte count refused')
bad=copy.deepcopy(catalogue);bad['src/contract_0.gd']['mtime_ns']=True
refuse(lambda:S.source_contract(baseline,bad),'boolean Full source stamp refused')
case_base=copy.deepcopy(baseline);case_catalogue=copy.deepcopy(catalogue)
case_base['SRC/CONTRACT_0.GD']=case_base.pop('src/contract_1.gd')
case_catalogue['SRC/CONTRACT_0.GD']=case_catalogue.pop('src/contract_1.gd')
refuse(lambda:S.source_contract(case_base,case_catalogue),'same-size case-aliased source domains refused')
assert checks==24,checks
print('SOURCE1102_CONTRACTS '+str(checks)+' authored controls completed')
