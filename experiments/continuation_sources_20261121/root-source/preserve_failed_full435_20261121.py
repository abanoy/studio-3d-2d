"""Retain compact failed Full evidence without copying native art or reports."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT.parent/'has-ui-camera-full-20261121-435dc02/output/windows-reference-body-1795253708684469500'
FRESH=RUN.parent.parent
DEST=ROOT/'output/source-full435-failed-prep-20261121'
assert not DEST.exists();DEST.mkdir()
def sha(raw):return hashlib.sha256(raw).hexdigest()
completion=json.loads((RUN/'completion.json').read_bytes())
assert completion['revision']=='435dc02426a7cdd313e43fe674c9008520845428'
assert completion['exit']==1 and completion['whole_verifier_pass'] is False and completion['fresh_final_report'] is False
assert completion['child_reaped'] and completion['all_private_jobs_isolated_closed'] and completion['receipt_provenance_verified']
assert completion['functional_source_count']==1102 and completion['functional_sources_unchanged'] and completion['revision_unchanged']
assert completion['unique_current_private_jobs']==113 and completion['result_groups']==0
before=(RUN/'source-before.json').read_bytes();after=(RUN/'source-after.json').read_bytes();assert before==after
source=json.loads(before);expected=json.loads((ROOT/'output/UI_CAMERA_FINAL_SOURCE_20261121.json').read_bytes())['files']
assert len(source)==len(expected)==1102
for row in expected:assert all(source[row['path']][k]==row[k] for k in ('bytes','sha256','git_sha1'))
stdout=(RUN/'stdout.log').read_bytes();stderr=(RUN/'stderr.log').read_bytes()
assert stdout.count(b'PASS editor geometry37, face36/lifecycle6, handles38 visible/clipped arcs (111 new checks)')==1
assert stdout.count(b'PASS camera wire29/key26/lens12 controls and eight style-scale-workspace timeline34/lens22 variants (515 checks)')==1
assert b'FAIL default body physics starts only after accepting the fitted import, without recording keys' in stderr
assert b'HEIGHT_IMPORT_NATIVE {"checks":9,"failures":1}' in stderr
nonzero=completion['nonzero_private_jobs']
assert len(nonzero)==2 and sorted(r['value']['exit'] for r in nonzero)==[1,2]
assert sum(r['value'].get('error')=='Owned converter cancelled' and r['value'].get('cancelled') is True for r in nonzero)==1
for name in ('completion.json','source-before.json','source-after.json','committed-source-blobs.json','launch.json','stdout.log','stderr.log'):
    (DEST/name).write_bytes((RUN/name).read_bytes())
receipts=[]
for index,row in enumerate(completion['current_jobs']):
    path=FRESH/row['path'];raw=path.read_bytes()
    assert sha(raw)==row['sha256'] and json.loads(raw)==row['value']
    name=f'current-receipts/{index:03d}.json';target=DEST/name;target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
    receipts.append({'path':name,'original_relative':row['path'],'bytes':len(raw),'sha256':sha(raw),'desktop':row['value']['desktop']})
summary={'format':'has_full435_failure_root_closure_1','status':'FAIL','root_exec_session':87359,'root_process_exit':1,'root_process_reaped':True,
 'revision':completion['revision'],'seconds':completion['seconds'],'functional_sources':1102,'source_and_head_preserved':True,
 'fresh_final_report':False,'aggregate_groups_claimed':0,'all182_pass_claimed':False,'new_editor_checks_passed':111,
 'new_camera_checks_passed':515,'current_private_jobs':113,'all_private_jobs_isolated_closed':True,
 'expected_cancel_jobs':1,'unexpected_exit1_jobs':1,'failed_native_height_assertions':1,'native_height_assertions_executed':9,
 'failure':'Old native-height test expected automatic Physics On; owner-requested import policy is Off.',
 'followup':'Strengthen default-Off and explicit opt-in checks; audit first-movie/scenarioD, qualify scoped routes, then fresh committed Full.',
 'receipt_provenance_verified':True,'provenance_full_sha256':sha((RUN/'receipt-provenance.json').read_bytes()),
 'physical_human_acceptance_claimed':False,'private_geometry_or_art_copied':False,'raw_receipts':receipts}
(DEST/'ROOT_CLOSURE.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
rows=[]
for path in sorted(DEST.rglob('*')):
    if path.is_file():
        raw=path.read_bytes();rows.append({'path':path.relative_to(DEST).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
(DEST/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_failed_full435_evidence_pins_1','files':rows,'file_count':len(rows),'bytes':sum(r['bytes'] for r in rows)},indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='raw_receipts'},indent=2))
