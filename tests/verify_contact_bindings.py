"""Compiled contact-chain safety, native pose identity, and bounded dense HAS world."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    source=Path(sys.argv[1]) if len(sys.argv)>1 else Path(json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['folder'])
    folder=ROOT/'output/contact-bindings'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/contact_binding_smoke.gd',extra=['--',str(source),str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=170);text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'CONTACT_BINDINGS ' in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),text
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];result['private_receipt']=str(receipt);(ROOT/'output/contact-bindings-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
