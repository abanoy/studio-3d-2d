"""Independent exact2f1acbd/1109 provenance admission, source only and UNRUN.
Never invoke the historical1084/1086 qualification mains or validators.
"""
from pathlib import Path
import hashlib
import os
import re
import stat
REVISION='2f1acbd7867087d9f18cfbc1122cc0c883c5f788'
BASELINE_PIN=(277374,'467e05f7d731366fe1654e09cb2a23586bc13aab6fe0b955ee46065294aa7da6')
FULL_CLONE='has-import-info-full-20261121-2f1acbd'
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
    need(value.get('revision')==REVISION,'FULL_EXACT2f1acbd_REVISION')
    need(all(value.get(key) is True for key in FLAGS),'FULL_STRONG_QUALIFICATION_FLAGS')
    need(type(value.get('exit')) is int and value['exit']==0,'FULL_ZERO_EXIT')
    need(type(value.get('functional_source_count')) is int and value['functional_source_count']==1109,'FULL_EXACT1109')
    need(type(value.get('result_groups')) is int and value['result_groups']==183,'FULL_EXACT183_GROUPS')

def report_contract(report):
    need(type(report) is dict and len(report)==183,'REPORT_EXACT183_GROUPS')
    info=report.get('import_capability');need(type(info) is dict and info.get('status')=='PASS' and info.get('checks')==267 and len(info.get('cases',[]))==21 and len(info.get('pairs',[]))==8,'REPORT_IMPORT_INFO267')
    for name,count in NEW_GROUPS.items():
        row=report.get(name)
        need(type(row) is dict and row.get('status')=='PASS' and type(row.get('checks')) is int
             and row['checks']==count and row.get('all_admitted_sources_unchanged') is True,'REPORT_NEW_GROUP_'+name)
        if name.startswith('editor_controls_'):
            need(row.get('generated_fixture_preserved') is True,'REPORT_EDITOR_FIXTURE_'+name)

def source_contract(baseline,catalogue):
    need(type(baseline) is dict and type(catalogue) is dict and len(baseline)==len(catalogue)==1109
         and set(baseline)==set(catalogue),'FULL_MAIN_EXACT_SOURCE_DOMAIN')
    need(len({name.casefold() for name in baseline})==1109,'SOURCE_CASE_ALIAS')
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
            dirs[:]=[item for item in dirs if item!='__pycache__']
            for item in files:
                if item.endswith('.pyc'):continue
                path=H.safe(Path(folder)/item)
                need(stat.S_ISREG(path.lstat().st_mode),'SPECIAL_SOURCE_PATH')
                names.add(path.relative_to(root).as_posix())
    need(len(names)==1109 and len({name.casefold() for name in names})==1109,'MAIN_EXACT1109_DOMAIN')
    return names

def admit_main(H,root,here):
    document=H.parse(H.read(here/'BASELINE_SOURCE1109.json',*BASELINE_PIN))
    need(document.get('format')=='has_exact_main1109_source_baseline_1'
         and document.get('revision')==REVISION and document.get('source_count')==1109,'MAIN_BASELINE_FORMAT')
    baseline=document['files']
    need(type(baseline) is dict and len(baseline)==1109 and domain(H,root)==set(baseline),'CURRENT1109_MAIN_DOMAIN')
    for name,row in baseline.items():
        path=root/H.rel(name);data=H.read(path,row['bytes'],row['sha256'])
        need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1'],'MAIN_BASELINE_GIT_BYTES')
        need(path.lstat().st_mtime_ns==int(row['main_mtime_ns']),'PREPARED_MAIN_SOURCE_STAMP_CHANGED')
    return baseline

