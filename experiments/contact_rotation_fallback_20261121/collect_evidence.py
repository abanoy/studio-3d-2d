"""Explicit text-only rotation evidence curation; no engine or source writes."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
PRIMARY=HERE.parents[1]
PACKED=PRIMARY.parent/'has-reconstruction-packed-20261121'
ORIGINS=[]
PINS={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
    a=path.stat();raw=path.read_bytes();b=path.stat()
    stamp=(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)
    assert stamp==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)
    PINS[path]=(stamp,sha(raw));return raw
def origin(path,raw):
    root,label=(PRIMARY,'PRIMARY') if path.is_relative_to(PRIMARY) else (PACKED,'PACKED')
    return {'root':label,'path':path.relative_to(root).as_posix(),'bytes':len(raw),'sha256':sha(raw)}
def write(name,raw,source=None):
    raw.decode('utf-8');assert b'\0' not in raw
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as stream:stream.write(raw)
    if source is not None:ORIGINS.append({'archive':name,**origin(source,raw)})
def save(name,value):write(name,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
def copy(name,path):
    raw=read(path);write(name,raw,path);return json.loads(raw) if path.suffix=='.json' else raw
def main():
    pre=PACKED/'output/contact-rotation-degeneracy-v2-prep-20261121'
    red=PACKED/'output/contact-rotation-degeneracy-1795308834830385300'
    denied=PACKED/'output/contact-rotation-degeneracy-1795308771766593600'
    green=PACKED/'output/contact-rotation-degeneracy-1795308931741742800'
    a=copy('before/actual_src89_red.json',pre/'ACTUAL_SOURCE_RED.json')
    assert a['status']=='FAIL' and a['checks']==20 and a['failures']==6 and a['all_jobs_closed'] is True
    copy('before/retained_interpretation.json',red/'SAFE_RESULT.json')
    # The first result is a setup failure, never six failed product controls.
    d=copy('prelaunch/setup_failure.json',denied/'SAFE_RESULT.json')
    proof=copy('prelaunch/private_receipt.json',denied/'Cases/generated/private-receipt.json')
    assert d['status']=='FAIL' and 'checks' not in d and proof['exit']==2 and 'child_pid' not in proof and 'Create private test desktop' in proof['error']
    g=copy('candidate/output_copy20.json',green/'SAFE_RESULT.json')
    assert g['status']=='PASS' and g['checks']==20 and g['failures']==0 and g['all_jobs_closed'] is True
    current=copy('current/public20.json',PRIMARY/'output/secondary-contact-rotation-1795309495945026800/verification.json')
    regression=copy('current/public47.json',PRIMARY/'output/secondary-contact-cache-1795309532600535200/verification.json')
    assert current['status']=='PASS' and current['checks']==20 and current['all_jobs_closed'] is True
    assert regression['status']=='PASS' and regression['checks']==47 and regression['all_jobs_closed'] is True
    assert regression['native_requested'] is False
    bindings=copy('current/bindings.json',PRIMARY/'output/contact-rotation-bindings.json')
    assert bindings['status']=='PASS' and len(bindings['stale_refusals'])==2
    patch=copy('code/PATCH.json',pre/'PATCH.json')
    baseline=read(PACKED/'src/secondary_skin_contact.gd')
    actual=read(PRIMARY/'src/secondary_skin_contact.gd')
    candidate=read(pre/'contact_rotation_fallback.gd')
    assert sha(baseline)==patch['baseline_sha256']=='89a07c661b023dab88b06e6fa21910364463a9270dfb5d1baf1b9b63a3101b87'
    assert actual==candidate and sha(actual)==patch['candidate_sha256']=='8aac05c4b3bbb132ff104a71bdc448b9b800f29c55496a53d78929384d568f65'
    assert baseline.decode().count(patch['old'])==1 and baseline.decode().replace(patch['old'],patch['new']).encode()==actual
    assert actual.decode().replace(patch['new'],patch['old']).encode()==baseline
    assert current['selected_source_sha256']==regression['production_skin_sha256']==sha(actual)
    for name,path in [('code/executed_generated_unit.gd.txt',pre/'contact_rotation_degeneracy.gd'),('code/executed_output_runner.py.txt',pre/'run_generated_rotation.py'),('code/current_public_unit.gd.txt',PRIMARY/'tests/secondary_contact_rotation_unit.gd'),('code/current_public_verifier.py.txt',PRIMARY/'tests/verify_secondary_contact_rotation.py')]:copy(name,path)
    for name,stage in [('before',red),('candidate',green)]:
        raw=read(stage/'Cases/generated/stdout.log')
        assertions=[line for line in raw.decode().splitlines() if line.startswith(('PASS ','FAIL '))]
        assert len(assertions)==20
        write(name+'/assertions.txt',('\n'.join(assertions)+'\n').encode())
        ORIGINS.append({'archive':name+'/assertions.txt','projection':'only exact PASS/FAIL assertion lines; user-profile marker omitted',**origin(stage/'Cases/generated/stdout.log',raw)})
        copy(name+'/private_receipt.json',stage/'Cases/generated/private-receipt.json')
    source=[]
    for rel in ['src/secondary_skin_contact.gd','tests/secondary_contact_rotation_unit.gd','tests/verify_secondary_contact_rotation.py','tests/wind_review_port_files.json','tests/helper_preview_port_files.json']:
        raw=read(PRIMARY/rel);source.append({'path':rel,'bytes':len(raw),'sha256':sha(raw)})
    save('source_identity.json',{'scope':'current_PRIMARY_source_identity_not_whole_full','files':source,'target_function':'secondary_skin_contact.rotation','old_src89_sha256':sha(baseline),'exact_patch_reversed':True,'production_rotational_math_thresholds_and_radii_unchanged_except_missing_direction_fallback':True})
    context=PACKED/'output/residual-contact-feasibility-20261121'
    preliminary=read(context/'SOURCE_CONNECTIVITY.json');corrected=read(context/'SOURCE_POLICY_CONNECTIVITY.json')
    # Only aggregate provenance references: do not copy private runtime mapping.
    save('separate_context.json',{'scope':'historical_SRC89_geometry_diagnostic_not_added_to_rotation_or_regression_counts','preliminary_source_graph_sha256':sha(preliminary),'corrected_source_graph_sha256':sha(corrected),'correction':'200 means generated nodes, not rotating controls;160 rotate and40 are terminal tails;123 relevant controls include109 direct and14 ancestor-only','runtime_18_scope':'Separately sampled Junko worst point already had a valid existing-helper rotation; no attribution of its residual collisions to this reproduced degeneracy','whole_hair_or_visual_completion':False})
    save('summary.json',{'format':'rotation_pole_fallback_actual_source_evidence_1','current_source_sha256':sha(actual),'before_actual_source_unit_status':'FAIL','before_checks':20,'before_failures':6,'before_passing_assertions':14,'prelaunch_setup_failure_assertions':0,'output_copy_candidate_checks':20,'current_actual_source_rotation_checks':20,'existing_generated_cache_regression_checks':47,'duplicate_same_fixture_runs_are_not_additive':True,'all_attempted_engine_jobs_closed':True,'prelaunch_denial_no_engine_created':True,'candidate_has_no_expected_failure_filter':True,'binding_stale_refusals':2,'wind_binding_members':60,'helper_binding_members':77,'graphics_used':False,'private_assets_read':False,'miku54_included':False,'whole_hair_complete':False,'native_junko_cause_demonstrated':False,'scope':'Reproduced feasible-orbit pole degeneracy fixed by deterministic perpendicular fallback; not sampled Junko residual-collision proof'})
    save('ORIGINS.json',{'files':ORIGINS})
    for path,(stamp,digest) in PINS.items():
        st=path.stat();assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==stamp and sha(path.read_bytes())==digest
    print(json.dumps({'status':'CURATED_INPUTS_PRESERVED','copied_or_projected_files':len(ORIGINS),'source_pins':len(PINS)}))
if __name__=='__main__':main()
