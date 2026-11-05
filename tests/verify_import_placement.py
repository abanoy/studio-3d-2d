"""Bounded near-camera placement, grounding, overlap fallback and native map checks."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command


def main():
    p=subprocess.run(command('tests/import_placement_smoke.gd'),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=110)
    text=p.stdout+p.stderr
    (ROOT/'output/import-placement-verification.log').write_text(text,encoding='utf-8')
    if p.returncode or '"failures":0' not in text or any(s in text for s in ('SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','another exclusive child')):raise RuntimeError(text)
    report=json.loads((ROOT/'output/import-placement-result.json').read_text(encoding='utf-8'))
    p=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],capture_output=True,text=True,check=True)
    probe=json.loads(p.stdout);video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(probe['format']['duration'])-2)<.001
    report['video']={'codec':'h264','size':[1920,1080],'fps':'24/1','frames':48,'duration':'2.000000'}
    (ROOT/'output/import-placement-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
