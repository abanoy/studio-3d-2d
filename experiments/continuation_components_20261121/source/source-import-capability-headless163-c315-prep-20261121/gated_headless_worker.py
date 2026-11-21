"""Trusted gate: no Godot starts until Root assigns this wrapper and sends START."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,stat,subprocess,sys,time
from ctypes import wintypes as W
sys.dont_write_bytecode=True
MAX_LOG=8*1024*1024

def need(ok,label):
    if not ok:raise RuntimeError(label)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(path,limit=262144):
    path=Path(path).absolute()
    for part in reversed((path,*path.parents)):
        s=part.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'REQUEST_PATH_ALIAS')
    before=path.stat();need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'BOUNDED_REQUEST')
    raw=path.read_bytes();after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'REQUEST_CHANGED')
    return raw

def retained_identity(handle,pid):
    kernel=C.WinDLL('kernel32',use_last_error=True)
    getid=kernel.GetProcessId;getid.restype=W.DWORD;getid.argtypes=[W.HANDLE]
    gettimes=kernel.GetProcessTimes;gettimes.restype=W.BOOL;gettimes.argtypes=[W.HANDLE,*([C.POINTER(W.FILETIME)]*4)]
    values=[W.FILETIME() for _ in range(4)]
    need(getid(handle)==pid and gettimes(handle,*(C.byref(v) for v in values)),'RETAINED_PROCESS_IDENTITY')
    return {'pid':pid,'created_100ns':str((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True);parser.add_argument('--request-sha256',required=True)
    args=parser.parse_args();need(os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize and sys.flags.isolated and sys.flags.no_site,'APPROVED_ISOLATED_WINDOWS313')
    raw=regular(args.request);need(sha(raw)==args.request_sha256,'REQUEST_PIN')
    request=json.loads(raw);need(request.get('format')=='has_root_junko_gated_request_1','REQUEST_FORMAT')
    job=request['job'];command=job['args'];output=Path(request['record_dir']).absolute()
    need(output==args.request.parent and output.is_dir(),'OWNED_REQUEST_OUTPUT')
    need(job['name'] in ('unit','controls','reader') and command[0]==request['godot_pin']['path'],'APPROVED_GODOT_COMMAND')
    need(command.count('--headless')==1 and '--script' in command and '--editor' not in command and '--import' not in command,'HEADLESS_SCRIPT_ONLY')
    need(command[command.index('--path')+1]==job['studio'] and job['cwd']==job['studio'],'EXACT_STUDIO')
    need(command[command.index('--script')+1] in ('res://tests/import_capability_summary_unit.gd','res://tests/import_capability_app_headless.gd'),'EXPLICIT_SYNTHETIC_SCRIPT')
    need(type(job['timeout_seconds']) is int and 1<=job['timeout_seconds']<=180,'BOUNDED_HEADLESS_TIMEOUT')
    godot=Path(command[0]);pin=request['godot_pin'];exe=regular(godot,1024*1024*1024)
    need(len(exe)==pin['bytes'] and sha(exe)==pin['sha256'],'GODOT_EXECUTABLE_PIN')
    receipt={'format':'has_root_gated_headless_receipt_1','job':job['name'],'request_sha256':args.request_sha256,
             'gate_accepted':False,'godot_launched':False,'godot_reaped':False,'godot_handle_closed':False,'status':'FAIL'}
    process=None;deadline=0
    try:
        line=sys.stdin.buffer.readline(4097)
        need(len(line)<=4096 and line.endswith(b'\n') and line.count(b'\n')==1 and sys.stdin.buffer.read(1)==b'','ONE_START_FRAME_AND_EOF')
        gate=json.loads(line)
        own=retained_identity(W.HANDLE(-1),os.getpid())
        need(gate.get('format')=='has_root_junko_START_1' and gate.get('request_sha256')==args.request_sha256
             and gate.get('nonce')==request['nonce'] and gate.get('owner')==own,'EXACT_ASSIGNED_WRAPPER_GATE')
        need(regular(args.request)==raw,'REQUEST_CHANGED_BEFORE_START')
        receipt['gate_accepted']=True;receipt['wrapper_identity']=own
        env=dict(os.environ)
        for key in tuple(env):
            if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(key,None)
        env.update(job['environment_overrides']);env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
        receipt['started_ns']=time.time_ns()
        with (output/'godot-stdout.log').open('xb') as out,(output/'godot-stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=job['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                                     close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['godot_launched']=True;receipt['godot_identity']=retained_identity(process._handle,process.pid)
            deadline=time.monotonic()+job['timeout_seconds']
            while process.poll() is None:
                need(time.monotonic()<deadline,'GODOT_TIMEOUT')
                need(os.fstat(out.fileno()).st_size<=MAX_LOG and os.fstat(err.fileno()).st_size<=MAX_LOG,'GODOT_LOG_BUDGET')
                time.sleep(.02)
            receipt['godot_exit']=process.wait(timeout=1);receipt['godot_reaped']=True
        need(receipt['godot_exit']==0,'GODOT_NONZERO')
        receipt['status']='PASS'
    except BaseException as error:
        receipt['error_type']=type(error).__name__;receipt['error']=str(error)
    finally:
        if process is not None:
            try:
                if process.returncode is None:process.kill();process.wait(timeout=5)
                receipt['godot_reaped']=process.returncode is not None
                receipt['godot_exit']=process.returncode
                if 'godot_identity' in receipt:need(retained_identity(process._handle,process.pid)==receipt['godot_identity'],'GODOT_HANDLE_IDENTITY_DRIFT')
            except BaseException as error:
                receipt['cleanup_error_type']=type(error).__name__;receipt['cleanup_error']=str(error);receipt['status']='FAIL'
            finally:
                if receipt['godot_reaped']:
                    try:process._handle.Close();receipt['godot_handle_closed']=True
                    except BaseException as error:receipt['handle_close_error']=str(error);receipt['status']='FAIL'
        receipt['finished_ns']=time.time_ns()
        if not receipt['godot_reaped'] or not receipt['godot_handle_closed']:receipt['status']='FAIL'
        with (output/'wrapper-receipt.json').open('xb') as file:
            file.write((json.dumps(receipt,indent=2)+'\n').encode());file.flush();os.fsync(file.fileno())
        print(json.dumps(receipt),flush=True)
    return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
