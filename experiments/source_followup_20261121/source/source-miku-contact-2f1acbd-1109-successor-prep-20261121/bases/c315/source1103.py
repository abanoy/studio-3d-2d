"""Independent exactc315/1103 provenance admission, source only and UNRUN.
Never invoke the historical1084/1086 qualification mains or validators.
"""
from pathlib import Path
import hashlib
import os
import re
import stat
REVISION='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
BASELINE_PIN=(284660, 'a2fd8aa45d82e5820a30686c84247f6b1f69833b7e45b7fe5c35f2d1a309f062')
FULL_CLONE='has-import-off-full-20261121-c31576d'
FLAGS=('whole_verifier_pass','child_reaped','functional_sources_unchanged','revision_unchanged',
       'fresh_final_report','all_private_jobs_isolated_closed','nonzero_jobs_are_expected_cancellations',
       'receipt_provenance_verified')
NEW_GROUPS={'editor_controls_geometry':37,'editor_controls_face':36,'editor_controls_handles':38,
            'camera_interactions_pure':67}
for theme in ('classic','neon'):
    for scale in (100,150):
        for workspace in ('simple','advanced'):
            NEW_GROUPS['camera_interactions_'+theme+'-'+str(scale)+'-'+workspace]=56
ROOT_FILES=('dependencies.json','launch.pyw','main.tscn','project.godot','run.py')
EXPERIMENTS=tuple('experiments/reference_body_20261120/'+name for name in (
    'receipt_provenance.py','run_full.py','run_scoped.py','stage_legacy_inputs.py',
    'test_receipt_provenance.py','verify_units.py'))

def need(value,code):
    if not value:raise ValueError(code)

def completion_contract(value):
    need(type(value) is dict and value.get('format')=='has_reference_body_full_coordinator_1','FULL_FORMAT')
    need(value.get('revision')==REVISION,'FULL_EXACTc315_REVISION')
    need(all(value.get(key) is True for key in FLAGS),'FULL_STRONG_QUALIFICATION_FLAGS')
    need(type(value.get('exit')) is int and value['exit']==0,'FULL_ZERO_EXIT')
    need(type(value.get('functional_source_count')) is int and value['functional_source_count']==1103,'FULL_EXACT1103')
    need(type(value.get('result_groups')) is int and value['result_groups']==182,'FULL_EXACT182_GROUPS')

def report_contract(report):
    need(type(report) is dict and len(report)==182,'REPORT_EXACT182_GROUPS')
    for name,count in NEW_GROUPS.items():
        row=report.get(name)
        need(type(row) is dict and row.get('status')=='PASS' and type(row.get('checks')) is int
             and row['checks']==count and row.get('all_admitted_sources_unchanged') is True,'REPORT_NEW_GROUP_'+name)
        if name.startswith('editor_controls_'):
            need(row.get('generated_fixture_preserved') is True,'REPORT_EDITOR_FIXTURE_'+name)

def source_contract(baseline,catalogue):
    need(type(baseline) is dict and type(catalogue) is dict and len(baseline)==len(catalogue)==1103
         and set(baseline)==set(catalogue),'FULL_MAIN_EXACT_SOURCE_DOMAIN')
    need(len({name.casefold() for name in baseline})==1103,'SOURCE_CASE_ALIAS')
    for name,expected in baseline.items():
        row=catalogue[name]
        need(type(row) is dict and type(row.get('bytes')) is int and row['bytes']>=0
             and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) is not None
             and re.fullmatch('[0-9a-f]{40}',row.get('git_sha1','')) is not None
             and type(row.get('mtime_ns')) is int and row['mtime_ns']>=0,'FULL_SOURCE_ROW')
        need(all(row.get(key)==expected.get(key) for key in ('bytes','sha256','git_sha1')),'FULL_MAIN_SOURCE_BYTES_'+name)

