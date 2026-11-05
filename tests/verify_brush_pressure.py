"""Independent taper math, native pressure events, cold HAS and real movie."""
from pathlib import Path
import argparse,base64,json,math,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def reference(path):
    domain=json.loads(path.read_bytes());maximum=0
    # Independent numerical maximization of the swept-disc field, rather than
    # reproducing the renderer's closed-form solution. Source is transparent.
    for case in domain.pop('reference_cases'):
        ax,ay=case['from'];bx,by=case['to'];r0,r1=case['radii'];rgba=base64.b64decode(case['rgba'])
        for y in range(48):
            for x in range(64):
                def field(t):return r0+(r1-r0)*t-math.hypot(x+.5-ax-(bx-ax)*t,y+.5-ay-(by-ay)*t)
                lo,hi=0.,1.
                for _ in range(48):
                    left=(2*lo+hi)/3;right=(lo+2*hi)/3
                    if field(left)<field(right):lo=left
                    else:hi=right
                coverage=max(0.,min(1.,max(field(0),field(1),field((lo+hi)/2))+.5))
                maximum=max(maximum,abs(rgba[(y*64+x)*4+3]-round(coverage*255)))
    assert maximum<=1,maximum
    domain.update(reference_cases=6,independent_alpha_error=maximum);return domain
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux: pre-provisioned private dummy X display')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicit private --isolated-display; no shared-desktop fallback')
        os.environ['DISPLAY']=options.isolated_display
    folder=ROOT/'output/brush-pressure'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/brush_pressure_unit.gd' if headless else 'tests/brush_pressure_smoke.gd'
        args=command(script,headless=headless,extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');marker='BRUSH_PRESSURE_UNIT ' if headless else 'BRUSH_PRESSURE_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:domain=reference(folder/'domain.json')
        elif os.name=='nt':
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(receipt))
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:
        manifest=z.read('project.json');assert not any(x in manifest for x in [b'pressure_size',b'brush_pressure',b'studio_pixels'])
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),domain=domain,results=results,private_receipts=receipts,pixels_exact=True,isolated_display=options.isolated_display)
    (ROOT/'output/brush-pressure-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
