"""Trusted Root gate for exactly one pure Python test or owned Junko preparer."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,stat,subprocess,sys,time
from ctypes import wintypes as W
MAX_LOG=16*1024*1024
def need(ok,code):
    if not ok:raise RuntimeError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def regular(path,limit=262144):
    path=Path(path).absolute()
    for p in (path,*path.parents):
        s=p.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'PATH_ALIAS')
    s=path.stat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit,'BOUNDED_FILE')
    raw=path.read_bytes();t=path.stat()
    need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_mode,s.st_nlink)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_mode,t.st_nlink),'READ_DRIFT');return raw
def identity(handle,pid):
    k=C.WinDLL('kernel32',use_last_error=True)
    getid=k.GetProcessId;getid.restype=W.DWORD;getid.argtypes=[W.HANDLE]
    times=k.GetProcessTimes;times.restype=W.BOOL;times.argtypes=[W.HANDLE,*([C.POINTER(W.FILETIME)]*4)]
    v=[W.FILETIME() for _ in range(4)]
    need(getid(handle)==pid and times(handle,*(C.byref(x) for x in v)),'RETAINED_IDENTITY')
    return {'pid':pid,'created_100ns':str((v[0].dwHighDateTime<<32)|v[0].dwLowDateTime)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True);a=p.parse_args()
    need(os.name=='nt' and sys.version_info[:2]==(3,13) and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize,'WINDOWS313_ISOLATED')
    raw=regular(a.request);need(sha(raw)==a.request_sha256,'REQUEST_SHA');r=json.loads(raw)
    need(r.get('format')=='has_junko_stage_a_gated_request_1','REQUEST_FORMAT')
    job=r['job'];cmd=job['command'];out=Path(r['record_dir']);studio=Path(job['studio']);pin=r['python_pin']
    need(out==a.request.parent and out.is_absolute() and out.is_dir(),'REQUEST_OUTPUT')
    need(job['name'] in ('unit45','body') and type(cmd) is list and all(type(x) is str for x in cmd),'JOB_DOMAIN')
    need(cmd[:4]==[pin['path'],'-I','-S','-B'] and Path(sys.executable).resolve()==Path(pin['path']).resolve(),'PYTHON_FLAGS')
    need(job['cwd']==str(studio),'EXACT_OWNED_CWD')
    if job['name']=='unit45':
        need(cmd[4:]==['-m','unittest','discover','-s',str(studio/'tests'),'-p','test_junko*.py','-v'] and job['timeout_seconds']==90,'EXACT_UNIT25_DISCOVERY')
        expected_exit=0
        scripts=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py','tests/test_junko_factory_boundary.py')
    else:
        need(cmd[4]==str(studio/'tools/prepare_junko_part_probe.py') and job['timeout_seconds']==720,'EXACT_BODY_DIAGNOSTIC_PREPARER')
        expected_exit=1
        scripts=('tools/prepare_junko_part_probe.py',)
    need(type(job.get('expected_child_exit'))is int and job['expected_child_exit']==expected_exit,'EXACT_EXPECTED_EXIT_SCOPE')
    exe=regular(pin['path'],512*1024*1024);need(len(exe)==pin['bytes'] and sha(exe)==pin['sha256'],'PYTHON_EXE_PIN')
    need(set(job['script_pins'])==set(scripts),'EXACT_SCRIPT_PIN_MEMBERSHIP')
    script_bytes={}
    for name in scripts:
        script=regular(studio/name,1024*1024);expected=job['script_pins'][name]
        need(len(script)==expected['bytes'] and sha(script)==expected['sha256'],'OWNED_SCRIPT_PIN');script_bytes[name]=script
    receipt={'format':'has_junko_stage_a_worker_1','job':job['name'],'request_sha256':a.request_sha256,'status':'FAIL','gate_accepted':False,'child_launched':False,'child_reaped':False,'child_handle_closed':False,'expected_child_exit':expected_exit}
    child=None
    try:
        line=sys.stdin.buffer.readline(4097)
        need(len(line)<=4096 and line.endswith(b'\n') and line.count(b'\n')==1 and sys.stdin.buffer.read(1)==b'','ONE_START_AND_EOF')
        gate=json.loads(line);own=identity(W.HANDLE(-1),os.getpid())
        need(gate.get('format')=='has_junko_stage_a_START_1' and gate.get('nonce')==r['nonce'] and gate.get('request_sha256')==a.request_sha256 and gate.get('owner')==own,'ASSIGNED_ROOT_GATE')
        need(regular(a.request)==raw and all(regular(studio/name,1024*1024)==b for name,b in script_bytes.items()),'REQUEST_OR_SCRIPT_CHANGED')
        receipt.update(gate_accepted=True,wrapper_identity=own,started_ns=time.time_ns())
        env=dict(os.environ)
        for key in tuple(env):
            if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(key,None)
        env.update(job['environment_overrides']);env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
        with (out/'child-stdout.log').open('xb') as stdout,(out/'child-stderr.log').open('xb') as stderr:
            child=subprocess.Popen(cmd,cwd=job['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
            receipt.update(child_launched=True,child_identity=identity(child._handle,child.pid))
            deadline=time.monotonic()+job['timeout_seconds']
            while child.poll() is None:
                need(time.monotonic()<deadline,'CHILD_TIMEOUT')
                need(os.fstat(stdout.fileno()).st_size<=MAX_LOG and os.fstat(stderr.fileno()).st_size<=MAX_LOG,'CHILD_LOG_BUDGET');time.sleep(.05)
            receipt.update(child_exit=child.wait(timeout=1),child_reaped=True)
        need(receipt['child_exit']==expected_exit,'CHILD_UNEXPECTED_EXIT');receipt['status']='EXPECTED_CHILD_REFUSAL' if expected_exit==1 else 'PASS'
    except BaseException as e:receipt.update(error_type=type(e).__name__,error=str(e))
    finally:
        if child is not None:
            try:
                if child.poll() is None:child.kill();child.wait(timeout=10)
                receipt.update(child_exit=child.returncode,child_reaped=child.returncode is not None)
                if 'child_identity' in receipt:need(identity(child._handle,child.pid)==receipt['child_identity'],'CHILD_IDENTITY_DRIFT')
            except BaseException as e:receipt.update(status='FAIL',cleanup_error=str(e))
            finally:
                if child.returncode is not None:
                    try:child._handle.Close();receipt['child_handle_closed']=True
                    except BaseException as e:receipt.update(status='FAIL',handle_error=str(e))
        if not receipt['child_reaped'] or not receipt['child_handle_closed']:receipt['status']='FAIL'
        receipt['finished_ns']=time.time_ns()
        with (out/'worker-receipt.json').open('xb') as f:f.write((json.dumps(receipt,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
        print(json.dumps({'status':receipt['status'],'job':job['name'],'child_reaped':receipt['child_reaped'],'child_handle_closed':receipt['child_handle_closed']}),flush=True)
    return 0 if receipt['status'] in ('PASS','EXPECTED_CHILD_REFUSAL') else 1
if __name__=='__main__':raise SystemExit(main())
