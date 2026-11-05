"""Real beginner path, visual hints, normal import/physics/keys/paint/clips/HAS/MP4."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=ROOT/'output/first-movie'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples/tutorials').iterdir() if p.is_file()}
    for label,extra,marker in [('movie',[],'FIRST_MOVIE_SMOKE '),('resume',['--resume'],'FIRST_MOVIE_RESUME ')]:
        args=command('tests/first_movie_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0' in log and not any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        if os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'));assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        results.append(json.loads(log.split(marker)[-1].splitlines()[0]))
    video=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',results[0]['movie']],text=True,encoding='utf-8'))
    v=next(s for s in video['streams'] if s['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['format']['duration'])-2)<.001,video
    assert originals=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples/tutorials').iterdir() if p.is_file()}
    import array
    audio=next(s for s in video['streams'] if s['codec_type']=='audio')
    assert audio['codec_name']=='aac'
    pcm=array.array('h');pcm.frombytes(subprocess.check_output(['ffmpeg','-v','error','-i',results[0]['movie'],'-vn','-ac','1','-ar','48000','-f','s16le','-']))
    if sys.byteorder!='little':pcm.byteswap()
    onset=next(i for i,v in enumerate(pcm) if abs(v)>1000)
    assert abs(onset-80000)<=240,onset
    result={'results':results,'private_receipts':receipts,'originals':originals,'video':v,'cue_onset_sample':onset,'isolated_display':options.isolated_display};(ROOT/'output/first-movie-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
