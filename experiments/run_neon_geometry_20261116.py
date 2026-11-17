"""Root: apply the reviewed rail correction and run isolated geometry regressions."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-geometry-20261116-attempt1'
ENGINE=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    original=REVIEW/'src/workspace_layout.gd'
    proposal=ROOT/'experiments/neon_redesign_geometry_successor_20261116/rail/workspace_layout.proposed.gd'
    assert sha(original)=='81e905a8c1bb7c25ae2ef7e9b84b3c8ab3043cfb226db4a50e772622922371bf'
    assert sha(proposal)=='9109127f800bd13bacdbaa417f02d9a136267f325887e1ca6b56966e632d518f'
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','neon_geometry_safety')
    safety.FOLDER=FOLDER;safety.closed('before')
    old=original.read_bytes();assert old.count(b'\r\n')==old.count(b'\n')
    new=proposal.read_bytes();assert b'\r' not in new
    original.write_bytes(new.replace(b'\n',b'\r\n'))
    save(FOLDER/'rail-applied.json',{'original_sha256':hashlib.sha256(old).hexdigest(),'draft_LF_sha256':sha(proposal),'applied_CRLF_sha256':sha(original),'only_newline_reconstruction':'LF to CRLF retains existing working-tree style'})
    sources=safety.sources()
    save(FOLDER/'source-before.json',sources)
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','neon_geometry_observer')
    runner=module(REVIEW/'run.py','neon_geometry_runner')
    jobs=[('inset',True,ROOT/'experiments/neon_redesign_geometry_review_20261116/inset_scene_regression.gd'),('compact',False,ROOT/'experiments/neon_redesign_geometry_successor_20261116/compact_timeline_reveal_regression.gd'),('rail',False,ROOT/'experiments/neon_redesign_geometry_successor_20261116/rail/rail_placement_smoke.gd')]
    rows=[]
    try:
        for label,headless,source in jobs:
            relative='experiments/neon_geometry_runtime_20261116/'+label+'.gd'
            target=REVIEW/relative;target.parent.mkdir(exist_ok=True,parents=True)
            assert not target.exists();target.write_bytes(source.read_bytes())
            out=FOLDER/label;out.mkdir(exist_ok=False)
            parse=[str(ENGINE),'--headless','--path',str(REVIEW),'--log-file',str(out/'parse-engine.log'),'--script','res://'+relative,'--check-only']
            process,log=observer.invoke(out,'parse',parse,40)
            good=process['exit']==0 and not any(s in log for s in ('SCRIPT ERROR','ERROR:'))
            row={'label':label,'source_sha256':sha(source),'parse':process,'parsed':good}
            rows.append(row)
            if not good:continue
            destination=out/'result.json' if headless else out/'app-result'
            args=runner.command(relative,headless=headless,extra=['--log-file',str(out/'app-engine.log'),'--',destination.as_posix()])
            process,log=observer.invoke(out,'app',args,130)
            row['process']=process
            result=destination if headless else destination/'result.json'
            row['result']=json.loads(result.read_bytes()) if result.exists() else None
            row['errors']=[line for line in log.splitlines() if any(s in line for s in ('SCRIPT ERROR','ERROR:','WARNING:','ObjectDB instances leaked'))]
            if not headless:
                receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes());row['receipt']=receipt
                assert receipt.get('job_closed') and receipt.get('desktop_closed') and receipt.get('child_desktop_confirmed') and not receipt.get('foreground_child_observed')
            row['passed']=process['exit']==0 and not row['errors'] and row['result'] is not None and row['result'].get('failures')==0
    finally:
        safety.closed('after')
        preserved=safety.sources()==sources
        save(FOLDER/'verification.json',{'format':'has_root_neon_geometry_execution_1','passed':len(rows)==3 and all(r.get('passed') for r in rows) and preserved,'rows':rows,'functional_source_unchanged_during_tests':preserved,'main_source_modified':False})
    print(json.dumps({'folder':str(FOLDER),'source_preserved':preserved,'rows':[{k:r.get(k) for k in ('label','parsed','passed','errors')}|{'checks':r.get('result',{}).get('checks') if r.get('result') else None,'failures':r.get('result',{}).get('failures') if r.get('result') else None} for r in rows]}))
if __name__=='__main__':main()