def domain(H,root):
    names=set(ROOT_FILES)|set(EXPERIMENTS)
    def walk_error(error):raise error
    for prefix in ('src','tests','tools','examples','data'):
        for folder,dirs,files in os.walk(H.safe(root/prefix),followlinks=False,onerror=walk_error):
            for item in dirs:H.safe(Path(folder)/item)
            dirs[:]=[item for item in dirs if item not in ('__pycache__','.godot','.git')]
            for item in files:
                if item.endswith(('.pyc','.pyo')):continue
                path=H.safe(Path(folder)/item)
                need(stat.S_ISREG(path.lstat().st_mode),'SPECIAL_SOURCE_PATH')
                names.add(path.relative_to(root).as_posix())
    need(len(names)==1103 and len({name.casefold() for name in names})==1103,'MAIN_EXACT1103_DOMAIN')
    return names

def admit_main(H,root,here):
    document=H.parse(H.read(here/'BASELINE_SOURCE1103.json',*BASELINE_PIN))
    need(document.get('format')=='has_exact_main1103_source_baseline_1'
         and document.get('revision')==REVISION and document.get('source_count')==1103,'MAIN_BASELINE_FORMAT')
    baseline=document['files']
    need(type(baseline) is dict and len(baseline)==1103 and domain(H,root)==set(baseline),'CURRENT1103_MAIN_DOMAIN')
    for name,row in baseline.items():
        path=root/H.rel(name);data=H.read(path,row['bytes'],row['sha256'])
        need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1'],'MAIN_BASELINE_GIT_BYTES')
        need(path.lstat().st_mtime_ns==int(row['main_mtime_ns']),'PREPARED_MAIN_SOURCE_STAMP_CHANGED')
    return baseline

def admit_full(H,root,here,folder,completion_sha,source_sha,report_sha,outer_folder,outer_launch_sha,outer_completion_sha):
    for value in (completion_sha,source_sha,report_sha):need(re.fullmatch('[0-9a-f]{64}',value) is not None,'EXTERNAL_FULL_SHA256_REQUIRED')
    folder=H.safe(folder)
    clone=H.safe(root.parent/FULL_CLONE)
    need(folder.parent==clone/'output' and folder.name.startswith('windows-reference-body-'),'RESERVED_CANONICAL_FULL_FOLDER')
    need(not (clone/'override.cfg').exists() and not (clone/'project.binary').exists(),'CANONICAL_FULL_NO_OVERRIDE')
    completion=H.parse(H.read(folder/'completion.json',digest=completion_sha,limit=16*1024*1024))
    completion_contract(completion)
    before_raw=H.read(folder/'source-before.json',digest=source_sha,limit=4*1024*1024)
    after_raw=H.read(folder/'source-after.json',digest=source_sha,limit=4*1024*1024)
    need(before_raw==after_raw,'FULL_SOURCE_RAW_EQUALITY')
    catalogue=H.parse(before_raw)
    baseline_document=H.parse(H.read(here/'BASELINE_SOURCE1103.json',*BASELINE_PIN))
    need(baseline_document.get('format')=='has_exact_main1103_source_baseline_1'
         and baseline_document.get('revision')==REVISION and baseline_document.get('source_count')==1103,'MAIN_BASELINE_FORMAT')
    baseline=baseline_document['files'];source_contract(baseline,catalogue)
    report=H.parse(H.read(clone/'output/verification.json',digest=report_sha,limit=64*1024*1024))
    report_contract(report)
    groups=H.parse(H.read(here/'FULL182_GROUP_CONTRACT.json',*GROUP_PIN))
    exact_group_contract(completion,report,groups)
    launch=H.parse(H.read(folder/'launch.json',limit=1024*1024))
    need(launch.get('revision')==REVISION and type(launch.get('started_ns')) is int
         and launch['started_ns'] <= (clone/'output/verification.json').lstat().st_mtime_ns <= (folder/'completion.json').lstat().st_mtime_ns,'FRESH_FULL_REPORT_WINDOW')
    admit_outer_and_receipts(H,root,clone,folder,baseline,completion,launch,outer_folder,outer_launch_sha,outer_completion_sha)
    need(domain(H,root)==set(baseline),'CURRENT1103_FULL_DOMAIN')
    for name,row in baseline.items():
        path=root/H.rel(name);H.read(path,row['bytes'],row['sha256'])
        need(path.lstat().st_mtime_ns==int(row['main_mtime_ns']),'PREPARED_MAIN_SOURCE_STAMP_CHANGED')
    # Full checkout timestamps intentionally differ from Main. Each is preserved
    # independently; only bytes/Git blob IDs bind the two source catalogues.
    return baseline

