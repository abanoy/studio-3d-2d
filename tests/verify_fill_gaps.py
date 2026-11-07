import argparse,hashlib,os
"""Independent square-kernel reference and actual private gap-fill workflow."""
from pathlib import Path
import base64,json,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display
def reference(path):
    domain=json.loads(path.read_bytes());cases=domain.pop('cases')
    for case in cases:
        w,h,g=case['width'],case['height'],case['gap'];source=base64.b64decode(case['input']);left=g//2;right=g-left
        # Full two-dimensional neighborhoods, independent of rolling sums and
        # separability. Erosion uses neutral1 padding; dilation uses neutral0.
        eroded=bytes(int(all(source[yy*w+xx] if 0<=xx<w and 0<=yy<h else 1 for yy in range(y-left,y+right+1) for xx in range(x-left,x+right+1))) for y in range(h) for x in range(w))
        closed=bytes(int(source[y*w+x] and any(eroded[yy*w+xx] if 0<=xx<w and 0<=yy<h else 0 for yy in range(y-right,y+left+1) for xx in range(x-right,x+left+1))) for y in range(h) for x in range(w))
        assert closed==base64.b64decode(case['output']),(w,h,g)
    domain.update(independent_masks=len(cases),mask_differences=0);return domain
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/fill-gaps'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);results=[];receipts=[]
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    for label,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/fill_gaps_unit.gd' if headless else 'tests/fill_gaps_smoke.gd'
        args=command(script,headless=headless,extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=220)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');marker='FILL_GAPS_UNIT ' if headless else 'FILL_GAPS_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:domain=reference(folder/'domain.json')
        elif os.name=='nt':
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:assert not any(s in z.read('project.json') for s in [b'gap_pixels',b'close_gaps',b'sealed_pixels'])
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),domain=domain,results=results,private_receipts=receipts,pixels_exact=True)
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    result.update(source_sha256=frozen,isolated_display=options.isolated_display)
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'output/fill-gaps-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
