"""Current-source contact cache:47 generated checks;optional explicit private720/native15.
No candidate overlays,private assets or earlier Full gate are needed by default.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT)]
import verify_import_capability as V
BASELINE='tests/reference/secondary_skin_contact_baseline.gd'
BASELINE_SHA='0bea5b2633866301cae9eef958f48a02a7db13da6d67967083954458b9debb13'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def input_pin(path):return (V.identity(path.lstat()),sha(V.read(path)))
def same_input(path,pin):return input_pin(path)==pin

REPORT_SCALARS=('checks','failures','synthetic_only','graphics_used','private_assets_read','selected_vertices','chains','natural_chains','collider_instances','skin_vertices','skin_refreshes','centroid_drop','average_tick_usec','anchor_error','original_joint_error','maximum_off_vertex_error','minimum_contact_gap','maximum_remaining_contact_pairs','final_remaining_contact_pairs','production_skin_sha256','compared_ticks','exact_pose','exact_full_fk','exact_solver_metrics','raw_input_preserved','baseline_solver_mean_usec','candidate_solver_mean_usec','baseline_solver_max_usec','candidate_solver_max_usec','comparison_order_alternated','whole_tick_includes_both_solvers_and_comparisons','first_mismatch_tick','first_mismatch_kind')
STATS=('vertices','array_reads','refreshes','corrections','blocked_points','hot_array_reads','remaining_pairs','minimum_gap','iteration_limit_hits','cache_eligible_calls','cache_fallback_calls','broad_tests','narrow_tests','row_cache_hits','row_cache_misses','row_summaries','cache_verification_scans','active_rows_scanned','maximum_active_rows','capsule_builds','cached_rows_evaluated','authoritative_scans','cached_scans','cache_initializations')
def safe_stats(value):
    if not isinstance(value,dict):return {}
    return {key:value[key] for key in STATS if key in value and type(value[key]) in (int,float,bool)}
def safe_report(report):
    value={key:report[key] for key in REPORT_SCALARS if key in report and type(report[key]) in (int,float,bool,str)}
    for key in ('baseline_solver_stats','candidate_solver_stats'):
        if key in report:value[key]=safe_stats(report[key])
    if isinstance(report.get('cases'),list):
        value['cases']=[{**{key:row[key] for key in ('name','baseline_corrections','baseline_remaining_pairs') if key in row and type(row[key]) in (str,int,float,bool)},'candidate_counters':safe_stats(row.get('candidate_counters'))} for row in report['cases'] if isinstance(row,dict)]
    return value

def safe_case(row):
    value={k:row.get(k) for k in ('name','status','checks','expected_checks','headless','launcher_reaped','launcher_handle_closed','private_resources_closed','private_receipt_mode','graphical_placement_proven')}
    report=row.get('report')
    if isinstance(report,dict):value['report']=safe_report(report)
    if row.get('private_receipt'):
        raw=V.read(Path(row['private_receipt']));proof=json.loads(raw)
        V.need(sha(raw)==row['private_receipt_sha256'],'Physical receipt changed before projection')
        value['receipt_sha256']=sha(raw)
        value['closure']={k:proof.get(k) for k in ('exit','job_closed','desktop_closed','private_window_seen','child_desktop_confirmed','foreground_child_observed','desktop_switch_requested')}
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','candidate','spec'):parser.add_argument('--'+name,type=Path)
    for name in ('source','candidate','spec'):parser.add_argument('--'+name+'-sha256')
    options=parser.parse_args()
    names=('source','candidate','spec')
    group=[getattr(options,n) for n in names]+[getattr(options,n+'_sha256') for n in names]
    V.need(not any(group) or all(group),'Native paths and their three expectedSHA256 pins must be supplied all together')
    V.need(os.name=='nt','Existing bounded Windows private-headless launcher required')
    native=all(group);protected={};private_inputs=[]
    if native:
        for name in names:
            expected=getattr(options,name+'_sha256')
            V.need(isinstance(expected,str) and re.fullmatch('[0-9a-f]{64}',expected) is not None,'Expected lower-case SHA256 required')
            path=getattr(options,name).resolve(strict=True);V.safe(path)
            raw=V.read(path);V.need(sha(raw)==expected,'Explicit native input differs from expectedSHA256')
            protected[path]=input_pin(path);private_inputs.append(path)
        V.need(len(set(private_inputs))==3,'Three distinct original/candidate/spec inputs required')
        V.need(options.source_sha256!=options.candidate_sha256,'Derived candidate must differ from original source')
    environment=dict(os.environ);frozen,blobs=V.source_blobs()
    V.need(BASELINE in blobs and sha(blobs[BASELINE])==BASELINE_SHA,'Byte-exact independent reference baseline required')
    required=('tests/secondary_contact_cache_unit.gd','tests/secondary_contact_cache_native_smoke.gd','tests/verify_secondary_contact_cache.py','src/secondary_skin_contact.gd')
    V.need(all(name in blobs for name in required),'Installed current-source cache verifier files missing')
    production_sha=sha(blobs['src/secondary_skin_contact.gd'])
    folder=ROOT/'output'/('secondary-contact-cache-'+str(time.time_ns()));folder.mkdir();(folder/'Cases').mkdir()
    runtime=V.studio(folder,'Studio',blobs)
    result={'format':'has_secondary_contact_cache_current_source_1','status':'FAIL','checks':0,'expected_checks':62 if native else 47,'cases':[],'graphics_used':False,'native_requested':native,'source_context':'exact_current_source_snapshot','overlay_files':0,'baseline_reference_sha256':BASELINE_SHA,'production_skin_sha256':production_sha,'whole_full_claimed':False,'whole_hair_complete':False,'native_input_sha256':{name:getattr(options,name+'_sha256') for name in names} if native else {}}
    problem=None
    try:
        row=V.run_case(folder,'generated',runtime,'tests/secondary_contact_cache_unit.gd','SECONDARY_CONTACT_CACHE_UNIT ',47,[],True,result,None)
        V.need(row['report'].get('synthetic_only') is True and row['report'].get('private_assets_read') is False and row['report'].get('graphics_used') is False,'Generated47 scope differs')
        if native:
            row=V.run_case(folder,'native',runtime,'tests/secondary_contact_cache_native_smoke.gd','SECONDARY_CONTACT_CACHE_NATIVE ',15,[str(private_inputs[1]),str(private_inputs[2]),str(private_inputs[0]),production_sha],True,result,None)
            metrics=row['report']
            V.need(metrics.get('production_skin_sha256')==production_sha and metrics.get('compared_ticks')==720 and metrics.get('first_mismatch_tick')==-1,'Actual installed production source must complete all720 ticks')
            V.need(all(metrics.get(key) is True for key in ('exact_pose','exact_full_fk','exact_solver_metrics','raw_input_preserved','comparison_order_alternated')),'Exact720pose/FK/metrics/input/order contract failed')
        result['checks']=sum(row.get('checks',0) for row in result['cases'])
        V.need(result['checks']==result['expected_checks'],'Required current-source control count differs')
        result['status']='PASS'
    except BaseException as error:
        problem=error;result['error']=str(error);result['error_type']=type(error).__name__
    finally:
        result['source_preservation_failures']=V.sources_unchanged(frozen)
        current,_=V.source_blobs();result['source_membership_preserved']=set(current)==set(frozen)
        result['runtime_preserved']=all(V.read(runtime/name)==raw for name,raw in blobs.items())
        result['protected_inputs_preserved']=all(same_input(path,pin) for path,pin in protected.items())
        result['parent_environment_preserved']=dict(os.environ)==environment
        result['all_jobs_closed']=bool(result['cases']) and all(row.get('private_resources_closed') is True and row.get('launcher_reaped') is True and row.get('launcher_handle_closed') is True for row in result['cases'])
        if result['source_preservation_failures'] or not all(result[key] is True for key in ('source_membership_preserved','runtime_preserved','protected_inputs_preserved','parent_environment_preserved','all_jobs_closed')):result['status']='FAIL'
        V.new(folder/'PRIVATE_VERIFICATION.json',(json.dumps(result,indent=2)+'\n').encode())
        public={k:v for k,v in result.items() if k not in ('cases','error')}
        public['cases']=[safe_case(row) for row in result['cases']]
        if problem is not None:public['error']='Control orpreservation gate failed;retained private local logs contain details'
        V.new(folder/'verification.json',(json.dumps(public,indent=2)+'\n').encode())
        print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}),flush=True)
    if problem is not None:raise problem
    V.need(result['status']=='PASS','Current-source cache source/runtime/input/Job gate failed')
    return 0

if __name__=='__main__':raise SystemExit(main())
