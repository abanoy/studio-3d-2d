import argparse,hashlib,os
"""Project swatches: container validation, actual UI, cold readers and movie."""
from pathlib import Path
import copy,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command,configure_private_display
import has_project as has
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/palette'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);results=[];receipts=[]
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_palette.py'],cwd=ROOT,capture_output=True);(folder/'container.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr).decode('utf-8',errors='replace')
    for mode in ['unit','writer','packed','linked','recovery','lesson','folder']:
        headless=mode=='unit';script='tests/palette_unit.gd' if headless else 'tests/palette_smoke.gd';args=command(script,headless=headless,extra=(["--audio-driver","Dummy"] if os.name!="nt" else [])+['--',str(folder),mode,'--demo-room'])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200);log=p.stdout+p.stderr;(folder/(mode+'.log')).write_text(log,encoding='utf-8');marker='PALETTE_UNIT ' if headless else 'PALETTE_SMOKE ' if mode=='writer' else 'PALETTE_READ '
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        result=json.loads(log.split(marker)[-1].splitlines()[0]);assert result['failures']==0;results.append(result)
        if headless:
            template={'schema_version':3,'scene':{'path':'assets/'+'0'*64+'.glb','sha256':'0'*64},'model':{},'audio':{},'layers':[]}
            for case in json.loads((folder/'palette-cases.json').read_bytes()):
                test=copy.deepcopy(template);test['palette']=case['value']
                try:has.members(test);valid=True
                except has.HasError:valid=False
                assert valid==case['valid'],case
        elif os.name=='nt':
            path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
    result=json.loads((folder/'result.json').read_bytes());probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result.update(folder=str(folder),results=results,private_receipts=receipts,pixels_exact=True,cross_runtime_cases=16,container_tests=3)
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    result.update(source_sha256=frozen,isolated_display=options.isolated_display)
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'output/palette-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
