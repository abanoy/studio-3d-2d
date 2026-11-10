"""Real UI fan/secondary/body/Record/HAS/MP4 checks, with optional owner VRMs."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command
from verify_native_import import private_vrm
def main():
    paths=[];before={}
    for name in ['AvatarSample_A.vrm','AvatarSample_Avrm0.vrm']:
        path=private_vrm(name)
        if path.is_file():paths.append(str(path));before[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
        else:print('SKIP optional native fan sample: '+name)
    args=command('tests/fan_motion_smoke.gd',extra=['--',*paths])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=230)
    log=p.stdout+p.stderr;(ROOT/'output/fan-motion-verification.log').write_text(log,encoding='utf-8')
    for path,state in before.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
    if p.returncode or 'FAN_MOTION ' not in log or any(x in log for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):raise RuntimeError(log)
    result=json.loads((ROOT/'output/fan-motion-result.json').read_text(encoding='utf-8'));assert result['failures']==0,result
    receipt=Path(args[args.index('--receipt')+1]);private=json.loads(receipt.read_bytes())
    assert private['exit']==0 and private['child_desktop_confirmed'] and not private['foreground_child_observed'] and private['job_closed'] and private['desktop_closed'],private
    result['private_receipt']=str(receipt)
    probe=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],capture_output=True,text=True,check=True)
    video=next(x for x in json.loads(probe.stdout)['streams'] if x['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1'),video
    result['originals']={str(p):state[0] for p,state in before.items()};result['video']={k:video[k] for k in ['codec_name','width','height','nb_read_frames','r_frame_rate','duration']}
    (ROOT/'output/fan-motion-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
