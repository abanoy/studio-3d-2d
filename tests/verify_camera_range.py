"""Shot/editor projection isolation, original large scene, native project and movie."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    folder=ROOT/'output/camera-range'/str(time.time_ns());folder.mkdir(parents=True)
    plans=[];originals={};base=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output')
    for label,relative in [('MMD','pose-smoke/miku-project'),('GMod','source-smoke/source-project'),('SFM','sfm-smoke/project')]:
        project=base/relative
        if not (project/'project.json').is_file():continue
        doc=json.loads((project/'project.json').read_text(encoding='utf-8'));row=doc.get('model',{}) or doc['world']['objects'][-1]
        plans.append({'label':label,'source':str(project/row['path']),'metadata':row.get('metadata',{})})
    report=base/'native-import-verification.json'
    if report.is_file():
        for bundle in json.loads(report.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);parameters=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if parameters.get('kind')=='vrm_preparation':plans.append({'label':'VRM'+parameters['vrm_version'],'source':str(bundle/'scene.glb'),'metadata':{}})
    for plan in plans:
        path=Path(plan['source']);originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'native-plans.json').write_text(json.dumps(plans),encoding='utf-8')
    args=command('tests/camera_range_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=210)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    if p.returncode or 'CAMERA_RANGE ' not in log or any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')):raise RuntimeError(log)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    for path,state in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
    video=next(s for s in json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    receipt=json.loads(Path(args[3]).read_text());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result['private_receipt']=args[3];(ROOT/'output/camera-range-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
