"""Actual hidden practice courses, whole-state Previous, fresh-process Continue, MP4."""
from pathlib import Path
import json, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/tutorials'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,extra,marker in [('practice',[],'TUTORIAL_SMOKE '),('resume',['--resume'],'TUTORIAL_RESUME ')]:
        args=command('tests/tutorial_smoke.gd',extra=['--',str(folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=130)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0' in log and not any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'))
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
        receipts.append(str(receipt));results.append(json.loads(log.split(marker)[-1].splitlines()[0]))
    probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_frames','-of','json',results[0]['movie']],capture_output=True,text=True,check=True)
    video=json.loads(probe.stdout)['streams'][0]
    assert video['codec_name']=='h264' and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='24/1' and video['nb_frames']=='48',video
    result={'results':results,'video':video,'private_receipts':receipts};(ROOT/'output/tutorials-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
