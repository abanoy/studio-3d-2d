import argparse,os
"""Experimental independent body contract; normal editor integration remains open."""
from pathlib import Path
from native_fixture_root import fixture_output
import hashlib
import json
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command,configure_private_display
from verify_source_shapes import prepare
from native_fixture_plans import recorded_native_models

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/body-curves'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);receipts=[];reports={}
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','data','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    originals=prepare(folder)
    plan_path=folder/'native-plans.json';plans=json.loads(plan_path.read_text(encoding='utf-8'))
    names={'MMD':('左腕','右腕'),'GMod':('L_UpperArm','R_UpperArm'),'SFM':('bip_upperArm_L','bip_upperArm_R')}
    for plan in plans:plan['left'],plan['right']=names[plan['label']]
    native=(fixture_output()/'native-import-verification.json')
    if native.is_file():
        for bundle in json.loads(native.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);report=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if report.get('kind')!='vrm_preparation':continue
            path=bundle/'scene.glb';label='VRM1' if report['vrm_version'].startswith('1') else 'VRM0'
            plans.append({'label':label,'source':str(path),'metadata':{},'left':'J_Bip_L_UpperArm','right':'J_Bip_R_UpperArm'})
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    plan_path.write_text(json.dumps(plans),encoding='utf-8')
    recorded,path=recorded_native_models()
    if path is not None:originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'recorded-models.json').write_text(json.dumps(recorded),encoding='utf-8')
    for script,headless,marker in [('tests/body_curves_unit.gd',True,'BODY_CURVES_UNIT '),('tests/body_curves_smoke.gd',False,'BODY_CURVES ')]:
        cmd=command(script,headless=headless,extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+['--',str(folder)])
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=p.stdout+p.stderr;(folder/(Path(script).stem+'.log')).write_text(log,encoding='utf-8')
        if p.returncode or marker not in log or '"failures":0' not in log or any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked')):raise RuntimeError(log)
        reports[marker.strip()]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)))
        if os.name=='nt' and not headless:
            path=Path(cmd[cmd.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    for path,expected in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==expected
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    p=subprocess.run([ffprobe,'-v','error','-count_frames','-show_streams','-of','json',result['movie']],capture_output=True,text=True,check=True)
    video=next(s for s in json.loads(p.stdout)['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    result.update(folder=str(folder),source_sha256=frozen,reports=reports,private_receipts=receipts,video=video,isolated_display=options.isolated_display,native_fixture_count=len(plans),scope='Authored independent skinned branches and explicitly available native plans; original fixture does not certify native-format fidelity.')
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'output/body-curves-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))

if __name__=='__main__':main()
