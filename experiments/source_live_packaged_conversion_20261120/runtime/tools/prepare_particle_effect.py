"""Bounded explicit PCF -> native sprite descriptor experiment, not main app UI."""
from pathlib import Path
import argparse,ctypes,hashlib,json,os,sys
from ctypes import wintypes
from source_particles import Resources,decoder,systems,native_vtf,png_rgba
from particle_effect import compile_effect
from source_content import mount_paths,kv_read
from source_paths import DEFAULT_GMOD,DEFAULT_WORKSHOP
from source_installation import installed_context
from source_archive import resource_path
from private_desktop import ExtendedLimits

def budget():
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateJobObjectW.restype=wintypes.HANDLE;k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
    k.SetInformationJobObject.restype=wintypes.BOOL;k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
    k.AssignProcessToJobObject.restype=wintypes.BOOL;k.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
    k.GetCurrentProcess.restype=wintypes.HANDLE;k.GetCurrentProcess.argtypes=[]
    handle=k.CreateJobObjectW(None,None);limits=ExtendedLimits();limits.BasicLimitInformation.LimitFlags=0x102;limits.BasicLimitInformation.PerProcessUserTimeLimit=30*10000000;limits.ProcessMemoryLimit=512*1024*1024
    if not handle or not k.SetInformationJobObject(handle,9,ctypes.byref(limits),ctypes.sizeof(limits))or not k.AssignProcessToJobObject(handle,k.GetCurrentProcess()):raise OSError(ctypes.get_last_error(),'Particle worker budget unavailable')
    return handle

def prepare(request,output):
    source=Path(request['provider']).resolve(strict=True);member=resource_path(request['member'])
    context=installed_context(request.get('gmod',DEFAULT_GMOD),request.get('workshop',DEFAULT_WORKSHOP),request.get('extra',[]),source)
    base,dmx=decoder(request.get('sourceio'));discovery=context['discovery']
    for provider in discovery['providers']:
        if provider['path']in request.get('mount_overrides',{}):provider['enabled']=bool(request['mount_overrides'][provider['path']])and provider['present']
    resources=Resources([source,*mount_paths(discovery,source)]);native=resources.read(member);rows=systems(native,dmx)
    matches=[s for s in rows if s['name']==request['system']]
    if len(matches)!=1:raise ValueError('Select one exact particle system name')
    system=matches[0];effect=compile_effect(system,request.get('duration',2),request.get('seed',17))
    material_name=system['parameters'].get('material','').replace('\\','/').lower();material_name='materials/'+material_name.removeprefix('materials/').removesuffix('.vmt')+'.vmt'
    material=resources.read(material_name)
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    # Stage only data already selected, never includes/proxies/add-on scripts.
    material_path=output/'material.vmt';material_path.write_bytes(material);vmt=kv_read(material_path)
    if len(vmt)!=1 or vmt[0][0].lower()not in['spritecard','unlitgeneric']or not isinstance(vmt[0][1],list):raise ValueError('Unsupported particle material shader/include')
    values={}
    for key,value in vmt[0][1]:
        key=key.lower()
        if key in values or not isinstance(value,str):raise ValueError('Material proxies/nested/duplicate values unsupported')
        values[key]=value
    if set(values)-{'$basetexture','$vertexcolor','$vertexalpha','$translucent','$additive','$surfaceprop'}:raise ValueError('Unsupported particle material controls')
    if values.get('$additive')!='1'or values.get('$vertexcolor','1')!='1'or values.get('$vertexalpha','1')!='1':raise ValueError('Only vertex-colored additive particle materials supported')
    texture_name=values.get('$basetexture','').replace('\\','/').lower();texture_name='materials/'+texture_name.removeprefix('materials/').removesuffix('.vtf')+'.vtf'
    texture=resources.read(texture_name);png=png_rgba(texture,native_vtf(base))
    effect['texture']={'path':'sprite.png','sha256':hashlib.sha256(png).hexdigest(),'blend':'additive'}
    (output/'sprite.png').write_bytes(png);(output/'effect.json').write_text(json.dumps(effect,indent=2,allow_nan=False),encoding='utf-8')
    (output/'source.pcf').write_bytes(native);(output/'source.vtf').write_bytes(texture)
    report={'source_profile':'Source sprite approximation','system':system,'resources':resources.reads,'mount_warnings':resources.warnings,'sourceio_revision':base.name,'decoder_sha256':hashlib.sha256((base/'library/utils/datamodel.py').read_bytes()).hexdigest(),'effect_format':effect['format'],'births':len(effect['particles']),'max_live':effect['max_particles'],'limits':['Experimental adapter; not yet main editor/HAS import','Own seeded random values and analytic gravity; not native Source simulation equivalence','Fixed CP0; no moving attachments, child systems, trails, forces, refraction, sprite sheets or animated VTF','Culling/performance hints retained but not simulated','Source units mapped x,z,-y at0.01905; native data retained']}
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    return {'output':str(output),'system':system['name'],'births':len(effect['particles']),'resources':resources.reads}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('request',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    handle=budget()
    if args.request.stat().st_size>1024*1024:raise ValueError('Particle request exceeds1MiB')
    request=json.loads(args.request.read_text(encoding='utf-8'));print(json.dumps(prepare(request,args.output)))

if __name__=='__main__':main()
