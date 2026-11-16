"""Root-owned scalar-only diagnostic; retained failures are not qualification."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
STUDIO=ROOT/'output/native-five-stage-attempt2/Studio'
PACKET=ROOT/'experiments/source_native_five_opposite_diagnostic_20261116'
SCRIPT='tests/source_native_five_live_opposite_diagnostic.gd'
ENGINE=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def closed(folder,label):
    code="$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    p=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate(timeout=30)
    (folder/(label+'-inventory-stdout.log')).write_bytes(out);(folder/(label+'-inventory-stderr.log')).write_bytes(err)
    assert p.returncode==0 and not err.strip()
    result=json.loads(out);save(folder/(label+'-closure.json'),result);assert result['owned_count']==0
    return result
def source_map():
    paths=[p for n in ('src','tests','tools','data','examples') for p in (STUDIO/n).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
    paths += [STUDIO/n for n in ('project.godot','main.tscn','run.py','launch.pyw','dependencies.json')]
    return {p.relative_to(STUDIO).as_posix():sha(p) for p in sorted(paths)}
def invoke(folder,label,command,timeout):
    save(folder/(label+'-command.json'),command)
    start=time.monotonic();p=subprocess.Popen(command,cwd=STUDIO,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    save(folder/(label+'-start.json'),{'pid':p.pid,'retained_Popen':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    timed=False
    try:out,err=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed=True;p.terminate();out,err=p.communicate(timeout=10)
    (folder/(label+'-stdout.log')).write_bytes(out);(folder/(label+'-stderr.log')).write_bytes(err)
    row={'pid':p.pid,'exit':p.returncode,'retained_Popen_reaped':p.poll() is not None,'timed_out':timed,'owned_child_terminated':timed,'seconds':time.monotonic()-start}
    save(folder/(label+'-process.json'),row)
    return row

def main():
    assert sha(ENGINE)==ENGINE_SHA
    assert sha(PACKET/'INDEX.json')=='50df7f894b04633568679ab9252727597e7f76d5abff83d52d646602e63bd3f5'
    assert sha(PACKET/'source_native_five_live_opposite_diagnostic.gd')=='86cc15b664fc23472a4784cf7066e24791eb47d33be725254ff9c224ed1979df'
    assert sha(STUDIO/'src/source_secondary.gd')=='064c211efbb19b829defb959b6f9d0c6aeef36aa6c2af76065fda9f2b17b21be'
    folder=STUDIO/'output/opposite-diagnostic-attempt1';folder.mkdir()
    closed(folder,'before')
    target=STUDIO/SCRIPT;assert not target.exists();target.write_bytes((PACKET/'source_native_five_live_opposite_diagnostic.gd').read_bytes())
    override=STUDIO/'override.cfg';assert not override.exists()
    override.write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps('HAS Five Opposite '+str(time.time_ns()))+'\n',encoding='utf-8')
    before=source_map();save(folder/'SOURCE.json',{'overlay_context':'Stage2 strict064c performance backend; diagnostic observer added, no main product change','source_sha256':before,'override_sha256':sha(override)})
    mapping=json.loads((PACKET/'ROOT_DRIVER_MAP.json').read_bytes());job=mapping['job']
    job['folder']=str(folder);job['source_manifest_sha256']=sha(folder/'SOURCE.json')
    save(folder/'job.json',job)
    parse=invoke(folder,'parse',[str(ENGINE),'--headless','--path',str(STUDIO),'--audio-driver','Dummy','--log-file',str(folder/'parse-engine.log'),'--script','res://'+SCRIPT,'--check-only'],30)
    if parse['exit']!=0 or parse['timed_out']:
        save(folder/'verification.json',{'diagnostic_completed':False,'phase':'parse','parse':parse,'main_promoted':False});closed(folder,'after');print(json.dumps({'folder':str(folder),'parse_failed':True}));return 1
    spec=importlib.util.spec_from_file_location('root_five_diagnostic_runner',STUDIO/'run.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    previous=os.environ.get('HYBRID_GODOT');os.environ['HYBRID_GODOT']=str(ENGINE)
    try:command=module.command(SCRIPT,extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder/'job.json')])
    finally:
        if previous is None:os.environ.pop('HYBRID_GODOT',None)
        else:os.environ['HYBRID_GODOT']=previous
    assert module.ROOT.resolve()==STUDIO.resolve() and '--receipt' in command and Path(command[1]).resolve()==STUDIO/'tools/private_desktop.py'
    receipt_path=folder/'private-receipt.json';command[command.index('--receipt')+1]=str(receipt_path)
    process=invoke(folder,'diagnostic',command,160)
    result=json.loads((folder/'result.json').read_bytes()) if (folder/'result.json').exists() else {}
    receipt=json.loads(receipt_path.read_bytes()) if receipt_path.exists() else {}
    actual_names=set(result.get('named_checks',{}))
    complete=(result.get('format')==mapping['result_format'] and result.get('checks')==57 and result.get('complete_assertion_set') is True
              and actual_names==set(job['expected_names']) and result.get('job_sha256')==sha(folder/'job.json') and result.get('source_manifest_sha256')==sha(folder/'SOURCE.json'))
    private_closed=receipt.get('job_closed') is True and receipt.get('desktop_closed') is True and receipt.get('child_desktop_confirmed') is True and receipt.get('foreground_child_observed') is False and receipt.get('exit')==process['exit']
    logs=''.join((folder/name).read_text(encoding='utf-8',errors='replace') for name in ['diagnostic-stdout.log','diagnostic-stderr.log','engine.log'] if (folder/name).exists())
    errors=[line for line in logs.splitlines() if any(m in line for m in ['SCRIPT ERROR','ERROR:','WARNING:','ObjectDB instances leaked','resources still in use','Pages in use exist at exit'])]
    preserved=source_map()==before
    after=closed(folder,'after')
    record={'format':'has_root_native_five_opposite_diagnostic_execution_1','diagnostic_completed':bool(complete and private_closed and preserved and not errors and not process['timed_out']),
            'checks':result.get('checks',0),'retained_gate_failures':result.get('failures'),'parse':parse,'process':process,
            'private_job_desktop_closed':private_closed,'source_preserved':preserved,'error_markers':errors,'runtime_lease_released':after['owned_count']==0,
            'qualification_pass_claimed':False,'main_promoted':False,'result_sha256':sha(folder/'result.json') if result else None,
            'scalar_report_sha256':sha(folder/'opposite-diagnostic.json') if (folder/'opposite-diagnostic.json').exists() else None,
            'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder/'verification.json',record);print(json.dumps({'folder':str(folder),**record}))
    return 0 if record['diagnostic_completed'] else 1

if __name__=='__main__':raise SystemExit(main())
