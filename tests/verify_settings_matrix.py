"""Two saved content profiles crossed with two personal UI/input profiles."""
from pathlib import Path
import argparse,hashlib,json,math,os,struct,subprocess,sys,time,wave,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--isolated-display');p.add_argument('--output',type=Path);o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Linux requires a provisioned private display; no visible fallback')
  configure_private_display(o.isolated_display)
 folder=(o.output or ROOT/'output/settings-matrix'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
 with wave.open(str(folder/'tone.wav'),'wb') as out:
  out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(b''.join(struct.pack('<h',int(12000*math.sin(2*math.pi*1000*i/48000))) for i in range(24000)))
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 reports={};receipts=[]
 def execute(label,extra,marker):
  args=command('tests/settings_matrix_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=365);log=r.stdout+r.stderr;(folder/(label+'.log')).write_text(log)
  assert r.returncode==0 and marker in log and not any(token in log for token in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['checks']>0 and reports[label]['failures']==0
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);receipt=json.loads(path.read_bytes());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'];receipts.append(str(path))
  print(label+': PASS',flush=True)
 execute('writer',[],'SETTINGS_MATRIX_WRITE ')
 expected=json.loads((folder/'expected.json').read_bytes());manual={name:digest(folder/(name+'.has')) for name in ['a','b']}
 forbidden={'shortcuts','navigation','workspace','display','ui_scale','personal_preferences','theme'}
 for name in ['a','b']:
  with zipfile.ZipFile(folder/(name+'.has')) as archive:manifest=json.loads(archive.read('project.json'))
  assert not forbidden.intersection(manifest) and not forbidden.intersection(manifest.get('editor',{})) and not forbidden.intersection(manifest['video'])
 offline=[folder/'map.glb',folder/'tone.wav',folder/'writer-cache'];moved=[]
 try:
  for source in offline:
   target=source.with_name(source.name+'.offline');assert not target.exists();source.rename(target);moved.append((source,target))
  execute('reader-a',['--read','--profile-a'],'SETTINGS_MATRIX_READ ')
  execute('reader-b',['--read','--profile-b'],'SETTINGS_MATRIX_READ ')
 finally:
  for source,target in reversed(moved):target.rename(source)
 assert all(digest(folder/(name+'.has'))==sha for name,sha in manual.items())
 ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);media={}
 for name in ['a','b']:
  data=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',expected['movies'][name]],**flags));video=next(s for s in data['streams'] if s['codec_type']=='video');want=(1280,720,'30000/1001','61') if name=='a' else (960,540,'24/1','48')
  assert video['codec_name']=='h264' and (video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==want,video
  duration=61*1001/30000 if name=='a' else 2;assert abs(float(data['format']['duration'])-duration)<.003
  assert any(s.get('codec_name')=='aac' for s in data['streams'])
  pcm=subprocess.check_output([ffmpeg,'-v','error','-i',expected['movies'][name],'-f','s16le','-ar','48000','-ac','1','-'],**flags);onset=next(i for i,(v,) in enumerate(struct.iter_unpack('<h',pcm)) if abs(v)>1000);want_onset=round(24*(1001/30000 if name=='a' else 1/24)*48000);assert abs(onset-want_onset)<=96
  media[name]={'video':video,'audio_onset_sample':onset,'expected_onset_sample':want_onset}
 assert all(digest(ROOT/path)==sha for path,sha in frozen.items())
 result=dict(reports=reports,profiles=expected['personal'],project_settings={name:value['state']['video'] for name,value in expected['projects'].items()},media=media,source_sha256=frozen,manual_has_unchanged=True,personal_preferences_not_embedded=True,owned_originals_and_writer_cache_offline_for_readers=True,fresh_process_profiles=2,isolated_display=o.isolated_display,private_receipts=receipts,scope='Complete current implemented project-content/personal UI/input settings boundary; no new settings-load prompt or theme/input feature is introduced.')
 (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
