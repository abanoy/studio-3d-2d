"""Sparse multi-sound mixing: frozen PCM oracle, actual fade editing, cold storage and AAC."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicit private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/sparse-audio'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    reports={};receipts=[]
    def run(script,label,extra,marker,headless=False):
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+(['--',*extra] if extra else []))
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=220)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        if headless:
            report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[label]=report
        if os.name=='nt' and not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    for script,label,marker in [('audio_sparse_unit','sparse','AUDIO_SPARSE_UNIT '),('multi_audio_unit','multi','MULTI_AUDIO_UNIT '),('sequence_audio_unit','nested','SEQUENCE_AUDIO_UNIT ')]:
        run('tests/'+script+'.gd',label,[],marker,True)
    originals={}
    for name,frequency,amplitude,seconds in [('voice.wav',1000,12000,1),('peer.wav',1500,4000,.5)]:
        samples=array.array('h',(round(amplitude*math.sin(2*math.pi*frequency*i/44100)) for i in range(round(seconds*44100))))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(folder/name),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
        originals[name]=hashlib.sha256((folder/name).read_bytes()).hexdigest()
    run('tests/audio_fade_smoke.gd','writer',[str(folder)],'AUDIO_FADE_SMOKE ')
    result=json.loads((folder/'result.json').read_bytes());manual={Path(result['project']):Path(result['project']).read_bytes(),folder/'linked.has':(folder/'linked.has').read_bytes()}
    for mode in ['packed','linked','recovery','lesson']:run('tests/audio_fade_smoke.gd',mode,[str(folder),mode],'AUDIO_FADE_READ '+mode)
    assert all(p.read_bytes()==blob for p,blob in manual.items())
    roundtrip=json.loads((folder/'roundtrip.json').read_bytes());assert roundtrip['expected']==roundtrip['actual'] and roundtrip['expected_pcm']==roundtrip['actual_pcm']
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',result['movie']],**flags));video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and any(s['codec_name']=='aac' for s in media['streams']) and abs(float(media['format']['duration'])-2)<.001
    decoded=array.array('h');decoded.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',result['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':decoded.byteswap()
    def amplitude(at,frequency):
        values=decoded[round(at*48000):round((at+.02)*48000)]
        return 2*abs(sum(v*complex(math.cos(2*math.pi*frequency*i/48000),math.sin(2*math.pi*frequency*i/48000)) for i,v in enumerate(values)))/len(values)
    levels={name:amplitude(at,frequency) for name,at,frequency in [('in',.27,1000),('full',.4,1000),('out',.65,1000),('after',.8,1000),('peer',1.1,1500)]}
    assert 2500<levels['in']<5000 and 10500<levels['full']<13000 and 4500<levels['out']<6500 and levels['after']<100 and 3300<levels['peer']<4700,levels
    assert originals=={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in originals}
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    proof=dict(reports=reports,video=video,decoded_magnitudes=levels,private_receipts=receipts,isolated_display=options.isolated_display,original_sources_unchanged=True,manual_has_unchanged=True,functional_unchanged=True,cold_readers=['packed','linked','recovery','lesson'],native_fixtures=0,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
