"""Default empty world and routed Simple/Advanced preservation on a private display."""
from pathlib import Path
import argparse,array,hashlib,json,math,os,subprocess,sys,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display,engine_path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--isolated-display');p.add_argument('--output',type=Path,required=True);o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False);fixtures=ROOT/'output/fixtures';fixtures.mkdir(parents=True,exist_ok=True);voice=fixtures/'voice — тест.wav'
 if not voice.exists():
  pcm=array.array('h',(round(16000*math.sin(2*math.pi*1000*n/44100)) for n in range(22050)))
  if sys.byteorder!='little':pcm.byteswap()
  with wave.open(str(voice),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(pcm.tobytes())
 before=digest(voice);frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
 for label,script,extra,marker in [('new','tests/new_scene_smoke.gd',[],'NEW_SCENE_SMOKE '),('detail',None,['--','--ui-smoke','--demo-room'],'UI_SMOKE ')]:
  args=command(script,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log'))]+extra);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=135);log=r.stdout+r.stderr;(folder/(label+'.log')).write_text(log);assert r.returncode==0 and marker in log and not any(t in log for t in ['ERROR:','FAIL ','ObjectDB instances leaked']),log;report=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert report['checks']>0 and report['failures']==0;reports[label]=report;print(label+': PASS',flush=True)
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);proof=json.loads(path.read_bytes());assert proof['exit']==0 and proof['child_desktop_confirmed'] and not proof['foreground_child_observed'] and proof['job_closed'] and proof['desktop_closed'];receipts.append(str(path))
 assert digest(voice)==before and all(digest(ROOT/name)==sha for name,sha in frozen.items())
 ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',reports['new']['movie']]));v=next(s for s in media['streams'] if s['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1')
 result=dict(reports=reports,video=v,source_sha256=frozen,voice_source_unchanged=True,isolated_display=o.isolated_display,private_receipts=receipts,engine_version=subprocess.check_output([engine_path(),'--version'],text=True).strip(),scope='Current empty-world/grid/excluded-final/background/persistence and actual Simple/Advanced data/FOV/interpolation/audio/pixel-preservation interactions. Private Linux software verification, not native ecosystem/Windows/physical input/novice certification.')
 (folder/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
