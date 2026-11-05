"""Bounded .has project container v1. Data only; never executes archive contents."""
from pathlib import Path
import hashlib
import json
import math
import os
import re
import shutil
import stat
import struct
import sys
import tempfile
import zipfile
import zlib

MAX_TOTAL = 512 * 1024 * 1024
MAX_META = 1024 * 1024
MAX_FILES = 128


class HasError(ValueError): pass


def local_reference(value):
    if not isinstance(value,str) or not value or value.startswith(('\\\\','//')) or '://' in value:
        raise HasError('Linked assets must be local files')
    return Path(value)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def safe(name):
    if not isinstance(name, str) or not name or len(name.encode('utf-8'))>512 or '\\' in name or ':' in name or name.startswith('/'):
        raise HasError('Unsafe project member path')
    for part in name.split('/'):
        if part in ('', '.', '..') or part[-1:] in (' ', '.') or re.search(r'[<>"|?*\x00-\x1f]', part) or part.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
            raise HasError('Unsafe project member path: ' + name)
    return name


def preflight_archive(path):
    # Check the small standard ZIP end record before zipfile allocates its full
    # central directory. HAS v1 needs neither multi-disk nor ZIP64 archives.
    size=path.stat().st_size
    if size>MAX_TOTAL: raise HasError('HAS archive exceeds 512 MiB')
    with path.open('rb') as stream:
        stream.seek(max(0,size-65557));tail=stream.read(65557)
    offset=tail.rfind(b'PK\x05\x06')
    if offset<0 or len(tail)-offset<22: raise HasError('Invalid HAS ZIP end record')
    _,disk,start,on_disk,count,central_size,central_offset,comment=struct.unpack_from('<4s4H2IH',tail,offset)
    end=size-len(tail)+offset
    if disk or start or count!=on_disk or not 2<=count<=MAX_FILES or central_size>MAX_META or central_offset+central_size!=end or len(tail)-offset!=22+comment:
        raise HasError('Unsupported or excessive HAS ZIP directory')


def json_bytes(value): return json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8')


def read_json(blob):
    if len(blob) > MAX_META: raise HasError('Project metadata exceeds 1 MiB')
    value = json.loads(blob)
    if not isinstance(value, dict): raise HasError('Expected project metadata object')
    return value


