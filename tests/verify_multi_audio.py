"""Actual multi-clip editing, native world, cold HAS/recovery/lesson and movies."""
from pathlib import Path
import array,ast,hashlib,json,math,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    folder=ROOT/'output/multi-audio'/str(time.time_ns());folder.mkdir(parents=True)
    inputs=folder/'inputs';inputs.mkdir()
    for name,rate,channels,seconds,frequencies,amplitudes in [
        ('Voice — тест.wav',44100,1,.5,[1000],[16000]),
        ('Music.wav',48000,2,2,[600,900],[8000,6000]),
        ('Effect.wav',48000,1,1.2,[1500],[4000]),
    ]:
        samples=array.array('h',(round(amplitudes[c]*math.sin(2*math.pi*frequencies[c]*n/rate))for n in range(round(rate*seconds))for c in range(channels)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(inputs/name),'wb')as wav:wav.setparams((channels,2,rate,0,'NONE','not compressed'));wav.writeframes(samples.tobytes())
    originals={p.name:sha(p)for p in inputs.iterdir()}
    functional={str(p.relative_to(ROOT)):sha(p)for directory in ['src','tests','tools','data','examples']for p in (ROOT/directory).rglob('*')if p.is_file()and p.suffix!='.pyc'and '__pycache__'not in p.parts}
    (folder/'functional-inputs.json').write_text(json.dumps(functional,indent=2),encoding='utf-8')
    receipts=[]
    def run(args,label,marker,timeout=310):
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout);log=p.stdout+p.stderr
        (folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),log
        if '--receipt'in args:
            path=Path(args[args.index('--receipt')+1]);receipt=read(path)
            assert receipt['exit']==0 and receipt['child_desktop_confirmed']and not receipt['foreground_child_observed']and receipt['job_closed']and receipt['desktop_closed'],receipt
            receipts.append(str(path))
        return log
    run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_has_project.py'],'container','OK')
    run(command('tests/multi_audio_unit.gd',headless=True),'unit','MULTI_AUDIO_UNIT ')
    reference=read(ROOT/'output/contact-persistence-verification.json')['writer']['packed'];reference_hash=sha(reference)
    run(command('tests/multi_audio_smoke.gd',extra=['--',str(folder),'writer',reference]),'writer','MULTI_AUDIO ')
    writer=read(folder/'writer.json');assert writer['failures']==0
    saved={name:sha(writer[name])for name in ['packed','linked']}
    readers={}
    for mode in ['packed','linked','recovery','lesson']:
        run(command('tests/multi_audio_smoke.gd',extra=['--',str(folder),mode]),mode,'MULTI_AUDIO_READ ')
        readers[mode]=read(folder/('reader-'+mode+'.json'));assert readers[mode]['failures']==0
    media=[]
    for movie in [writer['movie'],readers['packed']['movie']]:
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',movie],text=True,encoding='utf-8'))
        video=next(s for s in probe['streams']if s['codec_type']=='video');audio=next(s for s in probe['streams']if s['codec_type']=='audio')
        assert(video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
        assert audio['codec_name']=='aac'and abs(float(probe['format']['duration'])-2)<.001
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',movie,'-vn','-f','s16le','-ac','2','-ar','48000','-']);pcm=array.array('h');pcm.frombytes(raw)
        if sys.byteorder!='little':pcm.byteswap()
        def magnitude(at,frequency,channel):
            values=pcm[round(at*48000)*2+channel:round((at+.1)*48000)*2:2];count=len(values)
            real=sum(value*math.cos(2*math.pi*frequency*i/48000)for i,value in enumerate(values));imag=sum(value*math.sin(2*math.pi*frequency*i/48000)for i,value in enumerate(values))
            return 2*math.hypot(real,imag)/count
        sound={'music_left':magnitude(1.1,600,0),'music_right':magnitude(1.1,900,1),'voice':magnitude(1.1,1000,0),'effect':magnitude(1.1,1500,0),'early_voice':magnitude(.8,1000,0),'early_effect':magnitude(.8,1500,0)}
        assert 1700<sound['music_left']<2300 and 1200<sound['music_right']<1800 and 7200<sound['voice']<8800 and 1100<sound['effect']<1700,sound
        assert sound['early_voice']<100 and sound['early_effect']>1100,sound
        quiet=pcm[round(.1*48000)*2:round(.2*48000)*2];assert max(map(abs,quiet))<10
        onset=next(i//2 for i,value in enumerate(pcm)if abs(value)>300)/48000;assert abs(onset-.25)<.003,onset
        media.append({'movie':movie,'video':video,'audio':audio,'decoded_magnitudes':sound,'first_onset_seconds':onset})
    assert originals=={p.name:sha(p)for p in(folder/'inputs-held').iterdir()}
    assert sha(reference)==reference_hash and all(sha(writer[name])==digest for name,digest in saved.items())
    assert all(sha(ROOT/name)==digest for name,digest in functional.items())
    result={'folder':str(folder),'writer':writer,'readers':readers,'media':media,'private_receipts':receipts,'originals':originals,'functional_unchanged':True}
    (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/multi-audio-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
