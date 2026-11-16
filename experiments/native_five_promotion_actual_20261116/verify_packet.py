"""Read-only receipt/hash audit; zero product, process, Git or network work."""
from pathlib import Path
import gzip,hashlib,json
HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(name):return json.loads((HERE/name).read_bytes())
def main():
    idx=read('INDEX.json');names={r['path'] for r in idx['files']}
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json' and '__pycache__' not in p.parts}
    assert names==actual and len(names)==idx['file_count'];checks=1
    for r in idx['files']:
        p=Path(r['path']);assert not p.is_absolute() and '..' not in p.parts and p.suffix in ('.json','.gd','.py','.md','.gz')
        raw=(HERE/p).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'];checks+=1
    assert sum(r['bytes'] for r in idx['files'])==idx['total_bytes'];checks+=1
    for r in read('SOURCE_MANIFEST.json')['copies']:
        raw=(HERE/r['stored']).read_bytes()
        if r['encoding']=='gzip_mtime0':raw=gzip.decompress(raw)
        else:assert r['encoding']=='identity'
        assert len(raw)==r['raw_bytes'] and sha(raw)==r['raw_sha256'];checks+=1
    v=read('promotion/verification.json');assert v['passed'] and len(v['promoted_paths'])==10
    assert v['source_before_sha256']==sha(gzip.decompress((HERE/'promotion/source-before.json.gz').read_bytes()))
    assert v['source_after_sha256']==sha(gzip.decompress((HERE/'promotion/source-after.json.gz').read_bytes()));checks+=1
    cpu=read('CPU/result.json');assert len(cpu['checks'])==120 and not cpu['failures'] and not cpu['subprocess_attempts'];checks+=1
    ports=read('promotion/current-port-validation.json');assert ports['passed'] and sum(len(x) for x in ports['ports'].values())==41;checks+=1
    b=read('BENCHMARK.json');assert b['GUI']['checks']==102 and b['state']['checks']==266 and not b['fresh_main_full_default_passed'];checks+=1
    print(json.dumps({'archive_audit_passed':True,'checks':checks,'files':len(names),'product_tests_run':0,'index_sha256':sha((HERE/'INDEX.json').read_bytes())}))
if __name__=='__main__':main()
