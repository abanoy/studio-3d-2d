from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
body=(ROOT/'experiments/run_neon_behavior_fixture_20261116.py').read_text(encoding='utf-8')
for before,after in {
 "SCRIPT='experiments/neon_redesign_refresh_fixture_20261116/neon_behavior_regression.gd'":"SCRIPT='experiments/neon_redesign_refresh_boundary_v3_20261116/neon_behavior_regression.gd'",
 "EXPECTED='8ee51d41d0719f5a5a29281d50c9be594d35c1c1534d0790b855fe16cbc0fc1c'":"EXPECTED='48d778041385988d0ac306ebbcf7440ae9e03ff35660871d0bed4e3f2a2cfcf9'",
 "FOLDER=REVIEW/'output/neon-behavior-fixture-20261116-attempt1'":"FOLDER=REVIEW/'output/neon-behavior-boundary-v3-20261116-attempt1'",
 "'has_neon_fixture_behavior_execution_1'":"'has_neon_boundary_v3_behavior_execution_1'"}.items():
    assert body.count(before)==1;body=body.replace(before,after)
target=ROOT/'experiments/run_neon_behavior_boundary_v3_20261116.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
print(json.dumps({'driver':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
