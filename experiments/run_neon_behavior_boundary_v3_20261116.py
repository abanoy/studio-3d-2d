"""Root-owned exact-original counterfactual for the reviewed Neon behavior probe."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
SCRIPT='experiments/neon_redesign_refresh_boundary_v3_20261116/neon_behavior_regression.gd'
SOURCE=ROOT/SCRIPT
EXPECTED='48d778041385988d0ac306ebbcf7440ae9e03ff35660871d0bed4e3f2a2cfcf9'
ENGINE=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
FOLDER=REVIEW/'output/neon-behavior-boundary-v3-20261116-attempt1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def sources():
    files=[p for d in ('src','tests','tools','data','examples') for p in (REVIEW/d).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
    files += [REVIEW/n for n in ('project.godot','main.tscn','run.py','launch.pyw')]
    return {p.relative_to(REVIEW).as_posix():sha(p) for p in sorted(files)}
def closed(label):
    code="$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*has-neon-review-20261116-c2d52ff*')}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json -Compress"
    p=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate(timeout=30);assert p.returncode==0 and not err.strip(),err.decode('utf-8','replace')
    v=json.loads(out);save(FOLDER/(label+'-closure.json'),v);assert v['owned_count']==0
def main():
    assert sha(SOURCE)==EXPECTED
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW,text=True).strip()=='c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2'
    baseline=json.loads((REVIEW/'output/windows-neon-c2d52ff-20261117T000859/source-before.json').read_bytes())['source_sha256']
    applied=json.loads((ROOT/'experiments/neon_windows_original_20261116/APPLIED_SUCCESSOR.json').read_bytes())
    for name,row in applied['changed'].items(): baseline[name]=row['new_sha256']
    baseline['src/workspace_layout.gd']='7d194eaf03d03b909fa0caaf84c197f91e8fb29af95f2978ae5f8d798e3dfe8b'
    assert sources()==baseline
    FOLDER.mkdir(exist_ok=False);closed('before')
    to=REVIEW/SCRIPT;to.parent.mkdir(exist_ok=True,parents=True)
    assert not to.exists();to.write_bytes(SOURCE.read_bytes());assert sha(to)==EXPECTED
    observer=module(ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py','neon_original_observer')
    runner=module(REVIEW/'run.py','neon_original_runner')
    job={'format':'has_neon_behavior_regression_job_1','phase':'ROOT_APPROVED_NEON_BEHAVIOR','root_closed_all':True,'expires_unix':time.time()+600,'script_sha256':EXPECTED,'app_sha256':sha(REVIEW/'src/app.gd'),'folder':(FOLDER/'app-result').as_posix()}
    save(FOLDER/'job.json',job)
    parsed=False;result=None;receipt=None;process=None
    try:
        parse=[str(ENGINE),'--headless','--path',str(REVIEW),'--log-file',str(FOLDER/'parse-engine.log'),'--script','res://'+SCRIPT,'--check-only']
        row,text=observer.invoke(FOLDER,'parse',parse,40)
        parsed=row['exit']==0 and not any(t in text for t in ('ERROR:','SCRIPT ERROR'))
        if parsed:
            args=runner.command(SCRIPT,extra=['--log-file',str(FOLDER/'app-engine.log'),'--',str(FOLDER/'job.json')])
            process,text=observer.invoke(FOLDER,'app',args,130)
            receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes())
            p=FOLDER/'app-result/result.json'
            result=json.loads(p.read_bytes()) if p.exists() else None
    finally:
        closed('after');preserved=sources()==baseline
        save(FOLDER/'verification.json',{'format':'has_neon_boundary_v3_behavior_execution_1','parsed':parsed,'process':process,'result':result,'receipt':receipt,'source_unchanged':preserved,'root_expected_original_regressions':False,'product_pass_claimed':False})
    print(json.dumps({'folder':str(FOLDER),'parsed':parsed,'exit':process['exit'] if process else None,'checks':result.get('checks') if result else None,'failures':result.get('failures') if result else None,'failed_named':[n for n,v in result.get('named_checks',{}).items() if v is False] if result else [],'source_unchanged':preserved,'job_and_desktop_closed':bool(receipt and receipt.get('job_closed') and receipt.get('desktop_closed'))}))
if __name__=='__main__':main()
