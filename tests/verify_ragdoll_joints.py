"""Actual bounded-velocity before/after joint probes using native bone frames."""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command
def main():
    p=subprocess.run(command('tests/ragdoll_joints_smoke.gd'),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=260)
    text=p.stdout+p.stderr
    (ROOT/'output/joints-verification.log').write_text(text,encoding='utf-8')
    if p.returncode or 'RAGDOLL_JOINTS ' not in text or '"failures":0' not in text or any(x in text for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):raise RuntimeError(text)
    report=json.loads((ROOT/'output/joints-result.json').read_text(encoding='utf-8'))
    (ROOT/'output/joints-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
