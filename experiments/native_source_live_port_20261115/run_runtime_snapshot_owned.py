"""Replay the real teardown with the unchanged180s outer budget, owned processes."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
ENGINE=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
TOOLS={PYTHON:'03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9',PWSH:'2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233',ENGINE:'63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
def sources():
    paths=[p for n in ('src','tests','tools','data','examples') for p in (ROOT/n).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
    paths += [ROOT/n for n in ('project.godot','main.tscn','run.py','launch.pyw','dependencies.json')]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def closed(folder,label):
    code="$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne "+str(os.getpid())+" -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -or $_.Name -match '^pythonw?\\.exe$')}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    process=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=process.communicate(timeout=30)
    save(folder/(label+'-inventory-process.json'),{'pid':process.pid,'exit':process.returncode,'reaped':process.poll() is not None})
    (folder/(label+'-inventory-stdout.log')).write_bytes(out);(folder/(label+'-inventory-stderr.log')).write_bytes(err)
    assert process.returncode==0 and not err.strip(),'Inventory failed'
    value=json.loads(out);save(folder/(label+'-runtime-closure.json'),value)
    assert value['owned_count']==0,'An owned runtime/helper remains; no process stopped'
    return value

def main():
    assert all(sha(p)==h for p,h in TOOLS.items())
    release=json.loads((ROOT/'output/windows-canonical-bone-binding-20261116T022132132/graphics-lease-closed-after-failure.json').read_bytes())
    assert release['released'] and release['all_collected_jobs_desktops_closed_private']
    tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    folder=ROOT/'output'/('runtime-snapshot-scope-'+tag);folder.mkdir()
    closed(folder,'before')
    before=sources();save(folder/'source-before.json',before)
    started=time.monotonic();started_ns=time.time_ns()
    command=[str(PYTHON),'-B',str(ROOT/'tests/verify_world_selection_teardown.py')]
    save(folder/'command.json',command)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_GODOT=str(ENGINE),HYBRID_PYTHON=str(PYTHON))
    child=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    save(folder/'owned-start.json',{'pid':child.pid,'command':command,'retained_Popen':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    timed_out=False
    try:out,err=child.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        timed_out=True;child.terminate();out,err=child.communicate(timeout=10)
    (folder/'stdout.log').write_bytes(out);(folder/'stderr.log').write_bytes(err)
    seconds=time.monotonic()-started
    process={'pid':child.pid,'exit':child.returncode,'retained_Popen_reaped':child.poll() is not None,'timeout_seconds':180,'timed_out':timed_out,'owned_wrapper_terminated':timed_out,'seconds':seconds}
    save(folder/'process.json',process)
    result_path=ROOT/'output/world-selection-teardown-latest.json'
    current=result_path.exists() and result_path.stat().st_mtime_ns>=started_ns
    proof=json.loads(result_path.read_bytes()) if current else {}
    actual=proof.get('result',{})
    cases=[row['case'] for row in actual.get('cases',[])]
    passed=(child.returncode==0 and not timed_out and current and proof.get('snapshot_scope')=='runtime_dependency_closure'
            and actual.get('checks')==28 and actual.get('failures')==0
            and cases==['controls-queue-free','focus-free','setup-free','focus-detach']
            and proof.get('unchanged_source') is True and proof.get('unchanged_override') is True)
    receipts=[]
    for label in ['normal-startup','process']:
        row=proof.get(label,{})
        receipt=row.get('receipt',{})
        receipt_pass=(row.get('exit')==0 and receipt.get('exit')==0 and receipt.get('job_closed') is True and receipt.get('desktop_closed') is True
                      and receipt.get('child_desktop_confirmed') is True and receipt.get('foreground_child_observed') is False)
        passed=passed and receipt_pass
        if row.get('receipt_path'):
            physical=Path(row['receipt_path']);assert physical.resolve().is_relative_to(ROOT/'output')
            assert json.loads(physical.read_bytes())==receipt
            receipts.append({'phase':label,'path':str(physical),'sha256':sha(physical),'passed':receipt_pass,'seconds':receipt.get('seconds')})
    after=sources();save(folder/'source-after.json',after)
    preserved=before==after and all(sha(p)==h for p,h in TOOLS.items())
    after_closed=closed(folder,'after')
    verification={'format':'has_actual_runtime_snapshot_teardown_replay_1','passed':bool(passed and preserved and after_closed['owned_count']==0),
                  'process':process,'checks_observed':actual.get('checks',0),'failures_observed':actual.get('failures'),
                  'snapshot_scope':proof.get('snapshot_scope'),'snapshot_files':len(proof.get('source_sha256',{})),
                  'source_and_runtime_preserved':preserved,'runtime_lease_released':after_closed['owned_count']==0,
                  'receipts':receipts,'actual_case_folder':proof.get('folder'),'full_default_pass_claimed':False,
                  'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder/'verification.json',verification)
    print(json.dumps({'folder':str(folder),**verification}))
    return 0 if verification['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
