"""Freeze an explicitly hash-bound terminal receipt audit; no release/process/runtime action."""
from pathlib import Path
import argparse,hashlib,json,re,shutil
import publication_gates as Gates
TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[1]
CONTEXT=json.loads((TASK/'RUN_EXPECTATIONS.json').read_bytes())
ROOT=Path(CONTEXT['workspace_root'])
REGISTRY=Gates.registry(TASK,CONTEXT)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--terminal-permission',action='store_true',required=True)
parser.add_argument('--inventory-sha256',required=True)
parser.add_argument('--release-sha256',required=True)
parser.add_argument('--audit-directory',type=Path,default=TASK/'receipt-audit')
options=parser.parse_args()
assert all(re.fullmatch(r'[0-9a-f]{64}',v) for v in [options.inventory_sha256,options.release_sha256])
BASE=options.audit_directory.resolve();RUN=ROOT/'output'/CONTEXT['run_name']
assert BASE.parent==TASK and BASE.is_dir() and not (BASE/'INDEX.json').exists()
def load(path):return Gates.load(Path(path))
def stamp(path):
 raw=Gates.read(Path(path));return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
state=load(RUN/'state.json')
assert state['status']=='passed' and state['suite_exit']==0 and state['source_unchanged'] is True and state['source_commit']==CONTEXT['source_commit']
assert stamp(RUN/'source-before.json')['sha256']==CONTEXT['source_before_sha256'] and stamp(RUN/'launch.json')['sha256']==CONTEXT['launch_sha256']
Gates.validate_raw_host(RUN,CONTEXT,state,load(RUN/'authoritative-host-termination.json'))
inventory=BASE/'receipt-inventory.json';assert stamp(inventory)['sha256']==options.inventory_sha256
value=load(inventory);summary=value['summary']
assert summary['passed'] and summary['state']==state and summary['source_commit']==CONTEXT['source_commit'] and summary['functional_source_entries']==CONTEXT['functional_source_entries'] and summary['full_result_top_level_entries']==CONTEXT['expected_result_entries']
assert summary['fresh_root_receipt_files']>0 and summary['unique_receipt_files']==summary['unique_desktops']>0 and not summary['unexpected_failures'] and summary['missing_referenced_receipts']==0
assert summary['expected_krita_cancel_exit_2_files']==1 and summary['success_exit_0_files']+1==summary['unique_receipt_files']
assert all(summary[k] is True for k in ('fresh_root_all_exit_0','fresh_root_all_private_closed','all_receipts_private_closed','all_receipts_fresh_for_run','all_inline_exact_physical_matches','authoritative_host_context_bound','source_before_after_equal'))
Gates.validate_result(load(BASE/'full-verification.json'),CONTEXT,REGISTRY)
for row in value['receipts']:
 assert stamp(row['preserved_raw_copy']['path'])=={'bytes':row['file']['bytes'],'sha256':row['file']['sha256']}
release=RUN/'graphics-lease-released.json';assert stamp(release)['sha256']==options.release_sha256
released=load(release)
assert released['released'] is True and released['source_commit']==CONTEXT['source_commit'] and released['canonical_run']==CONTEXT['run_name']
assert released['all_private_jobs_closed'] is True and released['no_process_killed'] is True and released['coordinator_pid']==CONTEXT['coordinator_pid'] and released['python_pid']==CONTEXT['python_pid']
assert released['canonical_state_sha256']==stamp(RUN/'state.json')['sha256'] and released['host_proof_sha256']==stamp(RUN/'authoritative-host-termination.json')['sha256'] and released['receipt_inventory_sha256']==options.inventory_sha256
shutil.copy2(release,BASE/'root-graphics-lease-released.json')
shutil.copy2(Path(__file__),BASE/'finalize_index.py')
shutil.copy2(TASK/'publication_gates.py',BASE/'publication_gates.py')
shutil.copy2(TASK/'RESULT_REGISTRY.json',BASE/'RESULT_REGISTRY.json')
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(BASE).as_posix(),**stamp(p)} for p in sorted(BASE.rglob('*')) if p.is_file()]}
assert all(Path(row['path']).suffix.lower() in {'.json','.py','.md','.txt','.log','.gz','.ps1'} for row in index['files'])
with (BASE/'INDEX.json').open('x',encoding='utf-8') as stream:json.dump(index,stream,indent=2);stream.write('\n')
print(json.dumps({'folder':str(BASE),'files':len(index['files']),'bytes':sum(r['bytes'] for r in index['files']),'index_sha256':stamp(BASE/'INDEX.json')['sha256'],'inventory_sha256':options.inventory_sha256,'summary':summary},indent=2))
