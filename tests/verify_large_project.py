"""400 drawing packed Open, media, actual termination and ordinary startup proof."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, time, wave, math, struct, zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--isolated-display',required=True);o=p.parse_args()
 if sys.platform!='linux':p.error('This process RSS and SIGKILL proof currently requires Linux.')
 configure_private_display(o.isolated_display);folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
 source=o.input.resolve();original=hashlib.sha256(source.read_bytes()).hexdigest();shutil.copy2(source,folder/'input.has')
 with wave.open(str(folder/'tone.wav'),'wb') as w:
  w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<h',int(14000*math.sin(2*math.pi*1000*i/48000))) for i in range(24000)))
 frozen={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for d in ['src','tests','tools'] for f in (ROOT/d).rglob('*') if f.is_file() and '__pycache__' not in f.parts}
 reports={}
 def run(script,label,marker,extra=(),scene=None,crash=False):
  args=command(script,extra=([str(scene)] if scene else [])+['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);peak=0;samples=0;start=time.monotonic()
  with (folder/(label+'.log')).open('w') as log:
   process=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
   while process.poll() is None:
    try:
     status=Path(f'/proc/{process.pid}/status').read_text();values=[int(line.split()[1])*1024 for line in status.splitlines() if line.startswith(('VmRSS:','VmHWM:'))];peak=max([peak,*values]);samples+=1
    except (FileNotFoundError,ProcessLookupError):pass
    if time.monotonic()-start>850:process.kill();raise AssertionError(label+' timeout')
    time.sleep(.05)
  text=(folder/(label+'.log')).read_text();assert process.returncode==(-9 if crash else 0),text
  assert marker in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
  report=json.loads(next(line[len(marker):] for line in text.splitlines() if line.startswith(marker)));assert report['failures']==0,report
  reports[label]=dict(result=report,seconds=time.monotonic()-start,process_rss_hwm_bytes=peak,samples=samples)
 run('tests/large_project_recovery_smoke.gd','writer','LARGE_PROJECT_WRITE ',[str(folder/'input.has')],crash=True)
 expected=json.loads((folder/'expected.json').read_bytes());manual=hashlib.sha256((folder/'large.has').read_bytes()).hexdigest();assert manual==expected['manual_sha']
 with zipfile.ZipFile(folder/'large.has') as archive:
  names=archive.namelist();assert len([n for n in names if n.endswith('.png')])==400 and len(names)>128
 for name in ['writer-cache','tone.wav','input.has']:(folder/name).rename(folder/(name+'.offline'))
 run('tests/large_project_recovery_smoke.gd','reader','LARGE_PROJECT_READ ',['--read'])
 scene=folder/'startup.tscn';scene.write_text('[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://tests/sequence_startup_app.gd" id="1"]\n[ext_resource type="Script" path="res://tests/large_project_startup.gd" id="2"]\n[node name="Studio" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n[node name="Observer" type="Node" parent="."]\nscript=ExtResource("2")\n')
 run(None,'startup','LARGE_PROJECT_STARTUP ',['--auto-open'],scene)
 media=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',expected['movie']]))
 video=next(s for s in media['streams'] if s['codec_type']=='video');audio=next(s for s in media['streams'] if s['codec_type']=='audio')
 assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','101')
 assert audio['codec_name']=='aac' and abs(float(media['format']['duration'])-101/24)<.002
 pcm=subprocess.check_output(['ffmpeg','-v','error','-i',expected['movie'],'-f','s16le','-ac','1','-ar','48000','-'])
 onset=next(i for i,(sample,) in enumerate(struct.iter_unpack('<h',pcm)) if abs(sample)>1000);assert abs(onset-48000)<=96,onset
 assert hashlib.sha256(source.read_bytes()).hexdigest()==original and hashlib.sha256((folder/'large.has').read_bytes()).hexdigest()==manual
 assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
 proof=dict(reports=reports,actual_abrupt_exit=True,offline_sources=True,source_unchanged=True,manual_has_unchanged=True,video=video,audio_onset_sample=onset,source_hashes=frozen,scope='Procedural 400 drawing corpus; process RSS excludes GPU and other processes; native artist and Windows evidence unrun.',isolated_display=o.isolated_display)
 (folder/'verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps({k:v for k,v in proof.items() if k!='source_hashes'},indent=2))
if __name__=='__main__':main()
