from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
selection=json.loads((OUT/'IMPORT_OFF_PUBLICATION_SELECTION_20261121.json').read_bytes())
rows=selection['paths'];names={r['path'] for r in rows}
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.longpaths=true','-c','core.whitespace=cr-at-eol',*args],cwd=ROOT)
assert git('rev-parse','HEAD').decode().strip()==selection['base']
assert not git('diff','--cached','--name-only')
for row in rows:
 raw=(ROOT/row['path']).read_bytes()
 assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
paths=OUT/'import-off-selected-paths-20261121.nul';assert not paths.exists()
paths.write_bytes(b''.join(r['path'].encode()+b'\0' for r in rows))
git('add','--pathspec-from-file='+str(paths),'--pathspec-file-nul')
assert set(git('diff','--cached','--name-only','-z').decode().rstrip('\0').split('\0'))==names
index={}
for raw in git('ls-files','--stage','-z').split(b'\0'):
 if not raw:continue
 meta,name=raw.split(b'\t',1);mode,oid,stage=meta.decode().split()
 if name.decode() in names:
  assert stage=='0';index[name.decode()]={'mode':mode,'git_sha1':oid}
assert set(index)==names
for row in rows:
 assert index[row['path']]=={'mode':row['mode'],'git_sha1':row['git_sha1']},row['path']
assert not git('diff','--cached','--check')
assert not any(name.startswith('output/') for name in names)
record={'status':'PASS','selected_count':len(rows),'selected_bytes':sum(r['bytes'] for r in rows),
 'all_selected_raw_blobs_and_modes_exact':True,'all_generated_output_changes_excluded':True,'paths':rows}
(OUT/'IMPORT_OFF_INDEX_VERIFIED_20261121.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='paths'}))
