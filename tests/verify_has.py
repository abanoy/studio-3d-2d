from pathlib import Path
import array
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command

def run(args,timeout=180):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr
    if p.returncode:raise RuntimeError(text)
    return text

def main():
    print(run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_has_project.py']))
    text=run(command('tests/has_smoke.gd'))
    (ROOT/'output/has-verification.log').write_text(text,encoding='utf-8')
    if 'HAS_SMOKE ' not in text or '"failures":0' not in text or any(x in text for x in ('SCRIPT ERROR','FAIL ','ObjectDB instances leaked','another exclusive child')):raise RuntimeError(text)
    r=json.loads((ROOT/'output/has-result.json').read_text(encoding='utf-8'))
    probe=json.loads(run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',r['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1')
    assert any(s['codec_name']=='aac' for s in probe['streams'])
    decoded=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',r['movie'],'-vn','-f','s16le','-ac','1','-ar','48000','pipe:1'],capture_output=True,check=True)
    samples=array.array('h');samples.frombytes(decoded.stdout)
    if sys.byteorder!='little':samples.byteswap()
    onset=next(i for i,x in enumerate(samples) if abs(x)>1000)/48000
    assert abs(onset-1)<0.002,onset
    r['video']=video
    r['audio_onset_seconds']=onset
    (ROOT/'output/has-verification.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='video'},indent=2))

if __name__=='__main__':main()
