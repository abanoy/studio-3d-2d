from pathlib import Path
out=Path(__file__).resolve().parent
text=(out/'run_import_info_canonical267_v2_scoped_20261121.py').read_text()
anchor="(studio/'override.cfg').write_text("
assert text.count(anchor)==1
extra='''META=OUT/'source-import-info-full-receipts-prep-20261121'
meta_raw=(META/'SOURCE_PINS.json').read_bytes();assert sha(meta_raw)=='a460d911b587e17251fa4bade39ec11a3b44f6b5ee47fe2ad31bf9b6fc1c3bdb'
protected[META/'SOURCE_PINS.json']=meta_raw
for row in json.loads(meta_raw)['files']:
 p=META/row['path'];raw=p.read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];protected[p]=raw
for row in json.loads((META/'TARGETS.json').read_bytes())['targets']:
 p=studio/row['path'];raw=p.read_bytes();assert len(raw)==row['base_bytes'] and sha(raw)==row['base_sha256'];p.write_bytes(protected[META/'payload'/row['path']])
'''
text=text.replace(anchor,extra+anchor)
changes=[('has-import-info-canonical267-v2-','has-import-info-metadata163-'),("report_dir=studio/'output/component267'","report_dir=studio/'output/import-capability-canonical'/str(time.time_ns())"),("'--scope','all'","'--scope','cpu'"),("timeout=4200","timeout=600"),("value.get('checks')==267","value.get('checks')==163"),("len(value.get('cases',[]))==21 and len(value.get('pairs',[]))==8","len(value.get('cases',[]))==5 and len(value.get('pairs',[]))==0"),("'has_import_info_canonical267_root_v2_1'","'has_import_info_metadata163_root_1'"),("'CPU_and_GUI_single_component_batch':True","'CPU_and_GUI_single_component_batch':False"),("'ordinary component all267, no Full'","'ordinary component metadata CPU163, no Full'"),("'ordinary component all267, no Full'","'ordinary component metadata CPU163, no Full'"),("'public verifier267'","'public verifier metadata163'")]
for old,new in changes:
 if old in text:text=text.replace(old,new)
anchor="report_dir=studio/'output/import-capability-canonical'/str(time.time_ns());start=time.time_ns()"
assert text.count(anchor)==1
extra='''with (stage/'policy-stdout.log').open('xb') as out,(stage/'policy-stderr.log').open('xb') as err:
 policy=subprocess.run([sys.executable,'-I','-S','-B','-u',str(studio/'experiments/reference_body_20261120/test_receipt_provenance.py')],cwd=studio,env=env,stdout=out,stderr=err,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
policy_logs=(stage/'policy-stdout.log').read_text()+(stage/'policy-stderr.log').read_text()
assert policy.returncode==0 and 'Ran 47 tests' in policy_logs and 'OK' in policy_logs
(stage/'POLICY47_RESULT.json').write_text(json.dumps({'format':'has_import_info_coordinator_policy47_1','status':'PASS','checks':47,'exit':0,'new_negative_controls':30,'prior_provenance_controls':17,'Full_claimed':False,'source_manifest_sha256':sha(meta_raw)},indent=2)+'\\n')
'''
text=text.replace(anchor,extra+anchor)
anchor="(stage/'ROOT_RESULT.json').write_text("
assert text.count(anchor)==1
extra='''proof_module=module('_metadata_actual_policy',studio/'experiments/reference_body_20261120/run_full.py')
admitted=proof_module.import_info_headless_receipts(studio,{'import_capability':value},proof_module.receipts(),start,time.time_ns(),proof_module.snapshot(),expected_checks=163)
assert len(admitted)==5
result['actual_headless_receipts_independently_admitted']=5
result['metadata_manifest_sha256']=sha(meta_raw)
result['policy47_passed']=True
'''
text=text.replace(anchor,extra+anchor)
target=out/'run_import_info_metadata163_20261121.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print(str(target))
