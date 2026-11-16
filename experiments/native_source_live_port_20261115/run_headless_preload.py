"""Root-owned source preload check in a disposable headless snapshot."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    assert sha(ENGINE) == ENGINE_SHA
    tag = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    folder = ROOT / 'output' / ('native-source-live-preload-' + tag)
    folder.mkdir()
    project = folder / 'Studio'
    project.mkdir()
    paths = sorted(p for p in (ROOT / 'src').rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts)
    paths += sorted((ROOT / 'data').glob('*.json')) + [ROOT / 'project.godot']
    pins = []
    for source in paths:
        relative = source.relative_to(ROOT)
        assert not source.is_symlink()
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        pins.append({'path': relative.as_posix(), 'bytes': source.stat().st_size, 'sha256': sha(source)})
    harness = project / 'preload_check.gd'
    harness.write_text('extends SceneTree\nconst Native=preload("res://src/source_secondary.gd")\nconst Live=preload("res://src/secondary_live.gd")\nconst Editor=preload("res://src/physics_editor.gd")\nconst Fan=preload("res://src/fan_editor.gd")\nfunc _initialize():\n\tprint("NATIVE_SOURCE_PRELOAD_OK")\n\tquit(0)\n', encoding='utf-8')
    save(folder / 'SOURCE.json', {'source_HEAD': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'files': pins, 'harness_sha256': sha(harness)})
    phases = []
    for phase, options in [('parse', ['--check-only']), ('preload', [])]:
        log = folder / (phase + '-engine.log')
        command = [str(ENGINE), '--headless', '--path', str(project), '--audio-driver', 'Dummy', '--log-file', str(log), '--script', 'res://preload_check.gd', *options]
        save(folder / (phase + '-command.json'), command)
        started = time.monotonic()
        child = subprocess.Popen(command, cwd=project, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out = False
        try:
            out, err = child.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            timed_out = True
            child.terminate()
            try:
                out, err = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                out, err = child.communicate(timeout=5)
        (folder / (phase + '-stdout.log')).write_bytes(out)
        (folder / (phase + '-stderr.log')).write_bytes(err)
        text = out.decode('utf-8', errors='replace') + err.decode('utf-8', errors='replace') + (log.read_text(encoding='utf-8', errors='replace') if log.exists() else '')
        markers = [line for line in text.splitlines() if any(value in line for value in ['ERROR:', 'WARNING:', 'SCRIPT ERROR', 'ObjectDB instances leaked', 'resources still in use', 'Pages in use exist at exit'])]
        passed = child.returncode == 0 and not timed_out and not markers and (phase == 'parse' or 'NATIVE_SOURCE_PRELOAD_OK' in text)
        row = {'phase': phase, 'pid': child.pid, 'exit': child.returncode, 'retained_Popen_reaped': child.poll() is not None, 'timed_out': timed_out, 'owned_child_terminated': timed_out, 'seconds': time.monotonic() - started, 'error_markers': markers, 'passed': passed}
        save(folder / (phase + '-process.json'), row)
        phases.append(row)
        if not passed:
            break
    preserved = all(sha(ROOT / p['path']) == sha(project / p['path']) == p['sha256'] for p in pins)
    result = {'format': 'has_native_source_live_preload_1', 'passed': len(phases) == 2 and all(p['passed'] for p in phases) and preserved, 'phases': phases, 'source_preserved': preserved, 'actual_native_load_or_simulation': False, 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder / 'verification.json', result)
    print(json.dumps({'folder': str(folder), **result}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
