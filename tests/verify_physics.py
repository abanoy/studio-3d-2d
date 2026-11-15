"""Real live physics, freeze/HAS and actual movie verification on private displays."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no visible fallback')
  configure_private_display(options.isolated_display)
 folder=(options.output or ROOT/'output/physics-portable'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
 frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 args=command('tests/physics_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'godot.log')])
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
 text=p.stdout+p.stderr;(folder/'engine.log').write_text(text,encoding='utf-8')
 if p.returncode or 'PHYSICS_SMOKE ' not in text or '"failures":0' not in text or any(x in text for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):raise RuntimeError(text)
 report=json.loads((ROOT/'output/physics-result.json').read_text(encoding='utf-8'))
 ffmpeg=os.environ.get('HYBRID_FFMPEG',str(Path('C:/Program Files/ffmpeg/bin/ffmpeg.exe')) if os.name=='nt' else '/usr/bin/ffmpeg')
 probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
 media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],text=True,encoding='utf-8'))
 video=next(x for x in media['streams'] if x['codec_type']=='video')
 assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
 assert abs(float(media['format']['duration'])-2)<.001
 assert not any(x['codec_type']=='audio' for x in media['streams'])
 receipt=None
 if os.name=='nt':
  receipt=Path(args[args.index('--receipt')+1]);desktop=json.loads(receipt.read_bytes())
  assert desktop['exit']==0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
 assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
 report.update(video=video,source_sha256=frozen,isolated_display=options.isolated_display,private_receipt=str(receipt) if receipt else None,native_fidelity_certified=False,physical_device_certified=False)
 (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 (ROOT/'output/physics-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