def immutable_runtime(H,Q,root,baseline):
    row=baseline['tools/build_owner_review_snapshot.py']
    builder,_=Q.load_pinned('_mikuc315_runtime_builder',root/'tools/build_owner_review_snapshot.py',row['bytes'],row['sha256'])
    need(builder.ROOT==root,'CURRENT_SNAPSHOT_READER_ROOT')
    tree=H.subprocess.check_output(['git','ls-tree','-r','-z',REVISION],cwd=root,timeout=60,creationflags=H.subprocess.CREATE_NO_WINDOW)
    entries=[];git_rows={}
    for record in tree.split(b'\0'):
        if not record:continue
        meta,name=record.split(b'\t',1);mode,kind,oid=meta.split();name=name.decode('utf-8')
        if not builder.included(name):continue
        need(mode in (b'100644',b'100755') and kind==b'blob','SOURCE_GIT_MODE')
        builder.validate_name(name);need(name not in git_rows,'DUPLICATE_GIT_PATH')
        entries.append((name,oid));git_rows[name]=oid.decode('ascii')
    need(len({name.casefold() for name in git_rows})==len(git_rows),'SOURCE_GIT_CASE_ALIAS')
    git_functional={name for name in git_rows if name in ROOT_FILES or name in EXPERIMENTS
                    or (name.split('/',1)[0] in ('src','tests','tools','examples','data')
                        and not name.endswith('.pyc') and '__pycache__' not in Path(name).parts)}
    need(git_functional==set(baseline),'EXACT_CURRENT1103_GIT_FUNCTIONAL_DOMAIN')
    need(set(baseline)<=git_rows.keys(),'CURRENT1103_GIT_DOMAIN')
    need(all(git_rows[name]==row['git_sha1'] for name,row in baseline.items()),'CURRENT1103_GIT_BLOBS')
    selected,cached=builder._runtime_entries(root,entries,REVISION)
    frozen={name:cached[name] for name,_ in selected}
    need(all(not name.startswith(('experiments/','output/','.git/','.godot/')) and '__pycache__' not in Path(name).parts
             and not name.endswith(('.pyc','.pyo')) for name in frozen),'RUNTIME_RESOURCE_SCOPE')
    expected_runtime={name for name in baseline if not name.startswith('experiments/')}
    need(len(expected_runtime)==1097 and expected_runtime<=frozen.keys(),'ALL1097_FUNCTIONAL_RUNTIME_SOURCES')
    for name in expected_runtime:
        need(len(frozen[name])==baseline[name]['bytes'] and H.sha(frozen[name])==baseline[name]['sha256'],'CURRENT_RUNTIME_BLOB_BYTES')
    return frozen


"""Pure admission contracts plus read-only Full evidence validation.
This file is concatenated with source1103_base.py, not loaded as a launcher.
"""
GROUP_PIN=(5673,'83c97507425ce7e886044fdb934711ef50fc55b95fd1f804f0da09cada0eccc6')
PHYSICAL=('desktop','child_pid','exit','seconds','job_closed','desktop_closed','private_window_seen',
          'child_desktop_confirmed','foreground_child_observed','desktop_switch_requested','cancelled','error')

