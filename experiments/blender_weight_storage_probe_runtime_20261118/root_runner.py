"""ROOT ONLY, UNRUN: guarded finite synthetic Blender weight API execution.

Import/default invocation starts no child. --execute additionally needs reviewed
packet hashes and a fresh, hash-pinned Root authority. No model/import/export.
"""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
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
import traceback

import protocol as P

HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[1]
PROBE = ROOT / 'experiments/blender_weight_storage_probe_20261118'
BASELINE = ROOT / 'experiments/neon_windows_3a3701a_20261117/active-observation/source-before.json'
BASELINE_SHA = '3ef2e7d8bed6e063afef59c8caccba914663752998761350c882fd4efbc78e9d'
WRAPPER = ROOT / 'tools/private_desktop.py'
WRAPPER_SHA = '9788e7fde42de7bce022589c86146eaa93deb142ef368aa37a05259ec3047628'
LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
SCRIPTS = ('blender_weight_storage_probe.py', 'weight_storage_contract.py')
USER_ENV = ('BLENDER_USER_CONFIG', 'BLENDER_USER_SCRIPTS', 'BLENDER_USER_DATAFILES',
            'BLENDER_USER_EXTENSIONS', 'BLENDER_USER_RESOURCES')
CANONICAL_PATTERN = r'(run_canonical_owned\.ps1|start_canonical_[^ ]*\.ps1|tests[\\/]verify\.py|replay_runtime\.py|neon_owner_cold187)'


def digest(raw): return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(path)
    P.need(path.is_absolute(), 'Absolute path required')
    for item in (path, *path.parents):
        P.need(not item.is_symlink() and not (os.path.lexists(item) and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400), 'Reparse/symlink path refused')
    return path.resolve()


def read(path, maximum, *, allow_empty=False):
    path = safe(path); before = path.stat()
    P.need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
           and (0 <= before.st_size if allow_empty else 0 < before.st_size) and before.st_size <= maximum, 'Bounded single-link regular file required')
    raw = path.read_bytes(); after = path.stat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    P.need(fields(before) == fields(after) and len(raw) == before.st_size, 'Stable file identity required')
    return raw, {'bytes': len(raw), 'mtime_ns': before.st_mtime_ns, 'inode': before.st_ino, 'sha256': digest(raw)}


def pairs(rows):
    result = {}
    for key, value in rows:
        P.need(key not in result, 'Duplicate JSON key refused'); result[key] = value
    return result


