"""Actual timeline contact copy/cut/paste/retime, cross-instance/project anchors and HAS/movie."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    components='--components' in sys.argv
    label='component-contact-clipboard' if components else 'contact-clipboard'
    folder=ROOT/'output'/label/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/contact_clipboard_smoke.gd',extra=['--',str(folder),*(['--components'] if components else [])])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=130)
    text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'CONTACT_CLIPBOARD ' in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),text
    r=json.loads((folder/'result.json').read_text());assert r['failures']==0
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',r['movie']],text=True))
    video=next(x for x in probe['streams'] if x['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48');assert abs(float(probe['format']['duration'])-2)<.001
    receipt=Path(args[args.index('--receipt')+1]);v=json.loads(receipt.read_text());assert v['exit']==0 and v['child_desktop_confirmed'] and not v['foreground_child_observed'] and v['job_closed'] and v['desktop_closed']
    r['private_receipt']=str(receipt);(ROOT/'output'/(label+'-verification.json')).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