def admit_full(H,Q,root,here,folder,completion_sha,source_sha,report_sha,outer_folder,outer_launch_sha,outer_completion_sha,postflight_sha):
    for value in (completion_sha,source_sha,report_sha,outer_launch_sha,outer_completion_sha,postflight_sha):
        need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'EXTERNAL_COMPLETED_FULL_AND_POSTFLIGHT_SHA_REQUIRED')
    baseline=admit_main(H,root,here)
    clone=H.safe(root.parent/FULL_CLONE);folder=H.safe(folder);outer=H.safe(outer_folder)
    need(folder.parent==outer.parent==clone/'output' and folder.name=='windows-reference-body-1795270518404649600'
         and outer.name=='root-full-launch-1795270518224140000','EXACT_RETAINED_FULL183_RUN_AND_OUTER')
    need(not (clone/'override.cfg').exists() and not (clone/'project.binary').exists(),'CANONICAL_FULL_NO_OVERRIDE')
    completion=H.parse(H.read(folder/'completion.json',digest=completion_sha,limit=16*1024*1024));completion_contract(completion)
    before_raw=H.read(folder/'source-before.json',digest=source_sha,limit=4*1024*1024)
    need(H.read(folder/'source-after.json',digest=source_sha,limit=4*1024*1024)==before_raw,'FULL_SOURCE_RAW_EQUALITY')
    source_contract(baseline,H.parse(before_raw))
    report=H.parse(H.read(clone/'output/verification.json',digest=report_sha,limit=64*1024*1024));report_contract(report)
    H.read(outer/'launch.json',digest=outer_launch_sha,limit=1024*1024);H.read(outer/'completion.json',digest=outer_completion_sha,limit=1024*1024)
    H.read(here/'FULL183_GROUP_CONTRACT_20261121.json',*GROUP_PIN)
    H.read(here/'POSTFLIGHT_SOURCE_REFERENCE.py',*POSTFLIGHT_SOURCE_PIN)
    H.read(root/'output/verify_import_info_full183_root_20261121.py',*POSTFLIGHT_SOURCE_PIN)
    postflight_path=root/'output/IMPORT_INFO_FULL183_ROOT_POSTFLIGHT_20261121.json'
    postflight=H.parse(H.read(postflight_path,digest=postflight_sha,limit=1024*1024))
    need(type(postflight) is dict and postflight.get('status')=='PASS' and postflight.get('revision')==REVISION
         and postflight.get('functional_sources')==1109 and postflight.get('canonical_groups')==183
         and postflight.get('import_info_checks')==267 and postflight.get('editor_camera_checks')==626
         and postflight.get('headless_lifecycle_jobs')==5,'ACTUAL_ROOT_POSTFLIGHT_183_PASS_REQUIRED')
    validator,_=Q.load_pinned('_full183_readonly_validation',here/'full183_validation.py',*VALIDATOR_PIN)
    calculated,reads=validator.validate(clone,folder,outer,REVISION,here)
    need(set(postflight)==set(calculated) and all(postflight[k]==v for k,v in calculated.items() if k!='recorded_ns'),
         'POSTFLIGHT_EXACT_COMPUTED_FULL_SCALARS')
    need(type(postflight.get('recorded_ns')) is int and (outer/'completion.json').lstat().st_mtime_ns<=postflight['recorded_ns'],
         'POSTFLIGHT_FOLLOWS_RETAINED_OUTER_COMPLETION')
    inner=H.parse(H.read(folder/'launch.json',limit=1024*1024));outside=H.parse(H.read(outer/'launch.json',limit=1024*1024))
    need(inner.get('coordinator_pid')==outside.get('pid')==9228 and inner.get('pid')==13748,'EXACT_RETAINED_FULL_COORDINATOR_AND_VERIFIER_PIDS')
    for path,pin in reads.items():H.read(Path(path),pin['bytes'],pin['sha256'],limit=128*1024*1024)
    for name,row in baseline.items():
        path=root/H.rel(name);H.read(path,row['bytes'],row['sha256']);need(path.lstat().st_mtime_ns==int(row['main_mtime_ns']),'MAIN_STAMP_CHANGED')
    need(domain(H,root)==set(baseline),'CURRENT1109_DOMAIN_AFTER_ADMISSION')
    return baseline

def immutable_runtime(H,Q,root,baseline):
    row=baseline['tools/build_owner_review_snapshot.py']
    builder,_=Q.load_pinned('_miku2f1acbd_runtime_builder',root/'tools/build_owner_review_snapshot.py',row['bytes'],row['sha256'])
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
    need(git_functional==set(baseline),'EXACT_CURRENT1109_GIT_FUNCTIONAL_DOMAIN')
    need(set(baseline)<=git_rows.keys(),'CURRENT1109_GIT_DOMAIN')
    need(all(git_rows[name]==row['git_sha1'] for name,row in baseline.items()),'CURRENT1109_GIT_BLOBS')
    selected,cached=builder._runtime_entries(root,entries,REVISION)
    frozen={name:cached[name] for name,_ in selected}
    need(all(not name.startswith(('experiments/','output/','.git/','.godot/')) and '__pycache__' not in Path(name).parts
             and not name.endswith(('.pyc','.pyo')) for name in frozen),'RUNTIME_RESOURCE_SCOPE')
    expected_runtime={name for name in baseline if not name.startswith('experiments/')}
    need(len(expected_runtime)==1103 and expected_runtime<=frozen.keys(),'ALL1103_FUNCTIONAL_RUNTIME_SOURCES')
    for name in expected_runtime:
        need(len(frozen[name])==baseline[name]['bytes'] and H.sha(frozen[name])==baseline[name]['sha256'],'CURRENT_RUNTIME_BLOB_BYTES')
    need(len(frozen)==1112,'EXACT1112_CURRENT_RUNTIME_WITH_CLOSURE')
    return frozen

GROUP_PIN=(6076,'d7bd9c53add4088d88a05d575a34752ed9ac15e802755f0ff8cb13142f5da0f4')
POSTFLIGHT_SOURCE_PIN=(12190,'b91c63c0096ba4ee3d7a4f158c37cf46ca57af5e343ee077152d3cd96c1f8957')
VALIDATOR_PIN=(13174,'f2484142436d1a9699a5686b67310cb8fd65f5bf1bd38a37352263cc7923b2cc')
