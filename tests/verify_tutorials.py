"""Actual hidden practice courses, whole-state Previous, fresh-process Continue, MP4."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chapter',choices=['existing','lighting','interpolation','constraints','physics'],default='existing')
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires --isolated-display for a private dummy display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    script='tests/'+options.chapter+'_lesson_smoke.gd' if options.chapter!='existing' else 'tests/tutorial_smoke.gd'
    cases=[('practice',[],'LIGHTING_LESSON_SMOKE '),('resume',['--read'],'LIGHTING_LESSON_READ ')] if options.chapter=='lighting' else [('practice',[],'TUTORIAL_SMOKE '),('resume',['--resume'],'TUTORIAL_RESUME ')]
    if options.chapter in ['interpolation','constraints','physics']:
        prefix=options.chapter.upper()+'_LESSON_'
        cases=[('practice',[],prefix+'SMOKE '),('resume',['--read'],prefix+'READ ')]
    folder=ROOT/'output/tutorials'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,extra,marker in cases:
        args=command(script,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0' in log and not any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'))
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        results.append(json.loads(log.split(marker)[-1].splitlines()[0]))
    probe_path=str(Path(os.environ['HYBRID_FFMPEG']).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')) if os.environ.get('HYBRID_FFMPEG') else 'ffprobe'
    probe=subprocess.run([probe_path,'-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_frames','-of','json',results[0]['movie']],capture_output=True,text=True,check=True)
    video=json.loads(probe.stdout)['streams'][0]
    assert video['codec_name']=='h264' and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='24/1' and video['nb_frames']=='48',video
    result={'results':results,'video':video,'private_receipts':receipts,'chapter':options.chapter,'isolated_display':options.isolated_display};(ROOT/('output/'+options.chapter+'-lesson-verification.json' if options.chapter!='existing' else 'output/tutorials-verification.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
