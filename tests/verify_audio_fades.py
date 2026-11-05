from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def run(args,log,marker,timeout=170):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
    raw=p.stdout+p.stderr;log.write_bytes(raw)
    assert p.returncode==0 and marker.encode() in raw and not any(s in raw for s in (b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--previous-audio',type=Path);options=parser.parse_args()
    folder=ROOT/'output/audio-fades'/str(time.time_ns());folder.mkdir(parents=True)
    if options.previous_audio:(folder/'previous_audio.gd').write_bytes(options.previous_audio.read_bytes())
    else:
        prior=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output/checkpoints/2026-11-04-035230-joint-sound-review/development-source.zip')
        with zipfile.ZipFile(prior) as z:(folder/'previous_audio.gd').write_bytes(z.read('src/audio_track.gd'))
    run(command('tests/audio_fade_unit.gd',headless=True,extra=['--',str(folder/'previous_audio.gd')]),folder/'unit.log','"failures":0')
    originals={}
    for name,freq,amp,seconds in [('voice.wav',1000,12000,1),('peer.wav',1500,4000,.5)]:
        data=array.array('h',(round(amp*math.sin(2*math.pi*freq*i/44100)) for i in range(round(seconds*44100))))
        if sys.byteorder!='little':data.byteswap()
        with wave.open(str(folder/name),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(data.tobytes())
        originals[name]=hashlib.sha256((folder/name).read_bytes()).hexdigest()
    args=command('tests/audio_fade_smoke.gd',extra=['--',str(folder)]);run(args,folder/'app.log','AUDIO_FADE_SMOKE ')
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    receipts=[str(receipt)]
    for mode in ('packed','linked','recovery','lesson'):
        args=command('tests/audio_fade_smoke.gd',extra=['--',str(folder),mode]);run(args,folder/(mode+'.log'),'AUDIO_FADE_READ ')
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    result=json.loads((folder/'result.json').read_bytes())
    roundtrip=json.loads((folder/'roundtrip.json').read_bytes());assert roundtrip['expected']==roundtrip['actual'] and roundtrip['expected_pcm']==roundtrip['actual_pcm']
    p=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],capture_output=True,check=True);(folder/'ffprobe.json').write_bytes(p.stdout);meta=json.loads(p.stdout);v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and any(s.get('codec_name')=='aac' for s in meta['streams']) and abs(float(meta['format']['duration'])-2)<.001
    raw=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',result['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','-']);data=array.array('h');data.frombytes(raw)
    if sys.byteorder!='little':data.byteswap()
    def amplitude(at,frequency):
        values=data[round(at*48000):round((at+.02)*48000)];return 2*abs(sum(v*complex(math.cos(2*math.pi*frequency*i/48000),math.sin(2*math.pi*frequency*i/48000)) for i,v in enumerate(values)))/len(values)
    levels={name:amplitude(at,freq) for name,at,freq in [('in',.27,1000),('full',.4,1000),('out',.65,1000),('after',.8,1000),('peer',1.1,1500)]}
    assert 2500<levels['in']<5000 and 10500<levels['full']<13000 and 4500<levels['out']<6500 and levels['after']<100 and 3300<levels['peer']<4700,levels
    assert originals=={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in originals}
    result.update(folder=str(folder),private_receipt=str(receipt),private_receipts=receipts,decoded_magnitudes=levels,original_inputs_unchanged=True,fresh_readers=['packed','linked','recovery','lesson'])
    (ROOT/'output/audio-fades-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS sound fades: exact PCM boundaries, Undo, stale edits, trimmed packed HAS, preview/movie pixels and decoded AAC ramps')
