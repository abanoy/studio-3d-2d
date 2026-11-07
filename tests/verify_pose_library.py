from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/body-pose-library'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);reports={};receipts=[]
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','data','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    for label,script,headless,extra,marker in [('writer','tests/pose_library_smoke.gd',False,[],'POSE_LIBRARY_SMOKE '),('reader','tests/pose_library_smoke.gd',False,['--read'],'POSE_LIBRARY_READ ')]:
        args=command(script,headless,extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+['--',str(folder),*extra]);args[args.index('--log-file')+1]=str(folder/(label+'-engine.log'));cancel=folder/(label+'-cancel');
        if os.name=='nt':args[args.index('--'):args.index('--')]=['--cancel-file',str(cancel)]
        with (folder/(label+'.log')).open('wb') as log:
            p=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);started=time.monotonic()
            while p.poll() is None:
                raw=(folder/(label+'-engine.log')).read_bytes() if (folder/(label+'-engine.log')).exists() else b''
                if any(x in raw for x in [b'SCRIPT ERROR',b'SHADER ERROR',b'ERROR:',b'FAIL ']) or time.monotonic()-started>120:
                    if os.name=='nt':cancel.write_text('stop owned failed test',encoding='utf-8')
                    else:p.terminate()
                time.sleep(.05)
        raw=(folder/(label+'.log')).read_bytes();assert p.returncode==0 and marker.encode() in raw and not any(x in raw for x in [b'SCRIPT ERROR',b'SHADER ERROR',b'ERROR:',b'FAIL ',b'ObjectDB instances leaked']),raw.decode('utf-8',errors='replace')
        if os.name=='nt':
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
        line=next(s for s in raw.decode('utf-8',errors='replace').splitlines() if s.startswith(marker));reports[label]=json.loads(line[len(marker):]);assert reports[label]['failures']==0
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']],text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0));video=next(s for s in probe['streams'] if s['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    result={'source_sha256':frozen,'isolated_display':options.isolated_display,'folder':str(folder),'reports':reports,'private_receipts':receipts,'video':video};(folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'output/body-pose-library-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['video','source_sha256']},indent=2))
if __name__=='__main__':main()
