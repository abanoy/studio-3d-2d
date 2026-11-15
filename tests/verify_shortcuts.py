"""Actual keyboard-capture/editor and fresh preferences checks, hidden on Windows."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(o.isolated_display)
    folder=(o.output or ROOT/'output/shortcuts'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    receipts=[];reports={}
    for label,script,headless,extra in [('unit','tests/shortcut_bindings_unit.gd',True,[]),('writer','tests/shortcut_editor_smoke.gd',False,['--',str(folder)]),('reader','tests/shortcut_editor_smoke.gd',False,['--',str(folder),'--read']),('invalid','tests/shortcut_editor_smoke.gd',False,['--',str(folder),'--invalid'])]:
        args=command(script,headless,extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+extra)
        p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=170,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        raw=p.stdout+p.stderr;(folder/(label+'.log')).write_bytes(raw)
        assert p.returncode==0 and b'SHORTCUT_' in raw and not any(x in raw for x in [b'ERROR:',b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked']),raw.decode('utf-8',errors='replace')
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
        marker={'unit':'SHORTCUT_BINDINGS_UNIT ','writer':'SHORTCUT_EDITOR_SMOKE ','reader':'SHORTCUT_EDITOR_READ ','invalid':'SHORTCUT_EDITOR_INVALID '}[label]
        line=next(row for row in raw.decode('utf-8',errors='replace').splitlines() if row.startswith(marker));reports[label]=json.loads(line[len(marker):]);assert reports[label]['failures']==0
    with zipfile.ZipFile(folder/'Keyboard scene.has') as z:
        manifests=[json.loads(z.read(n)) for n in z.namelist() if n.endswith('.json')]
        assert not any('shortcuts' in json.dumps(m) or 'personal.cfg' in json.dumps(m) for m in manifests)
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
    result={'folder':str(folder),'reports':reports,'private_receipts':receipts,'personal_keys_absent_from_has':True,'source_sha256':frozen,'isolated_display':o.isolated_display}
    (folder/'verification.json').write_text(json.dumps(result,indent=2))
    (ROOT/'output/shortcuts-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!="source_sha256"},indent=2))

if __name__=='__main__':main()
