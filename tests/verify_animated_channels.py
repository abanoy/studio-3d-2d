"""Expanded animated channels, native selection, HAS/recovery and synchronized MP4."""
from pathlib import Path
import array
import json
import math
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command


def run(args):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
    text=p.stdout+p.stderr
    if p.returncode or any(x in text for x in ('SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked')):raise RuntimeError(text)
    return text


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    fixtures=ROOT/'output/fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    wav=fixtures/'voice — тест.wav'
    if not wav.exists():
        samples=array.array('h',(int(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(wav),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
    text=run(command('tests/animated_channels_smoke.gd'))
    (ROOT/'output/animated-channels-verification.log').write_text(text,encoding='utf-8')
    if 'ANIMATED_CHANNELS ' not in text or '"failures":0' not in text:raise RuntimeError(text)
    report=json.loads((ROOT/'output/animated-channels-result.json').read_text(encoding='utf-8'))
    probe=json.loads(run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert any(s['codec_name']=='aac' for s in probe['streams']) and abs(float(probe['format']['duration'])-2)<0.001
    decoded=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],capture_output=True,check=True)
    pcm=array.array('h');pcm.frombytes(decoded.stdout)
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000)/48000
    assert abs(onset-1)<0.002,onset
    report['video']={'codec':'h264','width':1920,'height':1080,'frames':48,'fps':'24/1','duration':probe['format']['duration'],'audio':'aac','onset':onset}
    (ROOT/'output/animated-channels-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
