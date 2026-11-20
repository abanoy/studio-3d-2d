from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/'output/source-weight-join-20261120'
SHA='f838e0d893969aa1ad884a1c1d92e28ba019454f313632855f2a33c55fc3415c'
def identity(path):
    raw=path.read_bytes();info=path.stat()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mtime_ns=info.st_mtime_ns)
source=F/'join_saved_weights.py';test=F/'test_saved_weight_join.py'
prior={str(path):identity(path) for path in (source,test,F/'join_saved_weights_v1_17aba.py',F/'root-result-01.json')}
assert prior[str(source)]['sha256']==SHA
assert prior[str(F/'join_saved_weights_v1_17aba.py')]['sha256']=='17aba1957b5670f1ff6f1fdef20235e30afdc880a1035dc82f668bb0edf77cad'
commands=[[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(F),'-p','test_saved_weight_join.py','-v'],
          [sys.executable,'-B','-X','utf8',str(source),'--script-sha256',SHA,'--report',str(F/'root-result-02.json')]]
assert not (F/'root-result-02.json').exists()
results=[]
for index,command in enumerate(commands):
    began=time.perf_counter()
    p=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
    raw=p.stdout+p.stderr;(F/('root-command-'+str(index)+'.log')).write_bytes(raw)
    results.append(dict(args=command,exit=p.returncode,seconds=time.perf_counter()-began,log_sha256=hashlib.sha256(raw).hexdigest()))
    print(raw.decode('utf8',errors='replace'),flush=True)
    assert p.returncode==0
    if index==0:assert b'Ran 19 tests' in raw and b'\nOK' in raw
report=json.loads((F/'root-result-02.json').read_bytes())
assert report['status']=='MATCHED_PINNED_SAVED_B_WEIGHT_POINT_JOIN'
assert report['all_read_inputs_hash_size_stamp_unchanged'] and report['native_points']==9661
assert report['models']==json.loads((F/'root-result-01.json').read_bytes())['models']
assert all(identity(Path(path))==value for path,value in prior.items())
result=dict(format='has_source_saved_weight_root_qualification_1',passed=True,scope='Historical exact indexed numeric relation only',
            synthetic_methods=19,identities_unchanged=prior,commands=results,
            private_arrays_published=False,new_native_process_launched=False,
            actual_join_report_sha256=identity(F/'root-result-02.json')['sha256'],
            native_normal_fidelity_still_unqualified=True,current_exporter_or_Blender_state_qualified=False)
(F/'ROOT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items() if key not in ('identities_unchanged','commands')},indent=2))
