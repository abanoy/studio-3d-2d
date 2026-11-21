"""Collect exact safe text from the closed Root StageA failure, never native art."""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,os,re,stat,shutil
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT.parent/'has-junko-native-stage-a-1795270452664135900'
PACKET=ROOT/'output/source-junko-stage-a-failure-evidence-prep-20261121'
HOST=ROOT/'output/source-junko-stage-a-root-driver-v2-prep-20261121'
CAND=ROOT/'output/source-junko-body-dress-native-binding-prep-20261121'
HOST_SHA='d4ab53c3fa5e747e9a59de8a162e867742ff97904b0628eca410146d2f0a3e5c'
DRIVER_SHA='fa77cac428e8475444de61e4bd4b2be5db8007d3a8537c2b2cb1e87921c838f2'
CAND_SHA='9989f3f2746e37666dc541ef44990a71d757f4d4d7eaa035e0525a81eb357913'
ROWS={}
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def ident(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,getattr(s,'st_file_attributes',0))
def read(path,limit=16*1024*1024):
 for p in (path,*path.parents):
  s=p.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,p
 s=path.stat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit,path
 raw=path.read_bytes();assert ident(path.stat())==ident(s),path
 key=str(path);value=(ident(s),pin(raw));assert key not in ROWS or ROWS[key]==value,path;ROWS[key]=value;return raw
def parse(path):return json.loads(read(path))
def rel(name):
 p=PurePosixPath(name);assert name==p.as_posix() and p.parts and not p.is_absolute() and all(x not in ('.','..') and ':' not in x and '\\' not in x for x in p.parts);return Path(*p.parts)
