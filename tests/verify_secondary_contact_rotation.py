"""Twenty generated rotation controls against actual current SRC; no overlays/assets.
Optional --reference deliberately runs the retained pre-fix reference as a red test.
"""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT)]
import verify_import_capability as V
REFERENCE='tests/reference/secondary_skin_contact_baseline.gd'
REFERENCE_SHA='0bea5b2633866301cae9eef958f48a02a7db13da6d67967083954458b9debb13'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',action='store_true',help='Run the pre-fix reference; expected to FAIL six feasible-orbit assertions')
    options=parser.parse_args()
    frozen,blobs=V.source_blobs();environment=dict(os.environ)
    V.need(sha(blobs[REFERENCE])==REFERENCE_SHA,'Exact retained independent reference differs')
    script='tests/secondary_contact_rotation_unit.gd'
    V.need(script in blobs and 'tests/verify_secondary_contact_rotation.py' in blobs,'Install public current-source test before running')
    source=REFERENCE if options.reference else 'src/secondary_skin_contact.gd'
    source_sha=sha(blobs[source])
    folder=ROOT/'output'/('secondary-contact-rotation-'+str(time.time_ns()));folder.mkdir();(folder/'Cases').mkdir()
    runtime=V.studio(folder,'Studio',blobs)
    result={'format':'secondary_contact_rotation_current_source_1','status':'FAIL','checks':0,'expected_checks':20,'cases':[],'source_context':'exact_current_source_snapshot','overlay_files':0,'reference_mode':options.reference,'selected_source_sha256':source_sha,'graphics_used':False,'private_assets_read':False,'whole_hair_claimed':False}
    problem=None
    try:
        flags=['--source-sha',source_sha]+(['--reference'] if options.reference else [])
        row=V.run_case(folder,'generated',runtime,script,'SECONDARY_CONTACT_ROTATION ',20,flags,True,result,None)
        report=row['report']
        V.need(report.get('reference_mode') is options.reference and report.get('selected_source_sha256')==source_sha,'Selected actual function or pin differs')
        V.need(report.get('synthetic_only') is True and report.get('graphics_used') is False and report.get('private_assets_read') is False,'Pure generated scope differs')
        result.update(status='PASS',checks=20,failures=0)
    except BaseException as error:problem=error;result['error_type']=type(error).__name__
    finally:
        result['source_preservation_failures']=V.sources_unchanged(frozen)
        now,_=V.source_blobs();result['source_membership_preserved']=set(now)==set(frozen)
        result['runtime_preserved']=all(V.read(runtime/name)==raw for name,raw in blobs.items())
        result['environment_preserved']=dict(os.environ)==environment
        result['all_jobs_closed']=bool(result['cases']) and all(x.get('private_resources_closed') is True and x.get('launcher_reaped') is True and x.get('launcher_handle_closed') is True for x in result['cases'])
        # A reference red result stays FAIL. Preserve actual marker counts without
        # treating an expected failure as a passing product qualification.
        stdout=folder/'Cases/generated/stdout.log'
        if stdout.is_file():
            marker='SECONDARY_CONTACT_ROTATION '
            hits=[line[len(marker):] for line in V.read(stdout).decode('utf-8','replace').splitlines() if line.startswith(marker)]
            if len(hits)==1:
                report=json.loads(hits[0])
                if type(report.get('checks')) is int and type(report.get('failures')) is int:
                    result['observed_checks']=report['checks'];result['observed_failures']=report['failures']
        if result['source_preservation_failures'] or not all(result[k] is True for k in ('source_membership_preserved','runtime_preserved','environment_preserved','all_jobs_closed')):result['status']='FAIL'
        V.new(folder/'PRIVATE_VERIFICATION.json',(json.dumps(result,indent=2)+'\n').encode())
        public={k:v for k,v in result.items() if k!='cases'}
        public['cases']=[{k:v for k,v in row.items() if k in ('name','launcher_exit','launcher_reaped','launcher_handle_closed','private_resources_closed','private_receipt_mode','private_receipt_sha256','graphical_placement_proven')} for row in result['cases']]
        V.new(folder/'verification.json',(json.dumps(public,indent=2)+'\n').encode())
        print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(folder/'verification.json')}),flush=True)
    if problem is not None:raise problem
    V.need(result['status']=='PASS','Generated current-source rotation controls failed')
    return 0
if __name__=='__main__':raise SystemExit(main())
