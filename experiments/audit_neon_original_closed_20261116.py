"""Audit the failed exact Neon run and derive its fresh physical receipt set."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
RUN=REVIEW/'output/windows-neon-c2d52ff-20261117T000859'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((RUN/'state.json').read_bytes())
assert state['status']=='failed' and state['suite_exit']==1 and state['source_unchanged'] is True
assert (RUN/'source-before.json').read_bytes()==(RUN/'source-after.json').read_bytes()
sources=json.loads((RUN/'source-after.json').read_bytes())
assert sources['commit']=='c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2'
assert all(sha(REVIEW/n)==v for n,v in sources['source_sha256'].items())
start=datetime.datetime.fromisoformat(state['started_utc'].replace('Z','+00:00')).timestamp()
rows=[]
for path in sorted((REVIEW/'output').rglob('*.json')):
    if path.stat().st_mtime<start or path.stat().st_size>2_000_000:continue
    try:value=json.loads(path.read_bytes())
    except (ValueError,UnicodeError):continue
    if not isinstance(value,dict) or value.get('format')!='studio_private_desktop_1':continue
    assert value['job_closed'] is True and value['desktop_closed'] is True
    assert value['child_desktop_confirmed'] is True and value['foreground_child_observed'] is False and value['desktop_switch_requested'] is False
    rows.append({'path':path.relative_to(REVIEW).as_posix(),'sha256':sha(path),'receipt':value})
physical={}
for row in rows:
    v=row['receipt'];key=v['desktop']
    if key in physical:assert physical[key]['receipt']==v
    else:physical[key]=row
assert len(physical)>20
failed=[r for r in physical.values() if r['receipt']['exit']!=0]
assert len(failed)==2
assert any(r['receipt']['exit']==1 and 'object_timing_smoke_' in r['path'] for r in failed)
assert any(r['receipt']['exit']==2 for r in failed)
record={'format':'has_neon_original_partial_receipt_audit_1','suite_status':'FAILED_OBJECT_TIMING_28_CHECKS_2_FAILURES','functional_sources':len(sources['source_sha256']),'source_unchanged':True,'physical_jobs':len(physical),'physical_exit0':sum(r['receipt']['exit']==0 for r in physical.values()),'failed_product_job_exit1':1,'Krita_cancel_exit2_pending_exact_phase_join':1,'all_jobs_and_desktops_closed':True,'receipts':list(physical.values()),'failed_full_not_pass':True,'graphics_lease_release_requires_fresh_host_inventory':True}
target=RUN/'partial-receipt-inventory.json'
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k!='receipts'}))
