from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from test_mmd_motion import fixture

if __name__=='__main__':
    folder=ROOT/'output/mmd-motion-progress'/str(time.time_ns());folder.mkdir(parents=True)
    source=Path(json.loads((ROOT/'output/native-import-verification.json').read_bytes())['bundles'][0])/'scene.glb'
    original=hashlib.sha256(source.read_bytes()).hexdigest()
    motion=folder/'original.vmd';motion.write_bytes(fixture())
    (folder/'request.json').write_text(json.dumps({'source':str(source),'motion':str(motion)}),encoding='utf-8')
    args=command('tests/mmd_motion_progress_smoke.gd',extra=['--',str(folder)])
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=150,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    log=result.stdout+result.stderr;(folder/'app.log').write_bytes(log)
    assert result.returncode==0 and b'MMD_MOTION_PROGRESS ' in log and not any(marker in log for marker in (b'SCRIPT ERROR',b'SHADER ERROR',b'ObjectDB instances leaked')),log.decode('utf-8',errors='replace')
    receipt=Path(args[args.index('--receipt')+1]);desktop=json.loads(receipt.read_bytes())
    assert desktop['exit']==0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==original and motion.read_bytes()==fixture()
    report=json.loads((folder/'app-result.json').read_bytes());report.update(folder=str(folder),private_receipt=str(receipt),original_input_unchanged=True)
    (ROOT/'output/mmd-motion-progress-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS 241-frame motion candidate across editor frames, cancellation, stale seek, exact samples and Undo')
