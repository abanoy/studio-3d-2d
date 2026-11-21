import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent;suite=root/'output/source-production-normal-adapter-prep-20261120';out=root/'output/source-production-normal-adapter-cpu-20261120-01'
pins={'adapter':(suite/'normal_export_adapter.py',23576,'5d19134b9a4fbfd7a93777d9eb3026173d52b6380e3beb80a8211dedf9afc24e'),'tests':(suite/'test_normal_export_adapter.py',24169,'51417ecdfd5d8b79a0613853ade3f0595e3ecb610bb72fbc6023bf1ac92e2217'),'sealed_corrector':(root/'experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py',17632,'37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08'),'sealed_vvd_reader':(root/'experiments/native_normal_carrier_strategy_20261117/vvd_normals.py',4184,'f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb')}
def snap():
    rows={}
    for label,(p,size,digest) in pins.items():
        b=p.read_bytes();s=p.stat();assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,label
        rows[label]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap();out.mkdir(exist_ok=False);(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf8')
start=time.monotonic();r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','-v','test_normal_export_adapter'],cwd=suite,capture_output=True);elapsed=time.monotonic()-start
(out/'stdout.log').write_bytes(r.stdout);(out/'stderr.log').write_bytes(r.stderr)
after=snap();(out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf8');m=re.search(rb'Ran (\d+) tests',r.stderr)
result={'format':'has_production_normal_adapter_cpu_root_1','status':'PASS' if r.returncode==0 and before==after and m and int(m.group(1))==20 else 'FAIL','tests':int(m.group(1)) if m else None,'returncode':r.returncode,'elapsed_seconds':elapsed,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'application_adoption_qualified':False}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf8');print(r.stderr.decode('utf8',errors='replace'));print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)