"""Interactive automatic ragdolls, existing live peers, explicit Record and hidden GPU."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare
def main():
    folder=ROOT/'output/import-physics'/str(time.time_ns());folder.mkdir(parents=True)
    originals=prepare(folder)
    plans=json.loads((folder/'native-plans.json').read_text(encoding='utf-8'))
    for index,plan in enumerate(plans):
        target=folder/('native-'+str(index));target.mkdir()
        shutil.copy2(plan['source'],target/'scene.glb')
        parameters=plan['metadata'].get('native_parameters')
        if parameters:(target/'parameters.json').write_text(json.dumps(parameters),encoding='utf-8')
        plan['source']=str(target/'scene.glb')
    report=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\native-import-verification.json')
    if report.is_file():
        for bundle in json.loads(report.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);parameters=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if parameters.get('kind')!='vrm_preparation':continue
            path=bundle/'scene.glb';plans.append({'source':str(path),'label':'VRM'+parameters['vrm_version']})
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'native-plans.json').write_text(json.dumps(plans),encoding='utf-8')
    args=command('tests/import_physics_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=210)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    if p.returncode or 'IMPORT_PHYSICS ' not in log or any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']):raise RuntimeError(log)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    for path,state in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(video['duration'])-2)<.001,video
    receipt=json.loads(Path(args[3]).read_text());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result['private_receipt']=args[3];result['video']={k:video[k] for k in ['codec_name','width','height','r_frame_rate','nb_read_frames','duration']}
    (ROOT/'output/import-physics-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
