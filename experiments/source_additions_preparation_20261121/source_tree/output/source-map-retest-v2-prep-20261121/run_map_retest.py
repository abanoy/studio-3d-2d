"""Root-only actual map retest candidate. Author did not run native code.

Fresh tools copy +two qualified light patches; old review/installed sources stay
read-only. Uses the existing Source preparation CLI in one owned private job per
map, retaining the original archive staging and dependency rules.
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
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
REVIEW=Path('C:/a/Programming/cloudflare/HAS-Review-Neon-973039e-native/Studio')
FULL=ROOT/'output/windows-reference-body-1795233568436471500'
REVISION='36044471151a6e561d6d3a404859e76ddd05738d'
FULL_SHA='2ca293d180751d8d219c0371665cb64a0a9212cc7a2bb3ae20f1fbdd4e5a0471'
SOURCES_SHA='ae338017a4a0ac3483bfeb9bc8d1ab40355780bdeb235e29c104d9cf94c5f2f9'
LOCK=ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
CANDIDATE=ROOT/'output/source-map-light-compat-prep-20261120'
PATCHES={'source_lights.py':(8319,'284971f27040335b727c7a94639920cb6b1e37a37645ec8f553a704f1522eb5b'),
         'blender_source_bridge.py':(30697,'cc5a205772c83949bcc10f06633a73d83664c455e8daad163c06dba7a26dc60e')}
PRIVATE_SHA='c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61'
CASES=(('gm_construct','source-1795236768-093-561940885','7d5fe8cd5dfe0fb858a11e7cfa0be57de73f538e0e0b74048c5b77c1cf403eb7','4d1c027f2b93fa9100bcc4cb08b1dfdda437cadf4cf7d01d4b515dc2caa5a6a2',None),
       ('ttt_tiny_spaceship_v3','source-1795236859-745-653593157','4b6f8fa05e7458a866ed29093a0bf86c374c80531ffeffdebeb0663d3c36ea23','4848d3108c68b7e50d7762f8bf32b8a1391cbf2df198cbbdae9dd7a324e94eb3','maps/ttt_tiny_spaceship_v3.bsp'))
BOOTSTRAP_PIN=(3709,'59c9b66e7ba62339127aa874abcc02cd0e568b6c641d9f0d1cefddbbd8e52b4e')
PLACEMENT_WORKER=ROOT/'output/source-material-carrier-host-v11-prep-20261120/fresh_carrier_probe.py'
PLACEMENT_WORKER_PIN=(72518,'2c890e5065203473802fd799d21f274eb6d4c8d0c4644d8ecf767b411afd58ea')
PLACEMENT_SENTINEL=ROOT/'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py'
PLACEMENT_SENTINEL_PIN=(17989,'034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
ADMITTED={}
CATALOGUES={}
class Refusal(RuntimeError):pass
def need(value,code):
    if not value:raise Refusal(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(info):
    mode=info.st_mode & ~0o111 if os.name=='nt' and stat.S_ISREG(info.st_mode) else info.st_mode
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_nlink,mode,getattr(info,'st_file_attributes',0)&~0x40000)
def regular(info):return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and info.st_nlink==1 and not getattr(info,'st_file_attributes',0)&0x400
def fingerprint(path,remember=True,limit=4*1024**3):
    path=Path(path);before=path.lstat();need(regular(before) and 0<=before.st_size<=limit,'BOUNDED_REGULAR_FILE_REQUIRED')
    digest=hashlib.sha256();count=0
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno()))==stamp(before),'FILE_CHANGED_BEFORE_READ')
        while True:
            block=stream.read(1024*1024)
            if not block:break
            count+=len(block);need(count<=before.st_size,'FILE_GREW_DURING_READ');digest.update(block)
        after=os.fstat(stream.fileno())
    need(count==before.st_size and stamp(before)==stamp(after)==stamp(path.lstat()),'FILE_CHANGED_DURING_READ')
    row={'bytes':count,'sha256':digest.hexdigest()};key=str(path.resolve());identity=(stamp(before),row)
    if remember:
        if key in ADMITTED:need(ADMITTED[key]==identity,'ADMITTED_FILE_CHANGED')
        else:ADMITTED[key]=identity
    return row,before

def read(path,expected=None,limit=4*1024*1024):
    row,info=fingerprint(path,limit=limit)
    if expected:need((row['bytes'],row['sha256'])==expected,'INPUT_PIN_DIFFERS')
    raw=Path(path).read_bytes();need(len(raw)==row['bytes'] and sha(raw)==row['sha256'] and stamp(Path(path).lstat())==stamp(info),'SECOND_READ_DIFFERS')
    return raw

def parse(raw):
    def pairs(rows):
        result={}
        for key,value in rows:need(key not in result,'DUPLICATE_JSON_KEY');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _v:(_ for _ in ()).throw(Refusal('NONFINITE_JSON')))
def relative(value):
    need(type(value) is str and value and ':' not in value and '\\' not in value,'RELATIVE_PATH_REQUIRED')
    p=PurePosixPath(value);need(not p.is_absolute() and p.as_posix()==value and '..' not in p.parts,'RELATIVE_PATH_REQUIRED');return value
def git_head():
    return subprocess.check_output(['git','-c','core.autocrlf=false','rev-parse','HEAD'],cwd=ROOT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).decode().strip()
def write_new(path,value):
    with Path(path).open('x',encoding='utf8') as stream:json.dump(value,stream,indent=2);stream.write('\n')
def preserve():
    failures=[]
    for name,(expected_stamp,expected_row) in tuple(ADMITTED.items()):
        try:
            row,info=fingerprint(Path(name),remember=False)
            need(row==expected_row and stamp(info)==expected_stamp,'PRESERVATION_DIFFERS')
        except BaseException as error:failures.append({'path':name,'error_type':type(error).__name__})
    return failures

def source_paths(folder):
    result=set();pending=[folder]
    while pending:
        current=pending.pop();info=current.lstat()
        need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'SOURCE_DIRECTORY_ALIAS')
        for path in current.iterdir():
            if path.name in {'__pycache__','.git'} or path.suffix=='.pyc':continue
            info=path.lstat();need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'SOURCE_PATH_ALIAS')
            if stat.S_ISDIR(info.st_mode):pending.append(path)
            else:need(regular(info),'SOURCE_NONREGULAR_FILE');result.add(path.relative_to(folder).as_posix())
    return result

def catalogue(folder,rows):
    need(type(rows) is dict and source_paths(folder)==set(rows),'CATALOGUE_PATHSET_DIFFERS')
    CATALOGUES[str(folder.resolve())]=frozenset(rows)
    for name,expected in rows.items():
        name=relative(name);row,_info=fingerprint(folder/name)
        need(row=={'bytes':expected['bytes'],'sha256':expected['sha256']},'RUNTIME_SOURCE_PIN_DIFFERS')

def glb_shape(path):
    row,_info=fingerprint(path,remember=False,limit=128*1024*1024)
    with path.open('rb') as stream:
        head=stream.read(20)
        need(len(head)==20 and head[:4]==b'glTF' and int.from_bytes(head[4:8],'little')==2 and int.from_bytes(head[8:12],'little')==row['bytes'] and head[16:20]==b'JSON','OUTPUT_GLB_HEADER')
        count=int.from_bytes(head[12:16],'little');need(count<=row['bytes']-20 and count<=32*1024*1024,'OUTPUT_GLB_JSON_LIMIT')
        doc=parse(stream.read(count))
    lights=doc.get('extensions',{}).get('KHR_lights_punctual',{}).get('lights',[])
    need(type(lights) is list and len(lights)<=64,'OUTPUT_LIGHT_BUDGET')
    need(type(doc.get('meshes')) is list and len(doc['meshes'])>0,'OUTPUT_MAP_HAS_NO_MESHES')
    return dict(row,meshes=len(doc['meshes']),nodes=len(doc.get('nodes',[])),materials=len(doc.get('materials',[])),lights=len(lights))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--self-sha256',required=True);parser.add_argument('--expected-head',required=True);parser.add_argument('--root-exclusive-lane-confirmed',action='store_true');args=parser.parse_args()
    need(not sys.flags.optimize and sys.version_info[:2]==(3,13) and args.root_exclusive_lane_confirmed,'ROOT_PYTHON313_EXCLUSIVE_LANE_REQUIRED')
    need(re.fullmatch('[0-9a-f]{40}',args.expected_head) and git_head()==args.expected_head,'HEAD_DIFFERS')
    need(sha(read(Path(__file__)))==args.self_sha256,'COORDINATOR_PIN_DIFFERS')
    complete=parse(read(FULL/'completion.json'));need(sha(read(FULL/'completion.json'))==FULL_SHA,'FULL_COMPLETION_PIN')
    need(complete.get('revision')==REVISION and complete.get('functional_source_count')==1084 and complete.get('exit')==0,'CLOSED_FULL360_REQUIRED')
    for key in ['child_reaped','functional_sources_unchanged','revision_unchanged','fresh_final_report','all_private_jobs_isolated_closed','receipt_provenance_verified','whole_verifier_pass']:need(complete.get(key) is True,'CLOSED_FULL360_REQUIRED')
    raw=read(FULL/'source-after.json');need(sha(raw)==SOURCES_SHA,'FULL_SOURCE_PIN');sources=parse(raw);need(len(sources)==1084,'SOURCE_COUNT')
    for name,expected in sources.items():
        row,info=fingerprint(ROOT/relative(name));need(row=={'bytes':expected['bytes'],'sha256':expected['sha256']} and info.st_mtime_ns==expected['mtime_ns'],'CURRENT_SOURCE_DIFFERS')
    lockraw=read(LOCK);need(sha(lockraw)==LOCK_SHA,'RUNTIME_LOCK_PIN');lock=parse(lockraw)
    for name,expected in lock['runtime_executables'].items():
        row,_info=fingerprint(Path(name));need(row=={'bytes':expected['bytes'],'sha256':expected['sha256']},'RUNTIME_EXE_PIN')
    python=Path(lock['runtime_paths']['python']);blender=Path(lock['runtime_paths']['blender'])
    need(Path(sys.executable).resolve()==python.resolve(),'APPROVED_PYTHON_REQUIRED')
    catalogue(Path(lock['exporter_root']),lock['exporter_noncache_sources'])
    requests=[]
    for label,oldfolder,request_sha,original_sha,member in CASES:
        oldpath=REVIEW/'output/compatibility'/oldfolder/'conversion-request.json';raw=read(oldpath);need(sha(raw)==request_sha,'OLD_REQUEST_PIN')
        request=parse(raw);original=Path(request['original_source']);original_row,_info=fingerprint(original)
        need(original_row['sha256']==original_sha and request['sha256']==original_sha and request['source_member']==member and request['scale']==.01905,'ORIGINAL_MAP_IDENTITY')
        need(request['sourceio_revision']=='fe24260b97ac03b899d9b5d4f0fd7b34772f3647','SOURCEIO_REVISION')
        sdk=Path(request['sourceio']);catalogue(sdk,lock['sourceio_files']);requests.append((label,request,sdk))
    bootstrap_raw=read(Path(__file__).with_name('map_prepare_bootstrap.py'),BOOTSTRAP_PIN)
    read(PLACEMENT_WORKER,PLACEMENT_WORKER_PIN);read(PLACEMENT_SENTINEL,PLACEMENT_SENTINEL_PIN)
    stage=ROOT.parent/('has-source-map-retest-'+str(time.time_ns()));stage.mkdir();(stage/'tools').mkdir();(stage/'cases').mkdir()
    lane=ROOT/'output/source-map-retest.lock';lane_fd=None;lane_stamp=None;closure_proven=True;primary=None
    result={'format':'has_actual_optional_map_light_retest_2','status':'FAIL','revision_under_test':REVISION,'head':args.expected_head,'cases':[],'actual_editor_or_visual_acceptance':False,'current_application_modified':False,'stage':str(stage),'parent_environment_mutated':False}
    try:
        lane_fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(lane_fd,str(os.getpid()).encode());lane_stamp=stamp(os.fstat(lane_fd))
        for name,expected in sources.items():
            if not name.startswith('tools/'):continue
            raw=read(ROOT/name);target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            need(fingerprint(target)[0]=={'bytes':len(raw),'sha256':sha(raw)},'TOOLS_COPY_DIFFERS')
        # Only owned fresh copies are replaced; keep the originals in a sibling base.
        (stage/'bases').mkdir()
        for name,pin in PATCHES.items():
            target=stage/'tools'/name;(stage/'bases'/name).write_bytes(target.read_bytes());raw=read(CANDIDATE/name,pin);target.write_bytes(raw)
            # Adopt the deliberate new owned-copy identity before runtime work.
            ADMITTED.pop(str(target.resolve()),None);need(fingerprint(target)[0]=={'bytes':pin[0],'sha256':pin[1]},'LIGHT_OVERLAY_DIFFERS')
        sdk_source=requests[0][2]
        need(all(sdk.resolve()==sdk_source.resolve() for _label,_request,sdk in requests),'ONE_APPROVED_SDK_REQUIRED')
        owned_sdk=stage/'SourceIO';owned_sdk.mkdir()
        source_rows={name:row for name,row in lock['sourceio_files'].items() if '__pycache__' not in PurePosixPath(name).parts and '.git' not in PurePosixPath(name).parts and not name.endswith('.pyc')}
        need(source_rows,'EMPTY_SDK_SOURCE_SUBSET')
        result['sdk_catalogue_files']=len(lock['sourceio_files']);result['owned_sdk_source_subset_files']=len(source_rows)
        for name,expected in source_rows.items():
            raw=read(sdk_source/relative(name),limit=16*1024*1024);target=owned_sdk/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            need(fingerprint(target)[0]=={'bytes':expected['bytes'],'sha256':expected['sha256']},'SDK_COPY_DIFFERS')
        catalogue(owned_sdk,source_rows)
        need(sha(read(stage/'tools/private_desktop.py'))==PRIVATE_SHA,'PRIVATE_JOB_SOURCE_PIN')
        spec=importlib.util.spec_from_file_location('_has_map_retest_private_job',stage/'tools/private_desktop.py');private=importlib.util.module_from_spec(spec);sys.modules[spec.name]=private;spec.loader.exec_module(private)
        bootstrap_path=stage/'map_prepare_bootstrap.py';bootstrap_path.write_bytes(bootstrap_raw)
        need(fingerprint(bootstrap_path)[0]=={'bytes':BOOTSTRAP_PIN[0],'sha256':BOOTSTRAP_PIN[1]},'BOOTSTRAP_COPY_DIFFERS')
        for label,request,sdk in requests:
            case=stage/'cases'/label;case.mkdir();bundle=case/'bundle';status=case/'status.json';cancel=case/'cancel'
            mounts=[value for value in request['mounts'] if not Path(value).resolve().is_relative_to(REVIEW.resolve())]
            write_new(case/'mount-plan.json',mounts)
            command=[str(python),'-B',str(stage/'tools/prepare_source.py'),request['original_source'],'--output',str(bundle),'--sourceio',str(owned_sdk),'--blender',str(blender),'--gmod',request['gmod_installation'],'--workshop',request['workshop_root'],'--mount-plan',str(case/'mount-plan.json'),'--scale','0.01905','--status-file',str(status),'--cancel-file',str(cancel)]
            if request['source_member']:command.extend(['--member',request['source_member']])
            write_new(case/'preparer-command.json',command)
            for item in ['userdata','temp','blender-config']:(case/item).mkdir()
            prepare_path=stage/'tools/prepare_source.py';prepare_row,_info=fingerprint(prepare_path)
            config={'format':'has_map_prepare_hidden_bootstrap_1',
                    'worker':{'path':str(PLACEMENT_WORKER),'bytes':PLACEMENT_WORKER_PIN[0],'sha256':PLACEMENT_WORKER_PIN[1]},
                    'sentinel':{'path':str(PLACEMENT_SENTINEL),'bytes':PLACEMENT_SENTINEL_PIN[0],'sha256':PLACEMENT_SENTINEL_PIN[1]},
                    'preparer':{'path':str(prepare_path),**prepare_row},'args':command[3:],'placement':str(case/'placement.json'),
                    'environment':dict(PYTHONDONTWRITEBYTECODE='1',NO_BPY='1',BLENDER_USER_CONFIG=str(case/'blender-config'),APPDATA=str(case/'userdata'),LOCALAPPDATA=str(case/'userdata'),TEMP=str(case/'temp'),TMP=str(case/'temp'))}
            config_path=case/'bootstrap-config.json';write_new(config_path,config);config_row,_info=fingerprint(config_path)
            command=[str(python),'-B',str(bootstrap_path),'--config',str(config_path),'--config-sha256',config_row['sha256']]
            write_new(case/'command.json',command)
            cwd_before=Path.cwd();receipt=case/'private-receipt.json'
            row={'case':label,'conversion_passed':False,'private_job_closed':False}
            result['cases'].append(row)
            try:
                os.chdir(case)
                closure_proven=False
                code=private.run_private(command,receipt,timeout=720,cancel_file=cancel,memory_limit_mib=4096)
            finally:
                os.chdir(cwd_before)
            proof=parse(read(receipt));closed=proof.get('job_closed') is True and proof.get('desktop_closed') is True
            row['private_job_closed']=closed;closure_proven=closed
            need(closed,'PRIVATE_CLOSURE_NOT_PROVEN')
            need(proof.get('desktop_switch_requested') is False and proof.get('foreground_child_observed') is False and proof.get('child_desktop_confirmed') is True and proof.get('private_window_seen') is True and type(proof.get('maximum_owned_windows')) is int and proof['maximum_owned_windows']>=1,'PRIVATE_PLACEMENT_FAILED')
            placement=parse(read(case/'placement.json'));policy=placement.get('policy',{})
            need(placement.get('format')=='has_map_prepare_hidden_placement_1' and placement.get('worker_verified_hidden_sentinel_closed') is True and placement.get('placement_is_for_root_python_preparer') is True and placement.get('blender_gui_or_render_claim') is False,'HIDDEN_SENTINEL_RESULT_FAILED')
            need(type(policy) is dict and policy.get('format')=='has_hidden_background_desktop_placement_sentinel_1' and policy.get('class')=='STATIC' and policy.get('requested_size_pixels')==[0,0],'HIDDEN_SENTINEL_POLICY_FAILED')
            for key in ['disabled','noactivate_style','toolwindow_style','owned_pid_and_thread_verified','destroyed_in_finally']:need(policy.get(key) is True,'HIDDEN_SENTINEL_POLICY_FAILED')
            for key in ['visible_at_creation','visible_before_destruction','show_or_activation_calls','thread_desktop_switch_calls']:need(policy.get(key) is False,'HIDDEN_SENTINEL_POLICY_FAILED')
            row['hidden_root_sentinel_verified']=True
            need(code==0 and proof.get('exit')==0,'MAP_WORKER_REFUSED')
            status_value=parse(read(status));need(status_value.get('ok') is True,'MAP_STATUS_FAILED')
            parameters=parse(read(bundle/'parameters.json',limit=256*1024));native=parameters['native_parameters'];omissions=native['static_entity_light_omissions']
            need(omissions['format']=='has_optional_source_map_light_omissions_1' and omissions['global_limit']==64 and omissions['created']==len(native['static_entity_lights'])<=64,'OMISSION_REPORT_DIFFERS')
            need(omissions['light_entities']==sum(omissions[key] for key in ['created','invalid','budget','starts_off','animated_style','unsupported_type']),'OMISSION_ACCOUNTING_DIFFERS')
            raw_entities=parse(read(bundle/'entities.json',limit=64*1024*1024));need(type(raw_entities) is list,'RAW_ENTITIES_MISSING')
            shape=glb_shape(bundle/'scene.glb');need(shape['lights']==omissions['created'],'SERIALIZED_LIGHT_COUNT_DIFFERS')
            row.update(conversion_passed=True,geometry=shape,raw_entity_count=len(raw_entities),light_omissions=omissions,warning_count=len(parameters.get('warnings',[])),source_mesh_count=parameters['counts']['meshes'])
        need(len(result['cases'])==2 and all(row['conversion_passed'] for row in result['cases']),'TWO_MAPS_REQUIRED');result['status']='PASS'
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__;result['error_code']=str(error) if type(error) is Refusal else 'COORDINATOR_EXCEPTION'
    finally:
        failures=preserve()
        for folder,expected_paths in CATALOGUES.items():
            try:need(source_paths(Path(folder))==expected_paths,'RUNTIME_SOURCE_PATHSET_CHANGED')
            except BaseException as error:failures.append({'path':folder,'error_type':type(error).__name__})
        result['preservation_failures']=failures;result['all_admitted_inputs_unchanged']=not failures
        if failures:result['status']='FAIL'
        try:result['head_unchanged']=git_head()==args.expected_head
        except BaseException as error:result['head_unchanged']=False;result['head_check_error_type']=type(error).__name__
        if not result['head_unchanged']:result['status']='FAIL'
        result['owned_private_job_closure_proven']=closure_proven
        if lane_fd is not None:
            os.close(lane_fd)
            try:
                if closure_proven and regular(lane.lstat()) and stamp(lane.lstat())==lane_stamp:lane.unlink();result['lane_released']=True
                else:result['lane_released']=False;result['status']='FAIL'
            except BaseException as error:
                result['lane_released']=False;result['status']='FAIL';result['lane_cleanup_error_type']=type(error).__name__
        write_new(stage/'PUBLIC_MAP_RESULT.json',result);print(json.dumps(result),flush=True)
    return 0 if result['status']=='PASS' and primary is None else 1
if __name__=='__main__':raise SystemExit(main())
