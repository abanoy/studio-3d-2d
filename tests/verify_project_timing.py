from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command as engine_command,engine_path,configure_private_display
def command(*args,**kwargs):
    argv=engine_command(*args,**kwargs)
    if os.name!='nt':
        pos=argv.index('--') if '--' in argv else len(argv);argv[pos:pos]=['--audio-driver','Dummy']
    return argv

def receipt_for(args):
    if os.name!='nt':return None
    path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    return str(path)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--previous-storage',type=Path);parser.add_argument('--current-only',action='store_true',help='Explicitly omit unavailable checksum-bound historical-reader fixture; current app/persistence/media checks still run');parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(options.isolated_display)
    if options.current_only and options.previous_storage:parser.error('Choose current-only or the checksum-bound historical reader')
    folder=(options.output or ROOT/'output/project-timing'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    if not options.current_only:
        if options.previous_storage is not None:
            previous=options.previous_storage.read_bytes()
        else:
            prior=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output/checkpoints/2026-11-04-134345-media-review/development-source.zip')
            assert hashlib.sha256(prior.read_bytes()).hexdigest()=='03e81a97979398819c33055416ccf5667fd616d9d1b18307d25c3d0e7042352e'
            with zipfile.ZipFile(prior) as z:previous=z.read('src/storage.gd')
        assert hashlib.sha256(previous).hexdigest()=='67ab0813fc16cebac5c3d2e3780808dd8ba1537d5a6647bde1b7d0f1d22a9575','Previous-reader fixture differs from the checksum-bound original.'
        (folder/'previous_storage.gd').write_bytes(previous)
    for label,script in [('app','src/app.gd'),('test','tests/project_timing_smoke.gd')]:
        p=subprocess.run([engine_path(),'--headless','--path',str(ROOT),'--check-only','--script',script,'--log-file',str(folder/(label+'-parse.log'))],cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,timeout=30)
        assert p.returncode==0 and b'SCRIPT ERROR' not in p.stdout+p.stderr,(p.stdout+p.stderr).decode('utf-8',errors='replace')
    data=array.array('h',(round(12000*math.sin(2*math.pi*1000*n/48000)) for n in range(24000)))
    if sys.byteorder!='little':data.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(data.tobytes())
    args=command('tests/project_timing_smoke.gd',extra=['--',str(folder),'writer',*(['--current-only'] if options.current_only else [])]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);raw=p.stdout+p.stderr;(folder/'app.log').write_bytes(raw)
    assert p.returncode==0 and b'PROJECT_TIMING_SMOKE ' in raw and not any(x in raw for x in (b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
    receipt=receipt_for(args)
    report=json.loads((folder/'result.json').read_bytes());assert report['failures']==0
    receipts=[receipt] if receipt else [];saved_hash=hashlib.sha256(Path(report['project']).read_bytes()).hexdigest()
    for mode in ['packed','linked','recovery','lesson']:
        args=command('tests/project_timing_smoke.gd',extra=['--',str(folder),mode]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);raw=p.stdout+p.stderr;(folder/(mode+'.log')).write_bytes(raw)
        assert p.returncode==0 and b'PROJECT_TIMING_READ ' in raw and not any(x in raw for x in (b'SCRIPT ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
        path=receipt_for(args)
        if path:receipts.append(path)
    assert hashlib.sha256(Path(report['project']).read_bytes()).hexdigest()==saved_hash
    ffmpeg=os.environ.get('HYBRID_FFMPEG','C:/Program Files/ffmpeg/bin/ffmpeg.exe' if os.name=='nt' else '/usr/bin/ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    raw=subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]);(folder/'ffprobe.json').write_bytes(raw);meta=json.loads(raw);v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24000/1001','48') and abs(float(meta['format']['duration'])-2.002)<.01
    raw=subprocess.check_output([ffmpeg,'-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','-']);pcm=array.array('h');pcm.frombytes(raw)
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000);assert abs(onset-48048)<240,onset
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
    report.update(source_sha256=frozen,video=v,isolated_display=options.isolated_display,previous_reader_verified=not options.current_only,skips=['Historical checksum-bound previous reader unavailable; explicitly omitted'] if options.current_only else [])
    report.update(folder=str(folder),private_receipt=str(receipt),private_receipts=receipts,decoded_onset_sample=onset,fresh_readers=['packed','linked','recovery','lesson']);(folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n');(ROOT/'output/project-timing-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS project rate presets, exact rational audio, frame/key isolation, Undo, fresh HAS/recovery/lesson and NTSC H264/AAC output')
