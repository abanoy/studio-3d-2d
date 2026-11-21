import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-carrier-empty-extension-prep-20261120'
out=root/'output/source-carrier-empty-extension-cpu-20261120-01'
pins={'carrier_export.py': (29402, '762f7892b1fa30de34b4d494ac8aae2cc3c910a324a6785e0771ff7ea7b86dd9'), 'test_carrier_export.py': (51480, 'ffb4ad6bc7b472e7229bb773060e576d738feb1824d565b96aa9a273baf8770f')}
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
r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p','test_carrier_export.py'],cwd=root,capture_output=True)
elapsed=time.monotonic()-start
(out/'stdout.log').write_bytes(r.stdout); (out/'stderr.log').write_bytes(r.stderr)
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_carrier_empty_extension_cpu_root_1','status':'PASS' if r.returncode==0 and before==after else 'FAIL','returncode':r.returncode,'elapsed_seconds':elapsed,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':45}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); print(r.stderr.decode('utf-8',errors='replace'))
raise SystemExit(0 if result['status']=='PASS' else 1)