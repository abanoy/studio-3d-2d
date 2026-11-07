"""Bounded .has project container v1. Data only; never executes archive contents."""
from pathlib import Path
try:from .drawing_limits import MAX_PROJECT_FILES, error as drawing_count_error
except ImportError:from drawing_limits import MAX_PROJECT_FILES, error as drawing_count_error
from contextlib import contextmanager
import errno
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
try:from .sequence_graph import error as sequence_graph_error
except ImportError:from sequence_graph import error as sequence_graph_error
try:from .drawing_origin import error as drawing_origin_error
except ImportError:from drawing_origin import error as drawing_origin_error
try:from .pose_library import error as pose_library_error
except ImportError:from pose_library import error as pose_library_error
try:from .save_sync import existing_boundary, sync_directory, parents as sync_parents
except ImportError:from save_sync import existing_boundary, sync_directory, parents as sync_parents

MAX_TOTAL = 512 * 1024 * 1024
MAX_META = 1024 * 1024
MAX_FILES = MAX_PROJECT_FILES


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


def members(manifest,extended_ok=False):
    """Only declared current playback/editing assets; never glob whole game folders."""
    count_error=drawing_count_error(manifest.get("layers",[]))
    if count_error:raise HasError(count_error)
    video=manifest.get("video",{})
    if isinstance(video,dict) and "output_size" in video and (not isinstance(video["output_size"],str) or video["output_size"] not in ("1080p","720p","540p")):raise HasError("Invalid saved output size")
    try:from . import extended_timing as extended
    except ImportError:import extended_timing as extended
    if manifest.get('schema_version')==8:
        base,why=extended.unwrap(manifest)
        if why:raise HasError(why)
        return members(base,True)
    if 'timing_content_schema_version' in manifest or not extended_ok and extended.required(manifest):raise HasError('Extended project timing requires schema8')
    if manifest.get('schema_version')==7:
        try:from .reference_sheet import unwrap
        except ImportError:from reference_sheet import unwrap
        base,why=unwrap(manifest)
        if why:raise HasError(why)
        assets,cels=members(base,extended_ok);reference=manifest['reference_sheet']
        assets[reference['path']]={'path':reference['path'],'sha256':reference['sha256']}
        if len(assets)+len(cels)+2>MAX_FILES:raise HasError('Too many project files')
        return assets,cels
    if 'reference_sheet' in manifest or 'content_schema_version' in manifest:raise HasError('Project reference sheets require schema7')
    if manifest.get('schema_version')==6:
        graph=manifest.get('sequence_graph');why=sequence_graph_error(graph,manifest)
        if why:raise HasError(why)
        base=dict(manifest);base.pop('sequence_graph')
        base['schema_version']=5 if base.get('world',{}).get('format')=='studio_world_2' else 4
        assets,cels=members(base,extended_ok)
        for sequence in graph['assets']:
            child_assets,child_cels=members(sequence['scene'],extended_ok)
            for name,row in child_assets.items():
                if name in assets and assets[name]!=row:raise HasError('Conflicting nested sequence asset identity')
                assets[name]=row
            cels.update(child_cels)
        if len(assets)+len(cels)+2>MAX_FILES:raise HasError('Too many nested sequence files')
        return assets,cels
    if 'sequence_graph' in manifest:raise HasError('Editable sequences require project schema6')
    for layer in manifest.get('layers',[]):
        if isinstance(layer,dict) and 'origin' in layer:
            why=drawing_origin_error(layer['origin'])
            if why:raise HasError(why)
    world=manifest.get('world',{})
    actors=world.get('objects',[]) if isinstance(world,dict) and 'world' in manifest else [manifest.get('model',{})]
    if not isinstance(actors,list):raise HasError('Invalid world object list')
    for actor in actors:
        if isinstance(actor,dict) and isinstance(actor.get('metadata'),dict) and 'body_pose_library' in actor['metadata']:
            library=actor['metadata']['body_pose_library'];why=pose_library_error(library)
            if why:raise HasError(why)
            if library['sha256']!=actor.get('sha256'):raise HasError('Saved body poses belong to a different model source')
    palette=manifest.get('palette',[])
    if not isinstance(palette,list) or len(palette)>32:raise HasError('Invalid project palette or more than32 swatches')
    for row in palette:
        if not isinstance(row,dict) or set(row)!={'name','rgba'} or not isinstance(row.get('name'),str) or not 1<=len(row['name'])<=48 or any(ord(c)<32 or ord(c)==127 or 0xd800<=ord(c)<=0xdfff for c in row['name']):raise HasError('Invalid color swatch name')
        if not isinstance(row.get('rgba'),str) or len(row['rgba'])!=8 or any(c not in '0123456789abcdef' for c in row['rgba']):raise HasError('Invalid color swatch RGBA')
    version = manifest.get('schema_version')
    if version not in (3,4,5): raise HasError('HAS v1 requires project schema3,4 or5')
    if version in (4,5):
        if 'scene' in manifest or 'model' in manifest: raise HasError('Schema4 cannot contain obsolete scene/model slots')
        world=manifest.get('world')
        if not isinstance(world,dict) or world.get('format')!=('studio_world_2' if version==5 else 'studio_world_1') or not isinstance(world.get('objects'),list) or len(world['objects'])>64:
            raise HasError('Invalid world or more than64 objects')
        if version==4 and 'effects' in world:raise HasError('Particle effects require project schema5')
        rows=world['objects']; index={}
        duration=manifest.get('video',{}).get('duration_frames')
        if type(duration) not in (int,float) or not 1<=duration<=(extended.MAX_FRAMES if extended_ok else 240) or not math.isfinite(duration) or duration!=int(duration):
            raise HasError('Invalid world duration')
        if extended_ok and extended.video_error(manifest.get('video')):raise HasError(extended.video_error(manifest.get('video')))
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
        if version==5:
            effects=world.get('effects')
            if not isinstance(effects,list) or len(effects)>16:raise HasError('Invalid particle collection or more than16 effects')
            identities=set(index)
            for row in effects:
                if not isinstance(row,dict) or row.get('format')!='studio_particle_instance_1':raise HasError('Unsupported particle instance')
                if set(row)-{'format','id','name','path','sha256','texture_path','texture_sha256','position','rotation_xyzw','scale','start_frame','end_frame','source_in_seconds','visible'}:raise HasError('Unsupported particle instance fields')
                identity=row.get('id');name=row.get('name')
                if not isinstance(identity,str) or not 1<=len(identity)<=128 or any(ord(c)<32 or c in '/\\:'for c in identity) or identity in identities:raise HasError('Invalid or duplicate particle ID')
                identities.add(identity)
                if not isinstance(name,str) or not 1<=len(name)<=256 or not isinstance(row.get('visible'),bool):raise HasError('Invalid particle name/visibility')
                for field,low,high in [('start_frame',0,duration-1),('end_frame',1,duration),('source_in_seconds',0,60),('scale',.0001,1000)]:
                    v=row.get(field)
                    if type(v) not in (int,float) or not low<=v<=high or not math.isfinite(v) or (field in ('start_frame','end_frame')and v!=int(v)):raise HasError('Invalid particle timing/scale')
                if row['start_frame']>=row['end_frame']:raise HasError('Invalid particle clip range')
                for field,count in [('position',3),('rotation_xyzw',4)]:
                    v=row.get(field)
                    if not isinstance(v,list)or len(v)!=count or any(type(n)not in(int,float)or not -100000<=n<=100000 or not math.isfinite(n)for n in v):raise HasError('Invalid particle placement')
                if sum(n*n for n in row['rotation_xyzw'])<.000001:raise HasError('Invalid particle rotation')
                if 'source'in row or 'texture_source'in row or row.get('path')!='assets/'+str(row.get('sha256'))+'.json' or row.get('texture_path')!='assets/'+str(row.get('texture_sha256'))+'.png':raise HasError('Invalid managed particle paths')
                slots.extend([('particle',row),('particle_texture',{'path':row['texture_path'],'sha256':row.get('texture_sha256')})])
    else:
        slots=[(slot,manifest.get(slot,{})) for slot in ('scene','model')]
    audio=manifest.get('audio',{})
    if not isinstance(audio,dict): raise HasError('Invalid audio metadata')
    if 'format' in audio or 'clips' in audio:
        rows=audio.get('clips')
        if audio.get('format') not in ('studio_audio_2','studio_audio_3','studio_audio_4') or set(audio)!={'format','clips'} or not isinstance(rows,list) or not 1<=len(rows)<=16:
            raise HasError('Unsupported audio collection or more than16 clips')
    else: rows=[audio] if audio else []
    identities=set()
    for row in rows:
        if not isinstance(row,dict): raise HasError('Invalid audio clip')
        for field in ('fade_in_ms','fade_out_ms'):
            if field not in row: continue
            value=row[field]
            if audio.get('format')!='studio_audio_4' or type(value) not in (int,float) or not math.isfinite(value) or value!=int(value) or not 1<=value<=60000:raise HasError('Invalid or unversioned sound fade')
        if 'source_out_sample' in row:
            end=row['source_out_sample'];start=row.get('source_in_sample')
            if audio.get('format') not in ('studio_audio_3','studio_audio_4') or type(end) not in (int,float) or not math.isfinite(end) or end!=int(end) or not 0<end<=60*96000 or type(start) not in (int,float) or not math.isfinite(start) or end<=start:
                raise HasError('Invalid or unversioned audio end trim')
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
        if slot == 'model' and 'reference_opacity' in row:
            opacity = row['reference_opacity']
            if type(opacity) not in (int, float) or not math.isfinite(opacity) or not 0 <= opacity <= 1:
                raise HasError('Reference opacity must be between0 and1')
        name = safe(row['path']); digest = row['sha256']
        if not name.startswith('assets/') or not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}', digest): raise HasError('Invalid asset identity')
        if slot in ('scene','model') and not name.endswith('.glb') or slot == 'audio' and not name.endswith('.wav'): raise HasError('Invalid asset format')
        if slot=='particle'and not name.endswith('.json')or slot=='particle_texture'and not name.endswith('.png'):raise HasError('Invalid particle asset format')
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