def members(manifest):
    """Only declared current playback/editing assets; never glob whole game folders."""
    version = manifest.get('schema_version')
    if version not in (3,4): raise HasError('HAS v1 requires project schema3 or4')
    if version == 4:
        if 'scene' in manifest or 'model' in manifest: raise HasError('Schema4 cannot contain obsolete scene/model slots')
        world=manifest.get('world')
        if not isinstance(world,dict) or world.get('format')!='studio_world_1' or not isinstance(world.get('objects'),list) or len(world['objects'])>64:
            raise HasError('Invalid world or more than64 objects')
        rows=world['objects']; index={}
        duration=manifest.get('video',{}).get('duration_frames')
        if type(duration) not in (int,float) or not 1<=duration<=240 or not math.isfinite(duration) or duration!=int(duration):
            raise HasError('Invalid world duration')
        for row in rows:
            if not isinstance(row,dict): raise HasError('Invalid world object')
            identity=row.get('id'); parent=row.get('parent_id'); start=row.get('start_frame')
            if not isinstance(identity,str) or not identity or len(identity)>128 or any(ord(c)<32 or c in '/\\:' for c in identity) or identity in index:
                raise HasError('Invalid or duplicate world object ID')
            if row.get('kind') not in ('environment','model','group') or not isinstance(parent,str): raise HasError('Invalid world kind/parent')
            if type(start) not in (int,float) or not 0<=start<=duration or not math.isfinite(start) or start!=int(start):
                raise HasError('Invalid first presence frame')
            if 'source' in row or row.get('path')!='assets/'+str(row.get('sha256'))+'.glb': raise HasError('Invalid managed world asset path')
            index[identity]=row
        for row in rows:
            current=row['id'];seen=set()
            while current:
                if current in seen: raise HasError('Cyclic world parent hierarchy')
                if current not in index: raise HasError('Missing world parent')
                seen.add(current); current=index[current]['parent_id']
        slots=[('model',row) for row in rows]
    else:
        slots=[(slot,manifest.get(slot,{})) for slot in ('scene','model')]
    audio=manifest.get('audio',{})
    if not isinstance(audio,dict): raise HasError('Invalid audio metadata')
    if 'format' in audio or 'clips' in audio:
        rows=audio.get('clips')
        if audio.get('format')!='studio_audio_2' or set(audio)!={'format','clips'} or not isinstance(rows,list) or not 1<=len(rows)<=16:
            raise HasError('Unsupported audio collection or more than16 clips')
    else: rows=[audio] if audio else []
    identities=set()
    for row in rows:
        if not isinstance(row,dict): raise HasError('Invalid audio clip')
        identity=row.get('id')
        if not isinstance(identity,str) or not 1<=len(identity)<=128 or identity in identities: raise HasError('Invalid or duplicate audio identity')
        identities.add(identity)
        duration=manifest.get('video',{}).get('duration_frames',240)
        for field,low,high in [('start_frame',0,duration-1),('source_in_sample',0,60*96000),('gain_db',-60,12)]:
            value=row.get(field)
            if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high or (field!='gain_db' and value!=int(value)): raise HasError('Invalid audio timing/gain')
        if not isinstance(row.get('muted'),bool): raise HasError('Invalid audio mute value')
        slots.append(('audio',row))
    assets = {}
    for slot,row in slots:
        if not row: continue
        name = safe(row['path']); digest = row['sha256']
        if not name.startswith('assets/') or not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}', digest): raise HasError('Invalid asset identity')
        if slot in ('scene','model') and not name.endswith('.glb') or slot == 'audio' and not name.endswith('.wav'): raise HasError('Invalid asset format')
        if name in assets and assets[name]['sha256'] != digest: raise HasError('Conflicting asset checksums')
        assets[name] = {'path': name, 'sha256': digest}
    cels = set()
    for layer in manifest['layers']:
        for cel in layer['cels']:
            name = safe(cel['path'])
            if not name.startswith('cels/') or not name.endswith('.png'): raise HasError('Invalid cel path')
            cels.add(name)
    if version==3 and not assets or len(assets) + len(cels) + 2 > MAX_FILES: raise HasError('Missing assets or too many project files')
    return assets, cels


def check_cancel(request):
    if request.get('cancel') and Path(request['cancel']).exists(): raise HasError('Project operation cancelled; previous save preserved')


def checked_copy(source, destination, digest, request):
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=destination.name+'.',suffix='.tmp',dir=destination.parent)
    temporary=Path(name)
    with Path(source).open('rb') as src, os.fdopen(handle,'wb') as dst:
        total = 0
        for block in iter(lambda: src.read(1024 * 1024), b''):
            check_cancel(request); total += len(block)
            if total > MAX_TOTAL: raise HasError('Asset exceeds container limit')
            dst.write(block)
        dst.flush(); os.fsync(dst.fileno())
    if sha(temporary) != digest: raise HasError('Asset changed during copying')
    check_cancel(request);os.replace(temporary,destination)


