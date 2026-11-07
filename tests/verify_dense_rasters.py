"""Measure unique full-HD cold-raster staging independently of the ordinary app."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
from tools.drawing_limits import MAX_CELS

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--count',type=int,choices=[32,128,400],default=400);args=parser.parse_args()
    folder=(args.output or ROOT/'output/dense-rasters'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    argv=command('tests/cel_raster_dense_benchmark.gd',headless=True,extra=['--log-file',str(folder/'engine.log'),'--',str(folder),str(args.count)])
    max_rss=max_hwm=0;samples=0;started=time.monotonic()
    with (folder/'console.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        while process.poll() is None:
            if time.monotonic()-started>900:process.kill();process.wait();raise TimeoutError('Owned dense raster benchmark exceeded900seconds; partial artifacts retained')
            if sys.platform=='linux':
                try:
                    fields={row.split(':',1)[0]:row.split(':',1)[1].strip() for row in Path('/proc',str(process.pid),'status').read_text().splitlines() if ':' in row}
                    max_rss=max(max_rss,int(fields.get('VmRSS','0 kB').split()[0])*1024);max_hwm=max(max_hwm,int(fields.get('VmHWM','0 kB').split()[0])*1024);samples+=1
                except (OSError,ValueError):pass
            time.sleep(.05)
    text=(folder/'console.log').read_text();assert process.returncode==0 and 'DENSE_RASTER_BENCHMARK ' in text and not any(token in text for token in ['ERROR:','FAIL ','ObjectDB instances leaked']),text[-8000:]
    result=json.loads((folder/'result.json').read_text());assert result['failures']==0 and result['count']==args.count and result['unique_pixel_identities']==args.count and result['original_sources_unchanged']
    if args.count==400 and sys.platform=='linux':assert samples>0 and max_hwm<1024**3,'Observed Linux benchmark process exceeded1GiB; do not infer dense-project readiness'
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');movie=folder/'dense-preview.mp4'
    conversion=subprocess.run([ffmpeg,'-v','error','-framerate','24','-i',str(Path(result['sequence'])/'frame_%06d.png'),'-frames:v',str(result['composite_frames']),'-c:v','libx264','-pix_fmt','yuv420p','-y',str(movie)],capture_output=True,text=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    assert conversion.returncode==0,conversion.stderr
    probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',str(movie)]));video=next(s for s in media['streams'] if s['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1',str(result['composite_frames']))
    proof=dict(result=result,video=video,process=dict(observed_max_rss_bytes=max_rss,observed_max_hwm_bytes=max_hwm,linux_samples=samples,wall_seconds=time.monotonic()-started,note='Linux samples50ms; OS high-water observations include fixture/oracle work, not total session/GPU memory. NonLinux processRSS unmeasured.'),source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/cel_raster_reader.gd','src/cel_raster_snapshot.gd','src/cel_raster_snapshot_cache.gd','src/cel_raster_owner.gd','src/cel_pixel_history.gd','src/drawing.gd','tests/cel_raster_dense_benchmark.gd','tests/verify_dense_rasters.py']},production_cel_limit=MAX_CELS)
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
