"""Root-only import-information CPU/UI/packed-cold qualification; SOURCE ONLY, UNRUN.
No job starts until actual completed successful c315 Full evidence qualifies.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse,hashlib,importlib.util,json,os,re,stat,sys,time,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
Q_PIN=(21967,'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
S_PIN=(17881,'e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3')
INPUT_PIN=(4528,'f2916b068bf67996e9826047a6826dfd13e452e7d4225135def5974386ed93ab')
OFFLINE_PIN=(22293,'8890b6ce7ace4bc05adee05c575c021d1c906e3375f5736ae4367f44c50dbeb5')
COPY_NAMES=('Import info.has','expected.json')

def identity(info):
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,
            info.st_mode,getattr(info,'st_file_attributes',0))

def source_module(name,path,pin):
    for part in reversed((path,*path.parents)):
        info=part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:raise RuntimeError('SOURCE_HELPER_ALIAS')
    before=path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size!=pin[0]:raise RuntimeError('SOURCE_HELPER_REGULAR_PIN')
    raw=path.read_bytes()
    if identity(before)!=identity(path.lstat()) or len(raw)!=pin[0] or hashlib.sha256(raw).hexdigest()!=pin[1]:raise RuntimeError('SOURCE_HELPER_IDENTITY_OR_BYTES')
    spec=importlib.util.spec_from_loader(name,loader=None);module=importlib.util.module_from_spec(spec)
    module.__file__=str(path);sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__);return module

def variants():
    return [{'name':t+'-'+str(s)+'-'+w,'theme':t,'scale':s,'workspace':w}
            for t in ('classic','neon') for s in (100,150) for w in ('simple','advanced')]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('self-sha256','source-pins-sha256','expected-head','full-completion-sha256','full-source-sha256','full-report-sha256','full-outer-launch-sha256','full-outer-completion-sha256'):ap.add_argument('--'+key,required=True)
    ap.add_argument('--full-folder',type=Path,required=True);ap.add_argument('--full-outer-folder',type=Path,required=True)
    ap.add_argument('--root-exclusive-lane-confirmed',action='store_true',required=True);ap.add_argument('--cpu-only',action='store_true');o=ap.parse_args()
    Q=source_module('_import_info_Q',HERE/'qualified_ui_host.py',Q_PIN)
    H,_=Q.load_pinned('_import_info_H',HERE/'qualified_helpers.py',*Q.HELPER_PIN)
    P=source_module('_import_info_offline',HERE/'offline_reader_helpers.py',OFFLINE_PIN)
    H.need(H.ROOT==ROOT and os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize and o.root_exclusive_lane_confirmed,'ROOT_WINDOWS313_SCOPE')
    H.need(o.expected_head==BASE and H.head()==BASE,'EXACT_C315_HEAD')
    for value in (o.self_sha256,o.source_pins_sha256):H.need(re.fullmatch('[a-f0-9]{64}',value) is not None,'EXPLICIT_SOURCE_PINS')
    H.read(Path(__file__),digest=o.self_sha256)
    manifest=H.parse(H.read(HERE/'SOURCE_PINS.json',digest=o.source_pins_sha256,limit=2*1024*1024));admitted=set()
    H.need(manifest.get('format')=='has_import_capability_c315_source_pins_1' and manifest.get('revision')==BASE,'SOURCE_PACKET_FORMAT')
    for row in manifest['files']:
        name=H.rel(row['path']);H.need(name.casefold() not in admitted,'SOURCE_PACKET_CASE_ALIAS');admitted.add(name.casefold());H.read(HERE/name,row['bytes'],row['sha256'])
    actual=set()
    for folder,dirs,files in os.walk(HERE,followlinks=False):
        for n in dirs:H.safe(Path(folder)/n)
        for n in files:
            path=H.safe(Path(folder)/n);name=path.relative_to(HERE).as_posix().casefold();H.need(name not in actual,'ACTUAL_PACKET_CASE_ALIAS');actual.add(name)
    H.need(actual==admitted|{'source_pins.json'},'EXACT_FROZEN_PACKET_FILES')
    inputs=H.parse(H.read(HERE/'INPUT_PINS.json',*INPUT_PIN));H.need(inputs['revision']==BASE and len(inputs['targets'])==8,'EXACT_EIGHT_TARGETS')
    for row in inputs['files']:H.read(HERE/H.rel(row['path']),row['bytes'],row['sha256'])
    S,_=Q.load_pinned('_import_info_source',HERE/'source1103.py',*S_PIN)
    expected=S.admit_full(H,ROOT,HERE,o.full_folder,o.full_completion_sha256,o.full_source_sha256,o.full_report_sha256,o.full_outer_folder,o.full_outer_launch_sha256,o.full_outer_completion_sha256)
    frozen=S.immutable_runtime(H,Q,ROOT,expected);base_count=len(frozen);modified=set();added=set()
    for row in inputs['targets']:
        name=H.rel(row['path']);(modified if name in frozen else added).add(name)
        if name in frozen:H.need((len(frozen[name]),H.sha(frozen[name]))==(row['base_bytes'],row['base_sha256']),'TARGET_BASE_CHANGED')
        frozen[name]=H.read(HERE/'payload'/name,row['bytes'],row['sha256'])
    H.need(modified=={'src/pose_editor.gd','src/world_selection.gd','src/source_import.gd'} and added=={'src/import_capability_summary.gd','src/import_capability_editor.gd','tests/import_capability_summary_unit.gd','tests/import_capability_app_headless.gd','tests/import_capability_gui_smoke.gd'} and len(frozen)==base_count+5,'ONLY_REQUIRED_IMPORT_INFO_OVERLAY')
    patch=H.parse(H.read(HERE/'PATCHES.json'))
    for name in modified:
        text=H.read(ROOT/name,expected[name]['bytes'],expected[name]['sha256']).decode()
        for row in patch['patches']:
            if row['path']==name:H.need(text.count(row['before'])==1,'UNIQUE_LITERAL_ANCHOR');text=text.replace(row['before'],row['after'])
        H.need(text.encode()==frozen[name],'EXACT_LITERAL_PORT')
    lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));runtime=lock['runtime_paths']
    H.need(len(lock['runtime_executables'])==6,'SIX_APPROVED_RUNTIMES')
    for path,row in lock['runtime_executables'].items():H.read(path,row['bytes'],row['sha256'],limit=1024*1024*1024);H.need(Path(path).lstat().st_mtime_ns==row['mtime_ns'],'APPROVED_RUNTIME_STAMP')
    H.need(Path(sys.executable).resolve()==Path(runtime['python']).resolve(),'APPROVED_PYTHON')
    stage=ROOT.parent/('has-import-info-c315-'+str(time.time_ns()));H.safe(stage,missing=True)
    lane=ROOT/'output/import-capability-c315-qualification.lock';fd=None;stamp=None;token=uuid.uuid4().hex.encode();owned=False;primary=None;env=dict(os.environ)
    result={'format':'has_import_capability_c315_qualification_1','status':'FAIL','revision':BASE,'functional_baseline':1103,'cpu_only':o.cpu_only,'expected_checks':163 if o.cpu_only else 267,'expected_jobs':6 if o.cpu_only else 22,'cases':[],'jobs':[],'pairs':[],'application_adopted':False,'owner_inputs_used':False,'native_conversion_qualified':False,'all49_physics_qualified':False,'Source_shader_qualified':False,'new_Full_claimed':False,'Full_completion_sha256':o.full_completion_sha256,'source_manifest_sha256':o.source_pins_sha256}
    try:
        H.safe(lane,missing=True);fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR);H.need(os.write(fd,token)==len(token),'LOCK_SHORT_WRITE');os.fsync(fd);stamp=H.stamp(os.fstat(fd))
        stage.mkdir();owned=True;(stage/'Verification').mkdir();cpu=P.build_studio(H,stage,'CPUStudio',frozen)
        H.json_new(stage/'SOURCE_SNAPSHOT.json',{'revision':BASE,'runtime_files':{n:{'bytes':len(b),'sha256':H.sha(b)} for n,b in frozen.items()}})
        Q.run_case(H,stage,cpu,runtime,result,'import',None,[],None,0,graphical=False,timeout=90)
        Q.run_case(H,stage,cpu,runtime,result,'legacy43','tests/import_capability_summary_unit.gd',[],'IMPORT_CAPABILITY_SUMMARY ',43,graphical=False,timeout=40)
        for variant in [v for v in variants() if v['scale']==100]:
            data=stage/('CPUData-'+variant['name']);data.mkdir();flags=(['--classic'] if variant['theme']=='classic' else [])+(['--advanced'] if variant['workspace']=='advanced' else [])
            Q.run_case(H,stage,cpu,runtime,result,'app-'+variant['name'],'tests/import_capability_app_headless.gd',[data,*flags],'IMPORT_CAPABILITY_APP ',30,graphical=False,timeout=100)
        H.need(P.closure(H,result),'HEADLESS_CLOSURE_BEFORE_GUI')
        if not o.cpu_only:
            pairs=stage/'Pairs';pairs.mkdir()
            for variant in variants():
                name=variant['name'];folder=pairs/name;folder.mkdir();writer=P.build_studio(H,folder,'WriterStudio',frozen);reader=P.build_studio(H,folder,'ReaderStudio',frozen)
                wd=folder/'WriterData';rd=folder/'ReaderData';wd.mkdir();rd.mkdir()
                flags=(['--classic'] if variant['theme']=='classic' else [])+(['--150'] if variant['scale']==150 else [])+(['--advanced'] if variant['workspace']=='advanced' else [])
                writer_name='writer-'+name
                Q.run_case(H,stage,writer,runtime,result,writer_name,'tests/import_capability_gui_smoke.gd',[wd,*flags],'IMPORT_CAPABILITY_GUI ',7,graphical=True,timeout=150)
                H.need(P.closure(H,result),'WRITER_CLOSED_BEFORE_COLD')
                copied=[]
                for leaf in COPY_NAMES:
                    raw=H.read(wd/leaf,limit=128*1024*1024);H.new(rd/leaf,raw);copied.append({'name':leaf,'bytes':len(raw),'sha256':H.sha(raw)})
                H.need({path.name for path in rd.iterdir()}==set(COPY_NAMES),'EXACT_TWO_FILE_HANDOFF')
                row={'name':name,'writer_trees_offline_during_reader':False,'writer_tree_restoration_complete':False,'copied':copied};result['pairs'].append(row)
                with P.offline_trees(H,stage,(writer,wd,stage/'UserData'/writer_name),row):
                    Q.run_case(H,stage,reader,runtime,result,'reader-'+name,'tests/import_capability_gui_smoke.gd',[rd,'--read',*flags],'IMPORT_CAPABILITY_GUI_READ ',6,graphical=True,timeout=150)
                    H.need(P.closure(H,result),'READER_CLOSED_BEFORE_RESTORE')
                    for item in copied:H.read(rd/item['name'],item['bytes'],item['sha256'],limit=128*1024*1024)
                H.need(row['writer_tree_restoration_complete'] is True,'WRITER_RESTORATION_REQUIRED')
        result['checks']=sum(row.get('checks',0) for row in result['cases'])
        H.need(result['checks']==result['expected_checks'] and len(result['jobs'])==len(result['cases'])==result['expected_jobs'] and len(result['pairs'])==(0 if o.cpu_only else 8),'EXACT_QUALIFICATION_COUNTS')
        result['status']='PASS'
    except BaseException as error:primary=error;result['error_type']=type(error).__name__;result['error_code']=str(error) if isinstance(error,H.Refusal) else 'IMPORT_INFO_QUALIFICATION_EXCEPTION'
    finally:
        for process,row in H.OWNED:row['reaped']=H.reap(process)
        result['all_jobs_closed']=P.closure(H,result);result['writer_trees_restored']=not P.HIDDEN;result['environment_preserved']=dict(os.environ)==env
        result['preservation_failures']=H.preserve();result['all_inputs_preserved']=not result['preservation_failures']
        try:result['Main_preserved']=H.head()==BASE and S.domain(H,ROOT)==set(expected)
        except BaseException:result['Main_preserved']=False
        clean=all(result[k] is True for k in ('all_jobs_closed','writer_trees_restored','environment_preserved','all_inputs_preserved','Main_preserved'));result['owned_lock_removed']=False
        if fd is not None:
            try:
                H.need(clean and H.stamp(os.fstat(fd))==stamp and H.stamp(lane.lstat())==stamp,'OWNED_LOCK_RETAINED');os.lseek(fd,0,os.SEEK_SET);H.need(os.read(fd,128)==token,'LOCK_TOKEN_CHANGED');os.close(fd);fd=None;H.need(H.stamp(lane.lstat())==stamp,'LOCK_PATH_CHANGED');lane.unlink();result['owned_lock_removed']=True
            except BaseException as error:result['lock_error_type']=type(error).__name__
            finally:
                if fd is not None:os.close(fd)
        if not(clean and result['owned_lock_removed']):result['status']='FAIL'
        if owned:
            H.json_new(stage/'PRIVATE_RESULT.json',result);public={k:v for k,v in result.items() if k not in ('jobs','preservation_failures')};public['private_job_count']=len(result['jobs']);public['preservation_failure_count']=len(result['preservation_failures']);H.json_new(stage/'PUBLIC_RESULT.json',public);print(json.dumps({'status':result['status'],'checks':result.get('checks',0),'result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if primary is None and result['status']=='PASS' else 1
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status':'PREFLIGHT_REFUSED','type':type(error).__name__,'detail':str(error)}),flush=True);raise SystemExit(2)
