"""Source-only append plan for the completed standalone32 scope; never reads the active full."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-world-transaction-lifecycle32-20261117-attempt1'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    value=json.loads((FOLDER/'verification.json').read_bytes());report=json.loads((FOLDER/'report.json').read_bytes())
    assert value['passed'] is True and value['source_unchanged'] is True and value['functional_source_files']==1029 and value['full_suite_pass_claimed'] is False
    assert len(value['processes'])==2 and all(row['exit']==0 and row['retained_Popen_reaped'] is True and row['timed_out'] is False for row in value['processes'])
    assert report['checks']==32 and report['failures']==0 and report['cases'][-1]=='withheld-control-transaction'
    assert (FOLDER/'source-before.json').read_bytes()==(FOLDER/'source-after.json').read_bytes()
    rows={}
    def add(path,label):
        path=path.resolve();root='main' if path.is_relative_to(MAIN) else 'review';base=MAIN if root=='main' else REVIEW
        assert path.is_relative_to(base) and path.is_file() and path.suffix in ('.json','.log','.py','.gd','.md')
        raw=path.read_bytes();assert len(raw)<1024*1024;raw.decode('utf-8')
        rows[str(path)]={'root':root,'path':path.relative_to(base).as_posix(),'bytes':len(raw),'sha256':sha(raw),'gzip_exact_original':len(raw)>32768,'labels':[label]}
    for path in FOLDER.iterdir():
        if path.is_file() and path.suffix in ('.json','.log'):add(path,'completed_ROOT_standalone32')
    command=json.loads((FOLDER/'app-command.json').read_bytes());global_receipt=Path(command[command.index('--receipt')+1]);add(global_receipt,'actual_original_physical_receipt')
    for path in FOLDER.glob('*closure.json'):
        closed=json.loads(path.read_bytes());assert closed['owned_count']==0 and closed['matcher_positive_cases']==4 and closed['matcher_negative_cases']==3 and closed['termination_issued'] is False
    source=MAIN/'experiments/neon_world_rail_transaction_32_20261117'
    assert sha((source/'INDEX.json').read_bytes())=='1b227ba7e85afb8d7b4caa0dd558cdd217f6c1ce30fd53915defd1fc4987b925'
    for path in source.iterdir():
        if path.is_file() and path.suffix in ('.json','.py','.gd','.md'):add(path,'sealed_standalone32_source')
    receipts=[json.loads((Path({'main':MAIN,'review':REVIEW}[row['root']])/row['path']).read_bytes()) for row in rows.values() if row['path'].endswith('private-receipt.json') or row['path']==global_receipt.relative_to(REVIEW).as_posix()]
    assert len(receipts)==2 and receipts[0]==receipts[1] and receipts[0]['exit']==0
    plan={'format':'has_neon_lifecycle32_append_inputs_1','roots':{'main':str(MAIN),'review':str(REVIEW)},'files':list(rows.values()),'physical_receipt_files':2,'unique_physical_jobs':1,
          'scope':'standalone32 actual only, separate from formal12504 and future complete canonical','prior_sequence_recipe_index_sha256':'eda61664e18d73d630820d44a3d7a63cb9d5e9710772f5516fc4e4e06d74621b','verification':value,'report':report,'active_full_state_or_report_read':False,'engines_CIM_Git_executed':False}
    (HERE/'INPUTS.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'selected_inputs':len(rows),'raw_bytes':sum(row['bytes'] for row in rows.values()),'physical_jobs':1}))


if __name__=='__main__':main()
