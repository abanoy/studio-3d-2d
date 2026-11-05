"""Run actual declared-chain wind experiments, with optional owner VRM0/1."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
from prepare_vrm import prepare

def main():
    output=ROOT/'output';output.mkdir(exist_ok=True)
    folder=output/'secondary-motion'/('inputs_'+str(time.time_ns()));folder.mkdir(parents=True)
    paths=[];originals={}
    for name,label in [('AvatarSample_A.vrm','vrm1'),('AvatarSample_Avrm0.vrm','vrm0')]:
        path=Path('C:/Users/noble/Desktop')/name
        if not path.is_file():print('SKIP optional owner sample: '+name);continue
        originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
        paths.append(prepare(path,folder/label)['glb'])
    p=subprocess.run(command('tests/secondary_motion_smoke.gd',extra=['--',*paths]),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    log=p.stdout+p.stderr;(output/'secondary-motion-verification.log').write_text(log,encoding='utf-8')
    for path,before in originals.items():
        assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==before,path
    if p.returncode or 'SECONDARY_MOTION ' not in log or any(x in log for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):raise RuntimeError(log)
    result=json.loads((output/'secondary-motion-result.json').read_text(encoding='utf-8'))
    assert result['failures']==0,result
    result['video']=[]
    for movie in result['movies']:
        probe=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',movie],capture_output=True,text=True,check=True)
        video=next(s for s in json.loads(probe.stdout)['streams'] if s['codec_type']=='video')
        assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1'),video
        assert abs(float(video['duration'])-2)<0.000001,video
        result['video'].append({k:video[k] for k in ['codec_name','width','height','nb_read_frames','r_frame_rate','duration']})
    result['originals']={str(p):v[0] for p,v in originals.items()}
    (output/'secondary-motion-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
