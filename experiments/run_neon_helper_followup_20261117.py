"""Root-only original helper208/266 checks with frozen committed source and closure."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / 'experiments/run_neon_scene_followup_20261117.py'
assert hashlib.sha256(SUPPORT.read_bytes()).hexdigest() == '07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
spec = importlib.util.spec_from_file_location('root_strong_scope_helpers', SUPPORT)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
REVIEW = host.REVIEW
base_closed = host.closed

def helper_closed(folder, label):
    value = base_closed(folder, label)
    # Add the actual Python worker/controller/desktop entry points to the
    # inherited native/verification-coordinator observation; never terminate.
    code = r'''$ErrorActionPreference='Stop'
$pattern='tools[\\/](wind_preview_(worker|controller)|private_desktop)\.py|experiments[\\/]run_neon_helper_followup_20261117\.py'
foreach($name in @('C:\task\tools\wind_preview_worker.py','C:/task/tools/wind_preview_controller.py','C:\task\tools\private_desktop.py','C:/task/experiments/run_neon_helper_followup_20261117.py')) {if($name -notmatch $pattern){throw 'Helper matcher failed positive'}}
foreach($name in @('C:\task\tools\notwind_preview_worker.py','C:/task/tools/wind_preview_workerXpy')) {if($name -match $pattern){throw 'Helper matcher failed negative'}}
$items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne DRIVER_PID -and $_.Name -match '^pythonw?\.exe$' -and ($_.CommandLine -like '*has-neon-review-20261116-c2d52ff*' -or $_.CommandLine -like '*has-acceptance-session-20261111*') -and $_.CommandLine -match $pattern})
@{format='has_root_neon_helper_worker_scope_1';matcher_positive_cases=4;matcher_negative_cases=2;owned_matches=@($items|Select-Object ProcessId,Name,CreationDate,CommandLine);owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o');termination_issued=$false}|ConvertTo-Json -Depth 6 -Compress
'''.replace('DRIVER_PID', str(os.getpid()))
    process = subprocess.Popen([str(host.PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    out, err = process.communicate(timeout=40)
    (folder / (label + '-worker-scope-stdout.log')).write_bytes(out)
    (folder / (label + '-worker-scope-stderr.log')).write_bytes(err)
    assert process.poll() is not None and process.returncode == 0 and not err.strip()
    workers = json.loads(out)
    host.save(folder / (label + '-worker-closure.json'), workers)
    assert workers['owned_count'] == 0 and workers['termination_issued'] is False
    return dict(value, helper_worker_owned_count=workers['owned_count'])

host.closed = helper_closed

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    assert host.re.fullmatch('[a-z0-9-]{3,70}', args.label)
    assert host.re.fullmatch('[0-9a-f]{40}', args.revision)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == args.revision
    for path, pin in ((host.PYTHON, '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'),
                      (host.PWSH, '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'),
                      (host.ENGINE, '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'),
                      (REVIEW / 'src/app.gd', '88871ebd831d5a466b31336282a9bb53f264653dd5ff299fb10dc90a3080dd67')):
        assert host.sha(path) == pin, str(path)
    folder = REVIEW / 'output' / args.label
    folder.mkdir(exist_ok=False)
    before = host.sources()
    assert len(before) == 1029
    host.save(folder / 'source-before.json', before)
    host.closed(folder, 'before')
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE='1', HYBRID_GODOT=str(host.ENGINE), HYBRID_PYTHON=str(host.PYTHON))
    rows = []
    try:
        for mode, expected_cases, total in [('cpu', [('transport', 11), ('adapter', 128), ('host', 69)], 208),
                                             ('graphical', [('focused', 221), ('peers', 45)], 266)]:
            command = [str(host.PYTHON), '-B', '-u', str(REVIEW / 'tests/verify_helper_preview.py'), '--mode', mode, '--allow-checkout-eol']
            if mode == 'graphical':
                command.append('--lease-confirmed')
            host.save(folder / (mode + '-command.json'), command)
            start = time.time_ns()
            process = subprocess.Popen(command, cwd=REVIEW, env=environment, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            host.save(folder / (mode + '-start.json'), {'pid': process.pid, 'retained_Popen': True,
                'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            out, err = process.communicate(timeout=750)
            (folder / (mode + '-stdout.log')).write_bytes(out)
            (folder / (mode + '-stderr.log')).write_bytes(err)
            row = {'mode': mode, 'pid': process.pid, 'exit': process.returncode, 'retained_Popen_reaped': process.poll() is not None,
                   'timed_out': False, 'seconds': (time.time_ns() - start) / 1e9}
            host.save(folder / (mode + '-process.json'), row)
            markers = [line[len('HELPER_PREVIEW_MAIN '):] for line in out.decode('utf-8', 'strict').splitlines() if line.startswith('HELPER_PREVIEW_MAIN ')]
            assert len(markers) == 1
            status = json.loads(markers[0])
            path = Path(status['verification']).resolve(strict=True)
            assert path.name == 'verification.json' and path.is_relative_to((REVIEW / 'output/helper-preview').resolve()) and path.stat().st_mtime_ns >= start
            raw = path.read_bytes()
            (folder / (mode + '-report.json')).write_bytes(raw)
            report = json.loads(raw)
            row.update(report_path=str(path), report=report, root_exact_suite_assertions_passed=False)
            host.closed(folder, mode + '-after')
            rows.append(row)
            print(json.dumps({'mode': mode, 'exit': process.returncode, 'checks': report['checks'], 'seconds': row['seconds']}), flush=True)
            if process.returncode:
                break
            assert status['passed'] is True and report['format'] == 'has_helper_preview_main_verification_1' and report['passed'] is True
            assert report['mode'] == mode and report['source_context'] == 'main_source_snapshot' and report['overlay_files'] == 0
            assert Path(report['main_root']).resolve() == REVIEW.resolve() and Path(report['actual_res_root']).resolve() == path.parent / 'Studio'
            assert report['source_state']['revision'] == args.revision
            assert report['native_requested'] is False and report['native_inputs_checked'] is False and report['native_fidelity'] is False
            assert [(case['label'], case['checks']) for case in report['results']] == expected_cases and report['checks'] == total and all(case['passed'] is True for case in report['results'])
            assert set(report['preservation']) == {'main_sources', 'runtimes', 'head', 'native_originals', 'staged_native_inputs', 'published_requests', 'snapshot_sources', 'snapshot_extras', 'fixtures'} and all(value is True for value in report['preservation'].values())
            assert report['gpu_used'] is (mode == 'graphical')
            if mode == 'graphical':
                assert all(case['clean_private_receipt'] is True for case in report['results'])
            row['root_exact_suite_assertions_passed'] = True
    finally:
        after = host.sources()
        host.save(folder / 'source-after.json', after)
        final = host.closed(folder, 'after')
        host.save(folder / 'verification.json', {'format': 'has_root_neon_helper_followup_1', 'revision': args.revision,
            'rows': rows, 'all_functional_source_unchanged': before == after, 'functional_source_files': len(before),
            'host_scopes_closed': final['owned_count'] == 0, 'passed': len(rows) == 2 and all(row['exit'] == 0 and row['report']['passed'] is True and row['root_exact_suite_assertions_passed'] is True for row in rows) and before == after,
            'full_suite_pass_claimed': False})
        assert before == after
    return 0 if len(rows) == 2 and all(row['exit'] == 0 and row['root_exact_suite_assertions_passed'] is True for row in rows) else 1

if __name__ == '__main__':
    raise SystemExit(main())
