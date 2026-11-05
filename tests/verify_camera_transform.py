from pathlib import Path
import json,math,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def main():
    folder=ROOT/'output/camera-transform'/str(time.time_ns());folder.mkdir(parents=True);reports={};receipts=[]
    for label,script,headless,extra in [('unit','tests/camera_transform_unit.gd',True,['--',str(folder/'domain.json')]),('writer','tests/camera_transform_smoke.gd',False,['--',str(folder)]),('reader','tests/camera_transform_smoke.gd',False,['--',str(folder),'--read'])]:
        args=command(script,headless,extra=extra);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=170,creationflags=subprocess.CREATE_NO_WINDOW);raw=p.stdout+p.stderr;(folder/(label+'.log')).write_bytes(raw)
        assert p.returncode==0 and b'CAMERA_TRANSFORM_' in raw and not any(s in raw for s in [b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked']),raw.decode('utf-8',errors='replace')
        if not headless:
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
        marker={'unit':'CAMERA_TRANSFORM_UNIT ','writer':'CAMERA_TRANSFORM_SMOKE ','reader':'CAMERA_TRANSFORM_READ '}[label];line=next(x for x in raw.decode('utf-8',errors='replace').splitlines() if x.startswith(marker));reports[label]=json.loads(line[len(marker):]);assert reports[label]['failures']==0
    maximum=0.
    for row in reports['unit']['cases']:
        x,y,z=map(math.radians,row['angles']);cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
        expected=multiply(multiply([[cy,0,sy],[0,1,0],[-sy,0,cy]],[[1,0,0],[0,cx,-sx],[0,sx,cx]]),[[cz,-sz,0],[sz,cz,0],[0,0,1]])
        difference=max(abs(row['columns'][j][i]-expected[i][j]) for i in range(3) for j in range(3));maximum=max(maximum,difference);assert difference<2e-6,(row,difference)
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']],text=True));video=next(s for s in metadata['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    with zipfile.ZipFile(folder/'Numeric camera.has') as z:assert not any(s in z.read('project.json') for s in [b'camera_transform_editor',b'initial_values',b'edited_text'])
    result={'folder':str(folder),'reports':reports,'private_receipts':receipts,'independent_matrix_cases':len(reports['unit']['cases']),'maximum_matrix_error':maximum,'video':video,'transient_state_absent_from_has':True}
    (ROOT/'output/camera-transform-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='reports'},indent=2))
if __name__=='__main__':main()
