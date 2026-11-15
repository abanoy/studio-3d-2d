"""Real hidden in-app native preparation, adoption, cold save and MP4 proof."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    source=Path(os.environ.get('HYBRID_HECATIA_KRA','C:/a/Programming/cloudflare/prototypes/artist-animation-assistant/samples/hecatia.kra')).resolve(strict=True)
    before=(hashlib.sha256(source.read_bytes()).hexdigest(),source.stat().st_mtime_ns)
    assert before[0]=='fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758','This historical verifier requires the original 19-layer Hecatia fixture; use HYBRID_HECATIA_KRA to select its unchanged local copy.'
    folder=ROOT/'output/krita-import'/str(time.time_ns());folder.mkdir(parents=True);reports={};receipts=[]
    for label,extra in [('writer',[str(folder),str(source)]),('reader',[str(folder),'--read'])]:
        args=command('tests/krita_import_smoke.gd',extra=['--',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=205,creationflags=subprocess.CREATE_NO_WINDOW);raw=p.stdout+p.stderr;(folder/(label+'.log')).write_bytes(raw)
        assert p.returncode==0 and b'KRITA_IMPORT_' in raw and not any(s in raw for s in [b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked']),raw.decode('utf-8',errors='replace')
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
        marker='KRITA_IMPORT_'+('SMOKE ' if label=='writer' else 'READ ');line=next(s for s in raw.decode('utf-8',errors='replace').splitlines() if s.startswith(marker));reports[label]=json.loads(line[len(marker):]);assert reports[label]['failures']==0
    native=Path(reports['writer']['native_job'])/'prepared/private-desktop.json';r=json.loads(native.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(native))
    stopped=Path(reports['writer']['cancelled_job'])/'prepared/private-desktop.json';r=json.loads(stopped.read_bytes());assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    metadata=json.loads(subprocess.check_output(['C:/Program Files/ffmpeg/bin/ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']],text=True,creationflags=subprocess.CREATE_NO_WINDOW));video=next(s for s in metadata['streams'] if s['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    for name in ['Krita scene.has','Krita scene linked.has']:
        with zipfile.ZipFile(folder/name) as z:
            manifest=json.loads(z.read('project.json'));origin=manifest['layers'][2]['origin'];assert origin['name']=='hecatia.kra' and 'path' not in origin and len(manifest['layers'][2]['cels'])==8
            assert all(c['path'] in z.namelist() for c in manifest['layers'][2]['cels'])
    assert (hashlib.sha256(source.read_bytes()).hexdigest(),source.stat().st_mtime_ns)==before
    result={'folder':str(folder),'reports':reports,'private_receipts':receipts,'cancelled_receipt':str(stopped),'video':video,'portable_imported_pixels':True,'source_sha256':before[0],'source_unchanged':True};(ROOT/'output/krita-import-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='video'},indent=2))
if __name__=='__main__':main()
