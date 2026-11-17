"""ROOT ONLY: audit this exact terminal run and observe closure; never terminate a PID."""
from pathlib import Path
import argparse
import calendar
import datetime
import hashlib
import json
import math
import os
import re
import subprocess

import legacy_result_gates as Legacy

HERE=Path(__file__).resolve().parent
CONTEXT=json.loads((HERE/'CONTEXT.json').read_bytes())
ROOT=Path(CONTEXT['checkout'])
OUTPUT=ROOT/'output'
RUN=OUTPUT/CONTEXT['run_name']
PWSH=Path(CONTEXT['powershell'])


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def safe(path):
    path=Path(path).absolute();require('..' not in path.parts,'Parent traversal refused')
    for part in (path,*path.parents):
        if part.exists():require(not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'Reparse path refused')
    return path.resolve()


def load(path):
    path=safe(path);before=path.stat();require(before.st_size<=64*1024*1024,'Metadata bound exceeded')
    raw=path.read_bytes();after=path.stat()
    require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Metadata changed while reading')
    return json.loads(raw,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite metadata refused')))


def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def typed_same(left,right):
    if type(left) is not type(right):return False
    if type(left) is dict:return left.keys()==right.keys() and all(typed_same(item,right[key]) for key,item in left.items())
    if type(left) in (list,tuple):return len(left)==len(right) and all(typed_same(a,b) for a,b in zip(left,right))
    return left==right


def ns(value):
    match=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z',value or '')
    require(match is not None,'Exact UTC timestamp required')
    return calendar.timegm(datetime.datetime.strptime(match[1],'%Y-%m-%dT%H:%M:%S').timetuple())*10**9+int((match[2] or '').ljust(9,'0'))


def validate_terminal(state,birth,launch,before,after,context):
    require(state.get('format')=='has_owned_canonical_run_1' and state.get('status') in ('passed','failed','runner_error'), 'Terminal state required')
    require(type(state.get('suite_exit')) is int and ((state['status']=='passed' and state['suite_exit']==0) or (state['status']!='passed' and state['suite_exit']!=0)), 'State/exit mismatch')
    require(state.get('source_unchanged') is True and ns(state['finished_utc'])>=ns(state['started_utc']),'Completed unchanged source required')
    require(state['source_commit']==context['commit'] and type(state['pid']) is int and state['pid']==context['coordinator_pid'] and state['process_started']==context['coordinator_birth'],'Exact coordinator identity differs')
    require(state['checkout']==context['checkout'] and state['run_folder']==str(Path(context['checkout'])/'output'/context['run_name']),'Exact run scope differs')
    require(state['script_sha256']==context['runner_sha256'] and state['command']==[context['python_executable'],'-u','tests/verify.py'],'Canonical command/runner differs')
    require(birth['format']=='has_root_neon_corrected_birth_observation_1' and typed_same(birth['coordinator'],{'pid':context['coordinator_pid'],'creation_utc':context['coordinator_birth']}),'Actual nested birth schema differs')
    require(typed_same(birth['python'],{'pid':context['python_pid'],'parent_pid':context['coordinator_pid'],'creation_utc':context['python_birth'],'command_line':context['python_command']}),'Exact child birth/parent/command differs')
    require(launch['format']=='has_root_neon_full_launch_1' and launch['source_commit']==context['commit'] and type(launch['coordinator_pid']) is int and launch['coordinator_pid']==context['coordinator_pid'] and launch['coordinator_creation_utc']==context['coordinator_birth'],'Actual launch schema differs')
    require(launch['run_folder']==state['run_folder'] and type(launch['functional_source_files']) is int and launch['functional_source_files']==context['functional_sources'] and launch['runner']==context['runner'] and launch['runner_sha256']==context['runner_sha256'] and launch['graphics_lease']=='root-exclusive','Launch scope/runner/lease differs')
    require(typed_same(before,after) and before['commit']==context['commit'] and len(before['source_sha256'])==context['functional_sources'],'Before/after functional source identity differs')
    return state['status']=='passed'


def validate_result(result,context,registry):
    Legacy.validate_result(result,{'source_commit':context['commit']},registry)
    row=result['neon_workspace'];counts={'inset':12384,'behavior':32,'compact':14,'rail':45}
    require(row['format']=='has_neon_workspace_verification_1' and row['passed'] is True and typed_same(row['expected_checks'],counts) and type(row['checks']) is int and row['checks']==12475 and type(row['failures']) is int and row['failures']==0,'Neon result count/status differs')
    require(set(row['reports'])==set(counts) and row['all_functional_sources_hash_size_mtime_unchanged'] is True and row['all_private_jobs_and_desktops_closed'] is True,'Neon source/private closure differs')
    require(len(result)==158,'Expected158 named groups required')


def validate_current_sources(before):
    actual={path.relative_to(ROOT).as_posix() for part in ('src','tests','tools','data','examples') for path in (ROOT/part).rglob('*') if path.is_file() and path.suffix!='.pyc' and '__pycache__' not in path.parts}
    actual.update(('project.godot','main.tscn','run.py','launch.pyw'))
    require(actual==set(before['source_sha256']),'Functional source membership changed')
    for name,digest in before['source_sha256'].items():require(sha(safe(ROOT/name))==digest,'Functional source changed: '+name)


def terminal():
    # No output/verification.json read until terminal PASS and every birth/source pin passes.
    for name,digest in CONTEXT['immutable_run_inputs'].items():require(sha(RUN/name)==digest,'Pinned run input changed: '+name)
    state=load(RUN/'state.json');before=load(RUN/'source-before.json');after=load(RUN/'source-after.json')
    passed=validate_terminal(state,load(RUN/'root-birth-observation.json'),load(RUN/'launch.json'),before,after,CONTEXT)
    validate_current_sources(before)
    require(sha(Path(CONTEXT['runner']))==CONTEXT['runner_sha256'],'Canonical runner changed')
    require(sha(HERE/'legacy_result_gates.py')==CONTEXT['legacy_result_gates_sha256'],'Legacy result gates changed')
    require(sha(HERE/'RESULT_REGISTRY.json')==CONTEXT['registry_sha256'],'Registry changed')
    result=None
    if passed:
        path=OUTPUT/'verification.json';require(ns(state['started_utc'])<=path.stat().st_mtime_ns<=ns(state['finished_utc']),'Final full report is stale')
        result=load(path);validate_result(result,CONTEXT,load(HERE/'RESULT_REGISTRY.json'))
        normalized=path.read_text(encoding='utf-8-sig').replace('\r\n','\n').rstrip()
        log=(RUN/'canonical.log').read_text(encoding='utf-8-sig').replace('\r\n','\n').rstrip()
        require(log.endswith(normalized),'Fresh complete report is not exact canonical log suffix')
        require(all(not line.strip() or line.startswith('PASS ') for line in log[:-len(normalized)].splitlines()),'Unexpected PASS log prefix')
    return state,before,result


def observe():
    require(sha(PWSH)==CONTEXT['powershell_sha256'],'Approved observer executable changed')
    code=r'''$ErrorActionPreference='Stop'; $pins=@(@{pid=COORD_PID;birth='COORD_BIRTH'},@{pid=PYTHON_PID;birth='PYTHON_BIRTH'}); $identities=@(); foreach($pin in $pins){$item=Get-Process -Id $pin.pid -ErrorAction SilentlyContinue; $now=$null; if($item){$now=$item.StartTime.ToUniversalTime().ToString('o')}; $absent=($null -eq $item -or [DateTimeOffset]::Parse($now) -ne [DateTimeOffset]::Parse($pin.birth)); if(-not $absent){throw 'Exact original process is still alive'}; $identities+=@{pid=$pin.pid;expected_creation_utc=$pin.birth;pid_present=($null -ne $item);current_creation_utc=$now;original_absent=$true}}; $matches=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.ProcessId -ne DRIVER_PID -and ($_.CommandLine -like '*has-neon-review-20261116-c2d52ff*' -or $_.CommandLine -like '*has-acceptance-session-20261111*') -and ($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe).exe$' -or ($_.Name -match '^pythonw?.exe$') -or ($_.Name -match '^(pwsh|powershell).exe$' -and $_.CommandLine -match '(run_canonical_owned|start_canonical|private_desktop)'))}); if($matches.Count){throw 'A scoped runtime, helper or coordinator remains'}; @{coordinator=$identities[0];python=$identities[1];owned_runtime_matches=@();owned_runtime_command_matches_absent=$true;root_observer_issued_no_termination=$true;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 8 -Compress'''
    for key,value in {'COORD_PID':CONTEXT['coordinator_pid'],'COORD_BIRTH':CONTEXT['coordinator_birth'],'PYTHON_PID':CONTEXT['python_pid'],'PYTHON_BIRTH':CONTEXT['python_birth'],'DRIVER_PID':os.getpid()}.items():code=code.replace(key,str(value))
    process=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    # No termination API. A timeout or failed query never releases the graphics lease.
    out,err=process.communicate(timeout=60)
    require(process.poll() is not None and process.returncode==0 and not err.strip(),'Root identity/scope observer failed')
    value=json.loads(out);value['observer_retained_Popen_reaped']=True
    require(value['coordinator']['original_absent'] is True and value['python']['original_absent'] is True and value['owned_runtime_command_matches_absent'] is True and not value['owned_runtime_matches'],'Root absence observation differs')
    return value


def classify_receipt(receipt,is_cancel,passed):
    require(receipt.get('format')=='studio_private_desktop_1','Physical private receipt required')
    require(all(receipt.get(key) is True for key in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed')),'Private placement/closure failed')
    require(all(receipt.get(key) is False for key in ('desktop_switch_requested','foreground_child_observed')) and not receipt.get('monitor_error') and not receipt.get('desktop_enumeration_error'),'Desktop switch/foreground/monitor/enumeration error')
    require(type(receipt.get('exit')) is int,'Integer physical exit required')
    if is_cancel:
        require(receipt['exit']==2 and receipt.get('cancelled') is True and receipt.get('error')=='Owned converter cancelled','Registered Krita cancellation differs')
        return 'registered_Krita_cancel_exit2'
    require(not receipt.get('error') and not receipt.get('cancelled'),'Unregistered wrapper error/cancellation')
    if receipt['exit']==0:return 'normal_exit0'
    require(not passed,'A PASS suite contains a failed physical process')
    return 'failed_partial_run_nonzero_exit'


def validate_ownership(rows,inline,cancel_value):
    desktops={};classes={}
    for row in rows:
        value=row['receipt']
        require(type(value.get('desktop')) is str and type(value.get('child_pid')) is int and value['child_pid']>0,'Missing physical desktop/child identity')
        desktop=value['desktop']
        if desktop in desktops:require(typed_same(desktops[desktop],value) and classes[desktop]==row['classification'],'Conflicting physical receipt copies for one desktop')
        desktops[desktop]=value;classes[desktop]=row['classification']
    require(sum(typed_same(value,cancel_value) for value in desktops.values())==(1 if cancel_value is not None else 0),'Registered cancellation job count differs')
    for item in inline:require(typed_same(desktops.get(item['receipt'].get('desktop')),item['receipt']),'Inline receipt lacks exactly matching physical ownership')
    return classes


def inventory(state,result,end_ns):
    start=ns(state['started_utc']);finish=ns(state['finished_utc']);passed=state['status']=='passed'
    refs={};inline=[];documents={};queue=[];seen=set()
    def add(path,origin):
        path=safe(path);require(path.is_relative_to(OUTPUT.resolve()) and path.suffix=='.json' and path.is_file(),'Owned physical receipt path required')
        refs.setdefault(path,set()).add(origin)
    def walk(value,origin):
        if type(value) is dict:
            if value.get('format')=='studio_private_desktop_1':inline.append({'origin':origin,'receipt':value})
            if value.get('format')=='has_helper_preview_main_verification_1' and value.get('mode')=='graphical':
                for row in value.get('results',[]):
                    if 'private_receipt' in row:add(Path(value['actual_res_root'])/'output/helper-preview-qa'/row['label']/'private-receipt.json',origin+'.derived_helper_'+row['label'])
            for key,item in value.items():
                if type(item) is str and re.match(r'^[A-Za-z]:[\\/]',item):
                    path=Path(item)
                    if path.suffix.lower()=='.json' and ('receipt' in key.lower() or 'private-desktop' in item.lower() or 'private-receipt' in item.lower()):add(path,origin+'.'+key)
                    if key=='folder' and path.is_dir() and (path/'verification.json').is_file() and path.resolve().is_relative_to(OUTPUT.resolve()):queue.append(path/'verification.json')
                walk(item,origin+'.'+key)
        elif type(value) is list:
            for index,item in enumerate(value):
                if type(item) is str and re.match(r'^[A-Za-z]:[\\/]',item) and Path(item).suffix.lower()=='.json' and ('receipt' in origin.lower() or 'private-desktop' in item.lower() or 'private-receipt' in item.lower()):add(item,origin+'['+str(index)+']')
                walk(item,origin+'['+str(index)+']')
    for path in (OUTPUT/'private-desktop').glob('*.json'):
        if start<=path.stat().st_mtime_ns<=end_ns:add(path,'fresh_root_actual_interval')
    for pattern in ('*-verification.json','*-result.json'):
        queue.extend(path for path in OUTPUT.glob(pattern) if start<=path.stat().st_mtime_ns<=end_ns)
    if passed:
        queue.append(OUTPUT/'verification.json')
    while queue:
        require(len(seen)<1024 and len(refs)<4096 and len(inline)<10000,'Metadata discovery bound exceeded')
        path=safe(queue.pop(0))
        if path in seen:continue
        require(path.is_relative_to(OUTPUT.resolve()) and (passed or path!=OUTPUT/'verification.json'),'Stale final report prohibited on failure')
        require(start<=path.stat().st_mtime_ns<=end_ns,'Referenced phase document is stale')
        seen.add(path);documents[str(path)]={'sha256':sha(path),'mtime_ns':path.stat().st_mtime_ns};walk(load(path),str(path))
    cancel=None;phase=OUTPUT/'krita-import-verification.json'
    if phase.is_file() and start<=phase.stat().st_mtime_ns<=finish:
        cancel=safe(load(phase)['cancelled_receipt']);add(cancel,'source_registered_Krita_cancel')
        source=ROOT/'tests/verify_krita_import.py'
        require(sha(source)==load(RUN/'source-before.json')['source_sha256']['tests/verify_krita_import.py'] and "assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']" in source.read_text(encoding='utf-8'),'Krita cancellation source registration differs')
    require(not passed or cancel is not None,'Full PASS requires fresh registered Krita cancellation')
    rows=[];ignored=[];cancel_value=load(cancel) if cancel is not None else None
    for path in sorted(refs,key=str):
        value=load(path)
        if type(value) is not dict or value.get('format')!='studio_private_desktop_1':
            ignored.append({'path':str(path),'sha256':sha(path),'references':sorted(refs[path])});continue
        require(start<=path.stat().st_mtime_ns<=end_ns,'Physical receipt outside actual interval')
        require(not passed or path.stat().st_mtime_ns<=finish,'PASS receipt completed after canonical terminal state')
        classification=classify_receipt(value,typed_same(value,cancel_value),passed)
        row={'source_path':str(path),'source_sha256':sha(path),'mtime_ns':path.stat().st_mtime_ns,'classification':classification,'after_state_finish':path.stat().st_mtime_ns>finish,'receipt':value,'references':sorted(refs[path])}
        rows.append(row)
    require(rows,'No actual physical receipts discovered')
    unique_classes=validate_ownership(rows,inline,cancel_value)
    return {'rows':rows,'unique_physical_jobs':len(unique_classes),'unique_job_classifications':unique_classes,'duplicate_physical_copies':len(rows)-len(unique_classes),'inline_receipts':inline,'phase_documents':documents,'ignored_named_non_receipts':ignored,'registered_cancel_observed':cancel is not None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-terminal-confirmed',action='store_true',required=True)
    parser.add_argument('--release-closed',action='store_true')
    args=parser.parse_args()
    sealed=load(HERE/'INDEX.json')
    for row in sealed['files']:require(sha(HERE/row['path'])==row['sha256'],'Sealed helper payload changed')
    state,before,result=terminal()  # No process query, final report access or audit write before these gates.
    observed=observe();end=ns(observed['observed_utc']);require(end>=ns(state['finished_utc']),'Observation predates finish')
    found=inventory(state,result,end)
    # Recheck every terminal/source/report and receipt identity before the first audit write.
    state2,before2,result2=terminal();require(typed_same((state,before,result),(state2,before2,result2)),'Terminal inputs changed during audit')
    for row in found['rows']:require(sha(row['source_path'])==row['source_sha256'],'Receipt changed during audit')
    for name,meta in found['phase_documents'].items():require(sha(name)==meta['sha256'],'Phase document changed before audit admission')
    out=RUN/'terminal-audit-attempt1';require(not out.exists(),'Fresh terminal audit output required');out.mkdir(exist_ok=False)
    for index,row in enumerate(found['rows']):
        path=Path(row['source_path']);target=out/f'receipt-{index:03d}-{path.name}';target.write_bytes(path.read_bytes());require(sha(target)==row['source_sha256'],'Raw receipt copy differs');row['preserved_raw_copy']=str(target)
    for name in ('state.json','source-before.json','source-after.json','launch.json','root-birth-observation.json','canonical.log'):(out/name).write_bytes((RUN/name).read_bytes())
    if result is not None:(out/'full-verification.json').write_bytes((OUTPUT/'verification.json').read_bytes())
    # Preserve every actually consulted fresh phase document now, before a future rerun can overwrite it.
    phase_out=out/'phase-documents';phase_out.mkdir()
    for index,(name,meta) in enumerate(found['phase_documents'].items()):
        path=Path(name);require(sha(path)==meta['sha256'],'Phase document changed');target=phase_out/f'{index:03d}-{path.name}';target.write_bytes(path.read_bytes());require(sha(target)==meta['sha256'],'Raw phase copy differs');meta['preserved_raw_copy']=str(target)
    passed=state['status']=='passed'
    classes=list(found['unique_job_classifications'].values())
    report={'format':'has_neon_f387_terminal_receipt_inventory_1','source_commit':CONTEXT['commit'],'functional_sources':len(before['source_sha256']),'run_directory':str(RUN),'suite_status':state['status'],'suite_exit':state['suite_exit'],'full_suite_passed':passed,'final_full_report_used':passed,'result_groups':158 if passed else None,'core_groups':36 if passed else None,'movie_groups':21 if passed else None,'physical_receipt_files':len(found['rows']),'normal_exit0':classes.count('normal_exit0'),'registered_cancel_exit2':classes.count('registered_Krita_cancel_exit2'),'failed_partial_nonzero':classes.count('failed_partial_run_nonzero_exit'),'all_collected_jobs_desktops_closed_private':True,'all_inline_exact_physical_matches':True,'process_observation':observed,'root_observer_issued_no_termination':True,'graphics_lease_released':False,**found}
    save(out/'receipt-inventory.json',report);save(out/'host-observation.json',observed)
    if args.release_closed:
        second=observe();state3,before3,result3=terminal();require(typed_same((state,before,result),(state3,before3,result3)),'Terminal changed before release')
        for row in found['rows']:require(sha(row['source_path'])==row['source_sha256'],'Receipt changed before release')
        release={'format':'has_root_neon_f387_graphics_lease_release_1','released':True,'release_kind':'closed_passed_full_run' if passed else 'closed_failed_partial_run','released_utc':second['observed_utc'],'source_commit':CONTEXT['commit'],'canonical_run':RUN.name,'coordinator_pid':CONTEXT['coordinator_pid'],'python_pid':CONTEXT['python_pid'],'functional_sources':CONTEXT['functional_sources'],'full_suite_passed':passed,'suite_exit':state['suite_exit'],'final_full_report_used':passed,'physical_jobs':found['unique_physical_jobs'],'physical_receipt_files':len(found['rows']),'all_collected_jobs_desktops_closed_private':True,'all_inline_exact_physical_matches':True,'root_observer_issued_no_termination':True,'receipt_inventory_sha256':sha(out/'receipt-inventory.json'),'terminal_state_sha256':sha(RUN/'state.json'),'second_identity_and_scope_observation':second}
        save(RUN/'graphics-lease-closed.json',release)
    print(json.dumps({'audit':str(out),'physical_receipts':len(found['rows']),'inventory_sha256':sha(out/'receipt-inventory.json'),'full_suite_passed':passed,'graphics_lease_released':args.release_closed}))


if __name__=='__main__':main()
