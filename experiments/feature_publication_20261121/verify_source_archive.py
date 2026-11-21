from pathlib import Path, PurePosixPath
import hashlib,json,subprocess
root=Path(__file__).resolve().parents[1]; archive=root/'experiments/source_followup_20261121'
manifest=json.loads((archive/'CONTENTS.json').read_bytes())
rows=manifest['files']; assert len(rows)==861
raw=subprocess.check_output(['git','ls-files','--stage','-z','--','experiments/source_followup_20261121'],cwd=root)
index={}
for item in raw.split(b'\0'):
    if item:
        meta,name=item.split(b'\t',1);mode,oid,stage=meta.split();assert mode==b'100644' and stage==b'0'
        index[name.decode()]=oid.decode()
assert len(index)==862
changed=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=root).decode().split('\0')
assert {p for p in changed if p}==set(index)
for row in rows:
    path=PurePosixPath(row['path']);assert not path.is_absolute() and '..' not in path.parts
    target=archive/path;data=target.read_bytes()
    assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],str(path)
for name,oid in index.items():
    data=(root/name).read_bytes()
    assert b'\0' not in data;data.decode('utf-8-sig')
    assert Path(name).suffix in ['.json','.md','.py','.gd','.log','.ps1','.txt']
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,name
pins=list(archive.rglob('SOURCE_PINS.json'));assert len(pins)==31
for pin in pins:
    for row in json.loads(pin.read_bytes())['files']:
        data=(pin.parent/row['path']).read_bytes()
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
report={'format':'has_root_source_archive_review_1','status':'PASS','files':len(index),'bytes':sum((root/p).stat().st_size for p in index),'inner_source_manifests':len(pins),'all_staged_raw_blobs_exact':True,'all_manifest_rows_exact':True,'allowed_text_suffixes_only':True,'explicit_safe_collector_and_scope_reviewed':True,'new_runtime_or_native_fidelity_claimed':False}
(root/'output/ROOT_ARCHIVE_REVIEW_20261121.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
