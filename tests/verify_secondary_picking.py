"""Current-bone source bounds, routed click correction and camera/patch gestures."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/'tests'))
import run
from test_secondary_helpers import fixture, request
import secondary_helpers as helpers


def main():
    folder = ROOT/'output/secondary-picking'/str(time.time_ns())
    folder.mkdir(parents=True)
    source_paths = sorted([*ROOT.glob('src/*.gd'),*ROOT.glob('src/*.gdshader'),
        ROOT/'main.tscn',ROOT/'project.godot',Path(__file__),
        ROOT/'tests/secondary_pick_unit.gd',ROOT/'tests/secondary_pick_smoke.gd'])
    source_hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    (folder/'source-sha256.json').write_text(json.dumps(source_hashes,indent=2)+'\n',encoding='utf-8')
    proofs = {}
    for label, script, headless in [
            ('unit', 'secondary_pick_unit.gd', True),
            ('smoke', 'secondary_pick_smoke.gd', False)]:
        source = folder/'original.glb'
        if not source.exists(): fixture(source)
        derived = helpers.build(source,folder/'derived',request(helpers.GLB(source))) if not headless else None
        original = (hashlib.sha256(source.read_bytes()).hexdigest(), source.stat().st_mtime_ns)
        args = run.command('tests/'+script, headless=headless,
            extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),
                   '--',str(folder),str(source)]+([derived['glb']] if derived else []))
        with (folder/(label+'-stdout.log')).open('w',encoding='utf-8') as log:
            proc = subprocess.run(args,cwd=ROOT,stdout=log,stderr=log,timeout=115)
        text = (folder/(label+'-stdout.log')).read_text(encoding='utf-8',errors='replace')
        if proc.returncode or any(s in text for s in ['SCRIPT ERROR','SHADER ERROR','ERROR:','FAIL ','ObjectDB instances leaked']):
            raise RuntimeError(f'{label} failed; inspect {folder}')
        if headless:
            line = next(x for x in text.splitlines() if x.startswith('SECONDARY_PICK_UNIT '))
            result = json.loads(line.split(' ',1)[1])
        else: result = json.loads((folder/'result.json').read_bytes())
        assert result['failures']==0
        receipt = None
        if os.name=='nt' and not headless:
            receipt = json.loads(Path(args[args.index('--receipt')+1]).read_bytes())
            assert (receipt['exit']==0 and receipt['child_desktop_confirmed'] and
                    not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'])
        assert original==(hashlib.sha256(source.read_bytes()).hexdigest(),source.stat().st_mtime_ns)
        proofs[label] = {'result':result,'private_receipt':receipt}
    assert source_hashes=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}, 'Source changed during the picking experiment'
    (folder/'verification.json').write_text(json.dumps(proofs,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'folder':str(folder),**proofs},indent=2))


if __name__=='__main__': main()
