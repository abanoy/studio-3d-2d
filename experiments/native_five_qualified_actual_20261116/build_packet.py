"""Freeze explicit completed safe metadata and public code, never private assets."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
STAGE=ROOT/'output/native-five-stage-attempt3'
STUDIO=STAGE/'Studio'
STATE=STUDIO/'output/source-native-five-state-20261116T040011702334'
GUI=STUDIO/'output/native-five-gui-attempt1'
HOST=STAGE/'TRANSVERSE-ROOT-EXECUTION'
PLAN=[]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2);f.write('\n')
def privacy(value,path=''):
    if isinstance(value,dict):
        for k,v in value.items():privacy(v,path+'/'+k)
    elif isinstance(value,list):
        if any(isinstance(v,(float,int)) and not isinstance(v,bool) for v in value):
            permitted={'/scope/native_rule_indices_selected':[8,17,18,26,27],
                       '/UI_driver_binding/proposed_writer_packed_linked_checks':[82,11,8]}
            assert path in permitted and value==permitted[path],path
        for v in value:privacy(v,path+'/*')
def plan(path,name,compressed=False):
    assert path.suffix in ('.json','.log','.gd','.py')
    assert path.name!='expected.json' and not (HERE/name).exists()
    raw=path.read_bytes();raw.decode('utf-8-sig')
    if path.suffix=='.json':privacy(json.loads(raw))
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    PLAN.append((path,name,raw,compressed))

def main():
    sv,sr=read(STATE/'verification.json'),read(STATE/'result.json')
    assert sv['passed'] and sv['actual_result_valid'] and sv['runtime_lease_released']
    assert sv['checks_observed']==sr['checks']==len(sr['named_checks'])==266
    assert sv['failures_observed']==sr['failures']==0 and all(sr['named_checks'].values())
    assert sr['complete_assertion_set'] and sr['metrics']['completed_native_steps']==886
    assert sr['job_sha256']==sha((STATE/'job.json').read_bytes())
    assert sr['source_manifest_sha256']==sha((STATE/'SOURCE.json').read_bytes())
    assert sv['test_result_sha256']==sha((STATE/'result.json').read_bytes())
    assert all(sv['preservation'].values())
    for phase in sv['phases']:
        assert phase['passed'] and phase['exit']==0 and phase['retained_Popen_reaped']
        assert not phase['timed_out'] and not phase['owned_child_terminated'] and not phase['owned_child_forced_kill']
        assert not phase['error_markers']
    for when in ('before','after'):assert read(STATE/(when+'-runtime-closure.json'))['owned_count']==0
    for p in sorted(STATE.iterdir()):
        if p.is_file() and p.suffix in ('.json','.log'):
            zipped=p.name=='SOURCE.json';plan(p,'state/'+p.name+('.gz' if zipped else ''),zipped)
    gv=read(GUI/'verification.json')
    assert gv['passed'] and gv['checks_expected']==gv['checks_observed']==102
    assert gv['phase_expected']=={'writer':83,'reader-packed':11,'reader-linked':8}
    assert len(gv['results'])==3 and all(gv['preservation'].values()) and gv['error'] is None
    assert (GUI/'source-before.json').read_bytes()==(GUI/'source-after.json').read_bytes()
    results={}
    for i,(label,count) in enumerate(gv['phase_expected'].items()):
        folder=GUI/label;r=read(folder/'result.json');v=read(folder/'process-verification.json');receipt=read(folder/'private-receipt.json')
        assert r['checks']==len(r['named_checks'])==count and r['failures']==0
        assert r['complete_assertion_set'] and all(r['named_checks'].values())
        assert r['native_rules_solved']==5 and r['retained_rules']==49 and not r['private_native_arrays_serialized']
        assert r['job_sha256']==sha((folder/'job.json').read_bytes())
        assert r['source_manifest_sha256']==sha((GUI/'source-before.json').read_bytes())
        assert v==gv['results'][i] and v['passed'] and v['exit']==0 and v['retained_Popen_reaped']
        assert v['result_binding'] and v['private_receipt_passed'] and not v['timed_out']
        assert not v['error_markers'] and not v['metadata_errors'] and v['result_sha256']==sha((folder/'result.json').read_bytes())
        assert receipt['exit']==0 and receipt['job_closed'] and receipt['desktop_closed'] and receipt['child_desktop_confirmed']
        assert not receipt['foreground_child_observed']
        for name in ('result.json','job.json','process-verification.json','private-receipt.json','command.json','stdout.log','stderr.log','engine.log'):
            plan(folder/name,'GUI/'+label+'/'+name)
        results[label]=r
    for name in ('source-before.json','source-after.json','verification.json','offline-plan.json'):
        zipped=name.startswith('source-');plan(GUI/name,'GUI/'+name+('.gz' if zipped else ''),zipped)
    host=read(HOST/'verification.json');preserve=read(STAGE/'ROOT-PRESERVATION-qualified-102.json')
    assert host['passed'] and host['checks_observed']==102 and host['runtime_lease_released'] and host['main_promoted'] is False
    assert host['verification_sha256']==sha((GUI/'verification.json').read_bytes())
    assert host['state266_predecessor_sha256']==sha((STATE/'verification.json').read_bytes())
    assert host['process']['exit']==0 and host['process']['retained_Popen_reaped']
    assert not host['process']['timed_out'] and not host['process']['owned_wrapper_terminated']
    assert preserve['passed'] and preserve['original_functional_files_exact']==1017
    assert preserve['original_two_inputs_exact'] and preserve['baseline_verification_exact'] and preserve['sealed_packet_exact']
    assert sha((STAGE/'ROOT-PRESERVATION-qualified-102.json').read_bytes())=='6f0d28ad749dfef5d72dc4174e9f2f755124ce4e73bc0b7a928bf8fdf3f044f1'
    for when in ('before','after'):assert read(HOST/(when+'-closure.json'))['owned_count']==0
    for p in sorted(HOST.iterdir()):
        assert p.is_file() and p.suffix in ('.json','.log');plan(p,'host/'+p.name)
    for p in sorted(STAGE.iterdir()):
        if p.is_file() and p.suffix=='.json':
            zipped=p.stat().st_size>20000;plan(p,'stage/'+p.name+('.gz' if zipped else ''),zipped)
    sourcepins={
        'src/source_secondary.gd':'3b2c29dc11b60e68306f858a32d03271e30a039b8451916df2ff9324e7da4f84',
        'src/secondary_live.gd':'2613b19ce53b3a50fd001fe4e5b39bca2814165148b036993549490aa96c33a9',
        'src/source_chain_math.gd':'31491fbde49b635edadda5e661fa3eecabf0f7e3598f0dc448c0d944ffa6f844',
        'tests/source_native_five_live_ui.gd':'bea7c6b9d512583f05fe88f63f3113c34e3bc9dbf05ac31ce0961402ed704a12',
        'tests/source_native_five_state_unit.gd':'ab40f406e7b2ececc719761f0f0246ecb347bf853d711c3901671c8b8d6d7174',
        'tests/verify_source_native_five_live.py':'543da7be754ef8e748215ff6e39eaa897de458c3ea1eeeb8b51bf1c375bfc96e'}
    smap={r['path']:r for r in read(STATE/'SOURCE.json')['files']}
    gmap=read(GUI/'source-before.json')
    for name,pin in sourcepins.items():
        p=STUDIO/name;assert sha(p.read_bytes())==pin and gmap[name]['sha256']==pin
        if name.startswith('src/') or name.endswith('source_native_five_state_unit.gd'):
            assert smap[name]['sha256']==pin
        plan(p,'source/'+name)
    for name in ('src/source_jiggle_math.gd','experiments/native_source_live_port_20261115/run_five_state_owned.py'):
        plan(STUDIO/name,'source/'+name)
    for name in ('apply_five_strict2_stage.py','run_five_transverse_stage.py'):
        plan(ROOT/'experiments/native_source_live_port_20261115'/name,'source/root/'+name)
    upstream={
        'experiments/native_five_initial_actual_20261116/INDEX.json':'d9c9e28b7bf02e7e6d1651638330135ae7388f0f1ab785be46339ba3bc5548ec',
        'experiments/native_five_performance_followup_20261115/INDEX.json':'cae9f2b9cb550446897ebdec0a567e5b2ffb505184effac307b17d3042d1abd5',
        'experiments/source_native_five_transverse_fixture_20261116/INDEX.json':'0c066083e547aed8287d4ba4092e00d4853cf6d5ee8b8b4f5b25510ce85a9488'}
    for rel,pin in upstream.items():assert sha((ROOT/rel).read_bytes())==pin
    writer=results['writer'];fixture=writer['metrics']['controlled_fixture']
    assert writer['named_checks']['fan.controlled_transverse_fixture'] and writer['named_checks']['fan.opposite_tip_directions']
    assert fixture['admission_only_no_physics_tolerance_change'] and fixture['all5_both_mean_fields_hit']
    assert fixture['native8_goal_mean_axis_abs_dot_max']<=0.0001 and fixture['greatest_mean_field_normalized_dot']<=-0.9999
    assert fixture['root_geometry_frames0_24_exact'] and fixture['root_keys_equal']
    assert writer['metrics']['record_root_rotation_fixture']['actual_root_geometry_changed']
    benchmark={'format':'has_isolated_native_five_qualified_actual_1',
        'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'execution_context':'ISOLATED_STAGE3_PRE_PROMOTION','main_promotion_performed_by_packet':False,
        'base_Git_context_only':'dbf0bc1145f74b5bbff814ec6a417ccd23ce0885',
        'state':{'checks':266,'failures':0,'actors':3,'completed_native_steps':886,'negative_contexts':32,'passed':True},
        'GUI':{'checks':102,'failures':0,'phase_counts':{'writer':83,'reader-packed':11,'reader-linked':8},
            'passed':True,'closed_private_jobs':3,'all_receipts_exit0_no_foreground':True},
        'controlled_fixture':fixture,'record_root_rotation_fixture':writer['metrics']['record_root_rotation_fixture'],
        'protected_root_preservation':preserve,
        'root_wrapper':host['process'],'runtime_lease_released':True,
        'qualified_product_source_sha256':{k:v for k,v in sourcepins.items() if k.startswith('src/')},
        'performance':{'GUI_native_step_means_ms':{k:v['native_step_processing']['mean_usec']/1000 for k,v in writer['metrics'].items() if isinstance(v,dict) and 'native_step_processing' in v},
            'headless_rotating_native_step_means_ms':{k:sr['metrics'][k]['native_step_processing']['mean_usec']/1000 for k in ('rotation_half','rotation_one','rotation_two')},
            '120Hz_interval_ms':1000/120,'FPS_or_realtime_guarantee':False},
        'scope':{'rules':5,'retained_rules':49,'unselected_world_bones':64,'weighted_union_vertices':694,'unaffected_vertices':8967,
            'raw_source_report_inert_unchanged':True,'same_actor_active_ragdoll':'UNQUALIFIED_PARTIAL_SOURCE_RIG',
            'Source_SDK_artist_or_wider_model_fidelity':False,'private_asset_or_expected_or_pose_arrays_in_packet':False,
            'full_current_default_pass':False,'prior_dbf_complete_default':'FAILED_UNCHANGED','manual_owner_check':'DEFERRED_NO_RESULT'},
        'upstream_packet_indices':upstream,'formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED',
        'next':'Promote exact qualified product subset separately; update UI labels/provenance, affected regressions and a fresh complete default. Preserve earlier failures.'}
    # Preflight all copies before the first payload write.
    assert len({n for _,n,_,_ in PLAN})==len(PLAN)
    aliases=[]
    for p,name,raw,zipped in PLAN:
        target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(gzip.compress(raw,mtime=0) if zipped else raw)
        aliases.append({'source':p.relative_to(ROOT).as_posix(),'stored':name,'raw_bytes':len(raw),
                        'raw_sha256':sha(raw),'encoding':'gzip_mtime0' if zipped else 'identity'})
    save('BENCHMARK.json',benchmark)
    save('SOURCE_MANIFEST.json',{'format':'has_native_five_qualified_actual_sources_1','copies':aliases})
    rows=[]
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and p.name!='INDEX.json':
            raw=p.read_bytes();rows.append({'path':p.relative_to(HERE).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    save('INDEX.json',{'format':'has_native_five_qualified_actual_index_1','files':rows,'file_count':len(rows),'total_bytes':sum(x['bytes'] for x in rows)})
    print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'copies':len(aliases),'index_sha256':sha((HERE/'INDEX.json').read_bytes())}))

if __name__=='__main__':main()
