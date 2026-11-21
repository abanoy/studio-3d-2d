"""Collect only declared text/source evidence; final publication is separate."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,stat,time
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'experiments/continuation_sources_20261121'
PACKETS=[
 'source-import-off-followup-v3-prep-20261121',
 'source-import-off-first-movie-repeat-prep-20261121',
 'source-scenario-d-mask-coordinates-prep-20261121',
 'source-full435-failed-prep-20261121',
 'source-keyframe-easing435-port-prep-20261121',
 'source-keyframe-easing435-undo-fix-prep-20261121',
 'source-miku-pure171-prep-20261121',
 'source-miku-pure171-evidence-prep-20261121',
 'source-miku-contact-1102-successor-prep-20261121',
 'source-posed-head-render-bounds-prep-20261121',
 'source-posed-head-native-1102-qualification-prep-20261121',
 'source-character-parts-editor-prep-20261121',
 'source-character-parts-headless-protocol-prep-20261121',
 'source1102-contracts-cpu-1795255071802-be59cd39']
EXT={'.gd','.py','.ps1','.md','.txt','.json','.log','.cpp','.h'}
def relative(name):
    path=PurePosixPath(name)
    assert not path.is_absolute() and path.parts and all(p not in ('.','..') and ':' not in p and '\\' not in p for p in path.parts)
    return Path(*path.parts)
def read(path):
    info=path.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not getattr(info,'st_file_attributes',0)&0x400
    raw=path.read_bytes();now=path.lstat()
    assert (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)==(now.st_dev,now.st_ino,now.st_size,now.st_mtime_ns)
    assert path.suffix.lower() in EXT or path.name=='project.godot','Non-text/native payload refused: '+str(path)
    raw.decode('utf-8-sig')
    return raw
def copy(source,name):
    raw=read(source);target=DEST/relative(name)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert read(target)==raw,'Existing archive bytes differ: '+name
    else:
        with target.open('xb') as stream:assert stream.write(raw)==len(raw)
    assert read(source)==raw and read(target)==raw
    return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
if not DEST.exists():
    DEST.mkdir()
    (DEST/'BUILDING.json').write_text(json.dumps({'format':'has_owned_continuation_archive_build_1','publication_ready':False,'started_ns':time.time_ns()},indent=2)+'\n',encoding='utf-8')
assert (DEST/'BUILDING.json').is_file(),'Finalized archive must not be changed'
rows=[];packets=[]
for name in PACKETS:
    source=ROOT/'output'/name;manifest=source/'SOURCE_PINS.json';raw=read(manifest);value=json.loads(raw)
    entries=value['files'];assert type(entries) is list
    names=set()
    for row in entries:
        path=relative(row['path']);assert row['path'].casefold() not in names;names.add(row['path'].casefold())
        data=read(source/path)
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],str(source/path)
        rows.append(copy(source/path,'source/'+name+'/'+row['path']))
    rows.append(copy(manifest,'source/'+name+'/SOURCE_PINS.json'))
    packets.append({'folder':name,'declared_payloads':len(entries),'source_pins_sha256':hashlib.sha256(raw).hexdigest()})
assert len({r['path'].casefold() for r in rows})==len(rows)
result={'format':'has_continuation_source_collection_1','status':'BUILDING_NOT_PUBLICATION_READY',
 'packets':packets,'copied_files':len(rows),'bytes':sum(r['bytes'] for r in rows),
 'native_or_binary_payloads_copied':False,'all_declared_source_bytes_preserved':True,'paths':rows}
(ROOT/'output/CONTINUATION_ARCHIVE_COLLECTION_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('paths','packets')}))