def document(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON refused')))


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def packet(folder, pin):
    P.need(P.sha(pin), 'Exact packet SHA required')
    raw, _ = read(folder / 'INDEX.json', 1024 * 1024); P.need(digest(raw) == pin, 'Reviewed INDEX differs')
    entries = document(raw)['files']
    if type(entries) is dict: entries = [dict(path=name, **row) for name, row in entries.items()]
    P.need(type(entries) is list and 1 <= len(entries) <= 20, 'Bounded closed source packet required')
    names = [row['path'] for row in entries]
    P.need(len(names) == len(set(names)) and {p.name for p in folder.iterdir()} == {'INDEX.json', *names}, 'Exact packet directory closure required')
    for row in entries:
        name = row['path']
        P.need(type(name) is str and PurePosixPath(name).name == name and '/' not in name and '\\' not in name
               and ':' not in name and name not in ('.', '..', 'INDEX.json'), 'Direct source packet members required')
        body, _ = read(folder / name, 2 * 1024 * 1024)
        P.need(type(row['bytes']) is int and len(body) == row['bytes'] and digest(body) == row['sha256'], 'Source packet member differs')
    return {row['path']: {'bytes': row['bytes'], 'sha256': row['sha256']} for row in entries}


def functional_guard():
    raw, _ = read(BASELINE, 2 * 1024 * 1024); P.need(digest(raw) == BASELINE_SHA, 'Immutable public raw1029 map differs')
    baseline = document(raw); sources = baseline['source_sha256']
    P.need(baseline['commit'] == '3a3701ab6edfa81dc883759403c170b8555aab07' and type(sources) is dict and len(sources) == 1029, 'Qualified tested1029 source map required')
    names = {p.relative_to(ROOT).as_posix() for folder in ('src', 'tests', 'tools', 'data', 'examples')
             for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts}
    names.update(('project.godot', 'main.tscn', 'run.py', 'launch.pyw'))
    P.need(names == set(sources), 'Functional membership differs from tested1029')
    for name, pin in sources.items():
        path = safe(ROOT / name); P.need(path.is_relative_to(ROOT.resolve()), 'Functional source escapes Root')
        body, _ = read(path, 32 * 1024 * 1024, allow_empty=True); P.need(digest(body) == pin, 'Functional raw bytes differ')
    return {'public_snapshot_sha256': BASELINE_SHA, 'functional_files': 1029,
            'functional_map_sha256': digest(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode())}


def tools(pins):
    lock_raw, _ = read(LOCK, 2 * 1024 * 1024); P.need(digest(lock_raw) == LOCK_SHA, 'Approved prior runtime metadata differs')
    approved = document(lock_raw)['runtime_executables']; observed = {}
    for role, row in pins['executables'].items():
        path = safe(row['path']); raw, actual = read(path, 256 * 1024 * 1024)
        P.need(actual['sha256'] == row['sha256'], 'Approved executable SHA differs')
        if role != 'pwsh':
            P.need(str(path) in approved and all(actual[k] == approved[str(path)][k] for k in ('bytes', 'mtime_ns', 'sha256')), 'Approved prior executable byte/time identity differs')
        observed[role] = actual
    P.need(set(observed) == {'python', 'pythonw', 'blender', 'pwsh'}, 'Exact Python/Blender/PWSH tool scope required')
    wrapper, _ = read(WRAPPER, 256 * 1024); P.need(digest(wrapper) == WRAPPER_SHA, 'Approved private-desktop wrapper differs')
    return observed


def context(args, pins, authority, authority_identity):
    packet(HERE, args.packet_index_sha256); probe_members = packet(PROBE, pins['probe_index_sha256'])
    P.need(all(probe_members[name] == pins['scripts'][name] for name in SCRIPTS), 'Final probe scripts differ')
    raw, found = read(args.authority, 32 * 1024)
    P.need(digest(raw) == args.authority_sha256 and found == authority_identity, 'Root authority changed')
    P.authority(authority, ROOT, args.packet_index_sha256, pins['probe_index_sha256'], datetime.now(timezone.utc), initial=False)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=15,
                                   creationflags=subprocess.CREATE_NO_WINDOW).strip()
    P.need(head == P.HEAD, 'Current metadata HEAD differs; no expired admission is reusable')
    return {'tools': tools(pins), 'functional': functional_guard(), 'authority_sha256': digest(raw)}


