import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-carrier-image-lifecycle-prep-20261120'
out=root/'output/source-carrier-image-lifecycle-cpu-20261120-01'
pins={'carrier_export.py': (33129, '867b8ca6dbd11818edca22d6dc8a0e0671e0855d7d9c7c87ba317e5059868941'), 'test_carrier_export.py': (61652, '41c89692c9b3a2ed2ad907864e6885563196443de53a5b31148da54d37b4b425')}
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
result={'format':'has_source_carrier_image_lifecycle_cpu_root_1','status':'PASS' if r.returncode==0 and before==after else 'FAIL','returncode':r.returncode,'elapsed_seconds':elapsed,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':52}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); print(r.stderr.decode('utf-8',errors='replace'))
raise SystemExit(0 if result['status']=='PASS' else 1)