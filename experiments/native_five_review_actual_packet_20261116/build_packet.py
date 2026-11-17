"""Archive explicit safe metadata/projections only; never run apps or copy art."""
from pathlib import Path
import gzip,hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ROOT_RUN=ROOT/'output/native-hair-review-root-execution-20261116-attempt1'
RUN=ROOT/'output/native-hair-final-validation-52f63c9-20261116-attempt1'
REVIEW=ROOT.parent/'HAS-Review-20261115-Native-Hair-52f63c9'
PREP=ROOT/'experiments/native_five_review_after_full_20261116'
COMMIT='52f63c944ded7a651da871524d23a345b606424d'
copies=[];projections=[]
def sha(body):return hashlib.sha256(body).hexdigest()
def load(p):return json.loads(p.read_bytes())
def pin(p):
    body=p.read_bytes();return {'path':str(p),'bytes':len(body),'sha256':sha(body)}
def write(name,body):
    target=HERE/name;assert target.resolve().is_relative_to(HERE.resolve()) and not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(body)
def save(name,value):write(name,(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
def copy(source,name,compressed=False):
    assert source.is_file() and not source.is_symlink()
    before=source.stat();body=source.read_bytes();after=source.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    body.decode('utf-8')
    write(name,gzip.compress(body,mtime=0) if compressed else body)
    copies.append({'stored':name,'source':str(source),'raw_bytes':len(body),'raw_sha256':sha(body),'encoding':'gzip-json-exact' if compressed else 'exact-utf8'})
    return body
def main():
    root=load(ROOT_RUN/'verification.json');v=load(RUN/'verification.json');build=load(REVIEW/'BUILD-VERIFICATION.json')
    assert root['passed'] and root['checks_observed']==187 and root['examples']==4 and root['runtime_lease_released']
    assert root['process']['exit']==0 and root['process']['retained_Popen_reaped'] and not root['process']['timed_out'] and not root['process']['owned_wrapper_terminated']
    assert v['passed'] and v['source_commit']==COMMIT and not v['errors'] and len(v['results'])==4
    assert len(v['preservation'])==9 and all(v['preservation'].values()) and root['preservation']==v['preservation']
    assert sha((RUN/'verification.json').read_bytes())==root['verification_sha256']
    assert build['passed'] and build['source_commit']==COMMIT and build['native_source_files']==495 and build['native_source_bytes']==451266730
    assert build['graphics_launched'] is False and build['installed_Studio_not_written'] is True
    assert build['native_Source_solver']['solved_rules']==5 and build['native_Source_solver']['retained_rules']==49
    for f in sorted(ROOT_RUN.iterdir()):
        assert f.is_file() and f.suffix in ('.json','.log')
        copy(f,'root/'+f.name)
    for name in ('verification.json','harness-before.json','reference-inputs-before.json','runtime-generated-before.json','runtime-generated-after.json','source-delta-admission.json'):
        copy(RUN/name,'replay/'+name)
    for name in ('shipped-before.json','shipped-after.json'):
        copy(RUN/name,'replay/'+name+'.gz',True)
    assert (RUN/'shipped-before.json').read_bytes()==(RUN/'shipped-after.json').read_bytes()
    for f in sorted(REVIEW.iterdir()):
        if f.is_file():
            assert f.name in ('BUILD-STARTED.json','BUILD-VERIFICATION.json','Native-source-chooser.json','README.md','Start review.bat','Open Junko imported hair joints.bat','Open Keiki Tools.bat','Open Mima head expressions.bat','Open Nitori source choices.bat')
            copy(f,'review/'+f.name+('.gz' if f.name=='BUILD-VERIFICATION.json' else ''),f.name=='BUILD-VERIFICATION.json')
    counts=[]
    case_dirs=sorted(p for p in RUN.iterdir() if p.is_dir())
    assert len(case_dirs)==4
    for folder,process in zip(case_dirs,v['results']):
        r=load(folder/'result.json');checks=r['checks'];counts.append(len(checks))
        assert r['failures']==0 and all(row['ok'] is True for row in checks) and len(checks)==process['observed_checks']==process['expected_checks']
        assert len({row['label'] for row in checks})==len(checks)
        assert all(value is True for value in r['extra_checks'].values())
        assert r['source_manifest_sha256']==sha((RUN/'shipped-before.json').read_bytes())
        assert r['request_sha256']==sha((folder/'request.json').read_bytes())
        assert r['native_readbacks_at_finish']==0 and r['normal_startup']['signal_seen'] and r['normal_startup']['home_visible'] and r['normal_startup']['empty'] and r['normal_startup']['simple']
        assert r['normal_startup']['result']['restored'] is False and r['normal_startup']['result']['cancelled'] is False
        assert process['passed'] and process['exit']==0 and process['private_receipt_passed'] and process['strict_result_binding'] and process['retained_Popen_reaped'] and not process['timed_out']
        receipt=load(folder/'private-receipt.json')
        assert receipt['exit']==0 and all(receipt[n] is True for n in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'))
        assert not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested']
        differences=load(folder/'state-comparison.json');assert all(not x for x in differences['differences'].values())
        for name in ('command.json','private-receipt.json','process-verification.json','state-comparison.json','replay.tscn','engine.log','stdout.log','stderr.log'):
            copy(folder/name,'cases/'+folder.name+'/'+name)
        # Raw result includes camera/state arrays. Preserve only named checks,
        # scalar/image/audio digests and ordinary-startup/source identities.
        names=('format','failures','checks','extra_checks','native_readbacks_at_finish','normal_startup','audio_cache_proofs',
            'open_ms','load_worker_ms','install_ms','configured_paths','normalized_cache_root','normalized_project_folder','project_root','project_folder','profile','package','process_id','worker_pid','request_sha256','source_manifest_sha256',
            'focus_image','setup_image','native_focus','native_setup','relocated_native5')
        safe={name:r[name] for name in names if name in r}
        safe.update(archive_format='has_final_review_safe_result_projection_1',source_result=pin(folder/'result.json'),source_request_hash_only=pin(folder/'request.json'),
            omitted_private_fields=['camera_before','camera_after','runtime_objects','rasters','canvas_extent','setup_extent'],
            raw_expected_observed_project_or_image_not_copied=True)
        dest='cases/'+folder.name+'/result-projection.json';save(dest,safe)
        projections.append({'stored':dest,'source':str(folder/'result.json'),'source_sha256':sha((folder/'result.json').read_bytes()),'whitelist':list(names)})
    assert counts==[44,46,56,41] and sum(counts)==187
    junko=load(case_dirs[2]/'result.json')['relocated_native5']
    assert junko['on_created_five_rule_backend'] and junko['completed_fixed_ticks']>=1 and junko['off_exact'] and junko['ordinary_checkbox_and_physics_clock'] and junko['Record_or_fan_pipeline_repeated'] is False
    aliases={'builder/build_after_full.py':PREP/'builder/build_after_full.py','replay/validate_after_full.py':PREP/'replay/validate_after_full.py',
        'replay/replay.gd':PREP/'replay/replay.gd','replay/audio_contract.py':PREP/'replay/audio_contract.py','admission.py':PREP/'admission.py','source-delta.json':PREP/'source-delta.json',
        'root/review_run_owned.py':ROOT/'experiments/native_five_review_actual_20261116/run_owned.py','root/shared_normal_run_owned.py':ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py'}
    h=load(RUN/'harness-before.json')
    for alias,source in aliases.items():
        if str(source) in h:assert sha(source.read_bytes())==h[str(source)]['sha256']
        copy(source,'code/'+alias)
    context=load(ROOT_RUN/'source-context.json')
    assert sha(aliases['root/review_run_owned.py'].read_bytes())==context['driver_sha256']
    assert sha(aliases['root/shared_normal_run_owned.py'].read_bytes())==context['observer_sha256']
    assert context['review_packet_index_sha256']==sha((PREP/'INDEX.json').read_bytes())
    save('CODE_BINDINGS.json',{'format':'has_final_review_actual_code_bindings_1','root_context_names':{'driver_sha256':'code/root/review_run_owned.py','observer_sha256':'code/root/shared_normal_run_owned.py'},
        'active_replay_driver':'code/replay/validate_after_full.py','active_replay_observer':'code/replay/replay.gd',
        'root_shared_module_only_helpers_imported_no_main_call':True,'prepared_source_packet':pin(PREP/'INDEX.json'),
        'actual_harness_bindings':{n:r for n,r in h.items()},'native_conversion_performed':False})
    save('BENCHMARK.json',{'format':'has_native_five_final_review_actual_1','passed':True,'source_commit':COMMIT,'review':str(REVIEW),'checks':187,'examples':4,'checks_by_example':dict(zip([p.name for p in case_dirs],counts)),
        'preservation':v['preservation'],'root_seconds':root['process']['seconds'],'private_jobs':4,'all_four_private_jobs_closed':True,
        'runtime_lease_released':True,'source_functional_files':1019,'review_frozen_source_files':len(build['source_hashes']),
        'retained_native_family_files':495,'retained_native_family_bytes':451266730,'native_source_solver':build['native_Source_solver'],'relocated_native5':junko,
        'existing_examples_are_prior_trusted_DATA':True,'fresh_native_conversion_performed':False,'no_mock_or_controller_replacement':v['no_mock_or_controller_replacement'],
        'actual_graphics_validation_separate_from_copy_only_builder':True,'human_observation':'OWNER_DEFERRED_NO_RESULT','full49_SDK_artist_or_clean_install_qualified':False,
        'private_source_expected_state_geometry_PNG_audio_HAS_not_published':True,'cleanup_performed':False})
    save('SOURCE_MANIFEST.json',{'format':'has_review_actual_exact_copy_and_projection_manifest_1','copies':copies,'projections':projections})
    print(json.dumps({'prepared_archive':True,'checks':187,'cases':4,'copies':len(copies),'safe_result_projections':len(projections)}))
if __name__=='__main__':main()
