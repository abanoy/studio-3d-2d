import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-export-hook-compiler-context-v3-prep-20261120'
out=root/'output/source-export-hook-context-cpu-20261120-02'
local={'export_hook_proposal.py':(43512,'636a8d92d29b7c6a7118535cdea0e0ea3ba8a17f12ec30c680280755c6ba4f59'),'test_export_hook_compiler_context.py':(17581,'e79fa21d465c37e7bad990c7452668f77a79aacfe958d4b5a384dd2ef12ea1e2'),'resource_gate_proposal.py':(35869,'bc4fd1ff719e43618cd0984a73fc9c950d502e52c762ac4cb6e042ff1464fba3'),'shared_image_cache_proposal.py':(23263,'e903c871d53769d7dfc92e1ecdec75f316cf34ea8e8c5113116861cafefe6c0e'),'observer_instrumentation.py':(7829,'15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b'),'gather_binding.py':(17534,'617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850'),'test_export_hook_proposal.py':(35090,'a48a6bee400407cffefa2780ddbef6957bcd2e13acdfbdbb67fb454c3f3e8121'),'test_shared_image_cache_proposal.py':(31707,'e37227e8fade10040ec36c6f51d9edbdb6d52e977ead32a60f35a837caf21264')}
pins={'prep/'+name:(suite/name,*spec) for name,spec in local.items()}
lockpath=root/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
lockraw=lockpath.read_bytes(); locksha=hashlib.sha256(lockraw).hexdigest(); assert locksha=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'; lock=json.loads(lockraw)
sdk=pathlib.Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
rel='blender_bindings/models/mdl49/import_mdl.py'; row=lock['sourceio_files'][rel]; pins['approved_sourceio/'+rel]=(sdk/rel,row['bytes'],row['sha256'])
exporter=pathlib.Path(lock['exporter_root'])
for rel in ('blender/exp/primitive_extract.py','blender/exp/cache.py','io/exp/binary_data.py'):
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
for label,pattern,count in [('hook','test_export_hook_proposal.py',38),('shared','test_shared_image_cache_proposal.py',35),('context','test_export_hook_compiler_context.py',13)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr); passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(label,r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_export_hook_compiler_context_cpu_root_2','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':86}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)