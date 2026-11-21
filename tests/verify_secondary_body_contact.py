"""Current-source hair-contact CPU checks:25 synthetic,or54 with protected inputs.
Optional --project,--collider-input,--alignment are read-only original inputs.
Uses ordinary owned Windows Jobs and unique profiles;no prior Full is required.
"""
from pathlib import Path
import argparse,hashlib,json,math,os,sys,time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT))
import verify_import_capability as V

INPUTS=(('project','036eb37fcb17d71e6292751bb1af4b73350512c69a0c31a59efb4fa6a4341101'),
        ('collider_input','e3ada9ac313b21919c3a0d35617d8ec1dbd8cdf6abfe5dec0d8af4f7dd699971'),
        ('alignment','6ebf7e4793550a14a29ae569afaeb863cc458582aa07398fa5218948c89b2b7c'))
SYNTHETIC=(('math','tests/secondary_segment_contact_unit.gd','SECONDARY_SEGMENT_CONTACT ',17),
           ('budget','tests/secondary_body_contact_budget_unit.gd','SECONDARY_BODY_CONTACT_BUDGET ',8))
SAVED=(('construct','tests/secondary_body_colliders_smoke.gd','SECONDARY_BODY_COLLIDERS ',8),
       ('flow','tests/secondary_body_contact_smoke.gd','SECONDARY_BODY_CONTACT ',11),
       ('surface','tests/secondary_body_skin_contact_smoke.gd','SECONDARY_BODY_SKIN_CONTACT ',10))


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