def write(name,value):
 p=PACKET/rel(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def copy(path,name):
 raw=read(path);raw.decode('utf-8-sig');assert b'\0' not in raw
 p=PACKET/rel(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 return {'path':name,'origin':str(path),**pin(raw)}
def main():
 assert not PACKET.exists();result=parse(STAGE/'PUBLIC_RESULT.json')
 assert result['format']=='has_junko_body_dress_stage_a_1' and result['status']=='FAIL' and result['checks']==16
 assert result['revision']=='2f1acbd7867087d9f18cfbc1122cc0c883c5f788' and set(result['jobs'])=={'unit16','body'} and result['conversions']=={}
 assert result['jobs']['unit16']['status']=='PASS' and result['jobs']['body']['status']=='FAIL'
 assert all(result[k] is True for k in ('all_jobs_closed','all_memberships_and_Main_preserved','parent_environment_preserved','all_admitted_inputs_preserved','lock_removed'))
 assert result['preservation_failure_count']==0 and result['source_input_file_count']==2859
 assert all(result[k] is False for k in ('graphics_executed','Full_claimed','native_simulation_qualified','Godot_binding_qualified','application_modified','private_arrays_published'))
 for row in result['jobs'].values():
  assert all(row[k] is True for k in ('wrapper_reaped','wrapper_handle_closed','job_closed','active_zero_before_close','assigned_before_START'))
  assert row['accounting']['active']==0 and row['accounting']['terminated_by_limit']==0
 assert pin(read(HOST/'SOURCE_PINS.json'))['sha256']==HOST_SHA
 assert pin(read(HOST/'run_stage_a.py'))['sha256']==DRIVER_SHA
 assert pin(read(CAND/'SOURCE_PINS.json'))['sha256']==CAND_SHA
 closure=parse(CAND/'RUNTIME_SOURCE_CLOSURE.json');assert len(closure['files'])==114
 actual=[]
 for row in closure['files']:
  p=STAGE/'Studio'/rel(row['path']);raw=read(p)
  assert pin(raw)=={'bytes':row['bytes'],'sha256':row['sha256']},p
  actual.append({'path':row['path'],**pin(raw)})
 runtime={p.relative_to(STAGE/'Studio').as_posix() for p in (STAGE/'Studio').rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 assert runtime=={r['path'] for r in actual}
 unit=(read(STAGE/'jobs/unit16/child-stdout.log')+read(STAGE/'jobs/unit16/child-stderr.log')).decode('utf-8').replace('\r\n','\n')
 assert len(re.findall(r'^test_.* \.\.\. ok$',unit,re.M))==16 and re.search(r'Ran 16 tests? in [0-9.]+s\s+OK\s*$',unit)
 assert not re.search(r'FAILED|ERROR|Traceback',unit)
 PACKET.mkdir();origins=[copy(STAGE/'PUBLIC_RESULT.json','evidence/PUBLIC_RESULT.json')]
 for job in ('unit16','body'):
  folder=STAGE/'jobs'/job;proof=parse(folder/'worker-receipt.json');owner=parse(folder/'OWNERSHIP.json')
  assert owner['closure_proven'] is True and owner['phase']=='CLOSED_BEFORE_ASSERTION_CHECKS'
  assert proof['gate_accepted'] is True and proof['child_launched'] is True and proof['child_reaped'] is True and proof['child_handle_closed'] is True
  assert proof['wrapper_identity']==result['jobs'][job]['owner']
  assert proof['status']==('PASS' if job=='unit16' else 'FAIL') and proof['child_exit']==(0 if job=='unit16' else 1)
  for leaf in ('child-stdout.log','child-stderr.log','wrapper-stdout.log','wrapper-stderr.log','worker-receipt.json','OWNERSHIP.json','launch.json'):
   origins.append(copy(folder/leaf,'evidence/jobs/'+job+'/'+leaf))
 # Preserve the exact last traceback/tail only. All preceding converter output,
 # partial native bundle and raw identities remain external and private.
 logpath=STAGE/'Bundles/body/conversion.log';raw=read(logpath,64*1024*1024)
 begin=raw.rfind(b'Traceback (most recent call last):');assert begin>=0
 tail=raw[begin:];assert 0<len(tail)<=16*1024 and b'native_Blender_rest_matrix_mismatch' in tail and b'line 216, in prove_native_blender' in tail
 assert b'JUNKO_PART_EXPORT_IDENTITY ' not in raw and b'\0' not in tail
 for forbidden in (b'Blender_matrix_local_row_major',b'native_rest_words_uint32',b'raw_source_weights',b'JOINTS_0',b'WEIGHTS_0'):
  assert forbidden not in tail
 tail.decode('utf-8');(PACKET/'evidence/body-last-traceback.log').write_bytes(tail)
 write('TRACE_PROVENANCE.json',{'format':'has_exact_log_fragment_provenance_1','whole_origin':str(logpath),'whole_log_copied':False,**pin(raw),'fragment_path':'evidence/body-last-traceback.log','fragment_byte_offset':begin,'fragment_bytes':len(tail),'fragment_sha256':pin(tail)['sha256'],'byte_exact_slice_to_EOF':True,'interpretation':'Actual first native Body proof refused at existing strict native_Blender_rest_matrix_mismatch; numerical cause unmeasured here.'})
 write('EVIDENCE_ORIGINS.json',{'format':'has_junko_stage_a_safe_evidence_origins_1','files':origins})
 write('RUNTIME_SOURCE_PROOF.json',{'format':'has_junko_stage_a_exact_source_binding_1','host_source_pins_sha256':HOST_SHA,'host_driver_sha256':DRIVER_SHA,'native_candidate_source_pins_sha256':CAND_SHA,'runtime114_actual_readback_matches':True,'files':actual,'execution_author':'Root retained process run; collector did not execute a runtime','Main1109_and2859_preservation':'Actual Root public receipt, not rerun by this collector'})
 write('SCOPE.json',{'format':'has_junko_stage_a_actual_failure_scope_1','status':'ACTUAL_FAIL16','pure_controls_passed':16,'attempted_jobs':2,'Body_export_binding':'FAILED_BEFORE_COMPLETE_EXPORT_PROOF','Dress':'UNSTARTED','actual_conversions_qualified':0,'both_attempted_jobs_closed_reaped_active0':True,'source_inputs_preserved':2859,'Root_revision':result['revision'],'diagnosis_or_tolerance_change':False,'Godot54_inverse_bind_or_follow_qualified':False,'Full_result_reclassified':False,'private_assets_arrays_or_whole_log_copied':False})
 (PACKET/'README.md').write_text('''# Actual Junko StageA failure: preserve the strict refusal

Root ran the frozen StageA v2 fa77/d4ab host against published2f1acbd and the
9989f3 native probe. The16 pure controls passed. Body then failed in the existing
strict native-to-Blender rest-matrix proof at source_jiggle_crosswalk.py:216.
Dress was not started. No actual conversion/export binding is qualified.

Both attempted Root Jobs closed with active0; retained wrapper/child handles were
closed,2859 admitted inputs/Main1109/environment were preserved and lock removed.
These claims are bound to the copied actual public result and raw closure receipts.
The collector additionally read/hash-checked all114 actual runtime source files
against the frozen candidate closure and independently counted all16 unit lines.
It executed no runtime, converter, graphics, app or Full tests.

The exact last traceback is an attributed byte range of the retained complete
conversion log. The complete log, partial bundle, original/copy native assets,
SDK binaries, matrices/skin/native-word arrays and private identity inventories
remain local at the original stage and are not included. No numerical cause,
repair, tolerance waiver, Dress success,54-link/Godot calibration, simulation,
fidelity or successful Full is inferred. The first failed attempt remains failed.
''',encoding='utf-8')
 (PACKET/'code_used').mkdir();shutil.copyfile(__file__,PACKET/'code_used'/Path(__file__).name)
 # Every read source remains the exact same full-native identity and hash.
 for path in list(ROWS):read(Path(path))
 write('READBACK.json',{'status':'PASS','all_admitted_origin_identities_and_hashes_preserved':True,'runtime_source_files_checked':114,'safe_raw_evidence_files':len(origins),'pure_case_lines_checked':16,'original_stage_mutated':False,'runtime_executed_by_collector':False,'privacy_scope':'Explicit reviewed text allowlist and bounded traceback; not a general semantic privacy certification.'})
 files=[]
 for path in sorted(PACKET.rglob('*')):
  if path.is_file():
   b=path.read_bytes();b.decode('utf-8-sig');assert b'\0' not in b
   assert path.suffix in ('.py','.json','.log','.md');files.append({'path':path.relative_to(PACKET).as_posix(),**pin(b)})
 write('SOURCE_PINS.json',{'format':'has_junko_stage_a_failure_evidence_pins_1','status':'ACTUAL_FAIL16_PRESERVED_NO_RUNTIME_BY_COLLECTOR','files':files})
 print(json.dumps({'packet':str(PACKET),'files':len(files)+1,'payload_bytes':sum(r['bytes'] for r in files),'manifest':pin((PACKET/'SOURCE_PINS.json').read_bytes()),'actual_status':'FAIL16','collector_CPU_readback':'PASS'},indent=2))
if __name__=='__main__':main()
