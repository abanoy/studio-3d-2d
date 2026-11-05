from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def run(args,log,marker,timeout=120):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    data=p.stdout+p.stderr;log.write_bytes(data)
    assert p.returncode==0 and marker.encode() in data and not any(s in data for s in (b'SCRIPT ERROR',b'SHADER ERROR',b'ObjectDB instances leaked')),data.decode('utf-8',errors='replace')
if __name__=='__main__':
    folder=ROOT/'output/joint-constraints'/str(time.time_ns());folder.mkdir(parents=True)
    existing=Path(json.loads((ROOT/'output/mmd-ik-verification.json').read_bytes())['folder'])
    blender=os.environ.get('HYBRID_BLENDER',r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe')
    cases=[];originals={}
    for label,model,pose,controller,effector in [('miku','native/scene.glb','foot.vpd','左足ＩＫ','左足首'),('pmx','pmx/scene.glb','hinge.vpd','Foot target','Tip')]:
        source=existing/model;native=existing/pose
        for p in (source,native):originals[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        request={'source':str(source),'pose':str(native),'scale':.08,'blender':blender,'output':str(folder/(label+'-converted.json')),'result':str(folder/(label+'-result.json')),'cancel':str(folder/(label+'-cancel'))}
        path=folder/(label+'-request.json');path.write_text(json.dumps(request),encoding='utf-8')
        run([sys.executable,'tools/prepare_mmd_pose.py',str(path)],folder/(label+'-preparation.log'),'')
        assert json.loads(Path(request['result']).read_bytes())['ok']
        cases.append({'source':str(source),'controller':controller,'effector':effector,'reference':request['result']})
    (folder/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    run([blender,'--background','--factory-startup','--python','tests/joint_euler_reference.py','--',str(folder)],folder/'euler.log','JOINT_EULER_REFERENCE')
    args=command('tests/joint_constraints_probe.gd',extra=['--',str(folder)])
    run(args,folder/'app.log','JOINT_CONSTRAINTS_PROBE')
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
    assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in originals.items())
    result=json.loads((folder/'probe-result.json').read_bytes());result.update(folder=str(folder),private_receipt=str(receipt),original_inputs_unchanged=True)
    (ROOT/'output/joint-constraints-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS bounded standard joint runtime on real Miku/original PMX with reach, bone lengths, limits and independent Euler reference')
