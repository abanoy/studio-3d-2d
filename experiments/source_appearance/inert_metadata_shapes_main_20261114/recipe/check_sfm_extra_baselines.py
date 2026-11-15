from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
run=root/'output/sfm-extra-native-launch-20261114T013526736/run'
old_core=root/'output/source-choices-native/1794615194930984000-ae0e0967'
old_wide=root/'output/source-choices-native/1794615438168999800-42f0686d'
def cases(path):
 return {json.loads(p.read_bytes())['name']:p for p in (path/'cases').glob('*/expected.json')}
current=cases(run); previous={**cases(old_core),**cases(old_wide)}
rows=[]
for name in ['keiki_tools_chisels-groups-000','junko_hair-default-no-appearance','multi_skin_glove-default-no-appearance']:
 a=json.loads(current[name].read_bytes());b=json.loads(previous[name].read_bytes())
 assert a['glb_sha256']==b['glb_sha256']
 rows.append({'name':name,'exact_glb_sha256':a['glb_sha256'],'matches_prior_actual_app':True})
name='multi_skin_glove-default-no-appearance'
fresh=current[name].parent/'conversion-metadata/parameters.json'
prior=previous[name].parent/'conversion-metadata/parameters.json'
a=json.loads(fresh.read_bytes());b=json.loads(prior.read_bytes())
assert [k for k in a if a[k]!=b[k]]==['original_source']
assert a['original_source']!=b['original_source']
a['original_source']=b['original_source']
restored=json.dumps(a,ensure_ascii=True,indent=2).replace('\n','\r\n').encode('utf-8')
assert restored==prior.read_bytes()
report={'format':'has_sfm_extra_native_baselines_1','passed':True,'glb_joins':rows,
        'no_rule_report':{'only_different_field':'original_source','reason':'Each actual test uses a new owned input alias.',
                          'exact_legacy_writer_bytes_after_that_explicit_relocation':True,
                          'prior_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),
                          'fresh_sha256':hashlib.sha256(fresh.read_bytes()).hexdigest()},
        'limits':['Fresh Mima head did not use its older derived GLB as an exact baseline. Its native source, target tuples and actual geometry/control transport are checked separately.','These three GLB joins are derived-output equivalence, not original Source shader or artist fidelity.']}
(run/'independent-baselines.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
