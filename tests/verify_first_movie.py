"""Real beginner path, visual hints, normal import/physics/keys/paint/clips/HAS/MP4."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/first-movie'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples/tutorials').iterdir() if p.is_file()}
    for label,extra,marker in [('movie',[],'FIRST_MOVIE_SMOKE '),('resume',['--resume'],'FIRST_MOVIE_RESUME ')]:
        args=command('tests/first_movie_smoke.gd',extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0' in log and not any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'));assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
        receipts.append(str(receipt));results.append(json.loads(log.split(marker)[-1].splitlines()[0]))
    video=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',results[0]['movie']],text=True,encoding='utf-8'))
    v=next(s for s in video['streams'] if s['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['format']['duration'])-2)<.001,video
    assert originals=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples/tutorials').iterdir() if p.is_file()}
    result={'results':results,'private_receipts':receipts,'originals':originals,'video':v};(ROOT/'output/first-movie-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
