"""Real raster/editor/save/cold Open/movie checks; graphical jobs stay private."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=ROOT/'output/brush-opacity'/str(time.time_ns());folder.mkdir(parents=True)
    results=[];receipts=[]
    for name,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/brush_opacity_unit.gd' if headless else 'tests/brush_opacity_smoke.gd'
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),'--demo-room',*extra])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=175)
        log=p.stdout+p.stderr;(folder/(name+'.log')).write_text(log,encoding='utf-8')
        marker='BRUSH_OPACITY_UNIT ' if headless else 'BRUSH_OPACITY_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ('SCRIPT ERROR','SHADER ERROR','ERROR:','FAIL ','ObjectDB instances leaked')),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if not headless and os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
            receipts.append(str(receipt))
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:
        raw=z.read('project.json');assert b'brush_opacity' not in raw and b'coverage_tiles' not in raw and b'studio_pixels' not in raw
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    result.update(folder=str(folder),results=results,private_receipts=receipts,pixels_exact=True,isolated_display=options.isolated_display)
    (ROOT/'output/brush-opacity-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
