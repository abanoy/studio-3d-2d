"""Independent exact435/1102 provenance admission, source only and UNRUN.
Never invoke the historical1084/1086 qualification mains or validators.
"""
from pathlib import Path
import hashlib
import os
import re
import stat
REVISION='435dc02426a7cdd313e43fe674c9008520845428'
BASELINE_PIN=(284402,'e2b3b407a36bb45d68218669990f3d741aa1f604727c51f641b115a0f0494900')
FULL_CLONE='has-ui-camera-full-20261121-435dc02'
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
    need(value.get('revision')==REVISION,'FULL_EXACT435_REVISION')
    need(all(value.get(key) is True for key in FLAGS),'FULL_STRONG_QUALIFICATION_FLAGS')
    need(type(value.get('exit')) is int and value['exit']==0,'FULL_ZERO_EXIT')
    need(type(value.get('functional_source_count')) is int and value['functional_source_count']==1102,'FULL_EXACT1102')
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
    need(type(baseline) is dict and type(catalogue) is dict and len(baseline)==len(catalogue)==1102
         and set(baseline)==set(catalogue),'FULL_MAIN_EXACT_SOURCE_DOMAIN')
    need(len({name.casefold() for name in baseline})==1102,'SOURCE_CASE_ALIAS')
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
    need(len(names)==1102 and len({name.casefold() for name in names})==1102,'MAIN_EXACT1102_DOMAIN')
    return names

def admit_main(H,root,here):
    document=H.parse(H.read(here/'BASELINE_SOURCE1102.json',*BASELINE_PIN))
    need(document.get('format')=='has_exact_main1102_source_baseline_1'
         and document.get('revision')==REVISION and document.get('source_count')==1102,'MAIN_BASELINE_FORMAT')
    baseline=document['files']
    need(type(baseline) is dict and len(baseline)==1102 and domain(H,root)==set(baseline),'CURRENT1102_MAIN_DOMAIN')
    for name,row in baseline.items():
        path=root/H.rel(name);data=H.read(path,row['bytes'],row['sha256'])
        need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1'],'MAIN_BASELINE_GIT_BYTES')
        need(path.lstat().st_mtime_ns==int(row['main_mtime_ns']),'PREPARED_MAIN_SOURCE_STAMP_CHANGED')
    return baseline

def admit_full(H,root,here,folder,completion_sha,source_sha,report_sha):
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
    baseline_document=H.parse(H.read(here/'BASELINE_SOURCE1102.json',*BASELINE_PIN))
    need(baseline_document.get('format')=='has_exact_main1102_source_baseline_1'
         and baseline_document.get('revision')==REVISION and baseline_document.get('source_count')==1102,'MAIN_BASELINE_FORMAT')
    baseline=baseline_document['files'];source_contract(baseline,catalogue)
    report=H.parse(H.read(clone/'output/verification.json',digest=report_sha,limit=64*1024*1024))
    report_contract(report)
    launch=H.parse(H.read(folder/'launch.json',limit=1024*1024))
    need(launch.get('revision')==REVISION and type(launch.get('started_ns')) is int
         and launch['started_ns'] <= (clone/'output/verification.json').lstat().st_mtime_ns <= (folder/'completion.json').lstat().st_mtime_ns,'FRESH_FULL_REPORT_WINDOW')
    need(domain(H,root)==set(baseline),'CURRENT1102_FULL_DOMAIN')
    for name,row in baseline.items():
        path=root/H.rel(name);H.read(path,row['bytes'],row['sha256'])
        need(path.lstat().st_mtime_ns==int(row['main_mtime_ns']),'PREPARED_MAIN_SOURCE_STAMP_CHANGED')
    # Full checkout timestamps intentionally differ from Main. Each is preserved
    # independently; only bytes/Git blob IDs bind the two source catalogues.
    return baseline

