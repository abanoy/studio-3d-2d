"""Actual background image worker, responsive app, serialized catalog and teardown."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/recovery-preview'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/recovery_preview_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'RECOVERY_PREVIEW ' in log and '"failures":0' in log and not any(x in log for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'))
    assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
    result['private_receipt']=str(receipt);(ROOT/'output/recovery-preview-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
