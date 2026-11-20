"""Retain sequential private workflow/native/reference regression observations."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[2]
module_spec=importlib.util.spec_from_file_location('body_full_manifest',Path(__file__).with_name('run_full.py'))
manifest=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(manifest)


def main():
    folder=ROOT/'output'/('reference-body-scoped-'+str(time.time_ns()));folder.mkdir()
    before=manifest.snapshot();(folder/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
    commands=[('reference-body-neon',['tests/verify_reference_body.py','--theme','neon'],'reference-body-neon-verification.json'),
              ('reference-body-light',['tests/verify_reference_body.py','--theme','light'],'reference-body-light-verification.json'),
              ('reference-body-native',['tests/verify_reference_body_native.py'],'reference-body-native-verification.json'),
              ('human-reference-neon',['tests/verify_human_reference.py','--theme','neon'],'human-reference-neon-verification.json'),
              ('human-reference-light',['tests/verify_human_reference.py','--theme','light'],'human-reference-light-verification.json')]
    results={};passed=False;error='';start=time.time_ns()
    try:
        for name,args,result_file in commands:
            began=time.time_ns();argv=[sys.executable,'-B','-u',*args]
            with (folder/(name+'.log')).open('wb') as log:
                process=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=1200,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            path=ROOT/'output'/result_file
            assert process.returncode==0 and path.is_file() and path.stat().st_mtime_ns>=began,(name,process.returncode)
            result=json.loads(path.read_bytes())
            results[name]=dict(exit=process.returncode,seconds=(time.time_ns()-began)/1e9,
                    result=result,result_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),args=argv)
            (folder/(name+'-verification.json')).write_text(json.dumps(results[name],indent=2)+'\n')
            print('PASS '+name+' '+str(round(results[name]['seconds'],3))+'s',flush=True)
        assert manifest.snapshot()==before,'Functional files or driver bytes/mtimes changed'
        passed=True
    except Exception as failure:
        error=type(failure).__name__+': '+str(failure)
        raise
    finally:
        after=manifest.snapshot();(folder/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
        report=dict(format='has_reference_body_scoped_1',passed=passed,error=error,folder=str(folder),
                seconds=(time.time_ns()-start)/1e9,sources_unchanged=before==after,source_count=len(before),results=results)
        (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print('REFERENCE_BODY_SCOPED '+json.dumps({key:value for key,value in report.items() if key!='results'}),flush=True)


if __name__=='__main__':main()
