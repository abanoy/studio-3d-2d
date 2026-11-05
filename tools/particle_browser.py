"""Bounded named-PCF-system browsing/preparation. Never runs game/add-on scripts."""
from pathlib import Path
import argparse,json,os
from asset_audit import AssetError
from particle_effect import compile_effect
from source_particles import Resources,decoder,systems
from source_paths import DEFAULT_GMOD,DEFAULT_WORKSHOP
from source_installation import installed_context
from prepare_particle_effect import budget,prepare

def list_systems(request):
    source=Path(request['provider']).resolve(strict=True)
    installed_context(request.get('gmod',DEFAULT_GMOD),request.get('workshop',DEFAULT_WORKSHOP),request.get('extra',[]),source)
    _,dmx=decoder(request.get('sourceio'))
    resource=Resources([source]);blob=resource.read(request['member']);rows=systems(blob,dmx)
    result=[]
    for system in rows:
        try:
            effect=compile_effect(system,request.get('duration',2),request.get('seed',17))
            if not effect['particles']:raise AssetError('No births inside the chosen duration')
            candidate=True;reason='Basic operators supported; material and texture are checked when preparing.'
        except AssetError as error:candidate=False;reason=str(error)
        result.append({'name':system['name'],'candidate':candidate,'reason':reason})
    return {'ok':True,'systems':result,'source_sha256':resource.reads[0]['sha256'],'note':'Support is a HAS sprite approximation; complete parent/child effects, trails and richer shaders are not imported.'}

def execute(request):
    if request.get('action')=='list':return list_systems(request)
    if request.get('action')=='prepare':return {'ok':True,**prepare(request,request['output'])}
    raise AssetError('Unknown particle browser action')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('request',type=Path);args=parser.parse_args()
    handle=budget()
    if args.request.stat().st_size>1024*1024:raise AssetError('Particle request exceeds1MiB')
    request=json.loads(args.request.read_text(encoding='utf-8'));target=Path(request['result'])
    try:result=execute(request)
    except Exception as error:result={'ok':False,'error':str(error)}
    blob=json.dumps(result,ensure_ascii=True,allow_nan=False).encode('utf-8')
    if len(blob)>1024*1024:blob=json.dumps({'ok':False,'error':'Particle system list exceeds1MiB; choose a smaller file.'}).encode()
    temporary=target.with_name(target.name+'.tmp');temporary.write_bytes(blob);os.replace(temporary,target)
    return 0 if result['ok']else 1

if __name__=='__main__':raise SystemExit(main())
