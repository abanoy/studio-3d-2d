"""Collect exact safe text from the closed Root StageA failure, never native art."""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,os,re,stat,shutil
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT.parent/'has-junko-factory-boundary-diagnostic-v4-1795273816968444900'
PACKET=ROOT/'output/source-junko-factory-boundary45-evidence-prep-20261121'
HOST=ROOT/'output/source-junko-factory-boundary-v4-root-driver-prep-20261121'
CAND=ROOT/'output/source-junko-factory-boundary-diagnostic-prep-20261121'
HOST_SHA='20f2dcfd7d95127ab3b139b3cc87a99c74e00aa869a21c672027c40c163a1bcc'
DRIVER_SHA='583f4be48984b68e165f6db7dfd9fb1f320c771c4a968df8af00c8087b3d9e79'
CAND_SHA='5a07872ec538d18835c01f1f11b83ea24ae69858a9ead03fa0f31c9dd1640974'
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
 assert result['format']=='has_junko_factory_boundary_diagnostic_v4_1' and result['status']=='EXPECTED_REFUSAL_WITH_DIAGNOSTIC' and result['checks']==45
 assert result['revision']=='2f1acbd7867087d9f18cfbc1122cc0c883c5f788' and set(result['jobs'])=={'unit45','body'} and result['conversions']=={}
 assert result['jobs']['unit45']['status']=='PASS' and result['jobs']['body']['status']=='EXPECTED_CHILD_REFUSAL'
 assert all(result[k] is True for k in ('all_jobs_closed','all_memberships_and_Main_preserved','parent_environment_preserved','all_admitted_inputs_preserved','lock_removed'))
 assert result['preservation_failure_count']==0 and result['source_input_file_count']==2934
 assert all(result[k] is False for k in ('graphics_executed','Full_claimed','native_simulation_qualified','Godot_binding_qualified','application_modified','private_arrays_published'))
 for row in result['jobs'].values():
  assert all(row[k] is True for k in ('wrapper_reaped','wrapper_handle_closed','job_closed','active_zero_before_close','assigned_before_START'))
  assert row['accounting']['active']==0 and row['accounting']['terminated_by_limit']==0
 assert pin(read(HOST/'SOURCE_PINS.json'))['sha256']==HOST_SHA
 assert pin(read(HOST/'run_stage_a.py'))['sha256']==DRIVER_SHA
 assert pin(read(CAND/'SOURCE_PINS.json'))['sha256']==CAND_SHA
 closure=parse(CAND/'RUNTIME_SOURCE_CLOSURE.json');assert len(closure['files'])==118
 actual=[]
 for row in closure['files']:
  p=STAGE/'Studio'/rel(row['path']);raw=read(p)
  assert pin(raw)=={'bytes':row['bytes'],'sha256':row['sha256']},p
  actual.append({'path':row['path'],**pin(raw)})
 runtime={p.relative_to(STAGE/'Studio').as_posix() for p in (STAGE/'Studio').rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 assert runtime=={r['path'] for r in actual}
 unit=(read(STAGE/'jobs/unit45/child-stdout.log')+read(STAGE/'jobs/unit45/child-stderr.log')).decode('utf-8').replace('\r\n','\n')
 assert len(re.findall(r'^test_.* \.\.\. ok$',unit,re.M))==45 and re.search(r'Ran 45 tests? in [0-9.]+s\s+OK\s*$',unit)
 assert not re.search(r'FAILED|ERROR|Traceback',unit)
 PACKET.mkdir();origins=[copy(STAGE/'PUBLIC_RESULT.json','evidence/PUBLIC_RESULT.json')]
 for job in ('unit45','body'):
  folder=STAGE/'jobs'/job;proof=parse(folder/'worker-receipt.json');owner=parse(folder/'OWNERSHIP.json')
  assert owner['closure_proven'] is True and owner['phase']=='CLOSED_BEFORE_ASSERTION_CHECKS'
  assert proof['gate_accepted'] is True and proof['child_launched'] is True and proof['child_reaped'] is True and proof['child_handle_closed'] is True
  assert proof['wrapper_identity']==result['jobs'][job]['owner']
  assert proof['status']==('PASS' if job=='unit45' else 'EXPECTED_CHILD_REFUSAL') and proof['child_exit']==(0 if job=='unit45' else 1)
  for leaf in ('child-stdout.log','child-stderr.log','wrapper-stdout.log','wrapper-stderr.log','worker-receipt.json','OWNERSHIP.json','launch.json'):
   origins.append(copy(folder/leaf,'evidence/jobs/'+job+'/'+leaf))
 # Copy only the one public scalar marker, with exact full-log byte provenance.
 # Never read/copy the private sidecar or publish the full converter log.
 logpath=STAGE/'Bundles/body/conversion.log';raw=read(logpath,64*1024*1024)
 diagnostic=result['diagnostic'];scalar=diagnostic['scalar_errors']
 assert diagnostic['status']=='EXPECTED_REFUSAL_WITH_DIAGNOSTIC' and diagnostic['original_close_predicate_still_false'] is True
 assert result['dress_started'] is False and all(diagnostic[k] is False for k in ('source_rest_tolerance_changed','diagnosed_cause_claimed','reference_pose_or_later_factory_writes_ruled_out','export_binding_qualified','Godot_binding_qualified','native_simulation_qualified'))
 assert pin(raw)['sha256']==diagnostic['conversion_log_sha256']
 assert diagnostic['five_factory_boundaries_recorded'] is True and diagnostic['private_refpose_flags_recorded'] is True and len(scalar)==18
 prefix=b'JUNKO_PART_REST_DIAGNOSTIC '
 markers=[(i,line) for i,line in enumerate(raw.splitlines(keepends=True)) if line.startswith(prefix)]
 assert len(markers)==1
 number,line=markers[0];assert len(line)<=4096 and json.loads(line[len(prefix):])==scalar
 assert type(scalar['first_native_index'])is int and scalar['first_native_index']==38
 assert all(type(v) in (int,float) and __import__('math').isfinite(v) for v in scalar.values())
 assert b'JUNKO_PART_REST_DIAGNOSTIC_CAPTURE_FAILED' not in raw and b'JUNKO_PART_EXPORT_IDENTITY ' not in raw
 assert b'source_jiggle_crosswalk.CrosswalkError: native_Blender_rest_matrix_mismatch' in raw
 offset=sum(len(x) for x in raw.splitlines(keepends=True)[:number])
 assert raw[offset:offset+len(line)]==line
 (PACKET/'evidence/public-scalar-marker.log').write_bytes(line)
 write('SCALAR_PROVENANCE.json',{'format':'has_exact_public_scalar_log_fragment_1','whole_origin':str(logpath),'whole_log_copied':False,**pin(raw),'fragment_path':'evidence/public-scalar-marker.log','fragment_byte_offset':offset,'fragment_bytes':len(line),'fragment_sha256':pin(line)['sha256'],'byte_exact_slice':True,'private_sidecar_read_or_copied_by_collector':False,'interpretation':'Measured first rest-refusal scalar errors only. Existing close() remains false; no numerical cause or repair concluded.'})
 write('PRIVATE_ARTIFACTS_EXTERNAL.json',{'private_sidecar_path':str(STAGE/'Bundles/body/PRIVATE_first_rest_refusal.json'),'sha256_as_recorded_by_actual_Root':diagnostic['private_diagnostic_sha256'],'collector_read_private_sidecar':False,'copied_assets_or_arrays':False})
 write('EVIDENCE_ORIGINS.json',{'format':'has_junko_stage_a_safe_evidence_origins_1','files':origins})
 write('RUNTIME_SOURCE_PROOF.json',{'format':'has_junko_stage_a_exact_source_binding_1','host_source_pins_sha256':HOST_SHA,'host_driver_sha256':DRIVER_SHA,'native_candidate_source_pins_sha256':CAND_SHA,'runtime118_actual_readback_matches':True,'files':actual,'execution_author':'Root retained process run; collector did not execute a runtime','Main1109_and2934_preservation':'Actual Root public receipt, not rerun by this collector'})
 write('SCOPE.json',{'format':'has_junko_factory_boundary45_actual_scope_1','status':'EXPECTED_REFUSAL_WITH_DIAGNOSTIC','pure_controls_passed':45,'pure_composition':[16,9,20],'prior25_are_included_not_additional':True,'must_not_be_reported_as70_unique':True,'attempted_jobs':2,'Body':'EXPECTED_ORIGINAL_REST_REFUSAL_WITH_FACTORY_BOUNDARY_SCALARS','Dress':'UNSTARTED','qualified_conversions':0,'both_attempted_jobs_closed_reaped_active0':True,'source_inputs_preserved':2934,'Root_revision':result['revision'],'original_tolerance_changed':False,'diagnosed_cause_claimed':False,'Godot54_inverse_bind_or_follow_qualified':False,'Full_result_reclassified':False,'private_assets_arrays_matrices_names_or_whole_log_copied':False})
 (PACKET/'README.md').write_text("""# Actual factory boundary diagnostic45

Root ran v4host583f/20f2 and candidate5a078 against Main2f1acbd. All45 pure
controls passed:16 original+9 delegation+20 boundary cases. The old25 are included,
not70 distinct tests. Body retained the original native rest-matrix refusal at
index38; Dress never started and zero native conversions/export bindings qualify.
Both retained wrapper/child handles closed, Root Jobs ended active0,2934 admitted
inputs/Main1109/environment were preserved and the owned lock was removed.

The actual scalar measurements separate these observed boundaries: assignment to
immediate EditBone getter4.774332046508789e-5, later Edit changes0,
Edit-to-Object transition4.291534423828125e-6 and Object-to-final proof0.
Assignment-to-native reference error was9.558213465155063e-8; the bone length was
0.019050002098083496 before and after. Complete18 scalar values stay exact in the
public result and exact raw marker line. These measurements locate differences;
they do not establish the numerical cause or a repair. The original close()==false
and tolerance/model data remained unchanged.

The collector independently hash-checked118 actual Studio source files to the
frozen candidate, counted45 raw unittest OK lines, and verified both raw worker/
Job closure records. No runtime/Blender/GPU/Main/Full tests ran in this collector.
Only one public scalar marker was copied from the converter log, with the entire
log's SHA/size and exact byte range. The private sidecar was not read or copied;
matrices,bone names,words,pointers,assets,private inventories and whole logs stay
local. No successful native export,54-link/Godot/skin/follow/simulation/fidelity or
Full result is inferred. StageA FAIL16 and expected-refusal25 remain unchanged.
""",encoding='utf-8')
 (PACKET/'code_used').mkdir();shutil.copyfile(__file__,PACKET/'code_used'/Path(__file__).name)
 # Every read source remains the exact same full-native identity and hash.
 for path in list(ROWS):read(Path(path))
 write('READBACK.json',{'status':'PASS','all_admitted_origin_identities_and_hashes_preserved':True,'runtime_source_files_checked':118,'safe_raw_evidence_files':len(origins),'pure_case_lines_checked':45,'original_stage_mutated':False,'runtime_executed_by_collector':False,'privacy_scope':'Explicit reviewed text allowlist and bounded traceback; not a general semantic privacy certification.'})
 files=[]
 for path in sorted(PACKET.rglob('*')):
  if path.is_file():
   b=path.read_bytes();b.decode('utf-8-sig');assert b'\0' not in b
   assert path.suffix in ('.py','.json','.log','.md');files.append({'path':path.relative_to(PACKET).as_posix(),**pin(b)})
 write('SOURCE_PINS.json',{'format':'has_junko_factory_boundary45_evidence_pins_1','status':'ACTUAL_FACTORY_DIAGNOSTIC45_NO_RUNTIME_BY_COLLECTOR','files':files})
 print(json.dumps({'packet':str(PACKET),'files':len(files)+1,'payload_bytes':sum(r['bytes'] for r in files),'manifest':pin((PACKET/'SOURCE_PINS.json').read_bytes()),'actual_status':'EXPECTED_REFUSAL_WITH_FACTORY_DIAGNOSTIC45','collector_CPU_readback':'PASS'},indent=2))
if __name__=='__main__':main()
