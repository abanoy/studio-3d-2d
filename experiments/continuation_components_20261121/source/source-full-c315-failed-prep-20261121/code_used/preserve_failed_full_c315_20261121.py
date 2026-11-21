"""Preserve the failed c315 aggregate and closed-job evidence, without native art."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
FRESH=ROOT.parent/'has-import-off-full-20261121-c31576d'
RUN=FRESH/'output/windows-reference-body-1795260488673286600'
OUTER=FRESH/'output/root-full-launch-1795260488526602700'
DEST=ROOT/'output/source-full-c315-failed-prep-20261121'
assert not DEST.exists()
def sha(raw):return hashlib.sha256(raw).hexdigest()
c=json.loads((RUN/'completion.json').read_bytes());outer=json.loads((OUTER/'completion.json').read_bytes())
assert c['revision']=='c31576d0c1d84030d51ec886f2f3976a60a70c7b' and c['exit']==1 and c['whole_verifier_pass'] is False
assert c['functional_source_count']==1103 and c['functional_sources_unchanged'] and c['revision_unchanged']
assert c['child_reaped'] and c['all_private_jobs_isolated_closed'] and c['receipt_provenance_verified']
assert c['unique_current_private_jobs']==167 and c['result_groups']==0 and not c['fresh_final_report']
assert outer['exit']==1 and all(outer[k] is True for k in ('child_reaped','parent_environment_unchanged','coordinator_source_unchanged','revision_unchanged'))
before=(RUN/'source-before.json').read_bytes();assert before==(RUN/'source-after.json').read_bytes()
source=json.loads(before);expected=json.loads((ROOT/'output/IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json').read_bytes())
assert len(source)==len(expected)==1103 and set(source)==set(expected)
assert all(all(source[name][k]==row[k] for k in ('bytes','sha256','git_sha1')) for name,row in expected.items())
stdout=(RUN/'stdout.log').read_bytes();stderr=(RUN/'stderr.log').read_bytes()
assert stdout.count(b'(111 new checks)')==1 and stdout.count(b'(515 checks)')==1 and b'PASS optional height review' in stdout
assert stderr.count(b'FAIL unreachable rotation drag keeps last valid native preview:')==4
assert stderr.count(b'CONTACT_TRANSFORM {"checks":129,"failures":4,')==1
nonzero=c['nonzero_private_jobs'];assert len(nonzero)==2 and sorted(r['value']['exit'] for r in nonzero)==[1,2]
assert sum(r['value'].get('error')=='Owned converter cancelled' and r['value'].get('cancelled') is True for r in nonzero)==1
DEST.mkdir()
def copy(path,name):
 raw=path.read_bytes();raw.decode('utf-8-sig');target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);assert target.read_bytes()==raw
for name in ('completion.json','source-before.json','source-after.json','committed-source-blobs.json','launch.json','stdout.log','stderr.log'):
 copy(RUN/name,name)
for name in ('launch.json','completion.json','coordinator-stdout.log','coordinator-stderr.log'):copy(OUTER/name,'outer/'+name)
rows=[]
for index,row in enumerate(c['current_jobs']):
 path=FRESH/row['path'];raw=path.read_bytes();assert sha(raw)==row['sha256'] and json.loads(raw)==row['value']
 name=f'current-receipts/{index:03d}.json';copy(path,name)
 rows.append({'path':name,'original_relative':row['path'],'sha256':sha(raw),'bytes':len(raw),'desktop':row['value']['desktop']})
summary={'format':'has_failed_c315_full_root_closure_1','status':'FAIL','revision':c['revision'],'seconds':c['seconds'],
 'root_exec_session':1322,'root_exit':1,'root_exec_reaped':True,'coordinator_pid':22996,'verifier_pid':23816,
 'source_count':1103,'source_and_head_preserved':True,'outer_source_and_environment_preserved':True,
 'current_private_jobs':167,'all_private_jobs_isolated_closed':True,'new_editor_camera_checks_passed':626,
 'height_followup_passed':True,'fresh_final_report':False,'aggregate_groups_claimed':0,
 'failure':'Four of129 contact-transform assertions fail at the unreachable rotation-drag last-valid-preview check.',
 'diagnosis':'The test still maps degrees using a fixed .02 pixel sensitivity; production rings now use projected ray/plane angles. Runtime correction is not yet qualified.',
 'contact_checks_executed':129,'contact_failures':4,'expected_cancellation_jobs':1,'unexpected_exit1_jobs':1,
 'native_hosts_full_gate':'CLOSED; c315 is not a successful Full proof.',
 'provenance_full_sha256':sha((RUN/'receipt-provenance.json').read_bytes()),
 'prior_receipt_paths_preserved':c['unchanged_prior_receipt_paths'],'raw_current_receipts':rows,
 'human_device_acceptance_claimed':False,'native_geometry_or_art_copied':False}
(DEST/'ROOT_CLOSURE.json').write_text(json.dumps(summary,indent=2)+'\n')
copy(Path(__file__),'code_used/preserve_failed_full_c315_20261121.py')
pins=[]
for p in sorted(DEST.rglob('*')):
 if p.is_file():
  raw=p.read_bytes();pins.append({'path':p.relative_to(DEST).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
(DEST/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_failed_c315_full_evidence_pins_1','files':pins},indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='raw_current_receipts'}))
