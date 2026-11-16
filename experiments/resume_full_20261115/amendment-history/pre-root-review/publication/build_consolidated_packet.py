"""Consolidate frozen summary/receipt metadata with lossless aliases, no old mutation."""
from pathlib import Path
import gzip,hashlib,json,shutil,argparse,re
import publication_gates as Gates
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
CONTEXT=json.loads((BASE/'RUN_EXPECTATIONS.json').read_bytes())
ROOT=Path(CONTEXT['workspace_root'])
REGISTRY=Gates.registry(BASE,CONTEXT)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--terminal-permission',action='store_true',required=True)
parser.add_argument('--summary-index-sha256',required=True)
parser.add_argument('--audit-index-sha256',required=True)
parser.add_argument('--destination',type=Path,default=BASE/'review-ready')
options=parser.parse_args()
assert all(re.fullmatch(r'[0-9a-f]{64}',v) for v in [options.summary_index_sha256,options.audit_index_sha256])
SUMMARY=BASE/'actual-summary';AUDIT=BASE/'receipt-audit';RUN=ROOT/'output'/CONTEXT['run_name']
state=json.loads((RUN/'state.json').read_bytes())
assert state['status']=='passed' and state['suite_exit']==0 and state['source_unchanged'] is True and state['source_commit']==CONTEXT['source_commit']
Gates.validate_raw_host(RUN,CONTEXT,state,Gates.load(RUN/'authoritative-host-termination.json'))
SCOPED_PROOF=Gates.validate_scoped(ROOT,CONTEXT,Gates.load(RUN/'source-before.json'))
DEST=options.destination.resolve();assert DEST.parent==BASE and not DEST.exists();DEST.mkdir(exist_ok=False)

def sha(data):return hashlib.sha256(data).hexdigest()
def relative(value):
 path=Path(value)
 assert not path.is_absolute() and '..' not in path.parts and path.parts
 assert path.suffix.lower() in {'.json','.py','.gd','.md','.txt','.log','.gz','.ps1'}
 return path
def stamp(path):
 data=Gates.read(Path(path));return {'bytes':len(data),'sha256':sha(data)}
def load(path):return Gates.load(Path(path))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def copy(source,target):
 target=DEST/relative(target);target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.read_bytes()==Path(source).read_bytes()
 else:shutil.copy2(source,target)
 return target
indices={
 'summary':{'root':SUMMARY,'expected':options.summary_index_sha256},
 'receipt_audit':{'root':AUDIT,'expected':options.audit_index_sha256},
}
for name,entry in indices.items():
 assert stamp(entry['root']/'INDEX.json')['sha256']==entry['expected']
 entry['index']=load(entry['root']/'INDEX.json')
 for row in entry['index']['files']:assert stamp(entry['root']/relative(row['path']))=={'bytes':row['bytes'],'sha256':row['sha256']}
 copy(entry['root']/'INDEX.json','provenance/'+name+'-original-INDEX.json')
for row in indices['summary']['index']['files']:copy(SUMMARY/relative(row['path']),row['path'])
gzip_proof=[]
for name,expected in indices['summary']['index']['gzip_originals'].items():
 packed=(DEST/name).read_bytes();raw=gzip.decompress(packed)
 assert len(raw)==expected['bytes'] and sha(raw)==expected['sha256']
 gzip_proof.append({'path':name,'compressed':stamp(DEST/name),'decoded':expected,'roundtrip_verified':True})