def exact_group_contract(completion,report,groups):
    need(type(groups) is dict and groups.get('format')=='has_exact_full182_group_contract_1'
         and groups.get('revision')==REVISION,'EXACT_GROUP_CONTRACT_FORMAT')
    names=groups.get('expected_group_keys')
    need(type(names) is list and len(names)==len(set(names))==182 and set(report)==set(names),'EXACT_FULL182_GROUP_KEYS')
    need(groups.get('new_groups')==NEW_GROUPS and sum(NEW_GROUPS.values())==626,'EXACT_NEW626_CONTRACT')
    movies=sorted(name for name in names if name.endswith('_video') or name.startswith('posed_model_video_'))
    actual=completion.get('movie_groups')
    need(len(movies)==21 and sorted(groups.get('movie_groups',[]))==movies
         and type(actual) is list and len(actual)==21 and len(set(actual))==21
         and sorted(actual)==movies,'EXACT_21_MOVIE_GROUP_KEYS')

def physical_receipt_contract(value):
    need(type(value) is dict and value.get('format')=='studio_private_desktop_1'
         and type(value.get('desktop')) is str and 0<len(value['desktop'])<=256
         and type(value.get('child_pid')) is int and value['child_pid']>0
         and type(value.get('exit')) is int,'GENUINE_TYPED_PRIVATE_RECEIPT')
    need(all(value.get(key) is True for key in ('job_closed','desktop_closed','child_desktop_confirmed'))
         and value.get('foreground_child_observed') is False and value.get('desktop_switch_requested') is False,
         'ACTUAL_PRIVATE_RECEIPT_CLOSED_ISOLATED')
    need(value['exit']==0 or (value['exit']==2 and value.get('cancelled') is True
         and value.get('error')=='Owned converter cancelled'),'UNEXPECTED_PRIVATE_JOB_EXIT')

def receipt_contract(completion,classification):
    need(type(classification) is dict and classification.get('conflicts')==[]
         and classification.get('changed_original_archives')==[],'CURRENT_RECEIPT_PROVENANCE_CLEAN')
    current=classification.get('current');jobs=completion.get('current_jobs')
    need(type(current) is list and 0<len(current)<=100000 and type(jobs) is list
         and 0<len(jobs)<=100000,'NONEMPTY_CURRENT_PRIVATE_JOB_DOMAIN')
    need(type(completion.get('unique_current_private_jobs')) is int
         and completion['unique_current_private_jobs']==len(jobs)
         and type(completion.get('new_receipt_paths')) is int
         and completion['new_receipt_paths']==len(current),'PRIVATE_JOB_COUNTS_EXACT')
    by_desktop={};paths=set()
    for row in current:
        need(type(row) is dict and set(row)=={'path','sha256','value'}
             and type(row.get('path')) is str and row['path'].startswith('output/')
             and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) is not None,'CURRENT_RECEIPT_ROW')
        need(row['path'] not in paths,'DUPLICATE_CURRENT_RECEIPT_PATH');paths.add(row['path'])
        value=row['value'];physical_receipt_contract(value);desktop=value['desktop']
        if desktop in by_desktop:
            need(all(value.get(k)==by_desktop[desktop]['value'].get(k) for k in PHYSICAL),'DUPLICATE_RECEIPT_PHYSICAL_CONFLICT')
        else:by_desktop[desktop]=row
    need(len(jobs)==len(by_desktop),'COMPLETE_DEDUPLICATED_JOB_DOMAIN')
    seen=set();nonzero=[]
    for row in jobs:
        need(type(row) is dict and set(row)=={'path','sha256','value'},'COMPLETION_JOB_SCHEMA')
        physical_receipt_contract(row['value']);d=row['value']['desktop']
        need(d not in seen and d in by_desktop and row==by_desktop[d],'COMPLETION_ACTUAL_RECEIPT_BINDING');seen.add(d)
        if row['value']['exit']!=0:nonzero.append(row)
    need(len(nonzero)==1 and completion.get('nonzero_private_jobs')==nonzero,'EXACT_ONE_EXPECTED_CANCEL')

