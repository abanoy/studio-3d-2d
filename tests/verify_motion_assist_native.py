"""Read-only motion-assist preview over prepared native rigs; hidden Windows GPU."""
from pathlib import Path
import json, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    reference=json.loads((ROOT/'output/contact-persistence-verification.json').read_text())['writer']['packed']
    folder=ROOT/'output/motion-assist-native'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/motion_assist_native.gd',extra=['--',str(folder),reference])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=200)
    text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'MOTION_ASSIST_NATIVE ' in text and not any(v in text for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0 and len(result['native_reports'])==5
    movie=folder/'preview-movie/movie.mp4'
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(movie)],text=True))
    v=next(x for x in probe['streams'] if x['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(probe['format']['duration'])-2)<.001
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text())
    assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    result.update(folder=str(folder),private_receipt=str(receipt),diagnostic_movie=str(movie),normal_export_integrated=False)
    (ROOT/'output/motion-assist-native-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='native_reports'},indent=2))
if __name__=='__main__':main()
