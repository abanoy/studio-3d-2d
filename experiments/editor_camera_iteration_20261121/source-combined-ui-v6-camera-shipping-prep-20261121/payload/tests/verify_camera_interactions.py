"""Current-checkout camera interaction regressions; no historical Full dependency."""
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
from run import command, configure_private_display


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_mode, info.st_nlink, getattr(info, 'st_file_attributes', 0))


def source_inputs():
    paths = [ROOT/name for name in ('run.py', 'project.godot', 'main.tscn', 'dependencies.json')]
    for prefix in ('src', 'tests', 'tools', 'data', 'examples'):
        for folder, dirs, files in os.walk(ROOT/prefix, followlinks=False):
            for name in dirs:
                info = (Path(folder)/name).lstat()
                need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0)&0x400,
                     'Source directory alias refused')
            dirs[:] = [name for name in dirs if name not in ('.godot', '.git', '__pycache__')]
            paths.extend(Path(folder)/name for name in files if not name.endswith(('.pyc', '.pyo')))
    frozen = {}
    for path in paths:
        before = path.lstat()
        need(stat.S_ISREG(before.st_mode) and not getattr(before, 'st_file_attributes', 0)&0x400,
             'Source must be a regular file')
        raw = path.read_bytes()
        need(identity(before) == identity(path.lstat()), 'Source changed while admitted')
        frozen[path] = (identity(before), hashlib.sha256(raw).hexdigest())
    return frozen


def sources_unchanged(frozen):
    failures = []
    for path, (stamp, digest) in frozen.items():
        try:
            if identity(path.lstat()) != stamp or hashlib.sha256(path.read_bytes()).hexdigest() != digest or identity(path.lstat()) != stamp:
                failures.append(str(path.relative_to(ROOT)))
        except OSError:
            failures.append(str(path.relative_to(ROOT)))
    return failures


