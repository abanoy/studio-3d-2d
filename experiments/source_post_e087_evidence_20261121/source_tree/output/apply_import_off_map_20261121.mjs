import * as fs from 'node:fs/promises';
import * as crypto from 'node:crypto';
import * as path from 'node:path';
const root='C:/a/Programming/cloudflare/has-body-addition-20261120';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const stamp=s=>[s.dev,s.ino,s.size,s.mtimeNs,s.nlink,s.mode].map(String).join(':');
const raw=await fs.readFile(root+'/output/windows-reference-body-1795233568436471500/source-after.json');
if(hash(raw)!=='ae338017a4a0ac3483bfeb9bc8d1ab40355780bdeb235e29c104d9cf94c5f2f9')throw Error('BASELINE_MANIFEST_PIN');
let times=0;const baseline=JSON.parse(raw.toString().replace(/("mtime_ns"\s*:\s*)(\d+)/g,(_all,key,digits)=>{times++;return key+JSON.stringify(digits);}));
if(Object.keys(baseline).length!==1084||times!==1084)throw Error('BASELINE_EXACT_TIMESTAMP_COUNT');
const identities={};
for(const [name,pin]of Object.entries(baseline)){
 const abs=root+'/'+name;const before=await fs.lstat(abs,{bigint:true});
 if(!before.isFile()||before.isSymbolicLink()||before.nlink!==1n||String(before.mtimeNs)!==pin.mtime_ns)throw Error('CURRENT_BASE_IDENTITY '+name);
 const bytes=await fs.readFile(abs);if(bytes.length!==pin.bytes||hash(bytes)!==pin.sha256||stamp(before)!==stamp(await fs.lstat(abs,{bigint:true})))throw Error('CURRENT_BASE_PIN '+name);
 identities[name]=stamp(before);
}
const proposal=root+'/output/source-import-default-off-map-adoption-prep-20261121';
const rawManifest=await fs.readFile(proposal+'/ADOPTION_MANIFEST.json');
if(hash(rawManifest)!=='22c2317e30546b46cc03bf0613bcbd57435376e1b0272c5f106ecd3e2576cc3a')throw Error('PROPOSAL_PIN');
const original=JSON.parse(rawManifest);const rows=[...original.functional_files.map(x=>({...x,kind:'functional'})),...original.documentation_files.map(x=>({...x,kind:'documentation'}))];
const prepared=[];
for(const row of rows){
 const rel=row.path;if(!/^(src|tools|tests|docs)\/[A-Za-z0-9_\-./]+$/.test(rel)||rel.includes('..'))throw Error('TARGET_SCOPE');
 let source=proposal+'/payload/'+rel;let pin={...row.target};
 if(rel==='tests/import_physics_smoke.gd'){source=root+'/output/import-physics-default-off-cold-wire-v3-prep-20261121/import_physics_smoke.gd';pin={bytes:21848,sha256:'9104065d55830781b07e47c358ddaa8c039d038b53780dcbeeafaad52c0d9be1'};}
 const target=await fs.readFile(source);if(target.length!==pin.bytes||hash(target)!==pin.sha256)throw Error('TARGET_PIN '+rel);
 let old=null;
 if(row.operation==='modify'){old=await fs.readFile(root+'/'+rel);if(old.length!==row.baseline.bytes||hash(old)!==row.baseline.sha256)throw Error('MODIFY_BASE_PIN '+rel);}
 else{try{await fs.lstat(root+'/'+rel);throw Error('ADD_ALREADY_EXISTS '+rel);}catch(error){if(error.code!=='ENOENT')throw error;}}
 const parent=path.dirname(root+'/'+rel);if(path.resolve(await fs.realpath(parent)).toLowerCase()!==path.resolve(parent).toLowerCase())throw Error('PARENT_ALIAS');
 prepared.push({...row,source,target:pin,bytes:target,old});
}
const gpu=JSON.parse(await fs.readFile(root+'/output/source-import-default-off-root-reaped-20261121.json','utf8'));
const controls=JSON.parse(await fs.readFile(root+'/output/cold-wire-controls-1795243058547846800/PUBLIC_RESULT.json','utf8'));
const maps=JSON.parse(await fs.readFile(root+'/output/source-map-retest-root-reaped-20261121.json','utf8'));
if(gpu.status!=='PASS'||gpu.smoke_checks!==54||gpu.native_profiles!==5||controls.status!=='PASS'||controls.oracle_checks!==20||controls.oracle_failures!==0||maps.status!=='PASS'||maps.actual_map_conversions!==2)throw Error('ACTUAL_QUALIFICATION_REQUIRED');
const folder=root+'/output/import-off-map-adoption-'+Date.now();await fs.mkdir(folder);await fs.mkdir(folder+'/bases');
const journal={format:'has_exact_import_off_map_adoption_1',status:'APPLYING',base_revision:'e0879c7df74bc3704902bfdaf4ff74eee40c3aea',functional_baseline_count:1084,functional_target_count:1086,targets:prepared.map(({bytes,old,...r})=>r),applied:[],qualification:{gpu_checks:54,native_profiles:5,strong_oracle_controls:20,map_conversions:2,relocated_map_cpu_tests:28,full_current_suite_rerun:false},owner_installation_or_assets_modified:false};
await fs.writeFile(folder+'/JOURNAL.json',JSON.stringify(journal,null,2)+'\n',{flag:'wx'});
for(const row of prepared){
 if(row.old){const backup=folder+'/bases/'+row.path;await fs.mkdir(path.dirname(backup),{recursive:true});await fs.writeFile(backup,row.old,{flag:'wx'});}
 await fs.writeFile(root+'/'+row.path,row.bytes,{flag:row.operation==='add'?'wx':'w'});
 const verify=await fs.readFile(root+'/'+row.path);if(verify.length!==row.target.bytes||hash(verify)!==row.target.sha256)throw Error('APPLIED_READBACK '+row.path);
 journal.applied.push(row.path);await fs.writeFile(folder+'/JOURNAL.json',JSON.stringify(journal,null,2)+'\n');
}
const changed=new Set(prepared.filter(x=>x.kind==='functional').map(x=>x.path));let untouched=0;
for(const [name,pin]of Object.entries(baseline)){
 if(changed.has(name))continue;const verify=await fs.readFile(root+'/'+name);
 if(verify.length!==pin.bytes||hash(verify)!==pin.sha256||stamp(await fs.lstat(root+'/'+name,{bigint:true}))!==identities[name])throw Error('UNTOUCHED_SOURCE_CHANGED '+name);
 untouched++;
}
if(untouched!==1078)throw Error('UNTOUCHED_SOURCE_COUNT');
journal.status='APPLIED_READBACK_VERIFIED';journal.untouched_original_functional_files=untouched;journal.functional_files_modified=6;journal.functional_files_added=2;
await fs.writeFile(folder+'/JOURNAL.json',JSON.stringify(journal,null,2)+'\n');
await fs.writeFile(root+'/output/IMPORT_OFF_MAP_ADOPTION_20261121.json',JSON.stringify({...journal,journal:folder+'/JOURNAL.json'},null,2)+'\n',{flag:'wx'});
export const result={status:journal.status,modified:6,added:2,docs:3,untouched_original_functional_files:untouched,journal:folder+'/JOURNAL.json',functional_source_count:1086};
