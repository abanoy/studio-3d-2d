"""Actual edited-cel idle release with exact Undo/Redo and scoped allocation evidence."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicitly provisioned --isolated-display')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/cel-raster-budget'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    domain=subprocess.run([sys.executable,str(ROOT/'tests/verify_cel_raster_snapshot.py'),'--output',str(folder/'domain')],cwd=ROOT,capture_output=True,text=True,timeout=90,**flags)
    (folder/'domain.log').write_text(domain.stdout+domain.stderr,encoding='utf-8');assert domain.returncode==0,domain.stdout+domain.stderr
    args=command('tests/cel_raster_budget_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'engine.log'),'--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240,**flags);log=result.stdout+result.stderr;(folder/'run.log').write_text(log,encoding='utf-8')
    assert result.returncode==0 and 'CEL_RASTER_BUDGET_SMOKE ' in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    proof=json.loads((folder/'verification.json').read_bytes());assert proof['failures']==0
    if os.name=='nt':
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];proof['private_receipt']=str(path)
    proof['domain']=json.loads((folder/'domain/verification.json').read_bytes());proof['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/app.gd','src/storage.gd','src/cel_raster_owner.gd','src/cel_raster_snapshot_cache.gd','src/cel_raster_budget.gd','tests/cel_raster_budget_smoke.gd']};proof['isolated_display']=options.isolated_display
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
