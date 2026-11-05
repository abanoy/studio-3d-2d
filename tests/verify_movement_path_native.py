"""Private native path/contact editing with ordinary packed save/reopen."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    diagnostic=next((x for x in ['--diagnostic-order','--diagnostic-copy'] if x in sys.argv),'')
    label='native-path-'+diagnostic.removeprefix('--') if diagnostic else 'native-path-components'
    folder=ROOT/'output'/label/str(time.time_ns());folder.mkdir(parents=True)
    source=Path(json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['packed'])
    frozen={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in ['src','tests','tools','data','examples'] for p in (ROOT/d).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    frozen[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
    args=command('tests/movement_path_native.gd',extra=['--',str(folder),str(source)]+([diagnostic] if diagnostic else []))
    run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=210)
    log=run.stdout+run.stderr;(folder/'native.log').write_text(log,encoding='utf-8')
    result=json.loads((folder/'result.json').read_text());assert len(result['native_reports'])==5
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==run.returncode and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    result.update(folder=str(folder),private_receipt=str(receipt),source_unchanged=True,functional_unchanged=True,exit=run.returncode,ok=run.returncode==0 and result['failures']==0)
    (ROOT/'output'/(label+'-verification.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
    assert result['ok'] and 'PATH_NATIVE ' in log and not any(t in log for t in ['ERROR:','FAIL ','ObjectDB instances leaked']), 'Native path acceptance incomplete; see '+str(folder/'native.log')
if __name__=='__main__':main()
