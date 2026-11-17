"""Execute the reviewed staged normal diagnostic; private vectors stay in output."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'output/normal-boundary-20261116-attempt2'
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PACKET=ROOT/'experiments/normal_boundary_probe_sentinel_20261116'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def closure(folder,label):
    code="$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    p=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate(timeout=30);(folder/(label+'-inventory-stdout.log')).write_bytes(out);(folder/(label+'-inventory-stderr.log')).write_bytes(err)
    assert p.returncode==0 and not err.strip();value=json.loads(out);save(folder/(label+'-closure.json'),value);assert value['owned_count']==0;return value
def invoke(folder,label,command,timeout):
    save(folder/(label+'-command.json'),command);start=time.monotonic()
    p=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    save(folder/(label+'-start.json'),{'pid':p.pid,'retained_Popen':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});timed=False
    try:out,err=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed=True;p.terminate();out,err=p.communicate(timeout=15)
    (folder/(label+'-stdout.log')).write_bytes(out);(folder/(label+'-stderr.log')).write_bytes(err)
    row={'pid':p.pid,'exit':p.returncode,'retained_Popen_reaped':p.poll() is not None,'timed_out':timed,'owned_wrapper_terminated':timed,'seconds':time.monotonic()-start}
    save(folder/(label+'-process.json'),row);return row,out.decode('utf-8','replace')
def main():
    assert sha(PWSH)=='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
    assert sha(PACKET/'INDEX.json')=='a2475b28c03c6b87cc0d98d537433204b9553122a97f1197321455a491e2ef64'
    rows=load(PACKET/'INDEX.json')['files']
    entries=rows.items() if isinstance(rows,dict) else ((row['path'],row) for row in rows)
    for name,row in entries:
        p=PACKET/name;assert p.resolve().is_relative_to(PACKET.resolve()) and sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
    import sys;sys.path.insert(0,str(PACKET));import probe_support
    lease,files=probe_support.check_lease(STAGE/'lease.json',PACKET/'capture_blender_normals.py')
    assert sha(STAGE/'lease.json')=='9462405eeb4d909c7c5bd8394f89926b1b864f94937869bf1992aae3dc7d7b02'
    folder=STAGE/'root-execution';folder.mkdir();closure(folder,'before')
    commands=load(STAGE/'ROOT_COMMANDS.json');capture,stdout=invoke(folder,'capture',commands['capture_command'],commands['outer_timeout_seconds'])
    receipt_path=STAGE/'private-receipt.json';receipt=load(receipt_path) if receipt_path.exists() else {}
    closed=all(receipt.get(n) is True for n in ('child_desktop_confirmed','job_closed','desktop_closed')) and receipt.get('foreground_child_observed') is False and receipt.get('exit')==capture['exit']
    public_path=STAGE/'capture/PUBLIC_CAPTURE.json';public=load(public_path) if public_path.exists() else {}
    capture_ok=capture['exit']==0 and not capture['timed_out'] and capture['retained_Popen_reaped'] and closed and 'HAS_NORMAL_CAPTURE ' in stdout and public.get('status')=='CAPTURE_COMPLETE_COMPARISON_UNRUN'
    required=load(PACKET/'ROOT_ADDITIONAL_REQUIREMENTS.json')['public_field_required_values']
    policy=public.get('background_isolation_sentinel',{})
    capture_ok=capture_ok and receipt.get('private_window_seen') is True and 'HAS_NORMAL_ISOLATION_SENTINEL ' in stdout and all(type(policy.get(k)) is type(v) and policy.get(k)==v for k,v in required.items())
    comparison=None;result={}
    if capture_ok:
        comparison,_=invoke(folder,'comparison',commands['comparison_command'],90)
        if (STAGE/'BLENDER_BOUNDARY_COMPARISON.json').exists():result=load(STAGE/'BLENDER_BOUNDARY_COMPARISON.json')
    probe_support.check_lease(STAGE/'lease.json',PACKET/'capture_blender_normals.py')
    after=closure(folder,'after')
    record={'format':'has_root_normal_boundary_execution_1','diagnostic_completed':capture_ok and comparison is not None and comparison['exit']==0 and not comparison['timed_out'] and result.get('format')=='has_blender_normal_boundary_comparison_2',
        'capture':capture,'comparison':comparison,'private_job_desktop_closed':closed,'runtime_lease_released':after['owned_count']==0,
        'public_capture_sha256':sha(public_path) if public else None,'comparison_sha256':sha(STAGE/'BLENDER_BOUNDARY_COMPARISON.json') if result else None,
        'comparison_status':result.get('status'),'normal_fidelity_pass_claimed':False,'lease_and_all_input_context_rechecked':True,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder/'verification.json',record);print(json.dumps(record));return 0 if record['diagnostic_completed'] else 1
if __name__=='__main__':raise SystemExit(main())
