"""Root-only isolated component checks; source authored without execution.

Four independent e087 Studio copies. Candidate overlays and the three radial
app anchors live only inside their suite copy. No current application adoption,
actual native assets, SDK, Blender, rendering qualification or editor Full claim.
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

INPUTS = [
    {
        "suite": "default_off",
        "source": "output/import-physics-default-off-prep-20261120/payload/src/import_actions.gd",
        "target": "src/import_actions.gd",
        "bytes": 3870,
        "sha256": "3f280041d2f09a6fbd956d0e56d2bc6f8ced11453bbf794fbde0c223495dd8f2"
    },
    {
        "suite": "default_off",
        "source": "output/import-physics-default-off-prep-20261120/payload/tests/import_physics_defaults_unit.gd",
        "target": "tests/import_physics_defaults_unit.gd",
        "bytes": 4701,
        "sha256": "dbee24031470b4b779d636ba7225ccb86959391813ed26610362877e4a3e2dc7"
    },
    {
        "suite": "selection",
        "source": "output/source-loose-part-selection-prep-20261120/loose_part_selection.gd",
        "target": "src/loose_part_selection.gd",
        "bytes": 3351,
        "sha256": "d34f10fac37fa108c3727d4aafe96989db6a76273b4815672141dae8ee195758"
    },
    {
        "suite": "selection",
        "source": "output/source-loose-part-selection-prep-20261120/loose_part_selector.gd",
        "target": "src/loose_part_selector.gd",
        "bytes": 8583,
        "sha256": "c9d9ac270e8753092fea0c51eb1d65d765455187ba68907bcc5d33114f448624"
    },
    {
        "suite": "selection",
        "source": "output/source-loose-part-selection-prep-20261120/loose_part_selection_unit.gd",
        "target": "tests/loose_part_selection_unit.gd",
        "bytes": 9574,
        "sha256": "41899631f0823c01ab4eddef220b9e65ef7a0b462f4a80cd08dffb14b0b90a4c"
    },
    {
        "suite": "radial",
        "source": "output/character-tools-radial-prep-20261121/payload/src/character_tools.gd",
        "target": "src/character_tools.gd",
        "bytes": 10450,
        "sha256": "3d6dc85c334360d2f7e2d948d95047eafe19f4b408191322441b83c47abc438f"
    },
    {
        "suite": "radial",
        "source": "output/character-tools-radial-prep-20261121/payload/src/character_tool_policy.gd",
        "target": "src/character_tool_policy.gd",
        "bytes": 3297,
        "sha256": "3e62019de547f9fb6900f17f5e7124d76dcb67a3553b65f877f6f6937bb7b294"
    },
    {
        "suite": "radial",
        "source": "output/character-tools-radial-prep-20261121/payload/src/shortcut_bindings.gd",
        "target": "src/shortcut_bindings.gd",
        "bytes": 4559,
        "sha256": "c8ccc33ddf29aac16af627dcaa0b12214f8c1492abf0933d0ebbfb9a959e17cc"
    },
    {
        "suite": "radial",
        "source": "output/character-tools-radial-prep-20261121/payload/src/shortcut_editor.gd",
        "target": "src/shortcut_editor.gd",
        "bytes": 6385,
        "sha256": "7cc71b21681ee9ff67046760a999dbcce75f1d44264998ecd2e73db99edc3ff4"
    },
    {
        "suite": "radial",
        "source": "output/character-tools-radial-prep-20261121/payload/tests/character_tools_unit.gd",
        "target": "tests/character_tools_unit.gd",
        "bytes": 13654,
        "sha256": "b1d218369dc7884150abade272a68f715fcca06ca97b7f9884aa028eef276aeb"
    },
    {
        "suite": "all49",
        "source": "output/source-junko-all49-prep-20261120/source_secondary_all49.gd",
        "target": "src/source_secondary_all49.gd",
        "bytes": 32513,
        "sha256": "ad34fd5d60a0224dc3274d75de53354cb1d0054ce37def64a4c519a053c90edc"
    },
    {
        "suite": "all49",
        "source": "output/source-junko-all49-prep-20261120/source_secondary_all49_unit.gd",
        "target": "tests/source_secondary_all49_unit.gd",
        "bytes": 10082,
        "sha256": "6b4d4279f95c03d5c6b7425f62c3ddbe1669a914195f5a2d23c96439c64e4665"
    }
]
PATCH_PIN = {"path":"output/character-tools-radial-prep-20261121/PATCHES.json","bytes":5104,"sha256":"5ca7d27cb8cd5f066e4074b8e9a17a05cf7424b8c83332c76d91e8eb5505f3f3"}
SUITES = [
    {
        "id": "default_off",
        "unit": "tests/import_physics_defaults_unit.gd",
        "checks": 16,
        "marker": "Import OFF default controls: 16; failures: 0",
        "marker_kind": "line"
    },
    {
        "id": "selection",
        "unit": "tests/loose_part_selection_unit.gd",
        "checks": 32,
        "marker": "LOOSE_PART_SELECTION_UNIT ",
        "marker_kind": "json"
    },
    {
        "id": "radial",
        "unit": "tests/character_tools_unit.gd",
        "checks": 49,
        "marker": "CHARACTER_TOOLS_UNIT ",
        "marker_kind": "json"
    },
    {
        "id": "all49",
        "unit": "tests/source_secondary_all49_unit.gd",
        "checks": 26,
        "marker": "ALL49 authored synthetic checks: 26; failures: 0",
        "marker_kind": "line"
    }
]

def replace_owned(path, raw):
    # Deliberate overlay only after the original fresh-copy identity was admitted.
    key=str(safe(path));need(key in EXPECTED,'OVERLAY_NOT_OWNED')
    read(path)
    with Path(path).open('wb') as stream:
        need(stream.write(raw)==len(raw),'SHORT_OVERLAY_WRITE');stream.flush();os.fsync(stream.fileno())
    EXPECTED.pop(key)
    read(path,len(raw),sha(raw))

def apply_radial_anchors(raw, patch_document):
    need(type(patch_document) is dict and patch_document.get('format')=='has_source_only_character_tools_radial_patch_1','RADIAL_PATCH_SCHEMA')
    rows=[row for row in patch_document.get('patches',[]) if row.get('path')=='src/app.gd']
    need(len(rows)==3 and rows[0].get('base_sha256')==sha(raw),'RADIAL_APP_BASE')
    text=raw.decode('utf-8')
    for row in rows:
        before,after=row.get('before'),row.get('after')
        need(type(before) is str and before and type(after) is str and text.count(before)==1,'RADIAL_ANCHOR_NOT_UNIQUE')
        text=text.replace(before,after,1)
    return text.encode('utf-8')

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

def job(studio, case, name, godot_args, runtime, env, rows):
    receipt=case/(name+'-private.json')
    command=[runtime['pythonw'],'-B','-s',str(studio/'tools/private_desktop.py'),
        '--receipt',str(receipt),'--timeout','90','--memory-limit-mib','4096','--',
        runtime['godot'],'--headless','--audio-driver','Dummy','--path',str(studio),*godot_args]
    json_new(case/(name+'-command.json'),command)
    row={'name':name,'reaped':False,'private_job_closed':False,'desktop_closed':False,'foreground_child_observed':None,'status':'FAIL'}
    rows.append(row)
    process=None
    try:
        with (case/(name+'-stdout.log')).open('xb') as out,(case/(name+'-stderr.log')).open('xb') as err:
            process=subprocess.Popen(command,cwd=studio,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            OWNED.append((process,row))
            row['pid']=process.pid
            json_new(case/(name+'-launch.json'),{'pid':process.pid,'private_receipt':str(receipt)})
            process.wait(timeout=120)
    finally:
        if process is not None: row['reaped']=reap(process)
    need(row['reaped'],'OWNED_LAUNCHER_UNREAPED')
    proof=parse(read(receipt,limit=1024*1024))
    row.update(private_job_closed=proof.get('job_closed') is True,desktop_closed=proof.get('desktop_closed') is True,
        child_desktop_observed=proof.get('child_desktop_confirmed') is True,
        foreground_child_observed=proof.get('foreground_child_observed'))
    need(proof.get('format')=='studio_private_desktop_1' and row['private_job_closed'] and row['desktop_closed'],'PRIVATE_CLOSURE_UNPROVEN')
    need(proof.get('desktop_switch_requested') is False and proof.get('foreground_child_observed') is False and proof.get('error') is None,'PRIVATE_ISOLATION_FAILED')
    need(process.returncode==0 and type(proof.get('exit')) is int and proof['exit']==0,'COMPONENT_PROCESS_FAILED')
    stdout=read(case/(name+'-stdout.log'),limit=MAX_LOG).decode('utf-8','replace')
    stderr=read(case/(name+'-stderr.log'),limit=MAX_LOG).decode('utf-8','replace')
    need(not re.search(r'(?m)^(?:SCRIPT ERROR:|ERROR:|FAIL )',stdout+'\n'+stderr),'COMPONENT_ENGINE_OR_ASSERTION_ERROR')
    row['status']='PASS'
    return stdout

def validate_marker(stdout, suite):
    lines=stdout.splitlines()
    if suite['marker_kind']=='line':
        need(lines.count(suite['marker'])==1,'COMPONENT_COMPLETE_MARKER')
    else:
        matches=[line[len(suite['marker']):] for line in lines if line.startswith(suite['marker'])]
        need(len(matches)==1,'COMPONENT_COMPLETE_MARKER')
        value=parse(matches[0])
        need(type(value) is dict and type(value.get('checks')) is int and value['checks']==suite['checks']
            and type(value.get('failures')) is int and value['failures']==0,'COMPONENT_COMPLETE_COUNTS')
        need(value.get('application_adopted') is False,'COMPONENT_SCOPE_DIFFERS')
        key='native_or_worker_started' if suite['id']=='selection' else 'native_asset_tested'
        need(value.get(key) is False,'COMPONENT_SCOPE_DIFFERS')
    need(sum(line.startswith('PASS ') for line in lines)==suite['checks'],'COMPONENT_NAMED_CHECK_COUNT')

def preserve():
    failures=[]
    for name,(identity,count,digest) in tuple(EXPECTED.items()):
        try:
            read(name,count,digest,remember=False)
            need(stamp(Path(name).lstat())==identity,'INPUT_STAMP_CHANGED')
        except BaseException as error:
            failures.append({'path':name,'error_type':type(error).__name__})
    return failures

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256',required=True)
    parser.add_argument('--root-exclusive-lane-confirmed',action='store_true')
    args=parser.parse_args()
    need(os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize
        and args.root_exclusive_lane_confirmed,'ROOT_WINDOWS_PYTHON313_LANE_REQUIRED')
    need(re.fullmatch('[0-9a-f]{64}',args.self_sha256) and sha(read(Path(__file__)))==args.self_sha256,'COORDINATOR_PIN')
    need(head()==REVISION,'IMMUTABLE_E087_HEAD_REQUIRED')
    B=load_builder()
    complete,catalogue,_proofs=B.validate_full(FULL,FULL_REVISION,FULL_SHA)
    read(FULL/'completion.json',digest=FULL_SHA)
    for name in ('source-before.json','source-after.json'):read(FULL/name,digest=SOURCE_SHA)
    for name,row in catalogue.items():
        path=ROOT/rel(name);read(path,row['bytes'],row['sha256'])
        need(path.lstat().st_mtime_ns==row['mtime_ns'],'CURRENT_SOURCE_MTIME_DIFFERS')
    frozen=B.source_blobs(REVISION,catalogue)
    need(len(frozen)==1087 and not any(name.startswith(('output/','experiments/','.godot/')) for name in frozen),'RUNTIME_SNAPSHOT_SCOPE')
    lock=parse(read(LOCK,digest=LOCK_SHA))
    for name,row in lock['runtime_executables'].items():
        read(name,row['bytes'],row['sha256'])
        need(Path(name).lstat().st_mtime_ns==row['mtime_ns'],'RUNTIME_MTIME_DIFFERS')
    runtime=lock['runtime_paths']
    need(Path(sys.executable).resolve()==Path(runtime['python']).resolve(),'APPROVED_PYTHON_REQUIRED')
    blobs={}
    for row in INPUTS:
        need(row['suite'] in {suite['id'] for suite in SUITES},'COMPONENT_INPUT_SUITE')
        blobs[row['source']]=read(ROOT/rel(row['source']),row['bytes'],row['sha256'])
    patch=parse(read(ROOT/PATCH_PIN['path'],PATCH_PIN['bytes'],PATCH_PIN['sha256']))
    need(sha(frozen['tools/private_desktop.py'])==PRIVATE_SHA,'PRIVATE_LAUNCHER_PIN')
    stage=ROOT.parent/('has-headless-components-'+str(time.time_ns()))
    safe(stage,missing=True);need(not stage.exists(),'STAGE_EXISTS')
    lane=ROOT/'output/source-headless-components.lock'
    lane_fd=None;lane_identity=None;stage_owned=False;primary=None
    result={'format':'has_isolated_headless_gds_components_1','status':'FAIL','revision':REVISION,
        'qualified_full_revision':FULL_REVISION,'checks_expected':123,'functional_sources':1084,
        'runtime_snapshot_files':len(frozen),'stage':str(stage),'suites':[],
        'application_adopted':False,'native_assets_tested':False,'sdk_or_blender_invoked':False,
        'gui_or_render_qualified':False,'recording_or_actual_motion_qualified':False}
    try:
        safe(lane,missing=True)
        lane_fd=os.open(lane,os.O_CREAT|os.O_EXCL|os.O_RDWR)
        token=uuid.uuid4().hex.encode();need(os.write(lane_fd,token)==len(token),'LANE_WRITE')
        os.fsync(lane_fd);lane_identity=stamp(os.fstat(lane_fd))
        stage.mkdir(exist_ok=False);stage_owned=True
        for suite in SUITES:
            case=stage/suite['id'];case.mkdir();studio=case/'Studio';studio.mkdir()
            for name,raw in frozen.items():
                target=studio/rel(name);target.parent.mkdir(parents=True,exist_ok=True);new(target,raw)
            overlaid=[]
            for row in INPUTS:
                if row['suite']!=suite['id']:continue
                target=studio/rel(row['target']);target.parent.mkdir(parents=True,exist_ok=True)
                raw=blobs[row['source']]
                if target.exists():replace_owned(target,raw)
                else:new(target,raw)
                overlaid.append({'path':row['target'],'bytes':len(raw),'sha256':sha(raw)})
            if suite['id']=='radial':
                raw=apply_radial_anchors(frozen['src/app.gd'],patch)
                replace_owned(studio/'src/app.gd',raw)
                overlaid.append({'path':'src/app.gd','bytes':len(raw),'sha256':sha(raw),'isolated_candidate_anchors':3})
            profile='HAS Headless Components '+uuid.uuid4().hex
            new(studio/'override.cfg',('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
            for name in ('UserData/Roaming','UserData/Local','UserData/Temp'):(case/name).mkdir(parents=True)
            env=os.environ.copy()
            for key in tuple(env):
                if key.startswith('HYBRID_') or key in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX'):env.pop(key,None)
            env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',APPDATA=str(case/'UserData/Roaming'),
                LOCALAPPDATA=str(case/'UserData/Local'),TEMP=str(case/'UserData/Temp'),TMP=str(case/'UserData/Temp'))
            row={'suite':suite['id'],'checks_expected':suite['checks'],'status':'FAIL','overlays':overlaid,'jobs':[]}
            result['suites'].append(row)
            job(studio,case,'import',['--editor','--import','--quit'],runtime,env,row['jobs'])
            stdout=job(studio,case,'unit',['--script','res://'+suite['unit']],runtime,env,row['jobs'])
            validate_marker(stdout,suite)
            row.update(status='PASS',checks_passed=suite['checks'])
        need(len(result['suites'])==4 and all(row['status']=='PASS' for row in result['suites']),'FOUR_COMPONENT_SUITES_REQUIRED')
        result['checks_passed']=sum(row['checks_passed'] for row in result['suites']);result['status']='PASS'
    except BaseException as error:
        primary=error;result['error_type']=type(error).__name__
        result['error_code']=str(error) if type(error) is Refusal else 'COMPONENT_COORDINATOR_EXCEPTION'
    finally:
        for process,row in OWNED:
            row['reaped']=reap(process)
        result['all_owned_launchers_reaped']=all(row['reaped'] for _process,row in OWNED)
        result['all_private_jobs_closed']=all(row['private_job_closed'] and row['desktop_closed'] for _process,row in OWNED)
        failures=preserve();result['input_count']=len(EXPECTED)
        result['all_input_hash_size_mtime_identity_unchanged']=not failures;result['preservation_failures']=failures
        try: result['head_unchanged']=head()==REVISION
        except BaseException: result['head_unchanged']=False
        closure=result['all_owned_launchers_reaped'] and result['all_private_jobs_closed']
        result['owned_lane_removed']=False
        if lane_fd is not None:
            try:
                need(closure and stamp(os.fstat(lane_fd))==lane_identity and stamp(lane.lstat())==lane_identity,'LANE_RETENTION_REQUIRED')
                os.lseek(lane_fd,0,os.SEEK_SET);need(os.read(lane_fd,128)==token,'LANE_IDENTITY_DIFFERS')
                os.close(lane_fd);lane_fd=None
                need(stamp(lane.lstat())==lane_identity,'LANE_PATH_DIFFERS');lane.unlink();result['owned_lane_removed']=True
            except BaseException as error:result['lane_error_type']=type(error).__name__
            finally:
                if lane_fd is not None:os.close(lane_fd)
        if failures or not closure or not result['head_unchanged'] or not result['owned_lane_removed']:result['status']='FAIL'
        if stage_owned:
            json_new(stage/'PUBLIC_COMPONENT_RESULT.json',result)
            print(json.dumps({'status':result['status'],'result':str(stage/'PUBLIC_COMPONENT_RESULT.json'),
                'checks_passed':result.get('checks_passed',0),'error_code':result.get('error_code')}),flush=True)
    return 0 if result['status']=='PASS' and primary is None else 1

if __name__=='__main__':raise SystemExit(main())
