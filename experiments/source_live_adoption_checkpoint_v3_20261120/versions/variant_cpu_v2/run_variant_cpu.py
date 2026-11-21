"""Root-only isolated synthetic CPU coordinator, authored but not executed.

Restore to ROOT/output before execution. Runs only after exact successful360 Full.
No native engine, SDK, asset conversion, current-root output or bytecode write.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / 'output/windows-reference-body-1795233568436471500'
REVISION = '36044471151a6e561d6d3a404859e76ddd05738d'
PYTHON = Path('C:/Program Files/Python313/python.exe')
PYTHON_BYTES = 105840
PYTHON_SHA = '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
DEPENDENCIES = [
    {
        "path": "output/source-next-sfm-variants-prep-20261120/variant_plan.py",
        "bytes": 10002,
        "sha256": "41cc24c4d8b8ee953bb5b229e668d92daba4f9dd6b317e2f7c0decd30290aded"
    },
    {
        "path": "output/source-next-sfm-variants-prep-20261120/test_variant_plan.py",
        "bytes": 12036,
        "sha256": "a11a053e392e77f26486d4681529d11a0e77dd6d4b5b677ea94aa8cce2ebd5d8"
    },
    {
        "path": "output/source-sfm-variant-export-prep-20261120/retained_variants.py",
        "bytes": 28942,
        "sha256": "455b084748a4470e9ffb38b31d0902583fe8c7b6271ad0ed5746ae6910b00804"
    },
    {
        "path": "output/source-sfm-variant-export-prep-20261120/variant_plan.py",
        "bytes": 10002,
        "sha256": "41cc24c4d8b8ee953bb5b229e668d92daba4f9dd6b317e2f7c0decd30290aded"
    },
    {
        "path": "output/source-sfm-variant-export-prep-20261120/test_retained_variants.py",
        "bytes": 20714,
        "sha256": "86aff623ecc0aabaebbbc60429da75afdba4339bff5a8d69fe53c029654a68b1"
    },
    {
        "path": "output/source-sfm-variant-runtime-prep-20261120/tools/model_variant_plan.py",
        "bytes": 10002,
        "sha256": "41cc24c4d8b8ee953bb5b229e668d92daba4f9dd6b317e2f7c0decd30290aded"
    },
    {
        "path": "output/source-sfm-variant-runtime-prep-20261120/tools/model_variant_project.py",
        "bytes": 6621,
        "sha256": "197bd072cffdd8b7702b5bc6fcac6dd80688bab2f87824d7186b22f1b908c98a"
    },
    {
        "path": "output/source-sfm-variant-runtime-prep-20261120/tests/test_model_variant_project.py",
        "bytes": 5147,
        "sha256": "f3dc05cc00da1f77514b47e5de99d09a625654a94b697a787cf51cf2ca5ba1ee"
    },
    {
        "path": "tools/source_jiggle_crosswalk.py",
        "bytes": 29012,
        "sha256": "c384cbfe912170d5107995c60ac5bcf033ad6061a14ff29d06599898fcfaf646"
    },
    {
        "path": "tools/import_basis.py",
        "bytes": 22046,
        "sha256": "fbb9efa1b56b0e50df125107af88b738f68657917f75ccbe0819f9eb5e92960d"
    }
]
SUITES = (
    ('planner', 'output/source-next-sfm-variants-prep-20261120', 'test_variant_plan.py', 31),
    ('exporter', 'output/source-sfm-variant-export-prep-20261120', 'test_retained_variants.py', 26),
    ('project', 'output/source-sfm-variant-runtime-prep-20261120/tests', 'test_model_variant_project.py', 13),
)
MAX_FILE = 256 * 1024 * 1024
MAX_LOG = 1024 * 1024
SUITE_TIMEOUT = 120.0
ADMITTED = {}
OWNED_CHILDREN = []


class Refusal(RuntimeError):
    pass


def need(condition, code):
    if not condition:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(info):
    # Windows lstat infers execute bits from .exe; fstat cannot infer its name.
    mode = info.st_mode & ~0o111 if os.name == 'nt' and stat.S_ISREG(info.st_mode) else info.st_mode
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink, mode, getattr(info, 'st_file_attributes', 0) & ~0x40000)


def regular(info):
    return (stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
            info.st_nlink == 1 and not getattr(info, 'st_file_attributes', 0) & 0x400)


def parent_guards(path, boundary):
    need(path.resolve().is_relative_to(boundary.resolve()), 'PATH_OUTSIDE_ADMITTED_BOUNDARY')
    current = path.parent
    while current != boundary:
        info = current.lstat()
        need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
             not getattr(info, 'st_file_attributes', 0) & 0x400, 'DIRECTORY_ALIAS_REFUSED')
        current = current.parent
    info = boundary.lstat()
    need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
         not getattr(info, 'st_file_attributes', 0) & 0x400, 'BOUNDARY_ALIAS_REFUSED')


def read_stable(path, remember=True, limit=MAX_FILE):
    info = path.lstat()
    need(regular(info) and 0 <= info.st_size <= limit, 'BOUNDED_SINGLE_LINK_FILE_REQUIRED')
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(info), 'FILE_CHANGED_BEFORE_READ')
        raw = stream.read(info.st_size + 1)
        opened = os.fstat(stream.fileno())
    need(len(raw) == info.st_size and stamp(info) == stamp(opened) == stamp(path.lstat()), 'FILE_CHANGED_DURING_READ')
    identity = (stamp(info), sha(raw))
    name = str(path.resolve())
    if remember:
        if name in ADMITTED:
            need(ADMITTED[name] == identity, 'ADMITTED_INPUT_CHANGED')
        else:
            ADMITTED[name] = identity
    return raw, info


def json_pairs(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def parse(raw):
    def nonfinite(_value):
        raise Refusal('NONFINITE_JSON_VALUE')
    return json.loads(raw, object_pairs_hook=json_pairs, parse_constant=nonfinite)


def exact_json(path, expected_sha):
    need(type(expected_sha) is str and re.fullmatch('[0-9a-f]{64}', expected_sha) and expected_sha != '0' * 64,
         'REAL_REVIEWED_FULL_DIGEST_REQUIRED')
    raw, _info = read_stable(path)
    need(sha(raw) == expected_sha, 'FULL_ARTIFACT_DIGEST_DIFFERS')
    return parse(raw)


def current_sources(catalogue):
    need(type(catalogue) is dict and len(catalogue) == 1084, 'EXACT_1084_CATALOGUE_REQUIRED')
    result = {}
    for name, row in catalogue.items():
        need(type(name) is str and name and ':' not in name and '\\' not in name, 'SOURCE_PATH_SCHEMA')
        relative = PurePosixPath(name)
        need(relative.as_posix() == name and not relative.is_absolute() and '..' not in relative.parts and
             '__pycache__' not in relative.parts and relative.suffix != '.pyc', 'SOURCE_PATH_SCHEMA')
        need(type(row) is dict and type(row.get('bytes')) is int and type(row.get('mtime_ns')) is int and
             type(row.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'SOURCE_ROW_SCHEMA')
        target = ROOT / name
        parent_guards(target, ROOT)
        raw, info = read_stable(target)
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'] and info.st_mtime_ns == row['mtime_ns'],
             'CURRENT_SOURCE_DIFFERS_FROM_CLOSED_FULL')
        result[name] = (stamp(info), sha(raw))
    return result


def final_preservation():
    failures = []
    for name, identity in tuple(ADMITTED.items()):
        try:
            raw, info = read_stable(Path(name), remember=False)
            need((stamp(info), sha(raw)) == identity, 'INPUT_CHANGED_AFTER_CPU_RUN')
        except BaseException as error:
            failures.append({'path': name, 'error_type': type(error).__name__})
    return failures


def no_cache_files(stage):
    pending = [stage]
    while pending:
        folder = pending.pop()
        info = folder.lstat()
        need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
             not getattr(info, 'st_file_attributes', 0) & 0x400, 'STAGE_DIRECTORY_ALIAS')
        for child in folder.iterdir():
            info = child.lstat()
            need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'STAGE_ALIAS')
            need(child.name != '__pycache__' and child.suffix != '.pyc', 'UNEXPECTED_BYTECODE_WRITE')
            if stat.S_ISDIR(info.st_mode):
                pending.append(child)
            else:
                need(regular(info), 'STAGE_NONREGULAR_FILE')


def reap(process):
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    else:
        process.wait(timeout=5)
    need(process.poll() is not None, 'OWNED_CHILD_NOT_REAPED')


def run_suite(stage, env, suite):
    label, directory, pattern, expected = suite
    logs = stage / 'logs'
    stdout_path, stderr_path = logs / (label + '.stdout.log'), logs / (label + '.stderr.log')
    process = None
    started = time.perf_counter()
    result = {'suite': label, 'expected_tests': expected, 'launched': False, 'reaped': False}
    try:
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            args = [str(PYTHON), '-B', '-s', '-m', 'unittest', 'discover', '-s', str(stage / directory), '-p', pattern, '-v']
            process = subprocess.Popen(args, cwd=stage, env=env, stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            OWNED_CHILDREN.append(process)
            result['launched'] = True
            result['pid'] = process.pid
            print(json.dumps({'event': 'suite_started', 'suite': label, 'expected_tests': expected}), flush=True)
            deadline = time.monotonic() + SUITE_TIMEOUT
            while process.poll() is None:
                need(time.monotonic() < deadline, 'CPU_SUITE_TIMEOUT')
                need(stdout_path.stat().st_size <= MAX_LOG and stderr_path.stat().st_size <= MAX_LOG, 'CPU_LOG_BUDGET')
                time.sleep(0.05)
            process.wait(timeout=5)
            result['exit'] = process.returncode
    except BaseException as error:
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if type(error) is Refusal else 'CPU_SUITE_EXCEPTION'
    finally:
        try:
            reap(process)
            result['reaped'] = process is None or process.poll() is not None
        except BaseException as error:
            result['cleanup_error_type'] = type(error).__name__
    result['seconds'] = time.perf_counter() - started
    try:
        if stdout_path.exists() and stderr_path.exists() and result['reaped']:
            stdout, _info = read_stable(stdout_path, remember=False, limit=MAX_LOG)
            stderr, _info = read_stable(stderr_path, remember=False, limit=MAX_LOG)
            combined = stdout + b'\n' + stderr
            counts = re.findall(rb'^Ran ([0-9]+) tests? in [0-9.]+s\r?$', combined, re.M)
            ok = re.findall(rb'^OK\r?$', combined, re.M)
            result['tests_run'] = int(counts[0]) if len(counts) == 1 else None
            result['passed'] = (result.get('exit') == 0 and result['tests_run'] == expected and len(ok) == 1 and
                                'error_type' not in result and 'cleanup_error_type' not in result)
            result['stdout'] = {'bytes': len(stdout), 'sha256': sha(stdout)}
            result['stderr'] = {'bytes': len(stderr), 'sha256': sha(stderr)}
        else:
            result['passed'] = False
    except BaseException as error:
        result['passed'] = False
        result['readback_error_type'] = type(error).__name__
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-completion-sha256', required=True)
    parser.add_argument('--full-source-after-sha256', required=True)
    args = parser.parse_args()
    need(not sys.flags.optimize and sys.version_info[:2] == (3, 13), 'ORDINARY_PYTHON313_REQUIRED')
    need(Path(sys.executable).resolve() == PYTHON.resolve(), 'APPROVED_PYTHON_REQUIRED')
    stage, lock_handle = None, None
    primary = None
    result = {'format': 'has_source_variant_preparatory_cpu_coordinator_1', 'status': 'FAIL',
              'revision': REVISION, 'dependency_files': 10, 'expected_tests': 70, 'suites': [],
              'native_or_engine_launched': False, 'sdk_or_native_assets_read': False,
              'actual_variant_export_or_runtime_qualified': False, 'application_adopted': False,
              'current_root_output_or_bytecode_writes_authorized': False}
    try:
        read_stable(Path(__file__).resolve())
        python_raw, _info = read_stable(PYTHON)
        need(len(python_raw) == PYTHON_BYTES and sha(python_raw) == PYTHON_SHA, 'PYTHON_PIN_DIFFERS')
        lock_raw, _info = read_stable(LOCK)
        need(sha(lock_raw) == LOCK_SHA, 'TRUSTED_RUNTIME_LOCK_DIFFERS')
        runtime = parse(lock_raw)['runtime_executables'][str(PYTHON).replace('/', '\\')]
        need(runtime['bytes'] == PYTHON_BYTES and runtime['sha256'] == PYTHON_SHA, 'TRUSTED_PYTHON_BINDING_DIFFERS')
        completion = exact_json(FULL / 'completion.json', args.full_completion_sha256)
        need(completion.get('format') == 'has_reference_body_full_coordinator_1' and completion.get('revision') == REVISION and
             type(completion.get('exit')) is int and completion['exit'] == 0 and completion.get('functional_source_count') == 1084,
             'SUCCESSFUL_FULL360_REQUIRED')
        for key in ('child_reaped', 'functional_sources_unchanged', 'revision_unchanged', 'all_private_jobs_isolated_closed',
                    'nonzero_jobs_are_expected_cancellations', 'receipt_provenance_verified', 'whole_verifier_pass', 'fresh_final_report'):
            need(completion.get(key) is True, 'SUCCESSFUL_CLOSED_FULL360_REQUIRED')
        catalogue = exact_json(FULL / 'source-after.json', args.full_source_after_sha256)
        source_before = current_sources(catalogue)
        need(len(DEPENDENCIES) == 10 and len({row['path'].casefold() for row in DEPENDENCIES}) == 10, 'EXACT_TEN_DEPENDENCIES_REQUIRED')
        retained = {}
        for row in DEPENDENCIES:
            parent_guards(ROOT / row['path'], ROOT)
            raw, _info = read_stable(ROOT / row['path'])
            need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'DEPENDENCY_PIN_DIFFERS')
            retained[row['path']] = raw
        # Exclusive new sibling; no existing folder or current-root output is owned.
        candidate = ROOT.parent / ('has-source-variant-cpu-' + str(time.time_ns()))
        need(candidate.parent.resolve() == ROOT.parent.resolve() and candidate.name.startswith('has-source-variant-cpu-'), 'STAGE_CONTAINMENT')
        candidate.mkdir()
        stage = candidate  # Ownership starts only after exclusive creation succeeds.
        lock_handle = (stage / 'COORDINATOR.lock').open('xb')
        (stage / 'logs').mkdir(); (stage / 'temp').mkdir(); (stage / 'userdata').mkdir()
        for name, raw in retained.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(raw); output.flush(); os.fsync(output.fileno())
            copied, _info = read_stable(target)
            need(copied == raw, 'SNAPSHOT_COPY_DIFFERS')
        env = dict(os.environ)
        for key in ('PYTHONSTARTUP', 'PYTHONINSPECT', 'PYTHONHOME', 'PYTHONPYCACHEPREFIX'):
            env.pop(key, None)
        env.update(PYTHONPATH=str(stage / 'tools'), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                   TEMP=str(stage / 'temp'), TMP=str(stage / 'temp'), APPDATA=str(stage / 'userdata'), LOCALAPPDATA=str(stage / 'userdata'))
        for suite in SUITES:
            row = run_suite(stage, env, suite)
            result['suites'].append(row)
            need(row.get('reaped') is True, 'UNREAPED_CHILD_PREVENTS_LATER_SUITE')
        no_cache_files(stage)
        need(current_sources(catalogue) == source_before, 'CURRENT_1084_SOURCES_CHANGED')
        need(all(row['passed'] for row in result['suites']) and len(result['suites']) == 3, 'CPU_SUITE_FAILED')
        result['status'] = 'PASS'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if type(error) is Refusal else 'COORDINATOR_EXCEPTION'
    finally:
        child_cleanup_failures = []
        for child in OWNED_CHILDREN:
            try:
                reap(child)
            except BaseException as error:
                child_cleanup_failures.append({'pid': child.pid, 'error_type': type(error).__name__})
        result['owned_child_cleanup_failures'] = child_cleanup_failures
        if child_cleanup_failures:
            result['status'] = 'FAIL'
        failures = final_preservation()
        result['preservation_failures'] = failures
        result['all_admitted_inputs_hash_size_identity_nsmtime_unchanged'] = not failures
        result['admitted_input_files'] = len(ADMITTED)
        if failures:
            result['status'] = 'FAIL'
        if lock_handle is not None:
            try:
                lock_handle.close()
            except BaseException as error:
                result['status'] = 'FAIL'
                result['lock_close_error_type'] = type(error).__name__
        result['owned_children_reaped'] = not child_cleanup_failures and all(child.poll() is not None for child in OWNED_CHILDREN)
        if not result['owned_children_reaped']:
            result['status'] = 'FAIL'
        if stage is not None:
            result['stage'] = str(stage)
            # A result is new and bounded; raw test logs stay in this owned sibling.
            try:
                with (stage / 'PUBLIC_CPU_RESULT.json').open('x', encoding='utf8') as output:
                    json.dump(result, output, indent=2); output.write('\n')
            except BaseException as error:
                result['status'] = 'FAIL'
                result['result_write_error_type'] = type(error).__name__
        print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'PASS' and primary is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
