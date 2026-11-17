"""Independent exact closed4ed archive review; no builder/native/process/Git."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
PACKET=HERE.parent/'neon_failed_4ed_actual_packet_20261117'
REVIEW=HERE.parents[2]/'has-neon-review-20261116-c2d52ff'
def sha(data):return hashlib.sha256(data).hexdigest()
def equal(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b
def main():
    assert sha((PACKET/'INDEX.json').read_bytes())=='765247e3ad96b440b5b856dfcd2878b79e98d14bb015d577d558fa8f99c7a854'
    idx=json.loads((PACKET/'INDEX.json').read_bytes())
    assert {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()}=={r['path'] for r in idx['files']}|{'INDEX.json'}
    for row in idx['files']:
        data=(PACKET/row['path']).read_bytes();assert len(data)==row['bytes'] and sha(data)==row['sha256']
    bindings=json.loads((PACKET/'EXACT_SOURCE_BINDINGS.json').read_bytes())['files'];raw={}
    for row in bindings:
        original=REVIEW/row['path'];assert row['root']=='neon' and original.is_relative_to(REVIEW) and '..' not in Path(row['path']).parts
        data=(PACKET/row['archive_path']).read_bytes();assert len(data)==row['archive_bytes'] and sha(data)==row['archive_sha256']
        if row['gzip_exact_original']:data=gzip.decompress(data)
        assert len(data)==row['bytes'] and sha(data)==row['sha256'] and sha(original.read_bytes())==row['sha256']
        data.decode('utf-8-sig');assert b'\0' not in data
        raw[row['archive_path'].removesuffix('.gz')]=data
    def obj(name):return json.loads(raw[name])
    inventory=obj('actual/receipt-inventory.json');release=obj('actual/graphics-lease-closed.json');state=obj('actual/state.json')
    assert sha(raw['actual/receipt-inventory.json'])==release['receipt_inventory_sha256']=='6b8c57667a3c553152396711a6b755faf7f923714ad6724eddba06bf123ad87d'
    assert sha(raw['actual/state.json'])==release['terminal_state_sha256']
    assert state['status']=='failed' and state['suite_exit']==1 and state['source_unchanged'] is True
    assert release['released'] is True and release['release_kind']=='closed_failed_partial_run' and release['full_suite_passed'] is False and release['final_full_report_used'] is False
    assert release['physical_jobs']==release['physical_receipt_files']==49 and release['released_utc']=='2026-11-17T03:19:55.1591793Z'
    before=obj('actual/source-before.json');assert equal(before,obj('actual/source-after.json')) and len(before['source_sha256'])==1029 and before['commit']==state['source_commit']==release['source_commit']=='4ed3a63b716f696daa1699a76443d6f1abb9b096'
    assert inventory['suite_status']=='failed' and inventory['suite_exit']==1 and inventory['full_suite_passed'] is False and inventory['final_full_report_used'] is False
    assert (inventory['normal_exit0'],inventory['registered_cancel_exit2'],inventory['failed_partial_nonzero'],inventory['unique_physical_jobs'],inventory['physical_receipt_files'])==(48,1,0,49,49)
    receipts={};classes=collections.Counter()
    for i,row in enumerate(inventory['rows']):
        receipt=row['receipt'];key=(receipt['desktop'],receipt['child_pid'])
        assert key not in receipts;receipts[key]=receipt;classes[row['classification']]+=1
        for name,wanted in {'format':'studio_private_desktop_1','desktop_switch_requested':False,'private_window_seen':True,'child_desktop_confirmed':True,'foreground_child_observed':False,'job_closed':True,'desktop_closed':True}.items():assert equal(receipt.get(name),wanted),(i,name)
        assert type(receipt['child_pid']) is int and type(receipt['exit']) is int and row['references']
        leaf=Path(row['preserved_raw_copy']).name
        archived=raw[f'actual/receipts/{i:03d}-{leaf}'];assert sha(archived)==row['source_sha256'] and equal(json.loads(archived),receipt)
        if receipt['exit']==2:assert row['classification']=='registered_Krita_cancel_exit2' and receipt['cancelled'] is True and receipt['error']=='Owned converter cancelled' and 'source_registered_Krita_cancel' in row['references']
        else:assert receipt['exit']==0 and row['classification']=='normal_exit0'
    assert classes=={'normal_exit0':48,'registered_Krita_cancel_exit2':1} and inventory['duplicate_physical_copies']==0 and inventory['registered_cancel_observed'] is True
    for row in inventory['inline_receipts']:
        receipt=row['receipt'];assert equal(receipt,receipts[(receipt['desktop'],receipt['child_pid'])])
    for observation in (inventory['process_observation'],release['second_identity_and_scope_observation']):
        assert observation['root_observer_issued_no_termination'] is True and observation['owned_runtime_command_matches_absent'] is True and observation['owned_runtime_matches']==[] and observation['observer_retained_Popen_reaped'] is True
        for kind,pid,birth in [('coordinator',22224,'2026-11-17T03:02:32.4796950Z'),('python',1820,'2026-11-17T03:02:33.0241444Z')]:
            record=observation[kind];assert record['pid']==pid and record['expected_creation_utc']==birth and record['original_absent'] is True
    helper=obj('helper/verification.json');assert helper['checks']==0 and helper['results']==[] and helper['actual_res_root'] is None and helper['native_requested'] is False and helper['native_inputs_checked'] is False and helper['native_fidelity'] is False and helper['graphical_process_attempted'] is False and helper['gpu_used'] is False and helper['passed'] is False and helper['error']=='RuntimeError: Unreviewed helper main bytes: src/app.gd'
    scene=obj('scene/verification.json');assert scene['scene_view_smoke']['checks']==106 and scene['scene_view_smoke']['failures']==0 and scene['scene_view_unit']['checks']==12830 and scene['scene_view_unit']['failures']==0 and equal(scene['scene_view_unit'],obj('scene/unit.json'))
    smoke={k:v for k,v in scene['scene_view_smoke'].items() if k not in ('private_receipt','private_receipt_path')};assert equal(smoke,obj('scene/result.json'))
    command=obj('scene/scene_view_smoke-command.json');assert command[command.index('--receipt')+1]==scene['scene_view_smoke']['private_receipt_path'];r=scene['scene_view_smoke']['private_receipt'];assert equal(r,receipts[(r['desktop'],r['child_pid'])])
    canonical=raw['actual/canonical.log'].decode('utf-8-sig');passes=re.findall(r'^PASS ([a-z_]+):',canonical,re.M);assert len(passes)==len(set(passes))==36 and 'PASS neon workspace:' in canonical and 'Unreviewed helper main bytes' not in canonical and '"checks": 0' in canonical
    summary=json.loads((PACKET/'ACTUAL_RESULT.json').read_bytes());assert summary['physical_jobs']==49 and summary['full_suite_passed'] is False and summary['helper_checks_run']==0 and summary['stale_final_report_used'] is False
    report={'status':'PASS_INDEPENDENT_CLOSED_ARCHIVE_SOURCE_SCALAR_AUDIT','index_sha256':sha((PACKET/'INDEX.json').read_bytes()),'payloads_verified':len(idx['files']),'decompressed_original_bindings_currently_byte_verified':len(bindings),'source_entries_unchanged':1029,'raw_receipts_unique_jobs':49,'normal_exit0':48,'registered_Krita_cancel_exit2':1,'failed_physical_jobs':0,'inline_exact_typed_joins':len(inventory['inline_receipts']),'headless_jobs_not_counted_as_desktop_receipts':True,'core_PASS_lines':36,'scene106_and_unit12830_pass':True,'helper0_checks_no_snapshot_or_native_engine_launch':True,'two_recorded_exact_birth_scope_observations_absent_no_termination':True,'full_suite_pass_claimed':False,'engines_CIM_Git_run_by_audit':False,'active_output_read':False,'qualification_limit':'Most phase document raw bodies are omitted from compact public archive. Ownership references are preserved in the pinned terminal inventory; this audit independently checks raw receipt/inline identity but does not re-prove every referenced command from omitted private phase documents.','wording_correction':'Immutable README.md says before running checks or launching a process. Interpret native engine/worker/graphical launch only: tests/verify_helper_preview.py source_state and final head preservation invoke Git subprocesses outside that boundary.'}
    with (HERE/'REPORT.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
