"""Retain the full Windows verifier and audit exact source and private jobs."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from receipt_provenance import classify
TREES = ('src','tools','tests','data','examples')
FILES = ('project.godot','main.tscn','run.py','launch.pyw','dependencies.json',
         'experiments/reference_body_20261120/run_full.py',
         'experiments/reference_body_20261120/stage_legacy_inputs.py',
         'experiments/reference_body_20261120/verify_units.py',
         'experiments/reference_body_20261120/run_scoped.py',
         'experiments/reference_body_20261120/receipt_provenance.py',
         'experiments/reference_body_20261120/test_receipt_provenance.py')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    files = [path for tree in TREES
             for path in (ROOT/tree).rglob('*') if path.is_file()
             and path.suffix != '.pyc' and '__pycache__' not in path.parts]
    files += [ROOT/name for name in FILES]
    result = {}
    for path in sorted(files):
        data = path.read_bytes()
        result[path.relative_to(ROOT).as_posix()] = dict(sha256=hashlib.sha256(data).hexdigest(),
                git_sha1=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
                bytes=len(data),mtime_ns=path.stat().st_mtime_ns)
    return result


def committed_sources(revision):
    raw = subprocess.check_output(['git','ls-tree','-r','-z',revision,'--',*TREES,*FILES],cwd=ROOT)
    result = {}
    for row in raw.split(b'\0'):
        if not row:continue
        meta, name = row.split(b'\t',1)
        mode,kind,oid = meta.split()
        path = name.decode('utf-8')
        if Path(path).suffix == '.pyc' or '__pycache__' in Path(path).parts:continue
        assert kind == b'blob' and mode in (b'100644',b'100755'), path
        result[path] = oid.decode('ascii')
    return result


def receipts():
    rows = []
    # Frozen runtime copies include old committed experiment receipts. Inventory
    # their originals before launch, not just the current output directory.
    paths=[path for part in ('output','experiments') for path in (ROOT/part).rglob('*.json')]
    for path in paths:
        if path.stat().st_size > 1024*1024:continue
        try:
            data = path.read_bytes()
            value = json.loads(data)
        except (OSError, ValueError):continue
        if not isinstance(value,dict) or value.get('format') != 'studio_private_desktop_1':continue
        rows.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(), value=value))
    return rows


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def _info_read(path,root,limit=4*1024*1024):
    import stat
    path=Path(path)
    if not path.is_absolute() or not path.is_relative_to(root):raise ValueError('INFO_PATH_OUTSIDE_ROOT')
    for ancestor in (path,*path.parents):
        value=ancestor.lstat()
        if stat.S_ISLNK(value.st_mode) or getattr(value,'st_file_attributes',0)&0x400:raise ValueError('INFO_ALIAS')
        if ancestor==root:break
    before=path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size>limit:raise ValueError('INFO_BOUNDED_REGULAR_FILE')
    raw=path.read_bytes();after=path.stat()
    def stamp(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,s.st_mode,getattr(s,'st_file_attributes',0))
    if stamp(before)!=stamp(after):raise ValueError('INFO_READ_DRIFT')
    return raw,before.st_mtime_ns

def import_info_headless_receipts(root,report,current,started_ns,finished_ns,before,expected_checks=267):
    # Only this exact shipping component's five current CPU cases can omit HWNDs.
    info=report.get('import_capability')
    if info is None:return []
    def require(value,code):
        if not value:raise ValueError(code)
    require(expected_checks in (163,267),'INFO_ADMITTED_SCOPE_PARAMETER')
    require(type(info) is dict and info.get('format')=='has_current_import_capability_verification_1' and info.get('status')=='PASS','INFO_REPORT_FORMAT')
    require(type(info.get('checks')) is int and info['checks']==expected_checks and info.get('scope')==('all' if expected_checks==267 else 'cpu'),'INFO_SCOPE')
    require(all(info.get(k) is True for k in ('all_admitted_sources_unchanged','all_runtime_sources_unchanged','all_private_jobs_and_desktops_closed','all_writer_trees_restored','parent_environment_preserved')),'INFO_CLOSURE_FLAGS')
    require(all(info.get(k) is False for k in ('whole_full_claimed','native_or_owner_assets_read','sourceio_or_conversion_requested','experimental_coordinator_used','prior_Full_required')),'INFO_SCOPE_FLAGS')
    path=Path(info.get('report_path',''));component=path.parent
    require(path.name=='verification.json' and component.parent==root/'output/import-capability-canonical' and component.name.isdecimal(),'INFO_CANONICAL_REPORT_PATH')
    raw,mtime=_info_read(path,root);report_sha256=hashlib.sha256(raw).hexdigest()
    require(started_ns<=mtime<=finished_ns and json.loads(raw)==info,'INFO_FRESH_EXACT_COMPONENT_REPORT')
    cases=info.get('cases');require(type(cases) is list and len(cases)==(21 if expected_checks==267 else 5),'INFO_CASE_COUNT')
    require(len({row.get('name') for row in cases if type(row) is dict})==len(cases),'INFO_CASE_IDENTITIES')
    wanted={'legacy43':('tests/import_capability_summary_unit.gd',43,[])}
    for theme in ('classic','neon'):
        for mode in ('simple','advanced'):wanted['app-'+theme+'-'+mode]=('tests/import_capability_app_headless.gd',30,(['--classic'] if theme=='classic' else [])+(['--advanced'] if mode=='advanced' else []))
    cpus=[row for row in cases if row.get('headless') is True]
    require({row.get('name') for row in cpus}==set(wanted) and len(cpus)==5,'INFO_EXACT_FIVE_CPU_CASES')
    cpu=component/'CPUStudio'
    for name,source in before.items():
        if name.startswith('experiments/'):continue
        data,_=_info_read(cpu/name,root,128*1024*1024)
        require(len(data)==source['bytes'] and hashlib.sha256(data).hexdigest()==source['sha256'],'INFO_COPIED_CURRENT_SOURCE')
    admitted=[];desktops=set()
    for row in cpus:
        name=row['name'];script,count,flags=wanted[name];case=component/'Cases'/name;rp=case/'private-receipt.json'
        require(row.get('status')=='PASS' and type(row.get('checks')) is int and row['checks']==count and type(row.get('expected_checks')) is int and row['expected_checks']==count,'INFO_CASE_RESULT')
        require(all(row.get(k) is True for k in ('launcher_reaped','launcher_handle_closed','private_resources_closed')) and row.get('private_receipt_mode')=='headless_lifecycle_only' and row.get('graphical_placement_proven') is False,'INFO_CASE_LIFECYCLE')
        require(type(row.get('launcher_exit')) is int and row['launcher_exit']==0 and type(row.get('launcher_pid')) is int and row['launcher_pid']>0,'INFO_LAUNCHER')
        require(Path(row.get('private_receipt',''))==rp and Path(row.get('data',''))==case/'Data' and Path(row.get('user',''))==case/'User','INFO_CASE_PATH')
        command=row.get('engine_command');require(type(command) is list and command and all(type(x) is str for x in command),'INFO_ENGINE_COMMAND')
        require(command.count('--')==1,'INFO_ARGUMENT_BOUNDARY');cut=command.index('--');engine=command[:cut];user=command[cut+1:]
        require(engine.count('--headless')==1 and engine.count('--path')==1 and engine.count('--script')==1,'INFO_HEADLESS_COMMAND')
        require(engine[engine.index('--path')+1]==str(cpu) and engine[engine.index('--script')+1]==script and user==[str(case/'Data'),*flags],'INFO_EXACT_CASE_COMMAND')
        profile=Path(row.get('report',{}).get('user_profile',''))
        require(profile.is_relative_to(case/'User/Roaming') and type(row.get('report',{}).get('checks')) is int and row['report']['checks']==count and type(row.get('report',{}).get('failures')) is int and row['report']['failures']==0,'INFO_ACTUAL_USER_PROFILE')
        proof_raw,proof_mtime=_info_read(rp,root);proof=json.loads(proof_raw);digest=hashlib.sha256(proof_raw).hexdigest();relative=rp.relative_to(root).as_posix()
        require(started_ns<=proof_mtime<=mtime and digest==row.get('private_receipt_sha256'),'INFO_RECEIPT_BYTES_AND_FRESHNESS')
        witness=[r for r in current if r.get('path')==relative]
        require(len(witness)==1 and witness[0].get('sha256')==digest and witness[0].get('value')==proof,'INFO_CURRENT_PHYSICAL_RECEIPT')
        require(proof.get('format')=='studio_private_desktop_1' and type(proof.get('exit')) is int and proof['exit']==0 and type(proof.get('child_pid')) is int and proof['child_pid']>0 and type(row.get('private_child_pid')) is int and proof['child_pid']==row['private_child_pid'],'INFO_CHILD_IDENTITY')
        require(all(proof.get(k) is True for k in ('job_closed','desktop_closed')) and all(proof.get(k) is False for k in ('foreground_child_observed','desktop_switch_requested','private_window_seen')),'INFO_PHYSICAL_CLOSURE')
        require(type(proof.get('child_desktop_confirmed')) is bool and type(proof.get('maximum_owned_windows')) is int and proof['maximum_owned_windows']==0,'INFO_NO_GRAPHICAL_CLAIM')
        require(type(proof.get('job_memory_limit_bytes')) is int and proof['job_memory_limit_bytes']==4096*1024*1024 and not any(k in proof for k in ('error','monitor_error','desktop_enumeration_error','cancelled')),'INFO_JOB_ERROR_OR_LIMIT')
        desktop=proof.get('desktop');require(type(desktop) is str and len(desktop)==41 and desktop.startswith('HAS_Test_') and all(x in '0123456789abcdef' for x in desktop[9:]) and desktop not in desktops,'INFO_UNIQUE_DESKTOP')
        desktops.add(desktop);admitted.append({'path':relative,'sha256':digest,'desktop':desktop,'component_report_sha256':report_sha256,'headless_lifecycle_only':True})
    return admitted

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--fixture-root', type=Path, required=True)
    parser.add_argument('--sourceio', type=Path, required=True)
    options = parser.parse_args()
    revision = git('rev-parse','HEAD')
    assert revision == options.revision and not (ROOT/'override.cfg').exists()
    assert not git('diff','--name-only','HEAD','--',*TREES,*FILES)
    folder = ROOT/'output'/('windows-reference-body-'+str(time.time_ns()))
    folder.mkdir()
    def write(name,value):(folder/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    before = snapshot()
    expected = committed_sources(revision)
    assert {name:row['git_sha1'] for name,row in before.items()} == expected, 'Working file membership/raw bytes differ from requested commit'
    write('source-before.json',before)
    write('committed-source-blobs.json',expected)
    prior = receipts();write('prior-receipts.json',prior)
    initial = classify(prior,prior)
    assert not initial['conflicts'] and not initial['changed_original_archives']
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,
               HYBRID_GODOT=r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe',
               HYBRID_NATIVE_FIXTURES=str(options.fixture_root.resolve(strict=True)),
               HYBRID_HECATIA_KRA=r'C:\a\Programming\HAS\hecatia.kra',
               HYBRID_SOURCEIO=str(options.sourceio.resolve(strict=True)),
               HYBRID_NATIVE_INPUTS=r'C:\a\dump',
               HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
    env.pop('HYBRID_FAN_PROJECT',None)
    assert sha(Path(env['HYBRID_HECATIA_KRA'])) == 'fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758'
    start = time.time_ns()
    args = [sys.executable,'-B','-u','tests/verify.py']
    with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
        process = subprocess.Popen(args,cwd=ROOT,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        write('launch.json',dict(pid=process.pid,coordinator_pid=os.getpid(),started_ns=start,revision=revision,
              args=args,environment={key:value for key,value in env.items() if key.startswith('HYBRID_') or key=='PYTHONDONTWRITEBYTECODE'}))
        print(json.dumps(dict(folder=str(folder),child_pid=process.pid,revision=revision)),flush=True)
        process.wait()
    after = snapshot();write('source-after.json',after)
    all_rows = receipts();classification=classify(prior,all_rows)
    write('receipt-provenance.json',classification)
    current=classification['current']
    provenance_ok=not classification['conflicts'] and not classification['changed_original_archives']
    unique = {};duplicates = []
    physical = ('desktop','child_pid','exit','seconds','job_closed','desktop_closed','private_window_seen',
                'child_desktop_confirmed','foreground_child_observed','desktop_switch_requested','cancelled','error')
    for row in current:
        desktop = row['value']['desktop']
        if desktop in unique:
            previous = unique[desktop]
            assert all(previous['value'].get(key) == row['value'].get(key) for key in physical)
            duplicates.append(dict(desktop=desktop,paths=[previous['path'],row['path']]))
        else:unique[desktop] = row
    report_path = ROOT/'output/verification.json'
    fresh_report = report_path.is_file() and report_path.stat().st_mtime_ns >= start
    report = json.loads(report_path.read_bytes()) if fresh_report else {}
    info_admitted=[];info_admission_error=None
    try:info_admitted=import_info_headless_receipts(ROOT,report,current,start,time.time_ns(),before)
    except (OSError,ValueError,KeyError,TypeError,IndexError) as error:info_admission_error=str(error)
    info_paths={row['path'] for row in info_admitted}
    isolation = info_admission_error is None and all(row['path'] in info_paths or (row['value'].get('job_closed') is True and row['value'].get('desktop_closed') is True
            and row['value'].get('child_desktop_confirmed') is True
            and row['value'].get('foreground_child_observed') is False
            and row['value'].get('desktop_switch_requested') is False) for row in unique.values())
    nonzero = [row for row in unique.values() if row['value'].get('exit') != 0]
    expected_cancels = len(nonzero) == 1 and all(row['value'].get('exit') == 2 and row['value'].get('cancelled') is True
            and row['value'].get('error') == 'Owned converter cancelled' for row in nonzero)
    result = dict(format='has_reference_body_full_coordinator_1',revision=revision,exit=process.returncode,
            child_reaped=process.poll() is not None,seconds=(time.time_ns()-start)/1e9,
            functional_source_count=len(before),functional_sources_unchanged=before==after,
            revision_unchanged=git('rev-parse','HEAD')==revision,fresh_final_report=fresh_report,
            result_groups=len(report),movie_groups=[key for key in report if key.endswith('_video') or key.startswith('posed_model_video_')],
            unique_current_private_jobs=len(unique),new_receipt_paths=len(current),duplicates=duplicates,
            all_private_jobs_isolated_closed=isolation,import_info_headless_receipts=info_admitted,
            import_info_headless_admission_error=info_admission_error,nonzero_private_jobs=nonzero,
            nonzero_jobs_are_expected_cancellations=expected_cancels,current_jobs=list(unique.values()),
            byte_proven_archived_copy_paths=len(classification['archived_copies']),
            unchanged_prior_receipt_paths=len(classification['unchanged_prior_paths']),
            receipt_provenance_verified=provenance_ok,
            whole_verifier_pass=process.returncode==0 and before==after and fresh_report
                and git('rev-parse','HEAD')==revision and isolation and expected_cancels and provenance_ok)
    write('completion.json',result)
    print(json.dumps({key:value for key,value in result.items() if key not in ('current_jobs','nonzero_private_jobs')},indent=2),flush=True)
    return 0 if result['whole_verifier_pass'] else 1


if __name__ == '__main__':raise SystemExit(main())
