"""Seal source and exact sentinel aliases; never execute driver/process helpers."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PACKET=ROOT/'experiments/normal_setter_boundary_sentinel_20261117'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    assert sha(PACKET/'INDEX.json')=='2dc8f54ef0592cf92dbef26898da00aa2e2f5d4a6802a59e7efbf7c0f2514443'
    packet=json.loads((PACKET/'INDEX.json').read_bytes())
    rows=packet['files'];entries=rows.items() if isinstance(rows,dict) else ((row['path'],row) for row in rows)
    aliases={}
    for name,row in entries:
        assert sha(PACKET/name)==row['sha256'] and (PACKET/name).stat().st_size==row['bytes']
        aliases[name]=row['sha256']
    audit=json.loads((HERE/'SOURCE_AUDIT.json').read_bytes())
    assert audit['passed'] is True and audit['checks']==32 and audit['driver_sha256']==sha(HERE/'run_owned.py')
    assert audit['driver_imported_or_executed'] is False and audit['engine_or_CIM_or_Git_executed'] is False
    context={'format':'has_setter_root_driver_source_aliases_1','setter_packet':PACKET.relative_to(ROOT).as_posix(),
        'setter_packet_index_sha256':sha(PACKET/'INDEX.json'),'setter_payloads':aliases,
        'driver_sha256':sha(HERE/'run_owned.py'),'stage':'output/normal-setter-boundary-20261116-attempt1',
        'actual_staging_or_runtime_claimed':False,'lease_sha_and_exact_metadata_head_required_after_root_staging':True}
    (HERE/'SOURCE_BINDINGS.json').write_text(json.dumps(context,indent=2)+'\n',encoding='utf-8')
    files=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert path.suffix in {'.py','.json','.md'} and '__pycache__' not in path.parts,path
        files.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':files,'file_count':len(files),
        'bytes':sum(row['bytes'] for row in files),'excludes':['INDEX.json'],'driver_executed':False,
        'engine_CIM_or_Git_executed':False,'native_arrays_or_private_reports_included':False}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'driver_sha256':sha(HERE/'run_owned.py'),
        'source_checks':32,'files':len(files),'bytes':index['bytes'],'driver_executed':False}))


if __name__=='__main__':main()
