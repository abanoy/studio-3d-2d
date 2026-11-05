from pathlib import Path
import json, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    folder=ROOT/'output/foot-hold'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/foot_hold_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
    log=p.stdout+p.stderr;(folder/'app.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'FOOT_HOLD_SMOKE ' in log and not any(s in log for s in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked','another exclusive child']),log
    result=json.loads(log.split('FOOT_HOLD_SMOKE ')[-1].splitlines()[0]);assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text())
    assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    result['private_receipt']=str(receipt)
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1') and abs(float(v['duration'])-2)<.001
    (ROOT/'output/foot-hold-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
