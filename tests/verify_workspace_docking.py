"""Actual mouse docking, native tool window and cold layout persistence."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/workspace-docking'/str(time.time_ns());folder.mkdir(parents=True)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','data','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    reports={};receipts=[]
    for mode in ['writer','reader']:
        args=command('tests/workspace_docking_smoke.gd',extra=['--',str(folder)]+(['--read'] if mode=='reader' else []))
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=160)
        log=p.stdout+p.stderr;(folder/(mode+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and 'WORKSPACE_DOCKING ' in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads((folder/(mode+'.json')).read_bytes());assert report['failures']==0;reports[mode]=report
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(receipt))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
    result={'reports':reports,'private_receipts':receipts,'source_unchanged':True,'folder':str(folder)}
    (ROOT/'output/workspace-docking-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
