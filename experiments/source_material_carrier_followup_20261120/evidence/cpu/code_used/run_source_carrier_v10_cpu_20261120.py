import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-material-carrier-host-v10-prep-20261120'
base=root/'output/source-material-carrier-host-v9-prep-20261120/SOURCE_PINS.json'
out=root/'output/source-carrier-host-v10-cpu-20261120-01'
pins={r['path']:(r['bytes'],r['sha256']) for r in json.loads(base.read_text())['entries'] if r['path'].endswith('.py')}
pins.update({'fresh_carrier_probe.py':(72518,'121cc7181d29c45953633e40b39661ac8fe447fce03a3f8b973941a16113f32f'),'run_carrier.py':(87426,'49229ea7066acfd5762a9bd5a22bab21b1823fbb60ba562162dedb1fcaf85483'),'cold_image_readiness.py':(14496,'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9'),'test_cold_image_readiness.py':(22496,'8b8e9be06a1495a77ba5c13b35935151e695b61624964c7860075f94ec0a169f')})
pins['export_hook_proposal.py']=(48895,'cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511')
pins.update({'resource_gate_proposal.py':(54511,'f892ade8fc83d198261edd2fbcdd608ef0cb77ba41a3f1cf52b7705de4fdfea7'),'shared_image_cache_proposal.py':(34089,'b1c0862c21f5e7f86ca889107c4530b68eb624196a83256333ac379f06712b1e'),'test_bounded_read.py':(6889,'876c8f1948dc32e37506446884256475a0ae2381f531dcf2152ce9720f894cca')})
pins.update({'carrier_export.py':(33131,'983c9f44d4588decfb0169d5889db09c77b5b3cec7e1b1e280d38166d70fb763'),'test_carrier_export.py':(61653,'3a990ee974b4f405862b89d502f9d7fed66e726863baef27b6848f4c90758ee5')})
def snap():
    assert {p.relative_to(suite).as_posix() for p in suite.rglob('*.py')}==set(pins)
    rows={}
    for name,(size,digest) in pins.items():
        p=suite/name; b=p.read_bytes(); s=p.stat()
        assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,name
        rows[name]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap(); out.mkdir(exist_ok=False)
(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf-8')
results=[]
for label,pattern,count in [('worker','test_carrier_worker.py',45),('driver','test_carrier_driver.py',104),('bounded','test_bounded_read.py',13)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr)
    passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_carrier_host_v10_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':162}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)