"""Consolidate frozen summary/receipt metadata with lossless aliases, no old mutation."""
from pathlib import Path
import gzip,hashlib,json,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
SUMMARY=ROOT/'output/canonical-sfm-summary-prep-20261114/actual-summary'
AUDIT=ROOT/'output/canonical-sfm-receipt-audit-20261114'
RUN=ROOT/'output/windows-canonical-sfm-20261114T002803393'
DEST=BASE/'review-ready';DEST.mkdir(exist_ok=False)
def sha(data):return hashlib.sha256(data).hexdigest()
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':sha(data)}
def load(path):return json.loads(Path(path).read_bytes())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def copy(source,target):
 target=DEST/target;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.read_bytes()==Path(source).read_bytes()
 else:shutil.copy2(source,target)
 return target
indices={
 'summary':{'root':SUMMARY,'expected':'0809a7a0c27380df2439e47cb38cc7b7e3142cbfc45b3a4438d593fc11b76339'},
 'receipt_audit':{'root':AUDIT,'expected':'d9cf5b9170c5ace1d9fa4d9a6e83657b1dcd207f330133be747671cfe5d0e8eb'},
}
for name,entry in indices.items():
 assert stamp(entry['root']/'INDEX.json')['sha256']==entry['expected']
 entry['index']=load(entry['root']/'INDEX.json')
 for row in entry['index']['files']:assert stamp(entry['root']/row['path'])=={'bytes':row['bytes'],'sha256':row['sha256']}
 copy(entry['root']/'INDEX.json','provenance/'+name+'-original-INDEX.json')
for row in indices['summary']['index']['files']:copy(SUMMARY/row['path'],row['path'])
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
 'root-graphics-lease-released.json':('closure/graphics-lease-released.json','identity'),
 'audit_receipts.py':('recipe/audit_receipts.py','identity'),
 'finalize_index.py':('recipe/finalize_receipt_index.py','identity'),
 'README.md':('provenance/receipt-audit-original-README.md','identity'),
}
aliases=[]
for row in indices['receipt_audit']['index']['files']:
 old=row['path']
 if old in known:target,codec=known[old]
 elif old.startswith('physical-receipts/'):target,codec='closure/'+old,'identity'
 else:target,codec='receipt-audit/'+old,'identity'
 if codec=='identity':copy(AUDIT/old,target)
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
assert summary['status']=='passed' and summary['suite_exit']==0 and summary['source_commit']=='9f6f531538156fc34e3652bc81da8a608e379156' and summary['source_files_before']==summary['source_files_after']==982 and summary['result_key_count']==156 and summary['core_process_group_count']==36
assert inventory['summary']['passed'] and inventory['summary']['unique_receipt_files']==192 and inventory['summary']['success_exit_0_files']==191 and inventory['summary']['expected_krita_cancel_exit_2_files']==1
assert len([row for row in aliases if row['original_relative_path'].startswith('physical-receipts/')])==192
identity=load(DEST/'closure/coordinator-children-observed.json');host=load(DEST/'closure/host-proof.json');release=load(DEST/'closure/graphics-lease-released.json')
python=next(row for row in identity['children'] if row['pid']==8188)
assert identity['coordinator_pid']==host['coordinator_pid']==release['coordinator_pid']==3136
assert identity['coordinator_creation_utc_exact']==host['expected_creation_utc']=='2026-11-14T00:28:03.4147954Z'
assert python['parent_pid']==3136 and python['creation_utc_exact']==host['expected_python_creation_utc']=='2026-11-14T00:28:04.1593199Z'
assert release['released'] is True and release['all_private_jobs_closed'] is True and release['no_process_killed'] is True
assert release['canonical_state_sha256']==stamp(DEST/'canonical/state.json')['sha256'] and release['host_proof_sha256']==stamp(DEST/'closure/host-proof.json')['sha256'] and release['receipt_inventory_sha256']==sha(gzip.decompress((DEST/'closure/receipt-inventory.json.gz').read_bytes()))

