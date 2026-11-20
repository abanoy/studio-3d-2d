"""Root-only empty-request Blender library census on a byte-identical owned B.

The unchanged published coordinator supplies full/source/runtime/physical guards.
No SourceIO import, material request, geometry relabelling, export or save.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GUARD = ROOT / 'experiments/source_current_native_ids_20261120/run_probe.py'
GUARD_PIN = (51728, 'f9bc228e02f3097548fad9ed1e83bc7c3d475abc40c088cd3c236e91f1dbf324')
SUPPORT = ROOT / 'experiments/source_current_native_ids_20261120/fresh_current_id_probe.py'
SUPPORT_PIN = (35572, 'd78369585463dcc2a511e00889f7e768e10c61004cf4f3fac0df3885b7d60c93')
SENTINEL = ROOT / 'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py'
SENTINEL_PIN = (17989, '034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
ORIGINAL = ROOT.parent / 'has-acceptance-session-20261111/output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685/editable.blend'
BLEND_PIN = (2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def guard_module():
    raw = GUARD.read_bytes()
    if len(raw) != GUARD_PIN[0] or sha(raw) != GUARD_PIN[1]:
        raise ValueError('PUBLISHED_GUARD_IDENTITY_DIFFERS')
    spec = importlib.util.spec_from_file_location('has_library_guard_f9bc', GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-lane-confirmed', action='store_true')
    parser.add_argument('--driver-sha256', required=True)
    parser.add_argument('--worker-sha256', required=True)
    args = parser.parse_args()
    guard = guard_module()
    guard.need(args.root_lane_confirmed and sys.dont_write_bytecode, 'ROOT_LANE_AND_NO_BYTECODE_REQUIRED')
    own_raw, own_row, own_stamp = guard.read_checked(Path(__file__))
    guard.need(sha(own_raw) == args.driver_sha256, 'ROOT_LIBRARY_DRIVER_DIFFERS')
    context = {'root_lane_confirmed': True}
    proof = {}
    full = ROOT / 'output' / guard.FULL_NAME
    for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'),
                      ('before', 'source-before.json'), ('after', 'source-after.json'),
                      ('committed', 'committed-source-blobs.json')):
        context[key], proof[key] = guard.json_read(full / name)
    guard.validate_full(context)
    guard.need(guard.source_snapshot(context['after']) == context['after'], 'SOURCE_SNAPSHOT_DIFFERS')
    initial_git = guard.git_proof()
    guard.validate_git(initial_git, context)
    guard.need(proof['completion']['mtime_ns'] >= context['launch']['started_ns'] and
               proof['after']['mtime_ns'] >= context['launch']['started_ns'], 'FULL_PROOFS_PREDATE_LAUNCH')
    lock_path = ROOT / 'output/source-current-id-root-lane.lock'
    guard.safe(lock_path, exists=False)
    lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    lock_stamp = None
    stage = None
    process = None
    launcher_reaped = closure_confirmed = False
    launched = False
    before = {}
    runtimes = {}
    sources = {}
    try:
        os.write(lock_fd, (str(os.getpid())+'\n').encode('ascii'))
        lock_stamp = guard.stamp(os.fstat(lock_fd))
        stage = ROOT / 'output' / ('source-library-enumeration-run-'+str(time.time_ns()))
        guard.safe(stage, exists=False)
        stage.mkdir()
        for name in ('inputs', 'result', 'temp', 'user-config', 'user-scripts', 'user-datafiles', 'home'):
            (stage/name).mkdir()
        def runtime_reader():
            runtimes.update(guard.runtime_check(ROOT/guard.LOCK_REL))
            return runtimes
        admitted = guard.admit(context, source_reader=lambda: guard.source_snapshot(context['after']),
                               git_reader=guard.git_proof,
                               physical_reader=lambda: guard.observe_physical(stage, context['launch'], 'BEFORE'),
                               runtime_reader=runtime_reader)
        raw, original, original_stamp = guard.read_checked(ORIGINAL, BLEND_PIN)
        owned = stage/'inputs/material-source.blend'
        with owned.open('xb') as stream:
            stream.write(raw)
        os.utime(owned, ns=(ORIGINAL.stat().st_atime_ns, original['mtime_ns']))
        _, owned_row, owned_stamp = guard.read_checked(owned, BLEND_PIN)
        guard.need(owned_row == original, 'OWNED_B_COPY_DIFFERS')
        for role, path, pin in (('probe', HERE/'library_worker.py', None), ('support_worker', SUPPORT, SUPPORT_PIN),
                                ('sentinel', SENTINEL, SENTINEL_PIN), ('blend', owned, BLEND_PIN),
                                ('blender_exe', guard.BLENDER, guard.RUNTIME_PINS[str(guard.BLENDER)])):
            raw, row, identity = guard.read_checked(path, pin)
            if role == 'probe':
                guard.need(sha(raw) == args.worker_sha256, 'LIBRARY_WORKER_IDENTITY_DIFFERS')
            sources[role] = dict(path=str(path), bytes=row['bytes'], sha256=row['sha256'])
            before[role] = (row, identity)
        graphics = dict(format='has_B_library_enumeration_root_release_1', full_suite_passed=True,
                        tested_revision=guard.TESTED, current_head=admitted['head'], functional_file_count=guard.COUNT,
                        exact_source_hash_bytes_nsmtime=True, full_job_physically_closed=True,
                        root_lane_explicitly_confirmed=True, exclusive_runtime_lease=True,
                        physical_observation_is_global_lease=False,
                        full_completion_sha256=proof['completion']['sha256'],
                        observed_ns=admitted['physical']['observed_ns'], scope='EMPTY_LIBRARY_REQUESTS_ONLY')
        graphics_row = guard.write_new(stage/'graphics-release.json', graphics)
        guard.write_new(stage/'physical-closure.json', admitted['physical'])
        sources['full_completion'] = dict(path=str(full/'completion.json'), bytes=proof['completion']['bytes'],
                                          sha256=proof['completion']['sha256'])
        sources['graphics_release'] = {key: graphics_row[key] for key in ('path','bytes','sha256')}
        now = dt.datetime.now(dt.timezone.utc)
        request = dict(format='has_owned_B_empty_library_census_request_1',
                       phase='ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED', created_utc=now.isoformat(),
                       expires_utc=(now+dt.timedelta(minutes=30)).isoformat(), private_arrays_public=False,
                       owned_stage=str(stage), owned_output=str(stage/'result'), owned_temp=str(stage/'temp'), files=sources,
                       source_context=dict(full_suite_passed=True, full_job_physically_closed=True,
                                           exclusive_runtime_lease=True, observed_owned_processes=0,
                                           functional_file_count=guard.COUNT, tested_revision=guard.TESTED,
                                           full_completion_sha256=proof['completion']['sha256'],
                                           graphics_release_sha256=graphics_row['sha256']))
        request_row = guard.write_new(stage/'ROOT_REQUEST.json', request)
        guard.write_new(stage/'PRIVATE_BEFORE.json', dict(original=original, owned=owned_row, runtime=runtimes,
                                                         proof=proof, driver=own_row, sources=sources, git=initial_git))
        env = os.environ.copy()
        for key in ('PYTHONPATH','PYTHONHOME','BLENDER_SYSTEM_SCRIPTS','BLENDER_SYSTEM_DATAFILES','BLENDER_SYSTEM_PYTHON'):
            env.pop(key, None)
        env.update(TEMP=str(stage/'temp'), TMP=str(stage/'temp'), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                   BLENDER_USER_CONFIG=str(stage/'user-config'), BLENDER_USER_SCRIPTS=str(stage/'user-scripts'),
                   BLENDER_USER_DATAFILES=str(stage/'user-datafiles'), HOME=str(stage/'home'), USERPROFILE=str(stage/'home'))
        command=[str(guard.PYTHONW),'-B',str(ROOT/'tools/private_desktop.py'),'--receipt',str(stage/'private-desktop.json'),
                 '--timeout','150','--memory-limit-mib','4096','--',str(guard.BLENDER),'--background','--factory-startup',
                 '--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(HERE/'library_worker.py'),
                 '--','--request',str(stage/'ROOT_REQUEST.json'),'--request-sha256',request_row['sha256']]
        guard.need(guard.source_snapshot(context['after'])==context['after'] and guard.git_proof()==initial_git,
                   'PRELAUNCH_SOURCE_OR_HEAD_CHANGED')
        guard.observe_physical(stage, context['launch'], 'PRELAUNCH')
        with (stage/'PRIVATE_stdout.log').open('xb') as out, (stage/'PRIVATE_stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            launched=True
            guard.wait_recorded_owned(process, lambda: guard.write_new(stage/'PRIVATE_launch.json',
                dict(pid=process.pid,coordinator_pid=os.getpid(),started_ns=time.time_ns(),args=command)))
        launcher_reaped=process.poll() is not None
        desktop,desktop_row=guard.json_read(stage/'private-desktop.json')
        guard.need(type(desktop.get('child_pid')) is int and desktop['child_pid']>0, 'PRIVATE_CHILD_PID_REQUIRED')
        physical=guard.observe_physical(stage,dict(pid=process.pid,coordinator_pid=context['launch']['coordinator_pid'],
                     extra_absent_pids=[desktop['child_pid'],context['launch']['pid']]),'AFTER')
        guard.validate_fresh_physical(physical)
        closure_confirmed=True
        def preservation():
            guard.need(guard.source_snapshot(context['after'])==context['after'] and guard.git_proof()==initial_git,
                       'POST_SOURCE_OR_HEAD_CHANGED')
            guard.need(guard.runtime_check(ROOT/guard.LOCK_REL)==runtimes,'POST_RUNTIME_CHANGED')
            for path, pin, row, stamp in ((ORIGINAL,BLEND_PIN,original,original_stamp),(owned,BLEND_PIN,owned_row,owned_stamp)):
                _,after,identity=guard.read_checked(path,pin)
                guard.need(after==row and identity==stamp,'ORIGINAL_OR_OWNED_B_CHANGED')
            for role,(row,identity) in before.items():
                _,after,after_stamp=guard.read_checked(sources[role]['path'],(row['bytes'],row['sha256']))
                guard.need(after==row and after_stamp==identity,'LIBRARY_PROBE_INPUT_CHANGED')
            _,after,after_stamp=guard.read_checked(Path(__file__),(len(own_raw),args.driver_sha256))
            guard.need(after==own_row and after_stamp==own_stamp,'ROOT_DRIVER_CHANGED')
            for key,name in (('completion','completion.json'),('launch','launch.json'),('before','source-before.json'),
                             ('after','source-after.json'),('committed','committed-source-blobs.json')):
                _,identity=guard.json_read(full/name)
                guard.need(identity==proof[key],'FULL_PROOF_CHANGED')
            return True
        preservation()
        for key in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'):
            guard.need(desktop.get(key) is True,'PRIVATE_'+key.upper())
        guard.need(process.returncode==0 and desktop.get('exit')==0 and desktop.get('job_memory_limit_bytes')==4096*1024*1024 and
                   desktop.get('foreground_child_observed') is False and desktop.get('desktop_switch_requested') is False and
                   not any(key in desktop for key in ('error','monitor_error','desktop_enumeration_error','cancelled')),
                   'PRIVATE_LIBRARY_JOB_FAILED')
        worker,worker_row=guard.json_read(stage/'result/PUBLIC_LIBRARY_ENUMERATION.json',64*1024)
        placement,placement_row=guard.json_read(stage/'result/PLACEMENT_LIBRARY_ENUMERATION.json',64*1024)
        guard.need(worker.get('status')=='ENUMERATED_WITH_EMPTY_REQUESTS_AND_UNCHANGED_ID_CENSUS' and
                   worker.get('all_read_inputs_hash_size_stamp_unchanged') is True and worker.get('hidden_placement_verified') is True,
                   'LIBRARY_WORKER_NOT_QUALIFIED')
        for key in ('original_B_scene_opened','material_append_requested','image_pixels_read','blend_saved','exporter_invoked','native_arrays_published'):
            guard.need(worker.get(key) is False,'LIBRARY_SCOPE_'+key.upper())
        expected={role:{key:row[key] for key in ('bytes','sha256')} for role,row in sources.items()}
        expected['root_request']={key:request_row[key] for key in ('bytes','sha256')}
        guard.need(worker.get('input_identities')==expected and len(expected)==8,'EXACT_LIBRARY_WORKER_READS')
        summary=worker.get('summary')
        guard.need(type(summary) is dict and summary.get('all_destination_requests_empty') is True and
                   summary.get('actual_id_census_unchanged') is True and summary.get('source_materials')==4,
                   'EXACT_LIBRARY_EMPTY_CENSUS_RESULT')
        guard.need(placement.get('worker_verified_hidden_sentinel_closed') is True,'LIBRARY_SENTINEL_NOT_CLOSED')
        policy=placement.get('policy')
        guard.need(type(policy) is dict and policy.get('destroyed_in_finally') is True and
                   policy.get('visible_at_creation') is False and policy.get('visible_before_destruction') is False and
                   policy.get('owned_pid_and_thread_verified') is True and policy.get('show_or_activation_calls') is False and
                   policy.get('thread_desktop_switch_calls') is False,'LIBRARY_SENTINEL_POLICY')
        result=dict(format='has_root_owned_B_empty_library_census_1',status='EMPTY_LIBRARY_ENUMERATION_QUALIFIED',
                    tested_revision=guard.TESTED,current_source_head=initial_git['head'],functional_source_count=guard.COUNT,
                    worker_reads=8,private_job_closed=True,launcher_reaped=True,physical_after=physical,
                    source_runtime_original_and_owned_hash_size_nsmtime_unchanged=True,
                    material_append_requested=False,old_B_point_identity_qualified=False,normal_fidelity_qualified=False,
                    dependency_closure_qualified=False,exporter_qualified=False,application_adoption_qualified=False,
                    summary=summary,worker_result=worker_row,placement_result=placement_row,desktop_result=desktop_row)
        guard.write_new(stage/'PUBLIC_ROOT_RESULT.json',result)
        print(json.dumps(dict(status=result['status'],folder=stage.name,summary=summary)))
        return 0
    except BaseException as error:
        if process is not None:
            launcher_reaped=guard.reap_owned_launcher(process)
        if stage is not None:
            try:
                launch=dict(pid=process.pid if process is not None else context['launch']['pid'],
                            coordinator_pid=context['launch']['coordinator_pid'])
                receipt=stage/'private-desktop.json'
                if receipt.exists():
                    value,_=guard.json_read(receipt)
                    if type(value.get('child_pid')) is int:
                        launch['extra_absent_pids']=[value['child_pid'],context['launch']['pid']]
                observed=guard.observe_physical(stage,launch,'FAILURE')
                guard.validate_fresh_physical(observed)
                closure_confirmed=not launched or launcher_reaped
            except BaseException:
                observed=None
            audit=dict(format='has_owned_B_library_failed_run_1',status='FAILED',
                       error_type=type(error).__name__,error_code=str(error) if isinstance(error,guard.Refusal) else type(error).__name__,
                       launched=launched,launcher_reaped=launcher_reaped,physical_closure_confirmed=closure_confirmed,
                       physical_after=observed,owned_lock_retained=not closure_confirmed,
                       normal_fidelity_qualified=False,application_adoption_qualified=False)
            try: guard.write_new(stage/'PUBLIC_FAILED_RUN.json',audit)
            except BaseException: pass
            print(json.dumps(audit))
        else:
            print(json.dumps(dict(status='FAILED_BEFORE_STAGE',error_type=type(error).__name__)))
        return 1
    finally:
        if process is not None and process.poll() is None:
            guard.reap_owned_launcher(process)
        os.close(lock_fd)
        if closure_confirmed or not launched:
            guard.need(guard.stamp(lock_path.lstat())==lock_stamp,'OWNED_LIBRARY_LOCK_CHANGED')
            lock_path.unlink()

if __name__=='__main__':
    raise SystemExit(main())
