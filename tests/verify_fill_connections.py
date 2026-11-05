"""Exhaustive independent graph oracle and hidden connected-fill editor workflow."""
from pathlib import Path
from collections import deque
import base64,json,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def reference(path):
    domain=json.loads(path.read_bytes());cases=domain.pop('cases');refusals=0
    for c in cases:
        w,h=c['width'],c['height'];sample=base64.b64decode(c['sample']);target=base64.b64decode(c['target']);point=tuple(c['point']);at=(point[1]*w+point[0])*4;seed=sample[at:at+4];threshold=c['tolerance']*255
        allowed=bytes(int(abs(sample[i*4+3]-seed[3])*255)<=threshold and all(abs(sample[i*4+j]*sample[i*4+3]-seed[j]*seed[3])<=threshold for j in range(3)) for i in range(w*h))
        if c['gap']:
            left=c['gap']//2;right=c['gap']-left
            eroded=bytes(int(all(allowed[yy*w+xx] if 0<=xx<w and 0<=yy<h else 1 for yy in range(y-left,y+right+1) for xx in range(x-left,x+right+1))) for y in range(h) for x in range(w))
            allowed=bytes(int(allowed[y*w+x] and any(eroded[yy*w+xx] if 0<=xx<w and 0<=yy<h else 0 for yy in range(y-right,y+left+1) for xx in range(x-right,x+left+1))) for y in range(h) for x in range(w))
        if not allowed[point[1]*w+point[0]]:
            assert c['error'],(w,h,c,'seed refusal');refusals+=1;continue
        assert not c['error'],(w,h,c,'unexpected refusal')
        queue=deque([point]);region={point};directions=[(-1,0),(1,0),(0,-1),(0,1)]
        if c['connections']==8:directions+=[(-1,-1),(-1,1),(1,-1),(1,1)]
        while queue:
            x,y=queue.popleft()
            for dx,dy in directions:
                p=(x+dx,y+dy);xx,yy=p
                if 0<=xx<w and 0<=yy<h and p not in region and allowed[yy*w+xx]:region.add(p);queue.append(p)
        radius=c['grow'];grown={(xx,yy) for x,y in region for yy in range(max(0,y-radius),min(h,y+radius+1)) for xx in range(max(0,x-radius),min(w,x+radius+1))}
        result=bytearray(target);paint=bytes([30,160,220,170]);changed=[]
        for x,y in grown:
            i=(y*w+x)*4
            if target[i:i+4]!=paint:changed.append((x,y))
            result[i:i+4]=paint
        bounds=[min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)-min(x for x,y in changed)+1,max(y for x,y in changed)-min(y for x,y in changed)+1] if changed else [0,0,0,0]
        assert bytes(result)==base64.b64decode(c['output']),(w,h,c['connections'],c['point'],'pixels')
        assert (c['region'],c['expanded'],c['changed'],c['edge'],c['bounds'],c['actual_connections'])==(len(region),len(grown)-len(region),len(changed),any(x in (0,w-1) or y in (0,h-1) for x,y in grown),bounds,c['connections']),(w,h,c,'metadata')
        assert 1<=c['peak']<=w*h*(1 if c['connections']==8 else 2),(w,h,c,'pending bound')
    domain.update(independent_cases=len(cases),exhaustive_cases=512*9*2,expected_refusals=refusals,pixel_differences=0);return domain
def main():
    folder=ROOT/'output/fill-connections'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/fill_connections_unit.gd' if headless else 'tests/fill_connections_smoke.gd'
        args=command(script,headless=headless,extra=['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');marker='FILL_CONNECTIONS_UNIT ' if headless else 'FILL_CONNECTIONS_READ ' if extra else 'FILL_CONNECTIONS_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:domain=reference(folder/'domain.json')
        else:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    assert [(r['checks'],r['failures']) for r in results]==[(8,0),(27,0),(3,0)],results
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:assert not any(s in z.read('project.json') for s in [b'connectivity_choice',b'pending_peak',b'"connectivity"'])
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),results=results,domain=domain,private_receipts=receipts,pixels_exact=True)
    (ROOT/'output/fill-connections-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
