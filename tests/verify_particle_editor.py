"""Installed browser -> named effect -> common edit/Undo/HAS/movie, private GPU."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from run import command
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    sys.stdout.reconfigure(encoding='utf-8');reference=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else ROOT
    if reference!=ROOT:assert read(reference/'output/particle-scene-regression.json')['state']=='complete','Keep original full regression uncontended; run this after its completion'
    data=read(ROOT/'output/particle-browser-data-verification.json');folder=ROOT/'output/particle-editor'/str(time.time_ns());folder.mkdir(parents=True);plans=[]
    for case in data['cases']:
        report=read(Path(case['bundle'])/'report.json');source=report['resources'][0];plans.append({'provider':source['provider'],'member':source['resource'],'system':case['name']})
    (folder/'plans.json').write_text(json.dumps({'effects':plans,'sourceio':str(reference/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')}),encoding='utf-8')
    frozen={str(p.relative_to(ROOT)):sha(p)for d in ['src','tools','tests','data','examples']for p in(ROOT/d).rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.suffix!='.pyc'};receipts=[]
    for label,extra in [('writer',[]),('cold',['cold'])]:
        args=command('tests/particle_editor_smoke.gd',extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=280);s=p.stdout+p.stderr;(folder/(label+'.log')).write_text(s,encoding='utf-8');assert p.returncode==0 and 'PARTICLE_EDITOR 'in s and not any(t in s for t in ['ERROR:','FAIL ','ObjectDB instances leaked']),s
        receipt=Path(args[args.index('--receipt')+1]);r=read(receipt);assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed'];receipts.append(str(receipt))
        if label=='writer':
            result=read(folder/'result.json')
            with zipfile.ZipFile(result['linked'])as z:
                rows=read_header=json.loads(z.read('has.json'))['assets'];effects=[r for r in rows if r['path'].endswith(('.json','.png'))];assert len(effects)==4 and all(r['reference'].replace('\\','/').startswith('linked.assets/')for r in effects)
            for a in [folder/'inputs',folder/'worker',Path(result['import_root'])]:
                b=a.with_name(a.name+'-held');assert a.resolve().is_relative_to((ROOT/'output').resolve())and b.resolve().is_relative_to((ROOT/'output').resolve())and not b.exists();a.rename(b)
    result=read(folder/'result.json');probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],encoding='utf-8'));v=next(s for s in probe['streams']if s['codec_type']=='video');assert(v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1')
    assert all(sha(ROOT/n)==h for n,h in frozen.items());result.update({'cold':read(folder/'cold.json'),'private_receipts':receipts,'functional_unchanged':True,'normal_installation_updated':False})
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/particle-editor-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
