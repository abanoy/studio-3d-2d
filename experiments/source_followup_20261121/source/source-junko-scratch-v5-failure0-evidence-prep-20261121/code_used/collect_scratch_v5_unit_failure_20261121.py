"""Exact safe failure evidence only; no private capture, Blender or model reads."""
from pathlib import Path
import hashlib,json,re,stat,shutil
R=Path(__file__).resolve().parents[1]
S=R.parent/'has-junko-scratch-rest-v5-1795274686016416200'
D=R/'output/source-junko-scratch-v5-failure0-evidence-prep-20261121'
H=R/'output/source-junko-scratch-v5-root-driver-prep-20261121'
C=R/'output/source-junko-scratch-rest-representation-prep-20261121'
seen={}
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def stamp(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,getattr(s,'st_file_attributes',0))
def read(p):
 for a in (p,*p.parents):
  s=a.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,a
 s=p.stat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=1024*1024,p
 raw=p.read_bytes();assert stamp(p.stat())==stamp(s);row=(stamp(s),pin(raw));assert str(p) not in seen or seen[str(p)]==row;seen[str(p)]=row;return raw
def write(name,value):(D/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
 assert not D.exists();result=json.loads(read(S/'PUBLIC_RESULT.json'))
 assert result['format']=='has_junko_scratch_rest_v5_root_1' and result['status']=='FAIL' and result['checks']==0
 assert set(result['jobs'])=={'unit12'} and result['measurement']=={} and result['scratch_cases']==0
 assert all(result[k] is True for k in ('all_jobs_closed','all_admitted_inputs_preserved','Main_and_runtime_preserved','parent_environment_preserved','lock_removed')) and result['source_input_file_count']==1144 and result['preservation_failure_count']==0
 row=result['jobs']['unit12'];assert row['status']=='FAIL' and row['wrapper_exit']==1
 assert all(row[k] is True for k in ('wrapper_reaped','wrapper_handle_closed','job_closed','active_zero_before_close','assigned_before_START')) and row['accounting']['active']==0 and row['accounting']['terminated_by_limit']==0
 proof=json.loads(read(S/'jobs/unit12/worker-receipt.json'));owner=json.loads(read(S/'jobs/unit12/OWNERSHIP.json'))
 assert owner['closure_proven'] is True and proof['status']=='FAIL' and proof['child_exit']==1 and proof['wrapper_identity']==row['owner']
 assert all(proof[k] is True for k in ('gate_accepted','child_launched','child_reaped','child_handle_closed'))
 stderr=read(S/'jobs/unit12/child-stderr.log').decode('utf-8').replace('\r\n','\n')
 assert re.search(r'Ran 12 tests? in [0-9.]+s\s+FAILED \(failures=1\)\s*$',stderr)
 assert 'test_measured_row_uses_original_close' in stderr and 'AssertionError: False is not true' in stderr
 assert len(re.findall(r'^test_.* \.\.\. ok$',stderr,re.M))==11
 assert pin(read(H/'SOURCE_PINS.json'))['sha256']=='5140f53058ab4dddaedccd2f3428b0ead4af7a97fb009f43d143150b2980b20a'
 assert pin(read(C/'SOURCE_PINS.json'))['sha256']=='9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015'
 closure=json.loads(read(C/'RUNTIME_SOURCE_CLOSURE.json'));actual=[]
 for x in closure['files']:
  p=S/'Studio'/x['path'];b=read(p);assert pin(b)=={'bytes':x['bytes'],'sha256':x['sha256']};actual.append({'path':x['path'],**pin(b)})
 assert len(actual)==3
 D.mkdir();(D/'evidence').mkdir();origins=[]
 for src,name in [(S/'PUBLIC_RESULT.json','PUBLIC_RESULT.json')]+[(S/'jobs/unit12'/n,'unit12-'+n) for n in ('child-stdout.log','child-stderr.log','wrapper-stdout.log','wrapper-stderr.log','worker-receipt.json','OWNERSHIP.json','launch.json')]:
  b=read(src);b.decode('utf-8-sig');assert b'\0' not in b;(D/'evidence'/name).write_bytes(b);origins.append({'path':'evidence/'+name,'origin':str(src),**pin(b)})
 write('SCOPE.json',{'format':'has_scratch_v5_actual_unit_failure_1','status':'ACTUAL_FAIL0','unit_batch_pass_credit':0,'individual_ok_lines_observed_not_batch_credit':11,'failed_methods':1,'total_attempted_tests':12,'Blender_started':False,'scratch_measurements':0,'private_capture_or_matrices_read_by_collector':False,'all_one_owned_job_reaped_closed_active0':True,'admitted_inputs_preserved':1144,'source_host_manifest':'5140f53058ab4dddaedccd2f3428b0ead4af7a97fb009f43d143150b2980b20a','source_candidate_manifest':'9557dff66394116bb5b7049f036e6674195171f98da6a0ed895ce8bd86dac015','runtime3_source_hashes':actual,'root_revision':result['revision'],'production_or_native_tolerance_changed':False,'new_Full_or_model_repair_qualification':False})
 write('EVIDENCE_ORIGINS.json',{'files':origins})
 (D/'README.md').write_text('''# Scratch v5 actual unit failure, zero batch credit

Root attempted the frozen9557 helper/5140 host. One of12 pure tests failed:
test_measured_row_uses_original_close. Eleven individual OK lines are preserved,
but the batch receives0 pass credit; no Blender/scratch job started and no native
model/export/repair/Full qualification is inferred. One Root Job closed active0,
both retained handles closed,1144 admitted inputs/Main/environment stayed exact
and lock was removed, as copied actual receipts show.

Source-level cause: measured_row deliberately converts rest to a tuple. The fake
close callback a==b compared it to a list reference and rejected equal numbers.
This concerns the synthetic callback, not the immutable production close predicate.
A separately versioned fixture changes positive/negative callbacks to compare
sequence contents; the original failed fixture/results remain unchanged.

Collector independently checked raw12-test/one-failure output, closure and all3
runtime source hashes. Only safe text was copied. No private capture/sidecar,
matrix,name/native-word arrays,SDK/assets/model or complete runtime was read/copied.
Collector executed no tests/Blender/GPU/Main/Full programs.
''',encoding='utf-8')
 (D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
 for path in list(seen):read(Path(path))
 write('READBACK.json',{'status':'PASS','all_safe_origin_hashes_and_fullnative_identity_preserved':True,'engine_or_test_execution_by_collector':False})
 rows=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file()]
 write('SOURCE_PINS.json',{'format':'has_scratch_v5_fail0_evidence_pins_1','status':'ACTUAL_FAIL0_PRESERVED','files':rows})
 print(json.dumps({'packet':str(D),'files':len(rows)+1,'payload_bytes':sum(x['bytes'] for x in rows),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'collector_CPU_readback':'PASS'},indent=2))
if __name__=='__main__':main()
