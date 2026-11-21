import * as fs from 'node:fs/promises';
import * as crypto from 'node:crypto';
import * as path from 'node:path';
const root='C:/a/Programming/cloudflare/has-body-addition-20261120';
const stage='C:/a/Programming/cloudflare/has-ui-camera-combined-1795250102351318500';
const proposal=root+'/output/source-combined-ui-v6-camera-shipping-prep-20261121';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const stamp=s=>[s.dev,s.ino,s.size,s.mtimeNs,s.nlink,s.mode].map(String).join(':');
const need=(ok,code)=>{if(!ok)throw Error(code);};
const rawManifest=await fs.readFile(proposal+'/SOURCE_PINS.json');
need(hash(rawManifest)==='0bb3179a2e0abe4dbfe6471a9de906176360d461e2b38f10ccb739da40872acd','COMBINED_MANIFEST_PIN');
const manifest=JSON.parse(rawManifest);
for(const row of manifest.files){const raw=await fs.readFile(proposal+'/'+row.path);need(raw.length===row.bytes&&hash(raw)===row.sha256,'FROZEN_SOURCE_DRIFT '+row.path);}
const report=JSON.parse(await fs.readFile(stage+'/COMBINED_UI_CAMERA_RESULT.json','utf8'));
need(report.status==='PASS'&&report.checks===939&&report.ui_assertions===424&&report.camera_assertions===515&&report.jobs.length===25&&report.expected_head==='59a112a08373f12dcf771c21734b35391b757d4e','ACTUAL_939_REQUIRED');
for(const flag of ['all_owned_launchers_reaped','all_attempted_private_jobs_closed','parent_environment_unchanged','head_unchanged','all_admitted_inputs_preserved','current_functional_domain_preserved','owned_lock_removed'])need(report[flag]===true,'QUALIFICATION_FLAG '+flag);
const ordinary=[];
for(const [folder,count] of [['ordinary-editor-controls-20261121',111],['ordinary-camera-interactions-20261121',515]]){
 const value=JSON.parse(await fs.readFile(stage+'/Studio/output/'+folder+'/verification.json','utf8'));
 need(value.status==='PASS'&&value.scope==='all'&&value.checks===count&&value.all_admitted_sources_unchanged===true,'ORDINARY_ENTRYPOINT_REQUIRED '+folder);
 for(const item of value.cases){if(item.private_receipt){const proof=JSON.parse(await fs.readFile(item.private_receipt,'utf8'));need(proof.exit===0&&proof.child_desktop_confirmed===true&&proof.private_window_seen===true&&proof.foreground_child_observed===false&&proof.desktop_switch_requested===false&&proof.job_closed===true&&proof.desktop_closed===true,'ORDINARY_PRIVATE_CLOSURE '+folder);}}
 ordinary.push({folder,checks:count});
}
const snapshot=JSON.parse(await fs.readFile(stage+'/SOURCE_SNAPSHOT.json','utf8'));
const baseline=snapshot.current_functional_catalogue;
need(Object.keys(baseline).length===1086,'BASELINE_1086');
const rootFiles=['dependencies.json','launch.pyw','main.tscn','project.godot','run.py',...['receipt_provenance.py','run_full.py','run_scoped.py','stage_legacy_inputs.py','test_receipt_provenance.py','verify_units.py'].map(x=>'experiments/reference_body_20261120/'+x)];
async function domain(){
 const found=new Set(rootFiles);
 async function walk(folder,relative){for(const entry of await fs.readdir(folder,{withFileTypes:true})){
  const rel=relative+'/'+entry.name;const info=await fs.lstat(root+'/'+rel,{bigint:true});need(!info.isSymbolicLink(),'SOURCE_ALIAS '+rel);
  if(entry.isDirectory()){if(!['__pycache__','.godot','.git'].includes(entry.name))await walk(root+'/'+rel,rel);}
  else{need(info.isFile(),'SPECIAL_SOURCE '+rel);if(!entry.name.endsWith('.pyc')&&!entry.name.endsWith('.pyo'))found.add(rel);}
 }}
 for(const folder of ['src','tests','tools','examples','data'])await walk(root+'/'+folder,folder);
 return [...found].sort();
}
need(JSON.stringify(await domain())===JSON.stringify(Object.keys(baseline).sort()),'EXACT_CURRENT_DOMAIN');
const identities={};
for(const [name,pin]of Object.entries(baseline)){
 const absolute=root+'/'+name;const before=await fs.lstat(absolute,{bigint:true});
 need(before.isFile()&&!before.isSymbolicLink()&&before.nlink===1n,'CURRENT_SOURCE_IDENTITY '+name);
 const raw=await fs.readFile(absolute);need(raw.length===pin.bytes&&hash(raw)===pin.sha256&&stamp(before)===stamp(await fs.lstat(absolute,{bigint:true})),'CURRENT_SOURCE_BYTES '+name);
 identities[name]=stamp(before);
}
const document=JSON.parse(await fs.readFile(proposal+'/TARGETS.json','utf8'));
need(document.targets.length===23&&document.current_functional_sources===1086&&document.proposed_functional_sources===1102,'EXACT_ADOPTION_DOMAIN');
need(document.targets.filter(r=>r.operation==='replace').length===7&&document.targets.filter(r=>r.operation==='new').length===16,'EXACT_7_MODIFIED_16_NEW');
const prepared=[];
for(const row of document.targets){
 need(/^(src|tests)\/[A-Za-z0-9_./-]+$/.test(row.path)&&!row.path.includes('..'),'TARGET_SCOPE');
 const absolute=root+'/'+row.path;const parent=path.dirname(absolute);
 need(path.resolve(await fs.realpath(parent)).toLowerCase()===path.resolve(parent).toLowerCase(),'PARENT_ALIAS');
 const target=await fs.readFile(proposal+'/payload/'+row.path);
 need(target.length===row.bytes&&hash(target)===row.sha256,'TARGET_PIN '+row.path);
 const qualified=await fs.readFile(stage+'/Studio/'+row.path);
 need(qualified.equals(target),'QUALIFIED_STUDIO_PIN '+row.path);
 let old=null;
 if(row.operation==='replace'){
  old=await fs.readFile(absolute);need(old.length===row.base_bytes&&hash(old)===row.base_sha256,'MODIFIED_BASE_PIN '+row.path);
 }else{try{await fs.lstat(absolute);throw Error('NEW_PATH_EXISTS '+row.path);}catch(error){if(error.code!=='ENOENT')throw error;}}
 prepared.push({...row,target,old});
}
const folder=root+'/output/ui-camera-adoption-'+Date.now();await fs.mkdir(folder);await fs.mkdir(folder+'/bases');
const journal={format:'has_exact_ui_camera_adoption_1',status:'APPLYING',base_revision:'59a112a08373f12dcf771c21734b35391b757d4e',functional_baseline_count:1086,functional_target_count:1102,functional_files_modified:7,functional_files_added:16,targets:document.targets,applied:[],qualification:{combined_checks:939,ui_checks:424,camera_checks:515,combined_private_jobs:25,ordinary_entrypoints:ordinary,new_whole_full_rerun:false,owner_acceptance_claimed:false},generated_editor_uid_sidecars_adopted:false,owner_installation_or_assets_modified:false};
await fs.writeFile(folder+'/JOURNAL.json',JSON.stringify(journal,null,2)+'\n',{flag:'wx'});
for(const row of prepared){
 if(row.old){
  const current=await fs.readFile(root+'/'+row.path);
  need(current.equals(row.old)&&stamp(await fs.lstat(root+'/'+row.path,{bigint:true}))===identities[row.path],'IMMEDIATE_BASE_DRIFT '+row.path);
  const backup=folder+'/bases/'+row.path;await fs.mkdir(path.dirname(backup),{recursive:true});await fs.writeFile(backup,row.old,{flag:'wx'});
  need((await fs.readFile(backup)).equals(row.old),'BACKUP_READBACK '+row.path);
 }
 await fs.writeFile(root+'/'+row.path,row.target,{flag:row.operation==='new'?'wx':'w'});
 const readback=await fs.readFile(root+'/'+row.path);need(readback.length===row.bytes&&hash(readback)===row.sha256,'APPLIED_READBACK '+row.path);
 journal.applied.push(row.path);await fs.writeFile(folder+'/JOURNAL.json',JSON.stringify(journal,null,2)+'\n');
}
const modified=new Set(prepared.filter(r=>r.operation==='replace').map(r=>r.path));let unchanged=0;
for(const [name,pin]of Object.entries(baseline)){
 if(modified.has(name))continue;const raw=await fs.readFile(root+'/'+name);
 need(raw.length===pin.bytes&&hash(raw)===pin.sha256&&stamp(await fs.lstat(root+'/'+name,{bigint:true}))===identities[name],'UNTOUCHED_SOURCE_DRIFT '+name);unchanged++;
}
need(unchanged===1079,'UNTOUCHED_SOURCE_COUNT');
const finalNames=await domain();need(finalNames.length===1102&&JSON.stringify(finalNames)===JSON.stringify([...new Set([...Object.keys(baseline),...prepared.map(r=>r.path)])].sort()),'FINAL_EXACT_1102_DOMAIN');
journal.status='APPLIED_READBACK_VERIFIED';journal.untouched_original_functional_files=unchanged;
await fs.writeFile(folder+'/JOURNAL.json',JSON.stringify(journal,null,2)+'\n');
await fs.writeFile(root+'/output/UI_CAMERA_ADOPTION_20261121.json',JSON.stringify({...journal,journal:folder+'/JOURNAL.json'},null,2)+'\n',{flag:'wx'});
export const result={status:journal.status,modified:7,added:16,untouched_original_functional_files:unchanged,functional_source_count:1102,journal:folder+'/JOURNAL.json'};
