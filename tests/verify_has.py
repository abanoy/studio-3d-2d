from pathlib import Path
import argparse,hashlib,math,os,time,wave
import array
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def run(args,timeout=180):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr
    if p.returncode:raise RuntimeError(text)
    return text

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/has-portable'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    tone=array.array('h',(round(16000*math.sin(2*math.pi*1000*i/44100)) for i in range(22050)))
    if sys.byteorder!='little':tone.byteswap()
    with wave.open(str(folder/'voice.wav'),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(tone.tobytes())
    print(run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_has_project.py']))
    args=command('tests/has_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'godot.log'),'--',str(folder)]);text=run(args)
    (folder/'engine.log').write_text(text,encoding='utf-8')
    (ROOT/'output/has-verification.log').write_text(text,encoding='utf-8')
    if 'HAS_SMOKE ' not in text or '"failures":0' not in text or any(x in text for x in ('SCRIPT ERROR','FAIL ','ObjectDB instances leaked','another exclusive child')):raise RuntimeError(text)
    r=json.loads((ROOT/'output/has-result.json').read_text(encoding='utf-8'))
    ffmpeg=os.environ.get('HYBRID_FFMPEG','C:/Program Files/ffmpeg/bin/ffmpeg.exe' if os.name=='nt' else '/usr/bin/ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    probe=json.loads(run([ffprobe,'-v','error','-count_frames','-show_streams','-of','json',r['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1')
    assert any(s['codec_name']=='aac' for s in probe['streams'])
    decoded=subprocess.run([ffmpeg,'-v','error','-i',r['movie'],'-vn','-f','s16le','-ac','1','-ar','48000','pipe:1'],capture_output=True,check=True)
    samples=array.array('h');samples.frombytes(decoded.stdout)
    if sys.byteorder!='little':samples.byteswap()
    onset=next(i for i,x in enumerate(samples) if abs(x)>1000)/48000
    assert abs(onset-1)<0.002,onset
    receipt=None
    if os.name=='nt':
        receipt=Path(args[args.index('--receipt')+1]);desktop=json.loads(receipt.read_bytes());assert desktop['exit']==0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
    r.update(source_sha256=frozen,isolated_display=options.isolated_display,private_receipt=str(receipt) if receipt else None,native_fidelity_certified=False)
    r['video']=video
    r['audio_onset_seconds']=onset
    (folder/'verification.json').write_text(json.dumps(r,indent=2)+'\n')
    (ROOT/'output/has-verification.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k not in ['video','source_sha256']},indent=2))

if __name__=='__main__':main()
