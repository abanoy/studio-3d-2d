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
    isolation = all(row['value'].get('job_closed') is True and row['value'].get('desktop_closed') is True
            and row['value'].get('child_desktop_confirmed') is True
            and row['value'].get('foreground_child_observed') is False
            and row['value'].get('desktop_switch_requested') is False for row in unique.values())
    nonzero = [row for row in unique.values() if row['value'].get('exit') != 0]
    expected_cancels = len(nonzero) == 1 and all(row['value'].get('exit') == 2 and row['value'].get('cancelled') is True
            and row['value'].get('error') == 'Owned converter cancelled' for row in nonzero)
    report_path = ROOT/'output/verification.json'
    fresh_report = report_path.is_file() and report_path.stat().st_mtime_ns >= start
    report = json.loads(report_path.read_bytes()) if fresh_report else {}
    result = dict(format='has_reference_body_full_coordinator_1',revision=revision,exit=process.returncode,
            child_reaped=process.poll() is not None,seconds=(time.time_ns()-start)/1e9,
            functional_source_count=len(before),functional_sources_unchanged=before==after,
            revision_unchanged=git('rev-parse','HEAD')==revision,fresh_final_report=fresh_report,
            result_groups=len(report),movie_groups=[key for key in report if key.endswith('_video') or key.startswith('posed_model_video_')],
            unique_current_private_jobs=len(unique),new_receipt_paths=len(current),duplicates=duplicates,
            all_private_jobs_isolated_closed=isolation,nonzero_private_jobs=nonzero,
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
