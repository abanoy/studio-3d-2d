"""Exact static map measurement through actual GPU picking, HAS and ordinary MP4."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from run import command
def main():
    folder=ROOT/'output/map-calibration'/str(time.time_ns());folder.mkdir(parents=True)
    native='';originals={};source_report=ROOT/'output/source-verification.json'
    if source_report.is_file():
        r=json.loads(source_report.read_text(encoding='utf-8'));candidate=Path(r['map_bundle'])/'scene.glb'
        if candidate.is_file():native=str(candidate);originals[candidate]=(hashlib.sha256(candidate.read_bytes()).hexdigest(),candidate.stat().st_mtime_ns)
    (folder/'native-map.txt').write_text(native,encoding='utf-8');results=[];receipts=[]
    for name,extra in [('app',[]),('reader',['reader'])]:
        args=command('tests/map_calibration_smoke.gd',extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=175)
        log=p.stdout+p.stderr;(folder/(name+'.log')).write_text(log,encoding='utf-8');(folder/(name+'-command.json')).write_text(json.dumps({'args':args,'exit':p.returncode}))
        assert p.returncode==0 and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-7000:]
        tag='MAP_CALIBRATION_'+name.upper()+' ';r=json.loads(next(line.split(tag,1)[1]for line in log.splitlines()if line.startswith(tag)));assert r['failures']==0;results.append(r)
        receipt=Path(args[args.index('--receipt')+1]);record=json.loads(receipt.read_text());assert record['exit']==0 and record['child_desktop_confirmed']and not record['foreground_child_observed']and record['job_closed']and record['desktop_closed'];receipts.append(str(receipt))
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',results[0]['movie']],encoding='utf-8'));v=next(v for v in probe['streams']if v['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')and abs(float(probe['format']['duration'])-2)<.001
    for path,value in originals.items():assert(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==value
    result={'checks':sum(r['checks']for r in results),'failures':0,'folder':str(folder),'results':results,'private_receipts':receipts,'native_source':native}
    (ROOT/'output/map-calibration-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
