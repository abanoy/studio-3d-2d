"""Owned synthetic Python-only24 contracts; no actual Full/native/app calls."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
HERE=Path(__file__).resolve().parent
PINS={"source1102":{"bytes":11485,"sha256":"1cc8384a4ad167b336eaccd819559b11a754c66ed2f0bc8ef4b7778cd7b063ce"},"test":{"bytes":4123,"sha256":"3980bf6464261d026af14ae399bb611b98c73a22b980818bf393a1967d13092a"}}
def read(path):return path.read_bytes()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def stable(path):
    s=path.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode)
assert not sys.flags.optimize
paths={'source1102':HERE/'source1102.py','test':HERE/'test_source1102_contracts.py'}
before={name:(stable(path),read(path)) for name,path in paths.items()}
for name,(stamp,raw) in before.items():assert len(raw)==PINS[name]['bytes'] and digest(raw)==PINS[name]['sha256']
env=dict(os.environ)
for name in tuple(env):
    if name.startswith('HYBRID_') or name in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(name,None)
for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
    path=HERE/'Profile'/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
command=[sys.executable,'-B','-u',str(paths['test'])]
result={'format':'has_source1102_contracts_cpu_1','status':'FAIL','executor':'hair_bundles child CPU lane',
        'expected_checks':24,'native_or_graphical_jobs':False,'actual_Full_checkout_accessed':False,
        'actual_Full_admission_called':False,'application_adopted':False,'Full1102_claimed':False,
        'source_pins':PINS,'command':command,'started_ns':time.time_ns()}
process=None
try:
    with (HERE/'stdout.log').open('xb') as out,(HERE/'stderr.log').open('xb') as err:
        process=subprocess.Popen(command,cwd=HERE,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        result['pid']=process.pid
        try:result['exit']=process.wait(timeout=30)
        except BaseException:
            process.kill();process.wait(timeout=10);raise
    stdout=(HERE/'stdout.log').read_text(encoding='utf-8');stderr=(HERE/'stderr.log').read_text(encoding='utf-8')
    lines=stdout.splitlines();result['checks']=sum(line.startswith('PASS ') for line in lines)
    result['strict_summary']=lines[-1:] == ['SOURCE1102_CONTRACTS 24 authored controls completed']
    assert result['exit']==0 and result['checks']==24 and result['strict_summary'] and not stderr and not any(line.startswith('FAIL') for line in lines)
    result['status']='PASS'
except BaseException as error:result['error_type']=type(error).__name__;result['error']=str(error)
finally:
    result['reaped']=process is not None and process.poll() is not None
    result['inputs_preserved']=all(stable(paths[name])==stamp and read(paths[name])==raw for name,(stamp,raw) in before.items())
    result['source_before_after_equal']=result['inputs_preserved']
    result['child_tree_scope']='Reviewed test imports only stdlib and copied reader; it never launches subprocesses.'
    result['finished_ns']=time.time_ns()
    for leaf in ('stdout.log','stderr.log'):
        p=HERE/leaf
        if p.exists():result[leaf.replace('.','_')+'_sha256']=digest(read(p))
    if not result['reaped'] or not result['inputs_preserved']:result['status']='FAIL'
    raw=(json.dumps(result,indent=2)+'\n').encode();(HERE/'RESULT.json').write_bytes(raw)
    print(raw.decode(),flush=True)
raise SystemExit(0 if result['status']=='PASS' else 1)