def pack(request):
    folder = Path(request['folder']).resolve(strict=True)
    target = Path(request['path']).resolve()
    if target.suffix.lower() != '.has': raise HasError('Choose a .has project filename')
    mode = request['storage']
    if mode not in ('packed', 'linked'): raise HasError('Choose packed or linked storage')
    project_blob = (folder/'project.json').read_bytes()
    manifest = read_json(project_blob); assets, cels = members(manifest)
    payload = [{'path':'project.json','sha256':hashlib.sha256(project_blob).hexdigest(),'bytes':len(project_blob)}]
    records = []
    total = len(project_blob)
    for name in sorted(set(assets) | cels):
        check_cancel(request)
        path = (folder/name).resolve(strict=True)
        if not path.is_relative_to(folder) or path.is_symlink(): raise HasError('Asset outside snapshot')
        size = path.stat().st_size; total += size
        limit = 128*1024*1024 if name.endswith('.glb') else 32*1024*1024
        if size > limit or total > MAX_TOTAL: raise HasError('Project exceeds 512 MiB or per-asset limits')
        digest = sha(path)
        if name in assets and digest != assets[name]['sha256']: raise HasError('Snapshot asset checksum changed')
        row = {'path':name,'sha256':digest,'bytes':size}
        if name in assets:
            if mode == 'linked':
                reference = local_reference(request['references'][name]).resolve(strict=True)
                if reference.stat().st_size != size or sha(reference) != digest: raise HasError('Linked source changed: '+str(reference))
                # Opening a packed project then saving linked must not depend on
                # an expendable extraction cache. Externalize those assets beside HAS.
                caches = [Path(request['cache_root']).resolve()]+[Path(p).resolve() for p in request.get('cache_roots',[])]
                if any(reference.is_relative_to(cache) for cache in caches):
                    reference = target.with_name(target.stem+'.assets') / Path(name).name
                    if not reference.is_file() or sha(reference) != digest:
                        if reference.exists(): raise HasError('Conflicting linked sidecar asset')
                        checked_copy(path, reference, digest, request)
                try: row['reference'] = reference.relative_to(target.parent).as_posix()
                except ValueError: row['reference'] = str(reference)
            else: payload.append(row)
            records.append(row)
        else: payload.append(row)
    header = {'format':'hybrid_animation_studio','version':1,'storage':mode,'assets':records,'payload':payload}
    header_blob = json_bytes(header)
    if len(header_blob) > MAX_META: raise HasError('HAS metadata exceeds 1 MiB')
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=target.name+'.', suffix='.tmp', dir=target.parent); os.close(handle)
    temporary = Path(temporary)
    # Keep failed/cancelled temp data for diagnosis; never replace an older good file.
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        archive.writestr('has.json',header_blob)
        for row in payload:
            check_cancel(request)
            with (folder/row['path']).open('rb') as src, archive.open(row['path'],'w') as dst:
                h = hashlib.sha256()
                for block in iter(lambda: src.read(1024 * 1024), b''):
                    check_cancel(request);h.update(block);dst.write(block)
                if h.hexdigest()!=row['sha256']: raise HasError('Snapshot changed while packing')
    if temporary.stat().st_size > MAX_TOTAL: raise HasError('HAS archive exceeds 512 MiB')
    with temporary.open('r+b') as f: f.flush(); os.fsync(f.fileno())
    check_cancel(request)
    if target.is_file():
        # Do not promote a known corrupt archive over a usable previous backup.
        try:
            preflight_archive(target)
            with zipfile.ZipFile(target) as old:
                info = old.infolist()
                bounded = target.stat().st_size<=MAX_TOTAL and len(info)<=MAX_FILES and sum(e.file_size for e in info)<=MAX_TOTAL and old.getinfo('has.json').file_size<=MAX_META and all(e.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED) and not e.flag_bits & 1 for e in info)
                valid=False
                if bounded:
                    header=read_json(old.read('has.json'));members(read_json(old.read('project.json')))
                    valid=header.get('format')=='hybrid_animation_studio' and header.get('version')==1 and header.get('storage') in ('packed','linked') and old.testzip() is None
        except (OSError,ValueError,KeyError,zipfile.BadZipFile): valid = False
        if valid:
            backup = Path(str(target)+'.backup.tmp')
            shutil.copyfile(target,backup);os.replace(backup,Path(str(target)+'.backup'))
    check_cancel(request); os.replace(temporary,target)
    return {'ok':True,'path':str(target),'storage':mode,'bytes':target.stat().st_size}


