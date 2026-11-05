"""Root-path editing through private Windows UI, ordinary HAS and movie export."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    components='--components' in sys.argv
    label='movement-path-components' if components else 'movement-path'
    folder=ROOT/'output'/label/str(time.time_ns());folder.mkdir(parents=True)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for d in ['src','tests','tools','data','examples']for p in(ROOT/d).rglob('*')if p.is_file()and p.suffix!='.pyc'and '__pycache__'not in p.parts}
    receipts=[]
    for script,headless,marker in [('movement_path_unit',True,'MOVEMENT_PATH_UNIT '),('movement_path_smoke',False,'MOVEMENT_PATH ')]:
        args=command('tests/'+script+'.gd',headless=headless,extra=['--',str(folder),*(['--components'] if components else [])])
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
        log=p.stdout+p.stderr;(folder/(script+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and marker in log and '"failures":0'in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        if not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed'];receipts.append(str(receipt))
    result=json.loads((folder/'result.json').read_text());probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in probe['streams']if s['codec_type']=='video');assert(v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1')
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in frozen.items())
    result.update(folder=str(folder),private_receipts=receipts,functional_unchanged=True,unit_checks=13)
    result['component_model']=components
    (ROOT/'output'/ (label+'-verification.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
