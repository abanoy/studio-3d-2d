"""Read only the pinned post-e087 source/evidence packet; execute no tests/Git/native code."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,re,stat
class Refusal(RuntimeError):pass
def need(ok,code):
 if not ok:raise Refusal(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
 def pairs(items):
  out={}
  for key,value in items:need(key not in out,'DUPLICATE_JSON_KEY');out[key]=value
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refusal('NONFINITE_JSON')))
def rel(name):
 need(type(name) is str and name and ':' not in name and '\\' not in name,'RELATIVE_PATH')
 p=PurePosixPath(name);need(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name,'CANONICAL_RELATIVE_PATH');return name
def identity(info):
 mode=info.st_mode&~0o111 if os.name=='nt' and stat.S_ISREG(info.st_mode) else info.st_mode
 return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,mode,getattr(info,'st_file_attributes',0)&~0x40000
def read(path,count=None,digest=None):
 before=path.lstat();need(stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode) and before.st_nlink==1 and not getattr(before,'st_file_attributes',0)&0x400 and before.st_size<=8*1024*1024,'SAFE_REGULAR_BOUNDED_FILE')
 with path.open('rb') as stream:
  need(identity(os.fstat(stream.fileno()))==identity(before),'CHANGED_BEFORE_READ');raw=stream.read(before.st_size+1)
  need(identity(os.fstat(stream.fileno()))==identity(before),'CHANGED_DURING_READ')
 need(len(raw)==before.st_size and identity(path.lstat())==identity(before),'CHANGED_AFTER_READ')
 need((count is None or len(raw)==count) and (digest is None or sha(raw)==digest),'BYTE_PIN_DIFFERS');return raw,identity(before)
def paths(root):
 result=set();pending=[root]
 while pending:
  current=pending.pop();info=current.lstat();need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'DIRECTORY_ALIAS')
  for path in current.iterdir():
   info=path.lstat();need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'PATH_ALIAS')
   if stat.S_ISDIR(info.st_mode):pending.append(path)
   else:need(stat.S_ISREG(info.st_mode),'NONREGULAR_ENTRY');result.add(path.relative_to(root).as_posix())
 return result
def safe_evidence(value):
 if isinstance(value,dict):
  for key,item in value.items():
   need(not (re.fullmatch(r'native_parameters|positions|vertices|weights|inverseBindMatrices|pose|shape_pose|buffers|bufferViews|accessors|rigs',key,re.I) and isinstance(item,(dict,list))),'RAW_PRIVATE_EVIDENCE_FIELD')
   safe_evidence(item)
 elif isinstance(value,list):
  for item in value:safe_evidence(item)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--packet-root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--manifest-sha256',required=True);opt=ap.parse_args();root=opt.packet_root.absolute()
 need(re.fullmatch('[0-9a-f]{64}',opt.manifest_sha256),'MANIFEST_SHA')
 manifest_raw,manifest_stamp=read(root/'CONTENTS.json',digest=opt.manifest_sha256);doc=parse(manifest_raw)
 need(doc.get('format')=='has_post_e087_source_evidence_contents_1' and doc.get('new_full_1086_claimed') is False,'MANIFEST_SCOPE')
 rows=doc.get('files');need(type(rows) is list and rows,'MANIFEST_ROWS');allowed={};folded=set();verified={}
 for row in rows:
  need(type(row) is dict and set(row)=={'path','bytes','sha256','kind','origin','proposed_repository_path'},'ROW_SCHEMA')
  name=rel(row['path']);need(name!='CONTENTS.json' and name not in allowed and name.casefold() not in folded,'PATH_COLLISION')
  need(type(row['bytes']) is int and 0<=row['bytes']<=8*1024*1024 and re.fullmatch('[0-9a-f]{64}',row['sha256']),'ROW_PIN')
  need(row['proposed_repository_path']==doc['proposed_repository_prefix']+'/'+name,'PROPOSED_PATH')
  need(not re.search(r'(?:^|/)(?:\.git|\.godot|__pycache__)(?:/|$)|\.(?:has|glb|gltf|mdl|gma|vvd|vtx|phy|pmx|vrm|zip|rar|bin|png|jpe?g|exr|tga|vtf|vmt|exe|dll|pyc|pyo)$',name,re.I),'FORBIDDEN_ART_ASSET_OR_CACHE')
  allowed[name]=row;folded.add(name.casefold())
 need(paths(root)==set(allowed)|{'CONTENTS.json'},'EXACT_PACKET_PATHSET')
 for name,row in allowed.items():
  raw,stamp=read(root/name,row['bytes'],row['sha256']);verified[name]=(raw,stamp)
  if row['kind']=='compact_evidence' and name.endswith('.json'):safe_evidence(parse(raw))
  if name.endswith('.log'):need(not re.search(rb'"(?:native_parameters|inverseBindMatrices|bufferViews|vertices|weights)"\s*:\s*[\[{]',raw),'RAW_DATA_LOG')
 for group in doc['frozen_source_folders']:
  prefix='source_tree/'+rel(group['folder'])+'/';manifest=prefix+'SOURCE_PINS.json';raw=verified[manifest][0]
  need((len(raw),sha(raw))==(group['manifest_bytes'],group['manifest_sha256']),'SOURCE_MANIFEST_PIN')
  original=parse(raw);need(original.get('format')==group['format'],'SOURCE_MANIFEST_FORMAT');entries=original.get('files',original.get('entries'));need(type(entries) is list,'SOURCE_ROWS');expected={manifest}
  for item in entries:
   name=prefix+rel(item['path']);need(name in allowed and (allowed[name]['bytes'],allowed[name]['sha256'])==(item['bytes'],item['sha256']),'SOURCE_DEPENDENCY_PIN');expected.add(name)
  need(expected=={name for name in allowed if name.startswith(prefix)} and len(expected)==group['files'],'EXACT_FROZEN_SOURCE_FOLDER')
 for version in ['documentation','documentation-v2']:
  edits=parse(verified['documentation_recovery/'+version+'/EDITS.json'][0]);need(len(edits['files'])==7,'SEVEN_DOCUMENT_EDITS')
  for row in edits['files']:
   base=verified['documentation_recovery/bases/'+rel(row['path'])][0];need((len(base),sha(base))==(row['baseline']['bytes'],row['baseline']['sha256']),'DOCUMENT_BASE_PIN')
   if row['operation']=='append_utf8':rebuilt=base+row['append'].encode('utf-8');need(rebuilt.startswith(base),'HISTORY_PREFIX')
   else:
    need(row['operation']=='insert_after_prefix_utf8' and type(row['prefix_bytes']) is int and 1<=row['prefix_bytes']<=3,'DOCUMENT_INSERTION')
    cut=row['prefix_bytes'];rebuilt=base[:cut]+row['insert'].encode('utf-8')+base[cut:];new=parse(rebuilt);old=parse(base);need('latest_owner_requested_increment_20261121' in new,'DOCUMENT_INCREMENT');new.pop('latest_owner_requested_increment_20261121');need(new==old,'HISTORICAL_JSON_FIELDS')
   need((len(rebuilt),sha(rebuilt))==(row['target']['bytes'],row['target']['sha256']),'EXACT_DOCUMENT_RECONSTRUCTION')
 gpu=parse(verified['evidence/gpu_v3_passed/PUBLIC_DEFAULT_OFF_GPU_RESULT.json'][0]);need(gpu['status']=='PASS' and gpu['checks']==54 and gpu['native_profiles_observed']==5 and gpu['all_private_jobs_closed'] and gpu['all_admitted_inputs_preserved'],'ACTUAL_GPU_54_FIVE')
 need(gpu['video']=={'codec_name':'h264','width':1920,'height':1080,'r_frame_rate':'24/1','nb_read_frames':'48','duration':'2.000000'},'ACTUAL_MP4')
 strong=parse(verified['evidence/strong_cold_controls/PUBLIC_RESULT.json'][0]);need(strong['status']=='PASS' and strong['oracle_checks']==20 and strong['oracle_failures']==0 and strong['all_private_jobs_closed'],'STRONG20')
 passed=verified['source_tree/output/import-physics-default-off-cold-wire-prep-20261121/import_physics_smoke.gd'][0];latest=verified['source_tree/output/import-physics-default-off-cold-wire-v3-prep-20261121/import_physics_smoke.gd'][0];anchor=b'\tvar folder: String=OS.get_cmdline_user_args()[0]'
 need(anchor in passed and anchor in latest and passed[passed.index(anchor):]==latest[latest.index(anchor):],'QUALIFIED_54_BODY_PRESERVED')
 adoption=parse(verified['evidence/root/IMPORT_OFF_MAP_ADOPTION_20261121.json'][0]);need(adoption['status']=='APPLIED_READBACK_VERIFIED' and adoption['functional_target_count']==1086 and adoption['untouched_original_functional_files']==1078,'ACTUAL_EIGHT_ADOPTION')
 for target in adoption['targets']:
  source=target['source'].replace('\\','/').casefold();matches=[row for row in rows if type(row['origin']) is str and row['origin'].replace('\\','/').casefold()==source]
  need(any((row['bytes'],row['sha256'])==(target['target']['bytes'],target['target']['sha256']) for row in matches),'ADOPTED_SOURCE_RECOVERABLE')
 final_targets=parse(verified['evidence/adoption/FINAL_FUNCTIONAL_TARGETS.json'][0]);need(final_targets['current_functional_count']==1086 and len(final_targets['targets'])==8,'FINAL_EIGHT_TARGETS')
 for row in final_targets['targets']:
  raw=verified[row['archive']][0];need((len(raw),sha(raw))==(row['target']['bytes'],row['target']['sha256']),'LATEST_ADOPTED_SOURCE_PIN')
 style=parse(verified['evidence/root/SOURCE_LIGHT_TEST_STYLE_FINAL_20261121.json'][0]);original_test=verified['source_tree/output/source-import-default-off-map-adoption-prep-20261121/payload/tests/test_source_lights.py'][0];final_test=verified['evidence/style/test_source_lights_final.py'][0]
 need(original_test==final_test+b'\n'*3 and original_test.endswith(b'\n'*4) and (len(final_test),sha(final_test))==(style['final']['bytes'],style['final']['sha256']) and sha(original_test[:-1])==style['intermediate']['sha256'],'ONLY_THREE_REDUNDANT_LF_BYTES_REMOVED')
 regression=parse(verified['evidence/root/POST_IMPORT_MAP_ADOPTION_REGRESSION_20261121.json'][0]);need(regression['status']=='PASS' and regression['total_cpu_tests']==57 and regression['tests']['source_appearance']['passed']==29 and regression['complete_current_1086_full_suite_claimed'] is False,'ACTUAL_57_CPU_SCOPE')
 canonical=parse(verified['evidence/root/COMPLETION_OVERVIEW_REGENERATION_20261121.json'][0]);overview=verified['evidence/document_regeneration/current_canonical_overview.md'][0];need(canonical['status']=='REGENERATED_AND_ORIGINAL_LF_RETAINED' and (len(overview),sha(overview))==(canonical['bytes'],canonical['sha256']),'FINAL_CANONICAL_OVERVIEW')
 classification=parse(verified['evidence/classification/OUTCOMES.json'][0]);need(classification['mini_drivers']['v1']['status']=='AUTHORED_UNRUN' and classification['cold_failures']['exact_numeric_and_type_differences_observed_in_second_run_only'] is True,'RETAINED_FAILURE_SCOPE')
 for name,(raw,stamp) in verified.items():need(read(root/name,len(raw),sha(raw))[1]==stamp,'SECOND_READ_IDENTITY')
 need(read(root/'CONTENTS.json',digest=opt.manifest_sha256)[1]==manifest_stamp,'MANIFEST_IDENTITY')
 print(json.dumps({'format':'has_post_e087_recoverability_result_1','status':'PASS','payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'frozen_source_folders':len(doc['frozen_source_folders']),'document_draft_versions_reconstructed':14,'adopted_functional_files_recoverable':8,'actual_54_gpu_and_strong20_preserved':True,'new_1086_full_claimed':False,'tests_native_or_Git_executed':False}))
 return 0
if __name__=='__main__':raise SystemExit(main())
