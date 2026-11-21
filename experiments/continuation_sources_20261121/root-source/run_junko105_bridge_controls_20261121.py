from pathlib import Path
import hashlib,json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[1]
source=root/'output/source-character-parts-root-runner-v2-prep-20261121/test_native_identity_bridge.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='c795bf11e555adf279921c6bc1daa930fbce8a98b3096df0a1c1930fbfacef8d'
case=root/'output'/('junko105-bridge-controls-'+str(time.time_ns()));case.mkdir()
env=dict(os.environ);before=dict(os.environ)
with (case/'stdout.log').open('xb') as out,(case/'stderr.log').open('xb') as err:
    child=subprocess.Popen([sys.executable,'-I','-S','-B','-u',str(source)],cwd=case,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    try:code=child.wait(timeout=30)
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=5)
lines=(case/'stdout.log').read_text().splitlines()
value=json.loads(lines[-1].removeprefix('NATIVE_IDENTITY_BRIDGE_RESULT '))
assert code==0 and not (case/'stderr.log').read_bytes()
assert len([line for line in lines if line.startswith('PASS ')])==32
assert value['checks']==32 and value['failures']==0 and value['synthetic_only'] is True and value['native_inputs_read'] is False
assert dict(os.environ)==before
result={'status':'PASS','checks':32,'pid':child.pid,'exit_code':code,'reaped':True,'hidden':True,'synthetic_only':True,'native_inputs_read':False,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'case':str(case)}
(case/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
