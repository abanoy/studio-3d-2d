"""Prepare a counterfactual successor using the exact same32-assertion probe."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/run_neon_behavior_original_20261116.py'
body=old.read_text(encoding='utf-8')
edits={
 "FOLDER=REVIEW/'output/neon-behavior-original-20261116-attempt1'":"FOLDER=REVIEW/'output/neon-behavior-candidate-20261116-attempt1'",
 "    assert sources()==baseline":"    applied=json.loads((ROOT/'experiments/neon_windows_original_20261116/APPLIED_SUCCESSOR.json').read_bytes())\n    for name,row in applied['changed'].items(): baseline[name]=row['new_sha256']\n    assert sources()==baseline",
 "    assert not to.exists();to.write_bytes(SOURCE.read_bytes());assert sha(to)==EXPECTED":"    assert to.is_file() and sha(to)==EXPECTED",
 "'has_neon_original_behavior_execution_1'":"'has_neon_candidate_behavior_execution_1'",
 "'root_expected_original_regressions':True":"'root_expected_original_regressions':False",
}
for before,after in edits.items():assert body.count(before)==1;body=body.replace(before,after)
target=ROOT/'experiments/run_neon_behavior_candidate_20261116.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
print(json.dumps({'driver':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'same_probe_sha256':'40a2fae5485cdf08feb7abd2a3303a1cd92650a3785fcd842d7e94ea55a3a020'}))
