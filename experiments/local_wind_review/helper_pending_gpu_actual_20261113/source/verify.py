"""Prepare a pinned source copy; graphics require explicit released-lease mode."""
from pathlib import Path
import argparse
import ctypes
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import uuid
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'output/helper-preview-integration-20261113'
PIN='9897f86019dfb8499d0ee30f6560580fac7bb8da'
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PYTHONW=Path(r'C:\Program Files\Python313\pythonw.exe')
GODOT=Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp(p):
    p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def write(p,v):
    with Path(p).open('x',encoding='utf-8')as f:json.dump(v,f,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def safe(p):
    p=Path(p).absolute();assert p.resolve().is_relative_to(TASK.resolve())and p.resolve()!=TASK.resolve()
    for part in (p,*p.parents):
        if part.exists():assert not part.is_symlink()and not getattr(part.lstat(),'st_file_attributes',0)&0x400
    return p
def unchanged(rows):
    return all(Path(r['path']).is_file()and stamp(r['path'])==r for r in rows)

def lease_free(path):
    # The root writes this only after an authoritative host observation. Also
    # recheck the old coordinator through a native handle at admission time.
    release=json.loads(Path(path).read_bytes())
    assert release['format']=='has_canonical_graphics_lease_released_1'and release['released']is True
    assert release['canonical_run']=='canonical-owned-20261113T181617598'
    state=json.loads((ROOT/'output'/release['canonical_run']/'state.json').read_bytes())
    assert state['status']in ('passed','failed','runner_error')and state.get('finished_utc')
    assert release['source_commit']==state['source_commit']==PIN
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];kernel.WaitForSingleObject.restype=ctypes.c_ulong
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x100000,False,int(state['pid']))
    if handle:
        try:assert kernel.WaitForSingleObject(handle,0)==0,'Original coordinator PID is live; refuse graphics (including possible PID reuse)'
        finally:kernel.CloseHandle(handle)
    else:assert ctypes.get_last_error()==87,'Coordinator inspection failed; no visible fallback'
    return stamp(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--overlay',type=Path,required=True);p.add_argument('--run',action='store_true');p.add_argument('--lease-release',type=Path);a=p.parse_args()
    assert os.name=='nt'and Path(sys.executable).resolve()==PYTHON
    assert git('rev-parse','HEAD').decode().strip()==PIN
    assert sha(GODOT)=='63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
    assert sha(PYTHON)=='03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
    assert sha(PYTHONW)=='2bea4fc941b7d9436afa1be8cb46551c0694deed23b3fec87b969054238be099'
    overlay=safe(a.overlay);assert overlay.is_dir()
    if a.run:assert a.lease_release is not None;release=lease_free(a.lease_release)
    else:release=None
    names=git('ls-files','src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw').decode().splitlines()
    protected=[stamp(ROOT/n)for n in names if(ROOT/n).is_file()and not n.endswith('.pyc')and '__pycache__'not in Path(n).parts]+[stamp(PYTHON),stamp(PYTHONW),stamp(GODOT)]
    overlays=[stamp(x)for x in sorted(overlay.rglob('*'))if x.is_file()]
    harness=[stamp(x)for x in sorted(Path(__file__).parent.rglob('*'))if x.is_file()and '__pycache__'not in x.parts]
    folder=safe(TASK/'gpu-runs'/(str(time.time_ns())+'-'+uuid.uuid4().hex[:8]));folder.mkdir(parents=True)
    studio=folder/'Studio';studio.mkdir()
    archive=git('archive','--format=tar',PIN,'src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw')
    with tarfile.open(fileobj=io.BytesIO(archive))as tar:
        for member in tar.getmembers():
            path=Path(member.name)
            assert not path.is_absolute()and '..'not in path.parts
            if not member.isfile()or path.suffix=='.pyc'or '__pycache__'in path.parts:continue
            target=studio/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tar.extractfile(member).read())
    for rec in overlays:
        src=Path(rec['path']);target=studio/src.relative_to(overlay);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    script=Path(__file__).with_name('helper_preview_gpu.gd');assert script.is_file()
    shutil.copy2(script,studio/'tests/helper_preview_gpu.gd')
    profile='HAS-helper-wind-GPU-'+folder.name
    (studio/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="'+profile+'"\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('owned_fixture',studio/'tests/test_secondary_helpers.py');factory=importlib.util.module_from_spec(spec);sys.path.insert(0,str(studio/'tools'));spec.loader.exec_module(factory)
    source=folder/'two-panels.glb';factory.two_panel_fixture(source,'v1');protected.append(stamp(source))
    config=dict(folder=str(folder),project_root=str(studio),source=str(source),python=str(PYTHON),profile=profile,mode='pending_helper_gpu')
    write(folder/'config.json',config)
    runtime=[stamp(x)for x in sorted(studio.rglob('*'))if x.is_file()]
    before=dict(main=protected,overlay=overlays,harness=harness,runtime=runtime,lease_release=release)
    write(folder/'preservation-before.json',before)
    if not a.run:
        cmd=[str(GODOT),'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(folder/'parse-engine.log'),'--script','res://tests/helper_preview_gpu.gd','--check-only']
        write(folder/'parse-command.json',cmd)
        child=subprocess.Popen(cmd,cwd=studio,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out=False
        try:out,err=child.communicate(timeout=40)
        except subprocess.TimeoutExpired:timed_out=True;child.kill();out,err=child.communicate()
        (folder/'parse-stdout.log').write_text(out,encoding='utf-8');(folder/'parse-stderr.log').write_text(err,encoding='utf-8')
        preservation={k:unchanged(before[k])for k in ['main','overlay','harness','runtime']}
        passed=not timed_out and child.returncode==0 and not any(v in out+err for v in ['ERROR:','WARNING:','SCRIPT ERROR','ObjectDB instances leaked'])and all(preservation.values())
        status='PREPARED_PARSE_PASS_GPU_UNRUN'if passed else'FAILED_PARSE_GPU_UNRUN'
        write(folder/'execution.json',dict(status=status,head=PIN,parse_exit=child.returncode,timed_out=timed_out,preservation=preservation))
        print(json.dumps({'folder':str(folder),'status':status}));print(out+err);return 0 if passed else 1
    env=os.environ.copy();env.update(HYBRID_PYTHON=str(PYTHON),HYBRID_GODOT=str(GODOT),PYTHONDONTWRITEBYTECODE='1')
    os.environ.update({k:env[k]for k in ['HYBRID_PYTHON','HYBRID_GODOT','PYTHONDONTWRITEBYTECODE']})
    spec=importlib.util.spec_from_file_location('private_run',studio/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    cmd=runner.command('tests/helper_preview_gpu.gd',False,extra=['--audio-driver','Dummy','--',str(folder/'config.json')])
    assert Path(cmd[0]).resolve()==PYTHONW.resolve()and sha(PYTHONW)=='2bea4fc941b7d9436afa1be8cb46551c0694deed23b3fec87b969054238be099'
    write(folder/'command.json',cmd)
    child=subprocess.Popen(cmd,cwd=studio,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
    write(folder/'launch.json',dict(pid=child.pid,started_ns=time.time_ns(),private_desktop_launcher=True))
    timeout=False
    try:out,err=child.communicate(timeout=480)
    except subprocess.TimeoutExpired:timeout=True;child.kill();out,err=child.communicate()
    (folder/'stdout.log').write_text(out,encoding='utf-8');(folder/'stderr.log').write_text(err,encoding='utf-8')
    receipts=[json.loads(x.read_bytes())for x in (studio/'output/private-desktop').glob('*.json')]
    clean=len(receipts)==1 and all(r.get('exit')==0 and r.get('job_closed')is True and r.get('desktop_closed')is True and r.get('child_desktop_confirmed')is True and r.get('private_window_seen')is True and r.get('foreground_child_observed')is False and r.get('desktop_switch_requested')is False for r in receipts)
    result=json.loads((folder/'result.json').read_bytes())if(folder/'result.json').exists()else None
    forbidden=[v for v in ['ERROR:','WARNING:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','resources still in use','Orphan StringName:']if v in out+err]
    preservation={k:unchanged(before[k])for k in ['main','overlay','harness','runtime']};preservation['head']=git('rev-parse','HEAD').decode().strip()==PIN
    passed=not timeout and child.returncode==0 and clean and result is not None and result['failures']==0 and not forbidden and all(preservation.values())
    write(folder/'execution.json',dict(passed=passed,exit=child.returncode,timed_out=timeout,private_receipts=receipts,clean_private_receipt=clean,preservation=preservation,forbidden=forbidden,checks=result['checks']if result else None))
    print(json.dumps({'folder':str(folder),'passed':passed,'checks':result['checks']if result else None,'forbidden':forbidden,'preservation':preservation}),flush=True);print((out+err)[-5000:],flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
