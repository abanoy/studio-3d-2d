"""Real Simple/Advanced pin and knee correction with native rig/HAS/movie evidence."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/contact-correction'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/contact_correction_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=170)
    output=p.stdout+p.stderr;(folder/'engine.log').write_text(output,encoding='utf-8')
    assert p.returncode==0 and 'CONTACT_CORRECTION ' in output and not any(x in output for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),output
    r=json.loads((folder/'result.json').read_text());assert r['failures']==0
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',r['movie']],text=True));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48');assert abs(float(probe['format']['duration'])-2)<.001
    receipt=Path(args[args.index('--receipt')+1]);value=json.loads(receipt.read_text());assert value['exit']==0 and value['child_desktop_confirmed'] and not value['foreground_child_observed'] and value['job_closed'] and value['desktop_closed']
    r['private_receipt']=str(receipt);(ROOT/'output/contact-correction-verification.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
