"""Current skin/morph framing versus independent engine snapshots, all GPU work hidden."""
from pathlib import Path
from native_fixture_root import fixture_output
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare
def main():
    folder=ROOT/'output/pose-bounds'/str(time.time_ns());folder.mkdir(parents=True)
    originals=prepare(folder);plans=[{'label':'Shaped','source':str(folder/'shape.glb')}]
    plans+=json.loads((folder/'native-plans.json').read_text(encoding='utf-8'))
    native=(fixture_output()/'native-import-verification.json')
    if native.is_file():
        for bundle in json.loads(native.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);report=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if report.get('kind')!='vrm_preparation':continue
            path=bundle/'scene.glb';plans.append({'label':'VRM'+report['vrm_version'],'source':str(path)})
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'plans.json').write_text(json.dumps(plans),encoding='utf-8')
    args=command('tests/pose_bounds_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=210)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    if p.returncode or 'POSE_BOUNDS ' not in log or any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']):raise RuntimeError(log)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    for path,state in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==state,path
    video=next(s for s in json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    receipt=json.loads(Path(args[3]).read_text());assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result['private_receipt']=args[3];(ROOT/'output/pose-bounds-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
