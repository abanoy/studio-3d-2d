"""Normal independent body editing, native persistence, recovery and export."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare

def main():
    folder=ROOT/'output/body-animation'/str(time.time_ns());folder.mkdir(parents=True)
    originals=prepare(folder)
    plan_path=folder/'native-plans.json';plans=json.loads(plan_path.read_text(encoding='utf-8'))
    names={'MMD':('左腕','右腕'),'GMod':('L_UpperArm','R_UpperArm'),'SFM':('bip_upperArm_L','bip_upperArm_R')}
    for plan in plans:plan['left'],plan['right']=names[plan['label']]
    native=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output/native-import-verification.json')
    if native.is_file():
        for bundle in json.loads(native.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);report=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if report.get('kind')!='vrm_preparation':continue
            path=bundle/'scene.glb';label='VRM1' if report['vrm_version'].startswith('1') else 'VRM0'
            plans.append({'label':label,'source':str(path),'metadata':{},'left':'J_Bip_L_UpperArm','right':'J_Bip_R_UpperArm'})
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    plan_path.write_text(json.dumps(plans),encoding='utf-8')
    recorded=[]
    capture=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output/physics-recording-verification.json')
    if capture.is_file():
        path=Path(json.loads(capture.read_text(encoding='utf-8'))['folder'])/'native-recording.has'
        if path.is_file():
            with zipfile.ZipFile(path) as archive:document=json.loads(archive.read('project.json'))
            recorded=[row for row in document['world']['objects'] if row.get('kind')=='model']
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'recorded-models.json').write_text(json.dumps(recorded),encoding='utf-8')
    for script,headless,marker in [('tests/body_animation_unit.gd',True,'BODY_ANIMATION_UNIT '),('tests/body_animation_smoke.gd',False,'BODY_ANIMATION ')]:
        cmd=command(script,headless=headless,extra=['--',str(folder)])
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=p.stdout+p.stderr;(folder/(Path(script).stem+'.log')).write_text(log,encoding='utf-8')
        if p.returncode or marker not in log or '"failures":0' not in log or any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked')):raise RuntimeError(log)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    for path,expected in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==expected
    p=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],capture_output=True,text=True,check=True)
    video=next(s for s in json.loads(p.stdout)['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    receipt=json.loads(Path(cmd[3]).read_text(encoding='utf-8'))
    assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result.update(folder=str(folder),private_receipt=cmd[3]);(ROOT/'output/body-animation-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
