"""Independent postflight for the exact published source; never repairs a report."""
from pathlib import Path
import hashlib,json,subprocess,time

CONTROL=Path(__file__).resolve().parent
ROOT=Path('C:/a/Programming/cloudflare/has-ui-camera-full-20261121-435dc02')
RUN=ROOT/'output/windows-reference-body-1795253708684469500'
REV='435dc02426a7cdd313e43fe674c9008520845428'
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def read(path):
    before=path.stat();raw=path.read_bytes();after=path.stat()
    need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'Changing evidence: '+str(path))
    return json.loads(raw),{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def git(*args):
    return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=ROOT).decode().strip()
audit,audit_pin=read(CONTROL/'FULL182_REGISTRATION_AUDIT_20261121.json')
completion,completion_pin=read(RUN/'completion.json')
report,report_pin=read(ROOT/'output/verification.json')
before,before_pin=read(RUN/'source-before.json')
after,after_pin=read(RUN/'source-after.json')
launch,launch_pin=read(RUN/'launch.json')
expected,expected_pin=read(CONTROL/'UI_CAMERA_FINAL_SOURCE_20261121.json')
need(completion['revision']==REV==launch['revision']==git('rev-parse','HEAD'),'Revision mismatch')
need(type(completion['exit']) is int and completion['exit']==0,'Full process failed')
for key in ('child_reaped','functional_sources_unchanged','revision_unchanged','fresh_final_report',
            'all_private_jobs_isolated_closed','nonzero_jobs_are_expected_cancellations',
            'receipt_provenance_verified','whole_verifier_pass'):
    need(completion.get(key) is True,'Full coordinator gate failed: '+key)
need(completion['functional_source_count']==1102 and before==after and len(before)==1102,'Source closure mismatch')
need(before_pin==after_pin,'Source snapshot bytes differ')
rows={r['path']:r for r in expected['files']}
need(set(rows)==set(before),'Functional source membership differs from published source')
for name,row in rows.items():
    need(all(before[name][k]==row[k] for k in ('bytes','sha256','git_sha1')),'Published source mismatch: '+name)
need(set(report)==set(audit['expected_group_keys']) and len(report)==182==completion['result_groups'],'Exact Full182 key set differs')
need(len(completion['movie_groups'])==21,'Movie group count changed')
new={}
for name,count in audit['new_groups'].items():
    row=report[name]
    need(row.get('status')=='PASS' and type(row.get('checks')) is int and row['checks']==count,'New group failed/count mismatch: '+name)
    need(row.get('all_admitted_sources_unchanged') is True,'New group source preservation failed: '+name)
    if name.startswith('editor_controls_'): need(row.get('generated_fixture_preserved') is True,'Generated fixture changed: '+name)
    new[name]={'status':row['status'],'checks':count}
need(sum(r['checks'] for r in new.values())==626,'New check total mismatch')
need((ROOT/'output/verification.json').stat().st_mtime_ns>=launch['started_ns'],'Stale final report')
nonzero=completion['nonzero_private_jobs']
need(len(nonzero)==1 and nonzero[0]['value']['exit']==2 and nonzero[0]['value']['cancelled'] is True
     and nonzero[0]['value']['error']=='Owned converter cancelled','Unexpected private job failure')
need(git('rev-parse','HEAD')==REV,'Revision changed during postflight')
result={'format':'has_full182_root_postflight_1','status':'PASS','revision':REV,
 'functional_source_count':1102,'exact_group_count':182,'exact_group_keys_match':True,
 'new_groups':new,'new_checks':626,'movie_groups':completion['movie_groups'],
 'seconds':completion['seconds'],'current_private_jobs':completion['unique_current_private_jobs'],
 'all_private_jobs_isolated_closed':True,'only_nonzero_private_job_is_expected_converter_cancellation':True,
 'fresh_source_before_after_bytes_equal':True,'source_exact_published_1102':True,
 'pins':{'completion':completion_pin,'report':report_pin,'source_before':before_pin,
         'source_after':after_pin,'launch':launch_pin,'registration_audit':audit_pin,'published_source':expected_pin},
 'root_exec_session':87359,'coordinator_pid':launch['coordinator_pid'],'verifier_pid':launch['pid'],
 'human_device_acceptance_claimed':False,'timestamp_ns':time.time_ns()}
(CONTROL/'UI_CAMERA_FULL182_ROOT_POSTFLIGHT_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