def contract(name,value):
    if name=='math':V.need(value.get('native_or_graphics_used') is False,'Synthetic math scope required')
    elif name=='budget':V.need(value.get('synthetic_only') is True,'Synthetic compatibility scope required')
    elif name=='construct':
        V.need(value.get('fitted_colliders')==4 and value.get('inspected_vertices')==13111
               and value.get('source_arrays_published') is False,'Protected construction scope differs')
    elif name=='flow':
        V.need(value.get('runs')==2 and value.get('ticks_per_run')==480
               and value.get('contact_clearance_tolerance_changed') is False
               and number(value.get('active_minimum_segment_clearance'))
               and value['active_minimum_segment_clearance']>=-.00005,'Deterministic live-flow scope differs')
    elif name=='surface':
        stats=value.get('contact_stats',{})
        V.need(value.get('ticks')==480 and value.get('hair_vertices')==989
               and type(value.get('penetrating_skin_vertex_pairs')) is int
               and value['penetrating_skin_vertex_pairs']==0
               and number(value.get('minimum_skin_clearance')) and value['minimum_skin_clearance']>=-.00005
               and number(value.get('maximum_palette_disagreement'))
               and 0<=value['maximum_palette_disagreement']<=.00001
               and value.get('graphics_used') is False and value.get('source_arrays_published') is False
               and stats.get('vertices')==989 and stats.get('refreshes')==480
               and stats.get('hot_array_reads')==0,'Actual skin/cache scope differs')
    else:raise RuntimeError('Unknown contact case')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name,_digest in INPUTS:parser.add_argument('--'+name.replace('_','-'),type=Path)
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':parser.error('This verifier requires the owned Windows descendant-Job helper')
    supplied=[getattr(options,name) is not None for name,_digest in INPUTS]
    if any(supplied) and not all(supplied):parser.error('Supply all three protected inputs together,or none')
    saved=all(supplied);expected=54 if saved else 25
    raw_output=options.output or ROOT/'output/secondary-body-contact'/str(time.time_ns())
    V.safe(raw_output,missing=True);folder=raw_output.resolve()
    V.need(folder.is_relative_to((ROOT/'output').resolve()) and not folder.exists(),'Use a new output directory')
    folder.mkdir(parents=True);(folder/'Cases').mkdir()
    environment=dict(os.environ);frozen,blobs=V.source_blobs();input_rows=[]
    result={'format':'has_secondary_body_contact_cpu_1','status':'FAIL','checks':0,
            'expected_checks':expected,'scope':'protected_saved_case' if saved else 'synthetic',
            'cases':[],'whole_full_claimed':False,'graphics_used':False,'prior_Full_required':False,
            'owner_assets_read':saved,'source_arrays_published':False}
    primary=None;runtime=None
    try:
        for name,digest in INPUTS if saved else ():
            path=V.safe(getattr(options,name)).resolve(strict=True);raw=V.read(path)
            V.need(hashlib.sha256(raw).hexdigest()==digest,'Protected original input differs: '+name)
            input_rows.append((name,path,V.identity(path.lstat()),digest))
        source_rows=[{'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
                     for name,raw in sorted(blobs.items())]
        source_raw=(json.dumps({'format':'has_contact_cpu_source_hashes_1','files':source_rows},indent=2)+'\n').encode()
        V.new(folder/'SOURCE_HASHES.json',source_raw)
        result['source_hash_manifest_sha256']=hashlib.sha256(source_raw).hexdigest()
        result['source_files']=len(blobs)
        runtime=V.studio(folder,'CPUStudio',blobs)
        flags={name:str(path) for name,path,_stamp,_digest in input_rows}
        for name,script,marker,count in SYNTHETIC+(SAVED if saved else ()):
            extra=[] if name in ('math','budget') else [flags['project']]
            if name=='surface':extra+=[flags['collider_input'],flags['alignment']]
            row=V.run_case(folder,name,runtime,script,marker,count,extra,True,result,None)
            contract(name,row['report'])
            case_json=(json.dumps(row['report'],indent=2)+'\n').encode()
            target=folder/'Cases'/name/'result.json';V.new(target,case_json)
            V.need(json.loads(V.read(target))==row['report'],'Case JSON and actual marker differ')
            row['case_json_sha256']=hashlib.sha256(case_json).hexdigest()
            result['checks']=sum(item.get('checks',0) for item in result['cases'])
        V.need(len(result['cases'])==(5 if saved else 2) and result['checks']==expected,'Complete requested scope required')
        result['status']='PASS'
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__;result['error']=str(error)
    finally:
        result['source_preservation_failures']=[];result['runtime_source_preservation_failures']=[]
        try:
            current,_unused=V.source_blobs()
            result['source_preservation_failures']=V.sources_unchanged(frozen)
            result['all_admitted_sources_unchanged']=not result['source_preservation_failures'] and set(current)==set(frozen)
            if runtime:
                for name,raw in blobs.items():
                    if V.read(runtime/name)!=raw:result['runtime_source_preservation_failures'].append(name)
            result['all_runtime_sources_unchanged']=not result['runtime_source_preservation_failures']
        except BaseException as error:
            result['all_admitted_sources_unchanged']=False;result['all_runtime_sources_unchanged']=False
            result['source_error_type']=type(error).__name__
        result['original_inputs_preserved']=True
        try:
            for _name,path,stamp,digest in input_rows:
                V.need(V.identity(path.lstat())==stamp and hashlib.sha256(V.read(path)).hexdigest()==digest
                       and V.identity(path.lstat())==stamp,'Original protected input changed')
        except BaseException:result['original_inputs_preserved']=False
        result['parent_environment_preserved']=dict(os.environ)==environment
        result['all_private_jobs_and_desktops_closed']=bool(result['cases']) and all(
            row.get('launcher_reaped') is True and row.get('launcher_handle_closed') is True
            and row.get('private_resources_closed') is True for row in result['cases'])
        if not all(result.get(key) is True for key in ('all_admitted_sources_unchanged','all_runtime_sources_unchanged',
                'original_inputs_preserved','parent_environment_preserved','all_private_jobs_and_desktops_closed')):result['status']='FAIL'
        V.new(folder/'verification.json',(json.dumps(result,indent=2)+'\n').encode())
        print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}))
    if primary is not None:raise primary
    V.need(result['status']=='PASS','Contact source/input/process preservation failed')


if __name__=='__main__':main()
