"""Reference-sheet viewed-region guide, alignment, source preservation, Undo and MP4."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: explicitly provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=(options.output or ROOT/'output/reference-alignment'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    args=command('tests/reference_alignment_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder)])
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=160)
    log=p.stdout+p.stderr;(folder/'writer.log').write_text(log,encoding='utf-8');marker='REFERENCE_ALIGNMENT_SMOKE '
    assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    result=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert result['failures']==0
    receipts=[]
    if os.name=='nt':
        receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
        receipts.append(str(receipt))
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    media=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',result['movie']],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
    video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48') and abs(float(media['format']['duration'])-2)<.001
    result.update(video=video,private_receipts=receipts,isolated_display=options.isolated_display,physical_input_tested=False,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
