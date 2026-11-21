from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
expected='fd9ec2eff6157f02d93e51f1f9e9e2040fe407aa13f5922ac7e2967c76b1d450'
rows=[]
for revision in ('435dc02426a7cdd313e43fe674c9008520845428','c31576d0c1d84030d51ec886f2f3976a60a70c7b'):
 raw=subprocess.check_output(['git','cat-file','blob',revision+':web/studio.svg'],cwd=ROOT)
 assert len(raw)==720 and hashlib.sha256(raw).hexdigest()==expected
 oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 rows.append({'revision':revision,'path':'web/studio.svg','bytes':len(raw),'sha256':expected,'git_sha1':oid})
assert (ROOT/'web/studio.svg').read_bytes()==raw
result={'format':'has_cleanup_repository_art_recovery_1','status':'PASS','committed_copies':rows,
 'raw_artwork_copied':False,'deletion_performed':False,'physical_disk_reclaimed_claimed':False}
target=ROOT/'output/EASING_CLEANUP_REPOSITORY_ART_BINDING_20261121.json';assert not target.exists()
target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
