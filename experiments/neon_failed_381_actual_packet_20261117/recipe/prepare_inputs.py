"""Pin public/scalar evidence only; never read native arrays or private logs."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
NEON=Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plans={'setter':[],'failed381':[]}
    def add(kind,root,path,target,compress=False):
        source=root/path
        assert source.is_file() and source.suffix in {'.json','.log','.py','.md'}
        assert not source.name.startswith('PRIVATE') and source.name not in {'expected.json','parameters.json'}
        plans[kind].append({'root':'main' if root==MAIN else 'neon','path':path,'archive_path':target+('.gz' if compress else ''),
            'sha256':sha(source),'bytes':source.stat().st_size,'gzip_exact_original':compress})
    stage='output/normal-setter-boundary-20261116-attempt1'
    for name in ['capture/PUBLIC_SETTER.json','capture/PUBLIC_PLACEMENT.json','private-receipt.json','STAGED.json','ROOT_COMMANDS.json']:
        add('setter',MAIN,stage+'/'+name,'actual/'+name)
    for name in ['verification.json','capture-command.json','capture-process.json','capture-start.json',
            'before-closure.json','after-closure.json','before-inventory-stdout.log','before-inventory-stderr.log','after-inventory-stdout.log','after-inventory-stderr.log']:
        add('setter',MAIN,stage+'/root-execution/'+name,'actual/root-execution/'+name)
    for packet in ['normal_setter_boundary_probe_20261116','normal_setter_boundary_sentinel_20261117','normal_setter_actual_driver_20261117']:
        add('setter',MAIN,'experiments/'+packet+'/INDEX.json','source/'+packet+'-INDEX.json')
    packet='experiments/normal_setter_boundary_sentinel_20261117'
    for name in ['README.md','ROOT_ADDITIONAL_REQUIREMENTS.json','ISOLATION_POLICY.json','stage_after_full.py','setter_support.py','setter_probe.py']:
        add('setter',MAIN,packet+'/'+name,'source/setter/'+name,name.endswith('.py'))
    # Exact completed source catalogue, not source/native artifact bodies.
    add('setter',MAIN,'output/windows-canonical-bone-binding-20261116T041518335/source-before.json','source/completed52-source-before.json',True)
    public=json.loads((MAIN/stage/'capture/PUBLIC_SETTER.json').read_bytes())
    placement=json.loads((MAIN/stage/'capture/PUBLIC_PLACEMENT.json').read_bytes())
    execution=json.loads((MAIN/stage/'root-execution/verification.json').read_bytes())
    assert execution['diagnostic_completed'] is True and execution['public_setter_sha256']==sha(MAIN/stage/'capture/PUBLIC_SETTER.json')
    assert placement['public_setter_sha256']==execution['public_setter_sha256'] and placement['private_setter_sha256']==public['private_sha256']
    assert execution['normal_fidelity_pass_claimed'] is False and execution['private_job_desktop_closed'] is True and execution['both_scopes_released'] is True
    summaries={}
    for name,row in public['models'].items():
        stages=row['stages']
        assert row['setter_input_word_exact'] is True and row['observer_control_normals_word_exact'] is True and row['saved_geometry_exact'] is True
        assert len({value['corner_normals_sha256'] for value in stages.values()})==1
        assert all(value['topology_and_positions_exact'] is True for value in stages.values())
        assert row['control_vs_saved_corner_readback']['max']==0 and row['control_vs_saved_corner_readback']['above_2e_5']==0
        summaries[name]={'vertices':row['vertices'],'corners':row['corners'],**stages['after_setter']['setter_payload_to_corner_readback']}
    run='output/windows-neon-381d5a9-20261117T003337'
    audit=run+'/failed-terminal-audit-attempt1'
    inventory=json.loads((NEON/audit/'receipt-inventory.json').read_bytes())
    assert sha(NEON/audit/'receipt-inventory.json')=='bfc025aaf492ee5eb8b7b19c8cd0a581134773fa111a3c89ef452c30fdca0d92'
    assert inventory['physical_receipts']==27 and inventory['normal_exit0']==25 and inventory['registered_cancel_exit2']==1 and inventory['registered_assertion_failure_exit1']==1
    for name in ['graphics-lease-closed-after-failure.json','animated-channels-original-result.json','state.json','launch.json','root-birth-observation.json']:
        add('failed381',NEON,run+'/'+name,'actual/'+name)
    for name in ['receipt-inventory.json','host-observation.json','canonical.log','source-before.json','source-after.json']:
        add('failed381',NEON,audit+'/'+name,'actual/'+name,name in ['canonical.log','source-before.json','source-after.json'])
    for index,row in enumerate(inventory['rows']):
        source=Path(row['preserved_raw_copy'])
        assert source.is_relative_to(NEON) and sha(source)==row['source_sha256']
        add('failed381',NEON,source.relative_to(NEON).as_posix(),f'actual/receipts/{index:03d}-'+source.name)
    for name in ['INDEX.json','CONTEXT.json','SOURCE_AUDIT.json','close_failed.py','README.md']:
        add('failed381',MAIN,'experiments/neon_failed_381_terminal_20261117/'+name,'source/closure-helper/'+name)
    release=json.loads((NEON/run/'graphics-lease-closed-after-failure.json').read_bytes())
    assert release['released'] is True and release['full_suite_passed'] is False and release['physical_jobs']==27 and release['root_observer_issued_no_termination'] is True
    value={'format':'has_setter_and_failed381_public_archive_inputs_1','roots':{'main':str(MAIN),'neon':str(NEON)},'plans':plans,
        'setter_scalar_summary':summaries,'private_native_arrays_or_private_logs_read':False,
        'setter_private_hash_reference_only':public['private_sha256'],'setter_private_bytes_reference_only':public['private_bytes'],
        'failed381_inventory_sha256':sha(NEON/audit/'receipt-inventory.json'),'failed381_suite_passed':False}
    for rows in plans.values():assert len(rows)==len({row['archive_path'] for row in rows})
    (HERE/'INPUTS.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'setter_files':len(plans['setter']),'failed381_files':len(plans['failed381']),'inputs_sha256':sha(HERE/'INPUTS.json'),'private_inputs_read':False}))


if __name__=='__main__':main()
