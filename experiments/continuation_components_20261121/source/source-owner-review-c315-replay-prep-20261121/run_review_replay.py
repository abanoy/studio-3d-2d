"""Root-only three-package replay of the ACTUAL prepared review Studio.
SOURCE ONLY, UNRUN. The failed c315 Full never qualifies this host.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,stat,sys,time,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REVIEW=ROOT.parent/'HAS-Review-Editor-Camera-c31576d'
BASE='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
Q_PIN=(21967,'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
S_PIN=(17881,'e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3')
INPUT_PIN=(2189,'6a659ea39218e37dd904c7f550459613aad33d12fd2a24a7bdbb928a59cc3747')
R_PIN=(10751,'e5ca0949ff863e7336aeb8173c8e610546eb8333791b634412441c74503b9abe')

def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))
def source_module(name,path,pin):
    for p in reversed((path,*path.parents)):
        s=p.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise RuntimeError('SOURCE_ALIAS')
    s=path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size!=pin[0]:raise RuntimeError('SOURCE_PLAIN_REGULAR_PIN')
    b=path.read_bytes()
    if identity(path.lstat())!=identity(s) or (len(b),hashlib.sha256(b).hexdigest())!=pin:raise RuntimeError('SOURCE_IDENTITY_BYTES_CHANGED')
    module=importlib.util.module_from_spec(importlib.util.spec_from_loader(name,loader=None))
    module.__file__=str(path);sys.modules[name]=module;exec(compile(b,str(path),'exec'),module.__dict__);return module
def closed(H,result):
    return all(r.get('reaped') is True for _p,r in H.OWNED) and all(r.get('private_job_closed') is True and r.get('desktop_closed') is True for r in result['jobs'])
def admit_packet(H,digest):
    H.need(re.fullmatch('[0-9a-f]{64}',digest) is not None,'EXTERNAL_SOURCE_MANIFEST_PIN')
    manifest=H.parse(H.read(HERE/'SOURCE_PINS.json',digest=digest,limit=2*1024*1024))
    H.need(manifest.get('format')=='has_owner_review_c315_replay_source_pins_1' and manifest.get('revision')==BASE,'SOURCE_PACKET_FORMAT')
    names=set()
    for row in manifest['files']:
        n=H.rel(row['path']);H.need(n.casefold() not in names,'PACKET_CASE_ALIAS');names.add(n.casefold());H.read(HERE/n,row['bytes'],row['sha256'])
    actual=set();seen=set()
    def error(e):raise e
    for here,dirs,files in os.walk(HERE,followlinks=False,onerror=error):
        for n in dirs+files:
            p=H.safe(Path(here)/n);name=p.relative_to(HERE).as_posix().casefold();H.need(name not in seen,'ACTUAL_PACKET_ALIAS');seen.add(name)
            if n in files:actual.add(name)
    H.need(actual==names|{'source_pins.json'},'EXACT_SOURCE_PACKET_MEMBERSHIP')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('self-sha256','source-pins-sha256','expected-head','full-completion-sha256','full-source-sha256',
                'full-report-sha256','full-outer-launch-sha256','full-outer-completion-sha256'):ap.add_argument('--'+key,required=True)
    ap.add_argument('--full-folder',type=Path,required=True);ap.add_argument('--full-outer-folder',type=Path,required=True)
    ap.add_argument('--private-review-seal',type=Path,required=True)
    ap.add_argument('--root-exclusive-lane-confirmed',action='store_true',required=True);options=ap.parse_args()
    Q=source_module('_review_c315_ui_defs',HERE/'qualified_ui_host.py',Q_PIN)
    H,_=Q.load_pinned('_review_c315_owned',HERE/'qualified_helpers.py',*Q.HELPER_PIN)
    H.need(H.ROOT==ROOT and os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize
           and options.root_exclusive_lane_confirmed,'ROOT_WINDOWS313_EXCLUSIVE_LANE')
    H.need(options.expected_head==BASE and re.fullmatch('[0-9a-f]{64}',options.self_sha256) is not None,'EXACT_C315_OPTIONS')
    H.read(Path(__file__),digest=options.self_sha256);admit_packet(H,options.source_pins_sha256)
    inputs=H.parse(H.read(HERE/'HOST_INPUT_PINS.json',*INPUT_PIN))
    H.need(inputs.get('format')=='has_c315_owner_replay_source_inputs_1' and inputs.get('revision')==BASE
           and inputs.get('expected_cases')==3 and inputs.get('expected_total_checks')==69,'EXACT_THREE_PACKAGE_SOURCE_SCOPE')
    for row in inputs['files']:H.read(HERE/H.rel(row['path']),row['bytes'],row['sha256'])
    S,_=Q.load_pinned('_review_c315_full',HERE/'source1103.py',*S_PIN)
    H.need(H.head()==BASE,'CURRENT_MAIN_REVISION')
    expected_sources=S.admit_full(H,ROOT,HERE,options.full_folder,options.full_completion_sha256,options.full_source_sha256,
        options.full_report_sha256,options.full_outer_folder,options.full_outer_launch_sha256,options.full_outer_completion_sha256)
    committed=S.immutable_runtime(H,Q,ROOT,expected_sources)
    R=source_module('_review_c315_validation',HERE/'review_validation.py',R_PIN)
    H.read(HERE/'review_validation.py',*R_PIN)
    compare_row=next(row for row in inputs['files'] if row['path']=='review_state_compare.py')
    C,_=Q.load_pinned('_review_c315_saved_state',HERE/'review_state_compare.py',compare_row['bytes'],compare_row['sha256'])
    prep,seal=R.admit_review(H,REVIEW,options.private_review_seal,BASE,committed)
    studio=REVIEW/'Studio';replay=studio/'tests/owner_review_replay.gd'
    replay_pin=inputs['committed_replay_script_pin'];H.read(replay,replay_pin['bytes'],replay_pin['sha256'])
    H.need(H.sha(H.read(studio/'tools/private_desktop.py'))==H.PRIVATE_SHA,'REVIEW_COMMITTED_PRIVATE_LAUNCHER')
    lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));runtime=lock['runtime_paths']
    H.need(len(lock['runtime_executables'])==6,'SIX_APPROVED_RUNTIME_EXECUTABLES')
    for p,row in lock['runtime_executables'].items():
        H.read(p,row['bytes'],row['sha256'],limit=1024*1024*1024);H.need(Path(p).lstat().st_mtime_ns==row['mtime_ns'],'RUNTIME_STAMP_CHANGED')
    H.need(Path(sys.executable).resolve()==Path(runtime['python']).resolve() and Path(prep['pythonw']['path'])==Path(runtime['pythonw']),'APPROVED_PYTHON_RUNTIME')
    # All shared Full/source/receipt/outer gates and review seals precede stage,
    # lock, profile, request creation and every native process.
    stage=ROOT.parent/('has-owner-review-c315-replay-'+str(time.time_ns()));H.safe(stage,missing=True)
    lane=ROOT/'output/owner-review-c315-replay.lock';fd=None;lane_id=None;token=uuid.uuid4().hex.encode()
    owned=False;primary=None;parent_environment=dict(os.environ)
    result={'format':'has_owner_review_c315_three_replay_1','status':'FAIL','revision':BASE,'expected_cases':3,'expected_checks':69,
        'full_completion_sha256':options.full_completion_sha256,'full_source_sha256':options.full_source_sha256,
        'full_report_sha256':options.full_report_sha256,'full_outer_launch_sha256':options.full_outer_launch_sha256,
        'full_outer_completion_sha256':options.full_outer_completion_sha256,'source_manifest_sha256':options.source_pins_sha256,
        'preparation_sha256':R.PREP_PIN[1],'private_review_seal_sha256':R.SEAL_PIN[1],
        'actual_review_source_files':1106,'cases':[],'jobs':[],'six_package_aggregate_claimed':False,
        'human_approval_substituted':False,'artist_fidelity_approved':False,'clean_machine_portability_qualified':False,
        'live_performance_qualified':False,'new_Full_claimed':False,'installed_Studio_modified':False,'private_art_uploaded':False}
    try:
        H.safe(lane,missing=True);fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(fd,token)==len(token),'OWNED_LOCK_SHORT_WRITE');os.fsync(fd);lane_id=H.stamp(os.fstat(fd))
        stage.mkdir(exist_ok=False);owned=True;(stage/'PRIVATE').mkdir()
        launcher=stage/'Launcher';(launcher/'tools').mkdir(parents=True);(launcher/'output/private-desktop').mkdir(parents=True)
        # This is only the exact approved launcher and receipt root, never an app
        # snapshot. Godot --path and its reported res:// MUST be actual Studio.
        H.new(launcher/'tools/private_desktop.py',H.read(studio/'tools/private_desktop.py'))
        H.json_new(stage/'PRIVATE/PRIVATE_SCOPE.json',{'private_do_not_publish':True,'actual_review':str(REVIEW),
            'normal_startup_script':str(replay),'private_seal':str(options.private_review_seal),
            'note':'Request/project/state/metadata/images/logs remain local. No source or preference overlay is applied.'})
        for index,row in enumerate(prep['projects'],1):
            R.admit_review(H,REVIEW,options.private_review_seal,BASE,committed)
            package=Path(row['copy']);project,payload,expected_checks=R.metadata(H,package)
            summary=seal['case_summaries'][index-1];H.need(summary['expected_checks']==expected_checks,'PRIVATE_CASE_CARDINALITY')
            case=stage/'PRIVATE'/('case-'+str(index));case.mkdir();user=case/'User'
            for n in ('Roaming','Local','Temp'):(user/n).mkdir(parents=True)
            env=dict(parent_environment)
            for key in tuple(env):
                if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX'):env.pop(key,None)
            env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',HYBRID_PYTHON=runtime['python'],
                HYBRID_GODOT=runtime['godot'],HYBRID_FFMPEG=runtime['ffmpeg'],
                APPDATA=str(user/'Roaming'),LOCALAPPDATA=str(user/'Local'),TEMP=str(user/'Temp'),TMP=str(user/'Temp'))
            H.json_new(case/'expected.json',project)
            request={'format':'has_owner_review_replay_request_1','package':str(package).replace('\\','/'),
                'folder':str(case).replace('\\','/'),'result':str(case/'result.json').replace('\\','/')}
            H.json_new(case/'request.json',request)
            scene='[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path='+json.dumps(str(replay).replace('\\','/'))+' id="1_replay"]\n\n[node name="OwnerReviewReplay" type="Node"]\nscript = ExtResource("1_replay")\n'
            H.new(case/'replay.tscn',scene.encode())
            receipt=launcher/'output/private-desktop'/('case-'+str(index)+'.json')
            args=[runtime['pythonw'],str(launcher/'tools/private_desktop.py'),'--receipt',str(receipt),'--',runtime['godot'],
                  '--path',str(studio),str(case/'replay.tscn'),'--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(case/'request.json')]
            H.need('--script' not in args and '--headless' not in args and '--editor' not in args
                   and Path(args[args.index('--path')+1])==studio and not any('smoke' in a.lower() for a in args),'REAL_NORMAL_SCENE_ENTRY_ONLY')
            completed=H.owned_command(args,case,launcher,runtime,env,result['jobs'],window=True,timeout=205)
            H.need(closed(H,result),'STOP_UNLESS_PRIOR_JOB_CLOSED')
            proof=H.parse(H.read(receipt,limit=1024*1024));H.need(proof.get('private_window_seen') is True,'REAL_PRIVATE_WINDOW_OBSERVED')
            H.need(completed.returncode==0,'NORMAL_REPLAY_NONZERO_EXIT')
            log=completed.stdout+'\n'+completed.stderr;engine=H.read(case/'engine.log',limit=H.MAX_LOG).decode('utf-8','replace')
            H.need(not any(b in log+'\n'+engine for b in Q.BAD_LOG) and not re.search(r'(?m)^(ERROR:|SCRIPT ERROR:|FAIL )',log+'\n'+engine),'PRIVATE_REPLAY_ENGINE_OR_ASSERTION_FAILURE')
            markers=[line[len('OWNER_REVIEW_REPLAY '):] for line in completed.stdout.splitlines() if line.startswith('OWNER_REVIEW_REPLAY ')]
            H.need(len(markers)==1,'EXACT_ONE_NORMAL_REPLAY_MARKER');marker=H.parse(markers[0])
            H.need(type(marker.get('failures')) is int and marker['failures']==0 and marker.get('package')==request['package'],'REPLAY_COMPLETION_IDENTITY')
            H.need(sum(line.startswith('PASS ') for line in completed.stdout.splitlines())==expected_checks,'EXACT_PRIVATE_REPLAY_PASS_COUNT')
            report=H.parse(H.read(case/'result.json',limit=8*1024*1024))
            H.need(type(report.get('process_id')) is int and report['process_id']==proof.get('child_pid')
                   and type(report.get('worker_pid')) is int and report['worker_pid']>0
                   and report['worker_pid']!=report['process_id'],'ACTUAL_GODOT_AND_NORMAL_WORKER_PROCESS_BINDING')
            private_before=H.read(case/'observed-before.json',limit=4*1024*1024);private_after=H.read(case/'observed-after.json',limit=4*1024*1024)
            H.need(private_before==private_after,'EXACT_BEFORE_AFTER_PORTABLE_STATE_TEXT')
            checked=R.verify_case(H,case,report,project,payload,package,studio,prep['profile'],C.compare)
            checked['index']=index;checked['status']='PASS';result['cases'].append(checked)
            R.admit_review(H,REVIEW,options.private_review_seal,BASE,committed)
        H.need(len(result['cases'])==len(result['jobs'])==3 and sum(r['checks'] for r in result['cases'])==69,'ALL_THREE_NORMAL_REPLAYS_COMPLETE')
        result['status']='PASS'
    except BaseException as error:
        primary=error;result['private_error_type']=type(error).__name__;result['private_error_detail']=str(error)
        result['error_code']=str(error) if isinstance(error,H.Refusal) else 'PRIVATE_REPLAY_EXCEPTION'
    finally:
        for p,row in H.OWNED:row['reaped']=H.reap(p)
        result['all_owned_launchers_reaped']=all(r.get('reaped') is True for _p,r in H.OWNED)
        result['all_attempted_private_jobs_closed']=closed(H,result)
        result['parent_environment_unchanged']=dict(os.environ)==parent_environment
        try:result['Main_head_unchanged']=H.head()==BASE
        except BaseException:result['Main_head_unchanged']=False
        try:
            R.admit_review(H,REVIEW,options.private_review_seal,BASE,committed);result['review_original_sources_launchers_packages_stamps_unchanged']=True
        except BaseException:result['review_original_sources_launchers_packages_stamps_unchanged']=False
        result['preservation_failures']=H.preserve();result['all_admitted_inputs_preserved']=not result['preservation_failures']
        try:result['Main_source_domain_unchanged']=S.domain(H,ROOT)==set(expected_sources)
        except BaseException:result['Main_source_domain_unchanged']=False
        clean=all(result[k] is True for k in ('all_owned_launchers_reaped','all_attempted_private_jobs_closed','parent_environment_unchanged',
            'Main_head_unchanged','review_original_sources_launchers_packages_stamps_unchanged','all_admitted_inputs_preserved','Main_source_domain_unchanged'))
        result['owned_lock_removed']=False
        if fd is not None:
            try:
                H.need(clean and H.stamp(os.fstat(fd))==lane_id and H.stamp(lane.lstat())==lane_id,'OWNED_LOCK_RETAINED')
                os.lseek(fd,0,os.SEEK_SET);H.need(os.read(fd,128)==token,'OWNED_LOCK_TOKEN_CHANGED')
                os.close(fd);fd=None;H.need(H.stamp(lane.lstat())==lane_id,'OWNED_LOCK_PATH_CHANGED');lane.unlink();result['owned_lock_removed']=True
            except BaseException:pass
            finally:
                if fd is not None:os.close(fd)
        result['owned_lock_retained']=lane_id is not None and not result['owned_lock_removed']
        if not(clean and result['owned_lock_removed']):result['status']='FAIL'
        if owned:
            H.json_new(stage/'PRIVATE/PRIVATE_COORDINATOR_RESULT.json',result)
            public={k:result[k] for k in ('format','status','revision','expected_cases','expected_checks','full_completion_sha256','full_source_sha256',
                'full_report_sha256','full_outer_launch_sha256','full_outer_completion_sha256','source_manifest_sha256','preparation_sha256','private_review_seal_sha256',
                'actual_review_source_files','all_owned_launchers_reaped','all_attempted_private_jobs_closed','parent_environment_unchanged','Main_head_unchanged',
                'review_original_sources_launchers_packages_stamps_unchanged','all_admitted_inputs_preserved','Main_source_domain_unchanged',
                'owned_lock_removed','owned_lock_retained','six_package_aggregate_claimed','human_approval_substituted','artist_fidelity_approved',
                'clean_machine_portability_qualified','live_performance_qualified','new_Full_claimed','installed_Studio_modified','private_art_uploaded')}
            public['cases']=result['cases'];public['private_job_count']=len(result['jobs']);public['preservation_failure_count']=len(result['preservation_failures'])
            public['completed_cases']=len(result['cases']);public['checks']=sum(r['checks'] for r in result['cases'])
            public['error_code']='PRIVATE_REPLAY_FAILED' if result.get('error_code') else None
            H.json_new(stage/'PUBLIC_RESULT.json',public)
            print(json.dumps({'status':result['status'],'completed_cases':len(result['cases']),'checks':public['checks'],
                'public_result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if result['status']=='PASS' and primary is None else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status':'PREFLIGHT_REFUSED','error_type':type(error).__name__,'error_code':'PRIVATE_REVIEW_PREFLIGHT_REFUSED'}),flush=True)
        raise SystemExit(2)
