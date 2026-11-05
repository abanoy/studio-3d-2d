"""Independent raster translation/source-over reference and private actual editor."""
from pathlib import Path
import base64,json,math,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def reference(path):
    domain=json.loads(path.read_bytes());cases=domain.pop('cases');maximum=0;exact=0
    for c in cases:
        w,h=c['width'],c['height'];raw=base64.b64decode(c['input']);actual=base64.b64decode(c['output']);x,y,rw,rh=c['rect'];dx,dy=c['requested'];dx=max(-x,min(w-x-rw,dx));dy=max(-y,min(h-y-rh,dy));assert c['offset']==[dx,dy]
        output=bytearray(raw)
        if (dx or dy) and any(raw[(yy*w+xx)*4+3] for yy in range(y,y+rh) for xx in range(x,x+rw)):
            if not c['copy']:
                for yy in range(y,y+rh):
                    for xx in range(x,x+rw):output[(yy*w+xx)*4:(yy*w+xx)*4+4]=bytes(4)
            # Per-pixel mathematical straight-alpha source-over. No production
            # Images, region copies or engine blend calls in this reference.
            for yy in range(rh):
                for xx in range(rw):
                    si=((y+yy)*w+x+xx)*4;di=((y+dy+yy)*w+x+dx+xx)*4;s=raw[si:si+4];d=output[di:di+4]
                    if not s[3]:continue
                    a=s[3]*255+d[3]*(255-s[3]);pixel=[math.floor((s[j]*s[3]*255+d[j]*d[3]*(255-s[3]))/a+.5) for j in range(3)]+[math.floor(a/255+.5)];output[di:di+4]=bytes(pixel)
        error=max(abs(a-b) for a,b in zip(output,actual));maximum=max(maximum,error)
        assert error<=(0 if c['exact'] else 1),(c['rect'],c['requested'],c['copy'],error)
        if c['exact']:exact+=1
        assert c['changed']==(actual!=raw)
    domain.update(independent_cases=len(cases),exact_opaque_cases=exact,max_alpha_math_error=maximum);return domain
def main():
    folder=ROOT/'output/drawing-selection'/str(time.time_ns());folder.mkdir(parents=True);results=[];receipts=[]
    for label,headless,extra in [('unit',True,[]),('writer',False,[]),('reader',False,['--read'])]:
        script='tests/drawing_selection_unit.gd' if headless else 'tests/drawing_selection_smoke.gd'
        args=command(script,headless=headless,extra=['--',str(folder),'--demo-room',*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=220)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8');marker='DRAWING_SELECTION_UNIT ' if headless else 'DRAWING_SELECTION_READ ' if extra else 'DRAWING_SELECTION_SMOKE '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:domain=reference(folder/'domain.json')
        else:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    assert [(r['checks'],r['failures']) for r in results]==[(12,0),(35,0),(3,0)],results
    result=json.loads((folder/'result.json').read_bytes())
    with zipfile.ZipFile(result['project']) as z:assert not any(s in z.read('project.json') for s in [b'selection_preview',b'drawing_selection',b'preview_builds'])
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),results=results,domain=domain,private_receipts=receipts,pixels_exact=True)
    (ROOT/'output/drawing-selection-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
