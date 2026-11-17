"""Seal runner source and preparation evidence. Does not import run_owned."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    audit=json.loads((HERE/'SOURCE_AUDIT.json').read_bytes())
    assert audit['passed'] is True and audit['checks']==38
    assert audit['driver_sha256']==sha(HERE/'run_owned.py')
    assert audit['actual_engine_execution'] is False and audit['actual_cim_inventory'] is False and audit['actual_git_call'] is False
    rows=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert path.suffix in {'.py','.md','.json'} and '__pycache__' not in path.parts
        rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    value={'format':'has_source_experiment_index_1','packet':HERE.name,'files':rows,'file_count':len(rows),
        'bytes':sum(row['bytes'] for row in rows),'excludes':['INDEX.json'],'actual_root_execution':False,
        'actual_engine_execution':False,'actual_cim_inventory':False,'actual_git_call':False,'main_edits':False}
    (HERE/'INDEX.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'driver_sha256':sha(HERE/'run_owned.py'),
        'files':len(rows),'bytes':value['bytes'],'source_checks':38}))


if __name__=='__main__':main()
