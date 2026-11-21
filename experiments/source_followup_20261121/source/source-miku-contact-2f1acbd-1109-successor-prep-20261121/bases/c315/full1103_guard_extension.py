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
