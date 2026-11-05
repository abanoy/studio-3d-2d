"""Read-only, bounded Krita source inventory for a future normalized 2D clip.

This reads metadata, not paint tiles. A merged image is a saved still, never an
animation decoder. Native rendering remains the installed Krita's responsibility.
"""
from pathlib import Path
import copy,hashlib,struct,xml.dom.minidom,xml.etree.ElementTree as ET,zipfile,zlib

MAX_SOURCE=2*1024**3
MAX_FILES=32768
MAX_CENTRAL=16*1024**2
MAX_XML=4*1024**2
MAX_XML_TOTAL=16*1024**2

class KritaError(ValueError):pass

def local(tag):return tag.rsplit('}',1)[-1]
def integer(value,label,minimum=0,maximum=10_000_000):
    try:result=int(value)
    except (TypeError,ValueError,OverflowError):raise KritaError('Invalid Krita '+label) from None
    if str(result)!=str(value) or not minimum<=result<=maximum:raise KritaError('Unsupported Krita '+label)
    return result

def preflight(path):
    size=path.stat().st_size
    if not 22<=size<=MAX_SOURCE:raise KritaError('Krita source must be no larger than2GiB')
    with path.open('rb') as f:f.seek(max(0,size-65557));tail=f.read(65557)
    offset=tail.rfind(b'PK\x05\x06')
    if offset<0 or len(tail)-offset<22:raise KritaError('Invalid Krita ZIP directory')
    _,disk,start,on_disk,count,central_size,central_offset,comment=struct.unpack_from('<4s4H2IH',tail,offset)
    end=size-len(tail)+offset
    if disk or start or count!=on_disk or not 2<=count<=MAX_FILES or central_size>MAX_CENTRAL or central_offset+central_size!=end or len(tail)-offset!=22+comment:raise KritaError('Unsupported or excessive Krita ZIP directory')

def inspect(source,with_hash=True):
    if str(source).startswith(('\\\\','//')) or '://' in str(source):raise KritaError('Choose a local Krita file, not a network address')
    try:return _inspect(source,with_hash)
    except (OSError,zipfile.BadZipFile,zipfile.LargeZipFile,UnicodeError,zlib.error) as e:raise KritaError('Cannot inspect Krita source: '+str(e)) from None

