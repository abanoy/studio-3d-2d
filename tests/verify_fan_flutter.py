"""Native/included fan aiming, continuous flutter and immutable owner input."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
folder=ROOT/'output/fan-flutter'/str(time.time_ns());folder.mkdir(parents=True)
project=os.environ.get('HYBRID_FAN_PROJECT');originals={}
if project:
    source=Path(project).resolve(strict=True);assert source.is_dir() and (source/'project.json').is_file()
    originals={p:(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in source.rglob('*') if p.is_file()}
    assert all(not p.is_symlink() for p in originals)
    shutil.copytree(source,folder/'input')
frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
args=command('tests/fan_flutter_smoke.gd',extra=['--',str(folder)]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=230)
log=p.stdout+p.stderr;(folder/'app.log').write_text(log,encoding='utf-8');assert p.returncode==0 and 'FAN_FLUTTER ' in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
report=json.loads((folder/'result.json').read_bytes());assert report['failures']==0
receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==sha for p,sha in frozen.items())
assert all((hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)==state for p,state in originals.items())
report.update(folder=str(folder),private_receipt=str(receipt),native_input=bool(project),source_and_originals_unchanged=True)
(ROOT/'output/fan-flutter-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
