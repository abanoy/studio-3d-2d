"""Shot/editor projection isolation, original large scene, native project and movie."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(o.isolated_display)
    folder=(o.output or ROOT/'output/camera-range'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
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
    args=command('tests/camera_range_smoke.gd',extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=210)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    if p.returncode or 'CAMERA_RANGE ' not in log or any(s in log for s in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')):raise RuntimeError(log)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    for path,state in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
    video=next(s for s in json.loads(subprocess.check_output([str(probe),'-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    if os.name=='nt':
        receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_text());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
        result['private_receipt']=str(receipt_path)
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
    result.update(source_sha256=frozen,isolated_display=o.isolated_display,native_fixture_count=len(plans),video=video,scope='Original far-scene and reference fixtures; native coverage only for explicitly available prepared plans, never inferred from original fixtures.')
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'output/camera-range-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
