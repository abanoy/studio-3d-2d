"""Apply only independently reviewed corrections after the original run closes."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
run=REVIEW/'output/windows-neon-c2d52ff-20261117T000859'
closure=json.loads((run/'authoritative-host-closure.json').read_bytes())
assert closure['exclusive_graphics_lease_released'] and closure['source_unchanged']
baseline=json.loads((run/'source-before.json').read_bytes())['source_sha256']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(REVIEW/n)==v for n,v in baseline.items())
replacements={
 'src/app.gd':('neon_redesign_review_20261116/draft/src/app.gd','88871ebd831d5a466b31336282a9bb53f264653dd5ff299fb10dc90a3080dd67'),
 'tests/wind_review_port_files.json':('neon_redesign_review_20261116/draft/tests/wind_review_port_files.json','4cb3709064b668e63b25cb9576a69992495c5707ed5ec2dba291c0768852e79d'),
 'tests/object_timing_smoke.gd':('neon_redesign_geometry_successor_20261116/object_timing_smoke.gd','d8cd3048e23db2c5f94798fb8aac0df66a26262fb5d10c367baba3e3ff8eb267')}
for name,(draft,digest) in replacements.items():
    source=ROOT/'experiments'/draft;assert sha(source)==digest
    if name.endswith('.gd'):
        old=(REVIEW/name).read_bytes();new=source.read_bytes()
        assert old.count(b'\r\n')==old.count(b'\n') and new.count(b'\r\n')==new.count(b'\n')
subprocess.run(['git','switch','-c','codex/neon-windows-review-20261116'],cwd=REVIEW,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
for name,(draft,digest) in replacements.items():(REVIEW/name).write_bytes((ROOT/'experiments'/draft).read_bytes())
assert all(sha(REVIEW/n)==v for n,v in baseline.items() if n not in replacements)
record={'format':'has_neon_review_applied_corrections_1','base':'c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2','branch':'codex/neon-windows-review-20261116','changed':{n:{'old_sha256':baseline[n],'new_sha256':sha(REVIEW/n)} for n in replacements},'original_28_2_and_behavior32_13_failures_preserved':True,'product_full_pass_claimed':False}
target=ROOT/'experiments/neon_windows_original_20261116/APPLIED_SUCCESSOR.json'
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
