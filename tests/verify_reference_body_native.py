"""Checksum-pinned prepared VRM reference Body Physics on a private desktop.

No conversion, installation, network access or original artwork writes. Six
required cases use VRM0/VRM1 at relative sizes .5/1/2. Source/parameter hashes
are distinct from raw-original provenance reported by the preparation bundle.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from native_fixture_plans import wind_review_native_plans, WIND_REVIEW_PINS

ERRORS = ('SCRIPT ERROR', 'SHADER ERROR', 'ERROR:', 'FAIL ',
          'ObjectDB instances leaked', 'unclaimed string names',
          'Object was freed while a signal is being emitted',
          '_set_transient_exclusive_child', 'Pages in use exist at exit')
COUNTS = {'writer': 23, 'reader': 9}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def identity(path):
    path = Path(path)
    info = path.stat()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'sha256': digest, 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns}


def source_manifest():
    names = [path for name in ('src', 'tests', 'tools', 'data', 'examples')
             for path in (ROOT / name).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts]
    names += [ROOT / name for name in ('project.godot', 'main.tscn', 'run.py',
                                      'launch.pyw', 'dependencies.json')]
    return {path.relative_to(ROOT).as_posix(): identity(path) for path in sorted(set(names))}


def guard(path, boundary):
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    require('..' not in path.parts and path != boundary and path.resolve().is_relative_to(boundary.resolve()),
            'Output escapes the fresh owned test directory: ' + str(path))
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            info = None
        if info is not None:
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                    'Link/reparse output refused: ' + str(part))
        if part == boundary:
            break
    return path


def write_json(path, value):
    guard(path, ROOT / 'output' / 'reference-body-native')
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def runner():
    path = ROOT / 'run.py'
    spec = importlib.util.spec_from_file_location('reference_body_native_run', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.ROOT.resolve() == ROOT.resolve(), 'Runner belongs to a different checkout')
    return module


def originals_unchanged(plan):
    return identity(plan['manifest']) == plan['manifest_identity'] and all(
        identity(row['source']) == row['source_identity'] and
        identity(row['parameters']) == row['parameters_identity']
        for row in plan['inputs'].values())


def stage(folder, plan):
    staged = {}
    for role in ('vrm0', 'vrm1'):
        item = plan['inputs'][role]
        target = guard(folder / 'inputs' / role, folder)
        target.mkdir(parents=True)
        source, parameters = target / 'scene.glb', target / 'parameters.json'
        shutil.copy2(item['source'], source)
        shutil.copy2(item['parameters'], parameters)
        require(identity(source) == item['source_identity'] and identity(parameters) == item['parameters_identity'],
                'Staging changed source/report hash, byte size or nanosecond modification time')
        staged[role] = {'source': str(source).replace('\\', '/'),
                        'parameters': str(parameters).replace('\\', '/'),
                        'source_identity': identity(source),
                        'parameters_identity': identity(parameters),
                        'raw_original_sha256_from_report': WIND_REVIEW_PINS[role]['raw'],
                        'raw_original_bytes_read': False}
    write_json(folder / 'staged-before.json', staged)
    return staged


def invoke(run, target, reader=False):
    mode = 'reader' if reader else 'writer'
    args = run.command('tests/reference_body_native_smoke.gd', extra=[
        '--audio-driver', 'Dummy', '--', str(target / 'request.json'),
        *(['reader'] if reader else [])])
    require(os.name == 'nt' and args.count('--receipt') == 1 and
            Path(args[1]).resolve() == (ROOT / 'tools/private_desktop.py').resolve(),
            'Approved private Windows desktop required; no visible fallback')
    require(args.count('--path') == 1 and Path(args[args.index('--path') + 1]).resolve() == ROOT.resolve(),
            'Graphical command targets a different checkout')
    receipt_path = target / (mode + '-receipt.json')
    engine_path = target / (mode + '-engine.log')
    args[args.index('--receipt') + 1] = str(receipt_path)
    args[args.index('--log-file') + 1] = str(engine_path)
    write_json(target / (mode + '-command.json'), args)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        process = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                                 text=True, encoding='utf-8', errors='replace', timeout=330,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        output, code = process.stdout + process.stderr, process.returncode
    except subprocess.TimeoutExpired as error:
        def text(value):
            return value.decode('utf-8', 'replace') if isinstance(value, bytes) else value or ''
        output, code = text(error.stdout) + text(error.stderr) + '\nERROR: Native body timeout\n', 124
    (target / (mode + '-console.log')).write_text(output, encoding='utf-8')
    combined = output + ('\n' + engine_path.read_text(encoding='utf-8', errors='replace')
                         if engine_path.is_file() else '')
    errors = [marker for marker in ERRORS if marker in combined]
    result_path = target / (mode + '-result.json')
    result = json.loads(result_path.read_bytes()) if result_path.is_file() else {}
    receipt = json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else {}
    clean = (receipt.get('exit') == 0 and receipt.get('child_desktop_confirmed') is True and
             receipt.get('foreground_child_observed') is False and
             receipt.get('desktop_switch_requested') is False and
             receipt.get('job_closed') is True and receipt.get('desktop_closed') is True)
    request = json.loads((target / 'request.json').read_bytes())
    actual = result.get('metrics', {}).get('project_root', '')
    correct_root = bool(actual) and Path(actual).resolve() == ROOT.resolve()
    passed = (code == 0 and not errors and clean and correct_root and
              result.get('role') == request['role'] and result.get('scale') == request['scale'] and
              result.get('mode') == mode and result.get('checks') == COUNTS[mode] and
              result.get('failures') == 0 and result.get('native_fidelity_claimed') is False and
              'REFERENCE_BODY_NATIVE ' in output)
    row = {'mode': mode, 'exit': code, 'passed': passed, 'result': result,
           'error_markers': errors, 'correct_project_root': correct_root,
           'private_receipt': str(receipt_path), 'clean_isolation': clean}
    write_json(target / (mode + '-verification.json'), row)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs-manifest', type=Path)
    options = parser.parse_args()
    require(os.name == 'nt', 'This verifier requires the approved private Windows desktop')
    family = ROOT / 'output' / 'reference-body-native'
    guard(family, ROOT / 'output').mkdir(parents=True, exist_ok=True)
    folder = guard(family / str(time.time_ns()), family)
    folder.mkdir(exist_ok=False)
    before = source_manifest()
    write_json(folder / 'source-before.json', before)
    plan, staged, results, error = None, {}, [], ''
    try:
        plan = wind_review_native_plans(options.inputs_manifest)
        write_json(folder / 'native-originals-before.json', plan)
        staged = stage(folder, plan)
        run = runner()
        for role in ('vrm0', 'vrm1'):
            for scale in (0.5, 1.0, 2.0):
                target = guard(folder / (role + '-scale-' + str(scale)), folder)
                target.mkdir()
                item = staged[role]
                request = {'role': role, 'scale': scale,
                           'folder': str(target).replace('\\', '/'),
                           'project_root': str(ROOT).replace('\\', '/'),
                           'source': item['source'], 'parameters': item['parameters'],
                           'source_sha256': item['source_identity']['sha256'],
                           'parameters_sha256': item['parameters_identity']['sha256'],
                           'raw_original_sha256_from_report': item['raw_original_sha256_from_report']}
                write_json(target / 'request.json', request)
                writer = invoke(run, target)
                row = {'role': role, 'scale': scale, 'writer': writer}
                results.append(row)
                write_json(folder / 'progress.json', results)
                require(writer['passed'], 'Native writer failed: ' + str(target))
                row['reader'] = invoke(run, target, True)
                write_json(folder / 'progress.json', results)
                require(row['reader']['passed'], 'Native cold reader failed: ' + str(target))
                print('PASS ' + role + ' relative size ' + str(scale), flush=True)
    except Exception as failure:
        error = type(failure).__name__ + ': ' + str(failure)
    finally:
        after = source_manifest()
        try:
            originals_same = originals_unchanged(plan) if plan else None
            staged_after = {role: {**item, 'source_identity': identity(item['source']),
                                   'parameters_identity': identity(item['parameters'])}
                            for role, item in staged.items()}
            staged_same = staged_after == staged if staged else None
        except Exception as failure:
            originals_same, staged_same, staged_after = False, False, {}
            error = error or type(failure).__name__ + ': ' + str(failure)
        complete = len(results) == 6 and all(row['writer']['passed'] and row.get('reader', {}).get('passed') for row in results)
        passed = not error and complete and before == after and originals_same is True and staged_same is True
        report = {'format': 'has_reference_body_native_1', 'passed': passed,
                  'folder': str(folder), 'project_root': str(ROOT), 'error': error,
                  'expected_cases': 6, 'results': results,
                  'functional_hash_size_mtime_unchanged': before == after,
                  'original_fixture_hash_size_mtime_unchanged': originals_same,
                  'staged_fixture_hash_size_mtime_unchanged': staged_same,
                  'source_parameter_raw_hashes_distinctly_recorded': bool(staged),
                  'raw_original_bytes_read': False, 'private_art_uploaded': False,
                  'native_fidelity_claimed': False,
                  'pmd_pmx_sfm_controls': 'Not run: this bounded suite uses the two exact pinned VRM pairs.',
                  'scope': 'Prepared original-derived VRM0/VRM1; actual six-foot review, relative .5/1/2, connected Body/Freeze/Undo/Redo/Local Record, source FK, packed HAS/cold preview and independent drawing. No converter, broad native fidelity, contact-oracle, movie, artist or device qualification.'}
        write_json(folder / 'source-after.json', after)
        write_json(folder / 'staged-after.json', staged_after)
        write_json(folder / 'verification.json', report)
        latest = guard(ROOT / 'output' / 'reference-body-native-verification.json', ROOT / 'output')
        latest.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('REFERENCE_BODY_NATIVE_VERIFICATION ' + json.dumps({
        'passed': passed, 'folder': str(folder), 'error': error}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
