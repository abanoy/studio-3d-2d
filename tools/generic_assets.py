"""Declared local dependencies for OBJ/MTL and glTF. FBX images are staged by its worker."""
from pathlib import Path
import base64
import hashlib
import json
import shlex
from urllib.parse import unquote, urlsplit

MAX_TOTAL=512*1024*1024
MAX_FILE=128*1024*1024
IMAGE_EXT={'.png','.jpg','.jpeg','.tga','.bmp','.tif','.tiff','.webp','.dds'}


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def local_file(parent, name, root):
    name=name.replace('\\','/')
    if not name or name.startswith('/') or ':' in name or '\x00' in name:raise ValueError('Dependency must be a relative local path: '+name)
    path=(Path(parent)/name).resolve()
    if not path.is_relative_to(root):raise ValueError('Dependency is outside the asset folder. Select a common parent folder: '+name)
    if not path.is_file():raise ValueError('Missing dependency: '+str(path))
    if path.stat().st_size>MAX_FILE:raise ValueError('Dependency exceeds128MiB: '+name)
    return path


def words(line):
    lexer=shlex.shlex(line,posix=True);lexer.escape='';lexer.whitespace_split=True;lexer.commenters='#'
    return list(lexer)


def map_parts(tokens):
    i=0
    while i<len(tokens) and tokens[i].startswith('-'):
        option=tokens[i].lower();i+=1
        if option in ('-o','-s','-t'):
            count=0
            while i<len(tokens) and count<3:
                try:float(tokens[i])
                except ValueError:break
                i+=1;count+=1
            if not count:raise ValueError('Invalid MTL map option '+option)
        elif option=='-mm':i+=2
        elif option in ('-bm','-clamp','-blendu','-blendv','-imfchan','-texres','-type','-cc','-boost'):i+=1
        else:raise ValueError('Unsupported MTL map option '+option)
    if i>=len(tokens):raise ValueError('MTL texture path is missing')
    return tokens[:i],' '.join(tokens[i:])


def map_name(tokens):return map_parts(tokens)[1]


def dependencies(source,root):
    source=Path(source).resolve(strict=True);root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('Asset folder must be a directory')
    if not source.is_relative_to(root):raise ValueError('Asset folder must contain the selected source')
    found={source}
    if source.stat().st_size>MAX_FILE:raise ValueError('Source exceeds128MiB')
    total=source.stat().st_size
    def remember(path):
        nonlocal total
        if path not in found:
            total+=path.stat().st_size;found.add(path)
            if len(found)>2048 or total>MAX_TOTAL:raise ValueError('Dependency budget exceeded (2048files/512MiB)')
    if source.suffix.lower()=='.gltf':
        if source.stat().st_size>16*1024*1024:raise ValueError('glTF JSON exceeds16MiB')
        doc=json.loads(source.read_text(encoding='utf-8-sig'))
        if not isinstance(doc,dict) or not isinstance(doc.get('asset'),dict) or doc['asset'].get('version')!='2.0':raise ValueError('Only glTF2.0 is supported')
        buffers=doc.get('buffers',[]);images=doc.get('images',[])
        if not isinstance(buffers,list) or not isinstance(images,list) or len(buffers)+len(images)>2048:raise ValueError('Invalid or excessive glTF dependencies')
        for row in buffers+images:
            if not isinstance(row,dict):raise ValueError('Invalid glTF resource record')
            uri=row.get('uri')
            if uri is None:continue
            if not isinstance(uri,str):raise ValueError('Invalid glTF resource URI')
            if uri.startswith('data:'):
                header,encoded=uri.split(',',1)
                if not header.endswith(';base64') or len(encoded)>MAX_FILE*4//3+8:raise ValueError('Unsupported or oversized glTF data URI')
                if len(base64.b64decode(encoded,validate=True))>MAX_FILE:raise ValueError('Embedded resource exceeds128MiB')
                continue
            parsed=urlsplit(uri)
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:raise ValueError('glTF resources must be local files, without URLs/query/fragment')
            remember(local_file(source.parent,unquote(parsed.path,errors='strict'),root))
    elif source.suffix.lower()=='.obj':
        materials=[]
        with source.open(encoding='utf-8-sig',errors='replace') as stream:
            for line in stream:
                tokens=words(line)
                if tokens and tokens[0].lower()=='mtllib':
                    names=tokens[1:]
                    if not names:raise ValueError('OBJ material library filename is missing')
                    combined=' '.join(names)
                    if combined and (source.parent/combined).is_file():names=[combined]
                    for name in names:
                        material=local_file(source.parent,name,root);remember(material);materials.append(material)
                        if len(materials)>2048:raise ValueError('Excessive OBJ material library references')
        for material in materials:
            if material.suffix.lower()!='.mtl':raise ValueError('OBJ material library must be MTL')
            if material.stat().st_size>4*1024*1024:raise ValueError('MTL exceeds4MiB')
            for line in material.read_text(encoding='utf-8-sig',errors='replace').splitlines():
                tokens=words(line)
                if tokens and (tokens[0].lower().startswith('map_') or tokens[0].lower() in ('bump','disp','decal','norm')):
                    image=local_file(material.parent,map_name(tokens[1:]),root)
                    if image.suffix.lower() not in IMAGE_EXT:raise ValueError('Unsupported MTL image type: '+image.suffix)
                    remember(image)
    elif source.suffix.lower()!='.fbx':raise ValueError('Choose FBX, OBJ or glTF2.0')
    if len(found)>2048 or sum(p.stat().st_size for p in found)>MAX_TOTAL:raise ValueError('Dependency budget exceeded (2048files/512MiB)')
    return [{'path':str(p),'relative':p.relative_to(root).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(found)]