def _inspect(source,with_hash):
    path=Path(source).resolve(strict=True)
    if not path.is_file() or path.suffix.lower()!='.kra':raise KritaError('Choose a local Krita .kra file')
    before=path.stat();preflight(path)
    result={'format':'studio_krita_inventory_1','source':str(path),'bytes':before.st_size,'layers':[],'channels':[],'rendered':False}
    xml_bytes=0
    with zipfile.ZipFile(path) as z:
        entries=z.infolist();names=[i.orig_filename for i in entries]
        if len(names)!=len(set(names)):raise KritaError('Duplicate Krita ZIP members')
        for name,item in zip(names,entries):
            if '\\' in name or '\x00' in name or ':' in name or name.startswith('/') or any(p in ('.','..','') for p in name.rstrip('/').split('/')):raise KritaError('Unsafe Krita ZIP member')
            if item.flag_bits&1:raise KritaError('Encrypted Krita members are unsupported')
        if 'mimetype' not in names or z.getinfo('mimetype').file_size>128 or z.read('mimetype').strip()!=b'application/x-krita':raise KritaError('Not a Krita document')
        def xml(name):
            nonlocal xml_bytes
            item=z.getinfo(name);xml_bytes+=item.file_size
            if item.file_size>MAX_XML or xml_bytes>MAX_XML_TOTAL:raise KritaError('Krita XML exceeds the metadata budget')
            raw=z.read(item)
            if b'\x00' in raw:raise KritaError('Krita XML must use a single-byte-compatible encoding')
            if b'<!ENTITY' in raw.upper():raise KritaError('Krita XML entity declarations are unsupported')
            try:return ET.fromstring(raw)
            except ET.ParseError as e:raise KritaError('Invalid Krita XML: '+str(e)) from None
        if 'maindoc.xml' not in names:raise KritaError('Missing Krita document metadata')
        doc=xml('maindoc.xml');images=[n for n in doc.iter() if local(n.tag)=='IMAGE']
        if len(images)!=1:raise KritaError('Expected one Krita image')
        image=images[0];result.update(width=integer(image.get('width'),'width',1,32768),height=integer(image.get('height'),'height',1,32768),color_space=image.get('colorspacename',''),profile=image.get('profile',''))
        result['layers']=[dict(n.attrib) for n in image.iter() if local(n.tag)=='layer']
        animations=[n for n in image.iter() if local(n.tag)=='animation']
        if len(animations)>1:raise KritaError('Ambiguous Krita animation metadata')
        def timing(node):
            children=[n for n in node if local(n.tag) in ('framerate','range','currentTime')]
            if len({local(n.tag) for n in children})!=len(children):raise KritaError('Ambiguous Krita timing fields')
            values={local(n.tag):n.attrib for n in children}
            if 'framerate' in values:result['fps']=integer(values['framerate'].get('value'),'frame rate',1,1000)
            if 'range' in values:
                start=integer(values['range'].get('from'),'range start');end=integer(values['range'].get('to'),'range end')
                if end<start:raise KritaError('Reversed Krita playback range')
                result['range']={'start':start,'end_inclusive':end,'frames':end-start+1}
            if 'currentTime' in values:result['saved_current_frame']=integer(values['currentTime'].get('value'),'saved current frame')
        if animations:timing(animations[0]);result['animation_metadata']='maindoc.xml'
        # Krita loads this newer metadata after legacy maindoc animation values.
        # Only present fields override, matching its native loader.
        modern=image.get('name','')+'/animation/index.xml'
        if modern in names:
            legacy={k:result[k] for k in ('fps','range','saved_current_frame') if k in result}
            index=xml(modern)
            if local(index.tag)!='animation-metadata':raise KritaError('Invalid native animation index')
            timing(index);result['animation_metadata']=modern
            if any(result.get(k)!=v for k,v in legacy.items()):result['legacy_timing']=legacy
        for item in entries:
            if not item.filename.lower().endswith('.keyframes.xml'):continue
            channel_doc=xml(item.filename)
            for channel in channel_doc.iter():
                if local(channel.tag)!='channel':continue
                keys=[]
                for key in channel:
                    if local(key.tag)!='keyframe':continue
                    entry=dict(key.attrib);entry['time']=integer(key.get('time'),'keyframe time',-10_000_000);keys.append(entry)
                result['channels'].append({'member':item.filename,'name':channel.get('name',''),'keys':keys})
        result['animated']=any(c['keys'] for c in result['channels'])
        result['keyframe_count']=sum(len(c['keys']) for c in result['channels'])
        result['entries']=len(entries)
        result['native_member_bytes']=sum(i.file_size for i in entries)
        if 'mergedimage.png' in names:
            with z.open('mergedimage.png') as f:header=f.read(24)
            if not header.startswith(b'\x89PNG\r\n\x1a\n') or len(header)!=24:raise KritaError('Invalid merged PNG header')
            width,height=struct.unpack('>II',header[16:24]);result['saved_still']={'member':'mergedimage.png','width':width,'height':height,'bytes':z.getinfo('mergedimage.png').file_size,'animation':False}
    if with_hash:
        with path.open('rb') as f:result['source_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
    after=path.stat()
    if (after.st_size,after.st_mtime_ns)!=(before.st_size,before.st_mtime_ns):raise KritaError('Krita source changed during inspection')
    return result

def render_copy(inventory,visibility,destination,cancel=None):
    """Apply explicitly chosen visibility overrides only to a fresh native copy."""
    if not isinstance(visibility,dict) or len(visibility)>128 or any(not isinstance(k,str) or type(v) is not bool for k,v in visibility.items()):raise KritaError('Invalid layer visibility choices')
    known={r.get('uuid'):r for r in inventory['layers'] if r.get('uuid')}
    if any(key not in known for key in visibility):raise KritaError('Selected Krita layer no longer exists')
    source=Path(inventory['source']);dest=Path(destination)
    if dest.exists() or dest.resolve()==source.resolve():raise KritaError('Layer review needs a fresh scratch copy')
    with zipfile.ZipFile(source) as original:
        raw=original.read('maindoc.xml')
        if b'<!ENTITY' in raw.upper() or b'\x00' in raw:raise KritaError('Unsupported source XML')
        doc=xml.dom.minidom.parseString(raw);found=set()
        for node in doc.getElementsByTagNameNS('*','layer'):
            key=node.getAttribute('uuid')
            if key in visibility:
                if key in found:raise KritaError('Ambiguous Krita layer identity')
                node.setAttribute('visible','1' if visibility[key] else '0');found.add(key)
        if found!=set(visibility):raise KritaError('Selected Krita layers are missing from the document')
        replacement=doc.toxml(encoding='utf-8');doc.unlink()
        with zipfile.ZipFile(dest,'x') as target:
            for item in original.infolist():
                if cancel:cancel()
                info=copy.copy(item)
                if item.filename=='maindoc.xml':target.writestr(info,replacement)
                else:
                    with original.open(item) as src,target.open(info,'w') as sink:
                        for block in iter(lambda:src.read(1024*1024),b''):
                            if cancel:cancel()
                            sink.write(block)
        with zipfile.ZipFile(dest) as candidate:
            assert candidate.namelist()==original.namelist()
            for item in original.infolist():
                if item.filename!='maindoc.xml':
                    copied=candidate.getinfo(item.filename)
                    if (copied.CRC,copied.file_size)!=(item.CRC,item.file_size):raise KritaError('Scratch copy changed native artwork payload')
    return dest
