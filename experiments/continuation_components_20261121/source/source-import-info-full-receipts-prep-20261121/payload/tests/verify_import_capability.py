"""Ordinary current-source Import info controls:163 CPU +104 private GUI/cold.
No prior Full, experimental coordinator, native assets or converter is required.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse,hashlib,importlib.util,json,os,re,stat,subprocess,sys,time,uuid
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from verify_camera_interactions import need,identity,source_inputs,sources_unchanged
BAD=re.compile(r'SCRIPT ERROR|SHADER ERROR|FAIL |ObjectDB instances leaked|_set_transient_exclusive_child|^ERROR:',re.M)
COPY_NAMES=('Import info.has','expected.json')
MAX_LOG=8*1024*1024
STUDIOS=[]

def safe(path,missing=False):
    path=Path(os.path.abspath(path))
    for part in reversed((path,*path.parents)):
        if missing and not os.path.lexists(part):continue
        s=part.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Alias path refused')
    return path

def read(path,limit=128*1024*1024):
    path=safe(path);before=path.lstat();need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'Bounded single-link file required')
    data=path.read_bytes();need(identity(before)==identity(path.lstat()),'File changed during read');return data

def new(path,data):
    safe(path,missing=True)
    with path.open('xb') as f:f.write(data)

def inventory(folder):
    rows={};dirs={'.':identity(safe(folder).lstat())};seen=set();total=0
    def error(e):raise e
    for here,names,files in os.walk(folder,followlinks=False,onerror=error):
        for leaf in names+files:
            p=safe(Path(here)/leaf);name=p.relative_to(folder).as_posix();need(name.casefold() not in seen,'Tree case alias');seen.add(name.casefold())
            if leaf in names:dirs[name]=identity(p.lstat())
        need(len(seen)<=20000,'Tree entry bound')
        for leaf in files:
            p=Path(here)/leaf;data=read(p,512*1024*1024);total+=len(data);need(total<=2*1024*1024*1024,'Tree byte bound');rows[p.relative_to(folder).as_posix()]={'identity':identity(p.lstat()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    return {'files':rows,'directories':dirs}

def source_blobs():
    frozen=source_inputs()
    extra=[ROOT/'launch.pyw',ROOT/'THIRD_PARTY_NOTICES.md',ROOT/'docs/licenses.md']
    for path in (ROOT/'web').rglob('*'):
        safe(path)
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.pyo'):extra.append(path)
    for path in extra:
        data=read(path);frozen[path]=(identity(path.lstat()),hashlib.sha256(data).hexdigest())
    blobs={}
    for path,(stamp,digest) in frozen.items():
        data=read(path);need(identity(path.lstat())==stamp and hashlib.sha256(data).hexdigest()==digest,'Source admission changed');blobs[path.relative_to(ROOT).as_posix()]=data
    need(len(blobs)==len({n.casefold() for n in blobs}),'Source case alias')
    return frozen,blobs

def studio(parent,name,blobs):
    target=parent/name;target.mkdir(exist_ok=False)
    for relative,data in blobs.items():
        destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True);new(destination,data)
    STUDIOS.append(target);return target

def module_run(folder):
    path=folder/'run.py';raw=read(path);name='_import_info_run_'+uuid.uuid4().hex
    m=importlib.util.module_from_spec(importlib.util.spec_from_loader(name,loader=None));m.__file__=str(path);sys.modules[name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);need(m.ROOT==folder,'Copied launcher Root differs');return m

def private_receipt_closed(proof,launcher_exit,headless,child_command):
    # The pinned helper requires observed private windows only for graphical jobs.
    # Headless has no HWND: retain full lifecycle proof without inventing placement.
    if not isinstance(proof,dict) or type(headless) is not bool or type(launcher_exit) is not int:return False
    if not isinstance(child_command,(list,tuple)) or not child_command or any(type(v) is not str for v in child_command):return False
    engine_args=child_command[:child_command.index('--')] if '--' in child_command else child_command
    if ('--headless' in engine_args)!=headless:return False
    if proof.get('format')!='studio_private_desktop_1' or type(proof.get('exit')) is not int or proof['exit']!=launcher_exit:return False
    if not re.fullmatch(r'HAS_Test_[0-9a-f]{32}',str(proof.get('desktop',''))):return False
    if type(proof.get('child_pid')) is not int or proof['child_pid']<=0:return False
    if type(proof.get('job_memory_limit_bytes')) is not int or proof['job_memory_limit_bytes']!=4096*1024*1024:return False
    if any(proof.get(k) is not True for k in ('job_closed','desktop_closed')):return False
    if any(proof.get(k) is not False for k in ('foreground_child_observed','desktop_switch_requested')):return False
    if any(k in proof for k in ('error','monitor_error','desktop_enumeration_error','cancelled')):return False
    if type(proof.get('child_desktop_confirmed')) is not bool or type(proof.get('private_window_seen')) is not bool:return False
    windows=proof.get('maximum_owned_windows')
    if type(windows) is not int or windows<0:return False
    if headless:return proof['private_window_seen'] is False and windows==0
    return proof['child_desktop_confirmed'] is True and proof['private_window_seen'] is True and windows>0

def run_case(root,case_name,app_root,script,marker,count,flags,headless,result,display,prepared_data=None):
    case=root/'Cases'/case_name;case.mkdir();data=Path(prepared_data) if prepared_data is not None else case/'Data'
    if prepared_data is None:data.mkdir()
    else:need(data.is_relative_to(root) and data.is_dir() and {p.name for p in data.iterdir()}==set(COPY_NAMES),"Exact fresh reader handoff required")
    user=case/'User'
    for leaf in ('Roaming','Local','Temp'):(user/leaf).mkdir(parents=True)
    env=dict(os.environ)
    for key in tuple(env):
        if (key.startswith('HYBRID_') and key not in ('HYBRID_PYTHON','HYBRID_GODOT','HYBRID_FFMPEG')) or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX','PYTHONOPTIMIZE'):env.pop(key,None)
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',APPDATA=str(user/'Roaming'),LOCALAPPDATA=str(user/'Local'),TEMP=str(user/'Temp'),TMP=str(user/'Temp'))
    m=module_run(app_root)
    if os.name!='nt':
        need(bool(display),'A private isolated display is required; no shared fallback')
        old={k:os.environ.get(k) for k in ('DISPLAY','WAYLAND_DISPLAY','XDG_RUNTIME_DIR')}
        try:
            m.configure_private_display(display)
            for k in old:env[k]=os.environ[k]
            args=m.command(script,headless=headless,extra=['--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(data),*flags])
        finally:
            for k,v in old.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v
    else:
        args=m.command(script,headless=headless,extra=['--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(data),*flags])
        if '--receipt' not in args:
            # Headless scripts also get the ordinary owned Windows Job boundary.
            pythonw=Path(sys.executable).with_name('pythonw.exe');need(pythonw.is_file(),'Existing Pythonw required')
            receipt=case/'private-receipt.json';args=[str(pythonw),str(app_root/'tools/private_desktop.py'),'--receipt',str(receipt),'--',*args]
        args[2:2]=['--timeout','150','--memory-limit-mib','4096']
    row={'name':case_name,'engine_command':args[args.index('--')+1:] if os.name=='nt' else list(args),'headless':headless,'expected_checks':count,'status':'FAIL','launcher_reaped':False,'private_resources_closed':False}
    result['cases'].append(row);process=None;primary=None
    try:
        with (case/'stdout.log').open('xb') as out,(case/'stderr.log').open('xb') as err:
            process=subprocess.Popen(args,cwd=app_root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            row['launcher_pid']=process.pid;deadline=time.monotonic()+185
            while process.poll() is None:
                need(time.monotonic()<deadline,'Owned Import info timeout')
                need(os.fstat(out.fileno()).st_size<=MAX_LOG and os.fstat(err.fileno()).st_size<=MAX_LOG,'Owned log budget');time.sleep(.02)
            row['launcher_exit']=process.wait(timeout=1);row['launcher_reaped']=True
    except BaseException as error:primary=error
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
            row['launcher_reaped']=process.poll() is not None;row['launcher_exit']=process.returncode
            if os.name=='nt' and row['launcher_reaped']:process._handle.Close();row['launcher_handle_closed']=True
        if os.name=='nt' and '--receipt' in args:
            rp=Path(args[args.index('--receipt')+1])
            if rp.is_file():
                proof_raw=read(rp);proof=json.loads(proof_raw);row['private_receipt']=str(rp);row['private_receipt_sha256']=hashlib.sha256(proof_raw).hexdigest();row['private_child_pid']=proof.get('child_pid')
                child_command=args[args.index('--')+1:]
                row['private_resources_closed']=private_receipt_closed(proof,row['launcher_exit'],headless,child_command)
                row['private_receipt_mode']='headless_lifecycle_only' if headless else 'graphical_private_window'
                row['graphical_placement_proven']=not headless and row['private_resources_closed']
                need(row['private_resources_closed'],'Private Job/window closure proof failed')
        else:row['private_resources_closed']=row['launcher_reaped']
    need(row['launcher_reaped'] and row['private_resources_closed'],'Unproven owned process closure; stop')
    if primary is not None:raise primary
    text=read(case/'stdout.log',MAX_LOG).decode('utf-8','replace');error=read(case/'stderr.log',MAX_LOG).decode('utf-8','replace');engine=read(case/'engine.log',MAX_LOG).decode('utf-8','replace')
    need(row['launcher_exit']==0 and not BAD.search(text+'\n'+error+'\n'+engine),'Import info case assertion/engine error')
    hits=[line[len(marker):] for line in text.splitlines() if line.startswith(marker)];need(len(hits)==1,'One exact result marker required');value=json.loads(hits[0])
    need(type(value.get('checks')) is int and value['checks']==count and type(value.get('failures')) is int and value['failures']==0 and sum(line.startswith('PASS ') for line in text.splitlines())==count,'Exact Import info checks required')
    need(type(value.get('user_profile')) is str and bool(value['user_profile']),'Actual user profile required')
    if os.name=='nt':need(Path(value['user_profile']).is_relative_to(user/'Roaming'),'Actual unique per-case profile required')
    row.update(status='PASS',checks=count,report=value,data=str(data),user=str(user));return row

@contextmanager
def writer_offline(root,paths,state):
    moved=[]
    try:
        for source in paths:
            source=safe(source);need(source.is_relative_to(root) and source!=root,'Only new owned test trees may go offline');dest=source.with_name(source.name+'.OFFLINE');need(not os.path.lexists(dest),'Fresh offline target required');seal=inventory(source);os.rename(source,dest);moved.append((source,dest,seal));need(not source.exists(),'Writer source still available')
        state['writer_offline']=True;yield
    finally:
        failures=[]
        for source,dest,seal in reversed(moved):
            try:
                safe(dest);need(not os.path.lexists(source),'Writer source unexpectedly recreated');os.rename(dest,source);need(inventory(source)==seal,'Writer tree changed while offline')
            except BaseException as error:failures.append(type(error).__name__)
        state['writer_restored']=not failures;need(not failures,'Owned writer restoration failed')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scope',choices=('cpu','gui','all'),default='all');p.add_argument('--output',type=Path);p.add_argument('--isolated-display');o=p.parse_args()
    if os.name!='nt' and not o.isolated_display:p.error('Supply an explicitly private --isolated-display')
    root=(o.output or ROOT/'output/import-capability'/str(time.time_ns())).resolve();need(root.is_relative_to((ROOT/'output').resolve()) and not root.exists(),'Use a new output directory');safe(root,missing=True)
    root.mkdir(parents=True);(root/'Cases').mkdir();frozen,blobs=source_blobs();environment=dict(os.environ)
    result={'format':'has_current_import_capability_verification_1','report_path':str(root/'verification.json'),'status':'FAIL','scope':o.scope,'cases':[],'pairs':[],'checks':0,'whole_full_claimed':False,'native_or_owner_assets_read':False,'sourceio_or_conversion_requested':False,'experimental_coordinator_used':False,'prior_Full_required':False}
    primary=None
    try:
        if o.scope in ('cpu','all'):
            cpu=studio(root,'CPUStudio',blobs)
            run_case(root,'legacy43',cpu,'tests/import_capability_summary_unit.gd','IMPORT_CAPABILITY_SUMMARY ',43,[],True,result,o.isolated_display)
            for theme in ('classic','neon'):
                for mode in ('simple','advanced'):
                    flags=(['--classic'] if theme=='classic' else [])+(['--advanced'] if mode=='advanced' else [])
                    run_case(root,'app-'+theme+'-'+mode,cpu,'tests/import_capability_app_headless.gd','IMPORT_CAPABILITY_APP ',30,flags,True,result,o.isolated_display)
        if o.scope in ('gui','all'):
            for theme in ('classic','neon'):
                for scale in (100,150):
                    for mode in ('simple','advanced'):
                        name=theme+'-'+str(scale)+'-'+mode;pair=root/name;pair.mkdir();writer=studio(pair,'WriterStudio',blobs);reader=studio(pair,'ReaderStudio',blobs)
                        flags=(['--classic'] if theme=='classic' else [])+(['--150'] if scale==150 else [])+(['--advanced'] if mode=='advanced' else [])
                        w=run_case(root,'writer-'+name,writer,'tests/import_capability_gui_smoke.gd','IMPORT_CAPABILITY_GUI ',7,flags,False,result,o.isolated_display)
                        rd=pair/'ReaderData';rd.mkdir();copied=[]
                        for leaf in COPY_NAMES:
                            raw=read(Path(w['data'])/leaf);new(rd/leaf,raw);copied.append({'name':leaf,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
                        state={'name':name,'writer_offline':False,'writer_restored':False};result['pairs'].append(state)
                        with writer_offline(root,(writer,Path(w['data']),Path(w['user'])),state):
                            r=run_case(root,'reader-'+name,reader,'tests/import_capability_gui_smoke.gd','IMPORT_CAPABILITY_GUI_READ ',6,['--read',*flags],False,result,o.isolated_display,prepared_data=rd)
                            for row in copied:need(hashlib.sha256(read(rd/row['name'])).hexdigest()==row['sha256'],'Cold input changed')
        result['checks']=sum(row.get('checks',0) for row in result['cases']);need(result['checks']=={'cpu':163,'gui':104,'all':267}[o.scope],'Complete component count required')
        result['status']='PASS'
    except BaseException as error:primary=error;result['error_type']=type(error).__name__;result['error']=str(error)
    finally:
        try:
            current,_unused=source_blobs();result['source_preservation_failures']=sources_unchanged(frozen);result['all_admitted_sources_unchanged']=not result['source_preservation_failures'] and set(current)==set(frozen)
            result['runtime_source_preservation_failures']=[]
            for app_root in STUDIOS:
                for name,data in blobs.items():
                    if read(app_root/name)!=data:result['runtime_source_preservation_failures'].append(str((app_root/name).relative_to(root)))
            result['all_runtime_sources_unchanged']=not result['runtime_source_preservation_failures']
        except BaseException as error:result['all_admitted_sources_unchanged']=False;result['all_runtime_sources_unchanged']=False;result['source_error_type']=type(error).__name__
        result['parent_environment_preserved']=dict(os.environ)==environment
        result['all_private_jobs_and_desktops_closed']=all(row.get('launcher_reaped') is True and row.get('private_resources_closed') is True for row in result['cases'])
        result['all_writer_trees_restored']=all(row.get('writer_restored') is True for row in result['pairs'])
        if not all(result[k] for k in ('all_admitted_sources_unchanged','all_runtime_sources_unchanged','parent_environment_preserved','all_private_jobs_and_desktops_closed','all_writer_trees_restored')):result['status']='FAIL'
        new(root/'verification.json',(json.dumps(result,indent=2)+'\n').encode());print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(root/'verification.json')}))
    if primary is not None:raise primary
    need(result['status']=='PASS','Source/process/restoration preservation failed')
if __name__=='__main__':main()
