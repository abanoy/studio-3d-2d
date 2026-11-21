"""Root-only headless synthetic171 checks. SOURCE ONLY, UNRUN.
No Full checkout access, native asset inputs, converter, or graphical jobs.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import time
import uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REVISION='435dc02426a7cdd313e43fe674c9008520845428'
Q_PIN=(21967,'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
S_PIN=(11065,'097ce9c7ea92ecedf6c950a26be6ed680dbd006c69690352a110bc350811d59e')
INPUT_PIN=(4916,'172943e4a47b6e3f832e2ede6b4c8b39040dd355f90e5066b62d47757b6c3ef7')

def identity(info):
    # Access-time changes caused by reading are deliberately excluded.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink, info.st_mode, getattr(info, 'st_file_attributes', 0))


def source_module(name, path, pin):
    for part in reversed((path, *path.parents)):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError('SOURCE_HELPER_ALIAS')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != pin[0]:
        raise RuntimeError('SOURCE_HELPER_REGULAR_PIN')
    raw = path.read_bytes()
    if identity(before) != identity(path.lstat()) or len(raw) != pin[0] or hashlib.sha256(raw).hexdigest() != pin[1]:
        raise RuntimeError('SOURCE_HELPER_IDENTITY_OR_BYTES')
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256',required=True)
    parser.add_argument('--root-headless-only-confirmed',action='store_true',required=True)
    options=parser.parse_args()
    Q=source_module('_miku171_owned_helpers',HERE/'qualified_ui_host.py',Q_PIN)
    H,_=Q.load_pinned('_miku171_process_helpers',HERE/'qualified_helpers.py',*Q.HELPER_PIN)
    S,_=Q.load_pinned('_miku171_source1102',HERE/'source1102.py',*S_PIN)
    H.need(H.ROOT==ROOT and os.name=='nt' and sys.version_info[:2]==(3,13)
           and not sys.flags.optimize and options.root_headless_only_confirmed,'ROOT_WINDOWS313_HEADLESS_ONLY')
    H.need(re.fullmatch('[0-9a-f]{64}',options.self_sha256) is not None,'SELF_PIN_REQUIRED')
    H.read(Path(__file__),digest=options.self_sha256)
    inputs=H.parse(H.read(HERE/'INPUT_PINS.json',*INPUT_PIN))
    H.need(inputs.get('format')=='has_miku_pure171_source_inputs_1' and inputs.get('revision')==REVISION
           and len(inputs.get('targets',[]))==11 and inputs.get('full_qualification_used') is False
           and inputs.get('native_contact_allowed') is False and inputs.get('arraymesh_conformance_allowed') is False
           and inputs.get('owner_project_inputs_allowed') is False,'EXACT_SYNTHETIC_ONLY_SOURCE_DOMAIN')
    for row in inputs['files']:H.read(HERE/H.rel(row['path']),row['bytes'],row['sha256'])
    H.need(H.head()==REVISION,'PUBLICATION_HEAD_CHANGED')
    baseline=S.admit_main(H,ROOT,HERE)
    frozen=S.minimal_runtime(H,ROOT,HERE,baseline,inputs['targets'])
    H.need(len(frozen)==61,'EXACT_MINIMAL61_SOURCE_PROJECT')
    lock=H.parse(H.read(H.LOCK,digest=H.LOCK_SHA));runtime=lock['runtime_paths']
    H.need(len(lock['runtime_executables'])==6,'SIX_APPROVED_EXISTING_EXECUTABLE_PINS')
    used_executables=(runtime['python'],runtime['pythonw'],runtime['godot'])
    H.need(len(set(used_executables))==3 and all(path in lock['runtime_executables'] for path in used_executables),'THREE_DECLARED_USED_EXECUTABLES')
    for path in used_executables:
        row=lock['runtime_executables'][path]
        H.read(path,row['bytes'],row['sha256'],limit=1024*1024*1024)
        H.need(Path(path).lstat().st_mtime_ns==row['mtime_ns'],'RUNTIME_STAMP_CHANGED')
    H.need(Path(sys.executable).resolve()==Path(runtime['python']).resolve(),'APPROVED_PYTHON')
    stage=ROOT.parent/('has-miku-pure171-'+str(time.time_ns()));H.safe(stage,missing=True)
    lane=ROOT/'output/source-miku-pure171.lock';token=uuid.uuid4().hex.encode()
    fd=None;lane_identity=None;stage_owned=False;primary=None
    parent_environment=dict(os.environ)
    result={'format':'has_miku_headless_synthetic171_1','status':'FAIL','revision':REVISION,
            'current_functional_source_count':1102,'minimal_gd_source_files':59,'production_gd_dependencies':48,
            'owned_runtime_files':len(frozen),'new_synthetic_source_targets':11,
            'full_qualification_used':False,'Full1102_claimed':False,'owner_project_inputs_read':False,
            'reserved_full_checkout_accessed':False,'native_contact_launched':False,'arraymesh_conformance_launched':False,
            'graphical_jobs_allowed':False,'editor_import_launched':False,'actual_contact_qualified':False,'application_adopted':False,
            'private_arrays_published':False,'jobs':[],'cases':[]}
    try:
        H.safe(lane,missing=True);fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(fd,token)==len(token),'OWNED_LOCK_SHORT_WRITE');os.fsync(fd);lane_identity=H.stamp(os.fstat(fd))
        stage.mkdir(exist_ok=False);stage_owned=True;studio=stage/'Studio';studio.mkdir();(stage/'Verification').mkdir()
        for name,raw in frozen.items():
            target=studio/H.rel(name);target.parent.mkdir(parents=True,exist_ok=True);H.new(target,raw)
        (studio/'output/private-desktop').mkdir(parents=True)
        H.need(H.sha(H.read(studio/'tools/private_desktop.py'))==H.PRIVATE_SHA,'PRIVATE_LAUNCHER_PIN')
        H.new(studio/'override.cfg',('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps('HAS Miku Pure171 '+uuid.uuid4().hex)+'\n').encode())
        H.json_new(stage/'SOURCE_SNAPSHOT.json',{'format':'has_miku171_immutable435_snapshot_1','revision':REVISION,
                    'files':{name:{'bytes':len(raw),'sha256':H.sha(raw)} for name,raw in frozen.items()}})
        for name,script,marker,count in (
            ('probe-unit','tests/secondary_collision_probe_unit.gd','MIKU_COLLISION_PROBE_UNIT ',40),
            ('binding-unit','tests/miku_collider_binding_unit.gd','MIKU_BINDING_UNIT ',27),
            ('geometry-unit','tests/secondary_collision_geometry_unit.gd','COLLISION_GEOMETRY_UNIT ',26),
            ('conversion-unit','tests/godot_skin_weight_conversion_unit.gd','GODOT_SKIN_WEIGHT_CONVERSION_UNIT ',24),
            ('skin-unit','tests/miku_skin_binding_unit.gd','MIKU_SKIN_BINDING_UNIT ',54)):
            Q.run_case(H,stage,studio,runtime,result,name,script,[],marker,count,graphical=False,timeout=25)
        result['pure_checks']=sum(row.get('checks',0) for row in result['cases'])
        H.need(result['pure_checks']==171 and len(result['cases'])==5 and len(result['jobs'])==5
               and all(row.get('graphical') is False for row in result['cases']),'EXACT_HEADLESS171_FIVE_SCRIPT_CASES')
        result['status']='PASS'
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__
        result['error_code']=str(error) if isinstance(error,H.Refusal) else 'SYNTHETIC_QUALIFICATION_EXCEPTION'
    finally:
        for process,row in H.OWNED:row['reaped']=H.reap(process)
        result['all_owned_launchers_reaped']=all(row.get('reaped') is True for _process,row in H.OWNED)
        result['all_attempted_private_jobs_closed']=all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
        result['parent_environment_unchanged']=dict(os.environ)==parent_environment
        try:result['head_unchanged']=H.head()==REVISION
        except BaseException:result['head_unchanged']=False
        result['preservation_failures']=H.preserve();result['all_admitted_inputs_preserved']=not result['preservation_failures']
        try:result['current_functional_domain_preserved']=S.domain(H,ROOT)==set(baseline)
        except BaseException:result['current_functional_domain_preserved']=False
        closure=result['all_owned_launchers_reaped'] and result['all_attempted_private_jobs_closed']
        result['owned_lock_removed']=False
        if fd is not None:
            try:
                H.need(closure and H.stamp(os.fstat(fd))==lane_identity and H.stamp(lane.lstat())==lane_identity,'OWNED_LOCK_RETAINED')
                os.lseek(fd,0,os.SEEK_SET);H.need(os.read(fd,128)==token,'OWNED_LOCK_TOKEN_CHANGED')
                os.close(fd);fd=None;H.need(H.stamp(lane.lstat())==lane_identity,'OWNED_LOCK_PATH_CHANGED')
                lane.unlink();result['owned_lock_removed']=True
            except BaseException as error:result['lock_error_type']=type(error).__name__
            finally:
                if fd is not None:os.close(fd)
        result['owned_lock_retained']=lane_identity is not None and not result['owned_lock_removed']
        if not (closure and result['parent_environment_unchanged'] and result['head_unchanged']
                and result['all_admitted_inputs_preserved'] and result['current_functional_domain_preserved']
                and result['owned_lock_removed']):result['status']='FAIL'
        if stage_owned:
            H.json_new(stage/'PRIVATE_COORDINATOR_RESULT.json',result)
            public={key:value for key,value in result.items() if key not in ('jobs','cases','preservation_failures')}
            public['private_job_count']=len(result['jobs']);public['preservation_failure_count']=len(result['preservation_failures'])
            public['cases']=[{key:value for key,value in row.items() if key in ('name','status','checks','graphical')} for row in result['cases']]
            H.json_new(stage/'PUBLIC_RESULT.json',public)
            print(json.dumps({'status':result['status'],'pure_checks':result.get('pure_checks'),'result':str(stage/'PUBLIC_RESULT.json')}),flush=True)
    return 0 if result['status']=='PASS' and primary is None else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status':'PREFLIGHT_REFUSED','error_type':type(error).__name__,'detail':str(error)}),flush=True)
        raise SystemExit(2)
