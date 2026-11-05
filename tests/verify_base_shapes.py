"""Actual static shape controls, transactional geometry, helper/HAS/export proof."""
from pathlib import Path
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare
import hashlib


def main():
    folder=ROOT/'output/base-shapes'/str(time.time_ns());folder.mkdir(parents=True)
    originals=prepare(folder)
    cmd=command('tests/base_shape_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    if p.returncode or 'BASE_SHAPES ' not in log or any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']):raise RuntimeError(log)
    result=json.loads((folder/'base-result.json').read_text(encoding='utf-8'));assert result['failures']==0
    for path,expected in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==expected
    p=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],capture_output=True,text=True,check=True)
    video=next(s for s in json.loads(p.stdout)['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.000001
    receipt=json.loads(Path(cmd[3]).read_text(encoding='utf-8'))
    assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result.update(folder=str(folder),private_receipt=cmd[3]);(ROOT/'output/base-shapes-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
