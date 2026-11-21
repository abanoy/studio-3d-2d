from pathlib import Path
import hashlib,json,os,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'output/source-easing-c315-graphics-qualification-prep-20261121'
manifest=SOURCE/'SOURCE_PINS.json';manifest_raw=manifest.read_bytes()
assert hashlib.sha256(manifest_raw).hexdigest()=='71f1ea3af625b2032639ef4837c4a195d086b31e94a72d81a82aa7b31a9a8466'
inputs={}
for name in ('test_gate_file_fixtures.py','source1103.py'):
 row=next(r for r in json.loads(manifest_raw)['files'] if r['path']==name)
 raw=(SOURCE/name).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];inputs[name]=raw
case=ROOT/'output'/('easing-gate-files3-'+str(time.time_ns()));case.mkdir();(case/'Temp').mkdir()
before=dict(os.environ);env=dict(before);env.update(TEMP=str(case/'Temp'),TMP=str(case/'Temp'),PYTHONDONTWRITEBYTECODE='1')
with (case/'stdout.log').open('xb') as out,(case/'stderr.log').open('xb') as err:
 child=subprocess.Popen([sys.executable,'-I','-S','-B','-u',str(SOURCE/'test_gate_file_fixtures.py')],cwd=case,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=child.wait(timeout=30)
 finally:
  if child.poll() is None:child.kill();child.wait(timeout=5)
text=(case/'stderr.log').read_text();assert code==0 and not (case/'stdout.log').read_bytes()
assert re.search(r'Ran 3 tests in [0-9.]+s',text) and text.rstrip().endswith('OK') and 'ERROR' not in text and 'FAIL' not in text
assert all((SOURCE/name).read_bytes()==raw for name,raw in inputs.items()) and manifest.read_bytes()==manifest_raw and dict(os.environ)==before
result={'format':'has_easing_gate_files3_root_1','status':'PASS','tests':3,'process_pid':child.pid,'exit':code,'reaped':True,
 'synthetic_only':True,'native_inputs_read':False,'GUI_or_Full_admission_claimed':False,'sources_and_environment_preserved':True,
 'scope':'Three file-roundtrip checks of already separate synthetic admission policies; not added to60 as new native evidence.','case':str(case)}
(case/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
