"""Read-only archive verification, never product execution or process inspection."""
from pathlib import Path
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name):return json.loads((HERE/name).read_bytes())
def main():
    index=load('INDEX.json');expected={r['path'] for r in index['files']}
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json' and '__pycache__' not in p.parts}
    assert expected==actual and len(expected)==index['file_count'];checks=1
    for row in index['files']:
        p=Path(row['path']);assert not p.is_absolute() and '..' not in p.parts
        assert p.suffix in ('.json','.log','.gd','.py','.md','.gz') and p.name!='expected.json'
        raw=(HERE/p).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];checks+=1
    assert sum(r['bytes'] for r in index['files'])==index['total_bytes'];checks+=1
    for row in load('SOURCE_MANIFEST.json')['copies']:
        raw=(HERE/row['stored']).read_bytes()
        if row['encoding']=='gzip_mtime0':raw=gzip.decompress(raw)
        else:assert row['encoding']=='identity'
        assert len(raw)==row['raw_bytes'] and sha(raw)==row['raw_sha256'];checks+=1
    state=load('state/result.json');sv=load('state/verification.json')
    assert state['checks']==len(state['named_checks'])==266 and state['failures']==0 and all(state['named_checks'].values())
    assert sv['passed'] and sv['runtime_lease_released'] and sv['test_result_sha256']==sha((HERE/'state/result.json').read_bytes());checks+=1
    gv=load('GUI/verification.json');assert gv['passed'] and gv['checks_observed']==102
    for i,(name,count) in enumerate([('writer',83),('reader-packed',11),('reader-linked',8)]):
        r=load('GUI/'+name+'/result.json');p=load('GUI/'+name+'/process-verification.json');receipt=load('GUI/'+name+'/private-receipt.json')
        assert r['checks']==len(r['named_checks'])==count and r['failures']==0 and all(r['named_checks'].values())
        assert p==gv['results'][i] and p['passed'] and p['exit']==0 and p['retained_Popen_reaped'] and not p['timed_out']
        assert receipt['exit']==0 and receipt['job_closed'] and receipt['desktop_closed'] and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'];checks+=1
    host=load('host/verification.json');assert host['passed'] and host['runtime_lease_released'] and host['checks_observed']==102
    assert host['verification_sha256']==sha((HERE/'GUI/verification.json').read_bytes())
    assert host['state266_predecessor_sha256']==sha((HERE/'state/verification.json').read_bytes());checks+=1
    b=load('BENCHMARK.json');assert b['execution_context']=='ISOLATED_STAGE3_PRE_PROMOTION'
    assert not b['main_promotion_performed_by_packet'] and not b['scope']['full_current_default_pass']
    assert b['formal_acceptance']=='55/62_UNCHANGED' and b['implementation']=='52/54_UNCHANGED';checks+=1
    print(json.dumps({'archive_audit_passed':True,'checks':checks,'files':len(expected),'product_tests_run':0,'index_sha256':sha((HERE/'INDEX.json').read_bytes())}))

if __name__=='__main__':main()
