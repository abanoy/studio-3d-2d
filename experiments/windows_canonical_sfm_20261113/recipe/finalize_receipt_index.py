from pathlib import Path
import hashlib,json,shutil
BASE=Path(__file__).resolve().parent
release=BASE.parents[1]/'output/windows-canonical-sfm-20261114T002803393/graphics-lease-released.json'
if release.is_file():shutil.copy2(release,BASE/'root-graphics-lease-released.json')
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
inventory=BASE/'receipt-inventory.json'
assert stamp(inventory)['sha256']=='5a34a23fc83b84754313c929141248011b631ac119169a9b985662a84b63b158'
value=json.loads(inventory.read_bytes());summary=value['summary']
assert summary['passed'] and summary['fresh_root_receipt_files']==178 and summary['unique_receipt_files']==192 and not summary['unexpected_failures'] and summary['missing_referenced_receipts']==0
assert all(summary[k] is True for k in ('fresh_root_all_exit_0','fresh_root_all_private_closed','all_receipts_private_closed','all_receipts_fresh_for_run','all_inline_exact_physical_matches','authoritative_host_context_bound','source_before_after_equal'))
for row in value['receipts']:
 assert stamp(row['preserved_raw_copy']['path'])=={'bytes':row['file']['bytes'],'sha256':row['file']['sha256']}
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.relative_to(BASE).as_posix(),**stamp(p)} for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='INDEX.json']}
assert not any(p['path'].endswith(('.png','.glb','.has','.wav','.mp4','.dll','.exe','.pyc')) for p in index['files'])
(BASE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'files':len(index['files']),'bytes':sum(row['bytes'] for row in index['files']),'index_sha256':stamp(BASE/'INDEX.json')['sha256'],'inventory_sha256':stamp(inventory)['sha256'],'summary':summary},indent=2))
