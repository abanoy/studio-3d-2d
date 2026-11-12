"""Projected ring gesture directions and actual inner-frame overlay clipping."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/rotation-gizmo'/str(time.time_ns());folder.mkdir(parents=True)
    sources=[ROOT/'src/pose_editor.gd',ROOT/'src/canvas_view.gd',ROOT/'tests/rotation_gizmo_smoke.gd']
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    args=command('tests/rotation_gizmo_smoke.gd',extra=['--log-file',str(folder/'engine.log'),'--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
    log=p.stdout+p.stderr;(folder/'app.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'ROTATION_GIZMO ' in log and not any(x in log for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),log
    result=json.loads((ROOT/'output/rotation-gizmo-result.json').read_bytes());assert result['failures']==0 and len(result['cases'])==24,result
    if os.name=='nt':
        receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes())
        assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
        result['private_receipt']=receipt
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in frozen.items())
    result['source_sha256']=frozen
    (ROOT/'output/rotation-gizmo-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
