"""ROOT ONLY: close the exact failed 381d5a9 run; never infer a full PASS or kill a PID."""
from pathlib import Path
import argparse
import calendar
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
CONTEXT=json.loads((HERE/'CONTEXT.json').read_bytes())
ROOT=Path(CONTEXT['checkout'])
RUN=ROOT/'output'/CONTEXT['run_name']
OUTPUT=ROOT/'output'
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def safe(path):
    path=Path(path).absolute();assert '..' not in path.parts
    for part in (path,*path.parents):
        if part.exists():assert not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400
    return path.resolve()


def load(path):
    path=safe(path);assert path.stat().st_size<=64*1024*1024
    return json.loads(path.read_bytes())


def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def ns(value):
    match=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z',value)
    assert match
    return calendar.timegm(datetime.datetime.strptime(match[1],'%Y-%m-%dT%H:%M:%S').timetuple())*10**9+int((match[2] or '').ljust(9,'0'))


def terminal():
    state=load(RUN/'state.json')
    assert state['status'] in ('failed','runner_error') and state['suite_exit']==1 and state['source_unchanged'] is True and state.get('finished_utc')
    assert state['source_commit']==CONTEXT['commit'] and state['pid']==6012 and state['process_started']=='2026-11-17T00:34:20.7906987Z'
    assert state['checkout']==str(ROOT) and state['run_folder']==str(RUN)
    for name,digest in CONTEXT['terminal_input_hashes'].items():assert sha(RUN/name)==digest,name
    birth=load(RUN/'root-birth-observation.json');launch=load(RUN/'launch.json')
    assert birth['format']=='has_root_neon_corrected_birth_observation_1'
    assert birth['coordinator']=={'pid':6012,'creation_utc':'2026-11-17T00:34:20.7906987Z'}
    assert birth['python']['pid']==8148 and birth['python']['parent_pid']==6012 and birth['python']['creation_utc']=='2026-11-17T00:34:21.4146310Z'
    assert birth['python']['command_line']=='"C:\\Program Files\\Python313\\python.exe" -u tests/verify.py'.replace('\\\\','\\')
    assert launch['source_commit']==state['source_commit'] and launch['pid']==6012 and launch['creation_utc']==state['process_started'] and launch['runner_sha256']==state['script_sha256']
    before=load(RUN/'source-before.json');after=load(RUN/'source-after.json')
    assert before==after and before['commit']==CONTEXT['commit'] and len(before['source_sha256'])==1028
    actual={path.relative_to(ROOT).as_posix() for part in ('src','tests','tools','data','examples') for path in (ROOT/part).rglob('*') if path.is_file() and path.suffix!='.pyc' and '__pycache__' not in path.parts}
    actual.update(('project.godot','main.tscn','run.py','launch.pyw'))
    assert actual==set(before['source_sha256'])
    for name,digest in before['source_sha256'].items():assert sha(safe(ROOT/name))==digest,name
    report=load(RUN/'animated-channels-original-result.json')
    assert report['checks']==47 and report['failures']==1 and report['native_samples']==['pose-smoke/miku-project','source-smoke/source-project','sfm-smoke/project']
    return state,before,report


