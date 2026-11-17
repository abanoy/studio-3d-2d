"""Prepare distinct diagnostic and strengthened-fixture runs; product unchanged."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/run_neon_behavior_candidate_20261116.py'
original=old.read_text(encoding='utf-8')
rows=[]
for label,filename,digest in [('diagnostic','neon_behavior_diagnostic.gd','cb98532eebc4c250e1aaf24cd43c30bdfab6f33ea727b6a9419ed7ba6fbbe4d5'),('fixture','neon_behavior_regression.gd','8ee51d41d0719f5a5a29281d50c9be594d35c1c1534d0790b855fe16cbc0fc1c')]:
    body=original
    pairs={
     "SCRIPT='experiments/neon_redesign_review_20261116/neon_behavior_regression.gd'":f"SCRIPT='experiments/neon_redesign_refresh_fixture_20261116/{filename}'",
     "EXPECTED='40a2fae5485cdf08feb7abd2a3303a1cd92650a3785fcd842d7e94ea55a3a020'":f"EXPECTED='{digest}'",
     "FOLDER=REVIEW/'output/neon-behavior-candidate-20261116-attempt1'":f"FOLDER=REVIEW/'output/neon-behavior-{label}-20261116-attempt1'",
     "    assert sources()==baseline":"    baseline['src/workspace_layout.gd']='7d194eaf03d03b909fa0caaf84c197f91e8fb29af95f2978ae5f8d798e3dfe8b'\n    assert sources()==baseline",
     "    assert to.is_file() and sha(to)==EXPECTED":"    assert not to.exists();to.write_bytes(SOURCE.read_bytes());assert sha(to)==EXPECTED",
     "'has_neon_candidate_behavior_execution_1'":f"'has_neon_{label}_behavior_execution_1'"}
    for before,after in pairs.items():assert body.count(before)==1;body=body.replace(before,after)
    target=ROOT/f'experiments/run_neon_behavior_{label}_20261116.py'
    with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    rows.append({'label':label,'driver':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'script_sha256':digest})
print(json.dumps(rows))
