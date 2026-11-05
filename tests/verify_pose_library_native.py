from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def main():
    normal=Path('C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output');folder=ROOT/'output/body-pose-native'/str(time.time_ns());folder.mkdir(parents=True);plans=[]
    for label,relative in [('GMod','source-smoke/source-project'),('SFM','sfm-smoke/project')]:
        p=normal/relative;document=json.loads((p/'project.json').read_bytes());row=document.get('model') or next(x for x in document['world']['objects'] if x['kind']=='model');source=p/row['path'];assert source.is_file();plans.append({'label':label,'source':str(source)})
    native=json.loads((normal/'native-import-verification.json').read_bytes())
    for name in native['bundles']:
        p=Path(name);parameters=json.loads((p/'parameters.json').read_bytes())
        if parameters.get('kind')=='mmd_preparation' and str(parameters.get('source_file','')).lower().endswith('.pmd'):plans.insert(0,{'label':'MMD','source':str(p/'scene.glb')});break
    for name in native['bundles']:
        p=Path(name);parameters=json.loads((p/'parameters.json').read_bytes())
        if parameters.get('kind')=='vrm_preparation':plans.append({'label':'VRM'+str(parameters['vrm_version']),'source':str(p/'scene.glb')});break
    assert len(plans)==4;(folder/'plan.json').write_text(json.dumps(plans),encoding='utf-8');before={p['source']:hashlib.sha256(Path(p['source']).read_bytes()).hexdigest() for p in plans}
    args=command('tests/pose_library_native.gd',extra=['--',str(folder)]);p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=115,creationflags=subprocess.CREATE_NO_WINDOW);raw=p.stdout+p.stderr;(folder/'native.log').write_bytes(raw);assert p.returncode==0 and b'POSE_LIBRARY_NATIVE ' in raw and not any(x in raw for x in [b'SCRIPT ERROR',b'SHADER ERROR',b'ERROR:',b'FAIL ',b'ObjectDB instances leaked']),raw.decode('utf-8',errors='replace')
    line=next(s for s in raw.decode('utf-8',errors='replace').splitlines() if s.startswith('POSE_LIBRARY_NATIVE '));report=json.loads(line[len('POSE_LIBRARY_NATIVE '):]);assert report['failures']==0 and report['checks']==24
    path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];assert before=={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in before}
    result={'folder':str(folder),'report':report,'private_receipt':str(path),'source_hashes':before,'source_unchanged':True};(ROOT/'output/body-pose-native-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
