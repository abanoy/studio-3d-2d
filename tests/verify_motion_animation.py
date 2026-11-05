"""Model8 shared evaluation, authored controls and ordinary app persistence."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    folder=ROOT/'output/motion-animation'/str(time.time_ns());folder.mkdir(parents=True)
    args=command('tests/motion_animation_unit.gd',headless=True)
    p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=50)
    text=p.stdout+p.stderr;(folder/'unit.log').write_text(text,encoding='utf-8')
    assert p.returncode==0 and 'MOTION_ANIMATION_UNIT ' in text and not any(v in text for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
    result=json.loads(next(v.removeprefix('MOTION_ANIMATION_UNIT ') for v in text.splitlines() if v.startswith('MOTION_ANIMATION_UNIT ')))
    result.update(folder=str(folder),normal_native_verified=False)
    (ROOT/'output/motion-animation-unit-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
