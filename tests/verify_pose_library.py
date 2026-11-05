from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/body-pose-library'/str(time.time_ns());folder.mkdir(parents=True);reports={};receipts=[]
    for label,script,headless,extra,marker in [('writer','tests/pose_library_smoke.gd',False,[],'POSE_LIBRARY_SMOKE '),('reader','tests/pose_library_smoke.gd',False,['--read'],'POSE_LIBRARY_READ ')]:
        args=command(script,headless,extra=['--',str(folder),*extra]);args[args.index('--log-file')+1]=str(folder/(label+'-engine.log'));cancel=folder/(label+'-cancel');args[args.index('--'):args.index('--')]=['--cancel-file',str(cancel)]
        with (folder/(label+'.log')).open('wb') as log:
            p=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);started=time.monotonic()
            while p.poll() is None:
                raw=(folder/(label+'-engine.log')).read_bytes() if (folder/(label+'-engine.log')).exists() else b''
                if any(x in raw for x in [b'SCRIPT ERROR',b'SHADER ERROR',b'ERROR:',b'FAIL ']) or time.monotonic()-started>120:cancel.write_text('stop owned failed test',encoding='utf-8')
                time.sleep(.05)
        raw=(folder/(label+'.log')).read_bytes();assert p.returncode==0 and marker.encode() in raw and not any(x in raw for x in [b'SCRIPT ERROR',b'SHADER ERROR',b'ERROR:',b'FAIL ',b'ObjectDB instances leaked']),raw.decode('utf-8',errors='replace')
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path));line=next(s for s in raw.decode('utf-8',errors='replace').splitlines() if s.startswith(marker));reports[label]=json.loads(line[len(marker):]);assert reports[label]['failures']==0
    probe=json.loads(subprocess.check_output(['C:/Program Files/ffmpeg/bin/ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']],text=True,creationflags=subprocess.CREATE_NO_WINDOW));video=next(s for s in probe['streams'] if s['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    result={'folder':str(folder),'reports':reports,'private_receipts':receipts,'video':video};(ROOT/'output/body-pose-library-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='video'},indent=2))
if __name__=='__main__':main()
