"""All seven addendum timeline scenarioC steps, actual routed app, cold HAS and movie."""
from pathlib import Path
import argparse,hashlib,json,math,os,struct,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:parser.error('Linux needs an explicitly private display; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=(o.output or ROOT/'output/scenario-c'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
 with wave.open(str(folder/'tone.wav'),'wb') as out:
  out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(b''.join(struct.pack('<h',int(12000*math.sin(2*math.pi*1000*i/48000))) for i in range(24000)))
 tone=hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest();reports={};receipts=[]
 frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools'] for p in (ROOT/part).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 for label,extra,marker in [('writer',[],'SCENARIO_C_WRITE '),('reader',['--read'],'SCENARIO_C_READ ')]:
  args=command('tests/scenario_c_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=390);text=r.stdout+r.stderr;(folder/(label+'.log')).write_text(text)
  assert r.returncode==0 and marker in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
  reports[label]=json.loads(next(line[len(marker):] for line in text.splitlines() if line.startswith(marker)));assert reports[label]['failures']==0
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
  if label=='writer':
   expected=json.loads((folder/'expected.json').read_bytes());manual=hashlib.sha256((folder/'scenario-c.has').read_bytes()).hexdigest();assert manual==expected['manual_sha']
   for path,digest in expected['sources'].items():
    source=Path(path);assert hashlib.sha256(source.read_bytes()).hexdigest()==digest;source.rename(source.with_suffix(source.suffix+'.offline'))
   assert hashlib.sha256((folder/'tone.wav').read_bytes()).hexdigest()==tone
   (folder/'tone.wav').rename(folder/'tone.wav.offline');(folder/'writer-cache').rename(folder/'writer-cache.offline')
 ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
 media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',expected['movie']],**flags))
 video=next(s for s in media['streams'] if s['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','128') and abs(float(media['format']['duration'])-128/24)<.002
 assert any(s.get('codec_name')=='aac' for s in media['streams'])
 pcm=subprocess.check_output([ffmpeg,'-v','error','-i',expected['movie'],'-f','s16le','-ar','48000','-ac','1','-'],**flags);onset=next(i for i,(v,) in enumerate(struct.iter_unpack('<h',pcm)) if abs(v)>1000);assert abs(onset-48000)<=96,onset
 assert hashlib.sha256((folder/'scenario-c.has').read_bytes()).hexdigest()==manual
 assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
 proof=dict(reports=reports,video=video,audio_onset_sample=onset,manual_has_unchanged=True,originals_and_writer_cache_unavailable_for_cold_open=True,functional_source_unchanged=True,source_sha256=frozen,private_receipts=receipts,isolated_display=o.isolated_display,scope='All seven scenarioC software steps on original generated maps/rig; final Windows target and native ecosystem fidelity remain separate.')
 (folder/'verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
