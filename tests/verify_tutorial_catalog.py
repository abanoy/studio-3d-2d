"""Grouped Basic/Advanced entry points with existing course/checkpoint regressions."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicitly provisioned private display')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/tutorial-catalog'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    args=command('tests/tutorial_catalog_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'engine.log'),'--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=160,**flags);log=result.stdout+result.stderr;(folder/'browser.log').write_text(log,encoding='utf-8');marker='TUTORIAL_CATALOG_SMOKE '
    assert result.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    browser=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert browser['failures']==0
    receipts=[]
    if os.name=='nt':
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    regressions={}
    for name,script,proof in [('focused','verify_tutorials.py','tutorials-verification.json'),('beginner','verify_first_movie.py','first-movie-verification.json')]:
        args=[sys.executable,str(ROOT/'tests'/script)]+(['--isolated-display',options.isolated_display] if options.isolated_display else [])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=360,**flags);(folder/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stdout+result.stderr
        regressions[name]=json.loads((ROOT/'output'/proof).read_bytes())
    proof=dict(browser=browser,regressions=regressions,private_receipts=receipts,isolated_display=options.isolated_display,source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/tutorials.gd','src/tutorial_catalog.gd','src/lesson_store.gd','tests/tutorial_catalog_smoke.gd']})
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
