"""Actual Simple controls, native main-key isolation, packed HAS/cold Open/MP4."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def run(script,folder,extra,marker,timeout):
    args=command(script,extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr;(folder/(Path(script).stem+'.log')).write_text(text,encoding='utf-8')
    assert p.returncode==0 and marker in text and not any(v in text for v in ['ERROR:','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),text
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];return str(receipt)

def main():
    folder=ROOT/'output/motion-animation-app'/str(time.time_ns());folder.mkdir(parents=True)
    reference=json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['packed']
    receipt=run('tests/motion_animation_smoke.gd',folder,[reference],'MOTION_ANIMATION ',200)
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0 and len(result['native_reports'])==5
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],text=True));v=next(v for v in probe['streams'] if v['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(probe['format']['duration'])-2)<.001
    cold=run('tests/motion_animation_read.gd',folder,[],'MOTION_ANIMATION_READ ',100);reader=json.loads((folder/'reader.json').read_text());assert reader['failures']==0
    result.update(folder=str(folder),private_receipt=receipt,reader={**reader,'private_receipt':cold})
    (ROOT/'output/motion-animation-app-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['expected_world','pose_hashes']},indent=2))
if __name__=='__main__':main()
