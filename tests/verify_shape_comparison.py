"""Actual focused before/after geometry and document isolation, private GPU only."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from run import command
from verify_source_shapes import prepare


def main():
    folder=ROOT/'output/shape-comparison-tests'/str(time.time_ns());folder.mkdir(parents=True);originals=prepare(folder)
    plans=[{'id':'0','label':'Authored fixture','source':str(folder/'shape.glb'),'control':'Second shape','rotation':[0,0,0,1]}]
    catalogue_path=ROOT/'output/shape-catalog-verification.json';native=[];rotations={}
    if catalogue_path.is_file():
        catalogue=json.loads(catalogue_path.read_text(encoding='utf-8'));native=json.loads((Path(catalogue['folder'])/'catalogue-plans.json').read_text(encoding='utf-8'))[1:]
    audit_path=ROOT/'output/import-height-audit.json'
    if audit_path.is_file():
        audit=json.loads(audit_path.read_text(encoding='utf-8'))
        for plan in json.loads((Path(audit['folder'])/'plans.json').read_text(encoding='utf-8')):
            path=Path(plan['source'])
            if path.is_file():rotations[hashlib.sha256(path.read_bytes()).hexdigest()]=plan['rotation_xyzw']
    names={'MMD':'まばたき','GMod':'blink','SFM':'CloseLidUpL','VRM1.0':'Fcl_EYE_Close','VRM0.x':'Fcl_EYE_Close','Supplied Mima':'EEEE'}
    for i,plan in enumerate(native,1):
        path=Path(plan['source'])
        if not path.is_file():continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest();originals[path]=(digest,path.stat().st_mtime_ns)
        plans.append({'id':str(i),'label':plan['label'],'source':str(path),'control':names[plan['label']],'rotation':rotations.get(digest,[0,0,0,1])})
    (folder/'plans.json').write_text(json.dumps(plans,ensure_ascii=False),encoding='utf-8')
    args=command('tests/shape_comparison_smoke.gd',extra=['--',str(folder)]);p=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=200)
    log=p.stdout+p.stderr;(folder/'engine.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'SHAPE_COMPARISON_APP 'in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log[-6500:]
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert not result['failures']and len(result['models'])==len(plans)
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed']
    teardown_args=command('tests/shape_comparison_teardown.gd',extra=['--',str(folder)])
    p=subprocess.run(teardown_args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=45)
    log=p.stdout+p.stderr;(folder/'teardown-engine.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'SHAPE_COMPARISON_TEARDOWN 'in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
    teardown=json.loads((folder/'teardown-result.json').read_text(encoding='utf-8'));assert not teardown['failures']
    teardown_receipt=Path(teardown_args[teardown_args.index('--receipt')+1]);r=json.loads(teardown_receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed']and not r['foreground_child_observed']and r['job_closed']and r['desktop_closed']
    for path,value in originals.items():assert(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)==value,path
    draft=None
    if any(plan['label']=='Supplied Mima' for plan in plans):
        draft_args=command('tests/shape_comparison_smoke.gd',extra=['--',str(folder),'recover-draft'])
        p=subprocess.run(draft_args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=90)
        log=p.stdout+p.stderr;(folder/'draft-reader.log').write_text(log,encoding='utf-8')
        assert p.returncode==0 and 'FACE_DRAFT_RECOVERY ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        draft=json.loads((folder/'draft-reader.json').read_text());assert draft=={'checks':4,'failures':0}
        draft_receipt=Path(draft_args[draft_args.index('--receipt')+1]);r=json.loads(draft_receipt.read_text())
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
    result.update(folder=str(folder),private_receipts=[str(receipt),str(teardown_receipt)],teardown=teardown,native_fixtures_optional=True,native_models_tested=len(plans)-1)
    result['draft_recovery']=draft
    if draft is not None:result['private_receipts'].append(str(draft_receipt))
    (ROOT/'output/shape-comparison-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))


if __name__=='__main__':main()
