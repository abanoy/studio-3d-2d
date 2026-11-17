"""Root-only sequential hidden workspace verification with explicit fresh closure."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PYTHON = Path(r'C:\Program Files\Python313\python.exe')
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
CASES = (
    ('controls', 'verify_workspace_controls.py', [], 'workspace-controls-verification.json', 330),
    ('neon', 'verify_neon_workspace.py', ['--lease-confirmed', '--parse-scripts'], 'neon-workspace-verification.json', 990),
    ('resize', 'verify_workspace_resize.py', [], 'workspace-resize-verification.json', 330),
    ('docking', 'verify_workspace_docking.py', [], 'workspace-docking-verification.json', 370),
    ('nested', 'verify_workspace_nested.py', [], 'workspace-nested-verification.json', 370),
)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')

def sources():
    paths = [p for d in ('src', 'tests', 'tools', 'data', 'examples') for p in (REVIEW / d).rglob('*')
             if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
    paths += [REVIEW / n for n in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
    return {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(paths)}

def closed(folder, label):
    # Raw string keeps one backslash in the PowerShell regex. Test the actual
    # host matcher before querying; the earlier helper uses the same native pattern.
    code = r'''$ErrorActionPreference='Stop'
$pattern='^(Godot.*|blender|ffmpeg|ffprobe)\.exe$'
foreach($name in @('Godot_v4.6-stable_win64.exe','blender.exe','ffmpeg.exe','ffprobe.exe')) {if($name -notmatch $pattern){throw 'Native matcher failed positive case'}}
foreach($name in @('notblender.exe','blenderXexe','ffmpeg.exe.bak')) {if($name -match $pattern){throw 'Native matcher failed negative case'}}
$items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.ProcessId -ne DRIVER_PID -and ($_.CommandLine -like '*has-neon-review-20261116-c2d52ff*' -or $_.CommandLine -like '*has-acceptance-session-20261111*') -and ($_.Name -match $pattern -or ($_.Name -match '^pythonw?\.exe$' -and $_.CommandLine -match 'tests[\\/]verify|windows_private_desktop|run_canonical_owned|run_owned\.py') -or ($_.Name -match '^(pwsh|powershell)\.exe$' -and $_.CommandLine -match 'run_canonical_owned|private_desktop'))})
@{format='has_root_workspace_scope_observation_1';matcher_positive_cases=4;matcher_negative_cases=3;owned_matches=@($items|Select-Object ProcessId,Name,CreationDate,CommandLine);owned_count=$items.Count;observed_utc=[DateTime]::UtcNow.ToString('o');termination_issued=$false}|ConvertTo-Json -Depth 6 -Compress
'''.replace('DRIVER_PID', str(os.getpid()))
    p = subprocess.Popen([str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code],
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    out, err = p.communicate(timeout=40)
    (folder / (label + '-scope-stdout.log')).write_bytes(out)
    (folder / (label + '-scope-stderr.log')).write_bytes(err)
    assert p.poll() is not None and p.returncode == 0 and not err.strip(), err.decode('utf-8', 'replace')
    value = json.loads(out)
    save(folder / (label + '-closure.json'), value)
    assert value['owned_count'] == 0 and value['termination_issued'] is False, value
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--workspace-sha256', required=True)
    parser.add_argument('--world-sha256', required=True)
    parser.add_argument('--only', choices=[row[0] for row in CASES])
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]{3,70}', args.label)
    for path, pin in ((PYTHON, '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'),
                      (PWSH, '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'),
                      (ENGINE, '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'),
                      (REVIEW / 'src/workspace_layout.gd', args.workspace_sha256),
                      (REVIEW / 'src/world_selection.gd', args.world_sha256)):
        assert sha(path) == pin, str(path)
    folder = REVIEW / 'output' / args.label
    folder.mkdir(exist_ok=False)
    before = sources()
    save(folder / 'source-before.json', before)
    closed(folder, 'before')
    rows = []
    environment = os.environ.copy()
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['HYBRID_GODOT'] = str(ENGINE)
    environment['HYBRID_PYTHON'] = str(PYTHON)
    try:
        for label, script, extra, report_name, timeout in CASES:
            if args.only and args.only != label:
                continue
            command = [str(PYTHON), '-B', '-u', str(REVIEW / 'tests' / script), *extra]
            save(folder / (label + '-command.json'), command)
            start = time.time_ns()
            p = subprocess.Popen(command, cwd=REVIEW, env=environment, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            save(folder / (label + '-start.json'), {'pid': p.pid, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                                     'retained_Popen': True})
            # Existing test/launcher watchdogs retain ownership. A timeout here
            # never declares closure or releases the lane.
            out, err = p.communicate(timeout=timeout)
            (folder / (label + '-stdout.log')).write_bytes(out)
            (folder / (label + '-stderr.log')).write_bytes(err)
            row = {'label': label, 'pid': p.pid, 'exit': p.returncode, 'retained_Popen_reaped': p.poll() is not None,
                   'seconds': (time.time_ns() - start) / 1e9, 'timed_out': False}
            save(folder / (label + '-process.json'), row)
            if p.returncode == 0:
                report_path = REVIEW / 'output' / report_name
                assert report_path.stat().st_mtime_ns >= start
                (folder / (label + '-report.json')).write_bytes(report_path.read_bytes())
                row['report'] = json.loads(report_path.read_bytes())
            closed(folder, label + '-after')
            rows.append(row)
            print(json.dumps({'label': label, 'exit': p.returncode, 'seconds': row['seconds']}), flush=True)
            if p.returncode:
                break
    finally:
        after = sources()
        save(folder / 'source-after.json', after)
        final = closed(folder, 'after')
        save(folder / 'verification.json', {'format': 'has_root_workspace_followup_1', 'rows': rows,
             'all_functional_source_unchanged': before == after, 'functional_source_files': len(before),
             'host_scopes_closed': final['owned_count'] == 0,
             'passed': bool(rows) and all(row['exit'] == 0 for row in rows) and before == after,
             'full_suite_pass_claimed': False})
        assert before == after
    return 0 if rows and all(row['exit'] == 0 for row in rows) else 1

if __name__ == '__main__':
    raise SystemExit(main())
