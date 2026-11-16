"""Stage and execute one standalone, headless mathematical candidate attempt."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
FULL = ROOT / 'output/windows-canonical-bone-binding-20261115T225514304'
FK = ROOT / 'output/native-jiggle-headless-transport-prep-20261115/runtime-post-full-f0dd57a'
BAD = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ',
       'ObjectDB instances leaked', 'unclaimed string names', 'resources still in use')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--expected-index', required=True)
    parser.add_argument('--attempt', type=int, choices=range(1, 6), required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    assert packet.is_relative_to(ROOT / 'experiments') and sha(packet / 'INDEX.json') == args.expected_index
    state = json.loads((FULL / 'state.json').read_bytes())
    fk = json.loads((FK / 'verification.json').read_bytes())
    closure = json.loads((FK / 'authoritative-closure.json').read_bytes())
    assert state['status'] == 'passed' and state['suite_exit'] == 0 and state['source_unchanged']
    assert fk['passed'] and fk['result']['checks'] == 41588 and fk['result']['failures'] == 0
    assert closure['runtime_lease_released'] and closure['owned_runtime_commands_absent']
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == state['source_commit'] == fk['HEAD'] == 'f0dd57a2e568089d396fecba819ab987da658bf0'
    assert sha(ENGINE) == ENGINE_SHA
    index = json.loads((packet / 'INDEX.json').read_bytes())
    for row in index['files']:
        assert '..' not in Path(row['path']).parts and not Path(row['path']).is_absolute()
        source = packet / row['path']
        assert source.is_file() and not source.is_symlink() and source.stat().st_size == row['bytes']
        assert sha(source) == row['sha256']
    folder = ROOT / ('output/source-0x31-godot-math-20261115-attempt' + str(args.attempt))
    assert not folder.exists()
    folder.mkdir()
    for name in ['candidate.gd', 'harness.gd', 'PUBLIC_SYNTHETIC_ORACLE.json']:
        with (folder / name).open('xb') as stream:
            stream.write((packet / name).read_bytes())
        assert sha(folder / name) == sha(packet / name)
    project = folder / 'project.godot'
    project.write_text('config_version=5\n[application]\nconfig/name="HAS Source Math Probe"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n', encoding='utf-8')
    inputs = {'candidate': folder / 'candidate.gd', 'harness': folder / 'harness.gd',
              'oracle': folder / 'PUBLIC_SYNTHETIC_ORACLE.json', 'full_receipt': FULL / 'state.json',
              'FK_receipt': FK / 'verification.json', 'root_closure': FK / 'authoritative-closure.json',
              'full_root_closure': FULL / 'authoritative-host-termination.json', 'project': project}
    pins = {name: {'path': str(path), 'sha256': sha(path)} for name, path in inputs.items()}
    target = folder / 'result.json'
    lease = {'format': 'has_source0x31_godot_math_lease_1',
             'phase': 'ROOT_APPROVED_AFTER_FULL_AND_FK_PASS', 'full_status': 'PASS', 'FK_status': 'PASS',
             'root_closed_both': True, 'expires_unix': time.time() + 600,
             'engine_sha256': ENGINE_SHA, 'source_HEAD': head, 'files': pins,
             'public_result': str(target), 'packet_index_sha256': args.expected_index}
    lease_path = folder / 'ROOT-LEASE.json'
    save(lease_path, lease)
    phases = []
    errors = []
    for label, options, timeout in [('parse', ['--check-only'], 30), ('run', [], 120)]:
        log = folder / (label + '-engine.log')
        command = [str(ENGINE), '--headless', '--path', str(folder), '--audio-driver', 'Dummy',
                   '--log-file', str(log), '--script', 'res://harness.gd', *options,
                   '--', str(lease_path), str(inputs['oracle']), str(target)]
        save(folder / (label + '-command.json'), command)
        started = time.monotonic()
        process = subprocess.Popen(command, cwd=folder, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            stdout, stderr = process.communicate(timeout=10)
        (folder / (label + '-stdout.log')).write_bytes(stdout)
        (folder / (label + '-stderr.log')).write_bytes(stderr)
        texts = [stdout.decode('utf-8', errors='replace'), stderr.decode('utf-8', errors='replace'),
                 log.read_text(encoding='utf-8', errors='replace') if log.exists() else '']
        markers = [line for text in texts for line in text.splitlines() if any(word in line for word in BAD)]
        proof = {'phase': label, 'pid': process.pid, 'exit': process.returncode,
                 'retained_Popen_reaped': process.poll() is not None, 'timed_out': timed_out,
                 'terminated_owned_child': timed_out, 'error_markers': markers,
                 'seconds': time.monotonic() - started,
                 'passed': process.returncode == 0 and not timed_out and not markers}
        save(folder / (label + '-process.json'), proof)
        phases.append(proof)
        if not proof['passed']:
            errors.append(label + ' failed; evidence preserved')
            break
    preserved = all(sha(path) == pins[name]['sha256'] for name, path in inputs.items())
    result = json.loads(target.read_bytes()) if target.exists() else None
    passed = len(phases) == 2 and all(row['passed'] for row in phases) and preserved and result is not None
    passed = passed and result.get('failures') == 0 and result.get('status') == 'PASSED_SCALAR64_SYNTHETIC_ENGINE_MATH_ONLY'
    report = {'format': 'has_root_source0x31_math_execution_1', 'passed': bool(passed),
              'source_HEAD': head, 'packet': str(packet), 'packet_index_sha256': args.expected_index,
              'phases': phases, 'errors': errors, 'inputs_preserved': preserved,
              'result': result, 'native_sdk_or_artist_fidelity': False, 'application_integration': False,
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder / 'verification.json', report)
    print(json.dumps({'passed': bool(passed), 'folder': str(folder), 'errors': errors,
                      'checks': result.get('checks') if result else 0}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
