"""Explicit Local/World simulation capture, portable replay and real H264/AAC output."""
from pathlib import Path
import array, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command

def run(script,headless=False,timeout=180):
    p=subprocess.run(command(script,headless),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr
    (ROOT/'output'/f'{Path(script).stem}-verification.log').write_text(text,encoding='utf-8')
    if p.returncode or '"failures":0' not in text or any(x in text for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):
        raise RuntimeError(text)
    return text

def main():
    print(run('tests/physics_recording_unit.gd',True),flush=True)
    print(run('tests/physics_recording_smoke.gd'),flush=True)
    report=json.loads((ROOT/'output/physics-recording-result.json').read_text(encoding='utf-8'))
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],text=True,encoding='utf-8'))
    video=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(probe['format']['duration'])-2)<0.001
    assert any(x['codec_name']=='aac' for x in probe['streams'])==report['audio']
    if report['audio']:
        pcm=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',report['movie'],'-vn','-f','s16le','-ac','1','-ar','48000','pipe:1'])
        samples=array.array('h');samples.frombytes(pcm)
        if sys.byteorder!='little':samples.byteswap()
        onset=next(i for i,value in enumerate(samples) if abs(value)>1000)/48000
        assert abs(onset-1)<0.002,onset
        report['audio_onset_seconds']=onset
    report['video']={'codec':'h264','width':1920,'height':1080,'fps':'24/1','frames':48,'duration':probe['format']['duration']}
    (ROOT/'output/physics-recording-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
