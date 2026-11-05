"""Actual live-ragdoll independence across drawing Undo/Redo and persistence."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/drawing-history'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for mode,extra in [('writer',[]),('reader',['--read'])]:
        args=command('tests/drawing_history_smoke.gd',extra=['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=175)
        log=p.stdout+p.stderr;(folder/(mode+'.log')).write_text(log,encoding='utf-8');marker='DRAWING_HISTORY_SMOKE ' if mode=='writer' else 'DRAWING_HISTORY_READ '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    assert [(r['checks'],r['failures']) for r in results]==[(36,0),(3,0)],results
    result=json.loads((folder/'result.json').read_bytes());meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),results=results,private_receipts=receipts,pixels_exact=True)
    (ROOT/'output/drawing-history-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