write(DEST/'provenance/LOSSLESS_ALIAS_MAP.json',{'format':'has_canonical_sfm_lossless_metadata_aliases_1','original_indices':{name:{'source':str(entry['root']),'sha256':entry['expected'],'retained_as':'provenance/'+name+'-original-INDEX.json'} for name,entry in indices.items()},'receipt_audit_files':aliases,'root_run_files':root_aliases,'summary_payloads':'Retained at their original relative paths; original summary INDEX recovers every payload','all_205_audit_payloads_mapped':len(aliases)==205,'old_files_mutated_or_deleted':False})
write(DEST/'provenance/GZIP_ROUNDTRIP.json',{'format':'has_canonical_sfm_lossless_gzip_proof_1','files':gzip_proof,'all_passed':all(row['roundtrip_verified'] for row in gzip_proof),'raw_sha256_authoritative':True})
(DEST/'closure/IDENTITY_NOTE.md').write_text('The root observation preserves exact100ns Get-Process creation times and separate CIM values. Coordinator3136 exact00:28:03.4147954Z appears as00:28:03.4147950Z through CIM; Python8188 exact00:28:04.1593199Z appears as00:28:04.1593190Z. The observation explicitly identifies CIM truncation to microseconds. The child parent PID is3136. Closure binds the exact creation times, not equality with truncated CIM text. Raw observation and host proof are unchanged. No process enumeration or kill was performed by this packet builder.\n',encoding='utf-8')
(DEST/'README.md').write_text('Canonical full regression PASS at9f6f531538156fc34e3652bc81da8a608e379156:46minutes27.2334936seconds,982functional source entries preserved,156result groups and36core process groups.21movies passed their recorded gates.192actual private jobs/desktops closed:191exit0 and one registered expected Krita cancellation exit2. All178fresh root receipts passed, all receipts are fresh/private/closed,13inline occurrences match physical receipts, and there are no missing references or unexpected failures.\n\nThe exact raw summary and audit indices are retained in provenance. Full verification, source maps and receipt inventory use the frozen summary gzip files; LOSSLESS_ALIAS_MAP.json maps every original audit payload to either exact raw bytes or decoded gzip bytes, with original sizes/SHA256. GZIP_ROUNDTRIP.json proves lossless recovery. All192individual receipts remain byte-exact. Root run release, authoritative raw/flat host closure and coordinator-child observation are included; IDENTITY_NOTE.md explains CIM precision. The builder creates no release and runs no tests.\n\nScope remains Source Base/derived editor, conversion and persistence transport. This does not certify native Source shader/procedural jiggle/controller/assembly or artist fidelity, human/device/clean-install acceptance, or the unported next-increment proposals. Earlier worker-only/native app evidence and old failed canonical attempts remain separate at their tested sources. No native/model/HAS/GLB/media/runtime payload is included and no old file was changed or deleted.\n',encoding='utf-8')
copy(Path(__file__),'recipe/build_consolidated_packet.py')
write(DEST/'PUBLICATION.json',{'format':'has_windows_canonical_sfm_full_publication_1','source_commit':summary['source_commit'],'passed':True,'elapsed_seconds':summary['elapsed_seconds'],'functional_source_entries':982,'result_groups':156,'core_process_groups':36,'private_jobs':192,'exit_0':191,'expected_krita_cancel_exit_2':1,'raw_receipts_preserved':192,'lossless_audit_aliases':len(aliases),'original_summary_index_sha256':indices['summary']['expected'],'original_receipt_audit_index_sha256':indices['receipt_audit']['expected'],'no_runtime_tests_or_source_mutation':True})
for name,entry in indices.items():
 assert stamp(entry['root']/'INDEX.json')['sha256']==entry['expected']
 assert all(stamp(entry['root']/row['path'])=={'bytes':row['bytes'],'sha256':row['sha256']} for row in entry['index']['files'])
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(DEST).as_posix(),**stamp(p)} for p in sorted(DEST.rglob('*')) if p.is_file()]}
assert not any(row['path'].endswith(('.png','.glb','.has','.wav','.mp4','.dll','.exe','.pyc')) for row in index['files'])
write(DEST/'INDEX.json',index)
print(json.dumps({'folder':str(DEST),'files':len(index['files']),'bytes':sum(x['bytes'] for x in index['files']),'index_sha256':stamp(DEST/'INDEX.json')['sha256'],'audit_aliases':len(aliases),'raw_receipts':192,'old_packets_unchanged':True},indent=2))
