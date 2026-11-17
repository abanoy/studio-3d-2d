"""Root stages byte-exact readonly originals; this performs no PMX table parsing."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
ORIGINALS=Path(r'C:\a\tools\models').resolve()
discovery=ROOT/'output/PRIVATE-pmx-input-discovery-20261117/DISCOVERY.json'
raw=discovery.read_bytes();metadata=json.loads(raw);assert len(metadata['rows'])==4
dest=ROOT/'output/PRIVATE-pmx-oracle-inputs-20261117-attempt1';dest.mkdir(exist_ok=False)
fields=('st_dev','st_ino','st_size','st_mtime_ns','st_nlink','st_file_attributes')
def stamp(p):
 s=p.stat();return {k:getattr(s,k,None) for k in fields}
def digest(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
rows=[]
for i,row in enumerate(metadata['rows']):
 source=Path(row['path']);assert source.resolve().is_relative_to(ORIGINALS)
 for part in (source,*source.parents):assert not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400
 before=stamp(source);assert before==row['identity'] and before['st_nlink']==1 and 0<before['st_size']<=128*1024*1024
 assert digest(source)==row['sha256'] and stamp(source)==before
 copy=dest/('input-'+str(i)+'.pmx');count=0
 with source.open('rb') as inp,copy.open('xb') as out:
  while chunk:=inp.read(1024*1024):out.write(chunk);count+=len(chunk)
 assert count==before['st_size'] and stamp(source)==before
 assert digest(copy)==digest(source)==row['sha256'] and stamp(source)==before
 rows.append({'source':str(source),'source_identity':before,'sha256':row['sha256'],'copy':str(copy),'copy_identity':stamp(copy),'copy_bytes_equal_source':True})
record={'format':'has_private_owned_pmx_source_copies_1','discovery_sha256':hashlib.sha256(raw).hexdigest(),'producer_sha256':digest(Path(__file__)),'rows':rows,'source_read_only_and_unchanged':True,'native_body_or_joint_tables_parsed':False,'native_qualification':False,'private_original_copies_do_not_upload':True}
(dest/'PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'copies':len(rows),'bytes':sum(r['copy_identity']['st_size'] for r in rows),'source_unchanged':True,'tables_parsed':False,'native_qualified':False,'provenance_sha256':digest(dest/'PROVENANCE.json')}))
