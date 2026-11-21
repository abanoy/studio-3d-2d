from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'output/source-miku-contact-c315-1103-successor-prep-20261121'
def pin(p):
 s=p.stat();raw=p.read_bytes();return (s.st_dev,s.st_ino,s.st_nlink,s.st_mode,s.st_size,s.st_mtime_ns,hashlib.sha256(raw).hexdigest())
manifest=SOURCE/'SOURCE_PINS.json';assert pin(manifest)[-1]=='7a7fa46b26ff626d6f3a157679523c92192bdc48af39649239eca770e95bc60b'
inputs={SOURCE/name:pin(SOURCE/name) for name in ('test_source1103_contracts.py','source1103.py','SOURCE_PINS.json')}
assert inputs[SOURCE/'test_source1103_contracts.py'][-1]=='1628ee34b149d8d277b9c1fac82884062032980d2008d762a0f3f7cf8ec74331'
assert inputs[SOURCE/'source1103.py'][-1]=='e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3'
CASE=ROOT/'output'/('source1103-synthetic60-'+str(time.time_ns()));CASE.mkdir()
parent=dict(os.environ)
with (CASE/'stdout.log').open('xb') as out,(CASE/'stderr.log').open('xb') as err:
 child=subprocess.Popen([sys.executable,'-I','-S','-B','-u',str(SOURCE/'test_source1103_contracts.py')],cwd=CASE,env=dict(parent),stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=child.wait(timeout=30)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=5)
lines=(CASE/'stdout.log').read_text().splitlines()
assert code==0 and not (CASE/'stderr.log').read_bytes()
assert len([line for line in lines if line.startswith('PASS ')])==60 and lines[-1]=='SOURCE1103_CONTRACTS 60 controls completed'
assert all(pin(p)==row for p,row in inputs.items()) and dict(os.environ)==parent
result={'format':'has_source1103_synthetic60_root_1','status':'PASS','checks':60,'child_pid':child.pid,'exit':code,'reaped':True,
 'synthetic_only':True,'native_inputs_read':False,'source_and_environment_preserved':True,'Full_admission_claimed':False,'case':str(CASE)}
(CASE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
