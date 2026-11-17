"""Read-only exact-copy/projection/privacy audit; no app, process, Git or network."""
from pathlib import Path
import gzip,hashlib,json,math
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def main():
    manifest=load(HERE/'SOURCE_MANIFEST.json');checks=0;numeric_counts=0
    for row in manifest['copies']:
        stored=(HERE/row['stored']).read_bytes()
        body=gzip.decompress(stored) if row['encoding']=='gzip-json-exact' else stored
        assert len(body)==row['raw_bytes'] and sha(body)==row['raw_sha256']
        assert Path(row['source']).read_bytes()==body
        checks+=1
    for row in manifest['projections']:
        raw=load(Path(row['source']));stored=load(HERE/row['stored'])
        assert sha(Path(row['source']).read_bytes())==row['source_sha256']==stored['source_result']['sha256']
        for name in row['whitelist']:
            if name in raw:assert stored[name]==raw[name]
            else:assert name not in stored
        assert all(name not in stored for name in ('camera_before','camera_after','runtime_objects','rasters','canvas_extent','setup_extent'))
        assert not stored['failures'] and all(x['ok'] is True for x in stored['checks'])
        checks+=1
    benchmark=load(HERE/'BENCHMARK.json');v=load(HERE/'replay/verification.json');root=load(HERE/'root/verification.json')
    assert benchmark['passed'] and benchmark['checks']==sum(benchmark['checks_by_example'].values())==187 and benchmark['examples']==4
    assert len(benchmark['preservation'])==9 and all(benchmark['preservation'].values()) and benchmark['preservation']==v['preservation']==root['preservation']
    assert sha((HERE/'replay/verification.json').read_bytes())==root['verification_sha256']
    assert benchmark['relocated_native5']['completed_fixed_ticks']>=1 and benchmark['relocated_native5']['off_exact']
    context=load(HERE/'root/source-context.json');bindings=load(HERE/'CODE_BINDINGS.json')
    for key,name in bindings['root_context_names'].items():assert sha((HERE/name).read_bytes())==context[key]
    for name,row in bindings['actual_harness_bindings'].items():
        aliases=[x for x in manifest['copies'] if x['source']==name]
        if aliases:assert len(aliases)==1 and aliases[0]['raw_sha256']==row['sha256']
    checks+=5
    def scan(value,path):
        nonlocal numeric_counts
        if isinstance(value,dict):
            for key,item in value.items():scan(item,path+'.'+key)
        elif isinstance(value,list):
            if value and all(type(v) in (int,float) for v in value):
                assert path.endswith('.native5_prior_state_GUI_checks') and value==[266,102],path
                numeric_counts+=1
            for i,item in enumerate(value):scan(item,path+'['+str(i)+']')
        elif isinstance(value,float):assert math.isfinite(value),path
        elif isinstance(value,str):
            assert len(value)<65536 and not value.startswith(('data:image/','data:audio/','data:application/octet-stream')),path
    for p in HERE.rglob('*'):
        if not p.is_file():continue
        assert p.suffix.lower() not in ('.has','.glb','.gltf','.blend','.mdl','.vvd','.vtx','.png','.wav','.mp4','.vrm','.pmx','.pyc')
        if p.suffix=='.gz':body=gzip.decompress(p.read_bytes());scan(json.loads(body),'$:'+p.name)
        elif p.suffix=='.json':scan(load(p),'$:'+p.name)
        else:p.read_bytes().decode('utf-8')
    checks+=1
    index_path=HERE/'INDEX.json'
    if index_path.exists():
        index=load(index_path);actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json'}
        assert actual=={row['path'] for row in index['files']}
        for row in index['files']:
            p=HERE/row['path'];assert p.stat().st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
        checks+=1
    print(json.dumps({'passed':True,'archive_checks':checks,'exact_copies':len(manifest['copies']),'safe_result_projections':len(manifest['projections']),
        'numeric_count_lists_only':numeric_counts,'product_runtime_tests_executed':0,'source_scope':'Actual187checkreview; this invocation audits archive metadata only.',
        'index_sha256':sha(index_path.read_bytes()) if index_path.exists() else None}))
if __name__=='__main__':main()
