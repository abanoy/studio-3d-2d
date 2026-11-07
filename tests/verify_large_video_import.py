"""400 unique prepared video drawings: admission, cancel, edit, cold HAS, recovery and MP4."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:parser.error('Linux requires an existing private display; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=(o.output or ROOT/'output/large-video'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
 ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
 source=folder/'source.mov'
 encoder=subprocess.Popen([ffmpeg,'-v','error','-n','-f','rawvideo','-pixel_format','rgba','-video_size','64x36','-framerate','24','-i','-','-an','-c:v','qtrle','-threads','1',str(source)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,**flags)
 for frame in range(400):
  pixels=bytearray(64*36*4)
  color=bytes(((frame*17)%256,(frame*29)%256,(frame*43)%256,180 if frame%2 else 255))
  x=frame%45;y=(frame//45)%20
  for yy in range(y,y+12):
   for xx in range(x,x+12):pixels[(yy*64+xx)*4:(yy*64+xx)*4+4]=color
  pixels[(2*64+2)*4:(2*64+2)*4+4]=bytes((frame%256,frame//256,120,255))
  encoder.stdin.write(pixels)
 encoder.stdin.close();error=encoder.stderr.read().decode();assert encoder.wait(timeout=40)==0,error
 source_sha=digest(source)
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 reports={};memory={};receipts=[]
 def execute(label,extra,marker):
  args=command('tests/large_video_import_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);started=time.monotonic();peak=0;hwm=0
  with (folder/(label+'.log')).open('wb') as out:
   child=subprocess.Popen(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,**flags)
   while child.poll() is None:
    if time.monotonic()-started>915:child.terminate();child.wait(timeout=15);raise TimeoutError(label+' exceeded watchdog')
    if sys.platform=='linux':
     try:
      status=Path(f'/proc/{child.pid}/status').read_text()
      for line in status.splitlines():
       if line.startswith('VmRSS:'):peak=max(peak,int(line.split()[1])*1024)
       if line.startswith('VmHWM:'):hwm=max(hwm,int(line.split()[1])*1024)
     except FileNotFoundError:pass
    time.sleep(.05)
  log=(folder/(label+'.log')).read_text(errors='replace');assert child.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['checks']>0 and reports[label]['failures']==0
  memory[label]={'process_RSS_sample_peak_bytes':peak or None,'process_HWM_observed_bytes':hwm or None,'wall_seconds':time.monotonic()-started,'scope':'Godot process only, excludes converter/Python/driver/OS processes; not a whole-app hard budget'}
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
  print(label+': PASS',flush=True)
 execute('writer',[],'LARGE_VIDEO_WRITE ')
 packed=folder/'Video400.has';manual=digest(packed);assert digest(source)==source_sha
 with zipfile.ZipFile(packed) as archive:
  manifest=json.loads(archive.read('project.json'));assert manifest['schema_version']==8 and len(manifest['layers'][2]['cels'])==400 and manifest['layers'][2]['origin']['format']=='studio_drawing_origin_4' and manifest['layers'][2]['origin']['duration']==400
  assert len({c['path'] for c in manifest['layers'][2]['cels']})==400 and len(archive.namelist())<=1024
 moved=[]
 try:
  for path in [source,folder/'map.glb',folder/'writer-cache',Path(reports['writer']['job'])]:
   offline=path.with_name(path.name+'.offline');assert not offline.exists();path.rename(offline);moved.append((path,offline))
  execute('reader',['--read'],'LARGE_VIDEO_READ ')
 finally:
  for path,offline in reversed(moved):offline.rename(path)
 assert digest(packed)==manual and digest(source)==source_sha
 probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',reports['writer']['movie']],**flags));v=next(s for s in media['streams'] if s['codec_type']=='video')
 assert (v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'400','24/1') and abs(float(media['format']['duration'])-400/24)<.002
 assert not any(s['codec_type']=='audio' for s in media['streams'])
 assert all(digest(ROOT/path)==sha for path,sha in frozen.items())
 result=dict(reports=reports,process_memory=memory,video=v,source_sha256=frozen,original_video_sha256=source_sha,original_video_unchanged=True,manual_HAS_unchanged=True,source_map_accepted_prepared_job_and_writer_cache_offline_for_reader=True,actual_cold_reader=True,frozen_functional_sources=True,native_fixtures=0,isolated_display=o.isolated_display,private_receipts=receipts,scope='400 unique original generated video frames normalized to fullHD; registered admission, cancellation/Undo/edit/recovery/packed cold media only. No400noisy-frame/native/Windows/hardware/wholeRAM promise.')
 (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
