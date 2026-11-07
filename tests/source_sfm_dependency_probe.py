"""Read-only native material/texture inspection, never a Source import bypass."""
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
from collections import Counter
import argparse,importlib.util,json,hashlib,os,sys,struct
p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sourceio",type=Path,required=True);p.add_argument("--inventory",type=Path,required=True);p.add_argument("--metadata",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--asset-root",type=Path,required=True);args=p.parse_args()
if args.output.exists():raise FileExistsError(args.output)
import numpy as np
os.environ['NO_BPY']='1'
root=args.sourceio.resolve(strict=True);spec=importlib.util.spec_from_file_location('SourceIO',root/'__init__.py',submodule_search_locations=[str(root)]);module=importlib.util.module_from_spec(spec);sys.modules['SourceIO']=module;spec.loader.exec_module(module)
from SourceIO.library.source1.vmt import VMT
from SourceIO.library.source1.vtf import load_texture
from SourceIO.library.utils import MemoryBuffer,TinyPath
packages=json.loads(args.inventory.read_text());metadata=json.loads(args.metadata.read_text());by_model={(r['archive'],r['model']):r for r in metadata['models']}
materials=[];textures=[];models=[];decoded={};unchanged=True
for package in packages:
 folder=Path(package['folder']).resolve(strict=True);members=package['members'];virtual={}
 if not folder.is_relative_to(args.asset_root.resolve(strict=True)):raise ValueError('Sample folder escaped the explicit asset root')
 for name in members:
  if not (folder/name).resolve(strict=True).is_relative_to(folder):raise ValueError('Resource escaped its sample folder')
 for name in members:
  parts=PurePosixPath(name).parts
  for i,part in enumerate(parts):
   if part.lower() in ('materials','models'):
    virtual['/'.join(parts[i:]).casefold()]=folder/name;break
 def lookup(name):
  name=str(name).replace('\\','/').casefold();parts=PurePosixPath(name).parts
  if name.startswith('/') or ':' in name or '..' in parts:raise ValueError('Unsafe native resource reference')
  return virtual.get('/'.join(parts))
 for source in package['models']:
  row=by_model[(package['archive_name'],source['path'])];missing=[];resolved=[]
  for material in row['material_names']:
   found=None
   for search in row['material_search_paths']:
    name=(search.replace('\\','/').rstrip('/')+'/'+material).replace('\\','/').strip('/')
    if not name.lower().startswith('materials/'):name='materials/'+name
    if not name.lower().endswith('.vmt'):name+='.vmt'
    found=lookup(name)
    if found:break
   if found:resolved.append(str(found.relative_to(folder)))
   else:missing.append(material)
  parts=PurePosixPath(source['path']).parts;start=next(i for i,p in enumerate(parts) if p.lower()=='models');native=PurePosixPath(*parts[start:]);complete=lookup(str(native.with_suffix('.vvd'))) is not None and any(lookup(str(native.with_suffix(suffix))) is not None for suffix in ['.dx90.vtx','.dx80.vtx','.sw.vtx','.vtx']);models.append({'archive':package['archive_name'],'model':source['path'],'materials_found':len(resolved),'missing_materials':missing,'complete_geometry_sidecars':complete})
 for name,entry in members.items():
  path=folder/name
  if path.suffix.lower()=='.vmt':
   row={'archive':package['archive_name'],'path':name};calls=[0]
   def find_file(resource):
    calls[0]+=1
    if calls[0]>128:raise ValueError('Material include lookup bound exceeded')
    found=lookup(resource)
    return MemoryBuffer(found.read_bytes()) if found else None
   try:
    vmt=VMT(MemoryBuffer(path.read_bytes()),TinyPath(name),SimpleNamespace(find_file=find_file));row['shader']=vmt.shader;row['textures']={};row['missing_textures']=[]
    for field in ['$basetexture','$bumpmap','$normalmap','$detail','$iris','$envmapmask','$phongexponenttexture']:
     value=vmt.get_string(field,'')
     if not value or value.lower().startswith(('env_cubemap','_rt_')):continue
     resource=value.replace('\\','/');resource=resource[10:] if resource.lower().startswith('materials/') else resource;resource=resource[:-4] if resource.lower().endswith('.vtf') else resource;found=lookup('materials/'+resource+'.vtf');row['textures'][field]=value
     if found is None:row['missing_textures'].append(value)
   except Exception as e:row['error']=type(e).__name__+': '+str(e)
   materials.append(row)
  elif path.suffix.lower()=='.vtf':
   row={'archive':package['archive_name'],'path':name,'sha256':entry['sha256']}
   if entry['sha256'] in decoded:row['duplicate_of']=decoded[entry['sha256']];textures.append(row);continue
   raw=path.read_bytes();decoded[entry['sha256']]=len(textures)
   try:
    if len(raw)<20 or raw[:4]!=b'VTF\0':raise ValueError('Invalid VTF header')
    width,height=struct.unpack_from('<HH',raw,16);row['width']=width;row['height']=height
    if not width or not height or width*height>16777216:row['refused']='Texture exceeds existing16megapixel decode bound'
    else:
     pixels,h,w=load_texture(MemoryBuffer(raw));row['decoded_shape']=list(pixels.shape) if pixels is not None else None
     if pixels is None or (w,h)!=(width,height) or pixels.shape!=(height,width,4) or not np.all(np.isfinite(pixels)):raise ValueError('Invalid decoded VTF pixels/dimensions')
     row['decoded_sha256']=hashlib.sha256(pixels.tobytes()).hexdigest();del pixels
   except Exception as e:row['error']=type(e).__name__+': '+str(e)
   textures.append(row)
 for name,entry in members.items():
  if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=entry['sha256']:unchanged=False
summary={'models':len(models),'models_with_all_material_files':sum(not r['missing_materials'] for r in models),'models_with_geometry_sidecars':sum(r['complete_geometry_sidecars'] for r in models),'material_files':len(materials),'material_errors':sum('error'in r for r in materials),'material_missing_texture_references':sum(len(r.get('missing_textures',[])) for r in materials),'texture_files':len(textures),'unique_textures':len(decoded),'decoded_unique_textures':sum('decoded_sha256'in r for r in textures),'texture_errors':sum('error'in r for r in textures),'texture_refusals':sum('refused'in r for r in textures),'original_extracted_files_unchanged':unchanged,'scope':'Pinned SourceIO read-only MDL material lookup/VMT/VTF decoder only. No mesh conversion, native app import, rig posing or renderer-fidelity acceptance; installed-host guard unchanged.'}
args.output.write_text(json.dumps({'summary':summary,'models':models,'materials':materials,'textures':textures},indent=2));print(json.dumps(summary,indent=2))
