from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
 folder=ROOT/'output/scout-grab'/str(time.time_ns());folder.mkdir(parents=True)
 args=command('tests/scout_grab_smoke.gd',extra=['--',str(folder)])
 run=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=75)
 log=run.stdout+run.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
 assert run.returncode==0 and 'SCOUT_GRAB ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
 result=json.loads((folder/'result.json').read_text());receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text())
 assert result['failures']==0 and r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
 result.update(folder=str(folder),private_receipt=str(receipt))
 (ROOT/'output/scout-grab-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
