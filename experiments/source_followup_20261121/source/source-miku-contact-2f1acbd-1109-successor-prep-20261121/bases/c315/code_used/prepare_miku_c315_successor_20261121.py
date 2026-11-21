"""Source-authoring only. No imported candidate code, native or GPU execution."""
from pathlib import Path
import ast, hashlib, json, stat
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
OLD=OUT/'source-miku-contact-1102-successor-prep-20261121'
NEW=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return b
def put(name,b):
 p=NEW/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert read(p)==b,name
 else:p.write_bytes(b)
 return (len(b),sha(b))
def js(name,value):return put(name,(json.dumps(value,indent=2)+'\n').encode())
def replace(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
old_manifest=read(OLD/'SOURCE_PINS.json');original=json.loads(old_manifest)
for row in original['files']:
 raw=read(OLD/row['path']);assert (len(raw),sha(raw))==(row['bytes'],row['sha256'])
inputs=json.loads(read(OLD/'INPUT_PINS.json'))
for row in inputs['files']:
 if row['path'].startswith('payload/') or row['path'] in ('qualified_helpers.py','qualified_ui_host.py'):
  put(row['path'],read(OLD/row['path']))
for name in ('source1102.py','test_source1102_contracts.py','run_miku_contact_qualification.py','INPUT_PINS.json','SOURCE_PINS.json'):
 put('bases/435/'+name,read(OLD/name))
catraw=read(OUT/'IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json');cat=json.loads(catraw);assert len(cat)==1103
files={}
for name,row in cat.items():
 p=ROOT/name;raw=read(p);s=p.lstat()
 assert len(raw)==row['bytes'] and sha(raw)==row['sha256'] and s.st_mtime_ns==row['mtime_ns'],name
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_sha1']
 files[name]={'bytes':len(raw),'sha256':sha(raw),'git_sha1':row['git_sha1'],'main_mtime_ns':str(s.st_mtime_ns)}
basepin=js('BASELINE_SOURCE1103.json',{'format':'has_exact_main1103_source_baseline_1','revision':REV,'source_count':1103,'files':files})
put('PUBLISHED_CATALOGUE1103.json',catraw)
audit=json.loads(read(OUT/'FULL182_REGISTRATION_AUDIT_20261121.json'))
assert len(audit['expected_group_keys'])==182 and sum(audit['new_groups'].values())==626
groupinfo={'format':'has_exact_full182_group_contract_1','revision':REV,'expected_group_keys':audit['expected_group_keys'],
 'new_groups':audit['new_groups'],'movie_groups':[k for k in audit['expected_group_keys'] if k.endswith('_video') or k.startswith('posed_model_video_')]}
assert len(groupinfo['movie_groups'])==21
grouppin=js('FULL182_GROUP_CONTRACT.json',groupinfo)
source=read(OLD/'source1102.py').decode()
source=source.replace('435dc02426a7cdd313e43fe674c9008520845428',REV).replace('435','c315').replace('1102','1103').replace('1096','1097')
source=replace(source,"BASELINE_PIN=(284402,'e2b3b407a36bb45d68218669990f3d741aa1f604727c51f641b115a0f0494900')",'BASELINE_PIN='+repr(basepin))
source=replace(source,"FULL_CLONE='has-ui-camera-full-20261121-c315dc02'","FULL_CLONE='has-import-off-full-20261121-c31576d'")
source=replace(source,'def admit_full(H,root,here,folder,completion_sha,source_sha,report_sha):','def admit_full(H,root,here,folder,completion_sha,source_sha,report_sha,outer_folder,outer_launch_sha,outer_completion_sha):')
source=replace(source,'    report_contract(report)\n','    report_contract(report)\n    groups=H.parse(H.read(here/\'FULL182_GROUP_CONTRACT.json\',*GROUP_PIN))\n    exact_group_contract(completion,report,groups)\n')
source=replace(source,"    need(domain(H,root)==set(baseline),'CURRENT1103_FULL_DOMAIN')", "    admit_outer_and_receipts(H,root,clone,folder,baseline,completion,launch,outer_folder,outer_launch_sha,outer_completion_sha)\n    need(domain(H,root)==set(baseline),'CURRENT1103_FULL_DOMAIN')")
# This native successor never uses the old pure171 project constructor. Keeping
# it would expose a misleading old GDS_CLOSURE dependency in the shared API.
source=source[:source.index('\ndef minimal_runtime(')]
put('source1103_base.py',source.encode())
js('AUTHORING_INPUTS.json',{'format':'has_miku_c315_authoring_inputs_1','revision':REV,
 'old_manifest':{'bytes':len(old_manifest),'sha256':sha(old_manifest)},'baseline_pin':basepin,'group_pin':grouppin,
 'old_native_payload_targets':inputs['targets'],'source_status':'AWAIT_SHARED_GUARD_EXTENSION_AND_PEER','candidate_executed':False})
print(json.dumps({'new_folder':str(NEW),'baseline_pin':basepin,'group_pin':grouppin,'catalogue_pin':[len(catraw),sha(catraw)]}))