def immutable_runtime(H,Q,root,baseline):
    row=baseline['tools/build_owner_review_snapshot.py']
    builder,_=Q.load_pinned('_miku435_runtime_builder',root/'tools/build_owner_review_snapshot.py',row['bytes'],row['sha256'])
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
    need(git_functional==set(baseline),'EXACT_CURRENT1102_GIT_FUNCTIONAL_DOMAIN')
    need(set(baseline)<=git_rows.keys(),'CURRENT1102_GIT_DOMAIN')
    need(all(git_rows[name]==row['git_sha1'] for name,row in baseline.items()),'CURRENT1102_GIT_BLOBS')
    selected,cached=builder._runtime_entries(root,entries,REVISION)
    frozen={name:cached[name] for name,_ in selected}
    need(all(not name.startswith(('experiments/','output/','.git/','.godot/')) and '__pycache__' not in Path(name).parts
             and not name.endswith(('.pyc','.pyo')) for name in frozen),'RUNTIME_RESOURCE_SCOPE')
    expected_runtime={name for name in baseline if not name.startswith('experiments/')}
    need(len(expected_runtime)==1096 and expected_runtime<=frozen.keys(),'ALL1096_FUNCTIONAL_RUNTIME_SOURCES')
    for name in expected_runtime:
        need(len(frozen[name])==baseline[name]['bytes'] and H.sha(frozen[name])==baseline[name]['sha256'],'CURRENT_RUNTIME_BLOB_BYTES')
    return frozen


def minimal_runtime(H,root,here,baseline,targets):
    """Five synthetic script entrypoints only; no editor/import or asset files."""
    rows={row['path']:row for row in targets}
    need(len(rows)==11 and len({name.casefold() for name in rows})==11,'ELEVEN_SYNTHETIC_TARGETS')
    need(all(name.endswith('.gd') and name not in baseline for name in rows),'ONLY_NEW_GDSCRIPT_TARGETS')
    closure=H.parse(H.read(here/'GDS_CLOSURE.json',11540,'9f12ec66090482c412f75a5e89a1ae5b06e272e88864121fd7d9a5a5e8d0f41b'))
    need(closure.get('format')=='has_miku171_literal_gd_closure_1' and closure.get('gd_file_count')==59
         and closure.get('production_gd_files')==48 and closure.get('experiment_gd_files')==11,'EXACT_MINIMAL_GD_CLOSURE')
    expected={row['path']:row for row in closure['files']}
    need(len(expected)==59,'UNIQUE_MINIMAL_GD_PATHS')
    literal=re.compile(rb'\b(?:preload|load)\s*\(\s*[\"\']res://([^\"\'\r\n\x00]+)[\"\']\s*\)')
    frozen={};pending=list(rows)
    while pending:
        name=H.rel(pending.pop())
        if name in frozen:continue
        row=rows.get(name,baseline.get(name));need(row is not None,'SEALED_GD_DEPENDENCY_REQUIRED')
        raw=H.read((here/'payload' if name in rows else root)/name,row['bytes'],row['sha256'])
        need(name in expected and len(raw)==expected[name]['bytes'] and H.sha(raw)==expected[name]['sha256'],'MINIMAL_CLOSURE_BYTES')
        frozen[name]=raw
        for match in literal.finditer(raw):
            reference=match.group(1).decode('utf-8')
            need(reference.endswith('.gd'),'NO_STATIC_ASSET_LOAD_IN_SYNTHETIC_CLOSURE')
            need(reference in rows or reference in baseline,'UNSEALED_STATIC_GD_DEPENDENCY')
            pending.append(reference)
    need(set(frozen)==set(expected) and len(frozen)==59,'EXACT59_GD_CLOSURE')
    launcher='tools/private_desktop.py';row=baseline[launcher]
    frozen[launcher]=H.read(root/launcher,row['bytes'],row['sha256'])
    frozen['project.godot']=b'config_version=5\n\n[application]\nconfig/name="HAS Synthetic Pure171"\n'
    need(len(frozen)==61,'MINIMAL61_SOURCE_PROJECT')
    return frozen
