"""Focused private UI checks for the generated hair preset and both wind routes."""
from pathlib import Path
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT))
import verify_import_capability as V


def main():
    V.need(os.name=='nt','Approved private Windows desktop required')
    folder=ROOT/'output'/('generated-controls-'+str(time.time_ns()));folder.mkdir();(folder/'Cases').mkdir()
    environment=dict(os.environ);frozen,blobs=V.source_blobs();runtime=None;primary=None
    result={'status':'FAIL','cases':[],'owner_assets_used':False,'whole_full_claimed':False}
    try:
        runtime=V.studio(folder,'Studio',blobs)
        for classic,advanced in ((False,False),(False,True),(True,False),(True,True)):
            name=('classic' if classic else 'neon')+('-advanced' if advanced else '-simple')
            flags=(['--classic'] if classic else [])+(['--advanced'] if advanced else [])
            row=V.run_case(folder,name,runtime,'tests/generated_secondary_controls_smoke.gd','GENERATED_SECONDARY_CONTROLS ',16,flags,False,result,None)
            V.need(row['report'].get('captures')==3 and row['report'].get('owner_assets_used') is False,'Generated-only graphical scope required')
            V.need(row['report'].get('classic') is classic and row['report'].get('advanced') is advanced,'Actual theme/workspace must match the requested variant')
        result['status']='PASS'
    except BaseException as error:primary=error;result['error']=str(error)
    finally:
        result['checks']=sum(row.get('checks',0) for row in result['cases'])
        result['source_preservation_failures']=V.sources_unchanged(frozen)
        result['runtime_preserved']=runtime is not None and all(V.read(runtime/name)==raw for name,raw in blobs.items())
        result['parent_environment_preserved']=dict(os.environ)==environment
        result['all_private_resources_closed']=bool(result['cases']) and all(row.get('private_resources_closed') is True and row.get('launcher_reaped') is True and row.get('launcher_handle_closed') is True for row in result['cases'])
        if result['source_preservation_failures'] or not all(result.get(key) is True for key in ('runtime_preserved','parent_environment_preserved','all_private_resources_closed')):result['status']='FAIL'
        (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}))
    if primary is not None:raise primary
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
