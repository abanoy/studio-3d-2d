"""Root-only easing UI/packed-cold/movie qualification; SOURCE ONLY, UNRUN.
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
INPUT_PIN=(5535,'a65216a376df0b3287d7f9ba3bdca5870794efaa0e9b0cbeafec5d38edeca2b7')
HIDDEN=[]
COPY_NAMES=('Unbaked.has','Baked.has','original-keys.var','baked-keys.var','expected.json')

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

def matrix():
    rows=[]
    for theme in ('classic','neon'):
        for scale in (100,150):
            for workspace in ('simple','advanced'):
                movies=(theme,scale,workspace)==('neon',100,'advanced')
                rows.append({'name':theme+'-'+str(scale)+'-'+workspace,'theme':theme,'scale':scale,
                    'workspace':workspace,'movies':movies,'writer_checks':29 if movies else 23,'reader_checks':8})
    return rows

def seal_tree(H,folder):
    folder=H.safe(folder);info=folder.lstat();H.need(stat.S_ISDIR(info.st_mode),'OWNED_TREE_DIRECTORY')
    rows={};directories={'.':H.stamp(info)};seen=set();total=0
    def error(e):raise e
    for here,dirs,names in os.walk(folder,followlinks=False,onerror=error):
        for name in dirs+names:
            p=H.safe(Path(here)/name);relative=p.relative_to(folder).as_posix()
            H.need(relative.casefold() not in seen,'OWNED_TREE_CASE_ALIAS');seen.add(relative.casefold())
            if name in dirs:directories[relative]=H.stamp(p.lstat())
        H.need(len(seen)<=20000,'OWNED_TREE_ENTRY_CAP')
        for name in names:
            p=Path(here)/name;b=H.read(p,limit=512*1024*1024);total+=len(b)
            H.need(total<=2*1024*1024*1024,'OWNED_TREE_BYTE_CAP')
            rows[p.relative_to(folder).as_posix()]={'stamp':H.stamp(p.lstat()),'bytes':len(b),'sha256':H.sha(b)}
    return {'directory_identity':(info.st_dev,info.st_ino),'directories':directories,'files':rows,'bytes':total}

@contextmanager
def offline_trees(H,stage,folders,result):
    """Only rename exact newly-created owned trees; always restore before preserve."""
    moved=[]
    try:
        for folder in folders:
            folder=H.safe(folder);H.need(folder.is_relative_to(stage) and folder!=stage,'OWNED_OFFLINE_BOUNDARY')
            destination=folder.with_name(folder.name+'.OFFLINE')
            H.safe(destination,missing=True);H.need(not destination.exists(),'OFFLINE_TARGET_ALREADY_EXISTS')
            sealed=seal_tree(H,folder);os.rename(folder,destination)
            row={'original':folder,'offline':destination,'seal':sealed};moved.append(row);HIDDEN.append(row)
            H.need(not folder.exists() and destination.lstat().st_ino==sealed['directory_identity'][1],'OFFLINE_RENAME_READBACK')
        result['writer_trees_offline_during_reader']=all(not row['original'].exists() for row in moved)
        H.need(result['writer_trees_offline_during_reader'] is True,'WRITER_TREES_STILL_AVAILABLE')
        yield
    finally:
        failed=[]
        for row in reversed(moved):
            try:
                original,offline=row['original'],H.safe(row['offline'])
                H.need(not original.exists() and (offline.lstat().st_dev,offline.lstat().st_ino)==row['seal']['directory_identity'],'OFFLINE_TREE_IDENTITY_BEFORE_RESTORE')
                os.rename(offline,original)
                H.need(seal_tree(H,original)==row['seal'],'OFFLINE_TREE_CONTENT_OR_IDENTITY_CHANGED')
                HIDDEN.remove(row)
            except BaseException as error:failed.append(type(error).__name__)
        result['writer_tree_restoration_complete']=not failed
        H.need(not failed,'OWNED_OFFLINE_TREE_RESTORE_FAILED')

def build_studio(H,parent,name,frozen):
    studio=parent/name;studio.mkdir()
    for relative,raw in frozen.items():
        target=studio/H.rel(relative);target.parent.mkdir(parents=True,exist_ok=True);H.new(target,raw)
    (studio/'output/private-desktop').mkdir(parents=True)
    H.new(studio/'override.cfg',b'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="HAS Easing Unused Bootstrap"\n')
    H.need(H.sha(H.read(studio/'tools/private_desktop.py'))==H.PRIVATE_SHA,'EXACT_PRIVATE_LAUNCHER')
    return studio

def closure(H,result):
    return (all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
            and all(row.get('reaped') is True for _process,row in H.OWNED))

def copy_reader_inputs(H,writer,reader):
    H.need(not any(reader.iterdir()),'FRESH_EMPTY_READER_DATA')
    pins=[]
    for name in COPY_NAMES:
        source=H.safe(writer/name);raw=H.read(source,limit=128*1024*1024)
        H.new(reader/name,raw)
        pins.append({'name':name,'bytes':len(raw),'sha256':H.sha(raw)})
    # No writer preferences/profile/recovery/cache/.godot data is copied.
    H.need({p.name for p in reader.iterdir()}==set(COPY_NAMES),'ONLY_FIVE_PACKED_READER_INPUTS')
    expected=H.parse(H.read(reader/'expected.json',limit=2*1024*1024))
    H.need(type(expected) is dict and set(expected)=={'original_wire','baked_wire','authored','preview','paint','source'}
           and expected['authored']!=expected['preview'],'MEANINGFUL_PREVIEW_EXPECTED_PIXELS')
    for key in ('authored','preview','paint','source'):
        H.need(type(expected[key]) is str and re.fullmatch('[0-9a-f]{64}',expected[key]) is not None,'EXACT_EXPECTED_PIXEL_AND_SOURCE_HASHES')
    return pins

def movie_probe(H,stage,studio,runtime,result,name,movie):
    """Read-only ffprobe, retained/reaped and hidden; never a graphical job."""
    case=stage/'Verification'/name;case.mkdir();H.read(movie,limit=512*1024*1024)
    args=[runtime['ffprobe'],'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(movie)]
    proc=None;row={'name':name,'reaped':False,'read_only_probe':True};logged=False
    try:
        proc=H.subprocess.Popen(args,cwd=studio,stdout=H.subprocess.PIPE,stderr=H.subprocess.PIPE,
            creationflags=H.subprocess.CREATE_NO_WINDOW)
        H.OWNED.append((proc,row));row['pid']=proc.pid
        stdout,stderr=proc.communicate(timeout=35)
        H.new(case/'stdout.log',stdout);H.new(case/'stderr.log',stderr);logged=True
        H.need(len(stdout)<=2*1024*1024 and len(stderr)<=2*1024*1024 and proc.returncode==0 and not stderr.strip(),'MOVIE_PROBE_FAILED')
        report=H.parse(stdout);streams=report.get('streams');H.need(type(streams) is list and len(streams)==1,'ONE_SILENT_VIDEO_STREAM')
        video=streams[0]
        H.need(video.get('codec_type')=='video' and video.get('codec_name')=='h264'
               and type(video.get('width')) is int and video['width']==1920
               and type(video.get('height')) is int and video['height']==1080
               and video.get('avg_frame_rate')=='24/1' and video.get('nb_read_frames')=='48'
               and float(report['format']['duration'])==2.0,'EXACT_1080P_24FPS_48FRAME_TWO_SECOND_MOVIE')
        result['movies'].append({'name':name,'codec':'h264','width':1920,'height':1080,'frames':48,'fps':'24/1',
              'duration_seconds':2,'silent':True,'bytes':movie.lstat().st_size,'sha256':H.sha(H.read(movie,limit=512*1024*1024))})
    finally:
        if proc is not None:
            row['reaped']=H.reap(proc)
            if not logged:
                try:
                    stdout,stderr=proc.communicate(timeout=5)
                    H.new(case/'stdout.log',stdout[:H.MAX_LOG]);H.new(case/'stderr.log',stderr[:H.MAX_LOG])
                    row['failure_output_truncated']=len(stdout)>H.MAX_LOG or len(stderr)>H.MAX_LOG
                except BaseException as error:row['failure_log_error_type']=type(error).__name__

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('self-sha256','source-pins-sha256','expected-head','full-completion-sha256','full-source-sha256','full-report-sha256',
                'full-outer-launch-sha256','full-outer-completion-sha256'):ap.add_argument('--'+key,required=True)
    ap.add_argument('--full-folder',type=Path,required=True);ap.add_argument('--full-outer-folder',type=Path,required=True)
    ap.add_argument('--root-exclusive-lane-confirmed',action='store_true',required=True);options=ap.parse_args()
    Q=source_module('_easing_c315_owned_ui',HERE/'qualified_ui_host.py',Q_PIN)
    H,_=Q.load_pinned('_easing_c315_owned_helpers',HERE/'qualified_helpers.py',*Q.HELPER_PIN)
    H.need(H.ROOT==ROOT and os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize
           and options.root_exclusive_lane_confirmed,'ROOT_WINDOWS313_EXCLUSIVE_LANE')
    H.need(options.expected_head==BASE and re.fullmatch('[0-9a-f]{64}',options.self_sha256) is not None,'EXACT_ROOT_OPTIONS')
    H.read(Path(__file__),digest=options.self_sha256)
    H.need(re.fullmatch('[0-9a-f]{64}',options.source_pins_sha256) is not None,'EXTERNAL_SOURCE_MANIFEST_PIN')
    source_pins=H.parse(H.read(HERE/'SOURCE_PINS.json',digest=options.source_pins_sha256,limit=2*1024*1024))
    H.need(source_pins.get('format')=='has_easing_c315_graphics_qualification_source_pins_1'
           and source_pins.get('revision')==BASE and type(source_pins.get('files')) is list,'SOURCE_MANIFEST_FORMAT')
    admitted=set()
    for row in source_pins['files']:
        relative=H.rel(row['path']);H.need(relative.casefold() not in admitted,'SOURCE_MANIFEST_CASE_ALIAS')
        admitted.add(relative.casefold());H.read(HERE/relative,row['bytes'],row['sha256'])
    actual=set();all_paths=set()
    def walk_error(e):raise e
    for folder,dirs,names in os.walk(HERE,followlinks=False,onerror=walk_error):
        for n in dirs+names:
            p=H.safe(Path(folder)/n);relative=p.relative_to(HERE).as_posix().casefold()
            H.need(relative not in all_paths,'ACTUAL_SOURCE_PACKET_CASE_ALIAS');all_paths.add(relative)
        for n in names:
            p=H.safe(Path(folder)/n);actual.add(p.relative_to(HERE).as_posix().casefold())
    H.need(actual==admitted|{'source_pins.json'},'EXACT_WHOLE_FROZEN_PACKET_MEMBERSHIP')
    inputs=H.parse(H.read(HERE/'INPUT_PINS.json',*INPUT_PIN))
    H.need(inputs.get('format')=='has_easing_c315_graphics_host_inputs_1' and inputs.get('revision')==BASE
           and len(inputs.get('targets',[]))==7,'EXACT_SEVEN_SOURCE_TARGETS')
    for row in inputs['files']:H.read(HERE/H.rel(row['path']),row['bytes'],row['sha256'])
    S,_=Q.load_pinned('_easing_c315_source',HERE/'source1103.py',*S_PIN)
    H.need(H.head()==BASE,'CURRENT_MAIN_REVISION')
    expected=S.admit_full(H,ROOT,HERE,options.full_folder,options.full_completion_sha256,options.full_source_sha256,
        options.full_report_sha256,options.full_outer_folder,options.full_outer_launch_sha256,options.full_outer_completion_sha256)
    frozen=S.immutable_runtime(H,Q,ROOT,expected);base_runtime=len(frozen);modified=[];added=[]
    for row in inputs['targets']:
        relative=H.rel(row['path']);raw=H.read(HERE/'candidate/payload'/relative,row['bytes'],row['sha256'])
        (modified if relative in frozen else added).append(relative);frozen[relative]=raw
    H.need(set(modified)=={'src/app.gd','src/renderer.gd'} and len(added)==5 and len(frozen)==base_runtime+5,'ONLY_REVIEWED_EASING_OVERLAY')
    # Literal anchors must reproduce both changed production bases exactly.
    patch=H.parse(H.read(HERE/'candidate/PATCHES.json'))
    for relative in modified:
        original=H.read(ROOT/relative,expected[relative]['bytes'],expected[relative]['sha256']).decode()
        transformed=original
        for row in patch['patches']:
            if row['path']==relative:
                H.need(transformed.count(row['before'])==1,'UNIQUE_EXACT_EASING_LITERAL_ANCHOR')
                transformed=transformed.replace(row['before'],row['after'])
        H.need(transformed.encode()==frozen[relative],'EXACT_BASE_TO_QUALIFIED_OVERLAY')
    lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));runtime=lock['runtime_paths']
    H.need(len(lock['runtime_executables'])==6,'SIX_APPROVED_EXECUTABLE_PINS')
    for path,row in lock['runtime_executables'].items():
        H.read(path,row['bytes'],row['sha256'],limit=1024*1024*1024)
        H.need(Path(path).lstat().st_mtime_ns==row['mtime_ns'],'RUNTIME_STAMP_CHANGED')
    H.need(Path(sys.executable).resolve()==Path(runtime['python']).resolve(),'APPROVED_PYTHON')
    planned=matrix();H.need(len(planned)==8 and sum(r['writer_checks'] for r in planned)==190
        and sum(r['reader_checks'] for r in planned)==64,'EXACT_MATRIX_254_CHECKS')
    # No stage, lock or child creation precedes the successful actual Full gate.
    stage=ROOT.parent/('has-easing-c315-graphics-'+str(time.time_ns()));H.safe(stage,missing=True)
    lane=ROOT/'output/easing-c315-graphics-qualification.lock';fd=None;lane_id=None;token=uuid.uuid4().hex.encode()
    owned=False;primary=None;parent_environment=dict(os.environ)
    result={'format':'has_easing_c315_graphics_qualification_1','status':'FAIL','revision':BASE,
        'functional_baseline':1103,'expected_graphical_checks':254,'planned_variants':planned,'completed_variants':[],
        'source_candidate_manifest_sha256':inputs['candidate_manifest_sha256'],
        'qualification_source_manifest_sha256':options.source_pins_sha256,
        'full_completion_sha256':options.full_completion_sha256,'full_source_sha256':options.full_source_sha256,
        'full_report_sha256':options.full_report_sha256,'full_outer_launch_sha256':options.full_outer_launch_sha256,
        'full_outer_completion_sha256':options.full_outer_completion_sha256,'immutable_runtime_files':base_runtime,
        'owned_runtime_files_per_studio':len(frozen),'cases':[],'jobs':[],'movies':[],
        'application_adopted':False,'new_Full_claimed':False,'owner_inputs_used':False,'native_conversion_requested':False}
    try:
        H.safe(lane,missing=True);fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(fd,token)==len(token),'OWNED_LOCK_SHORT_WRITE');os.fsync(fd);lane_id=H.stamp(os.fstat(fd))
        stage.mkdir(exist_ok=False);owned=True;(stage/'Verification').mkdir();(stage/'Variants').mkdir()
        H.json_new(stage/'SOURCE_SNAPSHOT.json',{'revision':BASE,'base_count':1103,'candidate_targets':inputs['targets'],
            'runtime':{name:{'bytes':len(raw),'sha256':H.sha(raw)} for name,raw in frozen.items()}})
        for variant in planned:
            name=variant['name'];folder=stage/'Variants'/name;folder.mkdir()
            writer=build_studio(H,folder,'WriterStudio',frozen);reader=build_studio(H,folder,'ReaderStudio',frozen)
            writer_data=folder/'WriterData';writer_data.mkdir();reader_data=folder/'ReaderData';reader_data.mkdir()
            flags=(['--classic'] if variant['theme']=='classic' else [])+(['--150'] if variant['scale']==150 else [])+(['--advanced'] if variant['workspace']=='advanced' else [])
            writer_name=name+'-writer';reader_name=name+'-reader'
            Q.run_case(H,stage,writer,runtime,result,writer_name,'tests/easing_c315_graphical_smoke.gd',
                [writer_data,*flags,*(['--movies'] if variant['movies'] else [])],
                'EASING_C315_GRAPHICS ',variant['writer_checks'],graphical=True,timeout=420 if variant['movies'] else 180)
            H.need(closure(H,result),'WRITER_CLOSURE_BEFORE_COLD_COPY')
            writer_report=result['cases'][-1]['result'];movie_names=writer_report.get('movies')
            H.need(type(movie_names) is list and len(movie_names)==2,'TWO_EXPLICIT_MOVIE_SLOTS')
            if variant['movies']:
                H.need(all(type(n) is str and n for n in movie_names) and len(set(movie_names))==2,'TWO_DISTINCT_ACTUAL_MOVIES')
                for index,n in enumerate(movie_names):
                    movie=H.safe(Path(n));H.need(movie.is_relative_to(writer_data) and movie.name=='movie.mp4','OWNED_MOVIE_PATH')
                    movie_probe(H,stage,writer,runtime,result,name+'-probe-'+str(index),movie)
                H.need(closure(H,result),'ALL_MOVIE_PROBES_REAPED')
            else:H.need(movie_names==['',''],'NO_UNREQUESTED_MOVIES')
            copied=copy_reader_inputs(H,writer_data,reader_data)
            row={'name':name,'writer_checks':variant['writer_checks'],'reader_checks':0,'copied_inputs':copied,
                 'fresh_reader_process_profile_and_cache':True,'writer_trees_offline_during_reader':False,
                 'writer_tree_restoration_complete':False}
            result['completed_variants'].append(row)
            writer_user=stage/'UserData'/writer_name
            with offline_trees(H,stage,(writer,writer_data,writer_user),row):
                Q.run_case(H,stage,reader,runtime,result,reader_name,'tests/easing_c315_graphical_smoke.gd',
                    [reader_data,'--read',*flags],'EASING_C315_GRAPHICS_READ ',8,graphical=True,timeout=180)
                H.need(closure(H,result),'FRESH_READER_CLOSURE_BEFORE_RESTORE')
                for copied_row in copied:H.read(reader_data/copied_row['name'],copied_row['bytes'],copied_row['sha256'],limit=128*1024*1024)
                row['reader_checks']=8
            H.need(row['writer_tree_restoration_complete'] is True,'COLD_CASE_RESTORED')
        result['graphical_checks']=sum(row.get('checks',0) for row in result['cases'])
        H.need(len(result['cases'])==len(result['jobs'])==16 and len(result['completed_variants'])==8
            and result['graphical_checks']==254 and len(result['movies'])==2
            and all(r['reader_checks']==8 and r['writer_trees_offline_during_reader'] is True
                    and r['writer_tree_restoration_complete'] is True for r in result['completed_variants']), 'ALL_EIGHT_COMPLETE_WRITER_COLD_READER_PAIRS')
        result['status']='PASS'
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__
        result['error_code']=str(error) if isinstance(error,H.Refusal) else 'EASING_GRAPHICS_EXCEPTION'
    finally:
        for process,row in H.OWNED:row['reaped']=H.reap(process)
        result['all_owned_launchers_reaped']=all(row.get('reaped') is True for _p,row in H.OWNED)
        result['all_attempted_private_jobs_closed']=closure(H,result)
        result['all_writer_trees_restored']=not HIDDEN
        result['retained_offline_trees']=[{'original':row['original'].relative_to(stage).as_posix(),
            'offline':row['offline'].relative_to(stage).as_posix()} for row in HIDDEN]
        result['parent_environment_unchanged']=dict(os.environ)==parent_environment
        try:result['head_unchanged']=H.head()==BASE
        except BaseException:result['head_unchanged']=False
        result['preservation_failures']=H.preserve();result['all_admitted_inputs_preserved']=not result['preservation_failures']
        try:result['current_Main_functional_domain_preserved']=S.domain(H,ROOT)==set(expected)
        except BaseException:result['current_Main_functional_domain_preserved']=False
        clean=all(result[k] is True for k in ('all_owned_launchers_reaped','all_attempted_private_jobs_closed',
            'all_writer_trees_restored','parent_environment_unchanged','head_unchanged','all_admitted_inputs_preserved',
            'current_Main_functional_domain_preserved'))
        result['owned_lock_removed']=False
        if fd is not None:
            try:
                H.need(clean and H.stamp(os.fstat(fd))==lane_id and H.stamp(lane.lstat())==lane_id,'OWNED_LOCK_RETAINED')
                os.lseek(fd,0,os.SEEK_SET);H.need(os.read(fd,128)==token,'OWNED_LOCK_TOKEN_CHANGED')
                os.close(fd);fd=None;H.need(H.stamp(lane.lstat())==lane_id,'OWNED_LOCK_PATH_CHANGED')
                lane.unlink();result['owned_lock_removed']=True
            except BaseException as error:result['lock_error_type']=type(error).__name__
            finally:
                if fd is not None:os.close(fd)
        result['owned_lock_retained']=lane_id is not None and not result['owned_lock_removed']
        if not(clean and result['owned_lock_removed']):result['status']='FAIL'
        if owned:
            H.json_new(stage/'PRIVATE_COORDINATOR_RESULT.json',result)
            public={k:v for k,v in result.items() if k not in ('jobs','preservation_failures')}
            public['private_job_count']=len(result['jobs']);public['preservation_failure_count']=len(result['preservation_failures'])
            H.json_new(stage/'PUBLIC_RESULT.json',public)
            print(json.dumps({'status':result['status'],'graphical_checks':result.get('graphical_checks',0),
                'completed_pairs':sum(r['reader_checks']==8 for r in result['completed_variants']),
                'error_code':result.get('error_code'),'result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if result['status']=='PASS' and primary is None else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status':'PREFLIGHT_REFUSED','error_type':type(error).__name__,'detail':str(error)}),flush=True)
        raise SystemExit(2)
