import ast,hashlib,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-export-hook-compiler-context-v2-prep-20261120'
out=root/'output/source-export-hook-context-cpu-20261120-01'
lockpath=root/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
lockraw=lockpath.read_bytes(); assert hashlib.sha256(lockraw).hexdigest()=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
lock=json.loads(lockraw)
pins={suite/k:(v['bytes'],v['sha256']) for k,v in json.loads((suite/'BASES.json').read_text())['unchanged'].items()}
pins.update({suite/'export_hook_proposal.py':(40078,'a014dab02265b6ccb7f354c8f96eb8a212f569bfe0386ae99820fd6368e7102b'),suite/'test_export_hook_compiler_context.py':(9738,'9f0b22bfc66b023bdc2aeba27ad73b241a16aca2be5cf5a8159d1d170636f244')})
old=root/'output/source-shared-image-resource-prep-20261120'
for p,(size,digest) in pins.copy().items():
    if p.name in ('export_hook_proposal.py','test_export_hook_compiler_context.py') and p.parent==suite: continue
    source=(root/'output/source-material-carrier-host-v3-prep-20261120'/p.name) if p.name in ('observer_instrumentation.py','gather_binding.py') else old/p.name
    assert source.stat().st_size==size and hashlib.sha256(source.read_bytes()).hexdigest()==digest,p.name
sdk=pathlib.Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
rel='blender_bindings/models/mdl49/import_mdl.py'; row=lock['sourceio_files'][rel]; pins[sdk/rel]=(row['bytes'],row['sha256'])
exporter=pathlib.Path(lock['exporter_root'])
for rel in ('blender/exp/primitive_extract.py','blender/exp/cache.py','io/exp/binary_data.py'):
    row=lock['exporter_noncache_sources'][rel]; pins[exporter/rel]=(row['bytes'],row['sha256'])
pins[lockpath]=(len(lockraw),hashlib.sha256(lockraw).hexdigest())
def snap():
    rows={}
    for p,(size,digest) in pins.items():
        b=p.read_bytes(); s=p.stat(); assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,str(p)
        label=p.relative_to(root).as_posix() if p.is_relative_to(root) else 'approved_exporter/'+p.relative_to(exporter).as_posix()
        rows[label]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap(); out.mkdir(exist_ok=False)
(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf-8')
results=[]
for label,pattern,count in [('hook','test_export_hook_proposal.py',38),('shared','test_shared_image_cache_proposal.py',35),('context','test_export_hook_compiler_context.py',11)]:
    start=time.monotonic(); r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p',pattern],cwd=root,capture_output=True); elapsed=time.monotonic()-start
    (out/(label+'-stdout.log')).write_bytes(r.stdout); (out/(label+'-stderr.log')).write_bytes(r.stderr)
    match=re.search(rb'Ran (\d+) tests',r.stderr); passed=r.returncode==0 and match is not None and int(match.group(1))==count
    results.append({'scope':label,'status':'PASS' if passed else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'elapsed_seconds':elapsed})
    print(label,r.stderr.decode('utf-8',errors='replace'))
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_source_export_hook_compiler_context_cpu_root_1','status':'PASS' if all(r['status']=='PASS' for r in results) and before==after else 'FAIL','scopes':results,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'tests_expected':84}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)