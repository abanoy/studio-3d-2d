import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-shared-image-extension-lifecycle-prep-20261120'
out=root/'output/source-shared-image-extension-lifecycle-cpu-20261120-01'
local={'export_hook_proposal.py': (48895, 'cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511'), 'resource_gate_proposal.py': (55481, '4ce714dc84712384d089fc2d0b5b5a93c25c1f3dfe90f53ccee76477a3d1cee8'), 'shared_image_cache_proposal.py': (36158, 'b4aed0a276e5a469274e961e11bddff6183e6d56d4ff91af9e339af4712617e6'), 'test_export_hook_proposal.py': (35090, 'a48a6bee400407cffefa2780ddbef6957bcd2e13acdfbdbb67fb454c3f3e8121'), 'test_shared_image_cache_proposal.py': (31707, 'e37227e8fade10040ec36c6f51d9edbdb6d52e977ead32a60f35a837caf21264'), 'test_negative_texture_probes.py': (13049, '873967eea449cc1b1d3081cf1577bc3e716397fec07dc05fd254989789a87624'), 'test_material_guard_diagnostic.py': (12829, 'd4855e775f1353415701b5f7ce2dd15224917b7c26060949c8550c64269597c6'), 'test_empty_material_extensions.py': (11218, '111e19c6ff5db6ffd36c9f379640af20b964371c08825f3dc8e306fd26538b18'), 'test_final_material_extensions.py': (10219, '8ded42747c9f48957cffca71cf318a5993a2f08b6390e80646c831f79843c7d6'), 'test_make_image_return_diagnostic.py': (9571, 'af32d2b30dce34a77fd69e88c4178e3bf2a0baa6c2ec0ac0f9fdcd7933c222e6')}
local.update({'test_image_extension_lifecycle.py':(9418,'34513a8b13714e440e156749501978e112367f3ca65d2edce55e5d33be7a71ce'),'test_final_image_extensions.py':(8915,'62e834e9322c46bf742896913f1944ec3c14aadf554cc818cd3f9b5ad34ffe43')})
pins={'prep/'+name:(suite/name,*spec) for name,spec in local.items()}
lockpath=root/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
lockraw=lockpath.read_bytes(); locksha=hashlib.sha256(lockraw).hexdigest(); assert locksha=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'; lock=json.loads(lockraw)
sdk=pathlib.Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
exporter=pathlib.Path(lock['exporter_root'])
for rel in ('blender/exp/material/texture_info.py','blender/exp/cache.py','io/exp/binary_data.py','io/com/gltf2_io_extensions.py','io/exp/user_extensions.py'):
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
for label,pattern,count in [('hook','test_export_hook_proposal.py',38),('shared','test_shared_image_cache_proposal.py',35),('negative','test_negative_texture_probes.py',16),('material','test_material_guard_diagnostic.py',12),('empty','test_empty_material_extensions.py',12),('final','test_final_material_extensions.py',14),('make_diagnostic','test_make_image_return_diagnostic.py',9),('image_lifecycle','test_image_extension_lifecycle.py',10),('final_image_extensions','test_final_image_extensions.py',13)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr); passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(label,r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_image_extension_lifecycle_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':159}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)