def asset_limit(name):
    if name.startswith("references/") and name.endswith(".png"):return 16*1024*1024
    if name.endswith('.glb'):return 128*1024*1024
    if name.startswith('assets/')and name.endswith('.json'):return MAX_META
    if name.startswith('assets/')and name.endswith('.png'):return 8*1024*1024
    return 32*1024*1024


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


def verify_written_archive(path, header_blob, payload, request):
    """Read the completed temporary archive before touching either saved file."""
    preflight_archive(path)
    if not isinstance(payload,list) or len(payload)>MAX_FILES-1:raise HasError("Invalid saved HAS readback inventory")
    expected={'has.json':len(header_blob),**{row['path']:row['bytes'] for row in payload}}
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        if len(entries)!=len(expected) or {e.filename for e in entries}!=set(expected):
            raise HasError('Saved HAS readback inventory differs; previous save preserved')
        if sum(e.file_size for e in entries)>MAX_TOTAL:
            raise HasError('Saved HAS expanded data exceeds bounds; previous save preserved')
        for entry in entries:
            if entry.file_size!=expected[entry.filename] or entry.is_dir() or entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16) or entry.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):
                raise HasError('Saved HAS readback entry differs; previous save preserved')
        if archive.read('has.json')!=header_blob:
            raise HasError('Saved HAS readback header differs; previous save preserved')
        for row in payload:
            check_cancel(request);digest=hashlib.sha256();count=0
            with archive.open(row['path']) as source:
                for block in iter(lambda:source.read(1024*1024),b''):
                    check_cancel(request);count+=len(block)
                    if count>row['bytes']:raise HasError('Saved HAS readback exceeds declared size; previous save preserved')
                    digest.update(block)
            if count!=row['bytes'] or digest.hexdigest()!=row['sha256']:
                raise HasError('Saved HAS readback checksum differs: '+row['path']+'; previous save preserved')


