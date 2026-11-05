from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,engine_path
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--native-project',type=Path);options=parser.parse_args()
    folder=ROOT/'output/orbit-navigation'/str(time.time_ns());folder.mkdir(parents=True);receipts=[]
    for label,script in [('app','src/app.gd'),('test','tests/orbit_navigation_smoke.gd')]:
        p=subprocess.run([engine_path(),'--headless','--path',str(ROOT),'--check-only','--script',script,'--log-file',str(folder/(label+'-parse.log'))],cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
        raw=p.stdout+p.stderr;assert p.returncode==0 and b'SCRIPT ERROR' not in raw,raw.decode('utf-8',errors='replace')
    native=options.native_project
    if native is None:
        cases=json.loads((ROOT/'output/joint-authoring-verification.json').read_bytes())['cases'];native=Path(next(c['project'] for c in cases if c['label']=='miku'))
    native_hash=hashlib.sha256(native.read_bytes()).hexdigest();(folder/'native.has').write_bytes(native.read_bytes())
    for mode in ['writer','reader']:
        args=command('tests/orbit_navigation_smoke.gd',extra=['--',str(folder),*(['--read'] if mode=='reader' else [])])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
        data=p.stdout+p.stderr;(folder/(mode+'.log')).write_bytes(data)
        assert p.returncode==0 and b'ORBIT_NAVIGATION_' in data and not any(x in data for x in (b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    report=json.loads((folder/'result.json').read_bytes());assert report['failures']==0
    assert hashlib.sha256(native.read_bytes()).hexdigest()==native_hash
    report.update(folder=str(folder),private_receipts=receipts,native_project_unchanged=True);(ROOT/'output/orbit-navigation-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS optional orbit/pan/dolly, legacy fly default, native pose/key isolation, release guards and fresh preference restore')
