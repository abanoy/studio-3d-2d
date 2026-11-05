"""Opt-in installed Source particle experiment; no missing-native success/skips."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
from asset_audit import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    folder=ROOT/'output/particle-sprite'/str(time.time_ns());folder.mkdir(parents=True);receipts=[]
    frozen={str(p.relative_to(ROOT)):sha(p)for d in ['src','tools','tests','data','examples']for p in(ROOT/d).rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.suffix!='.pyc'}
    report=ROOT/'output/particle-system-research.json'
    if not report.is_file():raise RuntimeError('This opt-in native experiment needs the retained installed-PCF research inventory; no native pass/skip is invented.')
    research=read(report);plans=[];originals={}
    selected=[('SFM flash',4,'Explosions_MA_Flash_1'),('Workshop glow',1,'vFire_Glow_Tiny')]
    for i,(label,index,name)in enumerate(selected):
        prior=research['results'][index];request=prior['request'];provider=Path(request['provider']['path'])
        source=provider/request['file']['path']if provider.is_dir()else provider;originals[str(source)]={'sha256':digest(source),'mtime_ns':source.stat().st_mtime_ns}
        path=folder/(str(i)+'-request.json');path.write_text(json.dumps({'provider':str(provider),'member':request['file']['path'],'system':name,'duration':2,'seed':17}),encoding='utf-8')
        bundle=folder/('effect-'+str(i));args=[sys.executable,'tools/prepare_particle_effect.py',str(path),'--output',str(bundle)]
        p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=65,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt'else 0)
        (folder/(str(i)+'-prepare.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr
        effect=read(bundle/'effect.json');native=read(bundle/'report.json');assert len(effect['particles'])>0 and sha(bundle/'sprite.png')==effect['texture']['sha256'];assert native['resources'][0]['sha256']==read(prior['result'])['sha256']
        plans.append({'label':label,'bundle':str(bundle),'effect_sha256':sha(bundle/'effect.json'),'texture_sha256':sha(bundle/'sprite.png')})
    (folder/'plans.json').write_text(json.dumps(plans),encoding='utf-8')
    for name,extra in [('writer',[]),('cold',['cold'])]:
        args=command('tests/particle_sprite_smoke.gd',extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=180)
        text=p.stdout+p.stderr;(folder/(name+'.log')).write_text(text,encoding='utf-8');assert p.returncode==0 and 'PARTICLE_SPRITE 'in text and not any(s in text for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
        result=read(folder/('result.json'if name=='writer'else'cold.json'));assert result['failures']==0
        receipt=Path(args[args.index('--receipt')+1]);r=read(receipt);assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed'];receipts.append(str(receipt))
        if name=='writer':
            # Move only these owned native copies. The cold engine gets canonical
            # descriptor+PNG, never an installed-game lookup or a native parser.
            for plan in plans:
                b=Path(plan['bundle'])
                for file in ['source.pcf','source.vtf','material.vmt']:
                    p=b/file;q=b/(file+'.held');assert p.resolve().is_relative_to(folder.resolve())and not q.exists();p.rename(q)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(folder/'movie.mp4')],encoding='utf-8'));video=next(s for s in probe['streams']if s['codec_type']=='video')
    assert(video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')and abs(float(probe['format']['duration'])-2)<.001
    assert all(digest(path)==r['sha256']and Path(path).stat().st_mtime_ns==r['mtime_ns']for path,r in originals.items())
    assert all(sha(ROOT/name)==digest for name,digest in frozen.items())
    result={'folder':str(folder),'writer':read(folder/'result.json'),'cold':read(folder/'cold.json'),'private_receipts':receipts,'plans':plans,'originals':originals,'video':video,'functional_unchanged':True,'normal_editor_particle_support':False}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/particle-sprite-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
