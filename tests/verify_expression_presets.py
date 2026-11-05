"""Declared compound expression poses, native VRM0/1, Undo/HAS/cold/movie."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare
from test_helper_morphs import H,write_glb

def main():
    folder=ROOT/'output/expression-presets'/str(time.time_ns());folder.mkdir(parents=True);originals=prepare(folder)
    g=H.GLB(folder/'shared.glb')
    g.doc['extensions']={'VRMC_vrm':{'specVersion':'1.0','expressions':{'preset':{
        'happy':{'morphTargetBinds':[{'node':3,'index':0,'weight':.5},{'node':5,'index':1,'weight':.75}]},
        'blink':{'morphTargetBinds':[{'node':3,'index':1,'weight':1}]}},'custom':{
        'Switch':{'isBinary':True,'morphTargetBinds':[{'node':3,'index':1,'weight':1}]},
        'Material expression':{'morphTargetBinds':[{'node':3,'index':0,'weight':1}],'materialColorBinds':[{'material':0,'type':'color','targetValue':[1,0,0,1]}]}}}}}
    write_glb(folder/'compound.glb',g.doc,bytes(g.binary))
    material=json.loads(json.dumps(g.doc))
    for mesh in material['meshes']:
        mesh.pop('weights',None);mesh.get('extras',{}).pop('targetNames',None)
        for primitive in mesh['primitives']:primitive.pop('targets',None)
    for node in material['nodes']:node.pop('weights',None)
    material['extensions']['VRMC_vrm']['expressions']={'custom':{'Material only':{'materialColorBinds':[{'material':0,'type':'color','targetValue':[1,0,0,1]}]}}}
    write_glb(folder/'material-only.glb',material,bytes(g.binary))
    plans=[{'label':'Authored compound','source':str(folder/'compound.glb'),'expected':4,'id':'preset:happy','node':'5','index':'0'}]
    old=ROOT/'output/shape-catalog-verification.json'
    if old.is_file():
        report=json.loads(old.read_text(encoding='utf-8'))
        for row in json.loads((Path(report['folder'])/'catalogue-plans.json').read_text(encoding='utf-8')):
            if row['label'].startswith('VRM') and Path(row['source']).is_file():plans.append({'label':row['label'],'source':row['source'],'expected':14,'id':'preset:happy' if row['label']=='VRM1.0' else 'group:11','node':'91','index':'50'})
    for plan in plans:
        path=Path(plan['source']);originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    path=folder/'material-only.glb';originals[path]=(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    (folder/'plans.json').write_text(json.dumps(plans),encoding='utf-8');receipts=[]
    results={}
    for name,script,extra,headless,marker in [('unit','tests/expression_presets_unit.gd',[],True,'EXPRESSION_PRESETS_UNIT '),('app','tests/expression_presets_smoke.gd',[],False,'EXPRESSION_PRESETS_APP '),('reader','tests/expression_presets_smoke.gd',['reader'],False,'EXPRESSION_PRESETS_READER ')]:
        args=command(script,headless=headless,extra=['--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=190)
        log=p.stdout+p.stderr;(folder/(name+'.log')).write_text(log,encoding='utf-8');(folder/(name+'-command.json')).write_text(json.dumps({'args':args,'exit':p.returncode}))
        assert p.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-6500:]
        results[name]=json.loads(next(line[len(marker):]for line in log.splitlines()if line.startswith(marker)));assert results[name]['failures']==0
        if not headless:
            receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed'];receipts.append(str(receipt))
    probe=json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',results['app']['movie']],encoding='utf-8'));v=next(v for v in probe['streams']if v['codec_type']=='video')
    assert(v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')and abs(float(probe['format']['duration'])-2)<.001
    for path,value in originals.items():assert(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==value,path
    result={'folder':str(folder),'results':results,'native_models':len(plans)-1,'private_receipts':receipts,'checks':sum(row['checks']for row in results.values()),'failures':0}
    (ROOT/'output/expression-presets-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
