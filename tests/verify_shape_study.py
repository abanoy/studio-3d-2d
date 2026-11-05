"""Real six-native worker/UI/adoption/Undo/HAS, hidden Windows GPU only."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare


def main():
    folder=ROOT/'output/shape-study-tests'/str(time.time_ns());folder.mkdir(parents=True)
    for name in ['test_shape_observations.py','test_shape_study_worker.py']:
        p=subprocess.run([sys.executable,str(ROOT/'tests'/name)],cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=30)
        (folder/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr
    originals=prepare(folder)
    old=ROOT/'output/shape-catalog-verification.json'
    if old.is_file():
        catalogue=json.loads(old.read_text());prior=json.loads((Path(catalogue['folder'])/'catalogue-plans.json').read_text(encoding='utf-8'))
    else:prior=[{}]+json.loads((folder/'native-plans.json').read_text(encoding='utf-8'))
    plans=[{'label':'Authored fixture','source':str(folder/'shape.glb')}]+prior[1:]
    for plan in plans:
        path=Path(plan['source']);originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'plans.json').write_text(json.dumps(plans),encoding='utf-8')
    args=command('tests/shape_study_smoke.gd',extra=['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=200)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'SHAPE_STUDY_APP 'in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-7000:]
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    reader_args=command('tests/shape_study_smoke.gd',extra=['--',str(folder),'reader'])
    p=subprocess.run(reader_args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=60)
    log=p.stdout+p.stderr;(folder/'reader-engine.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'SHAPE_STUDY_READER 'in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    cold=json.loads((folder/'reader-result.json').read_text());assert cold['failures']==0
    cold_receipt=Path(reader_args[reader_args.index('--receipt')+1]);r=json.loads(cold_receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    teardown_args=command('tests/shape_study_teardown.gd',extra=['--',str(folder)])
    p=subprocess.run(teardown_args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=45)
    log=p.stdout+p.stderr;(folder/'teardown-engine.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'SHAPE_STUDY_TEARDOWN 'in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    teardown=json.loads((folder/'teardown-result.json').read_text());assert teardown['failures']==0
    teardown_receipt=Path(teardown_args[teardown_args.index('--receipt')+1]);r=json.loads(teardown_receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',result['movie']],encoding='utf-8'))
    v=next(row for row in probe['streams']if row['codec_type']=='video');assert(v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')and abs(float(probe['format']['duration'])-2)<.001
    for path,value in originals.items():assert (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==value,path
    result.update(folder=str(folder),private_receipts=[str(receipt),str(cold_receipt),str(teardown_receipt)],unit_tests=17,reader=cold,teardown=teardown,native_fixtures_optional=True)
    (ROOT/'output/shape-study-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))


if __name__=='__main__':main()
