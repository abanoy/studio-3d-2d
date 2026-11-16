"""Archive the explicit completed promotion metadata/public sources only."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
FOLDER=ROOT/'output/native-five-promotion-applied'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
def privacy(x,path=''):
    if isinstance(x,dict):
        for k,v in x.items():privacy(v,path+'/'+k)
    elif isinstance(x,list):
        if any(isinstance(v,(int,float)) and not isinstance(v,bool) for v in x):
            assert path=='/native_rule_indices_selected' and x==[8,17,18,26,27],path
        for v in x:privacy(v,path+'/*')
def main():
    v=read(FOLDER/'verification.json');before=read(FOLDER/'source-before.json');after=read(FOLDER/'source-after.json')
    assert v['passed'] and v['functional_files_before']==len(before)==1014 and v['functional_files_after']==len(after)==1019
    assert sha((FOLDER/'source-before.json').read_bytes())==v['source_before_sha256']
    assert sha((FOLDER/'source-after.json').read_bytes())==v['source_after_sha256']
    changed=sorted(n for n in set(before)|set(after) if before.get(n)!=after.get(n))
    assert changed==v['promoted_paths'] and len(changed)==10 and v['runtime_equivalent_to_qualified_stage']
    assert v['qualified_state_checks']==266 and v['qualified_GUI_checks']==102
    assert not v['main_UI_and_full_test_rerun_claimed'] and v['fresh_full_default_required']
    review=ROOT/'experiments/source_native_five_promotion_review_20261116'
    assert sha((review/'INDEX.json').read_bytes())==v['packet_index_sha256']=='0450b2d840b2a7ba91f95b5f1b97329d2eb7deeafcadb32f2000317b382d0e9f'
    rows=read(review/'REVIEW.json')['promotion_files'];assert sorted(r['path'] for r in rows)==changed
    cpu=ROOT/'output/helper-preview-driver-domain/source-five-promotion-20261116/result.json';c=read(cpu)
    assert len(c['checks'])==120 and not c['failures'] and c['source_preservation'] and not c['subprocess_attempts'] and c['runtime_processes']==0
    ports=read(FOLDER/'current-port-validation.json');assert ports['passed'] and sum(len(x) for x in ports['ports'].values())==41
    benchmark=ROOT/'docs/benchmarks/native_five_qualified_2026-11-15.json';b=read(benchmark)
    assert b['state']['checks']==266 and b['GUI']['checks']==102 and not b['fresh_main_full_default_passed']
    assert b['CPU_driver_controls']['result']['sha256']==sha(cpu.read_bytes())
    assert b['promotion']['sha256']==sha((FOLDER/'verification.json').read_bytes())
    plan=[(p,'promotion/'+p.name+('.gz' if p.name.startswith('source-') else ''),p.name.startswith('source-')) for p in sorted(FOLDER.iterdir())]
    plan += [(cpu,'CPU/result.json',False),(benchmark,'BENCHMARK.json',False)]
    for row in rows:
        p=ROOT/row['path'];assert sha(p.read_bytes())==row['proposed_sha256']==after[row['path']]
        assert p.read_bytes()==(review/'proposed'/row['path']).read_bytes()
        plan.append((p,'source/'+row['path'],False))
    for name in ('apply_qualified_five.py','record_qualified_five.py'):
        plan.append((ROOT/'experiments/native_source_live_port_20261115'/name,'source/root/'+name,False))
    prepared=[]
    for p,name,zipped in plan:
        assert p.suffix in ('.json','.gd','.py') and p.is_file()
        raw=p.read_bytes();raw.decode('utf-8-sig')
        if p.suffix=='.json':privacy(json.loads(raw))
        assert not (HERE/name).exists();prepared.append((p,name,zipped,raw))
    aliases=[]
    for p,name,zipped,raw in prepared:
        target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(gzip.compress(raw,mtime=0) if zipped else raw)
        aliases.append({'source':p.relative_to(ROOT).as_posix(),'stored':name,'raw_bytes':len(raw),'raw_sha256':sha(raw),'encoding':'gzip_mtime0' if zipped else 'identity'})
    save('SOURCE_MANIFEST.json',{'format':'has_native_five_promotion_actual_sources_1','copies':aliases})
    entries=[]
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and p.name!='INDEX.json':
            raw=p.read_bytes();entries.append({'path':p.relative_to(HERE).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    save('INDEX.json',{'format':'has_native_five_promotion_actual_index_1','files':entries,'file_count':len(entries),'total_bytes':sum(r['bytes'] for r in entries)})
    print(json.dumps({'files':len(entries),'bytes':sum(r['bytes'] for r in entries),'copies':len(aliases),'index_sha256':sha((HERE/'INDEX.json').read_bytes())}))
if __name__=='__main__':main()
