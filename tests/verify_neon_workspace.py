"""Sequential actual Windows neon regressions; explicit graphics lease attestation required.

Source-only integration draft until staged/reviewed by the root. The four standard
test aliases are independent of the focused experiment receipts. No host inventory
is inferred here: --lease-confirmed attests the caller already owns the lease;
actual graphical job/desktop closure is checked from physical launcher receipts.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ('inset', 'tests/neon_inset_scene_regression.gd', True, 12384, 90),
    ('behavior', 'tests/neon_behavior_regression.gd', False, 32, 150),
    ('compact', 'tests/neon_compact_timeline_reveal_smoke.gd', False, 14, 150),
    ('rail', 'tests/neon_rail_placement_smoke.gd', False, 45, 150),
)
MARKERS = {'inset': 'INSET_SCENE_REGRESSION ', 'compact': 'COMPACT_TIMELINE_REVEAL ',
           'rail': 'NEON_RAIL_PLACEMENT '}
BAD_LOG = ('SCRIPT ERROR', 'SHADER ERROR', 'ERROR:', 'FAIL ', 'ObjectDB instances leaked',
           'Shader compilation failed', '_set_transient_exclusive_child')
FUNCTIONAL_DIRS = ('src', 'tests', 'tools', 'data', 'examples')
FUNCTIONAL_FILES = ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(body): return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def snapshot(root):
    paths = []
    for part in FUNCTIONAL_DIRS:
        require((root/part).is_dir(), 'Missing functional directory: '+part)
        for directory, names, files in os.walk(root/part, followlinks=False):
            names[:] = [name for name in names if name != '__pycache__']
            for name in [*names, *files]:
                item = Path(directory)/name
                require(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0)&0x400,
                        'Functional reparse path refused')
            paths.extend(Path(directory)/name for name in files if not name.endswith('.pyc'))
    paths.extend(root/name for name in FUNCTIONAL_FILES)
    result = {}
    for path in sorted(paths):
        require(path.is_file(), 'Missing functional file: '+str(path))
        before = path.stat()
        body = path.read_bytes()
        after = path.stat()
        require((before.st_size, before.st_mtime_ns)==(after.st_size, after.st_mtime_ns), 'Functional file changed while hashing')
        result[path.relative_to(root).as_posix()] = {'sha256':sha(body), 'bytes':len(body), 'mtime_ns':after.st_mtime_ns}
    return result


def owned_fresh(root, path):
    path = Path(path)
    require(path.is_absolute(), 'Absolute owned output required')
    resolved = path.resolve()
    output = (root/'output').resolve()
    require(resolved.is_relative_to(output) and resolved != output and not path.exists(), 'Fresh owned output required')
    for parent in (path, *path.parents):
        if parent.exists():
            require(not parent.is_symlink() and not getattr(parent.lstat(), 'st_file_attributes', 0)&0x400,
                    'Output reparse path refused')
    return resolved


def behavior_job(root, folder, script, app_sha, lease_confirmed, now=None):
    require(lease_confirmed is True, 'Explicit private graphics lease confirmation required')
    folder = owned_fresh(root, folder)
    now = time.time() if now is None else now
    require(type(now) in (int,float) and math.isfinite(now), 'Finite job time required')
    require(re.fullmatch('[a-f0-9]{64}', app_sha) is not None, 'Exact current app SHA required')
    return {'format':'has_neon_behavior_regression_job_1', 'phase':'ROOT_APPROVED_NEON_BEHAVIOR',
            'root_closed_all':True, 'root_closure_is_explicit_caller_attestation':True,
            'folder':folder.as_posix(), 'created_unix':now, 'expires_unix':now+180,
            'script_sha256':sha(script.read_bytes()), 'app_sha256':app_sha}


def bounded_command(command_factory, script, headless, extra, root, seconds):
    args = [str(value) for value in command_factory(script, headless=headless, extra=extra)]
    if headless:
        require('--headless' in args and '--receipt' not in args, 'Headless command differs')
        return args, None
    require(args.count('--receipt')==1 and '--' in args, 'Actual private-desktop command required')
    receipt = owned_fresh(root, Path(args[args.index('--receipt')+1]))
    require(receipt.parent==(root/'output/private-desktop').resolve(), 'Wrong private receipt directory')
    boundary = args.index('--')
    require('--timeout' not in args[:boundary] and '--memory-limit-mib' not in args[:boundary], 'Duplicate wrapper limits')
    args[boundary:boundary] = ['--timeout',str(seconds),'--memory-limit-mib','4096']
    return args, receipt


def execute(args, root, folder, label, timeout):
    require(not (folder/(label+'-process.json')).exists(), 'Preserve process attempt')
    write_json(folder/(label+'-command.json'), args)
    start = time.monotonic()
    process = subprocess.Popen(args, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding='utf-8', errors='replace',
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate(timeout=15)
    log = stdout+stderr
    (folder/(label+'.log')).write_text(log, encoding='utf-8')
    record = {'pid':process.pid, 'exit':process.returncode, 'reaped':process.poll() is not None,
              'timed_out':timed_out, 'seconds':time.monotonic()-start}
    write_json(folder/(label+'-process.json'), record)
    require(not timed_out and record['reaped'] and record['exit']==0, 'Owned process failed; inspect '+label+'.log')
    require(not any(word in log for word in BAD_LOG), 'Engine diagnostics failed; inspect '+label+'.log')
    return log, record


def physical_receipt(path, started_ns):
    require(path.is_file() and path.stat().st_mtime_ns>=started_ns, 'Fresh physical receipt required')
    body = path.read_bytes()
    value = json.loads(body)
    require(value.get('format')=='studio_private_desktop_1' and type(value.get('exit')) is int and value['exit']==0,
            'Private process did not exit successfully')
    for name in ('child_desktop_confirmed','job_closed','desktop_closed'):
        require(value.get(name) is True, 'Private closure missing: '+name)
    for name in ('foreground_child_observed','desktop_switch_requested'):
        require(value.get(name) is False, 'Private desktop became visible or activation was requested')
    require(type(value.get('child_pid')) is int and value['child_pid']>0, 'Private child identity missing')
    require(not any(name in value for name in ('error','monitor_error','desktop_enumeration_error','cancelled')),
            'Private monitor, cancellation or cleanup failure')
    return value, sha(body)


def validate_report(name, report, log, script_sha=None, app_sha=None, expected_names=None):
    expected = dict((row[0],row[3]) for row in CASES)[name]
    require(type(report.get('checks')) is int and report['checks']==expected and
            type(report.get('failures')) is int and report['failures']==0, 'Incomplete or failed '+name+' assertion set')
    require(not any(word in log for word in BAD_LOG), 'Failure diagnostics in '+name)
    if name in MARKERS:
        lines = [line[len(MARKERS[name]):] for line in log.splitlines() if line.startswith(MARKERS[name])]
        require(len(lines)==1 and json.loads(lines[0])==report, 'Actual marker/result mismatch: '+name)
    if name=='behavior':
        require(report.get('format')=='has_neon_behavior_regression_result_1' and report.get('expected_checks')==32 and
                report.get('complete_assertion_set') is True and report.get('script_sha256')==script_sha and
                report.get('app_sha256')==app_sha, 'Behavior result not bound to this script/app')
        named = report.get('named_checks')
        require(type(named) is dict and len(named)==32 and set(named)==set(expected_names or ()) and
                all(value is True for value in named.values()), 'Behavior named predicates incomplete')
        passes = [line[len('PASS neon_behavior.'):] for line in log.splitlines() if line.startswith('PASS neon_behavior.')]
        require(len(passes)==32 and len(set(passes))==32 and set(passes)==set(named), 'Behavior log omitted or duplicated a predicate')
        require(report.get('synthetic_included_assets_only') is True and report.get('save_and_fullscreen_actions_instrumented') is True and
                report.get('refresh_preserved_faded_context') is True,
                'Behavior fixture/action scope differs')
    elif name=='inset':
        require(report.get('status')=='PASS' and type(report.get('configurations')) is int and report['configurations']==576 and
                report.get('native_assets_used') is False, 'Inset configuration/fixture scope differs')
        for key, limit in (('maximum_projection_error_pixels',.01),('maximum_ray_error',.000003)):
            value = report.get(key)
            require(type(value) in (int,float) and math.isfinite(value) and 0<=value<limit, 'Inset projection/ray bound failed')
    elif name=='compact':
        require(report.get('native_owner_assets_used') is False and report.get('compact_timeline_preserved') is True,
                'Compact fixture/layout scope differs')
        samples = report.get('samples')
        require(type(samples) is list and [row.get('row') for row in samples]==[0,32,63], 'Compact row coverage differs')
        for row in samples:
            require(row.get('visible_before_route') is True and row.get('selected_after_route') is True,
                    'Compact real input/reveal failed')
            height = row.get('viewport_height')
            require(type(height) in (int,float) and math.isfinite(height) and 26<=height<115, 'Compact viewport grew past negative-case premise')
    elif name=='rail':
        require(report.get('format')=='has_neon_rail_placement_regression_1' and
                report.get('synthetic_fixture_only') is True and report.get('screenshots_written') is False,
                'Rail fixture/output scope differs')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lease-confirmed',action='store_true')
    parser.add_argument('--parse-scripts',action='store_true',help='Headless --check-only on every alias before execution')
    parser.add_argument('--parse-only',action='store_true',help='Parse every alias only; does not produce a passing workspace suite report')
    options = parser.parse_args(argv)
    require(options.parse_only or options.lease_confirmed, '--lease-confirmed required before private graphics')
    require(options.parse_only or os.name=='nt', 'Actual private workspace suite requires Windows')
    sys.path.insert(0,str(ROOT))
    from run import command
    for _,name,_,_,_ in CASES: require((ROOT/name).is_file(), 'Standard test alias missing: '+name)
    folder = ROOT/'output/neon-workspace'/(str(time.time_ns())+'-'+uuid.uuid4().hex[:8])
    owned_fresh(ROOT,folder)
    folder.mkdir(parents=True,exist_ok=False)
    before = snapshot(ROOT)
    write_json(folder/'source-before.json',before)
    reports = {}
    parses = {}
    error = None
    try:
        if options.parse_scripts or options.parse_only:
            for name,script,_,_,_ in CASES:
                args,_ = bounded_command(command,script,True,['--check-only','--log-file',str(folder/(name+'-parse-engine.log'))],ROOT,60)
                _,record = execute(args,ROOT,folder,name+'-parse',75)
                parses[name] = record
        if not options.parse_only:
            for name,script,headless,_,seconds in CASES:
                source = ROOT/script
                script_sha = sha(source.read_bytes())
                app_sha = before['src/app.gd']['sha256']
                result_path = folder/'inset.json' if headless else folder/name/'result.json'
                require(not result_path.exists(), 'Preserve earlier result')
                expected_names = None
                if name=='behavior':
                    expected_names = re.findall(r'check\("([A-Za-z0-9_]+)"\s*,',source.read_text(encoding='utf-8'))
                    require(len(expected_names)==len(set(expected_names))==32, 'Behavior source assertion set differs')
                    job = behavior_job(ROOT,folder/name,source,app_sha,options.lease_confirmed)
                    job_path = folder/'behavior-job.json'
                    write_json(job_path,job)
                    extra_args = [str(job_path)]
                else:
                    extra_args = [str(result_path if headless else folder/name)]
                extra = ['--log-file',str(folder/(name+'-engine.log')),'--',*extra_args]
                args,receipt_path = bounded_command(command,script,headless,extra,ROOT,seconds)
                started_ns = time.time_ns()
                log,process = execute(args,ROOT,folder,name,seconds+20)
                require(result_path.is_file() and result_path.stat().st_mtime_ns>=started_ns, 'Fresh result missing: '+name)
                report = json.loads(result_path.read_bytes())
                validate_report(name,report,log,script_sha,app_sha,expected_names)
                row = {'result':report,'process':process,'result_path':str(result_path),'result_sha256':sha(result_path.read_bytes()),
                       'script_sha256':script_sha,'headless':headless}
                if receipt_path is not None:
                    receipt,digest = physical_receipt(receipt_path,started_ns)
                    row.update(private_receipt=receipt,private_receipt_path=str(receipt_path),private_receipt_sha256=digest)
                reports[name] = row
    except BaseException as failure:
        error = {'type':type(failure).__name__,'message':str(failure)}
        raise
    finally:
        after = snapshot(ROOT)
        write_json(folder/'source-after.json',after)
        unchanged = before==after
        write_json(folder/'attempt.json',{'format':'has_neon_workspace_attempt_1','folder':str(folder),
                    'error':error,'completed_cases':list(reports),'completed_parses':list(parses),
                    'all_functional_sources_hash_size_mtime_unchanged':unchanged,
                    'authoritative_host_inventory_performed':False})
        require(unchanged,'Functional source membership/hash/size/mtime changed')
    if options.parse_only:
        value = {'format':'has_neon_workspace_parse_only_1','folder':str(folder),'parses':parses,
                 'functional_sources_unchanged':True,'product_suite_executed':False}
        write_json(folder/'parse-only.json',value)
        print(json.dumps(value,indent=2));return 0
    require(set(reports)=={'inset','behavior','compact','rail'}, 'Incomplete workspace suite')
    value = {'format':'has_neon_workspace_verification_1','passed':True,'folder':str(folder),
             'reports':reports,'parses':parses,'checks':sum(row[3] for row in CASES),'failures':0,
             'expected_checks':{row[0]:row[3] for row in CASES},'functional_source_count':len(before),
             'all_functional_sources_hash_size_mtime_unchanged':True,'graphics_lease_attested_by_caller':True,
             'all_private_jobs_and_desktops_closed':True,'authoritative_host_inventory_performed':False,
             'source_before':{'path':str(folder/'source-before.json'),'sha256':sha((folder/'source-before.json').read_bytes())},
             'source_after':{'path':str(folder/'source-after.json'),'sha256':sha((folder/'source-after.json').read_bytes())}}
    write_json(folder/'verification.json',value)
    # Standard suite entry point; written only after all four actual results and physical closure gates pass.
    target = ROOT/'output/neon-workspace-verification.json'
    temporary = target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
    write_json(temporary,value)
    os.replace(temporary,target)
    print(json.dumps(value,indent=2));return 0


if __name__=='__main__': raise SystemExit(main())