def outer_contract(launch,completion,clone,outer,coordinator_sha):
    need(type(launch) is dict and launch.get('format')=='has_import_off_full_outer_launch_1'
         and launch.get('revision')==REVISION and Path(launch.get('checkout',''))==clone
         and type(launch.get('pid')) is int and launch['pid']>0
         and type(launch.get('started_ns')) is int and launch['started_ns']>0
         and launch.get('coordinator_sha256')==coordinator_sha
         and launch.get('parent_environment_changed') is False
         and launch.get('hidden_console') is True
         and launch.get('graphical_tests_must_use_private_desktops') is True,'ISOLATED_OUTER_LAUNCH')
    env=launch.get('child_environment');need(type(env) is dict,'ISOLATED_OUTER_ENVIRONMENT')
    for key,leaf in (('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')):
        need(type(env.get(key)) is str and Path(env[key])==outer/'User'/leaf,'FOUR_EXACT_FRESH_USER_DIRECTORIES')
    need(env.get('PYTHONDONTWRITEBYTECODE')=='1','OUTER_BYTECODE_DISABLED')
    need(type(completion) is dict and completion.get('format')=='has_import_off_full_outer_completion_1'
         and type(completion.get('exit')) is int and completion['exit']==0
         and type(completion.get('pid')) is int and completion['pid']==launch['pid']
         and completion.get('launch')==launch
         and all(completion.get(k) is True for k in ('child_reaped','parent_environment_unchanged',
                   'coordinator_source_unchanged','revision_unchanged')),'COMPLETED_SUCCESSFUL_OUTER_FULL')

def admit_outer_and_receipts(H,root,clone,folder,baseline,completion,inner_launch,outer,outer_launch_sha,outer_completion_sha):
    for value in (outer_launch_sha,outer_completion_sha):
        need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'EXTERNAL_OUTER_FULL_PINS_REQUIRED')
    outer=H.safe(outer)
    need(outer.parent==clone/'output' and outer.name.startswith('root-full-launch-'),'RESERVED_OUTER_FULL_FOLDER')
    outer_launch=H.parse(H.read(outer/'launch.json',digest=outer_launch_sha,limit=1024*1024))
    outer_done=H.parse(H.read(outer/'completion.json',digest=outer_completion_sha,limit=1024*1024))
    outer_contract(outer_launch,outer_done,clone,outer,baseline['experiments/reference_body_20261120/run_full.py']['sha256'])
    for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):H.safe(Path(outer_launch['child_environment'][key]))
    need(type(inner_launch.get('coordinator_pid')) is int and inner_launch['coordinator_pid']==outer_launch['pid']
         and outer_launch['started_ns']<=inner_launch['started_ns']
         <=(clone/'output/verification.json').lstat().st_mtime_ns
         <=(folder/'completion.json').lstat().st_mtime_ns
         <=(outer/'completion.json').lstat().st_mtime_ns,'SAME_FINISHED_OUTER_INNER_FULL_WINDOW')
    classification=H.parse(H.read(folder/'receipt-provenance.json',limit=64*1024*1024))
    receipt_contract(completion,classification)
    # Bind every current path to actual persisted receipt bytes, including
    # duplicate physical job receipts. Old archived copies stay in their own
    # classification and cannot satisfy a new/current job's closure.
    for row in classification['current']:
        relative=H.rel(row['path']);need(relative.startswith('output/'),'CURRENT_RECEIPT_INSIDE_CLONE_OUTPUT')
        actual=H.parse(H.read(clone/relative,digest=row['sha256'],limit=1024*1024))
        need(actual==row['value'],'ACTUAL_RECEIPT_BYTES_AND_REPORTED_FIELDS')
        physical_receipt_contract(actual)
    need(type(classification.get('unchanged_prior_paths')) is list
         and type(completion.get('unchanged_prior_receipt_paths')) is int
         and completion['unchanged_prior_receipt_paths']==len(classification['unchanged_prior_paths'])
         and type(classification.get('archived_copies')) is list
         and type(completion.get('byte_proven_archived_copy_paths')) is int
         and completion['byte_proven_archived_copy_paths']==len(classification['archived_copies']),
         'PRIOR_ARCHIVE_CLASSIFICATION_COUNTS')
