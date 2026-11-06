"""Bounded delivery sizes, alpha-safe PNG, captured movie/retry settings and cold source preservation."""
from pathlib import Path
import argparse,array,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display,command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/output-size'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports={};receipts=[]
    def run(script,label,marker,headless=False,extra=()):
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240);log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        reports[label]=json.loads(next(s[len(marker):] for s in log.splitlines() if s.startswith(marker)));assert reports[label]['failures']==0
        if os.name=='nt' and not headless:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    run('tests/output_size_unit.gd','unit','OUTPUT_SIZE_UNIT ',True)
    run('tests/output_size_smoke.gd','writer','OUTPUT_SIZE_SMOKE ')
    manual=(folder/'Delivery.has').read_bytes();(folder/'writer-cache').rename(folder/'writer-cache.offline')
    run('tests/output_size_smoke.gd','reader','OUTPUT_SIZE_READ ',extra=['--read'])
    assert (folder/'Delivery.has').read_bytes()==manual
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    media=[]
    for path in [reports['writer']['movie'],reports['writer']['retry']]:
        meta=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',path],**flags));video=next(s for s in meta['streams'] if s['codec_type']=='video')
        assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1280,720,'24/1','48') and abs(float(meta['format']['duration'])-2)<.001 and any(s['codec_name']=='aac' for s in meta['streams'])
        pcm=array.array('h');pcm.frombytes(subprocess.check_output([ffmpeg,'-v','error','-i',path,'-vn','-ac','1','-ar','48000','-f','s16le','pipe:1'],**flags))
        if sys.byteorder!='little':pcm.byteswap()
        onset=next(i for i,v in enumerate(pcm) if abs(v)>1000);assert abs(onset-48000)<96
        media.append(dict(path=path,video=video,decoded_onset_sample=onset))
    frames=list(Path(reports['writer']['png_folder']).glob('frame_*.png'));assert len(frames)==48
    # Inspect every actual PNG IHDR, independently of the engine's report.
    for p in frames:
        header=p.read_bytes()[:24];assert header[:8]==b'\x89PNG\r\n\x1a\n' and int.from_bytes(header[16:20],'big')==960 and int.from_bytes(header[20:24],'big')==540
    proof=dict(reports=reports,media=media,alpha_png_frames=48,manual_has_unchanged=True,writer_cache_unavailable_for_reader=True,private_receipts=receipts,isolated_display=options.isolated_display,folder=str(folder));(folder/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
