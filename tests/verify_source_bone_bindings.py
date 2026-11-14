"""Separate authored headless bone-binding and imported-helper controls (79+17)."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

BAD = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'FAIL ', 'ObjectDB instances leaked',
       'unclaimed string names', 'Pages in use exist at exit')
CASES = [('bindings', 'tests/source_bone_bindings_unit.gd', 'SOURCE_BONE_BINDINGS ', 79),
         ('helper', 'tests/source_native_helper_choice_unit.gd', 'SOURCE_NATIVE_HELPER_CHOICE ', 17)]
PHASE_TIMEOUT = 25


def require(ok, message):
    if not ok:
        raise ValueError(message)


def no_reparse(path):
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'Source/output reparse path refused: ' + str(part))


def identity(path):
    no_reparse(path)
    before = path.stat()
    require(path.is_file(), 'Regular source/runtime file required')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            'Source/runtime changed while hashing')
    return {'sha256': digest, 'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns}


def sources():
    paths = [path for name in ('src', 'tests', 'tools', 'data', 'examples')
             for path in (ROOT / name).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts]
    paths += [ROOT / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
    return {path.relative_to(ROOT).as_posix(): identity(path) for path in sorted(paths)}


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, indent=2)
        stream.write('\n')


def head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                                   timeout=10).strip()


def run_phase(script, target, phase, fixture, runtime):
    engine_log = (target / (phase + '-engine.log')).resolve()
    flags = ['--check-only'] if phase == 'parse' else []
    args = command(script, headless=True,
                   extra=['--audio-driver', 'Dummy', *flags, '--', str(fixture)])
    boundary = args.index('--')
    require('--headless' in args[:boundary] and args[args.index('--script') + 1] == script,
            'Only the exact authored headless script is admitted')
    args[args.index('--log-file') + 1] = str(engine_log)
    executable = str(Path(args[0]).resolve(strict=True))
    observed = identity(Path(executable))
    require(executable not in runtime or runtime[executable] == observed, 'Headless runtime changed')
    runtime[executable] = observed
    save(target / (phase + '-command.json'), args)
    started = time.time_ns()
    process = subprocess.Popen(args, cwd=ROOT, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding='utf-8', errors='replace',
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=PHASE_TIMEOUT)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()  # This exact owned, childless headless test process only.
        stdout, stderr = process.communicate(timeout=5)
    console = stdout + stderr
    (target / (phase + '-console.log')).write_text(console, encoding='utf-8')
    engine = engine_log.read_text(encoding='utf-8', errors='replace') if engine_log.is_file() else ''
    result = {'headless': True, 'graphics': False, 'native_conversion': False,
              'pid': process.pid, 'exit': process.returncode, 'timeout_seconds': PHASE_TIMEOUT,
              'timed_out': timed_out, 'owned_headless_terminated_on_timeout': timed_out,
              'started_ns': started, 'finished_ns': time.time_ns(),
              'console': identity(target / (phase + '-console.log')),
              'engine_log': identity(engine_log) if engine_log.is_file() else None}
    save(target / (phase + '-process.json'), result)
    require(not timed_out and process.returncode == 0 and engine_log.is_file(),
            script + '/' + phase + ' failed or timed out; raw evidence retained')
    require(not any(token in console + engine for token in BAD),
            script + '/' + phase + ' emitted an error/warning/failure; raw evidence retained')
    return console, engine, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    candidate = options.output or ROOT / 'output/source-bone-bindings-headless' / str(time.time_ns())
    no_reparse(candidate.absolute())
    folder = candidate.resolve()
    require(folder != ROOT / 'output' and folder.is_relative_to((ROOT / 'output').resolve())
            and not folder.exists(), 'Use a new owned output directory')
    folder.mkdir(parents=True)
    before, revision = sources(), head()
    save(folder / 'source-before.json', {'commit': revision, 'files': before})
    runtime = {str(Path(sys.executable).resolve()): identity(Path(sys.executable).resolve())}
    report = {'format': 'has_source_bone_bindings_headless_1', 'passed': False,
              'folder': str(folder), 'checks': 0, 'expected_checks': 96, 'headless': True, 'graphics': False,
              'native_conversion': False, 'native_simulation': False, 'reports': {},
              'source_unchanged': False, 'runtime_unchanged': False,
              'scope': 'Separate 79 authored binding and 17 helper-choice controls; no native conversion, graphics, solver or actual imported-HAS adoption claim'}
    try:
        for label, script, marker, expected in CASES:
            target = folder / label
            target.mkdir()
            fixture = (target / 'fixture').resolve()
            # A successful check-only gate precedes every script execution.
            _, _, parse = run_phase(script, target, 'parse', fixture, runtime)
            console, engine, run = run_phase(script, target, 'run', fixture, runtime)
            rows = [json.loads(line[len(marker):]) for line in console.splitlines() if line.startswith(marker)]
            engine_rows = [json.loads(line[len(marker):]) for line in engine.splitlines() if line.startswith(marker)]
            require(len(rows) == len(engine_rows) == 1 and rows[0] == engine_rows[0],
                    label + ' has missing/duplicate/different console and engine reports')
            value = rows[0]
            require(type(value.get('checks')) is int and value['checks'] == expected
                    and type(value.get('failures')) is int and value['failures'] == 0,
                    label + ' authored check count/result differs')
            if label == 'bindings':
                require(value.get('native_conversion') is False and value.get('native_simulation') is False
                        and value.get('source_profile_claim_is_authored_fixture_only') is True,
                        'Binding fixture scope differs')
                require((fixture / 'result.json').is_file() and
                        json.loads((fixture / 'result.json').read_bytes()) == value,
                        'Binding fixture serialized report differs')
            else:
                require(value.get('native_import') is False and value.get('simulation') is False,
                        'Helper-choice fixture scope differs')
            save(target / 'verified.json', value)
            report['reports'][label] = {'checks': expected, 'failures': 0, 'result': value,
                                        'parse': parse, 'run': run}
            report['checks'] += expected
        require(report['checks'] == 96, 'Separate headless check ledger differs')
        report['passed'] = True
    except BaseException as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        try:
            after, final_revision = sources(), head()
            save(folder / 'source-after.json', {'commit': final_revision, 'files': after})
            report['source_unchanged'] = before == after and revision == final_revision
            report['functional_source_files'] = len(before)
            report['source_revision'] = revision
            report['source_before_sha256'] = identity(folder / 'source-before.json')['sha256']
            report['source_after_sha256'] = identity(folder / 'source-after.json')['sha256']
            report['runtime_unchanged'] = all(identity(Path(path)) == value for path, value in runtime.items())
            report['runtime_identity'] = runtime
        except BaseException as error:
            report['preservation_error'] = type(error).__name__ + ': ' + str(error)
        report['passed'] = report['passed'] and report['source_unchanged'] and report['runtime_unchanged']
        save(folder / 'verification.json', report)
    require(report['passed'], 'Headless source/runtime preservation failed; evidence retained')
    print('SOURCE_BONE_BINDINGS_HEADLESS ' + json.dumps({'passed': True, 'checks': 96,
                                                       'verification': str(folder / 'verification.json')}))


if __name__ == '__main__':
    main()
