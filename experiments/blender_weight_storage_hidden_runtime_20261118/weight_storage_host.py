"""UNRUN additive hidden-placement host around the unchanged synthetic probe.

The probe itself makes no window call. This host owns one approved hidden HWND
for placement only, and records its policy after the helper's finally cleanup.
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORKSPACE_OUTPUT = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output')
HELPER_SHA = 'e42fa44efa599851396c517fa0b4bc90a692efb1f911517fa3d748879d1462c2'
HOST_NAMES = {'weight_storage_host.py', 'placement_sentinel.py'}
PROBE_SCRIPTS = {
    'blender_weight_storage_probe.py': {'bytes': 12938, 'sha256': 'd7f75e11bd8a90d0f652f67ae92843629e5126b965c5e7c4262ab97d901bac95'},
    'weight_storage_contract.py': {'bytes': 11972, 'sha256': 'f71753e3b7183c5fab343bf8af504cd5613879bd95b89d5f338f54123180db18'}}
HOLD_SECONDS = 0.5
PLACEMENT = {'format': 'has_hidden_background_desktop_placement_sentinel_1',
             'purpose': 'Owned background-process desktop placement only; no Blender GUI or render assertion.',
             'class': 'STATIC', 'requested_size_pixels': [0, 0], 'disabled': True,
             'noactivate_style': True, 'toolwindow_style': True, 'visible_at_creation': False,
             'visible_before_destruction': False, 'owned_pid_and_thread_verified': True,
             'destroyed_in_finally': True, 'show_or_activation_calls': False,
             'thread_desktop_switch_calls': False}


def need(ok, message):
    if not ok: raise ValueError(message)


def same(a, b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def safe(path):
    value = Path(path); need(value.is_absolute(), 'Absolute owned path required')
    for item in (value, *value.parents):
        need(not item.is_symlink() and not (os.path.lexists(item) and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400), 'Reparse path refused')
    return value.resolve()


def read(path, maximum):
    value = safe(path); before = value.stat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= maximum, 'Bounded stable single-link file required')
    raw = value.read_bytes(); after = value.stat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
    need(fields(before) == fields(after) and len(raw) == before.st_size, 'Owned file changed while reading')
    return raw, fields(before)


def unique(rows):
    value = {}
    for k, v in rows:
        need(k not in value, 'Duplicate request key'); value[k] = v
    return value


def document(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def digest(raw): return hashlib.sha256(raw).hexdigest()


def verify_probe_sources(source, plan):
    need({p.name for p in source.iterdir()} == set(PROBE_SCRIPTS)
         and same(plan.get('scripts'), PROBE_SCRIPTS), 'Exact unchanged probe source closure/identities required')
    for name, expected in PROBE_SCRIPTS.items():
        body, _ = read(source / name, 256 * 1024)
        need(len(body) == expected['bytes'] and digest(body) == expected['sha256'], 'Unchanged source differs')


def post_probe_context(source, plan, now=None):
    """Postcondition permits the completed report; fresh-output preflight cannot."""
    verify_probe_sources(source, plan)
    expiry = datetime.fromisoformat(plan['expires_utc'])
    now = now or datetime.now(timezone.utc)
    need(expiry.tzinfo is not None and expiry.utcoffset() == timedelta(0)
         and now < expiry <= now + timedelta(minutes=15), 'Unchanged probe request expired')
    need(all(safe(os.environ.get(key, '')) == safe(plan['owned_temp']) for key in ('TEMP', 'TMP')),
         'Owned temporary environment changed')


def load_request(path, expected_sha):
    need(type(expected_sha) is str and re.fullmatch('[0-9a-f]{64}', expected_sha), 'Root host-request SHA required')
    raw, identity = read(path, 32 * 1024); need(digest(raw) == expected_sha, 'Host request differs')
    value = document(raw)
    fields = {'format', 'run_id', 'stage', 'plan', 'plan_sha256', 'runtime_packet_sha256', 'host_sources'}
    need(type(value) is dict and set(value) == fields and value['format'] == 'has_owned_hidden_weight_host_request_1', 'Exact owned host request required')
    need(type(value['run_id']) is str and re.fullmatch('[0-9a-f]{32}', value['run_id']), 'Fresh host run ID required')
    stage = safe(value['stage'])
    need(stage.parent == safe(WORKSPACE_OUTPUT) and stage.name == 'weight-storage-probe-20261118-' + value['run_id']
         and HERE == stage / 'host' and safe(path) == stage / 'host-request.json', 'Exact separate owned host stage required')
    need(safe(value['plan']) == stage / 'request.json' and re.fullmatch('[0-9a-f]{64}', value['plan_sha256'])
         and re.fullmatch('[0-9a-f]{64}', value['runtime_packet_sha256']), 'Exact plan/runtime binding required')
    need({p.name for p in HERE.iterdir()} == HOST_NAMES and type(value['host_sources']) is dict
         and set(value['host_sources']) == HOST_NAMES, 'Exact host/helper directory closure required')
    for name, row in value['host_sources'].items():
        need(type(row) is dict and set(row) == {'bytes', 'sha256'} and type(row['bytes']) is int
             and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'Exact host-source identity required')
        body, _ = read(HERE / name, 256 * 1024)
        need(len(body) == row['bytes'] and digest(body) == row['sha256'], 'Owned host/helper source differs')
    need(value['host_sources']['placement_sentinel.py']['sha256'] == HELPER_SHA, 'Approved helper must remain byte-exact')
    plan_raw, plan_identity = read(stage / 'request.json', 32 * 1024)
    need(digest(plan_raw) == value['plan_sha256'], 'Unchanged probe plan differs')
    return value, identity, plan_identity


def run_with_placement(probe_main, sentinel_factory, plan_path, sleeper=time.sleep):
    """Pure orchestration API for CPU fakes; production uses exact approved helper."""
    previous = sys.argv[:]; policy = None; code = None; error_type = None
    try:
        with sentinel_factory() as placement:
            policy = placement
            # Bounded placement synchronization, never a performance measurement.
            sleeper(HOLD_SECONDS)
            sys.argv = [previous[0], '--', '--plan', str(plan_path)]
            try:
                code = probe_main()
                need(type(code) is int and code in (0, 1), 'Unchanged probe return code differs')
            except BaseException as error:
                error_type = type(error).__name__
            finally:
                sleeper(HOLD_SECONDS)
    except BaseException as error:
        error_type = error_type or type(error).__name__
    finally:
        sys.argv = previous
    return {'probe_return_code': code, 'placement': policy, 'error_type': error_type,
            'placement_complete': error_type is None and same(policy, PLACEMENT)}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-request', required=True); parser.add_argument('--host-request-sha256', required=True)
    args = parser.parse_args(argv if argv is not None else sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    request, request_identity, plan_identity = load_request(args.host_request, args.host_request_sha256)
    stage = safe(request['stage']); source = stage / 'source'
    plan_raw, _ = read(request['plan'], 32 * 1024)
    verify_probe_sources(source, document(plan_raw))
    need('weight_storage_contract' not in sys.modules, 'Unexpected preloaded probe contract refused')
    sys.path.insert(0, str(source))
    probe = module('owned_unchanged_weight_storage_probe', source / 'blender_weight_storage_probe.py')
    plan, plan_sha = probe.read_plan(request['plan'])
    need(plan_sha == request['plan_sha256'] and plan['run_id'] == request['run_id'], 'Host/probe plan identity differs')
    import bpy
    need(bpy.app.background is True and bpy.app.online_access is False and not bpy.data.filepath
         and bpy.context.preferences.filepaths.use_scripts_auto_execute is False
         and list(bpy.app.version) == [5, 1, 2], 'Factory background/offline/disabled-autoexec Blender5.1.2 required before window creation')
    helper = module('owned_approved_weight_placement', HERE / 'placement_sentinel.py')
    outcome = run_with_placement(probe.main, helper._hidden_placement_sentinel, request['plan'])
    report_sha = None
    try:
        checked = load_request(args.host_request, args.host_request_sha256)
        need(checked == (request, request_identity, plan_identity), 'Owned host/plan/source context changed')
        post_probe_context(source, plan)  # Completed output must exist now; never rerun fresh-output preflight.
        report_raw, _ = read(stage / 'PUBLIC_WEIGHT_STORAGE.json', 512 * 1024); report_sha = digest(report_raw)
    except BaseException as error:
        outcome['error_type'] = outcome['error_type'] or type(error).__name__
        outcome['placement_complete'] = False
    sidecar = {'format': 'has_hidden_weight_probe_host_placement_1',
               'status': 'HIDDEN_PLACEMENT_COMPLETE' if outcome['placement_complete'] else 'HOST_PLACEMENT_FAILED',
               'run_id': request['run_id'], 'request_sha256': request['plan_sha256'],
               'host_request_sha256': args.host_request_sha256, 'runtime_packet_sha256': request['runtime_packet_sha256'],
               'host_source_identities': request['host_sources'], 'public_probe_sha256': report_sha,
               'probe_return_code': outcome['probe_return_code'], 'placement': outcome['placement'], 'error_type': outcome['error_type'],
               'placement_sync_hold_seconds_before': HOLD_SECONDS, 'placement_sync_hold_seconds_after': HOLD_SECONDS,
               'host_window_API_scope': 'Exact approved hidden placement helper only; no shown/activated window or desktop switch.',
               'unchanged_probe_window_or_desktop_API_called': False,
               'native_storage_rule_qualified': False, 'native_fidelity_export_repair_adoption_qualified': False}
    target = stage / 'PUBLIC_HOST_PLACEMENT.json'
    need(safe(target).parent == safe(stage) and not os.path.lexists(target), 'Fresh exact owned placement sidecar required')
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(sidecar, stream, indent=2, allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print('HAS_SYNTHETIC_WEIGHT_HOST_PLACEMENT ' + json.dumps(sidecar, sort_keys=True))
    return 0 if outcome['placement_complete'] and outcome['probe_return_code'] == 0 else 1


if __name__ == '__main__': raise SystemExit(main())
