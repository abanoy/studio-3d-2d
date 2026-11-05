"""Real live ragdolls, connected Simple controls, freeze/HAS and static MP4 checks."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command
def main():
 p=subprocess.run(command('tests/physics_smoke.gd'),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
 text=p.stdout+p.stderr
 (ROOT/'output/physics-verification.log').write_text(text,encoding='utf-8')
 if p.returncode or 'PHYSICS_SMOKE ' not in text or '"failures":0' not in text or any(x in text for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):raise RuntimeError(text)
 report=json.loads((ROOT/'output/physics-result.json').read_text(encoding='utf-8'))
 probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],text=True,encoding='utf-8'))
 video=next(x for x in probe['streams'] if x['codec_type']=='video')
 assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
 assert abs(float(probe['format']['duration'])-2)<0.001
 assert not any(x['codec_type']=='audio' for x in probe['streams'])
 report['video']={'codec':'h264','width':1920,'height':1080,'fps':'24/1','frames':48,'duration':probe['format']['duration'],'audio':False}
 (ROOT/'output/physics-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
