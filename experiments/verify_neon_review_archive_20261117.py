"""Independent exact payload/source-binding verification of the review archive."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'experiments/neon_actual_review_packet_20261117'
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha((P/'INDEX.json').read_bytes())=='c9dc2b154bc4c2c44193e34b2f6226637bf8de74f6a3c20a7de7e3da8fe82832'
index=json.loads((P/'INDEX.json').read_bytes());rows=index['files']
assert len(rows)==228 and sum(r['bytes'] for r in rows)==799784
names={r['path'] for r in rows};assert len(names)==228
actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()}
assert actual==names|{'INDEX.json'}
blocked={'.png','.jpg','.jpeg','.glb','.gltf','.mdl','.vvd','.vtx','.pmx','.pmd','.vrm','.blend','.has','.wav','.mp3','.mp4','.kra','.bin','.exe','.dll'}
for row in rows:
    p=P/row['path'];assert p.resolve().is_relative_to(P) and not p.is_symlink() and p.suffix not in blocked
    b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
    text=gzip.decompress(b) if p.suffix=='.gz' else b
    assert b'\0' not in text;text.decode('utf-8')
bindings=json.loads((P/'EXACT_SOURCE_BINDINGS.json').read_bytes())['files'];assert len(bindings)==217
for row in bindings:
    b=(P/row['archive_path']).read_bytes();assert len(b)==row['archive_bytes'] and sha(b)==row['archive_sha256']
    raw=gzip.decompress(b) if row['gzip_exact_original'] else b
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
summary=json.loads((P/'ACTUAL_RESULTS.json').read_bytes())
assert summary['original_behavior']=='32/13' and summary['boundary_v3']=='32/0' and summary['corrected_full_suite']=='PENDING_SEPARATE_EXECUTION'
assert summary['merge_or_product_completion_claimed'] is False and summary['manual_owner_result']=='DEFERRED_NO_RESULT'
target=ROOT/'experiments/neon_review_root_archive_audit_20261117';target.mkdir(exist_ok=False)
result={'format':'has_independent_neon_review_archive_audit_1','passed':True,'exact_payload_checks':228,'exact_original_bindings':217,'unexpected_members':0,'native_media_or_project_suffixes':0,'all_utf8_text_or_compressed_text':True,'product_test_checks_claimed_by_this_audit':0,'archive_index_sha256':sha((P/'INDEX.json').read_bytes())}
(target/'ROOT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
