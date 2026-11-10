"""Real hidden GPU animation, block ownership, native shapes, HAS and MP4."""
from pathlib import Path
from native_fixture_root import fixture_output
import hashlib
import json
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare

def main():
    folder=ROOT/'output/shape-animation'/str(time.time_ns());folder.mkdir(parents=True)
    originals=prepare(folder)
    legacy_report=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\shape-animation-verification.json')
    legacy=None
    if legacy_report.is_file():
        old_report=json.loads(legacy_report.read_text(encoding='utf-8'))
        candidate=Path(old_report['legacy_source']) if old_report.get('legacy_source') else Path(old_report['folder'])/'animated-packed.has'
        if candidate.is_file():
            import zipfile
            with zipfile.ZipFile(candidate) as archive:
                project=json.loads(archive.read('project.json'))
            if any(row.get('format')=='studio_model_4' for row in project.get('world',{}).get('objects',[])):
                legacy=str(candidate)
                originals[candidate]=(hashlib.sha256(candidate.read_bytes()).hexdigest(),candidate.stat().st_mtime_ns)
    (folder/'legacy-project.json').write_text(json.dumps({'path':legacy}),encoding='utf-8')
    plan_path=folder/'native-plans.json';plans=json.loads(plan_path.read_text(encoding='utf-8'))
    native_report=(fixture_output()/'native-import-verification.json')
    if native_report.is_file():
        for bundle in json.loads(native_report.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);report=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if report.get('kind')!='vrm_preparation':continue
            path=bundle/'scene.glb';label='VRM1' if report['vrm_version'].startswith('1') else 'VRM0'
            plans.append({'label':label,'source':str(path),'metadata':{}})
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
            original=Path.home()/'Desktop'/report['source_file']
            if original.is_file():originals[original]=(hashlib.sha256(original.read_bytes()).hexdigest(),original.stat().st_mtime_ns)
    plan_path.write_text(json.dumps(plans),encoding='utf-8')
    for script,headless,marker in [('tests/shape_animation_unit.gd',True,'SHAPE_ANIMATION_UNIT '),('tests/shape_animation_smoke.gd',False,'SHAPE_ANIMATION ')]:
        cmd=command(script,headless=headless,extra=['--',str(folder)])
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200)
        log=p.stdout+p.stderr;(folder/(Path(script).stem+'.log')).write_text(log,encoding='utf-8')
        if p.returncode or marker not in log or '"failures":0' not in log or any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']):raise RuntimeError(log)
    result=json.loads((folder/'animated-result.json').read_text(encoding='utf-8'))
    for path,expected in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==expected
    p=subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],capture_output=True,text=True,check=True)
    video=next(s for s in json.loads(p.stdout)['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    receipt=json.loads(Path(cmd[3]).read_text(encoding='utf-8'))
    assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result.update(folder=str(folder),private_receipt=cmd[3],legacy_source=legacy);(ROOT/'output/shape-animation-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
