import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-empty-material-extension-prep-20261120'
out=root/'output/source-empty-material-extension-cpu-20261120-01'
local={'export_hook_proposal.py': (48895, 'cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511'), 'resource_gate_proposal.py': (54511, 'f892ade8fc83d198261edd2fbcdd608ef0cb77ba41a3f1cf52b7705de4fdfea7'), 'shared_image_cache_proposal.py': (27573, '5f54d0d1979a97e7174a967802b8de68bf48fe75d8af4c9c50a4ea90a9e624ba'), 'test_export_hook_proposal.py': (35090, 'a48a6bee400407cffefa2780ddbef6957bcd2e13acdfbdbb67fb454c3f3e8121'), 'test_shared_image_cache_proposal.py': (31707, 'e37227e8fade10040ec36c6f51d9edbdb6d52e977ead32a60f35a837caf21264'), 'test_negative_texture_probes.py': (13049, '873967eea449cc1b1d3081cf1577bc3e716397fec07dc05fd254989789a87624'), 'test_material_guard_diagnostic.py': (12829, 'd4855e775f1353415701b5f7ce2dd15224917b7c26060949c8550c64269597c6'), 'test_empty_material_extensions.py': (11218, '111e19c6ff5db6ffd36c9f379640af20b964371c08825f3dc8e306fd26538b18'), 'test_final_material_extensions.py': (10219, '8ded42747c9f48957cffca71cf318a5993a2f08b6390e80646c831f79843c7d6')}
pins={'prep/'+name:(suite/name,*spec) for name,spec in local.items()}
lockpath=root/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
lockraw=lockpath.read_bytes(); locksha=hashlib.sha256(lockraw).hexdigest(); assert locksha=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'; lock=json.loads(lockraw)
sdk=pathlib.Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
exporter=pathlib.Path(lock['exporter_root'])
for rel in ('blender/exp/material/texture_info.py','blender/exp/cache.py','io/exp/binary_data.py','io/com/gltf2_io_extensions.py'):
    row=lock['exporter_noncache_sources'][rel]; pins['approved_exporter/'+rel]=(exporter/rel,row['bytes'],row['sha256'])
pins['approved_lock']=(lockpath,len(lockraw),locksha)
def snap():
    rows={}
    for label,(p,size,digest) in pins.items():
        b=p.read_bytes(); s=p.stat(); assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,label
        rows[label]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap(); out.mkdir(exist_ok=False)
(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf-8')
results=[]
for label,pattern,count in [('hook','test_export_hook_proposal.py',38),('shared','test_shared_image_cache_proposal.py',35),('negative','test_negative_texture_probes.py',16),('material','test_material_guard_diagnostic.py',12),('empty','test_empty_material_extensions.py',12),('final','test_final_material_extensions.py',14)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr); passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(label,r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_empty_material_extension_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':127}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)