def unpack(request):
    source = Path(request['path']).resolve(strict=True)
    preflight_archive(source)
    folder = Path(request['folder']).resolve()
    if folder.exists(): raise HasError('Extraction directory must be new')
    with zipfile.ZipFile(source) as archive:
        entries = {}; total = 0
        for entry in archive.infolist():
            name = safe(entry.filename)
            if entry.is_dir() or name.casefold() in entries or entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16) or entry.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED): raise HasError('Duplicate, encrypted or unsupported HAS entry')
            entries[name.casefold()] = entry; total += entry.file_size
            limit = 128*1024*1024 if name.endswith('.glb') else MAX_META if name in ('has.json','project.json') else 32*1024*1024
            if entry.file_size > limit or total > MAX_TOTAL or len(entries) > MAX_FILES: raise HasError('HAS expanded data exceeds bounds')
        header = read_json(archive.read('has.json')); blob = archive.read('project.json'); manifest = read_json(blob)
        if header.get('format') != 'hybrid_animation_studio' or header.get('version') != 1 or header.get('storage') not in ('packed','linked'): raise HasError('Unsupported HAS container version')
        assets,cels = members(manifest)
        payload = header['payload']; records = header['assets']
        if not isinstance(payload,list) or not isinstance(records,list) or len(payload)+len(records)>MAX_FILES: raise HasError('Invalid HAS inventory')
        index={safe(row['path']):row for row in records}
        body={safe(row['path']):row for row in payload}
        if len(index)!=len(records) or len(body)!=len(payload) or set(index)!=set(assets): raise HasError('HAS inventory mismatch')
        expected = {'project.json',*cels,*assets} if header['storage']=='packed' else {'project.json',*cels}
        if set(body)!=expected or set(entries)!={n.casefold() for n in expected|{'has.json'}}: raise HasError('Unexpected or missing HAS payload')
        linked = {}; missing=[]; origins={}
        expanded=sum(entries[n.casefold()].file_size for n in {'project.json',*cels})
        for name,row in index.items():
            if row['sha256'] != assets[name]['sha256']: raise HasError('Asset identity differs from project')
            limit=128*1024*1024 if name.endswith('.glb') else 32*1024*1024
            if type(row.get('bytes')) is not int or not 0<=row['bytes']<=limit: raise HasError('Asset size exceeds bounds')
            expanded+=row['bytes']
            if expanded>MAX_TOTAL: raise HasError('Project expanded assets exceed 512 MiB')
            if header['storage']=='linked':
                reference = request.get('relinks',{}).get(name,row.get('reference'))
                if not isinstance(reference,str) or not reference: raise HasError('Invalid linked asset reference')
                ref = local_reference(reference)
                ref = ref.resolve() if ref.is_absolute() else (source.parent/ref).resolve()
                if not ref.is_file() or ref.stat().st_size != row['bytes'] or sha(ref)!=row['sha256']:
                    missing.append({'asset':name,'reference':str(ref),'sha256':row['sha256']})
                else: linked[name]=ref
        if missing: return {'ok':False,'error':'Linked asset is missing or changed. Locate the matching file or cancel to keep your current project.','missing':missing}
        folder.mkdir(parents=True,exist_ok=False)
        for name,row in body.items():
            check_cancel(request)
            entry=entries[name.casefold()]
            if entry.file_size!=row['bytes']: raise HasError('Payload size differs')
            destination=folder/name;destination.parent.mkdir(parents=True,exist_ok=True)
            h=hashlib.sha256();size=0
            with archive.open(entry) as src,destination.open('xb') as dst:
                for block in iter(lambda: src.read(1024*1024),b''):
                    check_cancel(request);size+=len(block)
                    if size>entry.file_size: raise HasError('Decompression exceeds declared size')
                    h.update(block);dst.write(block)
            if h.hexdigest()!=row['sha256']: raise HasError('HAS payload checksum differs: '+name)
        for name,ref in linked.items():
            checked_copy(ref,folder/name,index[name]['sha256'],request)
            origins[str((folder/name).resolve())]=str(ref)
    return {'ok':True,'folder':str(folder),'storage':header['storage'],'origins':origins}


def main():
    request=read_json(Path(sys.argv[1]).read_bytes())
    try:
        if request['action']=='pack': result=pack(request)
        elif request['action']=='unpack': result=unpack(request)
        else: raise HasError('Unknown HAS action')
    except (OSError,ValueError,KeyError,TypeError,AttributeError,EOFError,zlib.error,zipfile.BadZipFile,RuntimeError) as error: result={'ok':False,'error':str(error)}
    target=Path(request['result']);temp=Path(str(target)+'.tmp');temp.write_bytes(json_bytes(result));os.replace(temp,target)
    return 0 if result['ok'] else 1


if __name__=='__main__': raise SystemExit(main())
