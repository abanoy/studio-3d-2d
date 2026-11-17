"""Bounded root-only normal-probe prerequisites; no engine/process inventory."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).resolve().parents[2]
LOCK_SHA='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
REQUIRED_FILES={'blend','mdl','vvd','glb','parameters','blender_exe','probe','exporter_extract','exporter_constants','sourceio_import','full_receipt','closure_receipt'}
CONTEXT_FILES={'state','launch','birth','source_before','source_after','report','host','raw_host','release'}


def require(value,message):
    if not value:raise ValueError(message)


def sha(body):return hashlib.sha256(body).hexdigest()


def safe_path(value):
    path=Path(value)
    require(path.is_absolute(),'Absolute locked path required')
    for parent in (path,*path.parents):
        if parent.exists():require(not parent.is_symlink() and not getattr(parent.lstat(),'st_file_attributes',0)&0x400,'Reparse path refused')
    return path.resolve()


def load(path):return json.loads(path.read_bytes())


def validate_context(data, hashes, run_name, expected_commit, expected_count):
    """Pure validator, also tested with explicitly synthetic dictionaries."""
    require(set(data)==CONTEXT_FILES and set(hashes)==CONTEXT_FILES,'Complete actual full context required')
    state,launch,birth,before,after,report,host,raw,release=(data[key] for key in ('state','launch','birth','source_before','source_after','report','host','raw_host','release'))
    require(state.get('format')=='has_owned_canonical_run_1' and state.get('status')=='passed' and type(state.get('suite_exit')) is int and state['suite_exit']==0 and state.get('source_unchanged') is True,'Fresh complete default PASS required')
    require(state.get('source_commit')==expected_commit and state.get('finished_utc') and state.get('started_utc'),'Actual full source/timing required')
    require(launch.get('source_commit')==expected_commit and launch.get('pid')==state.get('pid') and launch.get('creation_utc')==state.get('process_started') and launch.get('run_folder')==state.get('run_folder'),'Launch/state identity differs')
    require(birth.get('format')=='has_root_full_child_birth_observation_1' and birth.get('source_commit')==expected_commit and birth.get('coordinator_pid')==state.get('pid') and birth.get('coordinator_birth')==state.get('process_started') and birth.get('python_parent')==state.get('pid') and birth.get('run_folder')==state.get('run_folder'),'Actual child birth context differs')
    require(before==after and hashes['source_before']==hashes['source_after'] and before.get('commit')==expected_commit and type(before.get('source_sha256')) is dict and len(before['source_sha256'])==expected_count,'Exact full source catalogue required')
    require(type(report) is dict and len(report)==157,'Current complete verifier report required')
    require(before['source_sha256'].get('tests/verify.py')=='459b90eeeae9d5523654c07fcbb3de27dad0e889943f46947333e8eb5a65437a','Default full verifier source differs')
    require(host.get('source_commit')==expected_commit and host.get('canonical_run')==run_name and host.get('coordinator_pid')==state.get('pid') and host.get('python_pid')==birth.get('python_pid') and host.get('expected_creation_utc')==birth.get('coordinator_birth') and host.get('expected_python_creation_utc')==birth.get('python_birth') and host.get('raw_observation_sha256')==hashes['raw_host'],'Actual flat host binding differs')
    for key in ('coordinator_absent','python_absent','owned_runtime_command_matches_absent','source_before_after_and_current_exact'):
        require(host.get(key) is True,'Authoritative host closure incomplete')
    require(host.get('functional_source_entries')==expected_count and host.get('coordinator_matches')==[] and host.get('owned_runtime_matches')==[],'Host scope differs')
    require(raw.get('source_commit')==expected_commit and raw.get('state_status')=='passed' and raw.get('suite_exit')==0 and raw.get('checked_utc')==host.get('observed_utc') and raw.get('root_birth_observation_sha256')==hashes['birth'],'Actual raw host binding differs')
    require(raw.get('canonical_run')==state.get('run_folder') and raw.get('owned_runtime_command_matches_absent') is True and raw.get('owned_runtime_matches')==[] and raw.get('functional_source_entries')==expected_count and raw.get('source_before_after_and_current_exact') is True,'Actual raw host scope differs')
    for role,pid,born in (('coordinator',state['pid'],birth['coordinator_birth']),('python',birth['python_pid'],birth['python_birth'])):
        require(raw.get(role,{}).get('pid')==pid and raw[role].get('expected_creation_utc')==born and raw[role].get('original_absent') is True,'Actual raw process closure differs')
    require(release.get('format')=='has_root_canonical_graphics_lease_release_1' and release.get('released') is True and release.get('source_commit')==expected_commit and release.get('canonical_run')==run_name and release.get('coordinator_pid')==state['pid'] and release.get('python_pid')==birth['python_pid'],'Actual graphics release differs')
    require(release.get('all_private_jobs_closed') is True and release.get('owned_runtime_command_matches_absent') is True and release.get('functional_source_entries')==expected_count and release.get('canonical_state_sha256')==hashes['state'] and release.get('host_proof_sha256')==hashes['host'] and release.get('full_report_sha256')==hashes['report'] and release.get('normalized_log_report_suffix_equal') is True,'Full receipt/graphics closure is not bound')
    return before['source_sha256']


def read_context(run, expected_commit, expected_count):
    run=safe_path(run);require(run.is_relative_to(ROOT/'output'),'Full run must be owned output')
    paths={key:run/name for key,name in {'state':'state.json','launch':'launch.json','birth':'root-birth-observation.json','source_before':'source-before.json','source_after':'source-after.json','host':'authoritative-host-termination.json','raw_host':'authoritative-host-terminal.json','release':'graphics-lease-released.json'}.items()}
    paths['report']=ROOT/'output/verification.json'
    # Gate status before opening terminal-only files; no output or native IO.
    state=load(paths['state']);require(state.get('status')=='passed' and state.get('source_unchanged') is True,'Full is not an actual completed unchanged PASS')
    require(Path(state['run_folder']).resolve()==run and Path(state['checkout']).resolve()==ROOT,'Actual full workspace/path differs')
    blobs={key:safe_path(path).read_bytes() for key,path in paths.items()}
    data={key:json.loads(body) for key,body in blobs.items()};hashes={key:sha(body) for key,body in blobs.items()}
    sources=validate_context(data,hashes,run.name,expected_commit,expected_count)
    start=datetime.datetime.fromisoformat(state['started_utc'].replace('Z','+00:00'));finish=datetime.datetime.fromisoformat(state['finished_utc'].replace('Z','+00:00'))
    stamp=datetime.datetime.fromtimestamp(paths['report'].stat().st_mtime,datetime.timezone.utc)
    require(start<=stamp<=finish,'Full report is stale')
    normalized=blobs['report'].decode('utf-8-sig').replace('\r\n','\n').rstrip()
    log=(run/'canonical.log').read_text(encoding='utf-8-sig').replace('\r\n','\n').rstrip()
    require(log.endswith(normalized),'Canonical report/log differs')
    require(all(not line.strip() or line.startswith('PASS ') for line in log[:-len(normalized)].splitlines()),'Canonical full log contains unexpected output')
    current={p.relative_to(ROOT).as_posix() for name in ('src','tests','tools','data','examples') for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    current.update(('project.godot','main.tscn','run.py','launch.pyw'))
    require(current==set(sources),'Current functional membership differs')
    for name,digest in sources.items():require(sha(safe_path(ROOT/name).read_bytes())==digest,'Current functional source differs')
    return {'run':str(run),'expected_commit':expected_commit,'functional_count':expected_count,'files':{key:{'path':str(paths[key]),'sha256':hashes[key]} for key in paths}}


def check_context_lock(context):
    actual=read_context(context['run'],context['expected_commit'],context['functional_count'])
    require(actual==context,'Full/closure context changed since root staging')


def check_lease(lease_path, current_probe):
    lease_path=safe_path(lease_path);lease=load(lease_path)
    require(lease.get('format')=='has_blender_normal_probe_lease_1' and lease.get('phase')=='ROOT_APPROVED_AFTER_FULL_PASS' and lease.get('publish_private_arrays') is False,'Actual root post-PASS lease required')
    require(set(lease.get('files',{}))==REQUIRED_FILES,'Exact12 locks required')
    expires=datetime.datetime.fromisoformat(lease['expires_utc'].replace('Z','+00:00'));require(datetime.datetime.now(datetime.timezone.utc)<expires,'Root lease expired')
    check_context_lock(lease['full_context'])
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0).strip()
    require(head==lease['HEAD'],'Current root HEAD differs')
    files={}
    for name,row in lease['files'].items():
        path=safe_path(row['path']);require(path.is_file() and sha(path.read_bytes())==row['sha256'],'Locked file changed: '+name);files[name]=path
    require(set(lease.get('analysis_files',{}))=={'support','metrics','comparator','matcher'},'Complete analysis source pins required')
    for row in lease['analysis_files'].values():require(sha(safe_path(row['path']).read_bytes())==row['sha256'],'Pinned analysis source changed')
    require(files['probe']==Path(current_probe).resolve(),'Wrong capture source')
    require(files['full_receipt']==Path(lease['full_context']['files']['state']['path']) and files['closure_receipt']==Path(lease['full_context']['files']['release']['path']),'12-lock full/closure aliases differ')
    require(sha(safe_path(lease['original_blend']['path']).read_bytes())==lease['original_blend']['sha256']==lease['files']['blend']['sha256'],'Original/copied blend identity differs')
    return lease,files
