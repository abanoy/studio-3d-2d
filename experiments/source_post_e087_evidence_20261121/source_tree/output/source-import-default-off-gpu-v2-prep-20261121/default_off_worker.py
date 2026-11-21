"""Owned child only: execute the unchanged OFF-default verifier with retained jobs."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys,types
sys.dont_write_bytecode=True

def pin(role):
    raw=Path(role['path']).read_bytes()
    if len(raw)!=role['bytes'] or hashlib.sha256(raw).hexdigest()!=role['sha256']:raise ValueError('WORKER_INPUT_PIN_DIFFERS')
    return raw

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--request-sha256',required=True);args=parser.parse_args()
    raw=Path(args.request).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.request_sha256:raise ValueError('WORKER_REQUEST_PIN')
    request=json.loads(raw)
    if request.get('format')!='has_exact_five_import_off_worker_1':raise ValueError('WORKER_REQUEST_FORMAT')
    helper_raw=pin(request['coordinator']);spec=importlib.util.spec_from_file_location('_off_gpu_worker_helpers',request['coordinator']['path'])
    H=importlib.util.module_from_spec(spec);sys.modules[spec.name]=H;exec(compile(helper_raw,request['coordinator']['path'],'exec',dont_inherit=True),H.__dict__)
    studio=Path(request['studio']);case=Path(request['case']);fixtures=Path(request['fixtures']);runtime=request['runtime'];document=request['fixture_document']
    need=H.need;read=H.read;H.read(args.request,digest=args.request_sha256)
    for role in request['owned_sources']:read(role['path'],role['bytes'],role['sha256'])
    need(Path(os.environ['HYBRID_NATIVE_FIXTURES'])==fixtures and Path(os.environ['TEMP'])==Path(request['temp']),'WORKER_OWNED_ENVIRONMENT')
    env=os.environ.copy();result={'format':'has_exact_five_import_off_worker_result_1','status':'FAIL','jobs':[]};primary=None
    try:
        private=studio/'output/private-desktop';private.mkdir(parents=True)
        command=[runtime['pythonw'],str(studio/'tools/private_desktop.py'),'--receipt',str(private/'import.json'),'--',runtime['godot'],
            '--headless','--audio-driver','Dummy','--path',str(studio),'--editor','--import','--quit']
        imported=H.owned_command(command,case,studio,runtime,env,result['jobs'],window=False,timeout=90);need(imported.returncode==0,'IMPORT_FAILED')
        sys.path[:0]=[str(studio),str(studio/'tests')]
        spec=importlib.util.spec_from_file_location('_owned_import_off_verifier',studio/'tests/verify_import_physics.py');verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
        need(verifier.ROOT==studio,'OWNED_VERIFIER_ROOT');actual_prepare=verifier.prepare
        def strict_prepare(folder):
            originals=actual_prepare(folder)
            plans=H.parse(read(Path(folder)/'native-plans.json',limit=4*1024*1024,remember=False))
            need([row.get('label') for row in plans]==H.EXPECTED_LABELS[:3],'ALL_THREE_PREPARED_SOURCE_PROFILES_REQUIRED')
            for plan,pin_row in zip(plans,document['models'][:3]):
                asset=H.safe(plan['source']);need(asset.is_relative_to(fixtures),'PREPARED_PLAN_ESCAPED_MIRROR');read(asset,pin_row['asset']['bytes'],pin_row['asset']['sha256'])
            return originals
        verifier.prepare=strict_prepare
        def gpu_run(args,**kwargs):
            H.audit_plan_file(case/'smoke/native-plans.json',document,studio,fixtures)
            return H.owned_command(args,case,studio,runtime,env,result['jobs'],window=True,timeout=min(int(kwargs.get('timeout',210)),210))
        def ffprobe_output(args,**kwargs):
            need(Path(args[0])==Path(runtime['ffprobe']),'ONLY_PINNED_FFPROBE_ALLOWED')
            process=None;row={'name':'ffprobe','reaped':False,'private_job_required':False};result['jobs'].append(row)
            try:
                process=H.subprocess.Popen(args,cwd=studio,env=env,stdout=H.subprocess.PIPE,stderr=H.subprocess.PIPE,creationflags=H.subprocess.CREATE_NO_WINDOW)
                H.OWNED.append((process,row));out,err=process.communicate(timeout=30)
                need(process.returncode==0 and len(out)<=1024*1024 and len(err)<=1024*1024,'FFPROBE_FAILED_OR_UNBOUNDED')
                return out.decode('utf-8') if kwargs.get('text') else out
            finally:
                if process is not None:row['reaped']=H.reap(process)
        verifier.subprocess=types.SimpleNamespace(run=gpu_run,check_output=ffprobe_output)
        previous=sys.argv;sys.argv=[str(studio/'tests/verify_import_physics.py'),'--output',str(case/'smoke')]
        try:verifier.main()
        finally:sys.argv=previous
        verification=H.parse(read(case/'smoke/verification.json',limit=8*1024*1024));plans=H.audit_plan_file(case/'smoke/native-plans.json',document,studio,fixtures)
        need(type(verification.get('checks')) is int and verification['checks']>0 and type(verification.get('failures')) is int and verification['failures']==0 and verification.get('native_models')==5,'ACTUAL_SMOKE_CHECKS_OR_PROFILES')
        engine=read(case/'smoke/engine.log',limit=H.MAX_LOG).decode('utf-8','replace')
        need(sum(line.startswith('PASS ') for line in engine.splitlines())==verification['checks'],'ACTUAL_NAMED_ASSERTION_COUNT')
        need(all(label in engine for label in H.EXPECTED_LABELS),'FIVE_NATIVE_PROFILE_NAMES_NOT_OBSERVED')
        result.update(status='PASS',checks=verification['checks'],failures=0,native_profiles_observed=len(plans),video=verification['video'],gpu_private_receipt=verification['private_receipt'],existing_verifier_completed=True)
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__;result['error_code']=str(error) if type(error) is H.Refusal else 'OWNED_VERIFIER_EXCEPTION'
    finally:
        for process,row in H.OWNED:row['reaped']=H.reap(process)
        result['all_owned_launchers_reaped']=all(row['reaped'] for _p,row in H.OWNED)
        result['all_private_jobs_closed']=all(not row.get('private_job_required',True) or row['private_job_closed'] and row['desktop_closed'] for _p,row in H.OWNED)
        failures=H.preserve();result['all_worker_read_inputs_preserved']=not failures;result['preservation_failures']=failures
        if failures or not result['all_owned_launchers_reaped'] or not result['all_private_jobs_closed']:result['status']='FAIL'
        H.json_new(case/'WORKER_RESULT.json',result)
    return 0 if result['status']=='PASS' and primary is None else 1
if __name__=='__main__':raise SystemExit(main())
