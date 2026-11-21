"""Root-only live-VMT candidate integration; no author execution.

Reuses the unchanged qualified V11 coordinator functions. No B scene request.
Only a fresh owned stage and the one retained private Blender job are mutated.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / 'output/source-material-carrier-host-v11-prep-20261120/run_carrier.py'
DRIVER_PIN = (87748, '75daf466f6fe0265088c4cf9efaeb2a3722b8062bf987620a5216529e7c9c51a')
WORKER = DRIVER.with_name('fresh_carrier_probe.py')
WORKER_PIN = (72518, '2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea')


def driver():
    raw = DRIVER.read_bytes()
    if (len(raw), hashlib.sha256(raw).hexdigest()) != DRIVER_PIN:
        raise ValueError('EXACT_QUALIFIED_DRIVER_REQUIRED')
    spec = importlib.util.spec_from_file_location('_live_qualified_v11_driver', DRIVER)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    exec(compile(raw, str(DRIVER), 'exec', dont_inherit=True), module.__dict__)
    module.read_checked(DRIVER, DRIVER_PIN)
    return module


BOOTSTRAP = r'''import hashlib,importlib.util,json,runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
config=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf8'))
def pinned(path,count,digest):
    raw=Path(path).read_bytes()
    if len(raw)!=count or hashlib.sha256(raw).hexdigest()!=digest: raise ValueError('LIVE_CHILD_SOURCE_PIN_DIFFERS')
    return raw
worker_path=config['worker']['path']
raw=pinned(worker_path,config['worker']['bytes'],config['worker']['sha256'])
spec=importlib.util.spec_from_file_location('_live_placement_source',worker_path)
W=importlib.util.module_from_spec(spec);sys.modules[spec.name]=W
exec(compile(raw,worker_path,'exec',dont_inherit=True),W.__dict__)
sentinel=pinned(config['sentinel']['path'],config['sentinel']['bytes'],config['sentinel']['sha256'])
pinned(config['candidate']['path'],config['candidate']['bytes'],config['candidate']['sha256'])
placement=None
try:
    with W.placement_sentinel(sentinel.decode('utf8'))() as placement:
        import bpy
        if bpy.app.background is not True or bpy.app.online_access is not False or bpy.context.preferences.filepaths.use_scripts_auto_execute is not False:
            raise ValueError('LIVE_FACTORY_OFFLINE_CONTEXT_REQUIRED')
        sys.path.insert(0,config['tools']);sys.path.insert(0,str(Path(config['candidate']['path']).parent))
        sys.argv=[config['candidate']['path'],'--',config['conversion_request']]
        runpy.run_path(config['candidate']['path'],run_name='__main__')
finally:
    result={'format':'has_live_normal_hidden_placement_1','policy':placement,
            'worker_verified_hidden_sentinel_closed':placement is not None and placement.get('destroyed_in_finally') is True}
    with Path(config['placement']).open('x',encoding='utf8') as stream:json.dump(result,stream,sort_keys=True)
'''


def validate_placement(D, value):
    D.need(value.get('format') == 'has_live_normal_hidden_placement_1' and
           value.get('worker_verified_hidden_sentinel_closed') is True, 'LIVE_PLACEMENT_REQUIRED')
    policy = value['policy']
    D.need(policy.get('format') == 'has_hidden_background_desktop_placement_sentinel_1' and
           policy.get('class') == 'STATIC' and policy.get('requested_size_pixels') == [0, 0], 'LIVE_SENTINEL_REQUIRED')
    for key in ('disabled','noactivate_style','toolwindow_style','owned_pid_and_thread_verified','destroyed_in_finally'):
        D.need(policy.get(key) is True, 'LIVE_SENTINEL_' + key)
    for key in ('visible_at_creation','visible_before_destruction','show_or_activation_calls','thread_desktop_switch_calls'):
        D.need(policy.get(key) is False, 'LIVE_SENTINEL_' + key)


def validate_bundle(D, stage):
    artifacts = {}
    for role, filename in (('scene_glb','scene.glb'),('parameters_json','parameters.json'),
                           ('editable_blend','editable.blend'),('dependencies_json','dependencies.json'),('carrier_glb','carrier.glb')):
        raw, row, _ = D.read_checked(stage / 'result' / filename, limit=128*1024*1024)
        artifacts[role] = dict(path=str(stage / 'result' / filename), **row)
        if role == 'parameters_json': parameters = D.strict_json(raw)
    native = parameters['native_parameters']; normal = parameters['native_normal_export']
    final = normal['normal_finalization']; measured = final['measurement']
    D.need(normal['status'] == 'LIVE_NORMAL_DERIVATIVE_CANDIDATE_COMPLETE' and normal['saved_B_opened'] is False and
           normal['one_operator_invocation'] is True and normal['raw_carrier_retained'] is True and
           normal['metadata_writes_to_live_materials'] is False and normal['final_glb_sha256'] == artifacts['scene_glb']['sha256'],
           'LIVE_FINALIZATION_REQUIRED')
    D.need(final['final_glb_sha256'] == artifacts['scene_glb']['sha256'] and
           final['raw_carrier_sha256'] == artifacts['carrier_glb']['sha256'] and
           final['final_checksum_bound_by_preservation'] is True and final['original_raw_bone_proof_unchanged'] is True and
           final['raw_hook_observed_corrected_bytes'] is False, 'LIVE_FINAL_BONE_REBIND_REQUIRED')
    D.need(measured['measured'] is True and measured['passed'] is True and
           measured['source_normal_metric'] == 'raw_unnormalized_euclidean_vector_distance' and
           type(measured['source_normal_threshold']) is float and measured['source_normal_threshold'] == 2e-5 and
           type(measured['source_normal_max_euclidean_error']) is float and measured['source_normal_max_euclidean_error'] == 0.0 and
           measured['source_points'] == measured['exported_normal_rows'] == 9661 and measured['compared_components'] == 28983,
           'LIVE_EXACT_NORMAL_MEASUREMENT_REQUIRED')
    sys.path.insert(0,str(ROOT / 'tools'))
    import source_jiggle_metadata as J
    import source_bone_metadata as B
    bones, jiggle, crosswalk = native['bones'], native['source_jiggle'], native['source_export_crosswalk']
    J._inert(jiggle, bones)
    D.need(len(bones) == 69 and len(jiggle['rules']) == 49 and jiggle['native_bone_count'] == 69,
           'LIVE_69_BONES_49_RULES_REQUIRED')
    D.need(crosswalk['format'] == 'studio_source_bone_crosswalk_1' and crosswalk['status'] == 'retained_inert' and
           crosswalk['native_bone_count'] == 69 and crosswalk['glb_sha256'] == artifacts['scene_glb']['sha256'] and
           crosswalk['proof_sha256'] == D.sha(B.proof_wire_bytes(crosswalk)) and
           crosswalk['jiggle_wire_sha256'] == B.jiggle_wire_sha256(jiggle,bones), 'LIVE_FINAL_CROSSWALK_WIRE_REQUIRED')
    for value in (jiggle, crosswalk):
        D.need(value['original_source_sha256'] == D.NATIVE['mdl'][2] and value['native_mdl_sha256'] == D.NATIVE['mdl'][2],
               'LIVE_NATIVE_METADATA_IDENTITY_REQUIRED')
    return artifacts


def main():
    P=argparse.ArgumentParser();P.add_argument('--root-lane-confirmed',action='store_true')
    P.add_argument('--host-sha256',required=True);P.add_argument('--candidate',type=Path,required=True)
    P.add_argument('--candidate-source-pins-sha256',required=True);P.add_argument('--original-request-sha256',required=True)
    args=P.parse_args();D=driver();D.need(args.root_lane_confirmed,'EXPLICIT_ROOT_LANE_REQUIRED')
    own,ownrow,ownstamp=D.read_checked(Path(__file__));D.need(D.sha(own)==args.host_sha256,'LIVE_HOST_PIN_DIFFERS')
    full=ROOT/'output'/D.FULL_NAME;context={'root_lane_confirmed':True};proofs={}
    for key,name in (('completion','completion.json'),('launch','launch.json'),('before','source-before.json'),
                     ('after','source-after.json'),('committed','committed-source-blobs.json')):
        raw,row,before=D.read_checked(full/name);context[key]=D.strict_json(raw);proofs[key]=(full/name,row,before)
    D.validate_full(context)
    D.need(D.source_snapshot(context['after'])==context['after'],'LIVE_SOURCE_CHANGED_BEFORE_ADMISSION')
    initial_git=D.git_proof();D.validate_git(initial_git,context)
    candidate=D.safe(args.candidate);D.need(candidate.parent==ROOT/'output' and candidate.name.startswith('source-live-normal-bridge-'),
                                          'OWNED_FROZEN_CANDIDATE_REQUIRED')
    manifest,mrow,mstamp=D.read_checked(candidate/'SOURCE_PINS.json')
    D.need(D.sha(manifest)==args.candidate_source_pins_sha256,'LIVE_CANDIDATE_MANIFEST_PIN_DIFFERS')
    candidate_files=D.complete_catalogue(candidate)
    bridge=candidate/'blender_source_bridge_candidate.py'
    D.need('blender_source_bridge_candidate.py' in candidate_files and 'source_native_normal_export.py' in candidate_files,
           'LIVE_CANDIDATE_FILES_REQUIRED')
    original_request=D.OLD/D.FAMILY/'conversion-request.json'
    reqraw,reqrow,reqstamp=D.read_checked(original_request)
    D.need(D.sha(reqraw)==args.original_request_sha256,'ORIGINAL_LIVE_REQUEST_PIN_DIFFERS')
    request=D.strict_json(reqraw);resources=Path(request['original_source']).parents[3]
    D.need(resources.is_relative_to(D.OLD) and resources.name=='family-03' and request['source_profile']=='standalone' and
           request['sha256']==D.NATIVE['mdl'][2] and request['scale']==.01905 and request.get('appearance') is None and
           request.get('source_member') is None and request['mounts']==[str(D.OLD/D.FAMILY/'native'),str(resources)],
           'EXACT_LIVE_ORIGINAL_PROFILE_REQUIRED')
    mount_before=D.complete_catalogue(resources)
    checks={};checks['functional_source']=lambda:D.source_snapshot(context['after'])==context['after']
    checks['head_and_committed_source']=lambda:D.git_proof()==initial_git
    checks['readonly_resource_mount']=lambda:D.complete_catalogue(resources,expected=mount_before)==mount_before
    checks['frozen_candidate']=lambda:D.complete_catalogue(candidate,expected=candidate_files)==candidate_files
    D.register_file_check(checks,'host',Path(__file__),(len(own),args.host_sha256),ownrow,ownstamp)
    D.register_file_check(checks,'qualified_driver',DRIVER,DRIVER_PIN,*D.read_checked(DRIVER,DRIVER_PIN)[1:])
    D.register_file_check(checks,'original_request',original_request,(reqrow['bytes'],reqrow['sha256']),reqrow,reqstamp)
    for key,(path,row,before) in proofs.items():D.register_file_check(checks,'full_'+key,path,(row['bytes'],row['sha256']),row,before)
    protected={}
    for role,(name,count,digest) in {**D.NATIVE,**D.PROVENANCE}.items():
        raw,row,before=D.read_checked(D.OLD/D.FAMILY/name,(count,digest));protected[role]=(raw,row,before)
        D.register_file_check(checks,'protected_original_'+role,D.OLD/D.FAMILY/name,(count,digest),row,before)
    lock=ROOT/'output/source-current-id-root-lane.lock';D.safe(lock,exists=False)
    lockfd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);lockstamp=None;stage=None;process=None
    launched=False;closed=False;success=None;lock_removed=False
    try:
        os.write(lockfd,(str(os.getpid())+'\n').encode());lockstamp=D.stamp(os.fstat(lockfd))
        stage=D.safe(ROOT/'output'/('source-live-normal-run-'+str(time.time_ns())),exists=False)
        D.need(not stage.exists(),'FRESH_LIVE_STAGE_REQUIRED');stage.mkdir()
        for name in ('inputs','result','temp','home','user-config','user-scripts','user-datafiles'):(stage/name).mkdir()
        runtime={}
        def runtime_reader():runtime.update(D.runtime_check(ROOT/D.LOCK_REL));return runtime
        admitted=D.admit(context,source_reader=lambda:D.source_snapshot(context['after']),git_reader=D.git_proof,
                         physical_reader=lambda:D.observe_physical(stage,context['launch'],'BEFORE'),runtime_reader=runtime_reader)
        checks['approved_runtime']=lambda:D.runtime_check(ROOT/D.LOCK_REL)==runtime
        for role,(name,count,digest) in D.NATIVE.items():
            destination=stage/'inputs'/Path(name).name;raw,row,_=protected[role]
            checks['expected_staged_'+role]=lambda p=destination,b=raw:D.read_checked(p)[0]==b
            with destination.open('xb') as stream:stream.write(raw)
            os.utime(destination,ns=(destination.stat().st_atime_ns,row['mtime_ns']))
            _,staged,before=D.read_checked(destination,(count,digest))
            D.register_file_check(checks,'staged_'+role,destination,(count,digest),staged,before)
        request=dict(request,source=str(stage/'inputs'/'junko hair.mdl'),output=str(stage/'result'),sourceio=str(D.SOURCEIO),
                     mounts=[str(stage/'inputs'),str(resources)])
        request_row=D.remember_written_file(checks,'conversion_request',D.write_new(stage/'conversion-request.json',request))
        workerraw,wrow,wstamp=D.read_checked(WORKER,WORKER_PIN)
        D.register_file_check(checks,'placement_helper',WORKER,WORKER_PIN,wrow,wstamp)
        sentinel_name=list(D.HELPERS)[3];sentinel_pin=D.HELPERS[sentinel_name]
        config=dict(worker=dict(path=str(WORKER),bytes=WORKER_PIN[0],sha256=WORKER_PIN[1]),
                    sentinel=dict(path=str(ROOT/sentinel_name),bytes=sentinel_pin[0],sha256=sentinel_pin[1]),
                    candidate=dict(path=str(bridge),bytes=candidate_files[bridge.name]['bytes'],sha256=candidate_files[bridge.name]['sha256']),
                    tools=str(ROOT/'tools'),conversion_request=str(stage/'conversion-request.json'),
                    placement=str(stage/'result/PUBLIC_LIVE_PLACEMENT.json'))
        D.remember_written_file(checks,'bootstrap_config',D.write_new(stage/'ROOT_LIVE_BOOTSTRAP.json',config))
        boot=stage/'live_bootstrap.py'
        with boot.open('xb') as stream:stream.write(BOOTSTRAP.encode())
        _,br,bs=D.read_checked(boot);D.register_file_check(checks,'bootstrap',boot,(br['bytes'],br['sha256']),br,bs)
        env=os.environ.copy()
        for key in ('PYTHONPATH','PYTHONHOME','BLENDER_SYSTEM_SCRIPTS','BLENDER_SYSTEM_DATAFILES','BLENDER_SYSTEM_PYTHON'):env.pop(key,None)
        env.update(TEMP=str(stage/'temp'),TMP=str(stage/'temp'),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
                   BLENDER_USER_CONFIG=str(stage/'user-config'),BLENDER_USER_SCRIPTS=str(stage/'user-scripts'),
                   BLENDER_USER_DATAFILES=str(stage/'user-datafiles'),HOME=str(stage/'home'),USERPROFILE=str(stage/'home'))
        command=[str(D.PYTHONW),'-B',str(ROOT/'tools/private_desktop.py'),'--receipt',str(stage/'private-desktop.json'),
                 '--timeout','180','--memory-limit-mib','4096','--',str(D.BLENDER),'--background','--factory-startup',
                 '--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(boot),'--',str(stage/'ROOT_LIVE_BOOTSTRAP.json')]
        D.need(all(check() is True for check in checks.values()),'LIVE_PRELAUNCH_PRESERVATION')
        D.observe_physical(stage,context['launch'],'PRELAUNCH')
        with (stage/'PRIVATE_stdout.log').open('xb') as out,(stage/'PRIVATE_stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=stage,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                                     creationflags=subprocess.CREATE_NO_WINDOW);launched=True
            D.wait_recorded_owned(process,lambda:D.write_new(stage/'PRIVATE_launch.json',dict(pid=process.pid,
                coordinator_pid=os.getpid(),started_ns=time.time_ns(),command=command,visible_fallback=False)))
        desktop,_=D.json_read(stage/'private-desktop.json',64*1024)
        physical=D.observe_physical(stage,dict(pid=process.pid,coordinator_pid=context['launch']['coordinator_pid'],
            extra_absent_pids=[desktop['child_pid'],context['launch']['pid']]),'AFTER');D.validate_fresh_physical(physical);closed=True
        D.need(process.returncode==0 and desktop.get('exit')==0,'LIVE_CONVERSION_JOB_FAILED')
        for key in ('job_closed','desktop_closed','child_desktop_confirmed','private_window_seen'):D.need(desktop.get(key) is True,'LIVE_PRIVATE_'+key)
        D.need(desktop.get('foreground_child_observed') is False and desktop.get('desktop_switch_requested') is False,
               'LIVE_PRIVATE_VISIBILITY_REQUIRED')
        placement,_=D.json_read(stage/'result/PUBLIC_LIVE_PLACEMENT.json');validate_placement(D,placement)
        artifacts=validate_bundle(D,stage)
        D.need(all(check() is True for check in checks.values()),'LIVE_POSTRUN_PRESERVATION')
        success=dict(format='has_source_live_native_normal_root_result_1',status='LIVE_VMT_NORMALS_BONES_AND_PARAMETERS_MATCHED',
            source_head=initial_git['head'],tested_full_revision=D.TESTED,functional_source_files=1061,
            models=2,points=9661,bones=69,jiggle_rules=49,final_normal_max_euclidean_error=0.0,
            source_normal_threshold=2e-5,final_parameters_crosswalk_bound=True,artifacts=artifacts,
            all_source_runtime_native_and_mount_preservation_checks_passed=True,
            readonly_mount_files=len(mount_before),readonly_mount_catalogue_sha256=D.sha(json.dumps(mount_before,sort_keys=True).encode()),
            private_job_closed=True,physical_owned_processes=0,foreground_activation=False,
            retained_launcher_reaped=True,application_adoption_qualified=False,B_loaded_in_Blender=False)
    finally:
        primary=sys.exc_info()[1];audit=None
        if primary is not None and stage is not None:
            reaped=process is not None and D.reap_owned_launcher(process)
            audit=D.failed_run_audit(checks,primary_error=primary,launcher_reaped=reaped,
                native_launch_attempted=launched,worker_receipt_present=(stage/'private-desktop.json').is_file(),
                closure_observer=lambda:D.observe_physical(stage,dict(pid=process.pid if process else context['launch']['pid'],
                    coordinator_pid=context['launch']['coordinator_pid'],extra_absent_pids=[context['launch']['pid']]),'FAILED'))
            closed=audit['physical_closure_confirmed']
        os.close(lockfd)
        if lockstamp is not None and (not launched or closed):
            D.safe(lock);D.need(D.stamp(lock.lstat())==lockstamp,'LIVE_OWNED_LOCK_CHANGED');lock.unlink();lock_removed=True
        if audit is not None:
            audit.update(owned_lock_retained=not lock_removed,owned_lock_cleanup_refused=not lock_removed)
            D.write_new(stage/'PUBLIC_LIVE_NORMAL_FAILED_PRESERVATION.json',audit)
    D.need(success is not None and closed and lock_removed,'LIVE_SUCCESS_AFTER_CLOSURE_REQUIRED')
    success['owned_lock_removed']=True
    D.write_new(stage/'PUBLIC_LIVE_NORMAL_ROOT_RESULT.json',success)
    print(json.dumps(dict(status=success['status'],stage=str(stage),scene_sha256=success['artifacts']['scene_glb']['sha256'])),flush=True)


if __name__=='__main__':
    main()
