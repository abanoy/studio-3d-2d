from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,engine_path,configure_private_display
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--native-project',type=Path);parser.add_argument('--original-only',action='store_true');parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if options.original_only and options.native_project:parser.error('Choose native project or explicit original-only scope')
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/orbit-navigation'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);receipts=[];reports={}
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    for label,script in [('app','src/app.gd'),('test','tests/orbit_navigation_smoke.gd')]:
        p=subprocess.run([engine_path(),'--headless','--path',str(ROOT),'--check-only','--script',script,'--log-file',str(folder/(label+'-parse.log'))],cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,timeout=30)
        raw=p.stdout+p.stderr;assert p.returncode==0 and b'SCRIPT ERROR' not in raw,raw.decode('utf-8',errors='replace')
    native=options.native_project
    if native is None and not options.original_only:
        cases=json.loads((ROOT/'output/joint-authoring-verification.json').read_bytes())['cases'];native=Path(next(c['project'] for c in cases if c['label']=='miku'))
    if native:
        native_hash=hashlib.sha256(native.read_bytes()).hexdigest();(folder/'native.has').write_bytes(native.read_bytes())
    for mode in ['writer','reader']:
        args=command('tests/orbit_navigation_smoke.gd',extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+['--',str(folder),*(['--read'] if mode=='reader' else []),*(['--original-only'] if options.original_only else [])])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        data=p.stdout+p.stderr;(folder/(mode+'.log')).write_bytes(data)
        assert p.returncode==0 and b'ORBIT_NAVIGATION_' in data and not any(x in data for x in (b'ERROR:',b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
        marker='ORBIT_NAVIGATION_READ ' if mode=='reader' else 'ORBIT_NAVIGATION_SMOKE '
        reports[mode]=json.loads(next(line[len(marker):] for line in data.decode('utf-8',errors='replace').splitlines() if line.startswith(marker)));assert reports[mode]['failures']==0
        if os.name=='nt':
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    report=json.loads((folder/'result.json').read_bytes());assert report['failures']==0
    if native:assert hashlib.sha256(native.read_bytes()).hexdigest()==native_hash
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
    report.update(reports=reports,folder=str(folder),private_receipts=receipts,native_project_unchanged=True if native else None,source_sha256=frozen,isolated_display=options.isolated_display,scope='Original fixture software navigation only; native checks explicitly unrun' if options.original_only else 'Includes provided prepared native model')
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'output/orbit-navigation-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
