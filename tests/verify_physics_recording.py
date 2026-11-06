"""Explicit Local/World simulation capture, portable replay and real H264/AAC output."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/physics-recording'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    wav=folder/'voice — тест.wav';samples=array.array('h',(int(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(wav),'wb') as out:out.setparams((1,2,44100,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
    original=hashlib.sha256(wav.read_bytes()).hexdigest();receipts=[];reports={};skips=[]
    for label,script,marker,headless in [('unit','tests/physics_recording_unit.gd','PHYSICS_RECORDING_UNIT ',True),('app','tests/physics_recording_smoke.gd','PHYSICS_RECORDING ',False)]:
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(folder),str(wav)])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),log
        reports[label]=json.loads(next(x[len(marker):] for x in log.splitlines() if x.startswith(marker)));assert reports[label]['failures']==0
        skips.extend(x for x in log.splitlines() if x.startswith('SKIP '))
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
    report=reports['app'];ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],**flags));video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert report['audio'] and any(s['codec_name']=='aac' for s in media['streams']) and abs(float(media['format']['duration'])-2)<.001
    pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',report['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,x in enumerate(pcm) if abs(x)>1000)/48000;assert abs(onset-1)<.002,onset
    assert hashlib.sha256(wav.read_bytes()).hexdigest()==original
    proof=dict(report=report,unit=reports['unit'],video={'codec':'h264','width':1920,'height':1080,'frames':48,'fps':'24/1','duration':media['format']['duration'],'audio':'aac','onset':onset},private_receipts=receipts,isolated_display=options.isolated_display,source_audio_unchanged=True,optional_native_skips=skips)
    if options.output is None:
        legacy=report.copy();legacy.update(video=proof['video'],audio_onset_seconds=onset)
        (ROOT/'output/physics-recording-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (ROOT/'output/physics-recording-verification.json').write_text(json.dumps(legacy,indent=2),encoding='utf-8')
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
