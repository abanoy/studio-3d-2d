"""Direct limb IK, native hand-foot posing and synchronized MP4."""
from pathlib import Path
import argparse
import array
import hashlib
import os
import json
import math
import subprocess
import sys
import time
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command, configure_private_display


def run(args):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
    text=p.stdout+p.stderr
    if p.returncode or any(x in text for x in ('SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child')):raise RuntimeError(text)
    return text


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    evidence=(options.output or ROOT/'output/limb-ik-evidence'/str(time.time_ns())).resolve();evidence.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    ffmpeg=Path(os.environ.get('HYBRID_FFMPEG',r'C:\Program Files\ffmpeg\bin\ffmpeg.exe' if os.name=='nt' else '/usr/bin/ffmpeg'));ffprobe=ffmpeg.with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
    fixtures=ROOT/'output/fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    wav=fixtures/'voice — тест.wav'
    if not wav.exists():
        samples=array.array('h',(int(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(wav),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
    args=command('tests/limb_ik_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(evidence/'engine.log')]);text=run(args)
    (evidence/'app.log').write_text(text,encoding='utf-8')
    (ROOT/'output/limb-ik-verification.log').write_text(text,encoding='utf-8')
    if 'LIMB_IK ' not in text or '"failures":0' not in text:raise RuntimeError(text)
    report=json.loads((ROOT/'output/limb-ik-result.json').read_text(encoding='utf-8'))
    probe=json.loads(run([str(ffprobe),'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert any(s['codec_name']=='aac' for s in probe['streams']) and abs(float(probe['format']['duration'])-2)<0.001
    decoded=subprocess.run([str(ffmpeg),'-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],capture_output=True,check=True)
    pcm=array.array('h');pcm.frombytes(decoded.stdout)
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000)/48000
    assert abs(onset-1)<0.002,onset
    report['video']={'codec':'h264','width':1920,'height':1080,'frames':48,'fps':'24/1','duration':probe['format']['duration'],'audio':'aac','onset':onset}
    (ROOT/'output/limb-ik-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
    report['source_sha256']=frozen;report['isolated_display']=options.isolated_display
    if os.name=='nt':
        receipt=Path(args[args.index('--receipt')+1]);proof=json.loads(receipt.read_bytes());assert proof['exit']==0 and proof['child_desktop_confirmed'] and not proof['foreground_child_observed'] and proof['job_closed'] and proof['desktop_closed'];report['private_receipt']=str(receipt)
    (evidence/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()
