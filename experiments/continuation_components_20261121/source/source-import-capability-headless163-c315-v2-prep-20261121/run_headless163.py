"""Root-only independent import-information headless163 controls; SOURCE ONLY, UNRUN.
Explicit separate headless scope; never admits or runs a graphical job.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse,hashlib,importlib.util,json,os,re,stat,sys,time,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
Q_PIN=(21967,'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
S_PIN=(17881,'e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3')

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

BOOT_PINS={"qualified_ui_host.py":[21967,"dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e"],"qualified_helpers.py":[26455,"990c37ddca7b1301613f5efc5a7e5a30ce2723369112ef274ee78d2d4dc34087"],"source1103.py":[17881,"e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3"],"root_native_job.py":[5018,"fe9a9da0b545fbc1c2b21d09e93dd931b52c5a9e4681c5f0d106c3e43d67f34b"],"approved_job_layout.py":[12692,"c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61"],"run_root105.py":[15101,"436e704ea893f1029852ec667bb0c4618a2e095ec339591f99fd5c03339300ad"],"gated_headless_worker.py":[6656,"4955af943d021ba0023d6617f981ece106dfd897bb561a50144377cab0181b69"],"headless_logs.py":[1545,"626dd8561975cbc14d2624e7340f62ce2b3b9f6e28d335a4218f03dd2d98ceb6"]}
CANDIDATE=ROOT/'output/source-import-capability-c315-prep-20261121'

def admit_packet(H,folder,digest,expected_format):
    H.need(re.fullmatch('[a-f0-9]{64}',digest) is not None,'EXTERNAL_SOURCE_PIN')
    manifest=H.parse(H.read(folder/'SOURCE_PINS.json',digest=digest,limit=4*1024*1024));names=set()
    H.need(manifest.get('format')==expected_format and manifest.get('revision')==BASE,'PACKET_FORMAT_AND_BASE')
    for row in manifest['files']:
        name=H.rel(row['path']);H.need(name.casefold() not in names,'MANIFEST_CASE_ALIAS');names.add(name.casefold());H.read(folder/name,row['bytes'],row['sha256'])
    files=set();allpaths=set();entries=0
    def error(value):raise value
    for here,dirs,leaves in os.walk(H.safe(folder),followlinks=False,onerror=error):
        for leaf in dirs+leaves:
            path=H.safe(Path(here)/leaf);name=path.relative_to(folder).as_posix().casefold();entries+=1
            H.need(entries<=10000 and name not in allpaths,'PACKET_BOUND_OR_CASE_ALIAS');allpaths.add(name)
            if leaf in leaves:files.add(name)
    H.need(files==names|{'source_pins.json'},'EXACT_SOURCE_PACKET_MEMBERSHIP');return manifest

def runner_pin(kind,path,row):
    if kind not in ('python','godot') or type(path) is not str or not path:raise ValueError('EXPLICIT_USED_RUNTIME_SCHEMA')
    # The preserved runner recognizes Python by POSIX suffix. Normalize only
    # that copied pathname; executable bytes/stamps still bind the original file.
    return {**row,'path':path.replace(chr(92),'/') if kind=='python' else path}

def current_domain(H):
    names=set(('dependencies.json','launch.pyw','main.tscn','project.godot','run.py'))|set('experiments/reference_body_20261120/'+leaf for leaf in ('receipt_provenance.py','run_full.py','run_scoped.py','stage_legacy_inputs.py','test_receipt_provenance.py','verify_units.py'))
    for prefix in ('src','tests','tools','examples','data'):
        for path in H.safe(ROOT/prefix).rglob('*'):
            path=H.safe(path);info=path.lstat()
            if stat.S_ISDIR(info.st_mode):continue
            H.need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'SPECIAL_MAIN_FUNCTIONAL_PATH')
            if path.suffix=='.pyc' or '__pycache__' in path.parts:continue
            names.add(path.relative_to(ROOT).as_posix())
    H.need(len(names)==len({n.casefold() for n in names})==1103,'EXACT_CANONICAL1103_MAIN_DOMAIN')
    return names

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-sha256',required=True);ap.add_argument('--source-pins-sha256',required=True)
    ap.add_argument('--candidate-source-pins-sha256',required=True);ap.add_argument('--root-headless-only-confirmed',action='store_true',required=True);o=ap.parse_args()
    if os.name!='nt' or sys.version_info[:2]!=(3,13) or sys.flags.optimize or not sys.flags.isolated or not sys.flags.no_site or not o.root_headless_only_confirmed:raise RuntimeError('ROOT_ISOLATED_WINDOWS313_HEADLESS_ONLY')
    modules={name:source_module('_headless163_'+name.replace('.','_'),HERE/name,tuple(pin)) for name,pin in BOOT_PINS.items() if name!='gated_headless_worker.py'}
    H=modules['qualified_helpers.py'];Q=modules['qualified_ui_host.py'];S=modules['source1103.py'];R=modules['run_root105.py'];J=modules['root_native_job.py'];L=modules['approved_job_layout.py'];V=modules['headless_logs.py']
    H.need(H.ROOT==ROOT and H.head()==BASE,'EXACT_CURRENT_C315_ROOT')
    H.need(re.fullmatch('[a-f0-9]{64}',o.self_sha256) is not None,'SELF_PIN');H.read(Path(__file__),digest=o.self_sha256)
    admit_packet(H,HERE,o.source_pins_sha256,'has_import_capability_headless163_source_pins_1')
    admit_packet(H,CANDIDATE,o.candidate_source_pins_sha256,'has_import_capability_c315_source_pins_1')
    for name,pin in BOOT_PINS.items():H.read(HERE/name,*pin)
    baseline=S.admit_main(H,ROOT,HERE);H.need(current_domain(H)==set(baseline),"EXACT_CANONICAL_SOURCE_MEMBERSHIP");frozen=S.immutable_runtime(H,Q,ROOT,baseline);base_count=len(frozen)
    inputs=H.parse(H.read(CANDIDATE/'INPUT_PINS.json',limit=2*1024*1024));H.need(inputs['revision']==BASE and len(inputs['targets'])==8,'EXACT_CANDIDATE_TARGETS')
    modified=set();added=set()
    for row in inputs['targets']:
        name=H.rel(row['path']);(modified if name in frozen else added).add(name)
        if name in frozen:H.need((len(frozen[name]),H.sha(frozen[name]))==(row['base_bytes'],row['base_sha256']),'OVERLAY_BASE_CHANGED')
        frozen[name]=H.read(CANDIDATE/'payload'/name,row['bytes'],row['sha256'])
    H.need(modified=={'src/pose_editor.gd','src/world_selection.gd','src/source_import.gd'} and added=={'src/import_capability_summary.gd','src/import_capability_editor.gd','tests/import_capability_summary_unit.gd','tests/import_capability_app_headless.gd','tests/import_capability_gui_smoke.gd'} and len(frozen)==base_count+5,'EXACT_EIGHT_OVERLAYS')
    patch=H.parse(H.read(CANDIDATE/'PATCHES.json'))
    for name in modified:
        text=H.read(ROOT/name,baseline[name]['bytes'],baseline[name]['sha256']).decode()
        for row in patch['patches']:
            if row['path']==name:H.need(text.count(row['before'])==1,'UNIQUE_C315_ANCHOR');text=text.replace(row['before'],row['after'])
        H.need(text.encode()==frozen[name],'EXACT_LITERAL_OVERLAY_BYTES')
    lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));runtime=lock['runtime_paths'];used=[]
    for key in ('python','godot'):
        path=runtime[key];row=lock['runtime_executables'][path];H.read(path,row['bytes'],row['sha256'],limit=1024*1024*1024);H.need(Path(path).lstat().st_mtime_ns==row['mtime_ns'],'USED_EXECUTABLE_STAMP');used.append(runner_pin(key,path,row))
    H.need(Path(sys.executable).resolve()==Path(runtime['python']).resolve(),'APPROVED_PYTHON')
    stage=ROOT.parent/('has-import-info-headless163-'+str(time.time_ns()));H.safe(stage,missing=True)
    lane=ROOT/'output/import-capability-headless163.lock';token=uuid.uuid4().hex.encode();fd=None;stamp=None;owned=False;primary=None;environment=dict(os.environ)
    result={'format':'has_import_capability_headless163_1','status':'FAIL','revision':BASE,'current_functional_sources':1103,'runtime_base_files':base_count,'runtime_overlay_files':len(frozen),'expected_checks':163,'expected_jobs':5,'checks':0,'jobs':[],'cases':[],'source_manifest_sha256':o.source_pins_sha256,'candidate_manifest_sha256':o.candidate_source_pins_sha256,'Full_claimed':False,'failed_Full_waived':False,'graphical_qualification_claimed':False,'native_inputs_used':False,'owner_assets_used':False,'adopted':False}
    try:
        H.safe(lane,missing=True);fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR);H.need(os.write(fd,token)==len(token),'LOCK_SHORT_WRITE');os.fsync(fd);stamp=H.stamp(os.fstat(fd))
        stage.mkdir(exist_ok=False);owned=True;(stage/'Cases').mkdir()
        specs=[('legacy43','unit','tests/import_capability_summary_unit.gd','IMPORT_CAPABILITY_SUMMARY ',43,[])]
        for theme in ('classic','neon'):
            for mode in ('simple','advanced'):
                specs.append((theme+'-'+mode,'controls','tests/import_capability_app_headless.gd','IMPORT_CAPABILITY_APP ',30,(['--classic'] if theme=='classic' else [])+(['--advanced'] if mode=='advanced' else [])))
        H.need(len(specs)==5 and sum(row[4] for row in specs)==163,'EXACT_HEADLESS_MATRIX')
        H.json_new(stage/'SOURCE_SNAPSHOT.json',{'revision':BASE,'files':{n:{'bytes':len(b),'sha256':H.sha(b)} for n,b in frozen.items()}})
        for case_name,job_name,script,marker,count,flags in specs:
            case=stage/'Cases'/case_name;case.mkdir();studio=case/'Studio';studio.mkdir();data=studio/'output/case';data.mkdir(parents=True)
            for name,blob in frozen.items():target=studio/H.rel(name);target.parent.mkdir(parents=True,exist_ok=True);H.new(target,blob)
            profile='HAS Import Info Headless '+case_name+' '+uuid.uuid4().hex
            H.new(studio/'override.cfg',('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
            user=case/'User'
            for leaf in ('Roaming','Local','Temp'):(user/leaf).mkdir(parents=True)
            env={'APPDATA':str(user/'Roaming'),'LOCALAPPDATA':str(user/'Local'),'TEMP':str(user/'Temp'),'TMP':str(user/'Temp'),'HYBRID_PYTHON':runtime['python'],'HYBRID_GODOT':runtime['godot']}
            command=[runtime['godot'],'--headless','--audio-driver','Dummy','--path',str(studio),'--log-file',str(case/'engine.log'),'--script','res://'+script]
            if job_name!='unit':command+=['--',str(data),*flags]
            H.need(command.count('--headless')==1 and '--editor' not in command and '--import' not in command,'HEADLESS_NO_EDITOR_OR_IMPORT')
            job={'name':job_name,'studio':str(studio),'cwd':str(studio),'args':command,'casefolder':str(data),'profile':profile,'environment_overrides':env,'timeout_seconds':150,'expected_checks':count,'expected_marker':marker}
            H.json_new(case/'HEADLESS_CASE.json',job)
            value=R.run_case(H,V,J,L,job,case,used,result);result['checks']+=value['checks'];result['cases'].append({'name':case_name,'checks':value['checks'],'status':'PASS'})
        H.need(result['checks']==163 and len(result['jobs'])==len(result['cases'])==5,'EXACT_FIVE_JOBS163_CHECKS');result['status']='PASS'
    except BaseException as error:primary=error;result['error_type']=type(error).__name__;result['error']=str(error)
    finally:
        result['all_owned_jobs_closed']=all(all(row.get(k) is True for k in ('wrapper_reaped','wrapper_handle_closed','active_zero_before_close','job_closed')) for row in result['jobs'])
        result['parent_environment_preserved']=dict(os.environ)==environment
        result['preservation_failures']=H.preserve();result['all_admitted_inputs_preserved']=not result['preservation_failures']
        try:result['Main_source_preserved']=H.head()==BASE and current_domain(H)==set(baseline)
        except BaseException:result['Main_source_preserved']=False
        clean=all(result[k] is True for k in ('all_owned_jobs_closed','parent_environment_preserved','all_admitted_inputs_preserved','Main_source_preserved'));result['owned_lock_removed']=False
        if fd is not None:
            try:
                H.need(clean and H.stamp(os.fstat(fd))==stamp and H.stamp(lane.lstat())==stamp,'OWNED_LOCK_RETAINED');os.lseek(fd,0,os.SEEK_SET);H.need(os.read(fd,128)==token,'LOCK_TOKEN_CHANGED');os.close(fd);fd=None;H.need(H.stamp(lane.lstat())==stamp,'LOCK_PATH_CHANGED');lane.unlink();result['owned_lock_removed']=True
            except BaseException as error:result['lock_error_type']=type(error).__name__
            finally:
                if fd is not None:os.close(fd)
        if not(clean and result['owned_lock_removed']):result['status']='FAIL'
        if owned:
            H.json_new(stage/'PRIVATE_RESULT.json',result);public={k:v for k,v in result.items() if k not in ('jobs','preservation_failures')};public['owned_job_count']=len(result['jobs']);public['preservation_failure_count']=len(result['preservation_failures']);H.json_new(stage/'PUBLIC_RESULT.json',public);print(json.dumps({'status':result['status'],'checks':result['checks'],'result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if primary is None and result['status']=='PASS' else 1
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:print(json.dumps({'status':'PREFLIGHT_REFUSED','type':type(error).__name__,'detail':str(error)}),flush=True);raise SystemExit(2)