def closure(stage, label, pins):
    # Read-only counts; inventory matching never authorizes process termination.
    tools(pins)
    code = "$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -notin @($PID," + str(os.getpid()) + ") -and (($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe|pythonw?)\\.exe$') -or ($_.Name -match '^(pwsh|powershell)\\.exe$' -and $_.CommandLine -match '" + CANONICAL_PATTERN + "')) -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*has-neon-review-20261116-c2d52ff*')}); @{owned_count=$items.Count; main_count=@($items | Where-Object {$_.CommandLine -like '*has-acceptance-session-20261111*'}).Count; review_count=@($items | Where-Object {$_.CommandLine -like '*has-neon-review-20261116-c2d52ff*'}).Count; observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    process = None
    try:
        process = subprocess.Popen([pins['executables']['pwsh']['path'], '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try: out, err = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.terminate()
            try: out, err = process.communicate(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); out, err = process.communicate(timeout=10)
            raise RuntimeError('Owned scope observer timed out')
        P.need(process.returncode == 0 and process.poll() is not None and not err.strip() and len(out) <= 65536, 'Retained scope observer failed')
        value = document(out); P.zero_scope(value); value['observer_retained_Popen_reaped'] = True
        save(stage / (label + '-closure.json'), value)
        return True
    finally:
        if process is not None and process.poll() is None: process.kill(); process.communicate(timeout=10)


def command(stage, pins):
    return [pins['executables']['pythonw']['path'], '-B', str(stage / 'private_desktop.py'),
            '--receipt', str(stage / 'private-receipt.json'), '--timeout', '120', '--memory-limit-mib', '2048', '--',
            pins['executables']['blender']['path'], '--factory-startup', '--disable-autoexec', '--offline-mode',
            '--background', '--threads', '1', '--python-exit-code', '47', '--python',
            str(stage / 'source/blender_weight_storage_probe.py'), '--', '--plan', str(stage / 'request.json')]


def invoke(stage, argv, env):
    save(stage / 'command.json', argv); process = None; timed = False; started = time.monotonic()
    with (stage / 'PRIVATE_STDOUT.log').open('xb') as out, (stage / 'PRIVATE_STDERR.log').open('xb') as err:
        try:
            process = subprocess.Popen(argv, cwd=stage, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            save(stage / 'launch.json', {'pid': process.pid, 'retained_Popen': True,
                                         'started_utc': datetime.now(timezone.utc).isoformat()})
            try: process.wait(timeout=165)
            except subprocess.TimeoutExpired:
                timed = True; process.terminate()
                try: process.wait(timeout=15)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=15)
        finally:
            if process is not None and process.poll() is None: timed = True; process.kill(); process.wait(timeout=15)
    P.need(process is not None and process.poll() is not None, 'Retained private wrapper was not reaped')
    result = {'pid': process.pid, 'exit': process.returncode, 'timed_out': timed, 'retained_Popen_reaped': True,
              'seconds': time.monotonic() - started,
              'streams_within_acceptance_cap': all((stage / name).stat().st_size <= 4 * 1024 * 1024 for name in ('PRIVATE_STDOUT.log', 'PRIVATE_STDERR.log'))}
    save(stage / 'process.json', result)
    return result


def copied_sources(stage, pins):
    P.need({p.name for p in (stage / 'source').iterdir()} == set(SCRIPTS), 'Owned source directory closure differs')
    for name in SCRIPTS:
        raw, row = read(stage / 'source' / name, 256 * 1024)
        P.need({k: row[k] for k in ('bytes', 'sha256')} == pins['scripts'][name], 'Owned copied script differs')
    raw, _ = read(stage / 'private_desktop.py', 256 * 1024); P.need(digest(raw) == WRAPPER_SHA, 'Owned wrapper copy differs')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true'); parser.add_argument('--authority', type=Path)
    parser.add_argument('--authority-sha256'); parser.add_argument('--packet-index-sha256')
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({'status': 'SOURCE_ONLY_NO_EXECUTION', 'native_run': False})); return 0
    P.need(os.name == 'nt' and args.authority is not None and P.sha(args.authority_sha256)
           and P.sha(args.packet_index_sha256), 'Explicit reviewed Root execution authority required')
    packet(HERE, args.packet_index_sha256)
    pins = document(read(HERE / 'RUNTIME_PINS.json', 64 * 1024)[0])
    raw, authority_identity = read(args.authority, 32 * 1024); P.need(digest(raw) == args.authority_sha256, 'Root authority SHA differs')
    authorized = document(raw)
    stage = P.authority(authorized, ROOT, args.packet_index_sha256, pins['probe_index_sha256'], datetime.now(timezone.utc))
    P.need(safe(args.authority) == ROOT / 'output' / ('weight-storage-probe-authority-' + authorized['run_id'] + '.json'), 'Exact direct Root authority path required')
    P.need(safe(sys.executable) == safe(pins['executables']['python']['path']), 'Approved Root Python caller required')
    baseline = context(args, pins, authorized, authority_identity)
    P.need(safe(stage).parent == safe(ROOT / 'output') and not os.path.lexists(stage), 'Fresh exact direct Root/output destination required')
    stage.mkdir(); (stage / 'source').mkdir(); (stage / 'temp').mkdir(); (stage / 'environment').mkdir()
    before = after = preserved = False; process = {}; receipt_summary = {}; summary = {}; report_sha = None; error_type = None
    try:
        before = closure(stage, 'before', pins)
        P.need(context(args, pins, authorized, authority_identity) == baseline, 'Prelaunch source/tools context differs')
        for name in SCRIPTS: shutil.copyfile(PROBE / name, stage / 'source' / name)
        shutil.copyfile(WRAPPER, stage / 'private_desktop.py'); copied_sources(stage, pins)
        env = {k: v for k, v in os.environ.items() if not k.startswith('BLENDER_') and k not in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP')}
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', TEMP=str(stage / 'temp'), TMP=str(stage / 'temp'), TMPDIR=str(stage / 'temp'))
        for key in USER_ENV:
            path = stage / 'environment' / key; path.mkdir(); env[key] = str(path)
        plan = {'format': 'has_fresh_synthetic_weight_storage_request_1', 'phase': 'ROOT_APPROVED_FRESH_SYNTHETIC_ONLY',
                'run_id': authorized['run_id'], 'expires_utc': authorized['expires_utc'], 'owned_root': str(stage),
                'owned_temp': str(stage / 'temp'), 'public_output': str(stage / 'PUBLIC_WEIGHT_STORAGE.json'),
                'runtime': {k: pins['executables']['blender'][k] for k in ('path', 'bytes', 'sha256')}, 'scripts': pins['scripts']}
        save(stage / 'request.json', plan); request_raw, request_identity = read(stage / 'request.json', 32 * 1024)
        request_sha = digest(request_raw)
        spec = importlib.util.spec_from_file_location('root_synthetic_weight_contract', stage / 'source/weight_storage_contract.py')
        contract = importlib.util.module_from_spec(spec); spec.loader.exec_module(contract)
        P.need(context(args, pins, authorized, authority_identity) == baseline, 'Immediate prelaunch context differs')
        process = invoke(stage, command(stage, pins), env)
        report_raw, _ = read(stage / 'PUBLIC_WEIGHT_STORAGE.json', 512 * 1024); report_sha = digest(report_raw)
        report = document(report_raw)
        summary = P.observation(report, plan, request_sha, contract)  # Read mismatch before requiring exit0.
        stdout, _ = read(stage / 'PRIVATE_STDOUT.log', 4 * 1024 * 1024)
        marker = 'HAS_SYNTHETIC_WEIGHT_STORAGE '
        lines = [line[len(marker):] for line in stdout.decode('utf-8', errors='strict').splitlines() if line.startswith(marker)]
        P.need(len(lines) == 1 and P.same(document(lines[0]), {'status': report['status'], 'request_sha256': request_sha,
               'cases': contract.CASE_COUNT, 'owned_cleanup_exact': report['owned_object_mesh_cleanup_exact']}), 'Exact report/request marker required')
        receipt_value = document(read(stage / 'private-receipt.json', 64 * 1024)[0])
        receipt_summary = P.receipt(receipt_value, process['exit'], contract)
        P.need(process['streams_within_acceptance_cap'] and process['timed_out'] is False, 'Private wrapper timeout/stream acceptance failed')
        P.need(read(stage / 'request.json', 32 * 1024)[1] == request_identity, 'Owned request changed')
    except BaseException as error:
        error_type = type(error).__name__
        (stage / 'PRIVATE_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        try:
            P.need(context(args, pins, authorized, authority_identity) == baseline, 'Final source/tools/authority context differs')
            if any((stage / 'source').iterdir()): copied_sources(stage, pins)
            preserved = True
        except BaseException as error:
            error_type = error_type or type(error).__name__
            (stage / 'PRIVATE_PRESERVATION_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
        try: after = closure(stage, 'after', pins)
        except BaseException as error:
            error_type = error_type or type(error).__name__
            (stage / 'PRIVATE_CLOSURE_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    passed = error_type is None and P.completed(process, receipt_summary, summary, preserved, before, after)
    result = {'format': 'has_root_finite_synthetic_weight_probe_execution_1', 'status': 'FINITE_SYNTHETIC_MATCH' if passed else 'NOT_PASS',
              'run_id': authorized['run_id'], 'metadata_head': P.HEAD, 'runtime_packet_sha256': args.packet_index_sha256,
              'probe_packet_sha256': pins['probe_index_sha256'], 'report_sha256': report_sha, 'observation': summary,
              'process': process, 'background_receipt': receipt_summary, 'source_tool_authority_preserved': preserved,
              'main_review_scopes_zero_before': before, 'main_review_scopes_zero_after': after, 'error_type': error_type,
              'model_or_native_asset_inputs': False, 'SourceIO_import_or_export': False,
              **{name: False for name in P.QUALIFICATIONS}}
    save(stage / 'ROOT_RESULT.json', result); print(json.dumps(result, sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__': raise SystemExit(main())
