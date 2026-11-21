"""Root-only exact-five-profile OFF-default GPU qualification; source authored, unrun.
Uses an owned e087 snapshot and existing prepared fixtures, with no conversion.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import time
import uuid
import types
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
REVISION = 'e0879c7df74bc3704902bfdaf4ff74eee40c3aea'
FULL_REVISION = '36044471151a6e561d6d3a404859e76ddd05738d'
FULL = ROOT/'output/windows-reference-body-1795233568436471500'
FULL_SHA = '2ca293d180751d8d219c0371665cb64a0a9212cc7a2bb3ae20f1fbdd4e5a0471'
SOURCE_SHA = 'ae338017a4a0ac3483bfeb9bc8d1ab40355780bdeb235e29c104d9cf94c5f2f9'
BUILDER = ROOT/'output/source-owner-review-builder-v3-prep-20261121/build_review.py'
BUILDER_PIN = (22176,'d5ab807301d2b51b9ecea5fab1624b12addffe8247f5eafae60bf02c63c6dcec')
LOCK = ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
PRIVATE_SHA = 'c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61'
EXPECTED = {}
OWNED = []
MAX_LOG = 8*1024*1024

class Refusal(RuntimeError): pass

def need(value, code):
    if not value: raise Refusal(code)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def stamp(info):
    mode = info.st_mode & ~0o111 if os.name == 'nt' and stat.S_ISREG(info.st_mode) else info.st_mode
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,mode,getattr(info,'st_file_attributes',0)&~0x40000)

def safe(path, missing=False):
    path = Path(os.path.abspath(path))
    for parent in reversed((path,*path.parents)):
        try: info = parent.lstat()
        except FileNotFoundError:
            need(missing and parent == path,'MISSING_OR_ALIAS_PARENT'); continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'PATH_ALIAS')
    return path

def read(path, count=None, digest=None, limit=256*1024*1024, remember=True):
    path = safe(path); before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= limit,'BOUNDED_REGULAR_INPUT_REQUIRED')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before),'INPUT_CHANGED_BEFORE_READ')
        raw = stream.read(before.st_size+1)
        need(stamp(os.fstat(stream.fileno())) == stamp(before),'INPUT_CHANGED_DURING_READ')
    need(len(raw) == before.st_size and stamp(path.lstat()) == stamp(before),'INPUT_READBACK_CHANGED')
    need((count is None or len(raw)==count) and (digest is None or sha(raw)==digest),'INPUT_PIN_DIFFERS')
    if remember:
        key = str(path); row = (stamp(before),len(raw),sha(raw))
        need(key not in EXPECTED or EXPECTED[key] == row,'PREVIOUS_INPUT_CHANGED')
        EXPECTED[key] = row
    return raw

def parse(raw):
    def pairs(rows):
        value={}
        for key,item in rows:
            need(key not in value,'DUPLICATE_JSON_KEY');value[key]=item
        return value
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _v: (_ for _ in ()).throw(Refusal('NONFINITE_JSON')))

def rel(name):
    need(type(name) is str and name and ':' not in name and '\\' not in name,'RELATIVE_PATH_REQUIRED')
    path = PurePosixPath(name)
    need(not path.is_absolute() and '..' not in path.parts and path.as_posix()==name,'RELATIVE_PATH_REQUIRED')
    return name

def new(path, raw):
    path = safe(path,missing=True)
    with path.open('xb') as stream:
        need(stream.write(raw)==len(raw),'SHORT_OWNED_WRITE');stream.flush();os.fsync(stream.fileno())
    read(path,len(raw),sha(raw))

def json_new(path, value):
    new(path,(json.dumps(value,indent=2)+'\n').encode())

def head():
    return subprocess.run(['git','-c','core.autocrlf=false','rev-parse','HEAD'],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW).stdout.decode().strip()

def load_builder():
    read(BUILDER,*BUILDER_PIN)
    spec=importlib.util.spec_from_file_location('_has_component_snapshot_reader',BUILDER)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    need(module.ROOT==ROOT,'SNAPSHOT_READER_ROOT');return module

OVERLAYS = [
    {
        "source": "output/import-physics-default-off-prep-20261120/payload/src/import_actions.gd",
        "target": "src/import_actions.gd",
        "bytes": 3870,
        "sha256": "3f280041d2f09a6fbd956d0e56d2bc6f8ced11453bbf794fbde0c223495dd8f2"
    },
    {
        "source": "output/import-physics-default-off-prep-20261120/payload/tests/import_physics_defaults_unit.gd",
        "target": "tests/import_physics_defaults_unit.gd",
        "bytes": 4701,
        "sha256": "dbee24031470b4b779d636ba7225ccb86959391813ed26610362877e4a3e2dc7"
    },
    {
        "source": "output/import-physics-default-off-cold-wire-prep-20261121/import_physics_smoke.gd",
        "target": "tests/import_physics_smoke.gd",
        "bytes": 21657,
        "sha256": "edb9d0f3f79873dece720f54565dc1de6f6e1808a2b12d95fdf83372acf1b540"
    },
    {
        "source": "output/import-physics-default-off-prep-20261120/payload/tests/verify_import_physics.py",
        "target": "tests/verify_import_physics.py",
        "bytes": 4708,
        "sha256": "b7a5df65220801fd4adbe6886b62b65356aa8ab06dd2e97e45f11eef02620438"
    }
]
FIXTURE_PIN = ("FIXTURE_PINS.json",5973,"9ab3c9808faebd9cf31cd5d5c5645d3255d8bfb6907ad2a7e66b07732adf1fff")
EXPECTED_LABELS = ["MMD","GMod","SFM","VRM1.0","VRM0.x"]

def replace_owned(path, raw):
    # Deliberate overlay only after the original fresh-copy identity was admitted.
    key=str(safe(path));need(key in EXPECTED,'OVERLAY_NOT_OWNED')
    read(path)
    with Path(path).open('wb') as stream:
        need(stream.write(raw)==len(raw),'SHORT_OVERLAY_WRITE');stream.flush();os.fsync(stream.fileno())
    EXPECTED.pop(key)
    read(path,len(raw),sha(raw))

def reap(process):
    try:
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=20)
        else: process.wait(timeout=1)
        return process.poll() is not None
    except BaseException: return False


def preserve():
    failures=[]
    for name,(identity,count,digest) in tuple(EXPECTED.items()):
        try:
            read(name,count,digest,remember=False)
            need(stamp(Path(name).lstat())==identity,'INPUT_STAMP_CHANGED')
        except BaseException as error:failures.append({'path':name,'error_type':type(error).__name__})
    return failures

def pinned_fixture_inputs(document):
    need(type(document) is dict and document.get('format')=='has_existing_five_native_import_fixture_pins_1','FIXTURE_PIN_FORMAT')
    need(type(document.get('models')) is list and [row.get('label') for row in document['models']]==EXPECTED_LABELS,'EXACT_FIVE_PROFILE_CATALOGUE')
    base=safe(document['fixture_root']);blobs={}
    for row in document['metadata_inputs']+[item['asset'] for item in document['models']]:
        path=safe(row['path']);need(path.is_relative_to(base),'FIXTURE_SCOPE')
        need(type(row['bytes']) is int and type(row['mtime_ns']) is str and row['mtime_ns'].isdigit(),'FIXTURE_STAMP_FORMAT')
        raw=read(path,row['bytes'],row['sha256']);need(path.lstat().st_mtime_ns==int(row['mtime_ns']),'FIXTURE_MTIME_CHANGED')
        blobs[str(path)]=raw
    report=parse(blobs[str(base/'native-import-verification.json')])
    need(type(report.get('bundles')) is list and len(report['bundles'])==4,'EXISTING_NATIVE_REPORT_DOMAIN')
    vrm=[]
    for bundle in report['bundles']:
        parameter=Path(bundle)/'parameters.json';need(str(parameter) in blobs,'PARAMETER_NOT_ADMITTED')
        value=parse(blobs[str(parameter)])
        if value.get('kind')=='vrm_preparation':vrm.append('VRM'+value['vrm_version'])
    need(vrm==EXPECTED_LABELS[3:],'BOTH_VRM_VERSIONS_REQUIRED')
    for row in document['models'][:3]:
        project=base/rel(row['project']);value=parse(blobs[str(project)])
        model=value.get('model',{}) or value['world']['objects'][-1]
        need(model['path']==row['asset_relative'] and project.parent/model['path']==Path(row['asset']['path']),'PROJECT_ASSET_BINDING')
    return blobs

def stage_fixtures(document,blobs,destination):
    destination.mkdir();base=Path(document['fixture_root'])
    for row in document['models'][:3]:
        original=base/row['project'];target=destination/rel(row['project'])
        target.parent.mkdir(parents=True,exist_ok=True);new(target,blobs[str(original)])
        asset=target.parent/rel(row['asset_relative']);asset.parent.mkdir(parents=True,exist_ok=True)
        new(asset,blobs[str(Path(row['asset']['path']))])
    report=parse(blobs[str(base/'native-import-verification.json')]);new_bundles=[]
    for index,bundle in enumerate(report['bundles']):
        target=destination/('bundle-'+str(index));target.mkdir()
        new(target/'parameters.json',blobs[str(Path(bundle)/'parameters.json')])
        for row in document['models'][3:]:
            if Path(row['bundle'])==Path(bundle):new(target/'scene.glb',blobs[str(Path(row['asset']['path']))])
        new_bundles.append(str(target))
    report['bundles']=new_bundles;json_new(destination/'native-import-verification.json',report)

def audit_plan_file(path,document,studio,fixture_copy):
    plans=parse(read(path,limit=4*1024*1024))
    need(type(plans) is list and [row.get('label') for row in plans]==EXPECTED_LABELS,'EXACT_FIVE_WORKER_PLANS_REQUIRED')
    for plan,pin in zip(plans,document['models']):
        asset=safe(plan['source']);need(asset.is_relative_to(path.parent) or asset.is_relative_to(fixture_copy),'WORKER_PLAN_NOT_OWNED')
        read(asset,pin['asset']['bytes'],pin['asset']['sha256'])
        parameters=asset.with_name('parameters.json')
        need(parameters.is_file(),'NATIVE_PARAMETERS_SIDECAR_REQUIRED');read(parameters,limit=4*1024*1024)
    return plans

def owned_command(args,case,studio,runtime,env,rows,*,window,timeout):
    args=list(map(str,args));need(len(args)>8 and Path(args[0])==Path(runtime['pythonw']) and Path(args[1])==studio/'tools/private_desktop.py','EXACT_OWNED_PRIVATE_COMMAND_REQUIRED')
    receipt=Path(args[args.index('--receipt')+1]);safe(receipt,missing=True)
    need(receipt.is_relative_to(studio/'output/private-desktop'),'PRIVATE_RECEIPT_SCOPE')
    boundary=args.index('--');need(Path(args[boundary+1])==Path(runtime['godot']),'APPROVED_GODOT_REQUIRED')
    need(('--headless' not in args)==window,'GPU_VS_HEADLESS_SCOPE')
    args[2:2]=['--timeout',str(timeout),'--memory-limit-mib','4096']
    index=len(rows);name='job-'+str(index);row={'name':name,'window_required':window,'reaped':False,'private_job_required':True,'private_job_closed':False,'desktop_closed':False,'status':'FAIL'};rows.append(row)
    proc=None;primary=None
    try:
        with (case/(name+'-stdout.log')).open('xb') as out,(case/(name+'-stderr.log')).open('xb') as err:
            proc=subprocess.Popen(args,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            OWNED.append((proc,row));row['pid']=proc.pid
            json_new(case/(name+'-launch.json'),{'pid':proc.pid,'command':args,'private_receipt':str(receipt)})
            proc.wait(timeout=timeout+15)
    except BaseException as error:primary=error
    finally:
        if proc is not None:row['reaped']=reap(proc)
        try:
            proof=parse(read(receipt,limit=1024*1024))
            row.update(private_job_closed=proof.get('job_closed') is True,desktop_closed=proof.get('desktop_closed') is True,
                child_desktop_observed=proof.get('child_desktop_confirmed') is True,foreground_child_observed=proof.get('foreground_child_observed'))
            need(proof.get('format')=='studio_private_desktop_1' and row['private_job_closed'] and row['desktop_closed'],'PRIVATE_CLOSURE_UNPROVEN')
            need(proof.get('desktop_switch_requested') is False and proof.get('foreground_child_observed') is False and proof.get('error') is None,'PRIVATE_ISOLATION_FAILED')
            need(not window or row['child_desktop_observed'],'ACTUAL_GPU_WINDOW_NOT_OBSERVED')
            need(proc is not None and row['reaped'] and type(proof.get('exit')) is int and proof['exit']==proc.returncode,'PRIVATE_EXIT_BINDING')
            row['status']='PASS' if proc.returncode==0 else 'FAIL'
        except BaseException as closure_error:
            row['closure_error_type']=type(closure_error).__name__
            if primary is None:primary=closure_error
    if primary is not None:raise primary
    stdout=read(case/(name+'-stdout.log'),limit=MAX_LOG).decode('utf-8','replace');stderr=read(case/(name+'-stderr.log'),limit=MAX_LOG).decode('utf-8','replace')
    need(not re.search(r'(?m)^(?:SCRIPT ERROR:|ERROR:|FAIL )',stdout+'\n'+stderr),'ENGINE_OR_ASSERTION_ERROR')
    return subprocess.CompletedProcess(args,proc.returncode,stdout,stderr)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256',required=True);parser.add_argument('--root-exclusive-lane-confirmed',action='store_true')
    options=parser.parse_args()
    need(os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize and options.root_exclusive_lane_confirmed,'ROOT_PYTHON313_WINDOWS_EXCLUSIVE_LANE_REQUIRED')
    read(Path(__file__),digest=options.self_sha256)
    # Refuse incomplete Full before Git, runtime/fixture reads or any process call.
    completion=parse(read(FULL/'completion.json',digest=FULL_SHA))
    need(completion.get('whole_verifier_pass') is True and completion.get('child_reaped') is True and completion.get('all_private_jobs_isolated_closed') is True,'WHOLE_FULL_CLOSURE_REQUIRED')
    B=load_builder();full,catalogue,_proofs=B.validate_full(FULL,FULL_REVISION,FULL_SHA)
    for name in ('source-before.json','source-after.json'):read(FULL/name,digest=SOURCE_SHA)
    need(head()==REVISION,'IMMUTABLE_E087_HEAD_REQUIRED')
    for name,row in catalogue.items():
        path=ROOT/rel(name);read(path,row['bytes'],row['sha256']);need(path.lstat().st_mtime_ns==row['mtime_ns'],'SOURCE_MTIME_DIFFERS')
    frozen=B.source_blobs(REVISION,catalogue);need(len(frozen)==1087,'RUNTIME_SNAPSHOT_SCOPE')
    lock=parse(read(LOCK,digest=LOCK_SHA));runtime=lock['runtime_paths']
    for path,row in lock['runtime_executables'].items():
        read(path,row['bytes'],row['sha256']);need(Path(path).lstat().st_mtime_ns==row['mtime_ns'],'RUNTIME_MTIME_DIFFERS')
    need(Path(sys.executable).resolve()==Path(runtime['python']).resolve(),'APPROVED_PYTHON_REQUIRED')
    fixture_document=parse(read(Path(__file__).with_name(FIXTURE_PIN[0]),FIXTURE_PIN[1],FIXTURE_PIN[2]))
    fixture_blobs=pinned_fixture_inputs(fixture_document)
    overlays={row['source']:read(ROOT/row['source'],row['bytes'],row['sha256']) for row in OVERLAYS}
    own_worker=Path(__file__).with_name('default_off_worker.py');worker_raw=read(own_worker,6418,'5134a79ca34916c2c7a7d4f0992d1e4af65cfa4a585731cc42dadcbdb2db4db2')
    bootstrap=Path(__file__).with_name('private_worker_bootstrap.py');bootstrap_raw=read(bootstrap,3709,'59c9b66e7ba62339127aa874abcc02cd0e568b6c641d9f0d1cefddbbd8e52b4e')
    placement_worker=ROOT/'output/source-material-carrier-host-v11-prep-20261120/fresh_carrier_probe.py'
    placement_sentinel=ROOT/'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py'
    read(placement_worker,72518,'2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea')
    read(placement_sentinel,17989,'034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
    stage=ROOT.parent/('has-import-default-off-gpu-'+str(time.time_ns()));safe(stage,missing=True);need(not stage.exists(),'STAGE_EXISTS')
    lane=ROOT/'output/source-import-default-off-gpu.lock';lane_fd=None;lane_identity=None;stage_owned=False;primary=None;outer_attempted=False;outer_closed=True;outer_receipt=None;outer_row=None;parent_environment=dict(os.environ)
    result={'format':'has_exact_five_profile_import_off_gpu_1','status':'FAIL','source_revision':REVISION,'qualified_full_revision':FULL_REVISION,
        'functional_sources':1084,'runtime_snapshot_files':1087,'native_profile_labels':EXPECTED_LABELS,'native_profiles_expected':5,'jobs':[],
        'application_adopted':False,'native_conversion_or_sdk_started':False,'owner_visual_acceptance':False}
    try:
        safe(lane,missing=True);lane_fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR);token=uuid.uuid4().hex.encode()
        need(os.write(lane_fd,token)==len(token),'LANE_WRITE');os.fsync(lane_fd);lane_identity=stamp(os.fstat(lane_fd))
        stage.mkdir(exist_ok=False);stage_owned=True;studio=stage/'Studio';studio.mkdir();case=stage/'Verification';case.mkdir()
        for name,raw in frozen.items():
            target=studio/rel(name);target.parent.mkdir(parents=True,exist_ok=True);new(target,raw)
        for row in OVERLAYS:
            target=studio/row['target'];target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():replace_owned(target,overlays[row['source']])
            else:new(target,overlays[row['source']])
        fixtures=stage/'Fixtures';stage_fixtures(fixture_document,fixture_blobs,fixtures)
        for name in ('UserData/Roaming','UserData/Local','UserData/Temp'):(stage/name).mkdir(parents=True)
        profile='HAS Import Default Off '+uuid.uuid4().hex
        new(studio/'override.cfg',('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
        env=os.environ.copy()
        for key in tuple(env):
            if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX'):env.pop(key,None)
        env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',HYBRID_PYTHON=runtime['python'],HYBRID_GODOT=runtime['godot'],
            HYBRID_FFMPEG=runtime['ffmpeg'],HYBRID_NATIVE_FIXTURES=str(fixtures),APPDATA=str(stage/'UserData/Roaming'),
            LOCALAPPDATA=str(stage/'UserData/Local'),TEMP=str(stage/'UserData/Temp'),TMP=str(stage/'UserData/Temp'))
        # The caller environment is never edited; only this owned child receives env.
        worker_copy=stage/'default_off_worker.py';new(worker_copy,worker_raw)
        bootstrap_copy=stage/'private_worker_bootstrap.py';new(bootstrap_copy,bootstrap_raw)
        request={'format':'has_exact_five_import_off_worker_1','coordinator':{'path':str(Path(__file__).resolve()),'bytes':Path(__file__).stat().st_size,'sha256':options.self_sha256},
            'studio':str(studio),'case':str(case),'fixtures':str(fixtures),'runtime':runtime,'fixture_document':fixture_document,'temp':str(stage/'UserData/Temp'),
            'owned_sources':[{'path':str(studio/row['target']),'bytes':row['bytes'],'sha256':row['sha256']} for row in OVERLAYS]}
        request_path=case/'worker-request.json';json_new(request_path,request)
        config={'format':'has_map_prepare_hidden_bootstrap_1','worker':{'path':str(placement_worker),'bytes':72518,'sha256':'2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea'},
            'sentinel':{'path':str(placement_sentinel),'bytes':17989,'sha256':'034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3'},
            'preparer':{'path':str(worker_copy),'bytes':len(worker_raw),'sha256':sha(worker_raw)},
            'args':['--request',str(request_path),'--request-sha256',sha(read(request_path))],'placement':str(case/'outer-placement.json'),
            'environment':{'PYTHONDONTWRITEBYTECODE':'1','NO_BPY':'1','BLENDER_USER_CONFIG':str(stage/'UserData/Temp'),'APPDATA':env['APPDATA'],'LOCALAPPDATA':env['LOCALAPPDATA'],'TEMP':env['TEMP'],'TMP':env['TMP']}}
        config_path=case/'bootstrap-config.json';json_new(config_path,config)
        command=[runtime['python'],'-B',str(bootstrap_copy),'--config',str(config_path),'--config-sha256',sha(read(config_path))]
        json_new(case/'outer-command.json',command)
        # Exact proven private_desktop owns and kills its complete child tree.
        private_path=studio/'tools/private_desktop.py';need(sha(read(private_path))==PRIVATE_SHA,'PRIVATE_SOURCE_PIN')
        outer_receipt=case/'outer-private.json';outer_closed=False;outer_attempted=True
        outer_command=[runtime['pythonw'],'-B','-s',str(private_path),'--receipt',str(outer_receipt),'--timeout','420','--memory-limit-mib','4096','--',*command]
        json_new(case/'outer-private-command.json',outer_command)
        outer_row={'name':'owned-verifier-tree','reaped':False,'private_job_required':True,'private_job_closed':False,'desktop_closed':False};result['jobs'].append(outer_row)
        process=None
        try:
            with (case/'outer-stdout.log').open('xb') as out,(case/'outer-stderr.log').open('xb') as err:
                process=subprocess.Popen(outer_command,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
                OWNED.append((process,outer_row));json_new(case/'outer-launch.json',{'pid':process.pid,'receipt':str(outer_receipt)})
                process.wait(timeout=450)
        finally:
            if process is not None:outer_row['reaped']=reap(process)
        code=process.returncode
        proof=parse(read(outer_receipt,limit=1024*1024));outer_closed=proof.get('job_closed') is True and proof.get('desktop_closed') is True
        need(outer_closed,'OUTER_PRIVATE_CLOSURE_UNPROVEN')
        need(proof.get('child_desktop_confirmed') is True and proof.get('private_window_seen') is True and proof.get('foreground_child_observed') is False and proof.get('desktop_switch_requested') is False,'OUTER_REAL_HIDDEN_PLACEMENT_REQUIRED')
        placement=parse(read(case/'outer-placement.json',limit=1024*1024));policy=placement.get('policy',{})
        need(placement.get('worker_verified_hidden_sentinel_closed') is True and placement.get('placement_is_for_root_python_preparer') is True and policy.get('format')=='has_hidden_background_desktop_placement_sentinel_1' and policy.get('class')=='STATIC' and policy.get('requested_size_pixels')==[0,0],'OUTER_SENTINEL_POLICY_REQUIRED')
        for key in ['disabled','noactivate_style','toolwindow_style','owned_pid_and_thread_verified','destroyed_in_finally']:need(policy.get(key) is True,'OUTER_SENTINEL_POLICY_REQUIRED')
        for key in ['visible_at_creation','visible_before_destruction','show_or_activation_calls','thread_desktop_switch_calls']:need(policy.get(key) is False,'OUTER_SENTINEL_POLICY_REQUIRED')
        worker_result=parse(read(case/'WORKER_RESULT.json',limit=8*1024*1024));result['worker']=worker_result
        need(code==0 and proof.get('exit')==0 and worker_result.get('status')=='PASS','OWNED_VERIFIER_REFUSED')
        need(worker_result.get('all_owned_launchers_reaped') is True and worker_result.get('all_private_jobs_closed') is True and worker_result.get('all_worker_read_inputs_preserved') is True,'WORKER_CLOSURE_OR_PRESERVATION')
        plans=audit_plan_file(case/'smoke/native-plans.json',fixture_document,studio,fixtures)
        result.update(status='PASS',checks=worker_result['checks'],failures=0,native_profiles_observed=len(plans),video=worker_result['video'],
            stage=str(stage),existing_verifier_completed=True,parent_environment_mutated=False,hidden_root_sentinel_verified=True)
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__;result['error_code']=str(error) if type(error) is Refusal else 'DEFAULT_OFF_GPU_COORDINATOR_EXCEPTION'
    finally:
        if outer_attempted:
            try:
                proof=parse(read(outer_receipt,limit=1024*1024));outer_closed=proof.get('job_closed') is True and proof.get('desktop_closed') is True
                if outer_row is not None:outer_row.update(private_job_closed=proof.get('job_closed') is True,desktop_closed=proof.get('desktop_closed') is True)
            except BaseException:outer_closed=False
        result['outer_private_job_closed']=outer_closed
        result['parent_environment_unchanged']=dict(os.environ)==parent_environment
        for process,row in OWNED:row['reaped']=reap(process)
        result['all_owned_launchers_reaped']=all(row['reaped'] for _p,row in OWNED)
        result['all_private_jobs_closed']=all(row['private_job_closed'] and row['desktop_closed'] for _p,row in OWNED)
        failures=preserve();result['all_admitted_inputs_preserved']=not failures;result['preservation_failures']=failures;result['admitted_inputs']=len(EXPECTED)
        try:result['head_unchanged']=head()==REVISION
        except BaseException:result['head_unchanged']=False
        closure=outer_closed and result['all_owned_launchers_reaped'] and result['all_private_jobs_closed'];result['owned_lock_removed']=False
        if lane_fd is not None:
            try:
                need(closure and stamp(os.fstat(lane_fd))==lane_identity and stamp(lane.lstat())==lane_identity,'OWNED_LOCK_RETAINED_FOR_UNPROVEN_CLOSURE')
                os.lseek(lane_fd,0,os.SEEK_SET);need(os.read(lane_fd,128)==token,'OWNED_LOCK_CHANGED');os.close(lane_fd);lane_fd=None
                need(stamp(lane.lstat())==lane_identity,'OWNED_LOCK_PATH_CHANGED');lane.unlink();result['owned_lock_removed']=True
            except BaseException as error:result['lock_error_type']=type(error).__name__
            finally:
                if lane_fd is not None:os.close(lane_fd)
        if failures or not closure or not result['head_unchanged'] or not result['parent_environment_unchanged'] or not result['owned_lock_removed']:result['status']='FAIL'
        result['owned_lock_retained']=not result['owned_lock_removed'] and lane_identity is not None
        if stage_owned:
            json_new(stage/'PUBLIC_DEFAULT_OFF_GPU_RESULT.json',result)
            print(json.dumps({'status':result['status'],'checks':result.get('checks'),'native_profiles_observed':result.get('native_profiles_observed'),
                'error_code':result.get('error_code'),'result':str(stage/'PUBLIC_DEFAULT_OFF_GPU_RESULT.json')}),flush=True)
    return 0 if result['status']=='PASS' and primary is None else 1

if __name__=='__main__':raise SystemExit(main())
