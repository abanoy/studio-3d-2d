import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-material-carrier-host-v11-prep-20261120'
base=root/'output/source-material-carrier-host-v9-prep-20261120/SOURCE_PINS.json'
out=root/'output/source-carrier-host-v11-cpu-20261120-01'
pins={r['path']:(r['bytes'],r['sha256']) for r in json.loads(base.read_text())['entries'] if r['path'].endswith('.py')}
pins.update({'fresh_carrier_probe.py':(72518,'2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea'),'run_carrier.py':(87748,'75daf466f6fe0265088c4cf9efaeb2a3722b8062bf987620a5216529e7c9c51a'),'cold_image_readiness.py':(14496,'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9'),'test_cold_image_readiness.py':(22496,'8b8e9be06a1495a77ba5c13b35935151e695b61624964c7860075f94ec0a169f')})
pins['export_hook_proposal.py']=(48895,'cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511')
pins.update({'resource_gate_proposal.py':(55481,'4ce714dc84712384d089fc2d0b5b5a93c25c1f3dfe90f53ccee76477a3d1cee8'),'shared_image_cache_proposal.py':(36158,'b4aed0a276e5a469274e961e11bddff6183e6d56d4ff91af9e339af4712617e6'),'test_bounded_read.py':(6889,'876c8f1948dc32e37506446884256475a0ae2381f531dcf2152ce9720f894cca')})
pins.update({'carrier_export.py':(33129,'867b8ca6dbd11818edca22d6dc8a0e0671e0855d7d9c7c87ba317e5059868941'),'test_carrier_export.py':(61652,'41c89692c9b3a2ed2ad907864e6885563196443de53a5b31148da54d37b4b425')})
pins['test_carrier_driver.py']=(91105,'e9be91462d48b8c4a1e5e967c3c25fac168e9266cbd9b96db90ece23848ff863')
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
for label,pattern,count in [('worker','test_carrier_worker.py',45),('driver','test_carrier_driver.py',106),('bounded','test_bounded_read.py',13)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr)
    passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_carrier_host_v11_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':164}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)