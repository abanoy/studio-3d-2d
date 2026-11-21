"""Source authoring and private read-only pinning. No app/tool/runtime imports."""
from pathlib import Path
import ast,hashlib,json,os,stat,time,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';REVIEW=ROOT.parent/'HAS-Review-Editor-Camera-c31576d'
DEST=OUT/'source-owner-review-c315-replay-prep-20261121';SHARED=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
PREP=(123121,'41f9cb3ff0bd38083f2f1ff990ab5ec83b922db0bbfbd30db33090206b64a410')
def ident(s):return [str(v) for v in (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))]
def read(p):
 for x in reversed((p,*p.parents)):
  s=x.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 b=p.read_bytes();assert ident(s)==ident(p.lstat());return b
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=read(p);return {'bytes':len(b),'sha256':sha(b),'identity':ident(p.lstat())}
def put(name,b):
 p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert read(p)==b
 else:p.write_bytes(b)
 return {'path':name,'bytes':len(b),'sha256':sha(b)}
prep_raw=read(REVIEW/'PREPARATION.json');assert (len(prep_raw),sha(prep_raw))==PREP
prep=json.loads(prep_raw);assert prep['source_file_count']==1106 and len(prep['projects'])==3 and len(prep['launchers'])==4
expected={'Studio/'+name for name in prep['source_hashes']}|{'Studio/override.cfg','README.txt','PREPARATION.json'}
expected|={'Examples/'+row['label']+'.has' for row in prep['projects']}|{row['path'] for row in prep['launchers']}
files={};directories={};seen=set()
def error(e):raise e
for here,dirs,names in os.walk(REVIEW,followlinks=False,onerror=error):
 here=Path(here);s=here.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
 directories[here.relative_to(REVIEW).as_posix()]=ident(s)
 for name in dirs+names:
  p=here/name;s=p.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
  relative=p.relative_to(REVIEW).as_posix();assert relative.casefold() not in seen;seen.add(relative.casefold())
 for name in names:
  p=here/name;relative=p.relative_to(REVIEW).as_posix();files[relative]=pin(p)
assert set(files)==expected and len(files)==1116
for name,digest in prep['source_hashes'].items():assert files['Studio/'+name]['sha256']==digest
originals=[];summaries=[]
for row in prep['projects']:
 for k,pkey in (('source','source_pin'),('older_review_copy','older_review_copy_pin'),('copy','copy_pin')):
  p=Path(row[k]);assert pin(p)==row[pkey];originals.append({'path':str(p),'pin':row[pkey]})
 with zipfile.ZipFile(row['copy']) as z:
  project=json.loads(z.read('project.json'));header=json.loads(z.read('has.json'))
  assert project['schema_version']==4 and header['storage']=='packed'
  objects=len(project['world']['objects']);cels=sum(len(l['cels']) for l in project['layers'])
  summaries.append({'label':row['label'],'objects':objects,'cels':cels,'expected_checks':20+objects+cels,'payload_members':len(header['payload'])})
seal={'format':'has_private_c315_review_readonly_seal_1','private_do_not_publish':True,'review':str(REVIEW),
 'preparation_pin':{'bytes':PREP[0],'sha256':PREP[1]},'files':files,'directories':directories,
 'protected_projects_and_older_copies':originals,'case_summaries':summaries,'authoring_only_no_runtime':True}
seal_path=OUT/('PRIVATE_REVIEW_C315_READONLY_SEAL_'+str(time.time_ns())+'.json')
seal_raw=(json.dumps(seal,indent=2)+'\n').encode();assert not seal_path.exists();seal_path.write_bytes(seal_raw)
rows=[]
for name in ('qualified_ui_host.py','qualified_helpers.py','source1103.py','BASELINE_SOURCE1103.json','FULL182_GROUP_CONTRACT.json'):
 rows.append(put(name,read(SHARED/name)))
tool=read(ROOT/'tools/verify_owner_review.py');gd=read(ROOT/'tests/owner_review_replay.gd')
rows.append(put('reference/verify_owner_review.py',tool));rows.append(put('reference/owner_review_replay.gd',gd))
text=tool.decode();compare=text[text.index('def compare('):text.index('\ndef load_runner(')]
module='"""Unchanged committed owner-review saved-state comparison contract."""\nimport math\n'+compare+'\n'
ast.parse(module);rows.append(put('review_state_compare.py',module.encode()))
inputs={'format':'has_c315_owner_replay_source_inputs_1','revision':prep['source_commit'],'files':rows,
 'preparation_pin':{'bytes':PREP[0],'sha256':PREP[1]},'private_seal_pin':{'bytes':len(seal_raw),'sha256':sha(seal_raw)},
 'expected_cases':3,'expected_total_checks':sum(r['expected_checks'] for r in summaries),'review_source_files':1106,
 'review_total_files':1116,'launcher_count':4,'committed_replay_script_pin':{'bytes':len(gd),'sha256':sha(gd)},
 'no_request_expected_observed_project_metadata_or_images_in_source_packet':True}
b=(json.dumps(inputs,indent=2)+'\n').encode();put('INPUT_PINS.json',b)
print(json.dumps({'folder':str(DEST),'input_pin':[len(b),sha(b)],'private_seal_path':str(seal_path),
 'private_seal_pin':[len(seal_raw),sha(seal_raw)],'expected_cases':3,'expected_total_checks':sum(r['expected_checks'] for r in summaries)}))
