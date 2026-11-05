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

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
from prepare_audio import prepare

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,log,timeout=180):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    content=result.stdout+result.stderr;log.write_bytes(content)
    assert result.returncode==0 and not any(s in content for s in (b'SCRIPT ERROR',b'SHADER ERROR',b'ObjectDB instances leaked')),content.decode('utf-8',errors='replace')
    return result.stdout
def tone(path,freq,amplitude=12000,seconds=.5,right=None):
    channels=[(freq,amplitude)]+([right] if right else [])
    samples=array.array('h',(round(level*math.sin(2*math.pi*frequency*i/44100)) for i in range(round(44100*seconds)) for frequency,level in channels))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(path),'wb') as out:out.setparams((len(channels),2,44100,0,'NONE','not compressed'));out.writeframes(samples.tobytes())

if __name__=='__main__':
    folder=ROOT/'output/compressed-audio'/str(time.time_ns());folder.mkdir(parents=True)
    ffmpeg=os.environ.get('HYBRID_FFMPEG',r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
    tone(folder/'base.wav',400,6000);tone(folder/'voice.wav',1000);tone(folder/'effect.wav',1500,8000,right=(1800,4000))
    for name,source,codec in [('Voice — тест.mp3','voice.wav','libmp3lame'),('Effect.ogg','effect.wav','libvorbis')]:
        run([ffmpeg,'-nostdin','-v','error','-i',str(folder/source),'-c:a',codec,str(folder/name)],folder/(name+'.encode.log'))
    (folder/'broken.mp3').write_bytes(b'Original malformed audio fixture. Not a stream.')
    originals={p.name:sha(p) for p in folder.iterdir() if p.suffix in ('.wav','.mp3','.ogg')}
    # Actual decoder failures must never publish a normalized audio file.
    errors={}
    for label,source,decoder,cancel in [('missing-decoder','Effect.ogg',str(folder/'missing.exe'),False),('bad-stream','broken.mp3',ffmpeg,False),('unsupported','base.wav',ffmpeg,False),('cancelled','Effect.ogg',ffmpeg,True)]:
        out=folder/label;out.mkdir();signal=out/'cancel'
        if cancel:signal.touch()
        try:prepare({'source':str(folder/source),'ffmpeg':decoder,'output':str(out/'audio.wav'),'cancel':str(signal)})
        except (OSError,ValueError,RuntimeError) as error:errors[label]=str(error)
        else:raise AssertionError(label+' should refuse')
        assert not (out/'audio.wav').exists() and not (out/'audio.partial.wav').exists()
    long=folder/'long.ogg'
    run([ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','sine=frequency=300:duration=62','-c:a','libvorbis',str(long)],folder/'long-encode.log')
    long_original=sha(long);out=folder/'long-refusal';out.mkdir()
    try:prepare({'source':str(long),'ffmpeg':ffmpeg,'output':str(out/'audio.wav'),'cancel':str(out/'cancel')})
    except ValueError as error:assert 'up to60seconds' in str(error);errors['overlong']=str(error)
    else:raise AssertionError('Long sound must not be silently truncated')
    assert not (out/'audio.wav').exists() and sha(long)==long_original
    args=command('tests/compressed_audio_smoke.gd',extra=['--',str(folder)])
    log=run(args,folder/'app.log');assert b'COMPRESSED_AUDIO ' in log
    receipt=Path(args[args.index('--receipt')+1]);desktop=json.loads(receipt.read_bytes())
    assert desktop['exit']==0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
    report=json.loads((folder/'app-result.json').read_bytes())
    probe=str(Path(ffmpeg).with_name('ffprobe.exe'))
    media=json.loads(run([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],folder/'ffprobe.json'))
    video=next(s for s in media['streams'] if s['codec_type']=='video');audio=next(s for s in media['streams'] if s['codec_type']=='audio')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert audio['codec_name']=='aac' and abs(float(media['format']['duration'])-2)<.001
    raw=run([ffmpeg,'-v','error','-i',report['movie'],'-vn','-ac','2','-ar','48000','-f','s16le','-'],folder/'decoded-output.pcm')
    samples=array.array('h');samples.frombytes(raw)
    if sys.byteorder!='little':samples.byteswap()
    def amplitude(at,frequency,channel=0):
        data=samples[round(at*48000)*2+channel:round((at+.1)*48000)*2:2];count=len(data)
        return 2*abs(sum(value*complex(math.cos(2*math.pi*frequency*i/48000),math.sin(2*math.pi*frequency*i/48000)) for i,value in enumerate(data)))/count
    levels={'wav':amplitude(.1,400),'mp3':amplitude(.6,1000),'ogg':amplitude(1.1,1500),'ogg_right':amplitude(1.1,1800,1),'ogg_right_leak':amplitude(1.1,1500,1),'early_mp3':amplitude(.3,1000),'early_ogg':amplitude(.8,1500)}
    assert 5000<levels['wav']<7000 and 10000<levels['mp3']<13000 and 6500<levels['ogg']<9500,levels
    assert levels['early_mp3']<100 and levels['early_ogg']<100,levels
    assert 3200<levels['ogg_right']<4800 and levels['ogg_right_leak']<100,levels
    assert max(map(abs,samples[round(1.7*48000)*2:round(1.8*48000)*2]))<10
    assert originals=={name:sha(folder/name) for name in originals}
    report.update(folder=str(folder),private_receipt=str(receipt),original_inputs_unchanged=True,refusals=errors,decoded_magnitudes=levels)
    (ROOT/'output/compressed-audio-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS MP3/Ogg normalization, picker/placement, cancel/failure/retry, Undo, packed/linked HAS, hardware/fallback playback and H264/AAC movie')
