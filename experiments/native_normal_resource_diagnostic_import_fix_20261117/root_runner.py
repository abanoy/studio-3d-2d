"""ROOT ONLY, later: bounded read-only B metadata diagnostic on a private desktop."""
from pathlib import Path
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import diagnostic_support as S

ENV_KEYS = ('TEMP', 'TMP', 'BLENDER_USER_CONFIG', 'BLENDER_USER_SCRIPTS', 'BLENDER_USER_DATAFILES', 'BLENDER_USER_EXTENSIONS')
CANONICAL_PATTERN = r'(run_canonical_owned\.ps1|start_canonical_[^ ]*\.ps1|tests[\\/]verify\.py|replay_runtime\.py|neon_owner_cold187)'
PLACEMENT = {'format': 'has_hidden_background_desktop_placement_sentinel_1', 'class': 'STATIC',
             'requested_size_pixels': [0, 0], 'disabled': True, 'noactivate_style': True,
             'toolwindow_style': True, 'visible_at_creation': False, 'visible_before_destruction': False,
             'owned_pid_and_thread_verified': True, 'destroyed_in_finally': True,
             'show_or_activation_calls': False, 'thread_desktop_switch_calls': False}


def typed_equal(actual, expected):
    if type(actual) is not type(expected): return False
    if type(expected) is dict: return actual.keys() == expected.keys() and all(typed_equal(actual[k], expected[k]) for k in expected)
    if type(expected) is list: return len(actual) == len(expected) and all(typed_equal(a, b) for a, b in zip(actual, expected))
    return actual == expected


def receipt_ok(receipt):
    required = {'format': 'studio_private_desktop_1', 'exit': 0, 'private_window_seen': True,
                'child_desktop_confirmed': True, 'foreground_child_observed': False,
                'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True,
                'job_memory_limit_bytes': 4096 * 1024 * 1024}
    return all(typed_equal(receipt.get(k), v) for k, v in required.items()) and not any(
        receipt.get(k) for k in ('error', 'monitor_error', 'desktop_enumeration_error', 'timed_out', 'cancelled'))


