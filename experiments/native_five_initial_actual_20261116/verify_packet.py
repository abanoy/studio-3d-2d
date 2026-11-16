"""Read-only archive audit; never runs frozen source, engines, processes or Git."""
from pathlib import Path
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name):return json.loads((HERE/name).read_bytes())
def main():
    index=load('INDEX.json')
    expected={r['path'] for r in index['files']}
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json' and '__pycache__' not in p.parts}
    assert expected==actual and len(expected)==index['file_count']
    checks=0
    for row in index['files']:
        path=Path(row['path']);assert not path.is_absolute() and '..' not in path.parts
        raw=(HERE/path).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];checks+=1
    manifest=load('SOURCE_MANIFEST.json')
    for row in manifest['copies']:
        raw=(HERE/row['stored']).read_bytes()
        if row['encoding']=='gzip_mtime0':raw=gzip.decompress(raw)
        else:assert row['encoding']=='identity'
        assert len(raw)==row['raw_bytes'] and sha(raw)==row['raw_sha256'];checks+=1
    bench=load('BENCHMARK.json')
    for name in ['initial-state','strict-state']:
        result=load(name+'/result.json');v=load(name+'/verification.json')
        assert result['checks']==len(result['named_checks'])==266 and result['failures']==0
        assert all(result['named_checks'].values()) and v['passed'] and v['runtime_lease_released'];checks+=1
    gui=load('failed-GUI/writer/result.json')
    assert gui['checks']==82 and gui['failures']==1 and not gui['named_checks']['fan.opposite_tip_directions'];checks+=1
    diag=load('strict-diagnostic/result.json');v=load('strict-diagnostic/verification.json')
    assert diag['checks']==57 and diag['failures']==2 and v['diagnostic_completed'] and not v['qualification_pass_claimed'];checks+=1
    assert not bench['strict_diagnostic']['qualification_pass'] and bench['production_backend']=='NATIVE8_ONLY_NOT_PROMOTED'
    assert bench['formal_acceptance']=='55/62_UNCHANGED' and bench['implementation']=='52/54_UNCHANGED';checks+=1
    print(json.dumps({'archive_audit_passed':True,'checks':checks,'files':len(expected),'copies':len(manifest['copies']),'product_tests_run':0,'index_sha256':sha((HERE/'INDEX.json').read_bytes())}))

if __name__=='__main__':main()
