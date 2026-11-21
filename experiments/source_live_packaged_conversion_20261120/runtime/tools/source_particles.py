"""Read-only particle resources; optional pinned decoders, no game/add-on execution.

This is the bounded adapter foundation, not normal Studio particle importing yet.
"""
from pathlib import Path
import hashlib,importlib.util,io,json,math,struct,sys,zlib
from asset_audit import AssetError,gma_index
from source_archive import resource_path
from source_content import vpk_index,vpk_read,kv_read

PIN='fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
ROOT=Path(__file__).resolve().parents[1]
MAX_FILE=8*1024*1024

class Resources:
    def __init__(self,paths):
        self.paths=list(dict.fromkeys(Path(p).resolve()for p in paths));self.indexes={};self.reads=[];self.warnings=[];self.total=0
        if len(self.paths)>4096:raise AssetError('Too many particle resource locations')

    def read(self,name):
        name=resource_path(name).lower()
        if not(name.startswith('particles/')and name.endswith('.pcf')or name.startswith('materials/')and name.endswith(('.vmt','.vtf'))):raise AssetError('Not a particle/material resource')
        for path in self.paths:
            blob=None
            if path.is_dir():
                p=(path/name).resolve()
                if not p.is_relative_to(path):raise AssetError('Particle resource escapes location')
                if not p.is_file():continue
                if p.stat().st_size>MAX_FILE:raise AssetError('Particle resource exceeds8MiB')
                before=(p.stat().st_size,p.stat().st_mtime_ns);blob=p.read_bytes()
                if before!=(p.stat().st_size,p.stat().st_mtime_ns):raise AssetError('Particle resource changed while reading')
            elif path.suffix.lower()in['.gma','.vpk']:
                key=str(path)
                if key not in self.indexes:
                    try:
                        if path.suffix.lower()=='.vpk':index={'entries':vpk_index(path)}
                        else:
                            if path.stat().st_size>512*1024*1024:raise AssetError('GMA exceeds512MiB')
                            with path.open('rb')as stream:index=gma_index(stream,path.stat().st_size)
                        index['lookup']={r.get('path',r.get('name','')).lower():r for r in index['entries']}
                        self.indexes[key]=index
                    except (OSError,ValueError,EOFError)as error:
                        self.indexes[key]=None;self.warnings.append({'path':key,'error':str(error)});continue
                index=self.indexes[key]
                if not index:continue
                entry=index['lookup'].get(name)
                if not entry:continue
                if entry.get('bytes',entry.get('size',0))>MAX_FILE:raise AssetError('Particle resource exceeds8MiB')
                if path.suffix.lower()=='.vpk':blob=vpk_read(path,entry)
                else:
                    with path.open('rb')as stream:stream.seek(index['payload_start']+entry['relative_offset']);blob=stream.read(entry['size'])
                    if len(blob)!=entry['size']or zlib.crc32(blob)&0xffffffff!=entry['crc32']:raise AssetError('Particle GMA resource CRC mismatch')
            if blob is not None:
                if self.total+len(blob)>64*1024*1024:raise AssetError('Particle dependency budget exceeds64MiB')
                self.total+=len(blob);self.reads.append({'provider':str(path),'resource':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()});return blob
        raise AssetError('Missing installed particle resource: '+name)

def decoder(sourceio=None):
    base=Path(sourceio or ROOT/'output/dependencies'/('sourceio-'+PIN)).resolve()
    reader=base/'library/utils/datamodel.py'
    if not reader.is_file():raise AssetError('The documented optional SourceIO parser is unavailable')
    spec=importlib.util.spec_from_file_location('has_particle_datamodel',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return base,module

def systems(blob,module):
    if len(blob)>MAX_FILE:raise AssetError('PCF exceeds8MiB')
    if not blob[:160].startswith(b'<!-- dmx encoding binary '):raise AssetError('Only binary Source PCFs are supported')
    model=module.load(in_file=io.BytesIO(blob))
    if model.format!='pcf'or model.format_ver not in[1,2]or len(model.elements)>50000:raise AssetError('Unsupported or excessive PCF graph')
    def plain(value,depth=0):
        if depth>6:raise AssetError('Excessive particle parameter nesting')
        if value is None or isinstance(value,(str,bool,int)):return value
        if isinstance(value,float):
            if not math.isfinite(value):raise AssetError('Nonfinite particle parameter')
            return value
        if isinstance(value,module.Element):return {'name':value.name,'type':value.type,'element_id':str(value.id)}
        if isinstance(value,(list,tuple))and len(value)<=64:return[plain(v,depth+1)for v in value]
        raise AssetError('Unsupported particle parameter type: '+type(value).__name__)
    result=[];names=set()
    for element in model.elements:
        if element.type!='DmeParticleSystemDefinition':continue
        if element.name in names:raise AssetError('Ambiguous duplicate particle system name')
        names.add(element.name);groups={}
        for key in ['renderers','operators','initializers','emitters','forces','constraints','children']:
            values=element.get(key,[])
            if len(values)>256:raise AssetError('Excessive particle operators')
            groups[key]=[{'function':v.get('functionName',''),'parameters':{k:plain(p)for k,p in v.items()if k!='functionName'}}for v in values]
        result.append({'name':element.name,'parameters':{k:plain(v)for k,v in element.items()if k not in groups},'groups':groups})
    return result

def native_vtf(sourceio):
    path=Path(sourceio)/'library/utils/pylib'
    name='has_particle_pylib'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path/'__init__.py',submodule_search_locations=[str(path)]);module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        try:spec.loader.exec_module(module)
        except BaseException:sys.modules.pop(name,None);raise
    return sys.modules[name].vtf

def png_rgba(blob,module):
    if len(blob)<64 or blob[:4]!=b'VTF\0':raise AssetError('Not a VTF image')
    # This first adapter deliberately admits only the old header without a
    # resource table: a single frame can still be a sprite sheet in newer VTFs.
    # Refuse before entering the optional native codec, rather than ignoring it.
    major,minor,header=struct.unpack_from('<III',blob,4)
    if major!=7 or minor!=2 or header!=80 or len(blob)<80:raise AssetError('Only VTF7.2/80-byte headers without sprite-sheet resources are supported')
    width,height=struct.unpack_from('<HH',blob,16);frames=struct.unpack_from('<H',blob,24)[0]
    if not width or not height or width*height>4194304 or frames!=1:raise AssetError('Only single-frame VTFs up to4MP are supported')
    if struct.unpack_from('<I',blob,20)[0]&0x4000 or struct.unpack_from('<H',blob,63)[0]!=1:raise AssetError('Only flat non-cubemap VTFs are supported')
    image=module.VTFFile();image.load_bytes(blob,True)
    if image.face_count!=1 or image.frame_count!=1:raise AssetError('Particle cubemap or animated VTF unsupported')
    rgba,w,h,is_float=module.load_vtf_texture(blob)
    if is_float or (w,h)!=(width,height)or len(rgba)!=w*h*4:raise AssetError('Unsupported VTF pixel layout')
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+rgba[y*w*4:(y+1)*w*4]for y in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
