"""Actual schema5 editor save/open/clock/MP4 checks using retained native packets."""
from pathlib import Path
import array,hashlib,importlib.util,json,math,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
import has_project as has
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    previous=read(ROOT/'output/particle-sprite-verification.json')
    folder=ROOT/'output/particle-scene'/str(time.time_ns());inputs=folder/'inputs';inputs.mkdir(parents=True);receipts=[]
    frozen={str(p.relative_to(ROOT)):sha(p)for d in ['src','tools','tests','data','examples']for p in(ROOT/d).rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.suffix!='.pyc'}
    tone=array.array('h',(int(16000*math.sin(2*math.pi*1000*n/48000))for n in range(24000)))
    if sys.byteorder!='little':tone.byteswap()
    with wave.open(str(inputs/'tone.wav'),'wb')as w:w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(tone.tobytes())
    for i,row in enumerate(previous['plans']):
        for leaf,target,digest in [('effect.json',f'effect-{i}.json',row['effect_sha256']),('sprite.png',f'texture-{i}.png',row['texture_sha256'])]:
            source=Path(row['bundle'])/leaf;assert sha(source)==digest;(inputs/target).write_bytes(source.read_bytes())
    for name in ['storage.gd']:
        blob=subprocess.check_output(['git','show','4e8e51788:hybrid-animation-studio/src/'+name],cwd=ROOT);(folder/('old_'+name)).write_bytes(blob)
    old_py=subprocess.check_output(['git','show','4e8e51788:hybrid-animation-studio/tools/has_project.py'],cwd=ROOT);(folder/'old_has_project.py').write_bytes(old_py)
    for name,extra in [('writer',[]),('cold',['cold'])]:
        args=command('tests/particle_scene_smoke.gd',extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=240)
        text=p.stdout+p.stderr;(folder/(name+'.log')).write_text(text,encoding='utf-8');assert p.returncode==0 and 'PARTICLE_SCENE 'in text and not any(v in text for v in ['ERROR:','FAIL ','ObjectDB instances leaked']),text
        result=read(folder/('result.json'if name=='writer'else 'cold.json'));assert result['failures']==0
        receipt=Path(args[args.index('--receipt')+1]);r=read(receipt);assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed'];receipts.append(str(receipt))
        if name=='writer':
            manifest=read(folder/'snapshot/project.json');assert manifest['schema_version']==5 and len(manifest['world']['effects'])==2
            spec=importlib.util.spec_from_file_location('old_has',folder/'old_has_project.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
            try:old.members(manifest)
            except old.HasError:pass
            else:raise AssertionError('Old HAS worker silently accepted particles')
            # Move only our new input directory and writer cache, after validating
            # both endpoints. Packed cold Open cannot fall back to these paths.
            for leaf in ['inputs','cache']:
                a=folder/leaf;b=folder/(leaf+'-held');assert a.resolve().is_relative_to(folder.resolve())and b.resolve().is_relative_to(folder.resolve())and not b.exists();a.rename(b)
    movie=Path(read(folder/'movie.json')['folder'])/'movie.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(movie)],encoding='utf-8'));v=next(s for s in probe['streams']if s['codec_type']=='video');assert(v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1')
    assert any(s['codec_name']=='aac'for s in probe['streams'])
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-vn','-f','s16le','-ac','1','-ar','48000','pipe:1'],capture_output=True,check=True);samples=array.array('h');samples.frombytes(decoded.stdout)
    if sys.byteorder!='little':samples.byteswap()
    onset=next(i for i,n in enumerate(samples)if abs(n)>1000)/48000;assert abs(onset-1)<.002,onset
    assert all(sha(ROOT/name)==digest for name,digest in frozen.items())
    result={'folder':str(folder),'writer':read(folder/'result.json'),'cold':read(folder/'cold.json'),'private_receipts':receipts,'movie':str(movie),'aac_onset_seconds':onset,'functional_unchanged':True,'native_packets':[r['effect_sha256']for r in previous['plans']],'old_storage_and_has_rejected':True,'normal_installation_updated':False}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/particle-scene-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
