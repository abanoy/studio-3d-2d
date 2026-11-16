"""Root-owned bounded native8 experiment; never modifies the product or originals."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
ENGINE_SHA = '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'
HEAD = 'f0dd57a2e568089d396fecba819ab987da658bf0'
FULL = ROOT / 'output/windows-canonical-bone-binding-20261115T225514304'
FK = ROOT / 'output/native-jiggle-headless-transport-prep-20261115/runtime-post-full-f0dd57a'
MATH = ROOT / 'output/source-0x31-godot-math-20261115-attempt1'
CLOSURE = ROOT / 'output/sfm-joints-final-replay-launch2-20261116T001109854/authoritative-closure.json'
BAD = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ',
       'ObjectDB instances leaked', 'unclaimed string names', 'resources still in use',
       'Pages in use exist at exit')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', required=True, type=Path)
    parser.add_argument('--index', required=True)
    parser.add_argument('--attempt', required=True, type=int, choices=range(1, 6))
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    assert packet.is_relative_to(ROOT / 'experiments') and sha(packet / 'INDEX.json') == args.index
    source_lock = packet / 'SOURCE_LOCK.json'
    pins = json.loads(source_lock.read_bytes())['files']
    assert len(pins) == 200 and len({p['path'] for p in pins}) == 200
    for row in json.loads((packet / 'INDEX.json').read_bytes())['files']:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = packet / relative
        assert path.is_file() and not path.is_symlink() and path.stat().st_size == row['bytes']
        assert sha(path) == row['sha256']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == HEAD
    full = json.loads((FULL / 'state.json').read_bytes())
    fk = json.loads((FK / 'verification.json').read_bytes())
    math = json.loads((MATH / 'verification.json').read_bytes())
    closure = json.loads(CLOSURE.read_bytes())
    assert full['status'] == 'passed' and full['suite_exit'] == 0 and full['source_unchanged']
    assert fk['passed'] and fk['result']['checks'] == 41588 and not fk['result']['failures']
    assert math['passed'] and math['result']['checks'] == 8994 and not math['result']['failures']
    assert closure['validation_passed'] and closure['owned_runtime_commands_absent']
    assert closure['root_graphics_lease_released'] and closure['no_process_killed']
    assert sha(ENGINE) == ENGINE_SHA
    catalogue_path = FULL / 'source-before.json'
    assert sha(catalogue_path) == '8d9e7d94c745081e0ca084bc64e7498bc7ccb218c44209e1354bcd53f3c50a2a'
    assert catalogue_path.read_bytes() == (FULL / 'source-after.json').read_bytes()
    catalogue = json.loads(catalogue_path.read_bytes())
    assert catalogue['commit'] == HEAD and len(catalogue['source_sha256']) == 1008
    full_pins = catalogue['source_sha256']
    assert all(sha(ROOT / path) == digest for path, digest in full_pins.items())
    folder = ROOT / ('output/source-0x31-native-leaf-20261115-attempt' + str(args.attempt))
    assert not folder.exists()
    folder.mkdir()
    project = folder / 'Studio'
    project.mkdir()
    original_pins = []
    for row in pins:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        source = ROOT / relative
        assert full_pins[row['path']] == row['sha256']
        assert source.is_file() and not source.is_symlink() and source.stat().st_size == row['bytes']
        assert sha(source) == row['sha256']
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        original_pins.append({'path': str(source), 'sha256': row['sha256']})
    # Public local vocabulary is required by ordinary Model.inventory labels.
    support_pins = []
    data_files = sorted((ROOT / 'data').rglob('*.json'))
    assert {str(p.relative_to(ROOT)).replace('\\', '/') for p in data_files} == {p for p in full_pins if p.startswith('data/')}
    assert len(data_files) == 3
    for source in data_files:
        assert not source.is_symlink()
        assert sha(source) == full_pins[source.relative_to(ROOT).as_posix()]
        target = project / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        support_pins.append({'source': str(source), 'path': str(target), 'sha256': sha(source)})
    aliases = {'candidate': (ROOT / 'experiments/source_0x31_godot_candidate_20261115/candidate.gd', 'leaf_candidate.gd'),
               'adapter': (packet / 'leaf_adapter.gd', 'leaf_adapter.gd'),
               'capture': (packet / 'weighted_capture.gd', 'weighted_capture.gd'),
               'harness': (packet / 'leaf_harness.gd', 'leaf_harness.gd')}
    lease = json.loads((packet / 'ROOT_LEASE_TEMPLATE.json').read_bytes())
    for name, (source, alias) in aliases.items():
        assert sha(source) == lease['files'][name]['sha256']
        target = project / alias
        target.write_bytes(source.read_bytes())
        lease['files'][name]['path'] = str(target)
    proofs = {'full_receipt': FULL / 'state.json', 'FK_receipt': FK / 'verification.json',
              'math_receipt': MATH / 'verification.json', 'root_closure': CLOSURE,
              'source_lock': source_lock, 'full_source_catalogue': catalogue_path}
    if args.attempt > 1:
        previous = ROOT / ('output/source-0x31-native-leaf-20261115-attempt' + str(args.attempt - 1)) / 'authoritative-closure.json'
        prior = json.loads(previous.read_bytes())
        assert prior['runtime_lease_released'] and prior['owned_runtime_commands_absent'] and prior['no_process_killed']
        proofs['previous_leaf_closure'] = previous
    for name, path in proofs.items():
        lease['files'][name] = {'path': str(path), 'sha256': sha(path)}
    for pin in lease['files'].values():
        assert sha(Path(pin['path'])) == pin['sha256']
    target = folder / 'result.json'
    lease.update(phase='ROOT_APPROVED_AFTER_FULL_FK_MATH_AND_CLOSURE', full_status='PASS',
                 FK_status='PASS', math_status='PASS', root_closed_all=True,
                 expires_unix=time.time() + 600, public_result=str(target))
    lease_path = folder / 'ROOT-LEASE.json'
    save(lease_path, lease)
    save(folder / 'COPY-PROVENANCE.json', {'source_HEAD': HEAD, 'packet_index_sha256': args.index,
          'application_files': len(pins), 'support': support_pins, 'original_pins': original_pins})
    phases = []
    for label, options, timeout in [('parse', ['--check-only'], 30), ('run', [], 60)]:
        log = folder / (label + '-engine.log')
        command = [str(ENGINE), '--headless', '--path', str(project), '--audio-driver', 'Dummy',
                   '--log-file', str(log), '--script', 'res://leaf_harness.gd', *options,
                   '--', str(lease_path), str(target)]
        save(folder / (label + '-command.json'), command)
        assert all(sha(project / row['path']) == row['sha256'] for row in pins)
        assert all(sha(Path(p['path'])) == p['sha256'] for p in lease['files'].values())
        assert all(sha(Path(p['source'])) == sha(Path(p['path'])) == p['sha256'] for p in support_pins)
        started = time.monotonic()
        process = subprocess.Popen(command, cwd=project, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        timed_out = False
        killed_owned_child = False
        save(folder / (label + '-owned-start.json'), {'pid': process.pid, 'command': command,
             'retained_Popen': True, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                killed_owned_child = True
                stdout, stderr = process.communicate(timeout=10)
        (folder / (label + '-stdout.log')).write_bytes(stdout)
        (folder / (label + '-stderr.log')).write_bytes(stderr)
        texts = [stdout.decode('utf-8', errors='replace'), stderr.decode('utf-8', errors='replace'),
                 log.read_text(encoding='utf-8', errors='replace') if log.exists() else '']
        markers = [line for text in texts for line in text.splitlines() if any(word in line for word in BAD)]
        proof = {'phase': label, 'pid': process.pid, 'exit': process.returncode,
                 'retained_Popen_reaped': process.poll() is not None, 'timed_out': timed_out,
                 'terminated_owned_child': timed_out, 'killed_owned_child': killed_owned_child,
                 'error_markers': markers,
                 'seconds': time.monotonic() - started,
                 'passed': process.returncode == 0 and not timed_out and not markers}
        save(folder / (label + '-process.json'), proof)
        phases.append(proof)
        if not proof['passed']:
            break
    preserved = all(sha(Path(p['path'])) == p['sha256'] for p in lease['files'].values())
    preserved = preserved and all(sha(Path(p['path'])) == p['sha256'] for p in original_pins)
    preserved = preserved and all(sha(Path(p['source'])) == sha(Path(p['path'])) == p['sha256'] for p in support_pins)
    preserved = preserved and all(sha(project / row['path']) == row['sha256'] for row in pins)
    preserved = preserved and all(sha(ROOT / path) == digest for path, digest in full_pins.items())
    result = json.loads(target.read_bytes()) if target.exists() else None
    passed = len(phases) == 2 and all(p['passed'] for p in phases) and preserved and result is not None
    passed = passed and result.get('failures') == 0 and result.get('status') == 'PASSED_NATIVE8_LEAF_READINESS_ONLY'
    passed = passed and result.get('checks') == 7289 and result.get('dynamics_steps') == 1440 and len(result.get('cases', [])) == 12
    report = {'format': 'has_root_native8_leaf_execution_1', 'passed': bool(passed),
              'source_HEAD': HEAD, 'packet': str(packet), 'packet_index_sha256': args.index,
              'phases': phases, 'inputs_preserved': preserved, 'result': result,
              'preregistered_expected': {'checks': 7289, 'dynamics_steps': 1440, 'cases': 12},
              'application_integration': False,
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(folder / 'verification.json', report)
    print(json.dumps({'passed': bool(passed), 'folder': str(folder),
                      'checks': result.get('checks') if result else 0,
                      'failures': result.get('failures') if result else 0,
                      'reason': result.get('reason') if result else None,
                      'errors': [p['error_markers'] for p in phases if not p['passed']]}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