def observe():
    assert sha(PWSH)=='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
    code=r'''$ErrorActionPreference='Stop'; $pins=@(@{pid=6012;birth='2026-11-17T00:34:20.7906987Z'},@{pid=8148;birth='2026-11-17T00:34:21.4146310Z'}); $identities=@(); foreach($pin in $pins){$item=Get-Process -Id $pin.pid -ErrorAction SilentlyContinue; $now=$null; if($item){$now=$item.StartTime.ToUniversalTime().ToString('o')}; $absent=($null -eq $item -or [DateTimeOffset]::Parse($now) -ne [DateTimeOffset]::Parse($pin.birth)); if(-not $absent){throw 'Exact original process is still alive'}; $identities+=@{pid=$pin.pid;expected_creation_utc=$pin.birth;pid_present=($null -ne $item);current_creation_utc=$now;original_absent=$true}}; $matches=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.ProcessId -ne DRIVER_PID -and ($_.CommandLine -like '*has-neon-review-20261116-c2d52ff*' -or $_.CommandLine -like '*has-acceptance-session-20261111*') -and ($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe).exe$' -or ($_.Name -match '^pythonw?.exe$') -or ($_.Name -match '^(pwsh|powershell).exe$' -and $_.CommandLine -match '(run_canonical_owned|start_canonical|private_desktop)'))}); if($matches.Count){throw 'A scoped runtime, helper or coordinator remains'}; @{coordinator=$identities[0];python=$identities[1];owned_runtime_matches=@();owned_runtime_command_matches_absent=$true;root_observer_issued_no_termination=$true;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 8 -Compress'''
    code=code.replace('DRIVER_PID',str(os.getpid()))
    process=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    # No termination API exists in this observer. A query timeout never releases the lease.
    out,err=process.communicate(timeout=60)
    assert process.poll() is not None and process.returncode==0 and not err.strip(),err.decode('utf-8','replace')
    value=json.loads(out);value['observer_retained_Popen_reaped']=True
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-terminal-confirmed',action='store_true',required=True)
    parser.add_argument('--release-closed-failed',action='store_true')
    args=parser.parse_args()
    state,before,failed_report=terminal()  # Before any process query or audit output.
    observed=observe()
    start,finish,end=ns(state['started_utc']),ns(state['finished_utc']),ns(observed['observed_utc'])
    assert end>=finish
    out=RUN/'failed-terminal-audit-attempt1';assert not out.exists()
    refs={};inline=[];documents={};queue=[];seen=set()
    def add(path,origin):
        path=safe(path);assert path.is_relative_to(OUTPUT.resolve()) and path.suffix=='.json'
        assert path.is_file();refs.setdefault(path,set()).add(origin)
    def walk(value,origin):
        if isinstance(value,dict):
            if value.get('format')=='studio_private_desktop_1':inline.append({'origin':origin,'receipt':value})
            for key,item in value.items():
                if isinstance(item,str) and re.match(r'^[A-Za-z]:[\\/]',item):
                    path=Path(item)
                    if path.suffix=='.json' and ('receipt' in key.lower() or path.name in ('private-desktop.json','private-receipt.json')):add(path,origin+'.'+key)
                    if key=='folder' and path.is_dir() and (path/'verification.json').is_file() and path.resolve().is_relative_to(OUTPUT.resolve()):queue.append(path/'verification.json')
                walk(item,origin+'.'+key)
        elif isinstance(value,list):
            for index,item in enumerate(value):walk(item,origin+'['+str(index)+']')
    # Physical fresh root receipts are authoritative. Nested receipts are discovered from actual
    # fresh phase reports, never recursively from copied historical source/snapshot evidence.
    for path in (OUTPUT/'private-desktop').glob('*.json'):
        if start<=path.stat().st_mtime_ns<=end:add(path,'fresh_root_actual_interval')
    for pattern in ('*-verification.json','*-result.json'):
        queue.extend(path for path in OUTPUT.glob(pattern) if start<=path.stat().st_mtime_ns<=end)
    while queue:
        assert len(seen)<1024 and len(refs)<4096 and len(inline)<10000
        path=safe(queue.pop(0))
        if path in seen:continue
        assert path.is_relative_to(OUTPUT.resolve()) and path.name!='verification.json' or path.parent!=OUTPUT
        seen.add(path);value=load(path);documents[str(path)]={'sha256':sha(path),'mtime_ns':path.stat().st_mtime_ns}
        walk(value,str(path))
    phase_path=OUTPUT/'krita-import-verification.json';phase=load(phase_path)
    assert start<=phase_path.stat().st_mtime_ns<=finish
    cancel=safe(phase['cancelled_receipt']);add(cancel,'source_registered_Krita_cancel')
    source=ROOT/'tests/verify_krita_import.py'
    assert sha(source)==before['source_sha256']['tests/verify_krita_import.py'] and "assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']" in source.read_text(encoding='utf-8')
    rows=[];desktops={};late=[]
    for path in sorted(refs,key=str):
        value=load(path)
        if not isinstance(value,dict) or value.get('format')!='studio_private_desktop_1':continue
        assert start<=path.stat().st_mtime_ns<=end
        assert all(value.get(key) is True for key in ['private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'])
        assert all(value.get(key) is False for key in ['desktop_switch_requested','foreground_child_observed']) and not value.get('monitor_error')
        assert value['desktop'] not in desktops,'Duplicate physical desktop receipt'
        if value['exit']==0:
            assert not value.get('error');classification='normal_exit0'
        elif path==cancel and value['exit']==2 and value.get('cancelled') is True and value.get('error')=='Owned converter cancelled':classification='registered_Krita_cancel_exit2'
        elif path.parent==OUTPUT/'private-desktop' and path.name.startswith('animated_channels_smoke_') and value['exit']==1 and not value.get('error'):classification='registered_animated_assertion_exit1'
        else:raise AssertionError('Unregistered receipt exit/error: '+str(path))
        row={'source_path':str(path),'source_sha256':sha(path),'classification':classification,'after_failed_state_finish':path.stat().st_mtime_ns>finish,'receipt':value,'references':sorted(refs[path])}
        rows.append(row);desktops[value['desktop']]=value
        if row['after_failed_state_finish']:late.append({'path':str(path),'sha256':row['source_sha256'],'child_pid':value['child_pid']})
    assert rows and sum(row['classification']=='registered_Krita_cancel_exit2' for row in rows)==1 and sum(row['classification']=='registered_animated_assertion_exit1' for row in rows)==1
    for item in inline:assert desktops.get(item['receipt']['desktop'])==item['receipt'],'Inline receipt lacks exact physical match'
    # All gates precede the first write. Preserve exact failures and raw physical receipts.
    out.mkdir(exist_ok=False)
    for index,row in enumerate(rows):
        path=Path(row['source_path']);target=out/f'receipt-{index:03d}-{path.name}'
        target.write_bytes(path.read_bytes());assert sha(target)==row['source_sha256'];row['preserved_raw_copy']=str(target)
    for name in ['state.json','source-before.json','source-after.json','launch.json','root-birth-observation.json','animated-channels-original-result.json','canonical.log']:
        (out/name).write_bytes((RUN/name).read_bytes())
    inventory={'format':'has_neon_failed_381_receipt_inventory_1','source_commit':CONTEXT['commit'],'functional_sources':1028,
        'run_directory':str(RUN),'state_sha256':sha(RUN/'state.json'),'source_before_sha256':sha(RUN/'source-before.json'),
        'source_after_sha256':sha(RUN/'source-after.json'),'suite_status':state['status'],'suite_exit':1,'full_suite_passed':False,'final_full_report_used':False,
        'failed_phase':{'checks':47,'failures':1,'native_samples':failed_report['native_samples'],'raw_sha256':sha(RUN/'animated-channels-original-result.json')},
        'physical_receipts':len(rows),'unique_desktops':len(desktops),'normal_exit0':sum(row['classification']=='normal_exit0' for row in rows),
        'registered_cancel_exit2':1,'registered_assertion_failure_exit1':1,'all_collected_jobs_desktops_closed_private':True,
        'observation_window_end_utc':observed['observed_utc'],'late_receipts':late,'rows':rows,'inline_receipts':inline,'fresh_phase_document_hashes':documents,
        'process_observation':observed,'root_observer_issued_no_termination':True,'graphics_lease_released':False}
    save(out/'receipt-inventory.json',inventory)
    save(out/'host-observation.json',observed)
    if args.release_closed_failed:
        second=observe()  # Fresh identity/command absence after metadata/receipt validation.
        terminal()
        for row in rows:assert sha(Path(row['source_path']))==row['source_sha256']
        release={'format':'has_root_neon_failed_graphics_lease_release_1','released':True,'release_kind':'closed_failed_partial_run',
            'released_utc':second['observed_utc'],'source_commit':CONTEXT['commit'],'canonical_run':RUN.name,'coordinator_pid':6012,'python_pid':8148,
            'functional_sources':1028,'full_suite_passed':False,'suite_exit':1,'final_full_report_used':False,'physical_jobs':len(rows),
            'normal_exit0':inventory['normal_exit0'],'registered_Krita_cancel_exit2':1,'registered_animated_assertion_exit1':1,
            'all_collected_jobs_desktops_closed_private':True,'root_observer_issued_no_termination':True,
            'receipt_inventory_sha256':sha(out/'receipt-inventory.json'),'failed_state_sha256':sha(RUN/'state.json'),
            'second_identity_and_scope_observation':second,'limits':'Failed partial run closed only. No full PASS or unrun phase inferred.'}
        save(RUN/'graphics-lease-closed-after-failure.json',release)
    print(json.dumps({'audit':str(out),'physical_receipts':len(rows),'inventory_sha256':sha(out/'receipt-inventory.json'),
        'full_suite_passed':False,'graphics_lease_released':args.release_closed_failed}))


if __name__=='__main__':main()
