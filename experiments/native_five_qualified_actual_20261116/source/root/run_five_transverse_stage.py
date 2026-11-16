"""Root-owned isolated strict2 GUI qualification with preserved failed predecessors."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
STUDIO=ROOT/'output/native-five-stage-attempt3/Studio'
PACKET=ROOT/'experiments/source_native_five_transverse_fixture_20261116'
PWSH=Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def closure(folder,label):
    code="$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    p=subprocess.Popen([str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-Command',code],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate(timeout=30)
    (folder/(label+'-inventory-stdout.log')).write_bytes(out);(folder/(label+'-inventory-stderr.log')).write_bytes(err)
    assert p.returncode==0 and not err.strip();record=json.loads(out)
    save(folder/(label+'-closure.json'),record);assert record['owned_count']==0
    return record
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--packet-index',required=True);options=ap.parse_args()
    assert sha(PYTHON)=='03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
    assert sha(PWSH)=='2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
    assert sha(PACKET/'INDEX.json')==options.packet_index
    index=load(PACKET/'INDEX.json');rows=index['files']
    entries=rows.items() if isinstance(rows,dict) else ((x['path'],x) for x in rows)
    for name,row in entries:
        p=PACKET/name;assert p.resolve().is_relative_to(PACKET.resolve()) and not p.is_symlink()
        assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    contract=load(PACKET/'CONTRACT.json')
    assert sha(STUDIO/'src/source_secondary.gd')=='3b2c29dc11b60e68306f858a32d03271e30a039b8451916df2ff9324e7da4f84'
    state=STUDIO/'output/source-native-five-state-20261116T040011702334/verification.json'
    s=load(state);assert s['passed'] and s['checks_observed']==266 and s['runtime_lease_released']
    folder=STUDIO.parent/'TRANSVERSE-ROOT-EXECUTION';folder.mkdir()
    closure(folder,'before')
    overlays=[]
    for name,old,key in [('source_native_five_live_ui.gd','ee14e069a6e9606edb1338aac1c91397d47fad9797148da09868babbc27c3a0a','observer_sha256'),('verify_source_native_five_live.py','07c3c2e7403af0096753c1c8c2b6e8516cb3bd3b74b46cfdc29bb00fca90d3e0','driver_sha256')]:
        source=PACKET/name;target=STUDIO/'tests'/name
        assert sha(target)==old and sha(source)==contract[key]
        target.write_bytes(source.read_bytes());overlays.append({'path':'tests/'+name,'preimage':old,'sha256':sha(target)})
    save(folder/'OVERLAYS.json',{'packet_index_sha256':sha(PACKET/'INDEX.json'),'overlays':overlays,'prior_state_verification_sha256':sha(state),'main_modified':False})
    command=load(STUDIO.parent/'ROOT-ONLY-COMMANDS.json')['GUI_after_state_terminal_closure_and_new_exclusive_lease']
    assert Path(command[0])==PYTHON and Path(command[2])==STUDIO/'tests/verify_source_native_five_live.py'
    save(folder/'command.json',command)
    started=time.monotonic();p=subprocess.Popen(command,cwd=STUDIO,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    save(folder/'start.json',{'pid':p.pid,'retained_Popen':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    timed=False
    try:out,err=p.communicate(timeout=1000)
    except subprocess.TimeoutExpired:
        timed=True;p.terminate();out,err=p.communicate(timeout=30)
    (folder/'stdout.log').write_bytes(out);(folder/'stderr.log').write_bytes(err)
    process={'pid':p.pid,'exit':p.returncode,'retained_Popen_reaped':p.poll() is not None,'timed_out':timed,'owned_wrapper_terminated':timed,'seconds':time.monotonic()-started}
    save(folder/'process.json',process)
    path=STUDIO/'output/native-five-gui-attempt1/verification.json'
    result=load(path) if path.exists() else {}
    after=closure(folder,'after')
    record={'format':'has_root_strict2_transverse_actual_1','passed':p.returncode==0 and not timed and result.get('passed') is True and result.get('checks_observed')==102 and after['owned_count']==0,
        'checks_observed':result.get('checks_observed'),'phase_expected':result.get('phase_expected'),'process':process,
        'verification_sha256':sha(path) if path.exists() else None,'state266_predecessor_sha256':sha(state),'packet_index_sha256':sha(PACKET/'INDEX.json'),
        'runtime_lease_released':True,'main_promoted':False,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder/'verification.json',record);print(json.dumps(record));return 0 if record['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