@contextmanager
def save_lock(target, label="HAS"):
    """A persistent inode avoids unlink/reopen races; the OS releases ownership on exit."""
    lock = Path(str(target)+'.lock')
    if lock.is_symlink():raise HasError('Linked '+label+' save lock refused; previous save preserved')
    flags = os.O_RDWR | os.O_CREAT | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_CLOEXEC',0)
    handle = os.open(lock,flags,0o600)
    try:
        opened=os.fstat(handle);named=lock.lstat()
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1 or opened.st_size!=0 or (opened.st_dev,opened.st_ino)!=(named.st_dev,named.st_ino):
            raise HasError('Unsafe '+label+' save lock; previous save preserved')
        try:
            if os.name=='posix':
                import fcntl
                fcntl.flock(handle,fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif os.name=='nt':
                import msvcrt
                os.lseek(handle,0,os.SEEK_SET);msvcrt.locking(handle,msvcrt.LK_NBLCK,1)
            else:raise HasError('HAS save locking is unavailable on this platform')
        except OSError as error:
            if error.errno not in (errno.EACCES,errno.EAGAIN):raise
            raise HasError('Another save is writing this '+label+' file. Wait for it to finish, then save again.') from error
        yield
    finally:
        os.close(handle)


def pack(request):
    chosen=Path(request['path']).expanduser();target=chosen.parent.resolve()/chosen.name
    if target.suffix.lower()!='.has':raise HasError('Choose a .has project filename')
    check_cancel(request)
    for destination in (target,Path(str(target)+'.backup'),Path(str(target)+'.backup.tmp')):
        if destination.is_symlink():raise HasError('Linked save destination refused; previous save and original source preserved')
        if destination.is_dir():raise HasError('Save destination is blocked by a directory; previous save preserved')
    boundary=existing_boundary(target.parent)
    target.parent.mkdir(parents=True,exist_ok=True)
    with save_lock(target):
        return _pack_locked({**request,'path':str(target),'_sync_boundary':str(boundary)})


def _pack_locked(request):
    folder = Path(request['folder']).resolve(strict=True)
    chosen = Path(request['path']).expanduser()
    target = chosen.parent.resolve() / chosen.name
    sync_paths={target.parent};sidecars_synced=os.name=='posix'
    for destination in (target, Path(str(target)+'.backup'), Path(str(target)+'.backup.tmp')):
        if destination.is_symlink(): raise HasError('Linked save destination refused; previous save and original source preserved')
        if destination.is_dir(): raise HasError('Save destination is blocked by a directory; previous save preserved')
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
        limit = asset_limit(name)
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
                    if reference.parent.is_symlink() or reference.is_symlink():raise HasError('Linked managed sidecar refused; previous save and original source preserved')
                    if not reference.is_file() or sha(reference) != digest:
                        if reference.exists(): raise HasError('Conflicting linked sidecar asset')
                        checked_copy(path, reference, digest, request)
                    if os.name=='posix':
                        with reference.open('rb') as stream:os.fsync(stream.fileno())
                    sync_paths.add(reference.parent)
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
    verify_written_archive(temporary,header_blob,payload,request)
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
                    old_header_blob=old.read('has.json');header=read_json(old_header_blob);members(read_json(old.read('project.json')))
                    valid=header.get('format')=='hybrid_animation_studio' and header.get('version')==1 and header.get('storage') in ('packed','linked')
                    if valid:verify_written_archive(target,old_header_blob,header['payload'],request)
        except (OSError,ValueError,KeyError,TypeError,EOFError,zlib.error,zipfile.BadZipFile,RuntimeError): valid = False
        if valid:
            backup = Path(str(target)+'.backup')
            checked_copy(target, backup, sha(target), request)
    synced=True
    for directory in sync_parents(sync_paths,request['_sync_boundary']):
        check_cancel(request);synced=sync_directory(directory) and synced
    check_cancel(request); os.replace(temporary,target)
    try:final_synced=sync_directory(target.parent)
    except OSError as error:return {'ok':False,'committed':True,'error':'HAS file was written, but directory sync failed: '+str(error)}
    return {'ok':True,'path':str(target),'storage':mode,'bytes':target.stat().st_size,'directory_synced':synced and final_synced,'owned_sidecars_synced':sidecars_synced}


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
            limit = MAX_META if name in ('has.json','project.json') else asset_limit(name)
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
            limit=asset_limit(name)
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
