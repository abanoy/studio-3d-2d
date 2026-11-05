from pathlib import Path
import array,hashlib,json,math,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,engine_path

def main():
    folder=ROOT/'output/project-duration'/str(time.time_ns());folder.mkdir(parents=True)
    for label,script in [('app','src/app.gd'),('test','tests/project_duration_smoke.gd')]:
        p=subprocess.run([engine_path(),'--headless','--path',str(ROOT),'--check-only','--script',script,'--log-file',str(folder/(label+'-parse.log'))],cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
        assert p.returncode==0 and b'SCRIPT ERROR' not in p.stdout+p.stderr,(p.stdout+p.stderr).decode('utf-8',errors='replace')
    data=array.array('h',(round(12000*math.sin(2*math.pi*1000*n/48000)) for n in range(96000)))
    if sys.byteorder!='little':data.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(data.tobytes())
    original=hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest();receipts=[];readers=[]
    for mode in ['writer','packed','linked','recovery','lesson']:
        args=command('tests/project_duration_smoke.gd',extra=['--',str(folder),mode]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW);raw=p.stdout+p.stderr;(folder/(mode+'.log')).write_bytes(raw)
        marker=b'PROJECT_DURATION_SMOKE ' if mode=='writer' else b'PROJECT_DURATION_READ '
        assert p.returncode==0 and marker in raw and not any(x in raw for x in (b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked')),raw.decode('utf-8',errors='replace')
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(receipt))
        result=json.loads(raw.split(marker)[-1].splitlines()[0]);assert result['failures']==0
        if mode=='writer':report=result;saved_hash=hashlib.sha256(Path(report['project']).read_bytes()).hexdigest()
        else:readers.append(result)
    assert hashlib.sha256(Path(report['project']).read_bytes()).hexdigest()==saved_hash and hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()==original
    raw=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]);(folder/'ffprobe.json').write_bytes(raw);meta=json.loads(raw);v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24000/1001','24') and abs(float(meta['format']['duration'])-1.001)<.01
    raw=subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','-']);pcm=array.array('h');pcm.frombytes(raw)
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000);assert abs(onset-24024)<240,onset
    report.update(folder=str(folder),private_receipts=receipts,decoded_onset_sample=onset,fresh_readers=readers)
    (ROOT/'output/project-duration-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
