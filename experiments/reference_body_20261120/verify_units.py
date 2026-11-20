"""Strict real-engine mechanical checks for the reference-size body increment."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from run import command

CASES=(('reference_body_scale_guard','REFERENCE_BODY_SCALE_GUARD ',71),
       ('reference_body_plan_unit','REFERENCE_BODY_PLAN_UNIT ',71),
       ('reference_body_anatomy_unit','REFERENCE_BODY_ANATOMY_UNIT ',75),
       ('reference_body_physics_unit','REFERENCE_BODY_PHYSICS_UNIT ',1039),
       ('physics_recording_unit','PHYSICS_RECORDING_UNIT ',17))
BAD=(b'ERROR:',b'FAIL ',b'ObjectDB instances leaked',b'resources still in use')


def source():
    names=['src/physics_rig.gd','src/physics_recording.gd','src/reference_body_plan.gd']
    names+=['tests/'+name+'.gd' for name,_,_ in CASES]
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def main():
    folder=ROOT/'output'/('reference-body-units-'+str(time.time_ns()))
    folder.mkdir();before=source();results={}
    for name,marker,count in CASES:
        args=command('tests/'+name+'.gd',True,extra=['--log-file',str(folder/(name+'-engine.log'))])
        start=time.perf_counter()
        process=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=150,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        log=process.stdout+process.stderr;(folder/(name+'.log')).write_bytes(log)
        assert process.returncode==0 and not any(value in log for value in BAD),log[-5000:]
        result=json.loads(next(line.split(marker,1)[1] for line in log.decode('utf-8').splitlines() if line.startswith(marker)))
        assert result['checks']==count and result['failures']==0,result
        if name=='reference_body_physics_unit':assert result['fixed_tick_cases']==9,result
        results[name]=dict(result=result,seconds=time.perf_counter()-start,exit=process.returncode,
                log_sha256=hashlib.sha256(log).hexdigest(),args=args)
        print(name+': '+json.dumps(result),flush=True)
    assert source()==before
    result=dict(format='has_reference_body_units_1',passed=True,folder=str(folder),sources=before,
            sources_unchanged=True,results=results)
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('REFERENCE_BODY_UNITS '+str(folder),flush=True)


if __name__=='__main__':main()
