"""Root-owned, headless lifecycle check; supplied inputs are read-only."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA = '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
INPUT = ROOT / 'output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685'
EXPECTED = {'scene.glb': '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d',
            'parameters.json': 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'}
SCRIPT = 'tests/source_native_state_unit.gd'
SCRIPT_SHA = '008e694dfc3947e9ca3054e6dff14b64e22ee0d1dea3aaf8147df6c9ec0e74fc'
BAD = ['ERROR:', 'WARNING:', 'SCRIPT ERROR', 'ObjectDB instances leaked',
       'resources still in use', 'Pages in use exist at exit', 'FAIL source_native_state.']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def closed(folder, name):
    # Read-only process inventory. The separately launched owner review is not
    # under this checkout and is never closed, hidden, or otherwise controlled.
    code = "$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'}); @{owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    child = subprocess.Popen([str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    out, err = child.communicate(timeout=30)
    (folder / (name + '-inventory-stdout.log')).write_bytes(out)
    (folder / (name + '-inventory-stderr.log')).write_bytes(err)
    save(folder / (name + '-inventory-process.json'), {'pid':child.pid,'exit':child.returncode,'retained_Popen_reaped':child.poll() is not None})
    assert child.returncode == 0 and not err.strip(), 'Read-only process inventory failed'
    value = json.loads(out)
    save(folder / (name + '-runtime-closure.json'), value)
    assert value['owned_count'] == 0, 'An owned runtime is still active'
    return value


def main():
    assert sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA
    assert sha(ROOT / SCRIPT) == SCRIPT_SHA
    assert all(sha(INPUT / name) == expected for name, expected in EXPECTED.items())
    tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    folder = ROOT / 'output' / ('source-native-state-' + tag)
    folder.mkdir()
    closed(folder, 'before')
    project = folder / 'Studio'
    project.mkdir()
    paths = sorted(p for p in (ROOT / 'src').rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts)
    paths += sorted((ROOT / 'data').glob('*.json')) + [ROOT / 'project.godot', ROOT / SCRIPT]
    pins = []
    for source in paths:
        relative = source.relative_to(ROOT)
        assert not source.is_symlink()
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        pins.append({'path': relative.as_posix(), 'bytes': source.stat().st_size, 'sha256': sha(source)})
    save(folder / 'SOURCE.json', {'source_HEAD': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'files': pins})
    inputs = folder / 'read-only-inputs'
    inputs.mkdir()
    for name, expected in EXPECTED.items():
        (inputs / name).write_bytes((INPUT / name).read_bytes())
        assert sha(inputs / name) == expected
    job = {'format': 'has_source_native_state_job_1', 'phase': 'ROOT_APPROVED_HEADLESS_STATE_TEST',
           'folder': str(folder), 'glb': str(inputs / 'scene.glb'), 'report': str(inputs / 'parameters.json'),
           'engine_sha256': ENGINE_SHA, 'expected_script_sha256': SCRIPT_SHA,
           'source_manifest_sha256': sha(folder / 'SOURCE.json'), 'root_closed_all': True,
           'expires_unix': time.time() + 600}
    save(folder / 'job.json', job)
    phases = []
    for phase, options in [('parse', ['--check-only']), ('state', [])]:
        log = folder / (phase + '-engine.log')
        command = [str(ENGINE), '--headless', '--path', str(project), '--audio-driver', 'Dummy', '--log-file', str(log), '--script', 'res://' + SCRIPT, *options, '--', str(folder / 'job.json')]
        save(folder / (phase + '-command.json'), command)
        started = time.monotonic()
        child = subprocess.Popen(command, cwd=project, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out = False
        forced_kill = False
        try:
            out, err = child.communicate(timeout=30 if phase == 'parse' else 200)
        except subprocess.TimeoutExpired:
            timed_out = True
            child.terminate()
            try:
                out, err = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                forced_kill = True
                child.kill()
                out, err = child.communicate(timeout=5)
        (folder / (phase + '-stdout.log')).write_bytes(out)
        (folder / (phase + '-stderr.log')).write_bytes(err)
        combined = out.decode('utf-8', errors='replace') + err.decode('utf-8', errors='replace') + (log.read_text(encoding='utf-8', errors='replace') if log.exists() else '')
        markers = [line for line in combined.splitlines() if any(value in line for value in BAD)]
        passed = child.returncode == 0 and not timed_out and not markers
        row = {'phase': phase, 'pid': child.pid, 'exit': child.returncode, 'retained_Popen_reaped': child.poll() is not None, 'timed_out': timed_out, 'owned_child_terminated': timed_out, 'owned_child_forced_kill': forced_kill, 'seconds': time.monotonic()-started, 'error_markers': markers, 'passed': passed}
        save(folder / (phase + '-process.json'), row)
        phases.append(row)
        if not passed:
            break
    result_path = folder / 'result.json'
    actual = json.loads(result_path.read_text(encoding='utf-8')) if result_path.exists() else None
    result_valid = (isinstance(actual, dict) and actual.get('checks') == 180 and actual.get('failures') == 0
                    and actual.get('complete_assertion_set') is True
                    and actual.get('job_sha256') == sha(folder / 'job.json')
                    and actual.get('test_script_sha256') == SCRIPT_SHA
                    and actual.get('source_manifest_sha256') == sha(folder / 'SOURCE.json')
                    and actual.get('metrics', {}).get('actors_loaded') == 3
                    and actual.get('cleanup', {}).get('owned_copy_hashes_restored') is True
                    and actual.get('cleanup', {}).get('passed_input_hashes_preserved') is True
                    and len(actual.get('named_checks', {})) == 180 and all(actual.get('named_checks', {}).values()))
    source_preserved = all(sha(ROOT / p['path']) == sha(project / p['path']) == p['sha256'] for p in pins)
    inputs_preserved = all(sha(INPUT / name) == sha(inputs / name) == expected for name, expected in EXPECTED.items())
    runtimes_preserved = sha(ENGINE) == ENGINE_SHA and sha(PWSH) == PWSH_SHA
    after = closed(folder, 'after')
    result = {'format': 'has_source_native_state_verification_1', 'passed': len(phases)==2 and all(p['passed'] for p in phases) and bool(result_valid) and source_preserved and inputs_preserved and runtimes_preserved,
              'phases': phases, 'actual_result_valid': bool(result_valid), 'checks_observed': actual.get('checks',0) if actual else 0,
              'failures_observed': actual.get('failures') if actual else None,
              'preservation': {'source':source_preserved,'read_only_inputs':inputs_preserved,'runtimes':runtimes_preserved},
              'runtime_lease_released':after['owned_count']==0,
              'test_result_sha256':sha(result_path) if result_path.exists() else None,
              'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder / 'verification.json', result)
    print(json.dumps({'folder':str(folder),**result}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
