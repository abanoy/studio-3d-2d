"""Collect exact safe text from the closed Root StageA failure, never native art."""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,os,re,stat,shutil
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT.parent/'has-junko-native-rest-diagnostic-v3-1795272061506205200'
PACKET=ROOT/'output/source-junko-first-rest-diagnostic25-evidence-prep-20261121'
HOST=ROOT/'output/source-junko-stage-a-rest-diagnostic-v3c-root-driver-prep-20261121'
CAND=ROOT/'output/source-junko-body-dress-rest-diagnostic-prep-20261121'
HOST_SHA='ae92f83c942de6d480190b8197bc541fd8ef8004e33af54292291affd8a2be03'
DRIVER_SHA='0ac784e55acf121ee8cb40699949a3b0afe13edd05c35956bf1e2cfa2e12b816'
CAND_SHA='8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3'
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
 assert result['format']=='has_junko_body_rest_diagnostic_v3_1' and result['status']=='EXPECTED_REFUSAL_WITH_DIAGNOSTIC' and result['checks']==25
 assert result['revision']=='2f1acbd7867087d9f18cfbc1122cc0c883c5f788' and set(result['jobs'])=={'unit25','body'} and result['conversions']=={}
 assert result['jobs']['unit25']['status']=='PASS' and result['jobs']['body']['status']=='EXPECTED_CHILD_REFUSAL'
 assert all(result[k] is True for k in ('all_jobs_closed','all_memberships_and_Main_preserved','parent_environment_preserved','all_admitted_inputs_preserved','lock_removed'))
 assert result['preservation_failure_count']==0 and result['source_input_file_count']==2902
 assert all(result[k] is False for k in ('graphics_executed','Full_claimed','native_simulation_qualified','Godot_binding_qualified','application_modified','private_arrays_published'))
 for row in result['jobs'].values():
  assert all(row[k] is True for k in ('wrapper_reaped','wrapper_handle_closed','job_closed','active_zero_before_close','assigned_before_START'))
  assert row['accounting']['active']==0 and row['accounting']['terminated_by_limit']==0
 assert pin(read(HOST/'SOURCE_PINS.json'))['sha256']==HOST_SHA
 assert pin(read(HOST/'run_stage_a.py'))['sha256']==DRIVER_SHA
 assert pin(read(CAND/'SOURCE_PINS.json'))['sha256']==CAND_SHA
 closure=parse(CAND/'RUNTIME_SOURCE_CLOSURE.json');assert len(closure['files'])==116
 actual=[]
 for row in closure['files']:
  p=STAGE/'Studio'/rel(row['path']);raw=read(p)
  assert pin(raw)=={'bytes':row['bytes'],'sha256':row['sha256']},p
  actual.append({'path':row['path'],**pin(raw)})
 runtime={p.relative_to(STAGE/'Studio').as_posix() for p in (STAGE/'Studio').rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 assert runtime=={r['path'] for r in actual}
 unit=(read(STAGE/'jobs/unit25/child-stdout.log')+read(STAGE/'jobs/unit25/child-stderr.log')).decode('utf-8').replace('\r\n','\n')
 assert len(re.findall(r'^test_.* \.\.\. ok$',unit,re.M))==25 and re.search(r'Ran 25 tests? in [0-9.]+s\s+OK\s*$',unit)
 assert not re.search(r'FAILED|ERROR|Traceback',unit)
 PACKET.mkdir();origins=[copy(STAGE/'PUBLIC_RESULT.json','evidence/PUBLIC_RESULT.json')]
 for job in ('unit25','body'):
  folder=STAGE/'jobs'/job;proof=parse(folder/'worker-receipt.json');owner=parse(folder/'OWNERSHIP.json')
  assert owner['closure_proven'] is True and owner['phase']=='CLOSED_BEFORE_ASSERTION_CHECKS'
  assert proof['gate_accepted'] is True and proof['child_launched'] is True and proof['child_reaped'] is True and proof['child_handle_closed'] is True
  assert proof['wrapper_identity']==result['jobs'][job]['owner']
  assert proof['status']==('PASS' if job=='unit25' else 'EXPECTED_CHILD_REFUSAL') and proof['child_exit']==(0 if job=='unit25' else 1)
  for leaf in ('child-stdout.log','child-stderr.log','wrapper-stdout.log','wrapper-stderr.log','worker-receipt.json','OWNERSHIP.json','launch.json'):
   origins.append(copy(folder/leaf,'evidence/jobs/'+job+'/'+leaf))
 # Copy only the one public scalar marker, with exact full-log byte provenance.
 # Never read/copy the private sidecar or publish the full converter log.
 logpath=STAGE/'Bundles/body/conversion.log';raw=read(logpath,64*1024*1024)
 diagnostic=result['diagnostic'];scalar=diagnostic['scalar_errors']
 assert diagnostic['status']=='EXPECTED_REFUSAL_WITH_DIAGNOSTIC' and diagnostic['original_close_predicate_still_false'] is True
 assert result['dress_started'] is False and all(diagnostic[k] is False for k in ('source_rest_tolerance_changed','diagnosed_cause_claimed','reference_pose_or_later_factory_writes_ruled_out','export_binding_qualified','Godot_binding_qualified','native_simulation_qualified'))
 assert pin(raw)['sha256']==diagnostic['conversion_log_sha256']
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
 write('RUNTIME_SOURCE_PROOF.json',{'format':'has_junko_stage_a_exact_source_binding_1','host_source_pins_sha256':HOST_SHA,'host_driver_sha256':DRIVER_SHA,'native_candidate_source_pins_sha256':CAND_SHA,'runtime116_actual_readback_matches':True,'files':actual,'execution_author':'Root retained process run; collector did not execute a runtime','Main1109_and2902_preservation':'Actual Root public receipt, not rerun by this collector'})
 write('SCOPE.json',{'format':'has_junko_first_rest_diagnostic25_actual_scope_1','status':'EXPECTED_REFUSAL_WITH_DIAGNOSTIC','pure_controls_passed':25,'pure_count_includes_prior16':True,'additional_delegation_controls':9,'old16_plus_current25_must_not_be_reported_as41_unique':True,'attempted_jobs':2,'Body':'EXPECTED_ORIGINAL_REST_REFUSAL_WITH_PUBLIC_SCALARS','Dress':'UNSTARTED','qualified_conversions':0,'both_attempted_jobs_closed_reaped_active0':True,'source_inputs_preserved':2902,'Root_revision':result['revision'],'original_tolerance_changed':False,'diagnosed_cause_claimed':False,'Godot54_inverse_bind_or_follow_qualified':False,'Full_result_reclassified':False,'private_assets_arrays_matrices_names_or_whole_log_copied':False})
 (PACKET/'README.md').write_text("""# Actual first Body rest-refusal diagnostic25

Root ran v3c0ac/ae92 with diagnostic8807 against2f1acbd. All25 pure controls
passed, including the prior16 plus9 delegation/privacy controls. These are25,
not41 distinct tests. Body reproduced the original strict rest-matrix refusal and
captured one scalar marker; Dress was never started and zero native conversions
or export bindings are qualified. Both Jobs/handles closed with active0,2902
admitted inputs/Main1109/environment were preserved and the owned lock removed.

First refused native index38 had basis/global error4.493998966426105e-5, parent
error2.03674886829579e-7 and translation error7.751130337574352e-8. The exact
full-precision measurements are retained in the public result and raw scalar line.
The original close predicate remained false; tolerance and model data stayed
unchanged. No rounding/refpose/factory-cause conclusion or repair is claimed.

The collector independently matched all116 actual Studio source files to the
frozen diagnostic closure, counted all25 raw unittest OK lines, and verified both
worker/Job closure receipts. It ran no runtime/Blender/GPU/Main/Full code. Only the
single exact public scalar line was copied from the converter log, bound to its
full-log SHA/size and byte range. The complete log, private matrix/name/nativeword
sidecar, original/copy native assets, partial bundles and identity inventories stay
local and were not copied. The collector did not read the private sidecar.

Original StageA FAIL16 and all preceding source packets remain unchanged. This
successful diagnostic preserves a native conversion refusal; it does not qualify
native export,54-link/Godot/rest/skin/follow/simulation/fidelity or successful Full.
""",encoding='utf-8')
 (PACKET/'code_used').mkdir();shutil.copyfile(__file__,PACKET/'code_used'/Path(__file__).name)
 # Every read source remains the exact same full-native identity and hash.
 for path in list(ROWS):read(Path(path))
 write('READBACK.json',{'status':'PASS','all_admitted_origin_identities_and_hashes_preserved':True,'runtime_source_files_checked':116,'safe_raw_evidence_files':len(origins),'pure_case_lines_checked':25,'original_stage_mutated':False,'runtime_executed_by_collector':False,'privacy_scope':'Explicit reviewed text allowlist and bounded traceback; not a general semantic privacy certification.'})
 files=[]
 for path in sorted(PACKET.rglob('*')):
  if path.is_file():
   b=path.read_bytes();b.decode('utf-8-sig');assert b'\0' not in b
   assert path.suffix in ('.py','.json','.log','.md');files.append({'path':path.relative_to(PACKET).as_posix(),**pin(b)})
 write('SOURCE_PINS.json',{'format':'has_junko_first_rest_diagnostic25_evidence_pins_1','status':'ACTUAL_DIAGNOSTIC25_NO_RUNTIME_BY_COLLECTOR','files':files})
 print(json.dumps({'packet':str(PACKET),'files':len(files)+1,'payload_bytes':sum(r['bytes'] for r in files),'manifest':pin((PACKET/'SOURCE_PINS.json').read_bytes()),'actual_status':'EXPECTED_REFUSAL_WITH_DIAGNOSTIC25','collector_CPU_readback':'PASS'},indent=2))
if __name__=='__main__':main()
