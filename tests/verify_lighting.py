"""Project lighting, material isolation/fades, native rigs, HAS and hidden GPU export."""
from pathlib import Path
from native_fixture_root import fixture_output
import argparse,os,json,subprocess,sys,time,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command,configure_private_display
from verify_source_shapes import prepare
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/lighting'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    originals=prepare(folder)
    plan_path=folder/'native-plans.json';plans=json.loads(plan_path.read_text(encoding='utf-8'))
    native=(fixture_output()/'native-import-verification.json')
    if native.is_file():
        for bundle in json.loads(native.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(bundle);report=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if report.get('kind')!='vrm_preparation':continue
            path=bundle/'scene.glb';plans.append({'label':'VRM'+report['vrm_version'],'source':str(path),'metadata':{}})
            originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    plan_path.write_text(json.dumps(plans),encoding='utf-8')
    args=command('tests/lighting_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'godot.log'),'--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    if p.returncode or 'LIGHTING ' not in log or '"failures":0' not in log or any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']):raise RuntimeError(log)
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    for path,expected in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==expected
    ffmpeg=os.environ.get('HYBRID_FFMPEG','C:/Program Files/ffmpeg/bin/ffmpeg.exe' if os.name=='nt' else '/usr/bin/ffmpeg')
    ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    receipt=None
    if os.name=='nt':
        receipt=Path(args[args.index('--receipt')+1]);desktop=json.loads(receipt.read_bytes());assert desktop['exit']==0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
    result.update(source_sha256=frozen,video=video,isolated_display=options.isolated_display,native_fidelity_certified=False,physical_device_certified=False)
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    result['private_receipt']=str(receipt) if receipt else None;(ROOT/'output/lighting-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
