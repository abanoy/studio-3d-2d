"""Independent read-only postflight; never interpret a live or partial Full as pass."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,time

root=Path(__file__).resolve().parents[1]
full=root.parent/'has-import-info-full-20261121-5d37647c'
inner=full/'output/windows-reference-body-1795288143754941900'
outer=full/'output/root-full-launch-1795288143519539300'
revision='5d37647c0004849247239817364e093c010eddd6'
def read(p):return json.loads(p.read_bytes())
end=read(inner/'completion.json');outside=read(outer/'completion.json')
assert end['whole_verifier_pass'] is True and end['exit']==0 and end['result_groups']==183
assert outside['exit']==0 and outside['child_reaped'] is True
assert all(outside[k] is True for k in ['parent_environment_unchanged','coordinator_source_unchanged','revision_unchanged'])
assert end['revision']==revision and end['child_reaped'] is True
assert all(end[k] is True for k in ['functional_sources_unchanged','revision_unchanged','fresh_final_report','all_private_jobs_isolated_closed','receipt_provenance_verified','nonzero_jobs_are_expected_cancellations'])
spec=importlib.util.spec_from_file_location('full5d_audit_source',full/'experiments/reference_body_20261120/run_full.py')
coordinator=importlib.util.module_from_spec(spec);spec.loader.exec_module(coordinator)
before,after=read(inner/'source-before.json'),read(inner/'source-after.json')
assert before==after==coordinator.snapshot()
assert {n:r['git_sha1'] for n,r in before.items()}==coordinator.committed_sources(revision)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=full).decode().strip()==revision
prior=read(inner/'prior-receipts.json');actual=coordinator.receipts();classification=coordinator.classify(prior,actual)
assert not classification['conflicts'] and not classification['changed_original_archives']
recorded={r['path']:r for r in read(inner/'receipt-provenance.json')['current']}
now={r['path']:r for r in classification['current']};assert recorded==now
jobs=[]
headless={r['path'] for r in end['import_info_headless_receipts']}
for row in end['current_jobs']:
    assert now[row['path']]==row
    receipt=row['value']
    assert receipt['job_closed'] is True and receipt['desktop_closed'] is True
    assert receipt['foreground_child_observed'] is False and receipt['desktop_switch_requested'] is False
    assert row['path'] in headless or receipt['child_desktop_confirmed'] is True
    jobs.append({'path':row['path'],'sha256':row['sha256'],**{k:receipt.get(k) for k in ['desktop','child_pid','exit','seconds','job_closed','desktop_closed','child_desktop_confirmed','private_window_seen','foreground_child_observed','desktop_switch_requested','cancelled','error']},'headless_lifecycle_only':row['path'] in headless})
assert len(jobs)==end['unique_current_private_jobs']
nonzero=[r for r in jobs if r['exit']!=0]
assert len(nonzero)==1 and nonzero[0]['exit']==2 and nonzero[0]['cancelled'] is True and nonzero[0]['error']=='Owned converter cancelled'
staged=read(full/'output/reference-body-legacy-staging.json')
for row in staged['files']:
    path=Path(row['source']);s=path.stat()
    assert s.st_size==row['bytes'] and s.st_mtime_ns==row['mtime_ns'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
report=read(full/'output/verification.json');assert len(report)==183
out=root/'output'/('full5d-postflight-'+str(time.time_ns()));out.mkdir()
result={'format':'has_full5d_independent_postflight_1','status':'PASS','revision':revision,
    'canonical_groups':len(report),'functional_sources':len(before),'all_current_sources_raw_blob_hash_size_mtime_unchanged':True,
    'unique_current_private_jobs':len(jobs),'private_receipt_paths':len(now),'headless_import_info_cases':len(headless),
    'all_current_jobs_and_desktops_closed_no_foreground':True,'one_expected_cancel_only':True,
    'original_fixture_files':len(staged['files']),'original_fixture_bytes':sum(r['bytes'] for r in staged['files']),
    'all_staged_fixture_originals_hash_size_mtime_unchanged':True,'movie_groups':end['movie_groups'],
    'inner_seconds':end['seconds'],'outer_seconds':outside['seconds'],
    'scope':'Frozen published5d only; later VoxelGI and natural-gravity additions are separate',
    'private_art_published':False}
for name,value in [('verification.json',result),('current_private_jobs.json',jobs)]:
    (out/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())
print(json.dumps({'folder':str(out),**result},indent=2))
