"""Actual fan-deformed manual pose returns on hair disable without draft/key edits."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command

def main():
    args=command('tests/hair_disable_smoke.gd')
    p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120)
    raw=p.stdout+p.stderr
    (ROOT/'output/hair-disable-verification.log').write_bytes(raw)
    assert p.returncode==0 and b'HAIR_DISABLE ' in raw and not any(x in raw for x in [b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked']),raw[-4000:]
    result=json.loads((ROOT/'output/hair-disable-result.json').read_bytes())
    assert result['checks']==8 and result['failures']==0,result
    receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes())
    assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
    result['private_receipt']=receipt
    (ROOT/'output/hair-disable-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
