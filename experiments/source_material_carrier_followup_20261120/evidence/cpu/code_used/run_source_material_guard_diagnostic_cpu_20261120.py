import hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-material-guard-diagnostic-prep-20261120'
out=root/'output/source-material-guard-diagnostic-cpu-20261120-01'
local={'export_hook_proposal.py': (43512, '636a8d92d29b7c6a7118535cdea0e0ea3ba8a17f12ec30c680280755c6ba4f59'), 'resource_gate_proposal.py': (50146, '6d6fdd70f73693aff2b1ce0163f153eefcd3e196a0a6ab6e88c4593a5d2a12fd'), 'shared_image_cache_proposal.py': (27573, '5f54d0d1979a97e7174a967802b8de68bf48fe75d8af4c9c50a4ea90a9e624ba'), 'test_export_hook_proposal.py': (35090, 'a48a6bee400407cffefa2780ddbef6957bcd2e13acdfbdbb67fb454c3f3e8121'), 'test_shared_image_cache_proposal.py': (31707, 'e37227e8fade10040ec36c6f51d9edbdb6d52e977ead32a60f35a837caf21264'), 'test_negative_texture_probes.py': (13049, '873967eea449cc1b1d3081cf1577bc3e716397fec07dc05fd254989789a87624'), 'test_material_guard_diagnostic.py': (12829, 'd4855e775f1353415701b5f7ce2dd15224917b7c26060949c8550c64269597c6')}
pins={'prep/'+name:(suite/name,*spec) for name,spec in local.items()}
lockpath=root/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
lockraw=lockpath.read_bytes(); locksha=hashlib.sha256(lockraw).hexdigest(); assert locksha=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'; lock=json.loads(lockraw)
sdk=pathlib.Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
exporter=pathlib.Path(lock['exporter_root'])
for rel in ('blender/exp/material/texture_info.py','blender/exp/cache.py','io/exp/binary_data.py'):
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
for label,pattern,count in [('hook','test_export_hook_proposal.py',38),('shared','test_shared_image_cache_proposal.py',35),('negative','test_negative_texture_probes.py',16),('material','test_material_guard_diagnostic.py',12)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr); passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(label,r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_material_guard_diagnostic_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':101}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)
