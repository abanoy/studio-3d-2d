import hashlib,importlib.util,json,pathlib,re,subprocess,sys,time
root=pathlib.Path(__file__).resolve().parent.parent
suite=root/'output/source-material-carrier-host-v6-prep-20261120'
base=root/'output/source-material-carrier-host-v5-prep-20261120'
out=root/'output/source-carrier-bounded-read-cpu-20261120-01'
pins={'baseline_driver':(base/'run_carrier.py',87417,'3b2957d228fd54eff1add759285c7c9509e918c0fa96be0bddfc7e8a698a1411'),'candidate_driver':(suite/'run_carrier.py',87426,'493a5cd1ae57cf81d7b7e649b254d1c177f85469ad8c4750851d77b26769d6b4'),'tests':(suite/'test_bounded_read.py',6889,'876c8f1948dc32e37506446884256475a0ae2381f531dcf2152ce9720f894cca'),'metadata_source':(base/'material_metadata.py',13818,'c04c4e20705b490ed7633855b2e3bdde14350adec35c8b2a25afc42b69508395'),'cold_source':(base/'cold_image_readiness.py',14496,'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9')}
def snap():
    rows={}
    for key,(p,size,digest) in pins.items():
        b=p.read_bytes(); s=p.stat(); assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,key
        rows[key]={'bytes':len(b),'sha256':digest,'mtime_ns':s.st_mtime_ns}
    return rows
before=snap(); out.mkdir(exist_ok=False)
(out/'before.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n',encoding='utf-8')
r=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(suite),'-p','test_bounded_read.py'],cwd=root,capture_output=True)
(out/'stdout.log').write_bytes(r.stdout); (out/'stderr.log').write_bytes(r.stderr)
match=re.search(rb'Ran (\d+) tests',r.stderr); tests_ok=r.returncode==0 and match and int(match.group(1))==13
bench=None
if tests_ok:
    modules={}
    for key in ('baseline_driver','candidate_driver'):
        spec=importlib.util.spec_from_file_location('_root_bounded_read_'+key,pins[key][0]); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); modules[key]=m
    rows=[]
    for turn in range(4):
        for target in ('metadata_source','cold_source'):
            p,size,digest=pins[target]
            order=('baseline_driver','candidate_driver') if turn%2==0 else ('candidate_driver','baseline_driver')
            for key in order:
                start=time.perf_counter_ns(); cpu=time.process_time_ns(); raw,identity,_stamp=modules[key].read_checked(p,(size,digest)); cpu=time.process_time_ns()-cpu; wall=time.perf_counter_ns()-start
                assert raw==p.read_bytes() and identity==before[target]
                rows.append({'reader':key,'source':target,'iteration':turn,'wall_ns':wall,'cpu_ns':cpu,'returned_bytes':len(raw),'declared_request_bytes':modules[key].MAX_READ+1 if key=='baseline_driver' else size+1})
    totals={key:{'calls':sum(row['reader']==key for row in rows),'wall_ns':sum(row['wall_ns'] for row in rows if row['reader']==key),'cpu_ns':sum(row['cpu_ns'] for row in rows if row['reader']==key),'returned_bytes':sum(row['returned_bytes'] for row in rows if row['reader']==key),'declared_request_bytes':sum(row['declared_request_bytes'] for row in rows if row['reader']==key)} for key in modules}
    bench={'format':'has_bounded_read_source_only_comparison_1','rows':rows,'totals':totals,'candidate_to_baseline_wall_ratio':totals['candidate_driver']['wall_ns']/totals['baseline_driver']['wall_ns'],'whole_native_coordinator_speedup_measured':False,'physical_memory_or_disk_saving_measured':False}
    (out/'BENCHMARK.json').write_text(json.dumps(bench,sort_keys=True,indent=2)+'\n',encoding='utf-8')
after=snap(); (out/'after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n',encoding='utf-8')
result={'format':'has_bounded_read_cpu_root_1','status':'PASS' if tests_ok and before==after else 'FAIL','tests':int(match.group(1)) if match else None,'returncode':r.returncode,'source_count':len(before),'source_hash_size_mtime_unchanged':before==after,'native_launch_attempted':False,'benchmark_completed':bench is not None,'benchmark_totals':bench['totals'] if bench else None}
(out/'ROOT_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(r.stderr.decode('utf-8',errors='replace')); print(json.dumps(result)); raise SystemExit(0 if result['status']=='PASS' else 1)