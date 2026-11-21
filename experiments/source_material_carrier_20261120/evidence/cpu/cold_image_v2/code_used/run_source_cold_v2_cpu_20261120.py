import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-cold-image-readiness-v2-prep-20261120'
out=root/'output/source-cold-image-cpu-20261120-02'
pins={'cold_image_readiness.py':(14496,'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9'),'test_cold_image_readiness.py':(22496,'8b8e9be06a1495a77ba5c13b35935151e695b61624964c7860075f94ec0a169f'),'material_inspection.py':(24579,'5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17')}
def snap():
    rows={}
    for name,(size,digest) in pins.items():
        p=suite/name; b=p.read_bytes(); s=p.stat()
        assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,name
        rows[name]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap(); out.mkdir(exist_ok=False)
(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf-8')
start=time.monotonic()
r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p','test_cold_image_readiness.py'],cwd=root,capture_output=True)
elapsed=time.monotonic()-start
(out/'stdout.log').write_bytes(r.stdout); (out/'stderr.log').write_bytes(r.stderr)
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_cold_image_cpu_root_2','status':'PASS' if r.returncode==0 and before==after else 'FAIL','returncode':r.returncode,'elapsed_seconds':elapsed,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':40}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); print(r.stderr.decode('utf-8',errors='replace'))
raise SystemExit(0 if result['status']=='PASS' else 1)