known={
 'full-verification.json':('verification.json.gz','gzip_decode'),
 'source-before.json':('canonical/source-before.json.gz','gzip_decode'),
 'source-after.json':('canonical/source-after.json.gz','gzip_decode'),
 'receipt-inventory.json':('closure/receipt-inventory.json.gz','gzip_decode'),
 'state.json':('canonical/state.json','identity'),
 'authoritative-host-termination.json':('closure/host-proof.json','identity'),
 'authoritative-host-terminal.json':('closure/authoritative-host-terminal.json','identity'),
 'coordinator-children-observed.json':('closure/coordinator-children-observed.json','identity'),
 'root-graphics-lease-released.json':('closure/graphics-lease-released.json','identity'),
 'audit_receipts.py':('recipe/audit_receipts.py','identity'),
 'finalize_index.py':('recipe/finalize_receipt_index.py','identity'),
 'RUN_EXPECTATIONS.json':('recipe/RUN_EXPECTATIONS.json','identity'),
 'RESULT_REGISTRY.json':('recipe/RESULT_REGISTRY.json','identity'),
 'publication_gates.py':('recipe/publication_gates.py','identity'),
 'README.md':('provenance/receipt-audit-original-README.md','identity'),
}
aliases=[]
for row in indices['receipt_audit']['index']['files']:
 old=row['path']
 if old in known:target,codec=known[old]
 elif old.startswith('physical-receipts/'):target,codec='closure/'+old,'identity'
 else:target,codec='receipt-audit/'+old,'identity'
 if codec=='identity':copy(AUDIT/relative(old),target)
 raw=gzip.decompress((DEST/target).read_bytes()) if codec=='gzip_decode' else (DEST/target).read_bytes()
 assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
 aliases.append({'original_relative_path':old,'original_file':str(AUDIT/old),'raw_bytes':row['bytes'],'raw_sha256':row['sha256'],'consolidated_path':target,'recover':codec,'consolidated_file':stamp(DEST/target),'raw_roundtrip_verified':True})

root_aliases=[]
for original,target in (
 ('graphics-lease-released.json','closure/graphics-lease-released.json'),
 ('coordinator-children-observed.json','closure/coordinator-children-observed.json'),
 ('authoritative-host-terminal.json','closure/authoritative-host-terminal.json'),
 ('authoritative-host-termination.json','closure/host-proof.json'),
 ('state.json','canonical/state.json'),('launch.json','canonical/launch.json')):
 copy(RUN/original,target)
 root_aliases.append({'original_file':str(RUN/original),'consolidated_path':target,**stamp(RUN/original),'exact_raw_copy':True})
summary=load(DEST/'SUMMARY.json');inventory=json.loads(gzip.decompress((DEST/'closure/receipt-inventory.json.gz').read_bytes()))
assert summary['status']=='passed' and summary['suite_exit']==0 and summary['source_commit']==CONTEXT['source_commit'] and summary['source_files_before']==summary['source_files_after']==CONTEXT['functional_source_entries'] and summary['result_key_count']==CONTEXT['expected_result_entries'] and summary['core_process_group_count']==CONTEXT['expected_core_process_groups']
audit=inventory['summary'];assert audit['passed'] and audit['unique_receipt_files']==audit['unique_desktops']>0 and audit['success_exit_0_files']+1==audit['unique_receipt_files'] and audit['expected_krita_cancel_exit_2_files']==1
assert summary['source_choice_foundation']['checks']==CONTEXT['foundation_checks'] and summary['source_choice_foundation']['separately_named_jiggle_cpu']['checks']==CONTEXT['separate_jiggle_cpu_checks'] and summary['source_import_owner']['checks']==CONTEXT['separate_source_import_owner_checks']
assert summary['source_choice_foundation']['separately_named_crosswalk_cpu']['checks']==CONTEXT['separate_crosswalk_cpu_checks'] and summary['source_choice_foundation']['separately_named_bone_bindings_headless']['checks']==CONTEXT['separate_bone_bindings_headless_checks']
Gates.validate_result(json.loads(gzip.decompress((DEST/'verification.json.gz').read_bytes())),CONTEXT,REGISTRY)
assert len([row for row in aliases if row['original_relative_path'].startswith('physical-receipts/')])==audit['unique_receipt_files']
identity=load(DEST/'closure/coordinator-children-observed.json');host=load(DEST/'closure/host-proof.json');release=load(DEST/'closure/graphics-lease-released.json')
assert stamp(DEST/'closure/coordinator-children-observed.json')['sha256']==CONTEXT['children_observation_sha256'] and identity['format']==CONTEXT['children_observation_format'] and identity['source_commit']==CONTEXT['source_commit']
python=identity['python'];assert python['pid']==CONTEXT['python_pid']
assert identity['coordinator']['pid']==host['coordinator_pid']==release['coordinator_pid']==CONTEXT['coordinator_pid']
assert identity['coordinator']['creation_utc']==host['expected_creation_utc']==CONTEXT['coordinator_creation_utc']
assert python['parent_pid']==CONTEXT['coordinator_pid'] and python['creation_utc']==host['expected_python_creation_utc']==CONTEXT['python_creation_utc']
assert python['command']==CONTEXT['suite_python_command']
assert release['released'] is True and release['all_private_jobs_closed'] is True and release['no_process_killed'] is True
assert release['canonical_state_sha256']==stamp(DEST/'canonical/state.json')['sha256'] and release['host_proof_sha256']==stamp(DEST/'closure/host-proof.json')['sha256'] and release['receipt_inventory_sha256']==sha(gzip.decompress((DEST/'closure/receipt-inventory.json.gz').read_bytes()))

