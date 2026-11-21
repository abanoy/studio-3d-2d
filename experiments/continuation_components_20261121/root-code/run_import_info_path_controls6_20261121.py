from pathlib import Path
import hashlib,json,os,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'output/source-import-capability-headless163-c315-v2-prep-20261121'
source=PREP/'test_runtime_paths.py';before_source=source.read_bytes();assert hashlib.sha256(before_source).hexdigest()=='122e296be0f33ec2f45b057b75e56b88db32fced450ea3f0164800505cfb08f7'
driver=(PREP/'run_headless163.py').read_bytes();assert hashlib.sha256(driver).hexdigest()=='d63dbc045fdbd2bdf0b33fa84ff8fcc0f424db4c35cb8814965e33f67507d9ed'
case=ROOT/'output'/('import-info-path-controls6-'+str(time.time_ns()));case.mkdir();(case/'Temp').mkdir()
parent=dict(os.environ);env=dict(parent);env.update(TEMP=str(case/'Temp'),TMP=str(case/'Temp'),PYTHONDONTWRITEBYTECODE='1')
with (case/'stdout.log').open('xb') as out,(case/'stderr.log').open('xb') as err:
 child=subprocess.Popen([sys.executable,'-I','-S','-B','-u',str(source)],cwd=case,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=child.wait(timeout=30)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=5)
logs=(case/'stderr.log').read_text();assert code==0 and not (case/'stdout.log').read_bytes()
assert re.search(r'Ran 6 tests in [0-9.]+s',logs) and logs.rstrip().endswith('OK') and 'ERROR' not in logs and 'FAIL' not in logs
assert source.read_bytes()==before_source and (PREP/'run_headless163.py').read_bytes()==driver and dict(os.environ)==parent
result={'status':'PASS','tests':6,'pid':child.pid,'exit':code,'reaped':True,'hidden':True,'synthetic_only':True,
 'native_or_Main_inputs_read':False,'component163_qualified':False,'source_and_environment_preserved':True,'case':str(case)}
(case/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
