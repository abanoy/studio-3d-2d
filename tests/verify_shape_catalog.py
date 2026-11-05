"""Shared catalogue unit/UI/metadata/Undo/HAS/cold Open/movie, private GPU only."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare

def execute(script,folder,extra,marker,headless=False):
    args=command(script,headless=headless,extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=205)
    log=p.stdout+p.stderr;(folder/(Path(script).stem+('-reader' if extra else '')+'.log')).write_text(log,encoding='utf-8')
    assert p.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-6500:]
    if headless:return json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)))
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text(encoding='utf-8'));assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];return str(receipt)

def main():
    folder=ROOT/'output/shape-catalog'/str(time.time_ns());folder.mkdir(parents=True);originals=prepare(folder)
    plans=[{'label':'Authored fixture','source':str(folder/'shape.glb')}]+json.loads((folder/'native-plans.json').read_text(encoding='utf-8'))
    native=Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\native-import-verification.json')
    if native.is_file():
        for name in json.loads(native.read_text(encoding='utf-8')).get('bundles',[]):
            bundle=Path(name);report=json.loads((bundle/'parameters.json').read_text(encoding='utf-8'))
            if report.get('kind')=='vrm_preparation':plans.append({'label':'VRM'+report['vrm_version'],'source':str(bundle/'scene.glb')})
    face=ROOT/'output/sfm-face-pilot.json'
    if face.is_file():
        report=json.loads(face.read_text(encoding='utf-8'))
        if report.get('preparation_complete'):plans.append({'label':'Supplied Mima','source':str(Path(report['bundle'])/'scene.glb')})
    for plan in plans:
        path=Path(plan['source']);originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'catalogue-plans.json').write_text(json.dumps(plans),encoding='utf-8')
    unit=execute('tests/shape_catalog_unit.gd',folder,[],'SHAPE_CATALOG_UNIT ',True);assert unit['failures']==0
    receipt=execute('tests/shape_catalog_smoke.gd',folder,[],'SHAPE_CATALOG_APP ')
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert result['failures']==0
    cold=execute('tests/shape_catalog_smoke.gd',folder,['reader'],'SHAPE_CATALOG_READER ');reader=json.loads((folder/'reader-result.json').read_text(encoding='utf-8'));assert reader['failures']==0
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],encoding='utf-8'));v=next(v for v in probe['streams'] if v['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(probe['format']['duration'])-2)<.001
    for path,value in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==value,path
    result.update(folder=str(folder),unit_checks=unit['checks'],private_receipts=[receipt,cold],reader=reader,native_fixtures_optional=True)
    (ROOT/'output/shape-catalog-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