write(DEST/'provenance/LOSSLESS_ALIAS_MAP.json',{'format':'has_canonical_sfm_lossless_metadata_aliases_1','original_indices':{name:{'source':str(entry['root']),'sha256':entry['expected'],'retained_as':'provenance/'+name+'-original-INDEX.json'} for name,entry in indices.items()},'receipt_audit_files':aliases,'root_run_files':root_aliases,'summary_payloads':'Retained at their original relative paths; original summary INDEX recovers every payload','all_audit_payloads_mapped':len(aliases)==len(indices['receipt_audit']['index']['files']),'old_files_mutated_or_deleted':False})
write(DEST/'provenance/GZIP_ROUNDTRIP.json',{'format':'has_canonical_sfm_lossless_gzip_proof_1','files':gzip_proof,'all_passed':all(row['roundtrip_verified'] for row in gzip_proof),'raw_sha256_authoritative':True})
(DEST/'closure/IDENTITY_NOTE.md').write_text('Exact coordinator '+str(CONTEXT['coordinator_pid'])+' birth '+CONTEXT['coordinator_creation_utc']+' and Python '+str(CONTEXT['python_pid'])+' birth '+CONTEXT['python_creation_utc']+' bind closure. The pinned live observation records source commit, both exact births, Python parent and command. It records no raw CIM timestamp or executable observation and no discovery-method note; none is invented. These recipes perform no process enumeration or kill.\n',encoding='utf-8')
scoped=ROOT/CONTEXT['scoped_native_packet'];scoped_index=load(scoped/'INDEX.json')
copy(scoped/'INDEX.json','scoped-native/INDEX.json')
for row in scoped_index['files']:copy(scoped/row['path'],'scoped-native/'+row['path'])
write(DEST/'provenance/SCOPED_NATIVE_BINDING.json',SCOPED_PROOF)
reviewed=ROOT/CONTEXT['reviewed_provenance_delta']['packet'];reviewed_index=load(reviewed/'INDEX.json')
copy(reviewed/'INDEX.json','reviewed-provenance-tests/INDEX.json')
for row in reviewed_index['files']:copy(reviewed/relative(row['path']),'reviewed-provenance-tests/'+row['path'])
write(DEST/'provenance/REVIEWED_SOURCE_DELTA.json',SCOPED_PROOF['reviewed_provenance_test_delta'])
(DEST/'README.md').write_text('Terminal canonical PASS at '+summary['source_commit']+' in '+str(summary['elapsed_seconds'])+' seconds. '+str(summary['source_files_before'])+' functional source entries, exact157 named result groups,36 named core processes and21 named root movie gates are verified against the pinned source registry. Foundation167 remains separate from jiggleCPU66, crosswalkCPU77, authored headless96(79+17), and owner53. '+str(audit['unique_receipt_files'])+' private receipt files close: '+str(audit['success_exit_0_files'])+' exit0 plus one explicitly registered Krita cancellation exit2. Actual default audio driver: '+summary['audio_scope']['dedicated_default_driver']+'; silent contact selection explicitly usesDummy. Raw receipts, source maps, host/release, log and verification have byte-exact lossless aliases. The scoped four-native packet is retained separately with1006 exact functional byte joins plus exactly two pinned independently reviewed provenance-test changes to this pushed canonical source. Its five private jobs are not added to the canonical total. FailedEE and failedc4d remainFAILED permanently. No native rest/mesh/art/HAS/media/runtime payload or Source solver/manual acceptance claim is included.\n',encoding='utf-8')
copy(Path(__file__),'recipe/build_consolidated_packet.py')
publication={'format':'has_windows_canonical_bone_binding_full_publication_1','source_commit':summary['source_commit'],'passed':True,'elapsed_seconds':summary['elapsed_seconds'],'functional_source_entries':summary['source_files_before'],'result_groups':summary['result_key_count'],'core_process_groups':summary['core_process_group_count'],'private_jobs':audit['unique_receipt_files'],'exit_0':audit['success_exit_0_files'],'expected_krita_cancel_exit_2':audit['expected_krita_cancel_exit_2_files'],'raw_receipts_preserved':audit['unique_receipt_files'],'lossless_audit_aliases':len(aliases),'original_summary_index_sha256':indices['summary']['expected'],'original_receipt_audit_index_sha256':indices['receipt_audit']['expected'],'no_runtime_tests_or_source_mutation':True,'separate_named_scopes':{'foundation':167,'jiggle_cpu':66,'crosswalk_cpu':77,'bone_bindings_headless':96,'source_import_owner':53},'audio_scope':summary['audio_scope'],'media':summary['media'],'scoped_native_packet':SCOPED_PROOF,'prior_EE_canonical_status':'FAILED_permanent','prior_c4d_canonical_status':'FAILED_permanent','scoped_native_fidelity_claim':False,'helper_provenance_evidence':summary['helper_provenance_evidence']}
write(DEST/'PUBLICATION.json',publication)
write(DEST/'CANONICAL_BENCHMARK.json',{'format':'has_canonical_bone_binding_benchmark_1','publication':publication,'canonical_result_keys':summary['result_keys'],'core_process_groups':summary['core_process_groups'],'source_choice_foundation':summary['source_choice_foundation'],'receipt_semantics':'Counts observed for this exact interval; original GUI receipts preserved. Exactly one registered Krita cancellation exit2 is expected, not a successful normal run. Headless79+17 and scoped native5 private jobs remain separate scopes.','native_solver':'not_implemented','manual_owner_acceptance':'separate_unrun_gate'})

for name,entry in indices.items():
 assert stamp(entry['root']/'INDEX.json')['sha256']==entry['expected']
 assert all(stamp(entry['root']/relative(row['path']))=={'bytes':row['bytes'],'sha256':row['sha256']} for row in entry['index']['files'])
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(DEST).as_posix(),**stamp(p)} for p in sorted(DEST.rglob('*')) if p.is_file()]}
assert all(Path(row['path']).suffix.lower() in {'.json','.py','.gd','.md','.txt','.log','.gz','.ps1'} for row in index['files'])
write(DEST/'INDEX.json',index)
print(json.dumps({'folder':str(DEST),'files':len(index['files']),'bytes':sum(x['bytes'] for x in index['files']),'index_sha256':stamp(DEST/'INDEX.json')['sha256'],'audit_aliases':len(aliases),'raw_receipts':audit['unique_receipt_files'],'old_packets_unchanged':True},indent=2))
