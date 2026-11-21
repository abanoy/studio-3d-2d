import hashlib,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-conditional-native-normal-v2-prep-20261120'
out=root/'output/source-corrected-normal-measurement-cpu-20261120-01'
pins={'conditional_correction.py':(17804,'1b95ed2ca925984adf1f011347290f4567926f28c15d253f14df032c5eb40dd2'),'test_corrected_measurement.py':(5558,'069a8b8a1115fd2df7632140419be62b4ca23c8fb5df9b2ba85ae351fba20bcc'),'../../experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py':(17632,'37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08'),'../../experiments/native_normal_carrier_strategy_20261117/vvd_normals.py':(4184,'f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb')}
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
r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p','test_corrected_measurement.py'],cwd=root,capture_output=True)
elapsed=time.monotonic()-start
(out/'stdout.log').write_bytes(r.stdout); (out/'stderr.log').write_bytes(r.stderr)
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_corrected_normal_measurement_cpu_root_1','status':'PASS' if r.returncode==0 and before==after else 'FAIL','returncode':r.returncode,'elapsed_seconds':elapsed,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':5}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); print(r.stderr.decode('utf-8',errors='replace'))
raise SystemExit(0 if result['status']=='PASS' else 1)