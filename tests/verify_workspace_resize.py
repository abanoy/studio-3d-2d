"""Actual private Windows UI: resize the scene with routed mouse drags."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/workspace-resize'/str(time.time_ns());folder.mkdir(parents=True)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for directory in ['src','tests','tools','data','examples']for p in(ROOT/directory).rglob('*')if p.is_file()and p.suffix!='.pyc'and '__pycache__'not in p.parts}
    project=os.environ.get('HYBRID_WORKSPACE_PROJECT')
    extra=['--',str(folder)]+([str(Path(project).resolve(strict=True))] if project else [])
    args=command('tests/workspace_resize_smoke.gd',extra=extra)
    process=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=310)
    log=process.stdout+process.stderr;(folder/'app.log').write_text(log,encoding='utf-8')
    assert process.returncode==0 and 'WORKSPACE_RESIZE 'in log and '"failures":0'in log and not any(text in log for text in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    receipt=Path(args[args.index('--receipt')+1]);private=json.loads(receipt.read_text(encoding='utf-8'))
    assert private['exit']==0 and private['child_desktop_confirmed']and not private['foreground_child_observed']and private['job_closed']and private['desktop_closed'],private
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));result.update(folder=str(folder),private_receipt=str(receipt),functional_unchanged=True)
    (ROOT/'output/workspace-resize-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

