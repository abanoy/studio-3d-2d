from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,engine_path
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--previous-storage',type=Path);options=parser.parse_args()
    folder=ROOT/'output/project-timing'/str(time.time_ns());folder.mkdir(parents=True)
    if options.previous_storage is not None:
        previous=options.previous_storage.read_bytes()
    else:
        prior=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output/checkpoints/2026-11-04-134345-media-review/development-source.zip')
        assert hashlib.sha256(prior.read_bytes()).hexdigest()=='03e81a97979398819c33055416ccf5667fd616d9d1b18307d25c3d0e7042352e'
        with zipfile.ZipFile(prior) as z:previous=z.read('src/storage.gd')
    assert hashlib.sha256(previous).hexdigest()=='67ab0813fc16cebac5c3d2e3780808dd8ba1537d5a6647bde1b7d0f1d22a9575','Previous-reader fixture differs from the checksum-bound original.'
    (folder/'previous_storage.gd').write_bytes(previous)
    for label,script in [('app','src/app.gd'),('test','tests/project_timing_smoke.gd')]:
        p=subprocess.run([engine_path(),'--headless','--path',str(ROOT),'--check-only','--script',script,'--log-file',str(folder/(label+'-parse.log'))],cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
        assert p.returncode==0 and b'SCRIPT ERROR' not in p.stdout+p.stderr,(p.stdout+p.stderr).decode('utf-8',errors='replace')
    data=array.array('h',(round(12000*math.sin(2*math.pi*1000*n/48000)) for n in range(24000)))
    if sys.byteorder!='little':data.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(data.tobytes())
    args=command('tests/project_timing_smoke.gd',extra=['--',str(folder)]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW);raw=p.stdout+p.stderr;(folder/'app.log').write_bytes(raw)
    assert p.returncode==0 and b'PROJECT_TIMING_SMOKE ' in raw and not any(x in raw for x in (b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    report=json.loads((folder/'result.json').read_bytes());assert report['failures']==0
    receipts=[str(receipt)];saved_hash=hashlib.sha256(Path(report['project']).read_bytes()).hexdigest()
    for mode in ['packed','linked','recovery','lesson']:
        args=command('tests/project_timing_smoke.gd',extra=['--',str(folder),mode]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW);raw=p.stdout+p.stderr;(folder/(mode+'.log')).write_bytes(raw)
        assert p.returncode==0 and b'PROJECT_TIMING_READ ' in raw and not any(x in raw for x in (b'SCRIPT ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    assert hashlib.sha256(Path(report['project']).read_bytes()).hexdigest()==saved_hash
    raw=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]);(folder/'ffprobe.json').write_bytes(raw);meta=json.loads(raw);v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24000/1001','48') and abs(float(meta['format']['duration'])-2.002)<.01
    raw=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','-']);pcm=array.array('h');pcm.frombytes(raw)
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000);assert abs(onset-48048)<240,onset
    report.update(folder=str(folder),private_receipt=str(receipt),private_receipts=receipts,decoded_onset_sample=onset,fresh_readers=['packed','linked','recovery','lesson']);(ROOT/'output/project-timing-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PASS project rate presets, exact rational audio, frame/key isolation, Undo, fresh HAS/recovery/lesson and NTSC H264/AAC output')
