from pathlib import Path
import array
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import wave
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def run(args,log,marker,timeout=180):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    data=result.stdout+result.stderr;log.write_bytes(data)
    assert result.returncode==0 and marker.encode() in data and not any(s in data for s in (b'SCRIPT ERROR',b'SHADER ERROR',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
    if '--receipt' in args:
        receipt=Path(args[args.index('--receipt')+1]);value=json.loads(receipt.read_bytes())
        assert value['exit']==0 and value['child_desktop_confirmed'] and not value['foreground_child_observed'] and value['job_closed'] and value['desktop_closed']
        return str(receipt)
    return None

if __name__=='__main__':
    folder=ROOT/'output/audio-trim'/str(time.time_ns());folder.mkdir(parents=True)
    prior=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output/checkpoints/2026-11-04-015322-mp3-ogg-audio/development-source.zip')
    assert hashlib.sha256(prior.read_bytes()).hexdigest()=='307b7af6e78ac5489ab9eb04ffe0374b9bcfbae2cfff14e66781037837820993'
    with zipfile.ZipFile(prior) as z:(folder/'legacy_audio.gd').write_bytes(z.read('src/audio_track.gd'))
    run(command('tests/audio_trim_unit.gd',headless=True,extra=['--',str(folder/'legacy_audio.gd')]),folder/'unit.log','AUDIO_TRIM_UNIT ')
    run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_has_project.py'],folder/'container.log','OK')
    originals={}
    for name,frequency,amplitude,seconds in [('voice.wav',1000,12000,2),('peer.wav',1500,4000,.5)]:
        data=array.array('h',(round(amplitude*math.sin(2*math.pi*frequency*i/44100)) for i in range(round(44100*seconds))))
        if sys.byteorder!='little':data.byteswap()
        with wave.open(str(folder/name),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(data.tobytes())
        originals[name]=hashlib.sha256((folder/name).read_bytes()).hexdigest()
    receipts=[]
    for mode in ['writer','packed','linked','recovery','lesson']:
        path=run(command('tests/audio_trim_smoke.gd',extra=['--',str(folder),mode]),folder/(mode+'.log'),'AUDIO_TRIM_SMOKE ' if mode=='writer' else 'AUDIO_TRIM_READ ')
        receipts.append(path)
    report=json.loads((folder/'app-result.json').read_bytes())
    ffmpeg=os.environ.get('HYBRID_FFMPEG',r'C:\Program Files\ffmpeg\bin\ffmpeg.exe');probe=str(Path(ffmpeg).with_name('ffprobe.exe'))
    p=subprocess.run([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],capture_output=True,check=True)
    (folder/'ffprobe.json').write_bytes(p.stdout);media=json.loads(p.stdout)
    video=next(s for s in media['streams'] if s['codec_type']=='video');audio=next(s for s in media['streams'] if s['codec_type']=='audio')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert audio['codec_name']=='aac' and abs(float(media['format']['duration'])-2)<.001
    p=subprocess.run([ffmpeg,'-v','error','-i',report['movie'],'-vn','-ac','2','-ar','48000','-f','s16le','-'],capture_output=True,check=True)
    data=array.array('h');data.frombytes(p.stdout)
    if sys.byteorder!='little':data.byteswap()
    def amplitude(at,frequency):
        samples=data[round(at*48000)*2:round((at+.1)*48000)*2:2];count=len(samples)
        return 2*abs(sum(value*complex(math.cos(2*math.pi*frequency*i/48000),math.sin(2*math.pi*frequency*i/48000)) for i,value in enumerate(samples)))/count
    levels={'voice':amplitude(.4,1000),'voice_after_trim':amplitude(.85,1000),'peer':amplitude(1.1,1500),'voice_during_peer':amplitude(1.1,1000)}
    assert 10500<levels['voice']<13000 and levels['voice_after_trim']<100 and 3300<levels['peer']<4700 and levels['voice_during_peer']<100,levels
    assert originals=={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in originals}
    report.update(folder=str(folder),private_receipts=receipts,original_inputs_unchanged=True,decoded_magnitudes=levels,fresh_readers=['packed','linked','recovery','lesson'])
    (ROOT/'output/audio-trim-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS non-destructive audio end trim, old-reader refusal, Undo/restore, waveform, fresh HAS/recovery/lesson and timed AAC movie')