def closure(stage, label):
    # Read-only inventory; termination is never applied to an inventory-matched PID.
    code = "$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -notin @($PID," + str(os.getpid()) + ") -and (($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe|pythonw?)\\.exe$') -or ($_.Name -match '^(pwsh|powershell)\\.exe$' -and $_.CommandLine -match '" + CANONICAL_PATTERN + "')) -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*has-neon-review-20261116-c2d52ff*')}); @{owned_count=$items.Count; main_count=@($items | Where-Object {$_.CommandLine -like '*has-acceptance-session-20261111*'}).Count; neon_count=@($items | Where-Object {$_.CommandLine -like '*has-neon-review-20261116-c2d52ff*'}).Count; observed_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress"
    process = subprocess.Popen([str(S.PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    try: out, err = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        process.terminate()
        try: out, err = process.communicate(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); out, err = process.communicate(timeout=10)
        raise RuntimeError('Owned inventory observer timed out')
    (stage / (label + '-PRIVATE_INVENTORY_STDOUT.log')).write_bytes(out)
    (stage / (label + '-PRIVATE_INVENTORY_STDERR.log')).write_bytes(err)
    S.need(process.returncode == 0 and process.poll() is not None and not err.strip(), 'Fresh scope observer failed')
    value = json.loads(out); value['observer_retained_Popen_reaped'] = True
    S.save(stage / (label + '-closure.json'), value)
    S.need(all(type(value.get(k)) is int and value[k] == 0 for k in ('owned_count', 'main_count', 'neon_count')), 'Native lane is occupied')
    return value


def invoke(stage, command, env):
    S.save(stage / 'command.json', command); process = None; timed = False
    started = time.monotonic()
    stdout_path = stage / 'PRIVATE_STDOUT.log'; stderr_path = stage / 'PRIVATE_STDERR.log'
    # Direct private-file streams keep native output out of parent RAM. The
    # post-run acceptance caps are not a live disk-allocation bound.
    with stdout_path.open('xb') as out, stderr_path.open('xb') as err:
        try:
            process = subprocess.Popen(command, cwd=stage, env=env, stdin=subprocess.DEVNULL,
                                       stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
            S.save(stage / 'launch.json', {'pid': process.pid, 'retained_Popen': True,
                                         'observed_after_creation_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            try: process.wait(timeout=165)
            except subprocess.TimeoutExpired:
                timed = True; process.terminate()
                try: process.wait(timeout=15)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=15)
        finally:
            if process is not None and process.poll() is None:
                timed = True; process.kill(); process.wait(timeout=15)
    S.need(process is not None and process.poll() is not None, 'Retained wrapper was not reaped')
    result = {'pid': process.pid, 'exit': process.returncode, 'timed_out': timed,
              'retained_Popen_reaped': True, 'seconds': time.monotonic() - started}
    S.save(stage / 'process.json', result)
    S.need(not timed and process.returncode == 0 and stdout_path.stat().st_size <= 4 * 1024 * 1024
           and stderr_path.stat().st_size <= 4 * 1024 * 1024, 'Owned diagnostic failed, timed out or exceeded stream acceptance cap')
    return result, stdout_path.read_text(encoding='utf-8', errors='strict')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--admission-sha256', required=True); parser.add_argument('--packet-index-sha256', required=True)
    parser.add_argument('--root-lane-confirmed', action='store_true', required=True)
    args = parser.parse_args(); S.need(os.name == 'nt', 'Windows root execution required')
    value, originals, lock, reference = S.check_inputs(args.admission, args.admission_sha256, args.packet_index_sha256)
    S.need(str(S.safe(sys.executable)) in lock['runtime_executables']
           and Path(sys.executable).name.lower() in ('python.exe', 'pythonw.exe'), 'Approved Python caller required')
    def recheck():
        current = S.check_inputs(args.admission, args.admission_sha256, args.packet_index_sha256)
        S.need(current == (value, originals, lock, reference), 'Admission/source/tool/input context changed')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S.ROOT, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
        S.need(head == value['expected_metadata_head'], 'Current metadata checkpoint changed')
    recheck()
    stage = S.safe(value['output']); S.need(stage.parent == S.ROOT / 'output' and not stage.exists(), 'Fresh direct ROOT/output destination required')
    stage.mkdir(); (stage / 'environment').mkdir()
    env = os.environ.copy(); env['PYTHONDONTWRITEBYTECODE'] = '1'
    for key in ENV_KEYS:
        path = stage / 'environment' / key; path.mkdir(); env[key] = str(path)
    env['TMPDIR'] = env['TEMP']
    before = after = {}; process = {}; complete = preserved = False; public = {}; error_type = None
    try:
        before = closure(stage, 'before'); recheck()
        original = S.safe(S.ROOT / reference['files']['blend']['path']); owned = stage / 'editable.blend'
        shutil.copyfile(original, owned); r = S.reader(); copied = r.identity(owned, single_link=True)
        S.need(copied['bytes'] == originals['blend']['bytes'] and copied['sha256'] == originals['blend']['sha256'], 'Byte-identical B copy required')
        blender = next(path for path in lock['runtime_executables'] if Path(path).name.lower() == 'blender.exe')
        request = {'stage': str(stage), 'packet_sha256': args.packet_index_sha256,
                   'admission_path': str(S.safe(args.admission)), 'admission_sha256': args.admission_sha256,
                   'original_blend': str(original), 'owned_blend': str(owned), 'original_identity': originals['blend'],
                   'owned_identity': copied, 'blender_executable': blender, 'public_reference': reference}
        S.save(stage / 'host-request.json', request); request_sha = S.digest((stage / 'host-request.json').read_bytes())
        pythonw = str(S.safe(sys.executable).with_name('pythonw.exe'))
        command = [pythonw, str(S.WRAPPER), '--receipt', str(stage / 'private-receipt.json'), '--timeout', '150',
                   '--memory-limit-mib', '4096', '--', blender, '--background', '--factory-startup', '--offline-mode',
                   '--disable-autoexec', '--python-exit-code', '1', '--python', str(S.HERE / 'diagnostic_host.py'), '--',
                   '--request', str(stage / 'host-request.json'), '--request-sha256', request_sha]
        recheck(); process, stdout = invoke(stage, command, env)
        S.need(receipt_ok(S.read_json(stage / 'private-receipt.json', 64 * 1024)), 'Physical private placement/closure failed')
        public = S.read_json(stage / 'PUBLIC_RESOURCES.json', 64 * 1024)
        sidecar = S.read_json(stage / 'PUBLIC_PLACEMENT.json', 64 * 1024)
        S.need(public['format'] == 'has_session_B_resource_diagnostic_summary_1' and public['profile'] == S.PROFILE
               and public['status'] == 'METADATA_COLLECTED_ROOT_CLOSURE_PENDING'
               and typed_equal(public['claims'], {key: False for key in S.QUALIFICATIONS}), 'Separate diagnostic summary required')
        S.need(sidecar['format'] == 'has_session_B_resource_diagnostic_placement_1' and sidecar['request_sha256'] == request_sha
               and sidecar['public_sha256'] == S.digest((stage / 'PUBLIC_RESOURCES.json').read_bytes())
               and sidecar['private_sha256'] == S.digest((stage / 'PRIVATE_RESOURCES.json').read_bytes()), 'Placement/output binding changed')
        S.need(all(typed_equal(sidecar['placement'].get(k), v) for k, v in PLACEMENT.items()), 'Hidden sentinel cleanup/policy failed')
        for marker, expected in (('HAS_B_RESOURCE_DIAGNOSTIC ', public), ('HAS_B_RESOURCE_PLACEMENT ', sidecar)):
            lines = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
            S.need(len(lines) == 1 and typed_equal(json.loads(lines[0]), expected), 'Exact host marker required')
        S.need((stage / 'PRIVATE_RESOURCES.json').stat().st_size == public['survey']['private_metadata_bytes']
               and sidecar['private_sha256'] == public['survey']['private_metadata_sha256'], 'Private collector payload binding changed')
        complete = True
    except BaseException as error:
        error_type = type(error).__name__; (stage / 'PRIVATE_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        try: recheck(); preserved = True
        except BaseException as error:
            error_type = error_type or type(error).__name__; (stage / 'PRIVATE_PRESERVATION_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
        try: after = closure(stage, 'after')
        except BaseException as error:
            error_type = error_type or type(error).__name__; (stage / 'PRIVATE_CLOSURE_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    record = {'format': 'has_root_session_B_resource_diagnostic_execution_1', 'profile': S.PROFILE,
              'diagnostic_completed': complete and preserved and before.get('owned_count') == after.get('owned_count') == 0,
              'input_source_tool_context_preserved': preserved, 'root_fresh_scopes_closed': after.get('owned_count') == 0,
              'process': process, 'resource_status': public.get('survey', {}).get('status'),
              'export_branch': public.get('export_branch'), 'claims': {key: False for key in S.QUALIFICATIONS},
              'admission_sha256': args.admission_sha256, 'packet_sha256': args.packet_index_sha256, 'error_type': error_type}
    S.save(stage / 'ROOT_RESULT.json', record); print(json.dumps(record, sort_keys=True))
    return 0 if record['diagnostic_completed'] else 1


if __name__ == '__main__': raise SystemExit(main())
