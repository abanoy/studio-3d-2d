"""Source-time block/part adapter; not normal editor/storage activation."""
from pathlib import Path
import json, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    folder=ROOT/'output/motion-assist-tracks'/str(time.time_ns());folder.mkdir(parents=True)
    p=subprocess.run(command('tests/motion_assist_tracks_unit.gd',headless=True),cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=50)
    text=p.stdout+p.stderr;(folder/'unit.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'MOTION_ASSIST_TRACKS_UNIT ' in text and not any(v in text for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
    result=json.loads(next(line.removeprefix('MOTION_ASSIST_TRACKS_UNIT ') for line in text.splitlines() if line.startswith('MOTION_ASSIST_TRACKS_UNIT ')))
    result.update(folder=str(folder),normal_editor_integrated=False)
    (ROOT/'output/motion-assist-tracks-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
