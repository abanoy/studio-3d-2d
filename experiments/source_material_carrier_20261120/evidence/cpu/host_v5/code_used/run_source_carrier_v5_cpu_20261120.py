import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-material-carrier-host-v5-prep-20261120'
base=root/'output/source-material-carrier-host-v4-prep-20261120/SOURCE_PINS.json'
out=root/'output/source-carrier-host-v5-cpu-20261120-01'
pins={r['path']:(r['bytes'],r['sha256']) for r in json.loads(base.read_text())['entries'] if r['path'].endswith('.py')}
pins.update({'fresh_carrier_probe.py':(72518,'ca9db9feaa46e70041fb206e8b32062890ee8d4365c9b05e308e0df5edead14e'),'run_carrier.py':(87417,'3b2957d228fd54eff1add759285c7c9509e918c0fa96be0bddfc7e8a698a1411'),'cold_image_readiness.py':(14496,'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9'),'test_cold_image_readiness.py':(22496,'8b8e9be06a1495a77ba5c13b35935151e695b61624964c7860075f94ec0a169f')})
pins['export_hook_proposal.py']=(43512,'636a8d92d29b7c6a7118535cdea0e0ea3ba8a17f12ec30c680280755c6ba4f59')
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
for label,pattern,count in [('worker','test_carrier_worker.py',45),('driver','test_carrier_driver.py',104)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr)
    passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_carrier_host_v5_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':149}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)