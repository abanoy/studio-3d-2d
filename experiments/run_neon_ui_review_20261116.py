"""Capture the corrected Windows UI through the existing private smoke test."""
from pathlib import Path
import importlib.util,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
FOLDER=REVIEW/'output/neon-corrected-ui-20261116-attempt1'
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def main():
    FOLDER.mkdir(exist_ok=False)
    safety=module(ROOT/'experiments/run_neon_behavior_original_20261116.py','neon_ui_safety');safety.FOLDER=FOLDER
    safety.closed('before');sources=safety.sources()
    retained=REVIEW/'output/windows-neon-c2d52ff-20261117T000859/original-ui';retained.mkdir(exist_ok=False)
    for p in (REVIEW/'output/ui-smoke').glob('*.png'):shutil.copy2(p,retained/p.name)
    runner=module(REVIEW/'run.py','neon_ui_runner')
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','neon_ui_observer')
    try:
        args=runner.command(extra=['--log-file',str(FOLDER/'engine.log'),'--','--ui-smoke','--demo-room'])
        process,log=observer.invoke(FOLDER,'app',args,150)
        receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes())
        screenshots=[]
        for p in (REVIEW/'output/ui-smoke').glob('*.png'):
            shutil.copy2(p,FOLDER/p.name);screenshots.append(p.name)
        passed=process['exit']==0 and 'UI_SMOKE ' in log and '"failures":0' in log and not any(t in log for t in ('ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked'))
    finally:
        safety.closed('after')
        preserved=safety.sources()==sources
    record={'format':'has_neon_corrected_windows_ui_review_1','passed':passed and preserved,'process':process,'receipt':receipt,'source_preserved':preserved,'synthetic_screenshots':screenshots,'manual_owner_result':'DEFERRED_NO_RESULT'}
    safety.save(FOLDER/'verification.json',record)
    print(json.dumps(record))
if __name__=='__main__':main()
