"""Independent affine/premultiplied reference and private resize/rotation workflow."""
from pathlib import Path
import base64,json,math,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def reference(path):
    domain=json.loads(path.read_bytes());cases=domain.pop('cases');maximum=0;exact=0
    for p in cases:
        w,h=p['width'],p['height'];raw=base64.b64decode(p['input']);actual=base64.b64decode(p['output']);rx,ry,rw,rh=p['rect'];sx,sy=p['scale'];a=math.radians(p['angle']);cs,sn=math.cos(a),math.sin(a)
        if abs(cs)<1e-12:cs=0
        if abs(sn)<1e-12:sn=0
        # Derive bounds from all transformed corners, then invert the general
        # affine2x2 matrix rather than the production rotation/scale expressions.
        matrix=(sx*cs,-sy*sn,sx*sn,sy*cs);aa,bb,cc,dd=matrix;det=aa*dd-bb*cc
        corners=[(aa*x+bb*y,cc*x+dd*y) for x in [-rw/2,rw/2] for y in [-rh/2,rh/2]]
        bw=max(1,math.ceil(max(x for x,y in corners)-min(x for x,y in corners)-1e-9));bh=max(1,math.ceil(max(y for x,y in corners)-min(y for x,y in corners)-1e-9))
        ox=max(0,min(w-bw,rx+rw//2-bw//2));oy=max(0,min(h-bh,ry+rh//2-bh//2));assert p['selection']==[ox,oy,bw,bh]
        result=bytearray(raw)
        if not p['copy']:
            for y in range(ry,ry+rh):
                for x in range(rx,rx+rw):result[(y*w+x)*4:(y*w+x)*4+4]=bytes(4)
        def premul(x,y):
            i=((ry+max(0,min(rh-1,y)))*w+rx+max(0,min(rw-1,x)))*4;r,g,b,a=raw[i:i+4];return [r*a,g*a,b*a,a]
        def sample(u,v):
            if not (-.5<=u<rw-.5 and -.5<=v<rh-.5):return [0.0]*4
            x,y=math.floor(u),math.floor(v);fx,fy=u-x,v-y
            tl,tr,bl,br=premul(x,y),premul(x+1,y),premul(x,y+1),premul(x+1,y+1)
            return [((tl[k]*(1-fx)+tr[k]*fx)*(1-fy)+(bl[k]*(1-fx)+br[k]*fx)*fy) for k in range(4)]
        offsets=[(.5,.5)] if cs==0 or sn==0 else [(.25,.25),(.75,.25),(.25,.75),(.75,.75)]
        for y in range(bh):
            for x in range(bw):
                samples=[]
                for px,py in offsets:
                    dx,dy=x+px-bw/2,y+py-bh/2;samples.append(sample((dd*dx-bb*dy)/det+rw/2-.5,(-cc*dx+aa*dy)/det+rh/2-.5))
                s=[sum(q[k] for q in samples)/len(samples) for k in range(4)]
                if s[3]<=0:continue
                i=((oy+y)*w+ox+x)*4;back=result[i+3]*(1-s[3]/255);alpha=s[3]+back;rgba=[max(0,min(255,math.floor((s[k]+result[i+k]*back)/alpha+.5))) for k in range(3)]+[max(0,min(255,math.floor(alpha+.5)))];result[i:i+4]=bytes(rgba)
        error=max(abs(a-b) for a,b in zip(result,actual));maximum=max(maximum,error)
        assert error<=(0 if p['exact'] else 1),(p['scale'],p['angle'],p['copy'],error)
        exact+=int(p['exact']);assert p['changed']==(actual!=raw)
    domain.update(independent_cases=len(cases),exact_quarter_cases=exact,max_math_error=maximum);return domain
def main():
    folder=ROOT/'output/drawing-transform'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/drawing_transform_unit.gd' if headless else 'tests/drawing_transform_smoke.gd'
        args=command(script,headless=headless,extra=['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');marker='DRAWING_TRANSFORM_UNIT ' if headless else 'DRAWING_TRANSFORM_READ ' if extra else 'DRAWING_TRANSFORM_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:domain=reference(folder/'domain.json')
        else:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    assert [(r['checks'],r['failures']) for r in results]==[(11,0),(34,0),(3,0)],results
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:assert not any(s in z.read('project.json') for s in [b'drawing_transform',b'scale_x',b'worker_ms',b'selection_preview'])
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),results=results,domain=domain,private_receipts=receipts,pixels_exact=True)
    (ROOT/'output/drawing-transform-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
