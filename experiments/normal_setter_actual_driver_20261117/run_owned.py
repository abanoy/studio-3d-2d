"""ROOT ONLY: execute the exact staged setter probe on its approved private desktop.

Source preparation must not import or execute this driver. Native logs stay private.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import time
import traceback
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'output/normal-setter-boundary-20261116-attempt1'
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
SCOPES=('has-acceptance-session-20261111','has-neon-review-20261116-c2d52ff')
WRAPPER_SHA='9788e7fde42de7bce022589c86146eaa93deb142ef368aa37a05259ec3047628'
PWSH_SHA='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
PYTHON_SHA='03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path):return json.loads(path.read_bytes())


def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def safe(path):
    path=Path(path)
    assert path.is_absolute()
    for part in (path,*path.parents):
        if part.exists():assert not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400
    return path.resolve()


def same(actual,expected):
    if type(actual) is not type(expected):return False
    if isinstance(expected,dict):return actual.keys()==expected.keys() and all(same(actual[key],expected[key]) for key in expected)
    if isinstance(expected,list):return len(actual)==len(expected) and all(same(a,b) for a,b in zip(actual,expected))
    return actual==expected


def scalar_metadata(value,depth=0):
    assert depth<=16
    if isinstance(value,dict):
        assert len(value)<=100 and all(type(key) is str and len(key)<=200 for key in value)
        for item in value.values():scalar_metadata(item,depth+1)
    elif isinstance(value,list):
        # Placement policy may contain the two zero-size pixel dimensions; no geometry arrays.
        assert len(value)<=4
        for item in value:
            assert not isinstance(item,(list,dict));scalar_metadata(item,depth+1)
    elif type(value) is float:assert math.isfinite(value)
    elif type(value) is str:assert len(value)<=4096
    else:assert value is None or type(value) in (bool,int)


def checked_packet(packet,digest):
    packet=safe(packet)
    assert packet.parent==safe(ROOT/'experiments') and sha(packet/'INDEX.json')==digest
    rows=load(packet/'INDEX.json')['files']
    entries=rows.items() if isinstance(rows,dict) else ((row['path'],row) for row in rows)
    pins={}
    for name,row in entries:
        path=safe(packet/name)
        assert path.is_relative_to(packet) and path.is_file() and sha(path)==row['sha256'] and path.stat().st_size==row['bytes']
        pins[name]=row['sha256']
    for name in ['setter_probe.py','setter_support.py','stage_after_full.py','ROOT_ADDITIONAL_REQUIREMENTS.json']:
        assert name in pins,'Sentinel successor and its root policy are required'
    assert {path.relative_to(packet).as_posix() for path in packet.rglob('*') if path.is_file()}==set(pins)|{'INDEX.json'}
    return packet,pins


def closure(folder,label):
    # Exact image names exclude this PowerShell observer. Both worktree scopes must be idle.
    code="$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and (($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$') -or ($_.Name -match '^(pythonw?|pwsh|powershell)\\.exe$' -and $_.CommandLine -match '(run_canonical_owned\\.ps1|start_canonical_[^ ]*\\.ps1|tests[\\\\/]verify\\.py)')) -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*has-neon-review-20261116-c2d52ff*')}); @{owned_count=$items.Count; main_count=@($items | Where-Object {$_.CommandLine -like '*has-acceptance-session-20261111*'}).Count; neon_count=@($items | Where-Object {$_.CommandLine -like '*has-neon-review-20261116-c2d52ff*'}).Count; observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    process=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    try:out,err=process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:out,err=process.communicate(timeout=10)
        except subprocess.TimeoutExpired:process.kill();out,err=process.communicate(timeout=10)
        raise RuntimeError('Owned inventory observer timed out')
    (folder/(label+'-inventory-stdout.log')).write_bytes(out)
    (folder/(label+'-inventory-stderr.log')).write_bytes(err)
    assert process.returncode==0 and process.poll() is not None and not err.strip()
    value=json.loads(out);value['observer_retained_Popen_reaped']=True
    save(folder/(label+'-closure.json'),value)
    assert all(type(value.get(name)) is int and value[name]==0 for name in ['owned_count','main_count','neon_count'])
    return value


def invoke(folder,command):
    save(folder/'capture-command.json',command)
    start=time.monotonic();process=None;out=b'';err=b'';timed=False;terminated=False
    try:
        process=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        save(folder/'capture-start.json',{'pid':process.pid,'retained_Popen':True,'observed_after_creation_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        try:out,err=process.communicate(timeout=165)
        except subprocess.TimeoutExpired:
            timed=True;terminated=True;process.terminate()
            try:out,err=process.communicate(timeout=15)
            except subprocess.TimeoutExpired:process.kill();out,err=process.communicate(timeout=15)
    finally:
        if process is not None and process.poll() is None:
            terminated=True;process.terminate()
            try:out,err=process.communicate(timeout=15)
            except subprocess.TimeoutExpired:process.kill();out,err=process.communicate(timeout=15)
        # These streams are private even though the expected success marker is scalar-only.
        (folder/'PRIVATE_CAPTURE_STDOUT.log').write_bytes(out)
        (folder/'PRIVATE_CAPTURE_STDERR.log').write_bytes(err)
        if process is not None:
            row={'pid':process.pid,'exit':process.returncode,'retained_Popen_reaped':process.poll() is not None,
                'timed_out':timed,'owned_wrapper_terminated':terminated,'seconds':time.monotonic()-start}
            save(folder/'capture-process.json',row)
    assert process is not None and process.poll() is not None
    return row,out.decode('utf-8','replace')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',type=Path,required=True)
    parser.add_argument('--packet-index-sha256',required=True)
    parser.add_argument('--lease-sha256',required=True)
    parser.add_argument('--expected-head',required=True)
    args=parser.parse_args()
    assert os.name=='nt' and re.fullmatch('[a-f0-9]{40}',args.expected_head)
    assert all(re.fullmatch('[a-f0-9]{64}',value) for value in [args.packet_index_sha256,args.lease_sha256])
    assert sha(Path(sys.executable))==PYTHON_SHA and sha(PWSH)==PWSH_SHA and sha(ROOT/'tools/private_desktop.py')==WRAPPER_SHA
    packet,pins=checked_packet(args.packet,args.packet_index_sha256)
    requirements=load(packet/'ROOT_ADDITIONAL_REQUIREMENTS.json')
    assert requirements['format']=='has_setter_hidden_background_additional_root_requirements_1' and requirements['original_primary_lease_roles']==26 and requirements['retain_all_original_receipt_and_source_requirements'] is True
    lease_path=safe(STAGE/'lease.json');commands_path=safe(STAGE/'ROOT_COMMANDS.json')
    assert sha(lease_path)==args.lease_sha256
    staged=load(STAGE/'STAGED.json');commands=load(commands_path)
    assert staged['format']=='has_setter_probe_stage_1' and staged['lease_sha256']==args.lease_sha256 and staged['current_head']==args.expected_head and staged['roles']==26 and staged['native_engine_launched'] is False
    assert commands['format']=='has_setter_probe_future_root_commands_1' and commands['not_executed'] is True and commands['capture_cwd']==str(ROOT) and commands['outer_timeout_seconds']==165
    assert commands['expected_exit']==0 and commands['expected_marker']=='HAS_SETTER_PROBE ' and commands['expected_public_status']=='SETTER_BOUNDARIES_MEASURED'
    required={'exit':0,'child_desktop_confirmed':True,'foreground_child_observed':False,'job_closed':True,'desktop_closed':True}
    assert same(requirements['private_receipt_required_addition'],{'private_window_seen':True})
    required.update(requirements['private_receipt_required_addition'])
    assert same(commands['receipt_requirements'],required)
    spec=importlib.util.spec_from_file_location('root_owned_setter_support',packet/'setter_support.py')
    support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
    lease,files=support.check_lease(lease_path,packet/'setter_probe.py')
    assert lease['expected_head']==args.expected_head
    checked_policy(packet,requirements,lease)
    for role,name in [('probe','setter_probe.py'),('support','setter_support.py'),('instrumentation','instrumentation.py'),('vvd_parser','vvd_normals.py')]:
        assert files[role]==packet/name and sha(files[role])==pins[name]
    expected=[str(Path(sys.executable).with_name('pythonw.exe')),str(ROOT/'tools/private_desktop.py'),'--receipt',str(STAGE/'private-receipt.json'),'--timeout','150','--memory-limit-mib','4096','--',str(files['blender_exe']),'--background','--factory-startup','--offline-mode','--disable-autoexec','--python-exit-code','1','--python',str(files['probe']),'--','--lease',str(lease_path)]
    assert commands['capture_command']==expected
    assert commands['public_result']==str(STAGE/'capture/PUBLIC_SETTER.json') and commands['private_result']==str(STAGE/'capture/PRIVATE_SETTER.json')
    assert commands['additional_stdout_marker']==requirements['additional_stdout_marker']
    assert commands['public_isolation_result']==str(STAGE/'capture'/requirements['sidecar_path_relative_to_capture'])
    commands_sha256=sha(commands_path)
    folder=STAGE/'root-execution';folder.mkdir(exist_ok=False)
    before={};after={};capture={};public={};receipt={};placement={};completed=False;context_rechecked=False;error_type=None
    try:
        before=closure(folder,'before')
        capture,stdout=invoke(folder,commands['capture_command'])
        receipt=load(STAGE/'private-receipt.json')
        assert all(type(receipt.get(key)) is type(value) and receipt.get(key)==value for key,value in required.items())
        assert receipt.get('private_window_seen') is True and receipt.get('desktop_switch_requested') is False and not receipt.get('monitor_error')
        assert capture['exit']==0 and not capture['timed_out'] and capture['retained_Popen_reaped'] is True and not capture['owned_wrapper_terminated']
        public_path=STAGE/'capture/PUBLIC_SETTER.json'
        assert public_path.stat().st_size<=256*1024
        public=load(public_path);scalar_metadata(public)
        assert public['format']=='has_sourceio_setter_boundary_probe_1' and public['status']=='SETTER_BOUNDARIES_MEASURED'
        assert public['files_unchanged'] is True and public['SourceIO_import_executed'] is True and public['original_importer_patched_on_disk'] is False and public['GLB_exported'] is False and public['blend_saved'] is False and public['material_resources_read'] is False
        markers=[line[len(commands['expected_marker']):] for line in stdout.splitlines() if line.startswith(commands['expected_marker'])]
        assert len(markers)==1 and same(json.loads(markers[0]),public)
        private_path=STAGE/'capture/PRIVATE_SETTER.json'
        assert 0<private_path.stat().st_size<=96*1024*1024 and private_path.stat().st_size==public['private_bytes'] and sha(private_path)==public['private_sha256']
        # Placement schema is pinned separately by the sentinel successor; never bypass it.
        placement=check_placement(packet,requirements,lease,stdout,public_path,private_path)
        completed=True
    except Exception as error:
        error_type=type(error).__name__
        (folder/'PRIVATE_DRIVER_FAILURE.log').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        if capture:
            try:
                lease_after,files_after=support.check_lease(lease_path,packet/'setter_probe.py')
                assert lease_after==lease and files_after==files and sha(lease_path)==args.lease_sha256
                checked_policy(packet,requirements,lease)
                checked_packet(packet,args.packet_index_sha256)
                assert sha(commands_path)==commands_sha256
                assert sha(ROOT/'tools/private_desktop.py')==WRAPPER_SHA and sha(PWSH)==PWSH_SHA and sha(Path(sys.executable))==PYTHON_SHA
                context_rechecked=True
            except Exception as error:
                error_type=error_type or type(error).__name__
                (folder/'PRIVATE_CONTEXT_FAILURE.log').write_text(traceback.format_exc(),encoding='utf-8')
        # invoke() reaps the exact wrapper before this authoritative two-scope closure.
        try:after=closure(folder,'after')
        except Exception as error:
            error_type=error_type or type(error).__name__
            (folder/'PRIVATE_CLOSURE_FAILURE.log').write_text(traceback.format_exc(),encoding='utf-8')
    complete=completed and context_rechecked and before.get('owned_count')==0 and after.get('owned_count')==0
    record={'format':'has_root_setter_boundary_execution_1','diagnostic_completed':complete,'capture':capture,
        'packet':packet.name,'packet_index_sha256':args.packet_index_sha256,'probe_sha256':pins['setter_probe.py'],
        'lease_sha256':args.lease_sha256,'ROOT_COMMANDS_sha256':commands_sha256,
        'driver_sha256':sha(Path(__file__)),'expected_head':args.expected_head,'public_status':public.get('status'),
        'public_setter_sha256':sha(STAGE/'capture/PUBLIC_SETTER.json') if public else None,
        'public_placement_sha256':placement.get('public_placement_sha256'),'metadata_policy_sha256':placement.get('metadata_policy_sha256'),
        'placement_validated':bool(placement),'private_job_desktop_closed':all(receipt.get(key) is True for key in ['child_desktop_confirmed','job_closed','desktop_closed']),
        'both_scopes_released':after.get('owned_count')==0 and after.get('main_count')==0 and after.get('neon_count')==0,
        'lease_all26_roles_full_source_and_runtime_rechecked':context_rechecked,'native_arrays_or_failure_logs_public':False,
        'normal_fidelity_pass_claimed':False,'error_type':error_type,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder/'verification.json',record)
    print(json.dumps(record))
    return 0 if complete else 1


def checked_policy(packet,requirements,lease):
    metadata=requirements['metadata_policy']
    policy_path=safe(metadata['path'])
    assert policy_path==packet/'ISOLATION_POLICY.json' and sha(policy_path)==metadata['sha256']
    assert same(lease['additional_metadata_policy'],metadata)
    policy=load(policy_path)
    assert policy['format']=='has_setter_background_isolation_policy_1' and policy['original_lease_roles']==26
    assert policy['public_sidecar']==requirements['sidecar_path_relative_to_capture'] and policy['public_sidecar_format']==requirements['sidecar_format']
    assert same(policy['public_field_required_values'],requirements['public_field_required_values'])
    for name in ['public_capture_field','public_setter_sha256_field','private_setter_sha256_field','additional_stdout_marker','private_receipt_required_addition']:
        assert same(policy[name],requirements[name])
    return policy


def check_placement(packet,requirements,lease,stdout,public_path,private_path):
    checked_policy(packet,requirements,lease)
    metadata=requirements['metadata_policy']
    relative=Path(requirements['sidecar_path_relative_to_capture'])
    assert relative.name=='PUBLIC_PLACEMENT.json' and len(relative.parts)==1
    sidecar_path=safe(public_path.parent/relative)
    assert sidecar_path.stat().st_size<=64*1024
    sidecar=load(sidecar_path);scalar_metadata(sidecar)
    assert sidecar['format']==requirements['sidecar_format']
    assert sidecar[requirements['public_setter_sha256_field']]==sha(public_path)
    assert sidecar[requirements['private_setter_sha256_field']]==sha(private_path)
    assert sidecar['metadata_policy_sha256']==metadata['sha256'] and sidecar['numeric_public_and_private_outputs_unchanged'] is True
    sentinel=sidecar[requirements['public_capture_field']]
    assert all(type(sentinel.get(key)) is type(value) and same(sentinel.get(key),value) for key,value in requirements['public_field_required_values'].items())
    marker=requirements['additional_stdout_marker']
    lines=[line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    assert len(lines)==1 and same(json.loads(lines[0]),sidecar)
    return {'public_placement_sha256':sha(sidecar_path),'metadata_policy_sha256':metadata['sha256']}


if __name__=='__main__':raise SystemExit(main())
