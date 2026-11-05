from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    folder=ROOT/'output/foot-contacts'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/foot_contacts_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
    text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'FOOT_CONTACTS_EXPERIMENT ' in text and not any(s in text for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),text
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text())
    assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    result['private_receipt']=str(receipt);(ROOT/'output/foot-contacts-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checks':result['checks'],'failures':0,'rigs':list(result['reports']),'folder':str(folder)},indent=2))
if __name__=='__main__':main()
