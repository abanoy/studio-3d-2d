"""Actual Windows metadata writes, mixed separators and containment/link guards."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        parser.error('These filesystem observations require Windows.')
    folder=(options.output or ROOT/'output/private-metadata-windows'/str(time.time_ns())).resolve()
    assert folder.is_relative_to(ROOT/'output') and not folder.exists()
    folder.mkdir(parents=True)
    base=folder/'owned metadata — тест';base.mkdir()
    original=folder/'sentinel.json';original.write_bytes(b'ORIGINAL OWNED SENTINEL')
    identity=hashlib.sha256(original.read_bytes()).hexdigest()
    hard=base/'hard-primary.json';os.link(original,hard)
    assert hard.stat().st_nlink==original.stat().st_nlink==2
    outside=folder/'outside-managed';outside.mkdir()
    outside_file=outside/'progress.json';outside_file.write_bytes(b'OUTSIDE DECLARED OWNER')
    outside_hash=hashlib.sha256(outside_file.read_bytes()).hexdigest()
    junction=base/'redirect'
    linked=subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(junction),str(outside)],
                          capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
    assert linked.returncode==0 and junction.is_junction(),linked.stdout+linked.stderr
    unavailable=[]
    for target in (base/'primary-link.json',base/'temporary-link.json.tmp'):
        try:os.symlink(original,target)
        except OSError as error:unavailable.append({'path':str(target),'reason':str(error)})
    source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for area in ('src','tests','tools','data','examples') for p in (ROOT/area).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    args=command('tests/private_metadata_windows_unit.gd',headless=True,extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=100)
    raw=p.stdout+p.stderr;(folder/'engine.log').write_bytes(raw)
    assert p.returncode==0 and b'PRIVATE_METADATA_WINDOWS ' in raw and not any(x in raw for x in (b'SCRIPT ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
    report=json.loads((folder/'result.json').read_bytes());assert report['failures']==0 and report['checks']>=13
    assert hashlib.sha256(original.read_bytes()).hexdigest()==identity and original.stat().st_nlink==1
    assert json.loads(hard.read_bytes())=={'saved':12}
    assert hashlib.sha256(outside_file.read_bytes()).hexdigest()==outside_hash
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==digest for n,digest in source.items())
    report.update(folder=str(folder),original_preserved=True,hard_link_replaced_without_changing_original=True,
                  junction_target_preserved=True,unavailable_link_fixtures=unavailable,source_unchanged=True,scope='Actual Windows filesystem; headless, no graphical app window.')
    (ROOT/'output/private-metadata-windows-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
