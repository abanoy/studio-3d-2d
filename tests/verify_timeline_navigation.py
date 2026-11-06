"""Private GUI timeline zoom/pan and existing workspace/channel/movie regression."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/timeline-navigation'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for name in ['src','tests','tools','data','examples'] for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    reports={};receipts=[];skips=[]
    samples=array.array('h',(round(12000*math.sin(2*math.pi*1000*i/48000)) for i in range(24000)))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(folder/'tone.wav'),'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
    original=hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()
    for script,label,marker,headless in [('tests/timeline_navigation_unit.gd','unit','TIMELINE_NAVIGATION_UNIT ',True),('tests/timeline_navigation_smoke.gd','app','TIMELINE_NAVIGATION_SMOKE ',False),('tests/workspace_controls_smoke.gd','workspace','WORKSPACE_CONTROLS ',False),('tests/animated_channels_smoke.gd','channels','ANIMATED_CHANNELS ',False)]:
        output=folder if label in ('unit','app') else folder/label;output.mkdir(exist_ok=True)
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(output)])
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=220)
        log=result.stdout+result.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(v in log for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0;reports[label]=report
        skips.extend(line for line in log.splitlines() if line.startswith('SKIP '))
        if os.name=='nt' and not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',reports['channels']['movie']],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
    video=next(v for v in media['streams'] if v['codec_type']=='video');assert video['codec_name']=='h264' and video['width']==1920 and video['height']==1080 and int(video['nb_frames'])==48
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in frozen.items())
    assert hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()==original
    proof=dict(reports=reports,video=video,optional_native_skips=skips,functional_unchanged=True,source_audio_unchanged=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
