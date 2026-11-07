"""Measure ordinary eager/adaptive Studio Open/seek latency and exact preview pixels."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicitly provisioned --isolated-display')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/cel-raster-app-benchmark'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    args=command('tests/cel_raster_app_benchmark.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'engine.log'),'--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=430,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);log=p.stdout+p.stderr;(folder/'run.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'CEL_RASTER_APP_BENCHMARK ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    proof=json.loads((folder/'verification.json').read_bytes());assert proof['ok']
    if os.name=='nt':
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];proof['private_receipt']=str(path)
    proof['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/app.gd','src/cel_raster_reader.gd','src/storage.gd','src/drawing.gd','src/drawing_overlay_cache.gd','tests/cel_raster_app_benchmark.gd']};proof['isolated_display']=options.isolated_display
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
