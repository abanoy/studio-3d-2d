"""Current-source/closed-parent/approved-runtime gates for the future setter probe."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
LOCK=ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
OLD_SUPPORT=ROOT/'experiments/normal_boundary_probe_20261116/probe_support.py'
OLD_SUPPORT_SHA='71fc6b8ddd270fc40a42212dad3e1a7fd64d24b8e7c401ee32d1744c8b00adf0'
READER=ROOT/'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
READER_SHA='5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'
ROLES={'mdl','vvd','vtx','saved_capture','prior_public','prior_comparison','prior_execution','prior_closure','blender_exe','probe','support','instrumentation','vvd_parser','approved_lock','identity_reader','normal_support','bridge','importer','sourceio_common','sourceio_fastmesh','sourceio_vvd','sourceio_vtx','sourceio_vtx_init','sourceio_mdl','full_state','graphics_release'}
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def safe(value):
    p=Path(value);require(p.is_absolute(),'Absolute path required')
    for a in (p,*p.parents):
        if a.exists():require(not a.is_symlink() and not getattr(a.lstat(),'st_file_attributes',0)&0x400,'Reparse path refused')
    return p.resolve()
def module(path,name,expected):
    require(sha(path.read_bytes())==expected,'Pinned prerequisite source differs')
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def normal_support():return module(OLD_SUPPORT,'setter_previous_context_support',OLD_SUPPORT_SHA)
def approved():
    require(sha(LOCK.read_bytes())==LOCK_SHA,'Approved input lock differs')
    lock=json.loads(LOCK.read_bytes());r=module(READER,'setter_approved_identity_reader',READER_SHA)
    require(len(lock['runtime_executables'])==6 and all(r.identity(Path(n))==v for n,v in lock['runtime_executables'].items()),'Approved runtime identity differs')
    require(len(lock['sourceio_files'])==574 and r.metadata_map(r.SOURCEIO)==lock['sourceio_files'],'Approved SourceIO574 catalogue differs')
    require(len(lock['exporter_noncache_sources'])==120 and r.metadata_map(Path(lock['exporter_root']),'exporter')==lock['exporter_noncache_sources'],'Approved exporter120 catalogue differs')
    return lock
def validate_prior(paths):
    public=json.loads(paths['prior_public'].read_bytes());comparison=json.loads(paths['prior_comparison'].read_bytes());execution=json.loads(paths['prior_execution'].read_bytes());closure=json.loads(paths['prior_closure'].read_bytes())
    require(public['private_sha256']==sha(paths['saved_capture'].read_bytes())==comparison['private_capture_sha256'],'Saved capture hash differs')
    require(comparison['status']=='COHERENT_BOUNDARY_MEASUREMENT' and type(comparison['matched_exported_vertices']) is int and comparison['matched_exported_vertices']==9661 and type(comparison['unmatched_exported_vertices']) is int and comparison['unmatched_exported_vertices']==0 and comparison['original_raw_gate']['historical_failure_reproduced'] is True,'Actual prior normal comparison required')
    require(execution['diagnostic_completed'] is True and execution['private_job_desktop_closed'] is True and execution['runtime_lease_released'] is True and execution['comparison_sha256']==sha(paths['prior_comparison'].read_bytes()) and execution['public_capture_sha256']==sha(paths['prior_public'].read_bytes()),'Prior probe was not fully completed/closed')
    require(type(closure['owned_count']) is int and closure['owned_count']==0,'Actual prior probe closure required')
    return {'private_capture_sha256':public['private_sha256'],'comparison_sha256':sha(paths['prior_comparison'].read_bytes()),'prior_closed':True}
def check_lease(path,probe):
    path=safe(path);lease=json.loads(path.read_bytes())
    require(lease.get('format')=='has_sourceio_setter_boundary_lease_1' and lease.get('phase')=='ROOT_APPROVED_AFTER_CLOSED_NORMAL_PROBE' and lease.get('private_arrays_public') is False,'Fresh bounded root setter lease required')
    require(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(lease['expires_utc']),'Setter lease expired')
    require(set(lease['files'])==ROLES,'Complete setter source/input role set required')
    files={}
    for name,row in lease['files'].items():
        p=safe(row['path']);require(p.is_file() and sha(p.read_bytes())==row['sha256'],'Locked setter input/source differs: '+name);files[name]=p
    require(files['probe']==Path(probe).resolve() and files['support']==Path(__file__).resolve(),'Wrong setter source')
    require(files['approved_lock']==LOCK and files['identity_reader']==READER and files['normal_support']==OLD_SUPPORT,'Prerequisite source aliases differ')
    expected=lease['full_context']
    require(files['full_state']==Path(expected['files']['state']['path']) and files['graphics_release']==Path(expected['files']['release']['path']),'Full receipt aliases differ')
    actual=normal_support().read_context(expected['run'],expected['expected_commit'],expected['functional_count']);require(actual==expected,'Completed full context changed')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0).strip();require(head==lease['expected_head'],'Current metadata checkpoint differs')
    require(validate_prior(files)==lease['prior_context'],'Prior normal context changed')
    lock=approved();require(Path(lease['sourceio_root'])==ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647','Wrong source runtime root')
    target=safe(lease['private_output']);require(target.is_relative_to(ROOT/'output') and target!=ROOT/'output','Private output boundary differs')
    return lease,files
