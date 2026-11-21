"""Build an isolated private owner review only after the new whole verifier passes.
Source-only authored candidate; Root owns execution. Never modifies old reviews.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = ROOT / 'output'
LOCK = OUTPUT / 'source-owner-review-builder.lock'
MAX_READ = 256 * 1024 * 1024
RECALL_HINT = 0x40000
RUNTIME_LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
RUNTIME_LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
CREATION = ROOT / 'output/source-live-normal-run-1795231337601347500/PUBLIC_LIVE_NORMAL_ROOT_RESULT.json'
CREATION_SHA = '71f9e8da5a88d4f4a7c997a30bad09afa399546a8934041863cece92877449f9'
ASSETS = {
    'scene_glb': ('scene.glb', 2478804, 'b8436dea1d13a7cb4632c37c50b4cab123616ec574720fe4e764b844c5293e71'),
    'parameters_json': ('parameters.json', 170388, '9b007f229d7b9dd837eb443cc31c6649620b17738481904aa7efd132164ae9dd'),
}
PYTHON = Path(r'C:/Program Files/Python313/python.exe')
PYTHONW = Path(r'C:/Program Files/Python313/pythonw.exe')
GODOT = Path(r'C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
BLENDER = Path(r'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe')
FFMPEG = Path(r'C:/Program Files/ffmpeg/bin/ffmpeg.exe')
NOTICES = ('THIRD_PARTY_NOTICES.md', 'docs/licenses.md')

class Refusal(RuntimeError): pass

def need(ok, code):
    if not ok: raise Refusal(code)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def safe(path, *, missing=False):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        try: info = part.lstat()
        except FileNotFoundError:
            need(missing, 'MISSING_PATH')
            continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0) & 0x400, 'LINK_OR_REPARSE_PATH')
        need(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'SPECIAL_PATH')
        if stat.S_ISREG(info.st_mode): need(info.st_nlink == 1, 'HARDLINK_PATH')
    return path

def stamp(info):
    # Windows lstat infers execute bits from .exe; fstat cannot infer its name.
    mode = info.st_mode & ~0o111 if os.name == 'nt' and stat.S_ISREG(info.st_mode) else info.st_mode
    return (info.st_dev,info.st_ino,mode,info.st_nlink,info.st_size,info.st_mtime_ns,
            getattr(info,'st_file_attributes',0) & ~RECALL_HINT)

def read(path, *, digest=None, count=None, limit=MAX_READ):
    path = safe(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= limit, 'READ_SIZE_OR_TYPE')
    if count is not None: need(type(count) is int and before.st_size == count, 'READ_SIZE_PIN')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'FILE_CHANGED_BEFORE_READ')
        raw = stream.read(before.st_size+1)
        need(stamp(os.fstat(stream.fileno())) == stamp(before), 'FILE_CHANGED_DURING_READ')
    need(stamp(path.lstat()) == stamp(before) and len(raw) == before.st_size, 'FILE_CHANGED_AFTER_READ')
    if digest is not None: need(sha(raw) == digest, 'READ_SHA_PIN')
    return raw, stamp(before)

def new(path, raw):
    path = safe(path, missing=True)
    need(not path.exists() and not path.is_symlink(), 'NEW_OUTPUT_EXISTS')
    need(path.parent.is_dir(), 'NEW_OUTPUT_PARENT_MISSING')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return read(path, digest=sha(raw), count=len(raw))

def json_new(path, value):
    return new(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)

def validate_name(name):
    need(type(name) is str and bool(name),'SOURCE_NAME_TYPE')
    parts = name.split('/')
    need(not PureWindowsPath(name).anchor and all(part not in ('','.','..') and part==part.rstrip(' .')
         and not any(ord(c)<32 or c in '\\:<>"|?*' for c in part) for part in parts),'UNSAFE_SOURCE_NAME')
    return parts

def validate_full(folder, revision, digest):
    need(re.fullmatch('[0-9a-f]{40}',revision) is not None,'REVISION_FORMAT')
    folder = safe(folder)
    need(folder.parent == OUTPUT and folder.name.startswith('windows-reference-body-'),'FULL_FOLDER_SCOPE')
    completion_raw, _ = read(folder/'completion.json',digest=digest,limit=16*1024*1024)
    value = json.loads(completion_raw)
    need(value.get('format') == 'has_reference_body_full_coordinator_1' and value.get('revision') == revision,'FULL_REVISION_OR_FORMAT')
    for name in ('whole_verifier_pass','child_reaped','functional_sources_unchanged','revision_unchanged',
                 'fresh_final_report','all_private_jobs_isolated_closed','nonzero_jobs_are_expected_cancellations','receipt_provenance_verified'):
        need(value.get(name) is True,'FULL_NOT_QUALIFIED_'+name.upper())
    need(type(value.get('functional_source_count')) is int and value['functional_source_count'] == 1084 and value.get('exit') == 0,'FULL_SOURCE_COUNT_OR_EXIT')
    before_raw,_ = read(folder/'source-before.json',limit=4*1024*1024)
    after_raw,_ = read(folder/'source-after.json',limit=4*1024*1024)
    before,after=json.loads(before_raw),json.loads(after_raw)
    need(type(before) is dict and len(before)==1084 and before==after,'FULL_SOURCE_CATALOGUE')
    for name,row in before.items():
        validate_name(name)
        need(type(row) is dict and type(row.get('bytes')) is int and row['bytes'] >= 0
             and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) and re.fullmatch('[0-9a-f]{40}',row.get('git_sha1','')),'FULL_SOURCE_ROW')
    return value,before,{str(folder/'completion.json'):(completion_raw,read(folder/'completion.json')[1]),
        str(folder/'source-before.json'):(before_raw,read(folder/'source-before.json')[1]),
        str(folder/'source-after.json'):(after_raw,read(folder/'source-after.json')[1])}

def source_blobs(revision, catalogue):
    # Use the qualified existing snapshot workflow, including its literal resource
    # closure. Authenticate the reader before importing its pure definitions.
    helper_path=ROOT/'tools/build_owner_review_snapshot.py'
    helper_row=catalogue['tools/build_owner_review_snapshot.py']
    read(helper_path,digest=helper_row['sha256'],count=helper_row['bytes'])
    need(helper_path.lstat().st_mtime_ns==helper_row['mtime_ns'],'SNAPSHOT_READER_STAMP')
    helper=load_module('qualified_review_snapshot_reader',helper_path)
    tree=git('ls-tree','-r','-z',revision)
    entries=[]; rows={}
    for record in tree.split(b'\0'):
        if not record: continue
        meta,name=record.split(b'\t',1); mode,kind,oid=meta.split(); name=name.decode('utf-8')
        if not helper.included(name): continue
        need(mode in (b'100644',b'100755') and kind==b'blob','SOURCE_GIT_MODE')
        helper.validate_name(name); entries.append((name,oid)); rows[name]=oid.decode('ascii')
    need(set(catalogue)<=rows.keys(),'SOURCE_GIT_DOMAIN')
    for name,row in catalogue.items(): need(rows[name]==row['git_sha1'],'SOURCE_GIT_BLOB_DIFFERS')
    need(len([name for name in catalogue if not name.startswith('experiments/')])==1078,'RUNTIME_SOURCE_SCOPE')
    need(len({name.casefold() for name in rows})==len(rows),'SOURCE_CASE_COLLISION')
    selected,cached=helper._runtime_entries(ROOT,entries,revision)
    need(all(not name.startswith(('experiments/','output/','.git/','.godot/')) and '__pycache__' not in Path(name).parts
        and not name.endswith(('.pyc','.pyo')) for name,_ in selected),'RUNTIME_RESOURCE_SCOPE')
    result={name:cached[name] for name,_ in selected}
    need({name for name in catalogue if not name.startswith('experiments/')}<=result.keys(),'RUNTIME_SOURCE_MISSING')
    for name,data in result.items():
        helper.validate_name(name)
        if name in catalogue:
            need(len(data)==catalogue[name]['bytes'] and sha(data)==catalogue[name]['sha256'],'SOURCE_BLOB_BYTES_DIFFERS')
    return result

def receipt_closed(value):
    return (value.get('format')=='studio_private_desktop_1'
            and value.get('job_closed') is True and value.get('desktop_closed') is True
            and value.get('child_desktop_confirmed') is True and value.get('foreground_child_observed') is False
            and value.get('desktop_switch_requested') is False)

def private_job(studio, runner, script, args, env, verification, name, state):
    command=runner.command(script,extra=['--audio-driver','Dummy','--',*args]) if script else runner.command(extra=args)
    need(len(command)>6 and Path(command[0])==PYTHONW and Path(command[1])==studio/'tools/private_desktop.py','NO_PRIVATE_LAUNCHER')
    receipt=Path(command[command.index('--receipt')+1]); safe(receipt,missing=True)
    need(receipt.is_relative_to(studio/'output/private-desktop'),'PRIVATE_RECEIPT_SCOPE')
    command[2:2]=['--timeout','210','--memory-limit-mib','4096']
    out_path,err_path=verification/(name+'-stdout.log'),verification/(name+'-stderr.log')
    proc=None
    try:
        with out_path.open('xb') as out,err_path.open('xb') as err:
            proc=subprocess.Popen(command,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            state['launched']=True; state['closure_confirmed']=False
            json_new(verification/(name+'-launch.json'),{'pid':proc.pid,'private_receipt':str(receipt),'args':command})
            proc.wait(timeout=240)
    finally:
        if proc is not None:
            if proc.poll() is None: proc.kill()
            proc.wait(timeout=30)
    value=json.loads(read(receipt,limit=1024*1024)[0])
    state['closure_confirmed']=receipt_closed(value)
    need(proc.returncode==0 and value.get('error') is None and state['closure_confirmed'],'PRIVATE_JOB_OR_CLOSURE_FAILED')
    json_new(verification/(name+'-private.json'),value)
    need(not re.search(r'(?m)^(?:SCRIPT ERROR:|ERROR:)',read(err_path,limit=8*1024*1024)[0].decode('utf-8','replace')),'PRIVATE_ENGINE_ERROR')
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-folder',type=Path,required=True)
    parser.add_argument('--full-completion-sha256',required=True)
    parser.add_argument('--revision',required=True)
    parser.add_argument('--sourceio',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--root-lane-confirmed',action='store_true',required=True)
    options=parser.parse_args()
    need(os.name=='nt' and options.root_lane_confirmed,'ROOT_WINDOWS_LANE_REQUIRED')
    # First gate: no runtime/native/process work occurs while Full is incomplete.
    full,catalogue,proofs=validate_full(options.full_folder,options.revision,options.full_completion_sha256)
    frozen=source_blobs(options.revision,catalogue)
    expected={}; checks=[]
    def retain(path,raw=None,identity=None,digest=None,count=None):
        path=Path(path)
        if raw is None: raw,identity=read(path,digest=digest,count=count)
        expected[str(path)]=(raw,identity)
        return raw
    for path,(raw,identity) in proofs.items(): retain(path,raw,identity)
    for name,row in catalogue.items():
        raw,identity=read(ROOT/name,digest=row['sha256'],count=row['bytes'])
        need((ROOT/name).lstat().st_mtime_ns==row['mtime_ns'],'WORKING_SOURCE_MTIME_DIFFERS')
        retain(ROOT/name,raw,identity)
    creation_raw=retain(CREATION,digest=CREATION_SHA)
    creation=json.loads(creation_raw)
    need(creation.get('format')=='has_source_live_native_normal_root_result_1' and creation.get('status')=='LIVE_VMT_NORMALS_BONES_AND_PARAMETERS_MATCHED','LIVE_CREATION_UNQUALIFIED')
    for name in ('final_parameters_crosswalk_bound','all_source_runtime_native_and_mount_preservation_checks_passed','private_job_closed','retained_launcher_reaped','owned_lock_removed'):
        need(creation.get(name) is True,'LIVE_CREATION_FLAG')
    need(creation.get('physical_owned_processes')==0 and creation.get('foreground_activation') is False
         and creation.get('models')==2 and creation.get('points')==9661 and creation.get('bones')==69 and creation.get('jiggle_rules')==49
         and creation.get('source_normal_threshold')==.00002 and creation.get('final_normal_max_euclidean_error')==0.0,'LIVE_CREATION_COUNTS')
    art={}
    for role,(name,count,digest) in ASSETS.items():
        row=creation['artifacts'][role]; need(row['bytes']==count and row['sha256']==digest,'ARTIFACT_RECEIPT_PIN')
        art[name]=retain(Path(row['path']),digest=digest,count=count)
        need(Path(row['path']).lstat().st_mtime_ns==row['mtime_ns'],'ARTIFACT_SOURCE_STAMP')
    lock_raw=retain(RUNTIME_LOCK,digest=RUNTIME_LOCK_SHA); runtime=json.loads(lock_raw)
    for path,row in runtime['runtime_executables'].items():
        retain(Path(path),digest=row['sha256'],count=row['bytes'])
        need(Path(path).lstat().st_mtime_ns==row['mtime_ns'],'RUNTIME_MTIME_PIN')
    sdk=safe(options.sourceio); sdk_rows={}
    for base,dirs,files in os.walk(sdk,followlinks=False):
        for name in dirs: safe(Path(base)/name)
        for name in files:
            path=Path(base)/name; relative=path.relative_to(sdk).as_posix(); sdk_rows[relative]=path
    need(set(sdk_rows)==set(runtime['sourceio_files']) and len(sdk_rows)==574,'SOURCEIO_EXACT_CATALOGUE')
    for name,path in sdk_rows.items():
        row=runtime['sourceio_files'][name]; retain(path,digest=row['sha256'],count=row['bytes'])
        need(path.lstat().st_mtime_ns==row['mtime_ns'],'SOURCEIO_MTIME_PIN')
    own_sources={}
    for name in ('build_review.py','prepare_review.gd','SOURCE_PINS.json'):
        path=HERE/name; raw,identity=read(path); retain(path,raw,identity); own_sources[name]=sha(raw)
    source_pins=json.loads(expected[str(HERE/'SOURCE_PINS.json')][0])
    for row in source_pins['files']:
        need(row['path'] in own_sources and own_sources[row['path']]==row['sha256'],'BUILDER_SOURCE_PIN')
    need(set(row['path'] for row in source_pins['files'])=={'build_review.py','prepare_review.gd'},'BUILDER_SOURCE_PIN_DOMAIN')
    stage=options.output or OUTPUT/('owner-review-Junko-'+str(time.time_ns()))
    stage=Path(os.path.abspath(stage)); safe(stage,missing=True)
    need(stage.parent==OUTPUT and re.fullmatch(r'owner-review-Junko-[A-Za-z0-9_-]+',stage.name) is not None,'REVIEW_OUTPUT_SCOPE')
    need(not stage.exists(),'REVIEW_OUTPUT_EXISTS')
    token=uuid.uuid4().hex; lock_owned=False; stage_owned=False; success=False
    state={'launched':False,'closure_confirmed':True}; primary=None
    try:
        safe(LOCK,missing=True)
        with LOCK.open('xb') as stream: stream.write(token.encode()); stream.flush(); os.fsync(stream.fileno())
        lock_owned=True
        stage.mkdir(exist_ok=False); stage_owned=True
        for name in ('Assets/Junko','Examples','Verification','UserData/Roaming','UserData/Local','UserData/Temp'):
            (stage/name).mkdir(parents=True,exist_ok=True)
        studio=stage/'Studio'; studio.mkdir(exist_ok=False)
        for name,raw in frozen.items():
            target=studio.joinpath(*validate_name(name)); target.parent.mkdir(parents=True,exist_ok=True); new(target,raw)
        source_hashes={name:sha(raw) for name,raw in frozen.items()}
        for name,raw in art.items(): new(stage/'Assets/Junko'/name,raw)
        for name in ('prepare_review.gd',): new(stage/'Verification'/name,expected[str(HERE/name)][0])
        profile='HAS Junko Review '+token
        new(studio/'override.cfg',('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
        env=os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=str(PYTHON),HYBRID_GODOT=str(GODOT),
            HYBRID_FFMPEG=str(FFMPEG),HYBRID_SOURCE_BLENDER=str(BLENDER),HYBRID_SOURCEIO=str(sdk),
            APPDATA=str(stage/'UserData/Roaming'),LOCALAPPDATA=str(stage/'UserData/Local'),TEMP=str(stage/'UserData/Temp'),TMP=str(stage/'UserData/Temp'))
        for key in ('HYBRID_FAN_PROJECT','HYBRID_NATIVE_FIXTURES','HYBRID_NATIVE_INPUTS'): env.pop(key,None)
        runner=load_module('isolated_junko_review_runner',studio/'run.py')
        need(runner.ROOT==studio,'REVIEW_RUNNER_ROOT')
        verification=stage/'Verification'
        startup_result=verification/'startup.json'
        private_job(studio,runner,None,['res://tests/current_candidate_startup.tscn','--',str(startup_result)],env,verification,'startup',state)
        startup=json.loads(read(startup_result,limit=1024*1024)[0])
        need(all(startup.get(key) is True for key in ('home_visible','simple','empty')) and profile in startup.get('profile',''),'ISOLATED_HOME_STARTUP')
        need(Path(startup['profile']).is_relative_to(stage/'UserData'),'USERDATA_ESCAPED_REVIEW')
        for mode in ('writer','reader'):
            request={'format':'has_corrected_junko_owner_review_request_1','mode':mode,'folder':stage.as_posix(),
                'result':(verification/(mode+'.json')).as_posix()}
            request_path=verification/(mode+'-request.json'); json_new(request_path,request)
            private_job(studio,runner,str(verification/'prepare_review.gd'),[str(request_path)],env,verification,mode,state)
            result=json.loads(read(verification/(mode+'.json'),limit=1024*1024)[0])
            need(result.get('passed') is True and result.get('mode')==mode and all(result.get('checks',{}).values()),'REVIEW_PREPARATION_CHECK_FAILED')
        for name,digest in source_hashes.items(): read(studio/name,digest=digest,count=len(frozen[name]))
        for name,(count,digest) in {value[0]:(value[1],value[2]) for value in ASSETS.values()}.items(): read(stage/'Assets/Junko'/name,digest=digest,count=count)
        need(not (studio/'experiments').exists() and not any(studio.rglob('*.pyc')) and not any(studio.rglob('__pycache__')),'REVIEW_SOURCE_SCOPE_LEAK')
        launch_env={'HYBRID_PYTHON':str(PYTHON),'HYBRID_GODOT':str(GODOT),'HYBRID_FFMPEG':str(FFMPEG),
            'HYBRID_SOURCE_BLENDER':str(BLENDER),'HYBRID_SOURCEIO':str(sdk),'PYTHONDONTWRITEBYTECODE':'1',
            'APPDATA':r'%~dp0UserData\Roaming','LOCALAPPDATA':r'%~dp0UserData\Local','TEMP':r'%~dp0UserData\Temp','TMP':r'%~dp0UserData\Temp'}
        for label,argument in [('Open Studio',''),('Open Junko',' "%~dp0Examples\\Junko.has"')]:
            text='@echo off\r\nsetlocal\r\n'+''.join('set "'+key+'='+value+'"\r\n' for key,value in launch_env.items())
            text+='start "" "'+str(PYTHONW)+'" "%~dp0Studio\\launch.pyw"'+argument+'\r\n'
            new(stage/(label+'.bat'),text.encode('utf-8'))
        new(stage/'README.md',('# Corrected Junko review\n\nOpen **Open Junko.bat** for the ready-made scene, or **Open Studio.bat** for a blank project.\n\nThe Junko project includes the corrected normals and matching imported 69-bone / 49-rule metadata. Select the hair model and enable Hair & clothes to use the qualified imported-hair preview. Motion starts off so you can inspect the original pose.\n\nThis Studio keeps its settings and recovery files in its own UserData folder, with caches and logs confined to this review. The original Studio and earlier reviews are unchanged. Runtime tools use the existing approved local installations.\n\nPrivate model files and screenshots are for local review; they are not included in the source publication. Passing automated checks does not constitute your visual acceptance.\n').encode())
        success=True
    except BaseException as error:
        primary=error
    finally:
        for path,(raw,identity) in expected.items():
            try:
                after,after_identity=read(Path(path),digest=sha(raw),count=len(raw))
                checks.append({'path':path,'unchanged':after_identity==identity})
            except BaseException: checks.append({'path':path,'unchanged':False})
        preserved=all(row['unchanged'] for row in checks) and len(checks)==len(expected)
        success=success and preserved and state['closure_confirmed']
        removed=False
        if lock_owned and state['closure_confirmed']:
            try:
                need(read(LOCK,count=len(token))[0]==token.encode(),'OWNED_LOCK_CHANGED')
                LOCK.unlink(); removed=True
            except BaseException as error:
                success=False
                if primary is None: primary=error
        if stage_owned:
            result={'format':'has_corrected_junko_owner_review_build_1','passed':success,'source_revision':options.revision,
                'full_verifier_passed':True,'qualified_functional_source_files':1084,'copied_runtime_source_files':len(frozen),
                'experiments_copied':False,'private_assets_local_only':True,'all_admitted_inputs_preserved':preserved,
                'source_sha256':{name:sha(raw) for name,raw in frozen.items()},'source_artifact_sha256':{name:sha(raw) for name,raw in art.items()},
                'private_jobs_closed':state['closure_confirmed'],'owned_lock_removed':removed,'owned_lock_retained':lock_owned and not removed,
                'primary_error':type(primary).__name__ if primary else None,'error_code':str(primary) if isinstance(primary,Refusal) else None,
                'owner_visual_acceptance':False,'preservation':checks}
            json_new(stage/('BUILD_VERIFIED.json' if success else 'BUILD_FAILED.json'),result)
    need(success,'REVIEW_BUILD_UNQUALIFIED')
    print(json.dumps({'passed':True,'review':str(stage),'open_studio':str(stage/'Open Studio.bat'),'open_junko':str(stage/'Open Junko.bat')}))
    return 0

if __name__=='__main__': raise SystemExit(main())
