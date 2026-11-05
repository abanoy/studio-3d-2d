from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/fill'/str(time.time_ns());folder.mkdir(parents=True);results={}
    for label,script,headless,marker in [('unit','fill_unit.gd',True,'FILL_UNIT '),('app','fill_smoke.gd',False,'FILL_SMOKE ')]:
        args=command('tests/'+script,headless=headless,extra=['--',str(folder),'--demo-room']);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');assert p.returncode==0 and marker in log and '"failures":0' in log and not any(x in log for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
        results[label]=json.loads(log.split(marker)[-1].splitlines()[0])
        if not headless:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];results['private_receipt']=str(path)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',results['app']['movie']],text=True));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    results['folder']=str(folder);(ROOT/'output/fill-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':main()
