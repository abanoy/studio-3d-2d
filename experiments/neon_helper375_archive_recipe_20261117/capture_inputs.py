"""Freeze only completed375 scalar/log/source and owned launch/outcome text."""
from pathlib import Path,PureWindowsPath
import hashlib,json
from archive_checks import ROOT_RUN,check,load,require
HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 require(not (HERE/'INPUTS.json').exists(),'Fresh recipe only')
 root=REVIEW/ROOT_RUN;result=load((root/'verification.json').read_bytes());before=load((root/'source-before.json').read_bytes());paths=set()
 paths.update(('REVIEW',p.relative_to(REVIEW).as_posix()) for p in root.iterdir() if p.is_file() and p.suffix in ('.json','.log'))
 source_hashes=set()
 for row in result['rows']:
  child=Path(row['report_path']).parent;require(child.is_relative_to(REVIEW/'output/helper-preview'),'Derived child escapes closed helper domain')
  for name in ('verification.json','fixture-identities.json','main-source-before.json','main-source-after.json','reviewed-main-bindings.json','snapshot-source-before.json','source-state-before.json','Studio/helper-preview-source-context.json','Studio/override.cfg'):
   paths.add(('REVIEW',(child/name).relative_to(REVIEW).as_posix()))
  qa=child/'Studio/output/helper-preview-qa'
  for case in row['report']['results']:
   folder=qa/case['label']
   for name in ('command.json','launch.json','engine.log','stdout.log','stderr.log','verification.json','result.json','private-receipt.json'):
    p=folder/name
    if p.is_file():paths.add(('REVIEW',p.relative_to(REVIEW).as_posix()))
  for name in ('owned-launch.json','owned-outcome.json'):
   for p in qa.rglob(name):
    paths.add(('REVIEW',p.relative_to(REVIEW).as_posix()))
    if name=='owned-launch.json':source_hashes.update(load(p.read_bytes())['source_sha256'].values())
 manifest=load((REVIEW/'tests/helper_preview_port_files.json').read_bytes())
 for row in manifest['files']:paths.add(('REVIEW',row['path']))
 for name in ('tests/helper_preview_port_files.json','run.py','project.godot','tools/private_desktop.py','dependencies.json'):paths.add(('REVIEW',name))
 # Resolve worker code identities from the root source map, never request or model arrays.
 for name,digest in before.items():
  if digest in source_hashes:
   require(Path(name).suffix=='.py','Worker source fingerprint is not source text');paths.add(('REVIEW',name))
 for name in ('experiments/run_neon_helper_followup_20261117.py','experiments/run_neon_scene_followup_20261117.py'):paths.add(('MAIN',name))
 source=MAIN/'experiments/neon_helper_preview_manifest_20261117'
 require((source/'INDEX.json').is_file(),'Reviewed manifest source packet must be sealed first')
 paths.update(('MAIN',p.relative_to(MAIN).as_posix()) for p in source.iterdir() if p.is_file())
 roots={'MAIN':MAIN,'REVIEW':REVIEW};rows=[];raw={};bindings={}
 for alias,name in sorted(paths):
  path=roots[alias]/name;require(path.suffix in ('.json','.log','.py','.gd','.md','.cfg','.godot'),'Nontext/media/configuration payload refused')
  for item in (path,*path.parents):
   if item.exists():require(not item.is_symlink() and not getattr(item.lstat(),'st_file_attributes',0)&0x400,'Input reparse refused')
  s=path.stat();data=path.read_bytes();after=path.stat();require((s.st_size,s.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Original changed during capture');data.decode('utf-8-sig')
  row={'root':alias,'path':name,'bytes':len(data),'sha256':sha(data),'mtime_ns':s.st_mtime_ns};rows.append(row);key=alias+':'+name;raw[key]=data;bindings[key]=row
 summary=check(raw,bindings,str(REVIEW))
 spec={'format':'has_helper375_closed_text_archive_recipe_1','scope':'EXPLICIT_COMPLETED_HELPER375_ROOT_DERIVED_CHILD_QA_OWNED_LAUNCH_OUTCOME_AND_PUBLIC_SOURCE','roots':{k:str(v) for k,v in roots.items()},'inputs':rows,'expected_summary':summary,'worker_configuration_request_preview_binding_and_model_files_included':False,'tool_provenance':'Exact executable fingerprints are declared and checked by archived root/source drivers; no executable bytes or new contemporaneous tool attestation copied.','active_full_output_read':False}
 with (HERE/'INPUTS.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(spec,f,indent=2);f.write('\n')
 print(json.dumps({'input_bindings':len(rows),'INPUTS_sha256':sha((HERE/'INPUTS.json').read_bytes()),'summary':summary},indent=2))
if __name__=='__main__':main()