def run_case(folder, name, script, marker, count, extra, *, headless, timeout):
    case = folder/name
    case.mkdir()
    user = case/'user'
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if os.name == 'nt':
        for variable, leaf in (('APPDATA', 'Roaming'), ('LOCALAPPDATA', 'Local'), ('TEMP', 'Temp'), ('TMP', 'Temp')):
            target = user/leaf
            target.mkdir(parents=True, exist_ok=True)
            env[variable] = str(target)
    engine_log = case/'engine.log'
    args = command(script, headless=headless,
                   extra=['--audio-driver', 'Dummy', '--log-file', str(engine_log), '--', str(case), *extra])
    if os.name == 'nt' and not headless:
        need('--receipt' in args, 'Windows app checks require run.command private desktop')
        args[2:2] = ['--timeout', str(timeout), '--memory-limit-mib', '4096']
    completed = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                               timeout=timeout+35,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    raw = completed.stdout+completed.stderr
    (case/'process.log').write_bytes(raw)
    proof = None
    if os.name == 'nt' and not headless:
        receipt = Path(args[args.index('--receipt')+1])
        proof = json.loads(receipt.read_bytes())
        need(proof.get('format') == 'studio_private_desktop_1'
             and type(proof.get('exit')) is int
             and proof.get('exit') == completed.returncode
             and proof.get('child_desktop_confirmed') is True
             and proof.get('private_window_seen') is True
             and proof.get('foreground_child_observed') is False
             and proof.get('desktop_switch_requested') is False
             and proof.get('job_closed') is True and proof.get('desktop_closed') is True,
             'Private process/window/closure proof failed')
    log = raw.decode('utf-8', 'replace')
    engine = engine_log.read_text(encoding='utf-8', errors='replace')
    bad = ('ERROR:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ', 'ObjectDB instances leaked', '_set_transient_exclusive_child')
    need(completed.returncode == 0 and not any(text in log or text in engine for text in bad),
         'Camera case failed: '+name+'; see '+str(case))
    lines = [line[len(marker):] for line in log.splitlines() if line.startswith(marker)]
    need(len(lines) == 1, 'Expected one exact camera result marker')
    report = json.loads(lines[0])
    need(type(report.get('checks')) is int and report['checks'] == count
         and type(report.get('failures')) is int and report['failures'] == 0
         and sum(line.startswith('PASS ') for line in log.splitlines()) == count,
         'Camera assertion count or failure mismatch')
    if name.startswith('timeline-'):
        need(report.get('controlled_focus_loss_notification') is True,
             'Controlled focus-loss scope marker required')
        image = (case/'camera-timeline.png').read_bytes()
        need(len(image) >= 24 and image[:8] == b'\x89PNG\r\n\x1a\n'
             and int.from_bytes(image[16:20], 'big') > 0 and int.from_bytes(image[20:24], 'big') > 0,
             'Timeline screenshot missing or invalid')
    return {'name': name, 'checks': count, 'report': report,
            'private_receipt': str(receipt) if proof is not None else None,
            'private_resources_closed': proof is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=('pure', 'variant', 'all'), default='all')
    parser.add_argument('--theme', choices=('classic', 'neon'), default='neon')
    parser.add_argument('--scale', type=int, choices=(100, 150), default=100)
    parser.add_argument('--workspace', choices=('simple', 'advanced'), default='simple')
    parser.add_argument('--isolated-display')
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if os.name != 'nt' and options.scope != 'pure':
        if sys.platform != 'linux' or not options.isolated_display:
            parser.error('Graphical cases require an explicitly provisioned private --isolated-display; no shared fallback')
        configure_private_display(options.isolated_display)
    folder = (options.output or ROOT/'output/camera-interactions'/str(time.time_ns())).resolve()
    need(folder.is_relative_to((ROOT/'output').resolve()) and not folder.exists(), 'Choose a new directory inside output')
    for parent in folder.parents:
        if parent.exists():
            info = parent.lstat()
            need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0)&0x400,
                 'Output alias refused')
    folder.mkdir(parents=True, exist_ok=False)
    frozen = source_inputs()
    result = {'format': 'has_current_camera_interaction_verification_1', 'status': 'FAIL',
              'scope': options.scope, 'cases': [], 'whole_full_claimed': False,
              'owner_assets_read': False, 'sourceio_or_conversion_requested': False}
    primary = None
    try:
        if options.scope in ('pure', 'all'):
            for name, script, marker, count in (
                ('cold-wire', 'tests/camera_cold_wire_unit.gd', 'CAMERA_COLD_WIRE_UNIT ', 29),
                ('key-edits', 'tests/camera_key_edits_unit.gd', 'CAMERA_KEY_EDITS_UNIT ', 26),
                ('lens-plan', 'tests/camera_lens_gesture_unit.gd', 'CAMERA_LENS_GESTURE_UNIT ', 12)):
                result['cases'].append(run_case(folder, name, script, marker, count, [], headless=True, timeout=30))
        variants = [(options.theme, options.scale, options.workspace)] if options.scope == 'variant' else [
            (theme, scale, workspace) for theme in ('classic', 'neon') for scale in (100, 150)
            for workspace in ('simple', 'advanced')] if options.scope == 'all' else []
        for theme, scale, workspace in variants:
            label = theme+'-'+str(scale)+'-'+workspace
            flags = (['--classic'] if theme == 'classic' else [])+(['--150'] if scale == 150 else [])+(['--advanced'] if workspace == 'advanced' else [])
            for name, script, marker, count, timeout in (
                ('timeline-', 'tests/camera_timeline_ux_smoke.gd', 'CAMERA_TIMELINE_UX_SMOKE ', 34, 175),
                ('lens-', 'tests/camera_lens_gesture_smoke.gd', 'CAMERA_LENS_GESTURE_SMOKE ', 22, 165)):
                result['cases'].append(run_case(folder, name+label, script, marker, count, flags, headless=False, timeout=timeout))
        expected = {'pure': 67, 'variant': 56, 'all': 515}[options.scope]
        result['checks'] = sum(row['checks'] for row in result['cases'])
        need(result['checks'] == expected, 'All requested camera checks must complete')
        result['status'] = 'PASS'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error'] = str(error)
    finally:
        result['source_preservation_failures'] = sources_unchanged(frozen)
        result['all_admitted_sources_unchanged'] = not result['source_preservation_failures']
        if not result['all_admitted_sources_unchanged']:
            result['status'] = 'FAIL'
        (folder/'verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'status': result['status'], 'checks': result.get('checks'),
                          'scope': options.scope, 'result': str(folder/'verification.json')}))
    if primary is not None:
        raise primary
    need(result['status'] == 'PASS', 'Camera source preservation failed')


if __name__ == '__main__':
    main()
