"""Copy exact approved source definitions only; never execute their programs."""
from pathlib import Path
import hashlib,json,stat
OUT=Path(__file__).resolve().parent
DEST=OUT/'source-easing-c315-graphics-qualification-prep-20261121'
SHARED=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
CANDIDATE=OUT/'source-keyframe-easing-c315-graphics-v2-prep-20261121'
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return b
def sha(b):return hashlib.sha256(b).hexdigest()
def copy(p,name):
 b=read(p);target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert read(target)==b
 else:target.write_bytes(b)
 return {'path':name,'bytes':len(b),'sha256':sha(b)}
manifest=read(CANDIDATE/'SOURCE_PINS.json');assert sha(manifest)=='b8d482e75aeca185a56abcdf87ae42af2d5f98b0a28fe2cb1675e7e75d0d4ab3'
rows=[]
for row in json.loads(manifest)['files']:
 b=read(CANDIDATE/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
 rows.append(copy(CANDIDATE/row['path'],'candidate/'+row['path']))
rows.append(copy(CANDIDATE/'SOURCE_PINS.json','candidate/SOURCE_PINS.json'))
for name in ('qualified_ui_host.py','qualified_helpers.py','source1103.py','BASELINE_SOURCE1103.json','FULL182_GROUP_CONTRACT.json'):
 rows.append(copy(SHARED/name,name))
targets=[]
for row in rows:
 if row['path'].startswith('candidate/payload/'):
  targets.append({'path':row['path'][len('candidate/payload/'):],'bytes':row['bytes'],'sha256':row['sha256']})
assert len(targets)==7
inputs={'format':'has_easing_c315_graphics_host_inputs_1','revision':'c31576d0c1d84030d51ec886f2f3976a60a70c7b',
 'files':rows,'targets':targets,'candidate_manifest_sha256':sha(manifest),'source_status':'SOURCE_ONLY_UNRUN'}
b=(json.dumps(inputs,indent=2)+'\n').encode();p=DEST/'INPUT_PINS.json';assert not p.exists();p.write_bytes(b)
print(json.dumps({'folder':str(DEST),'input_pin':[len(b),sha(b)],'targets':len(targets)}))
