from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
body=(ROOT/'experiments/prepare_neon_full_candidate_20261117.py').read_text(encoding='utf-8')
for before,after in {
 "REV='381d5a974d34eb4dc10208a44c1a54d178c72fbb'":"REV='f387d0e9ddfb099140c0699d9f7ed430f5d7b949'",
 "'windows-neon-381d5a9-'":"'windows-neon-f387d0e-'",
 "packet=ROOT/'experiments/neon_windows_candidate_20261117'":"packet=ROOT/'experiments/neon_windows_f387d0e_20261117'"}.items():
    assert body.count(before)==1;body=body.replace(before,after)
target=ROOT/'experiments/prepare_neon_f387_full_actual_20261117.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
print(json.dumps({'preflight':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
