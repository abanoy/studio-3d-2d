"""Private per-part motion UI acceptance using a supplied Yukari three-pose HAS study."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
import array, math, wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path);args=parser.parse_args();source=args.project.resolve(strict=True);sha=hashlib.sha256(source.read_bytes()).hexdigest()
 folder=ROOT/'output/motion-parts'/str(time.time_ns());folder.mkdir(parents=True)
 cue=folder/'arm-cue.wav'
 samples=array.array('h',(round(12000*math.sin(2*math.pi*880*i/48000)) for i in range(4800)))
 with wave.open(str(cue),'wb') as out:
  out.setparams((1,2,48000,0,'NONE','not compressed'))
  out.writeframes(samples.tobytes())
 command_args=command('tests/motion_parts_smoke.gd',extra=['--',str(folder),str(source)])
 p=subprocess.run(command_args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
 assert p.returncode==0 and 'MOTION_PARTS_APP ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
 result=json.loads((folder/'result.json').read_text());assert result['failures']==0
 receipt=Path(command_args[command_args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
 probe=json.loads(subprocess.check_output(['C:/Program Files/ffmpeg/bin/ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(x for x in probe['streams']if x['codec_type']=='video');assert(v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1')
 assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
 sound=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert sound['codec_name']=='aac' and sound['sample_rate']=='48000'
 decoded=subprocess.check_output(['C:/Program Files/ffmpeg/bin/ffmpeg.exe','-v','error','-i',result['movie'],'-map','0:a:0','-ac','1','-ar','48000','-f','s16le','-'])
 pcm=array.array('h');pcm.frombytes(decoded)
 active=[i for i,sample in enumerate(pcm) if abs(sample)>1500]
 assert active and abs(active[0]-36000)<=96 and abs(active[-1]-40800)<=96,(active[:1],active[-1:])
 cue.rename(folder/'arm-cue.original.wav')

 cold_args=command('tests/motion_parts_read.gd',extra=['--',str(folder)],project=folder/'part-motion.has');cold=subprocess.run(cold_args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
 text=cold.stdout+cold.stderr;(folder/'cold.log').write_text(text,encoding='utf-8');assert cold.returncode==0 and 'MOTION_PARTS_READ ' in text and not any(x in text for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
 cold_receipt=Path(cold_args[cold_args.index('--receipt')+1]);cr=json.loads(cold_receipt.read_text());assert cr['exit']==0 and cr['child_desktop_confirmed'] and not cr['foreground_child_observed'] and cr['job_closed'] and cr['desktop_closed']
 reader=json.loads((folder/'reader.json').read_text());assert reader['failures']==0
 result.update(folder=str(folder),private_receipt=str(receipt),source_sha256=sha,video=v,cue_samples=[active[0],active[-1]],reader={**reader,'private_receipt':str(cold_receipt)})
 (ROOT/'output/motion-parts-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
