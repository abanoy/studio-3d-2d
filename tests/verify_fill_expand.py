"""Independent flood/dilation oracle and actual private editor/HAS/movie workflow."""
from pathlib import Path
from collections import deque
import base64,json,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def reference(path):
    domain=json.loads(path.read_bytes());cases=domain.pop('cases')
    for c in cases:
        w,h,r=c['width'],c['height'],c['radius'];sample=base64.b64decode(c['sample']);target=base64.b64decode(c['target']);point=tuple(c['point'])
        # Independent per-pixel BFS, then full2D neighborhoods (no production
        # scanlines, separability or rolling sums). Seed is transparent here.
        queue=deque([point]);region={point}
        while queue:
            x,y=queue.popleft()
            for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if 0<=xx<w and 0<=yy<h and (xx,yy) not in region and sample[(yy*w+xx)*4+3]==0:
                    region.add((xx,yy));queue.append((xx,yy))
        grown={(x,y) for y in range(h) for x in range(w) if any((xx,yy) in region for yy in range(y-r,y+r+1) for xx in range(x-r,x+r+1))}
        result=bytearray(target);paint=bytes([30,160,220,170]);changed=[]
        for x,y in grown:
            i=(y*w+x)*4
            if target[i:i+4]!=paint:changed.append((x,y))
            result[i:i+4]=paint
        bounds=[min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)-min(x for x,y in changed)+1,max(y for x,y in changed)-min(y for x,y in changed)+1] if changed else [0,0,0,0]
        assert bytes(result)==base64.b64decode(c['output']),(w,h,r,'pixels')
        assert (c['region'],c['expanded'],c['changed'],c['edge'],c['bounds'])==(len(region),len(grown)-len(region),len(changed),any(x in (0,w-1) or y in (0,h-1) for x,y in grown),bounds),(w,h,r,'metadata')
    domain.update(independent_cases=len(cases),pixel_differences=0);return domain
def main():
    folder=ROOT/'output/fill-expand'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/fill_expand_unit.gd' if headless else 'tests/fill_expand_smoke.gd'
        args=command(script,headless=headless,extra=['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=220)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');marker='FILL_EXPAND_UNIT ' if headless else 'FILL_EXPAND_READ ' if extra else 'FILL_EXPAND_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:domain=reference(folder/'domain.json')
        else:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    assert [(r['checks'],r['failures']) for r in results]==[(22,0),(23,0),(3,0)],results
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:assert not any(s in z.read('project.json') for s in [b'expand_pixels',b'expanded_pixels',b'expand_edges'])
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),results=results,domain=domain,private_receipts=receipts,pixels_exact=True)
    (ROOT/'output/fill-expand-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
