import argparse,hashlib,os,time
"""Normal multi-object Add/Save/Open/New/Undo/recovery, with synchronized MP4 audio."""
from pathlib import Path
import array
import json
import math
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command as private_command,configure_private_display

EVIDENCE=None
RECEIPTS=[]
def command(script=None,headless=False,extra=()):
    return private_command(script,headless,extra=(["--audio-driver","Dummy"] if os.name!='nt' else [])+list(extra))
def desktop_receipt(args):
    if os.name=='nt' and '--receipt' in args:
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes())
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];RECEIPTS.append(str(path))



def run(args):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
    text=p.stdout+p.stderr
    if p.returncode or any(x in text for x in ('ERROR:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked')):raise RuntimeError(text)
    desktop_receipt(args)
    if EVIDENCE and '--script' in args:(EVIDENCE/(Path(args[args.index('--script')+1]).stem+'-'+str(time.time_ns())+'.log')).write_text(text,encoding='utf-8')
    return text


def main():
    global EVIDENCE
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    EVIDENCE=(options.output or ROOT/'output/private-world-tests'/str(time.time_ns())).resolve();EVIDENCE.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))

    sys.stdout.reconfigure(encoding='utf-8')
    fixtures=ROOT/'output/fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    wav=fixtures/'voice — тест.wav'
    if not wav.exists():
        samples=array.array('h',(int(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(wav),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
    text=run(command('tests/world_workflow_smoke.gd'))
    (ROOT/'output/world-workflow-verification.log').write_text(text,encoding='utf-8')
    if 'WORLD_WORKFLOW_SMOKE ' not in text or '"failures":0' not in text:raise RuntimeError(text)
    report=json.loads((ROOT/'output/world-workflow-result.json').read_text(encoding='utf-8'))
    probe=json.loads(run([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert any(s['codec_name']=='aac' for s in probe['streams']) and abs(float(probe['format']['duration'])-2)<0.001
    decoded=subprocess.run([ffmpeg,'-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],capture_output=True,check=True)
    pcm=array.array('h');pcm.frombytes(decoded.stdout)
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000)/48000
    assert abs(onset-1)<0.002,onset
    report['video']={'codec':'h264','width':1920,'height':1080,'frames':48,'fps':'24/1','duration':probe['format']['duration'],'audio':'aac','onset':onset}
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    report.update(source_sha256=frozen,isolated_display=options.isolated_display,private_receipts=RECEIPTS,scope='Original authored world and rig fixtures; native coverage only for explicitly available prepared samples, never inferred from generated fixtures.')
    (EVIDENCE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'output/world-workflow-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()
