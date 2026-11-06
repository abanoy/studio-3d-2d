"""Optional smoothing: exact disabled brush, tails/pressure gaps, Undo, physics and output."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import configure_private_display, command

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/stroke-smoothing'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports={};receipts=[];original=None
    for label,script,extra,marker in [('unit','tests/stroke_stabilizer_unit.gd',[],'STROKE_STABILIZER_UNIT '),('writer','tests/stroke_stabilizer_smoke.gd',[],'STROKE_STABILIZER_SMOKE '),('reader','tests/stroke_stabilizer_smoke.gd',['--read'],'STROKE_STABILIZER_READ ')]:
        args=command(script,headless=label=='unit',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;reports[label]=result
        if os.name=='nt' and label!='unit':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(receipt))
        if label=='writer':original=(folder/'Smoothed.has').read_bytes()
        elif label=='reader':assert (folder/'Smoothed.has').read_bytes()==original
    with zipfile.ZipFile(folder/'Smoothed.has') as archive:
        raw=archive.read('project.json');assert not any(s in raw for s in [b'stroke_stabilizer',b'brush_smoothing',b'studio_pixels_revision'])
    probe=str(Path(os.environ['HYBRID_FFMPEG']).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')) if os.environ.get('HYBRID_FFMPEG') else 'ffprobe'
    video=json.loads(subprocess.check_output([probe,'-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_frames','-of','json',reports['writer']['movie']]))['streams'][0]
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==('h264',1920,1080,'24/1','48'),video
    result=dict(reports=reports,video=video,private_receipts=receipts,isolated_display=options.isolated_display,physical_tablet_tested=False,native_fixtures=0,folder=str(folder))
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
