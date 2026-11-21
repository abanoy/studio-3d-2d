"""Root-only, isolated fresh SourceIO identity probe. Authored preparation, not a result.

No native operation is attempted unless the exact whole-suite result, working
source, committed bytes, immutable runtime lock and a fresh physical observation
all pass. The explicit Root lane attestation is separate from that observation.
Only a new output/source-material-carrier-run-<ns> tree and an owned lock are written.
One selected owned GLB export is attempted only after qualified fresh-model creation.
There is no visible launch fallback, scene save or owner-scene opening.
"""
from pathlib import Path, PurePosixPath
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import ntpath
import os
import re
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[1]
FULL_NAME = 'windows-reference-body-1795197079606290600'
TESTED = '9e3b039039833adce4723bbb70681595cd4eef16'
COUNT = 1061
SOURCEIO = Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
OLD = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111')
FAMILY = Path('output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685')
LOCK_REL = 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
PYTHON = Path(r'C:\Program Files\Python313\python.exe')
PYTHONW = Path(r'C:\Program Files\Python313\pythonw.exe')
BLENDER = Path(r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe')
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_PIN = (301360, '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233')
RUNTIME_PINS = {
    str(PYTHON): (105840, '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'),
    str(PYTHONW): (104304, '2bea4fc941b7d9436afa1be8cb46551c0694deed23b3fec87b969054238be099'),
    str(BLENDER): (108687824, '1e6624af112b3c936f4b038b025ebd2bf00ae72c4b62881a6787166d71c58fa5'),
}
HELPERS = {
    'experiments/source_saved_weight_join_20261120/join_saved_weights.py':
        (20860, 'f838e0d893969aa1ad884a1c1d92e28ba019454f313632855f2a33c55fc3415c'),
    'experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py':
        (27615, 'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d'),
    'experiments/normal_setter_boundary_sentinel_20261117/instrumentation.py':
        (3306, '361fcad3dbff79bfd5367cd71ac5a769fc8155d6f38a1b061d5ce6e631f5a895'),
    'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py':
        (17989, '034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3'),
}
# Literal policy.PINS subset. Native3 and a byte-identical owned B library enter
# child staging. The original GLB stays Root-only for post-closure semantic
# comparison; parameters remain hash-only Root provenance.
NATIVE = {
    'mdl': ('native/junko hair.mdl', 37644, '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
    'vvd': ('native/junko hair.vvd', 618368, '2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
    'vtx': ('native/junko hair.dx90.vtx', 173309, '924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'),
}
PROVENANCE = {
    'blend': ('editable.blend', 2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6'),
    'glb': ('scene.glb', 2322644, '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'),
    'parameters': ('parameters.json', 159684, 'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'),
}
TREES = ('src', 'tools', 'tests', 'data', 'examples')
FILES = ('project.godot', 'main.tscn', 'run.py', 'launch.pyw', 'dependencies.json',
         'experiments/reference_body_20261120/run_full.py',
         'experiments/reference_body_20261120/stage_legacy_inputs.py',
         'experiments/reference_body_20261120/verify_units.py',
         'experiments/reference_body_20261120/run_scoped.py',
         'experiments/reference_body_20261120/receipt_provenance.py',
         'experiments/reference_body_20261120/test_receipt_provenance.py')
MAX_READ = 256 * 1024 * 1024
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x40000
METADATA_PIN = (13818, 'c04c4e20705b490ed7633855b2e3bdde14350adec35c8b2a25afc42b69508395')
BINDING_PIN = (27946, '0e2b8cae2f376615e6d038c5f888e06aa31f9595345f54863be9a3e3c013afe0')
ENUMERATION_PIN = (18845, '6c3aeff6a56b22a448d3ca093997ca866e76ac6ec2fb3948c811abad9c86f903')
INSPECTION_PIN = (24579, '5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17')
RESOLVED_PIN = (30378, '82359c33b116278fb5f12ad75e49ecdfcda00c7fa2e6d283a5677867438d602f')
NORMAL_GATE_PIN = (9093, '0992c58c53be60712bc14668229959dcfffebf404d4d26db0374abf33ce3288c')
CARRIER_MODULES = {
    'export_hook': ('export_hook_proposal.py', 48895, 'cad4213ed8f55ac060a2f7b2387637a466ef751b36ac26769dbda93e7e343511'),
    'resource_gate': ('resource_gate_proposal.py', 54511, 'f892ade8fc83d198261edd2fbcdd608ef0cb77ba41a3f1cf52b7705de4fdfea7'),
    'shared_cache': ('shared_image_cache_proposal.py', 34089, 'b1c0862c21f5e7f86ca889107c4530b68eb624196a83256333ac379f06712b1e'),
    'extract_observer': ('observer_instrumentation.py', 7829, '15145030fab5b662be490e519ff59f870c4e9c0352766ff59bf3da3f12198f7b'),
    'gather_binder': ('gather_binding.py', 17534, '617c062b516ecefa5fab0a6ec8f98163a3b13f76896969cb22102f859323b850'),
    'semantic_compare': ('semantic_compare.py', 22754, 'c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00'),
    'cold_readiness': ('cold_image_readiness.py', 14496, 'eac159fa9c31f9a0bc600025f27a3e988dd486d1e38497698814f3121399bbd9'),
    'carrier_export': ('carrier_export.py', 33131, '983c9f44d4588decfb0169d5889db09c77b5b3cec7e1b1e280d38166d70fb763'),
}



class Refusal(RuntimeError):
    pass


def need(condition, code):
    if not condition:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def relative(name):
    need(type(name) is str and bool(name), 'RELATIVE_NAME_REQUIRED')
    item = PurePosixPath(name)
    need(item.as_posix() == name and not item.is_absolute() and '\\' not in name and ':' not in name
         and all(part not in ('', '.', '..') for part in item.parts), 'UNSAFE_RELATIVE_NAME')
    return name


def safe(path, exists=True):
    path = Path(path).absolute()
    need('..' not in path.parts, 'DOT_DOT_PATH')
    for item in reversed((path, *path.parents)):
        if not item.exists() and not item.is_symlink():
            need(not exists or item != path, 'MISSING_PATH')
            continue
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'LINK_OR_REPARSE_PATH')
        if stat.S_ISREG(info.st_mode):
            need(info.st_nlink == 1, 'HARDLINK_PATH')
    if exists:
        need(path.exists(), 'MISSING_PATH')
    return path


def raw_stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink,
            getattr(info, 'st_file_attributes', 0))


def stamp(info):
    # Windows directory-enumeration metadata can carry RECALL_ON_OPEN while
    # fstat/final lstat omit that hint for the same pinned file. Normalize only
    # 0x40000; raw_stamp remains available for diagnostics. Reparse admission
    # above uses raw 0x400, and every other attribute/identity field stays exact.
    # Microsoft also names this bit EA for an internal-use attribute; this is
    # deliberately a comparison policy, not a claim that EA state was verified.
    # https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
    values = raw_stamp(info)
    return (*values[:-1], values[-1] & ~FILE_ATTRIBUTE_RECALL_ON_OPEN)


def read_checked(path, pin=None, limit=MAX_READ):
    path = safe(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, 'FILE_TYPE_OR_SIZE')
    if pin is not None:
        need(len(pin) == 2 and type(pin[0]) is int and 0 <= pin[0] <= limit and
             before.st_size == pin[0] and type(pin[1]) is str and re.fullmatch('[0-9a-f]{64}', pin[1]) is not None,
             'BEFORE_READ_LITERAL_PIN_OR_SIZE_DIFFERS')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        need(stamp(opened) == stamp(before), 'FILE_CHANGED_BEFORE_READ')
        raw = stream.read(before.st_size + 1)
        final_open = os.fstat(stream.fileno())
    after = path.lstat()
    need(all(stamp(info) == stamp(before) for info in (opened, final_open, after)) and
         len(raw) == before.st_size, 'READ_CHANGED_FILE')
    row = dict(bytes=len(raw), mtime_ns=after.st_mtime_ns, sha256=sha(raw))
    if pin is not None:
        need((row['bytes'], row['sha256']) == tuple(pin), 'LITERAL_PIN_DIFFERS')
    return raw, row, stamp(after)


def json_read(path, limit=8 * 1024 * 1024):
    raw, row, _stamp = read_checked(path, limit=limit)
    return strict_json(raw), row


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def invalid(_value):
        raise Refusal('NONFINITE_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def write_new(path, value):
    path = safe(path, exists=False)
    need(not path.exists() and path.parent.is_dir() and path.is_relative_to(ROOT / 'output'), 'FRESH_OUTPUT_BOUNDARY')
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    need(len(raw) <= 8 * 1024 * 1024, 'REPORT_SIZE')
    with path.open('xb') as stream:
        stream.write(raw)
    return dict(path=str(path), bytes=len(raw), sha256=sha(raw))


def source_snapshot(expected=None):
    paths = []
    for tree in TREES:
        for base, dirs, files in os.walk(safe(ROOT / tree), followlinks=False):
            for name in dirs:
                safe(Path(base) / name)
            for name in files:
                path = Path(base) / name
                safe(path)
                if path.suffix != '.pyc' and '__pycache__' not in path.parts:
                    paths.append(path)
    paths += [ROOT / name for name in FILES]
    if expected is not None:
        need({path.relative_to(ROOT).as_posix() for path in paths} == set(expected), 'BEFORE_READ_SOURCE_MEMBERSHIP_DIFFERS')
    result = {}
    for path in sorted(paths):
        name = path.relative_to(ROOT).as_posix()
        pin = None if expected is None else (expected[name]['bytes'], expected[name]['sha256'])
        raw, row, _stamp = read_checked(path, pin)
        row['git_sha1'] = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        result[path.relative_to(ROOT).as_posix()] = row
    return result


def validate_source_rows(rows):
    need(type(rows) is dict and len(rows) == COUNT, 'EXACT_1061_SOURCE_DOMAIN')
    for name, row in rows.items():
        relative(name)
        need(type(row) is dict and set(row) == {'bytes', 'mtime_ns', 'sha256', 'git_sha1'} and
             type(row['bytes']) is int and row['bytes'] >= 0 and type(row['mtime_ns']) is int and row['mtime_ns'] > 0 and
             type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None and
             type(row['git_sha1']) is str and re.fullmatch('[0-9a-f]{40}', row['git_sha1']) is not None,
             'SOURCE_ROW_SCHEMA')


def validate_full(context):
    need(type(context) is dict and context.get('root_lane_confirmed') is True, 'EXPLICIT_ROOT_LANE_REQUIRED')
    value, launch = context['completion'], context['launch']
    need(type(value) is dict and value.get('format') == 'has_reference_body_full_coordinator_1' and
         value.get('revision') == TESTED and type(value.get('exit')) is int and value['exit'] == 0 and
         type(value.get('functional_source_count')) is int and value['functional_source_count'] == COUNT,
         'WHOLE_FRESH_9E_CONTEXT_REQUIRED')
    for key in ('whole_verifier_pass', 'child_reaped', 'functional_sources_unchanged', 'revision_unchanged',
                'fresh_final_report', 'all_private_jobs_isolated_closed', 'nonzero_jobs_are_expected_cancellations',
                'receipt_provenance_verified'):
        need(value.get(key) is True, 'UNQUALIFIED_FULL_' + key.upper())
    need(type(launch) is dict and launch.get('revision') == TESTED and
         all(type(launch.get(key)) is int and launch[key] > 0 for key in ('pid', 'coordinator_pid', 'started_ns')) and
         launch['pid'] != launch['coordinator_pid'], 'FULL_LAUNCH_SCHEMA')
    jobs = value.get('current_jobs')
    need(type(jobs) is list and len(jobs) > 0 and type(value.get('unique_current_private_jobs')) is int and
         value['unique_current_private_jobs'] == len(jobs), 'FULL_ACTUAL_PRIVATE_JOBS_REQUIRED')
    desktops, nonzero = set(), []
    for job in jobs:
        need(type(job) is dict and type(job.get('path')) is str and type(job.get('value')) is dict,
             'FULL_PRIVATE_JOB_ROW')
        row = job['value']
        need(row.get('format') == 'studio_private_desktop_1' and type(row.get('desktop')) is str and
             row['desktop'].startswith('HAS_Test_') and row['desktop'] not in desktops and
             all(row.get(key) is True for key in ('job_closed', 'desktop_closed', 'child_desktop_confirmed')) and
             row.get('foreground_child_observed') is False and row.get('desktop_switch_requested') is False and
             type(row.get('exit')) is int, 'FULL_PRIVATE_JOB_ISOLATION')
        need(not any(key in row for key in ('monitor_error', 'desktop_enumeration_error')) and
             (row['exit'] != 0 or not any(key in row for key in ('error', 'cancelled'))), 'FULL_PRIVATE_JOB_FAILURE')
        desktops.add(row['desktop'])
        if row['exit'] != 0:
            nonzero.append(job)
    need(len(nonzero) == 1 and nonzero[0]['value'].get('exit') == 2 and
         nonzero[0]['value'].get('cancelled') is True and
         nonzero[0]['value'].get('error') == 'Owned converter cancelled' and
         'krita' in nonzero[0]['path'].casefold(), 'FULL_EXPECTED_SINGLE_KRITA_CANCEL')
    validate_source_rows(context['before'])
    need(context['before'] == context['after'], 'FULL_SOURCE_BYTES_OR_NS_STAMPS_CHANGED')
    need(context['committed'] == {name: row['git_sha1'] for name, row in context['before'].items()},
         'TESTED_GIT_BLOB_MEMBERSHIP_DIFFERS')
    return value


def validate_git(proof, context):
    need(type(proof) is dict and type(proof.get('head')) is str and
         re.fullmatch('[0-9a-f]{40}', proof['head']) is not None and proof.get('tested_is_ancestor') is True and
         proof.get('tested_blobs') == context['committed'] and proof.get('head_blobs') == context['committed'],
         'HEAD_LINEAGE_OR_COMMITTED_RAW_BYTES_DIFFER')


def validate_physical(rows, own_pid, launch, *, root=ROOT):
    need(type(rows) is list and len(rows) < 65536 and type(own_pid) is int and own_pid > 0, 'CIM_ROWS_SCHEMA')
    ids = set()
    for row in rows:
        need(type(row) is dict and type(row.get('ProcessId')) is int and row['ProcessId'] >= 0 and
             type(row.get('ParentProcessId')) is int and row['ParentProcessId'] >= 0 and
             type(row.get('Name')) is str and all(row.get(key) is None or type(row.get(key)) is str
                                                for key in ('ExecutablePath', 'CommandLine')),
             'CIM_ROW_SCHEMA')
        need(row['ProcessId'] not in ids, 'CIM_DUPLICATE_PID')
        ids.add(row['ProcessId'])
    forbidden = {launch['pid'], launch['coordinator_pid'], *launch.get('extra_absent_pids', [])}
    # A retained launcher can have exited while a child still has its PID as
    # parent. Include those descendants even if their command text is missing.
    previous = set()
    while previous != forbidden:
        previous = set(forbidden)
        forbidden.update(row['ProcessId'] for row in rows if row['ParentProcessId'] in forbidden)
    need(not forbidden.intersection(ids), 'FULL_CHILD_OR_COORDINATOR_STILL_PRESENT')
    root_text = str(root).casefold().replace('/', '\\')
    root_pattern = re.compile(r'(?<![a-z0-9_\\])' + re.escape(root_text) + r'(?=[\\\s\"\x27]|$)')
    # Check only this primary session's actual native/test commands. Owner Studio
    # and protected old review paths are outside this root. No global lease is
    # inferred: explicit Root attestation remains a separate admission condition.
    blocked = []
    for row in rows:
        if row['ProcessId'] == own_pid:
            continue
        name = row['Name'].casefold()
        runtime = name.startswith(('python', 'godot')) or name in ('blender.exe', 'krita.exe', 'ffmpeg.exe', 'ffprobe.exe')
        command = (row.get('CommandLine') or '').casefold().replace('/', '\\')
        executable = (row.get('ExecutablePath') or '').casefold().replace('/', '\\')
        if runtime and (root_pattern.search(command) is not None or executable.startswith(root_text + '\\')):
            blocked.append(row['ProcessId'])
    need(not blocked, 'PRIMARY_ROOT_NATIVE_OR_TEST_PROCESS_PRESENT')
    return dict(format='has_source_material_binding_physical_closure_1', owned_processes=0, excluded_exact_pid=own_pid,
                full_child_pid=launch['pid'], full_coordinator_pid=launch['coordinator_pid'],
                full_pids_absent=True, private_process_rows_published=False)


def validate_fresh_physical(physical):
    need(type(physical) is dict and physical.get('owned_processes') == 0 and
         type(physical.get('owned_processes')) is int and physical.get('full_pids_absent') is True and
         physical.get('format') == 'has_source_material_binding_physical_closure_1' and
         physical.get('observer_retained_waited_reaped') is True and
         type(physical.get('observer_exit')) is int and physical['observer_exit'] == 0 and
         type(physical.get('excluded_exact_pid')) is int and physical['excluded_exact_pid'] == os.getpid() and
         type(physical.get('observed_ns')) is int and 0 <= time.time_ns() - physical['observed_ns'] <= 60 * 10**9,
         'FRESH_PHYSICAL_CLOSURE_REQUIRED')
    return physical


def admit(context, *, source_reader, git_reader, physical_reader, runtime_reader):
    """Injectable admission; bad full proofs cannot reach any runtime launcher."""
    validate_full(context)
    current = source_reader()
    need(current == context['after'], 'CURRENT_SOURCE_BYTES_OR_NS_STAMPS_DIFFER')
    git_proof = git_reader()
    validate_git(git_proof, context)
    physical = validate_fresh_physical(physical_reader())
    runtime = runtime_reader()
    need(type(runtime) is dict and runtime.get('immutable_lock_verified') is True and
         runtime.get('six_runtime_identities_verified') is True and runtime.get('sourceio574_exact_including_mtime') is True and
         runtime.get('literal_helpers_verified') is True and runtime.get('exporter120_exact_including_mtime') is True,
         'EXACT_APPROVED_RUNTIME_REQUIRED')
    return dict(head=git_proof['head'], tested_revision=TESTED, physical=physical, runtime=runtime)


def admitted_launch(context, *, source_reader, git_reader, physical_reader, runtime_reader, launch):
    proof = admit(context, source_reader=source_reader, git_reader=git_reader,
                  physical_reader=physical_reader, runtime_reader=runtime_reader)
    return launch(proof)


def retained_output(args, *, cwd=ROOT, env=None, timeout=30):
    """Read-only command, retained handle, bounded output, always reap owned PID."""
    process = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        out, err = process.communicate(timeout=timeout)
    except BaseException:
        if process.poll() is None:
            process.kill()  # Only this exact retained observer/Git handle.
        process.communicate()
        raise
    need(process.poll() is not None and process.returncode == 0 and len(out) <= 32 * 1024 * 1024 and
         len(err) <= 1024 * 1024, 'READ_ONLY_OBSERVER_FAILED')
    return out


def git_proof():
    env = os.environ.copy()
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    head = retained_output(['git', 'rev-parse', 'HEAD'], env=env).decode('ascii').strip()
    def blobs(revision):
        raw = retained_output(['git', 'ls-tree', '-r', '-z', revision, '--', *TREES, *FILES], env=env)
        result = {}
        for row in raw.split(b'\0'):
            if not row:
                continue
            meta, name = row.split(b'\t', 1)
            mode, kind, oid = meta.split()
            name = name.decode('utf-8')
            if Path(name).suffix == '.pyc' or '__pycache__' in Path(name).parts:
                continue
            relative(name)
            need(kind == b'blob' and mode in (b'100644', b'100755') and name not in result, 'GIT_BLOB_SCHEMA')
            result[name] = oid.decode('ascii')
        return result
    # An unsuccessful ancestry check is an admission refusal, never a new base.
    retained_output(['git', 'merge-base', '--is-ancestor', TESTED, head], env=env)
    return dict(head=head, tested_is_ancestor=True, tested_blobs=blobs(TESTED), head_blobs=blobs(head))


def observe_physical(stage, launch, suffix):
    command = ('[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); '
               '$ErrorActionPreference="Stop"; '
               '@(Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine) '
               '| ConvertTo-Json -Depth 3 -Compress')
    # The approved Codex host executable is single-link and hash-pinned. Do not
    # weaken no-hardlinks for System32's legitimate linked copy or fall back.
    read_checked(PWSH, PWSH_PIN)
    raw = retained_output([str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', command])
    rows = strict_json(raw.decode('utf-8-sig'))
    need(type(rows) is list, 'CIM_TOP_LEVEL_LIST')
    # This raw file is private ignored output; it may contain command paths.
    with (stage / ('PRIVATE_CIM_' + suffix + '.json')).open('xb') as stream:
        stream.write(raw)
    result = validate_physical(rows, os.getpid(), launch)
    result.update(observed_ns=time.time_ns(), raw_bytes=len(raw), raw_sha256=sha(raw),
                  observer_retained_waited_reaped=True, observer_exit=0)
    return result


def complete_catalogue(folder, *, exporter=False, expected=None):
    result, paths = {}, {}
    safe(folder)
    for base, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs:
            safe(Path(base) / name)
        for name in files:
            path = Path(base) / name
            if exporter and ('__pycache__' in path.parts or path.suffix == '.pyc'):
                continue
            safe(path)
            name = path.relative_to(folder).as_posix()
            paths[name] = path
    if expected is not None:
        need(set(paths) == set(expected), 'BEFORE_READ_CATALOGUE_MEMBERSHIP_DIFFERS')
    for name, path in sorted(paths.items()):
        pin = None if expected is None else (expected[name]['bytes'], expected[name]['sha256'])
        _raw, row, _stamp = read_checked(path, pin)
        result[name] = row
    return result


def runtime_check(lock_path):
    need(Path(lock_path) == ROOT / LOCK_REL, 'IMMUTABLE_APPROVED_LOCK_PATH_DIFFERS')
    raw, lock_identity, _stamp = read_checked(lock_path)
    need(Path(lock_path) == ROOT / LOCK_REL and sha(raw) == LOCK_SHA, 'IMMUTABLE_APPROVED_LOCK_DIFFERS')
    lock = strict_json(raw)
    need(type(lock.get('runtime_executables')) is dict and len(lock['runtime_executables']) == 6 and
         type(lock.get('sourceio_files')) is dict and len(lock['sourceio_files']) == 574, 'APPROVED_LOCK_SCOPE')
    observed = {}
    for name, expected in lock['runtime_executables'].items():
        _raw, row, _stamp = read_checked(Path(name), (expected['bytes'], expected['sha256']))
        need(row == expected, 'SIX_APPROVED_RUNTIME_IDENTITY_DIFFERS')
        observed[name] = row
    for name, pin in RUNTIME_PINS.items():
        need(name in observed and (observed[name]['bytes'], observed[name]['sha256']) == pin,
             'REQUIRED_RUNTIME_LITERAL_DIFFERS')
    need(Path(sys.executable).absolute() == PYTHON and sys.version_info[:2] == (3, 13) and
         sys.platform == 'win32' and sys.byteorder == 'little', 'ROOT_PINNED_PYTHON_CONTEXT')
    catalogue = complete_catalogue(SOURCEIO, expected=lock['sourceio_files'])
    need(catalogue == lock['sourceio_files'], 'COMPLETE_SOURCEIO574_IDENTITY_OR_NS_MTIME_DIFFERS')
    exporter_root = BLENDER.parent / '5.1/scripts/addons_core/io_scene_gltf2'
    need(lock.get('exporter_root') == str(exporter_root) and type(lock.get('exporter_noncache_sources')) is dict and
         len(lock['exporter_noncache_sources']) == 120, 'APPROVED_EXPORTER120_SCOPE')
    exporter = complete_catalogue(exporter_root, exporter=True, expected=lock['exporter_noncache_sources'])
    need(exporter == lock['exporter_noncache_sources'], 'EXPORTER120_IDENTITY_OR_NS_MTIME_DIFFERS')
    helpers = {}
    for name, pin in HELPERS.items():
        _raw, row, _stamp = read_checked(ROOT / name, pin)
        helpers[name] = row
    return dict(immutable_lock_verified=True, six_runtime_identities_verified=True,
                sourceio574_exact_including_mtime=True, literal_helpers_verified=True,
                exporter120_exact_including_mtime=True,
                lock=lock_identity, runtimes=observed, helpers=helpers,
                sourceio_catalogue=catalogue, exporter_noncache_catalogue=exporter)


def validate_result(result, placement, desktop, launcher_exit):
    need(launcher_exit == 0 and desktop.get('format') == 'studio_private_desktop_1' and
         type(desktop.get('exit')) is int and desktop['exit'] == 0 and
         type(desktop.get('child_pid')) is int and desktop['child_pid'] > 0 and
         desktop.get('job_memory_limit_bytes') == 4096 * 1024 * 1024 and
         type(desktop.get('desktop')) is str and desktop['desktop'].startswith('HAS_Test_'), 'PRIVATE_JOB_RESULT')
    for key in ('job_closed', 'desktop_closed', 'child_desktop_confirmed', 'private_window_seen'):
        need(desktop.get(key) is True, 'PRIVATE_JOB_' + key.upper())
    need(desktop.get('foreground_child_observed') is False and desktop.get('desktop_switch_requested') is False and
         not any(key in desktop for key in ('error', 'monitor_error', 'desktop_enumeration_error', 'cancelled')),
         'PRIVATE_JOB_VISIBILITY_OR_FAILURE')
    need(placement.get('format') == 'has_carrier_export_hidden_placement_1' and
         placement.get('worker_verified_hidden_sentinel_closed') is True and type(placement.get('policy')) is dict,
         'PLACEMENT_REPORT')
    policy = placement['policy']
    need(policy.get('format') == 'has_hidden_background_desktop_placement_sentinel_1' and
         policy.get('class') == 'STATIC' and policy.get('requested_size_pixels') == [0, 0], 'REAL_HIDDEN_SENTINEL_REQUIRED')
    for key in ('disabled', 'noactivate_style', 'toolwindow_style', 'owned_pid_and_thread_verified', 'destroyed_in_finally'):
        need(policy.get(key) is True, 'SENTINEL_' + key.upper())
    for key in ('visible_at_creation', 'visible_before_destruction', 'show_or_activation_calls', 'thread_desktop_switch_calls'):
        need(policy.get(key) is False, 'SENTINEL_' + key.upper())
    need(result.get('format') == 'has_fresh_source_native_carrier_export_probe_1' and
         result.get('status') == 'MATCHED_FRESH_NATIVE_IDS_OWNED_MATERIALS_AND_CARRIER_EXPORT', 'WORKER_NOT_QUALIFIED')
    for key in ('sourceio_import_executed', 'importer_attribute_never_patched', 'hidden_placement_verified',
                'all_read_inputs_hash_size_stamp_unchanged', 'original_importer_attribute_unchanged'):
        need(result.get(key) is True, 'WORKER_' + key.upper())
    for key in ('historical_saved_B_native_causality_qualified', 'original_B_scene_opened',
                'host_image_pixels_getter_used', 'blend_saved', 'native_arrays_published',
                'normal_fidelity_qualified', 'outer_physical_closure_verified_by_worker'):
        need(result.get(key) is False, 'WORKER_UNSUPPORTED_CLAIM_' + key.upper())
    need(result.get('sourceio_material_files_opened') == 0 and type(result.get('sourceio_material_files_opened')) is int and
         result.get('sourceio_image_datablocks_created') == 0 and type(result.get('sourceio_image_datablocks_created')) is int and
         result.get('sourceio_catalogue_files') == 574, 'WORKER_RESOURCE_DOMAIN')
    need(result.get('observer_ast_inverse') == dict(setter_sites=1, validate_sites=1, observer_calls=4,
                                                   original_function_AST_restored=True), 'WORKER_OBSERVER_AST')
    observation = result.get('observation')
    need(type(observation) is dict and observation.get('format') == 'has_fresh_sourceio_current_id_and_RNA_weight_observation_1' and
         observation.get('observed_new_models') == 2 and observation.get('observed_new_points') == 9661 and
         observation.get('observed_new_corners') == 42702, 'EXACT_TWO_MODEL_PROFILE')
    for key in ('fresh_creation_chain_matches_independent_native_candidate', 'current_exact_family_ordered_weight_storage_observed'):
        need(observation.get(key) is True, 'CURRENT_ID_OBSERVATION_MISSING')
    for key in ('historical_saved_B_native_causality_qualified', 'current_B_opened_or_relabelled',
                'generic_weight_storage_qualified', 'native_normal_fidelity_qualified', 'carrier_or_exporter_binding_qualified',
                'non_normal_semantic_equivalence_qualified', 'application_adoption_qualified'):
        need(observation.get(key) is False, 'DOWNSTREAM_QUALIFICATION_FORBIDDEN')
    models = observation.get('models')
    need(type(models) is list and len(models) == 2 and
         sorted((row.get('points'), row.get('corners'), row.get('groups'), row.get('observed_stages')) for row in models)
         == [(1650, 8370, 69, 4), (8011, 34332, 69, 4)], 'EXACT_MODEL_COUNTS_AND_PHASES')
    identities = result.get('input_identities')
    need(type(identities) is dict and len(identities) == 31 and result['sourceio_catalogue_files'] + len(identities) == 605,
         'EXACT_605_WORKER_INPUT_READS')
    need(result.get('original_current_ID_RNA_controls_retained') is True and
         result.get('inherited_authenticated_reads') == 590 and result.get('exact_authenticated_reads') == 605,
         'INHERITED_590_AND_EXTENDED_605_READ_CONTROLS')
    validate_material_report(result.get('material_binding'))
    for key in ('resolved_native_default_skin_equivalence_qualified', 'B_dependency_closure_qualified'):
        need(result.get(key) is False, 'UNSUPPORTED_MATERIAL_SCOPE_CLAIM')
    validate_owned_B_report(result)
    validate_carrier_report(result)
    nested = result['material_binding'].get('native_path_witness')
    validate_native_path_witness(nested)
    stable = ('candidate_order_sha256','native_path_provenance_sha256',
              'current_reference_witness_sha256','resolved_cache_witness_sha256')
    need(all(nested[key] == result['native_material_path_witness'][key] for key in stable),
         'MATERIAL_PATH_WITNESS_REPORT_BINDING_DIFFERS')
    return observation


def read_private_carrier(path,expected_bytes,expected_sha256):
    need(type(expected_bytes) is int and 28<=expected_bytes<=128*1024*1024 and
         type(expected_sha256) is str and re.fullmatch('[0-9a-f]{64}',expected_sha256) is not None,
         'CARRIER_READBACK_PIN_DOMAIN')
    raw,_row,_stamp=read_checked(path,(expected_bytes,expected_sha256),limit=128*1024*1024)
    return raw


def load_root_comparison_helpers(checks):
    sources=(('semantic_compare','semantic_compare.py',(22754,'c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00')),
             ('private_carrier_input_domain','input_domain.py',(16109,'c679d873aa45aac4fad553f014e83c8e42a9a458c8189151e9e3695072be8c74')))
    modules={}
    for name,filename,pin in sources:
        need(name not in sys.modules,'COLD_ROOT_COMPARISON_NAMESPACE_REQUIRED')
        path=HERE/filename
        raw,row,before=read_checked(path,pin)
        register_file_check(checks,'root_comparison_'+filename,path,pin,row,before)
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        exec(compile(raw,str(path),'exec',dont_inherit=True),module.__dict__)
        modules[name]=module
    return modules['private_carrier_input_domain']


def run_strict_non_normal(before_raw,carrier_raw,domain_module):
    need(type(before_raw) is bytes and type(carrier_raw) is bytes,'STRICT_COMPARISON_RAW_BYTES_REQUIRED')
    return domain_module.compare_qualified_non_normal(before_raw,carrier_raw)


def load_root_normal_helpers(checks):
    sources=(('private_carrier_normal_gate',HERE/'normal_gate.py',NORMAL_GATE_PIN),
             ('private_carrier_native_rows',ROOT/'experiments/native_point_expectation_bone_state_fix_20261118/native_point_expectation.py',
              (27615,'cbb4eca98a6cf5045211dc10bd8e060b79492ec306d61a4d29679fc0d5cc184d')))
    modules=[]
    for name,path,pin in sources:
        need(name not in sys.modules,'COLD_ROOT_NORMAL_NAMESPACE_REQUIRED')
        raw,row,before=read_checked(path,pin)
        register_file_check(checks,'root_normal_'+path.name,path,pin,row,before)
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        exec(compile(raw,str(path),'exec',dont_inherit=True),module.__dict__)
        modules.append(module)
    return tuple(modules)


def run_carrier_comparisons(before_raw,carrier_raw,relation,native_source,frame,domain_module,normal_module):
    reports={}
    try:
        reports['non_NORMAL']=run_strict_non_normal(before_raw,carrier_raw,domain_module)
        reports['non_NORMAL_passed']=True
    except ValueError:
        reports['non_NORMAL']={'passed':False,'code':'STRICT_NON_NORMAL_COMPARISON_REFUSED'}
        reports['non_NORMAL_passed']=False
    try:
        reports['raw_normal']=normal_module.measure_native_normal_gate(carrier_raw,relation,native_source,frame,domain_module)
        reports['raw_normal_passed']=reports['raw_normal'].get('passed') is True
    except ValueError:
        reports['raw_normal']={'passed':False,'code':'STRICT_NATIVE_NORMAL_MEASUREMENT_REFUSED','source_normal_threshold':2e-5}
        reports['raw_normal_passed']=False
    reports['passed']=reports['non_NORMAL_passed'] and reports['raw_normal_passed']
    return reports


def validate_carrier_report(result):
    for key in ('exporter_invoked','operator_preflight_observed','carrier_written'):
        need(result.get(key) is True,'ACTUAL_CARRIER_REQUIRED_'+key.upper())
    need(result.get('scene_or_registration_restoration_failed') is False,'EXPORT_SCENE_RESTORATION_REQUIRED')
    report=result.get('carrier_export')
    need(type(report) is dict and type(report.get('operator_invocations')) is int and report['operator_invocations']==1 and
         report.get('ordinary_operator_finished') is True and type(report.get('own_carrier_attributes')) is int and
         report['own_carrier_attributes']==2,'ONE_ACTUAL_CARRIER_OPERATOR_REQUIRED')
    need(type(report.get('carrier_glb_bytes')) is int and 28<=report['carrier_glb_bytes']<=128*1024*1024 and
         type(report.get('private_relation_sha256')) is str and
         re.fullmatch('[0-9a-f]{64}',report['private_relation_sha256']) is not None and
         type(report.get('carrier_glb_sha256')) is str and re.fullmatch('[0-9a-f]{64}',report['carrier_glb_sha256']) is not None,
         'CARRIER_OUTPUT_DIGEST_AND_BUDGET')
    need(not set(report).intersection({'private_relation_bytes','carrier_glb','raw','relation','source_ids'}),'PRIVATE_CARRIER_ARRAY_IN_PUBLIC_REPORT')
    need(result.get('carrier_output_present_unqualified') is True and
         result.get('carrier_output_presence_check_failed',False) is False and
         result.get('carrier_output_bytes_unqualified')==report['carrier_glb_bytes'] and
         result.get('carrier_output_sha256_unqualified')==report['carrier_glb_sha256'],'FINAL_OWNED_OUTPUT_READBACK_REQUIRED')
    observation=report.get('export_observation')
    need(type(observation) is dict and observation.get('format')=='has_source_export_hook_proposal_1' and
         type(observation.get('source_normal_threshold_unchanged')) is float and
         observation['source_normal_threshold_unchanged']==2e-5 and observation.get('source_normal_error_measured') is False,
         'EXACT_EXPORT_OBSERVATION_AND_UNMEASURED_NORMAL_THRESHOLD')
    bound=observation.get('actual_export_binding')
    need(type(bound) is dict and bound.get('passed') is True and
         type(bound.get('meshes')) is int and bound['meshes']==2 and
         type(bound.get('primitives')) is int and bound['primitives']==4 and
         type(bound.get('source_ids')) is int and bound['source_ids']==9661 and
         bound.get('carrier_glb_sha256')==report['carrier_glb_sha256'],'GENUINE_FINAL_PRIMITIVE_BINDING_REQUIRED')
    resources=observation.get('resources')
    need(type(resources) is dict and resources.get('format')=='has_narrow_shared_actual_resource_reference_observation_3' and
         type(resources.get('materials')) is int and resources['materials']==4 and
         type(resources.get('source_images')) is int and resources['source_images']==result['owned_B_inspection']['reached_images'] and
         type(resources.get('images')) is int and resources['images']==resources['source_images'] and
         type(resources.get('image_bindings')) is int and resources['source_images']<=resources['image_bindings']<=4 and
         type(resources.get('textures')) is int and resources['textures']==resources['image_bindings'],'GENUINE_SHARED_RESOURCE_BINDING_REQUIRED')
    readiness=result.get('bounded_image_buffer_readiness')
    need(type(readiness) is dict and readiness.get('format')=='has_bounded_packed_png_buffer_readiness_1' and
         readiness.get('status')=='BOUNDED_PACKED_PNG_BUFFERS_READY_1' and
         readiness.get('complete_set_admitted_before_buffer_getters') is True and
         readiness.get('packed_memory_branch_preconditions_validated') is True and
         readiness.get('nonbuffer_metadata_and_packed_refs_unchanged') is True and
         readiness.get('packed_hashes_rechecked') is True and
         type(readiness.get('images_verified_ready')) is int and
         readiness['images_verified_ready']==resources['source_images'],'BOUNDED_PACKED_BUFFER_READINESS_REQUIRED')
    return report


def validate_native_path_witness(value):
    need(type(value) is dict and value.get('format') == 'has_finite_native_preloaded_material_path_witness_1' and
         value.get('status') == 'RETURNED_BINDING_OBSERVED', 'NATIVE_PATH_WITNESS_REQUIRED')
    four_counts = ('selected_material_records','metadata_rows_observed','genuine_material_rows',
                   'full_path_present','full_path_string','selected_domain_memberships',
                   'candidate_membership_matches','global_lookup_matches','native_material_records',
                   'cache_materials_observed','source_B_refs_observed','provider_true')
    need(all(type(value.get(key)) is int and value[key] == 4 for key in four_counts),
         'NATIVE_PATH_COMPLETE_FOUR_MATERIAL_COUNTS')
    zero_counts = ('full_path_missing','full_path_nonstring','candidate_membership_missing',
                   'candidate_membership_ambiguous','global_lookup_conflicts')
    need(all(type(value.get(key)) is int and value[key] == 0 for key in zero_counts), 'NATIVE_PATH_NO_UNRESOLVED_ROWS')
    for key in ('preflight_admitted','resolver_bound','resolution_complete','returned_binding_observed',
                'no_metadata_writes','no_material_file_IO','no_file_existence_claim'):
        need(value.get(key) is True,'NATIVE_PATH_REQUIRED_'+key.upper())
    for key in ('native_or_historical_point_identity_qualified','resource_or_normal_fidelity_qualified',
                'exporter_invoked','application_adoption_qualified'):
        need(value.get(key) is False,'NATIVE_PATH_UNSUPPORTED_'+key.upper())
    need(type(value.get('domain_material_records')) is int and 4 <= value['domain_material_records'] <= 4096 and
         type(value.get('native_candidates')) is int and 4 <= value['native_candidates'] <= 1028 and
         type(value.get('provider_queries')) is int and 4 <= value['provider_queries'] <= value['native_candidates'] and
         type(value.get('provider_false')) is int and value['provider_false'] >= 0 and
         value['provider_queries'] == value['provider_true'] + value['provider_false'],
         'NATIVE_PATH_FINITE_QUERY_DOMAIN')
    need(type(value.get('phase_observations')) is int and value['phase_observations'] == 8 and
         type(value.get('returned_observations')) is int and value['returned_observations'] == 1,
         'NATIVE_PATH_ALL_ACTUAL_PHASES_AND_RETURNED')
    for key in ('check_calls','complete_check_calls'):
        need(type(value.get(key)) is int and 1 <= value[key] <= 65536,'NATIVE_PATH_CHECK_COUNT_DOMAIN')
    need(value['check_calls'] >= value['complete_check_calls'], 'NATIVE_PATH_COMPLETE_CHECK_COUNT')
    for key in ('candidate_order_sha256','native_path_provenance_sha256',
                'current_reference_witness_sha256','resolved_cache_witness_sha256'):
        need(type(value.get(key)) is str and re.fullmatch('[0-9a-f]{64}',value[key]) is not None,
             'NATIVE_PATH_STABLE_PROVENANCE_DIGEST')
    return value


def validate_material_report(value):
    need(type(value) is dict and value.get('format') == 'has_fresh_sourceio_resolved_material_slot_skin_observation_1',
         'RAW_MATERIAL_BINDING_REPORT_REQUIRED')
    counts = dict(native_material_records=4, native_skin_families=1, native_skin_references=4,
                  native_body_parts=2, native_model_records=3, native_mesh_records=4,
                  observed_models=2, observed_faces=14234)
    need(all(type(value.get(key)) is int and value[key] == count for key, count in counts.items()),
         'EXACT_JUNKO_MATERIAL_PROFILE')
    for key in ('sourceio_raw_matches_candidate_default_skin_on_used_meshes',
                'exact_family_raw_material_placeholder_slot_face_binding_observed',
                'exact_family_skin_property_reference_or_name_storage_observed'):
        need(value.get(key) is True, 'MATERIAL_BINDING_OBSERVATION_MISSING')
    for key in ('resolved_native_default_skin_equivalence_qualified', 'native_skin_switching_qualified',
                'material_files_or_B_opened', 'B_dependency_closure_qualified', 'native_normal_fidelity_qualified',
                'carrier_or_exporter_binding_qualified', 'non_normal_semantic_equivalence_qualified',
                'application_adoption_qualified'):
        need(value.get(key) is False, 'MATERIAL_BINDING_UNSUPPORTED_QUALIFICATION')
    need(type(value.get('used_raw_mesh_material_count')) is int and 1 <= value['used_raw_mesh_material_count'] <= 4 and
         type(value.get('candidate_default_skin_row_sha256')) is str and
         re.fullmatch('[0-9a-f]{64}', value['candidate_default_skin_row_sha256']) is not None,
         'FRESH_NATIVE_DEFAULT_ROW_PROOF_REQUIRED')
    rows = value.get('models')
    need(type(rows) is list and len(rows) == 2 and all(type(row) is dict and type(row.get('faces')) is int for row in rows) and
         sorted(row.get('faces') for row in rows) == [2790, 11444],
         'WHOLE_FACE_STREAM_COUNTS')
    for row in rows:
        need(type(row) is dict and type(row.get('observed_stages')) is int and row['observed_stages'] == 4 and
             type(row.get('slots')) is int and 1 <= row['slots'] <= 4 and row.get('skin_storage') in ('MATERIAL_ID', 'STRING') and
             type(row.get('raw_face_material_order_sha256')) is str and
             re.fullmatch('[0-9a-f]{64}', row['raw_face_material_order_sha256']) is not None,
             'FOUR_STAGE_MATERIAL_SLOT_SKIN_PROOF')
    need(value.get('explicit_read_only_preloaded_path_profile') is True, 'EXPLICIT_NATIVE_PATH_PROFILE_REQUIRED')
    need(value.get('external_material_file_existence_qualified') is False and
         value.get('B_material_properties_written') is False, 'RESOLVED_MATERIAL_READONLY_SCOPE_REQUIRED')
    validate_native_path_witness(value.get('native_path_witness'))
    return value


def reap_owned_launcher(process):
    """Only a retained Popen handle is accepted by callers; never find/kill PIDs.

    Cleanup failure is returned so a primary write/timeout/native error survives.
    A failed reap never establishes physical closure or releases the lane lock.
    """
    try:
        if process.poll() is None:
            process.kill()
    except BaseException:
        pass
    waited = False
    try:
        process.wait(timeout=20)
        waited = True
    except BaseException:
        pass
    try:
        return waited and process.poll() is not None
    except BaseException:
        return False


def wait_recorded_owned(process, record_writer):
    """Protect the launch-record write and every subsequent operation alike."""
    try:
        record_writer()
        process.wait(timeout=185)
        need(process.poll() is not None, 'OWNED_LAUNCHER_NOT_REAPED')
    finally:
        # Also covers a failed PRIVATE_launch.json write before the first wait.
        # This helper cannot replace the independent subsequent CIM observation.
        if sys.exc_info()[0] is not None or process.poll() is None:
            reap_owned_launcher(process)


def failed_run_audit(checks, *, primary_error, launcher_reaped, worker_receipt_present, closure_observer,
                     native_launch_attempted=True):
    """Always attempt fresh closure, preserving failure even when all checks pass."""
    audit = {}
    for name, check in checks.items():
        try:
            audit[name] = check() is True
        except BaseException:
            audit[name] = False
    physical = None
    closure_confirmed = False
    try:
        physical = validate_fresh_physical(closure_observer())
        closure_confirmed = not native_launch_attempted or launcher_reaped is True
    except BaseException:
        # Never mask the primary exception or infer closure from a missing
        # receipt, process.poll(), a timeout, or successful preservation reads.
        pass
    return dict(format='has_carrier_export_failed_run_preservation_1', status='UNQUALIFIED_FAILED_RUN',
                primary_error_type=type(primary_error).__name__,
                primary_error_code=str(primary_error) if isinstance(primary_error, Refusal) else type(primary_error).__name__,
                checks=audit, all_attempted_checks_passed=all(audit.values()),
                native_launch_attempted=native_launch_attempted is True,
                owned_launcher_reaped=native_launch_attempted is True and launcher_reaped is True,
                worker_receipt_present=worker_receipt_present is True,
                physical_closure_attempted=True, physical_closure_confirmed=closure_confirmed,
                physical_closure=physical, owned_lock_retained=not closure_confirmed,
                runtime_lane_released=False, application_adoption_qualified=False, native_fidelity_qualified=False)


def register_file_check(checks, label, path, pin, row, before):
    need(label not in checks, 'DUPLICATE_PRESERVATION_LABEL')
    def check():
        _raw, after, observed = read_checked(path, pin)
        return after == row and observed == before
    checks[label] = check


def remember_written_file(checks, label, row):
    path = Path(row['path'])
    _raw, identity, before = read_checked(path, (row['bytes'], row['sha256']))
    register_file_check(checks, label, path, (row['bytes'], row['sha256']), identity, before)
    return row


def owned_library_path_digest(path):
    key = ntpath.normcase(ntpath.normpath(str(path)))
    return sha(json.dumps(key, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode())


def validate_owned_B_report(result, expected_owned_path=None):
    for key in ('material_library_appended', 'material_resources_loaded', 'owned_B_materials_precede_native_import',
                'owned_B_resources_unchanged_after_native_import', 'all_four_source_materials_reuse_admitted_B_refs'):
        need(result.get(key) is True, 'COMBINED_B_' + key.upper())
    enumeration = result.get('owned_B_enumeration')
    need(type(enumeration) is dict and enumeration.get('format') == 'has_empty_library_enumeration_summary_2' and
         enumeration.get('actual_id_census_unchanged') is True and enumeration.get('all_destination_requests_empty') is True and
         type(enumeration.get('source_materials')) is int and 4 <= enumeration['source_materials'] <= 256,
         'COMBINED_B_ENUMERATION_REQUIRED')
    for key, maximum in (('before_id_count', 4096), ('after_id_count', 4096), ('id_collections', 128),
                         ('source_id_types', 128), ('source_catalogue_name_count', 16384), ('destination_request_types', 128)):
        need(type(enumeration.get(key)) is int and 0 < enumeration[key] <= maximum, 'COMBINED_EMPTY_CENSUS_COUNT')
    need(enumeration['before_id_count'] == enumeration['after_id_count'] and
         enumeration['source_id_types'] == enumeration['destination_request_types'] and
         enumeration['source_catalogue_name_count'] >= enumeration['source_materials'], 'COMBINED_EMPTY_CENSUS_CARDINALITY')
    for key in ('source_material_names_sha256', 'source_catalogue_sha256'):
        need(type(enumeration.get(key)) is str and re.fullmatch('[0-9a-f]{64}', enumeration[key]) is not None,
             'COMBINED_EMPTY_CENSUS_DIGEST')
    summary = result.get('owned_B_inspection')
    need(type(summary) is dict and summary.get('format') == 'has_material_only_library_inspection_summary_2' and
         summary.get('status') == 'INSPECTED_MATERIAL_ONLY_OWNED_LIBRARY_AND_PACKED_PNG_HEADERS_2', 'COMBINED_B_INSPECTION_REQUIRED')
    for key in ('append_requested', 'append_completed', 'surviving_originals_unchanged'):
        need(summary.get(key) is True, 'COMBINED_INSPECTION_' + key.upper())
    for key, count in (('requested_materials', 4), ('inspected_material_graphs', 4)):
        need(type(summary.get(key)) is int and summary[key] == count, 'COMBINED_INSPECTION_MATERIAL_COUNTS')
    need(type(summary.get('available_materials')) is int and summary['available_materials'] == enumeration['source_materials'] and
         type(summary.get('unrequested_catalogue_materials')) is int and
         summary['unrequested_catalogue_materials'] == enumeration['source_materials'] - 4, 'COMBINED_CATALOGUE_COUNTS')
    for key, maximum in (('reached_images', 128), ('shared_image_references', 4), ('packed_bytes_copied', 128 * 1024 * 1024),
                         ('prospective_rgba_f32_bytes', 128 * 1024 * 1024), ('before_id_count', 4096), ('after_id_count', 4096)):
        need(type(summary.get(key)) is int and 0 <= summary[key] <= maximum, 'COMBINED_INSPECTION_COUNT_BUDGET')
    libraries = summary.get('retained_owned_source_libraries')
    need(type(libraries) is int and libraries in (0, 1) and
         summary.get('owned_source_library_validation_attempted') is bool(libraries) and
         summary.get('retained_owned_source_library_verified') is bool(libraries), 'COMBINED_OWNED_LIBRARY_PROOF')
    if libraries:
        value = summary.get('retained_library_filepath_sha256')
        need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'COMBINED_OWNED_LIBRARY_DIGEST')
        if expected_owned_path is not None:
            need(value == owned_library_path_digest(expected_owned_path), 'COMBINED_OWNED_LIBRARY_PATH_DIFFERS')
    else:
        need('retained_library_filepath_sha256' not in summary, 'COMBINED_ZERO_LIBRARY_HAS_NO_PATH')
    added = summary.get('added_id_counts')
    need(type(added) is dict and set(added) <= {'materials', 'images', 'libraries'} and
         type(added.get('materials')) is int and added['materials'] == 4 and type(added.get('images', 0)) is int and
         added.get('images', 0) == summary['reached_images'] and type(added.get('libraries', 0)) is int and
         added.get('libraries', 0) == libraries and summary['before_id_count'] == enumeration['after_id_count'] and
         summary['after_id_count'] == summary['before_id_count'] + 4 + summary['reached_images'] + libraries,
         'COMBINED_INSPECTION_ADDED_IDS')
    for key in ('material_names_sha256', 'graph_metadata_sha256', 'packed_observation_sha256'):
        need(type(summary.get(key)) is str and re.fullmatch('[0-9a-f]{64}', summary[key]) is not None, 'COMBINED_INSPECTION_DIGEST')
    for key in ('material_binding_qualified', 'resource_equivalence_qualified', 'B_dependency_closure_qualified',
                'non_normal_semantic_equivalence_qualified', 'native_or_historical_point_identity_qualified', 'exporter_qualified',
                'normal_fidelity_qualified', 'application_adoption_qualified', 'transient_ID_or_C_level_read_absence_qualified',
                'image_buffer_getters_used', 'blend_saved', 'exporter_invoked', 'external_filepath_retrieval_attempted'):
        need(summary.get(key) is False, 'COMBINED_INSPECTION_SCOPE_' + key.upper())
    witness = result.get('native_material_path_witness')
    validate_native_path_witness(witness)
    attestation = result.get('preloaded_resolver_runtime_attestation')
    need(type(attestation) is dict and attestation.get('format') == 'has_preloaded_material_resolver_runtime_attestation_1' and
         all(attestation.get(key) is True for key in ('complete_module_code_equal','actual_globals_and_aliases_equal',
             'original_importer_attribute_unchanged','no_resolver_replacement')) and
         type(attestation.get('source_catalogue_helpers')) is int and attestation['source_catalogue_helpers']==2 and
         type(attestation.get('genuine_functions')) is int and attestation['genuine_functions']==3,
         'PRELOADED_RESOLVER_RUNTIME_ATTESTATION_REQUIRED')
    adaptation = result.get('readonly_preloaded_material_adaptation')
    need(type(adaptation) is dict and adaptation.get('format') == 'has_readonly_preloaded_material_adaptation_1' and
         all(adaptation.get(key) is True for key in ('no_metadata_writes','no_material_renames','no_material_swaps')) and
         type(adaptation.get('native_imports_before_append')) is int and adaptation['native_imports_before_append'] == 0,
         'READONLY_PRELOADED_MATERIAL_ADAPTATION_REQUIRED')
    return summary


def validate_legacy_bare_reuse_report(result, summary):
    # Kept for inherited pure contract cases, never used as the v3 actual profile.
    reuse = result.get('ordinary_importer_material_reuse_preflight')
    need(type(reuse) is dict and reuse.get('format') == 'has_owned_B_ordinary_material_lookup_preflight_1' and
         type(reuse.get('materials')) is int and reuse['materials'] == 4 and reuse.get('exact_full_path_rule') is True and
         reuse.get('unique_actual_refs') is True and reuse.get('material_names_sha256') == summary['material_names_sha256'] and
         all(type(reuse.get(key)) is int and reuse[key] == 0 for key in ('material_renames', 'material_swaps', 'native_imports_before_append')),
         'COMBINED_ORDINARY_IMPORTER_REUSE_PROOF')
    return summary


def new_stage():
    candidate = ROOT / 'output' / ('source-material-carrier-run-' + str(time.time_ns()))
    safe(candidate, exists=False)
    need(candidate.parent == ROOT / 'output' and not candidate.exists(), 'FRESH_STAGE_BOUNDARY')
    candidate.mkdir()
    return candidate


def validate_qualified_creation(value):
    need(type(value) is dict and value.get('format') == 'has_root_fresh_source_owned_B_resolved_material_creation_run_1' and
         value.get('status') == 'CURRENT_IDS_RNA_WITH_OWNED_B_RESOLVED_MATERIALS_MATCHED',
         'COMMITTED_REAL_MODEL_CREATION_NOT_QUALIFIED')
    for key in ('whole_full_pass_required','private_job_closed','launcher_reaped','hidden_placement_verified',
                'original_and_staged_hash_bytes_nsmtime_unchanged','source_and_head_unchanged',
                'material_library_appended','material_resources_loaded','all_four_source_materials_reuse_admitted_B_refs'):
        need(value.get(key) is True,'QUALIFIED_CREATION_REQUIRED_'+key.upper())
    need(type(value.get('functional_source_count')) is int and value['functional_source_count']==1061 and
         type(value.get('exact_authenticated_reads')) is int and value['exact_authenticated_reads']==596,
         'QUALIFIED_CREATION_SOURCE_AND_INPUT_DOMAIN')
    physical=value.get('fresh_physical_after')
    need(type(physical) is dict and type(physical.get('owned_processes')) is int and physical['owned_processes']==0 and
         physical.get('observer_retained_waited_reaped') is True and physical.get('full_pids_absent') is True,
         'QUALIFIED_CREATION_PHYSICALLY_CLOSED')
    for key in ('historical_saved_B_native_causality_qualified','normal_fidelity_qualified','exporter_qualified',
                'carrier_qualified','non_normal_semantic_equivalence_qualified','application_adoption_qualified',
                'original_B_scene_opened','exporter_invoked','blend_saved','native_arrays_published'):
        need(value.get(key) is False,'QUALIFIED_CREATION_SCOPE_'+key.upper())
    witness=value.get('native_material_path_witness')
    need(type(witness) is dict and witness.get('status')=='RETURNED_BINDING_OBSERVED' and
         witness.get('resolution_complete') is True and witness.get('no_metadata_writes') is True and
         witness.get('no_file_existence_claim') is True,'QUALIFIED_CREATION_NATIVE_PATH_WITNESS')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-lane-confirmed', action='store_true', help='Root attests no other session job will start during this probe')
    parser.add_argument('--driver-sha256', required=True)
    parser.add_argument('--worker-sha256', required=True)
    parser.add_argument('--ledger-sha256', required=True)
    parser.add_argument('--binding-sha256', required=True)
    parser.add_argument('--qualified-creation', type=Path, required=True)
    parser.add_argument('--qualified-creation-sha256', required=True)
    parser.add_argument('--approved-runtime-lock', type=Path, default=ROOT / LOCK_REL)
    parser.add_argument('--approved-runtime-lock-sha256', default=LOCK_SHA)
    options = parser.parse_args()
    need(options.root_lane_confirmed, 'EXPLICIT_ROOT_LANE_REQUIRED')
    need(options.binding_sha256 == BINDING_PIN[1] and BINDING_PIN[0] > 0,
         'FROZEN_BINDING_SOURCE_PIN_REQUIRED')
    need(options.approved_runtime_lock == ROOT / LOCK_REL and options.approved_runtime_lock_sha256 == LOCK_SHA,
         'ONLY_IMMUTABLE_APPROVED_RUNTIME_LOCK')
    own_raw, own_identity, own_stamp = read_checked(Path(__file__))
    need(sha(own_raw) == options.driver_sha256, 'ROOT_DRIVER_HASH_DIFFERS')
    full = safe(ROOT / 'output' / FULL_NAME)
    context = {'root_lane_confirmed': True}
    proof_files = {}
    for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'), ('before', 'source-before.json'),
                      ('after', 'source-after.json'), ('committed', 'committed-source-blobs.json')):
        context[key], proof_files[key] = json_read(full / name)
    validate_full(context)  # Incomplete/failed full run stops before staging/runtime/process queries.
    qualified_path=safe(options.qualified_creation)
    need(qualified_path.is_relative_to(ROOT/'experiments'),'COMMITTED_PUBLIC_CREATION_RECEIPT_REQUIRED')
    qualified_raw,qualified_row,qualified_stamp=read_checked(qualified_path)
    need(sha(qualified_raw)==options.qualified_creation_sha256,'QUALIFIED_CREATION_RECEIPT_PIN_DIFFERS')
    validate_qualified_creation(strict_json(qualified_raw))

    proof_stamps = {}
    for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'), ('before', 'source-before.json'),
                      ('after', 'source-after.json'), ('committed', 'committed-source-blobs.json')):
        row = proof_files[key]
        _raw, identity, proof_stamps[key] = read_checked(full / name, (row['bytes'], row['sha256']))
        need(identity == row, 'FULL_PROOF_CHANGED_DURING_ADMISSION')
    need(proof_files['completion']['mtime_ns'] >= context['launch']['started_ns'] and
         proof_files['after']['mtime_ns'] >= context['launch']['started_ns'], 'FULL_TERMINAL_PROOFS_PREDATE_LAUNCH')
    need(source_snapshot(context['after']) == context['after'], 'CURRENT_SOURCE_BYTES_OR_NS_STAMPS_DIFFER')
    initial_git = git_proof()
    validate_git(initial_git, context)
    qualified_relative=qualified_path.relative_to(ROOT).as_posix()
    blob=retained_output(['git','rev-parse',initial_git['head']+':'+qualified_relative]).decode('ascii').strip()
    expected_blob=hashlib.sha1(b'blob '+str(len(qualified_raw)).encode()+b'\x00'+qualified_raw).hexdigest()
    need(blob==expected_blob,'QUALIFIED_CREATION_RECEIPT_NOT_COMMITTED_EXACT_BYTES')

    safe(ROOT / 'output')
    lock_path = ROOT / 'output/source-current-id-root-lane.lock'
    safe(lock_path, exists=False)
    lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    lock_stamp = None
    stage = None
    launched = preservation_done = physical_confirmed = False
    process = None
    success_result = None
    incremental_checks = {}
    register_file_check(incremental_checks,'qualified_creation',qualified_path,
        (qualified_row['bytes'],qualified_row['sha256']),qualified_row,qualified_stamp)
    incremental_checks['functional_source'] = lambda: source_snapshot(context['after']) == context['after']
    incremental_checks['head_and_committed_source'] = lambda: git_proof() == initial_git
    register_file_check(incremental_checks, 'driver', Path(__file__),
                        (len(own_raw), options.driver_sha256), own_identity, own_stamp)
    for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'), ('before', 'source-before.json'),
                      ('after', 'source-after.json'), ('committed', 'committed-source-blobs.json')):
        row = proof_files[key]
        register_file_check(incremental_checks, 'full_proof_' + key, full / name,
                            (row['bytes'], row['sha256']), row, proof_stamps[key])
    try:
        os.write(lock_fd, (str(os.getpid()) + '\n').encode())
        lock_stamp = stamp(os.fstat(lock_fd))
        stage = new_stage()
        for name in ('inputs', 'result', 'temp', 'user-config', 'user-scripts', 'user-datafiles', 'home'):
            (stage / name).mkdir()
        runtime_holder = {}
        def runtime_reader():
            runtime_holder.update(runtime_check(options.approved_runtime_lock))
            return runtime_holder
        admission = admit(context, source_reader=lambda: source_snapshot(context['after']), git_reader=git_proof,
                          physical_reader=lambda: observe_physical(stage, context['launch'], 'BEFORE'), runtime_reader=runtime_reader)
        incremental_checks['approved_runtime'] = lambda: runtime_check(options.approved_runtime_lock) == runtime_holder
        native_rows, originals, original_stamps, staged_stamps = {}, {}, {}, {}
        owned_B_row = None
        for role, (name, count, digest) in {**NATIVE, **PROVENANCE}.items():
            original = OLD / FAMILY / name
            raw, row, original_stamp = read_checked(original, (count, digest))
            originals[role], original_stamps[role] = row, original_stamp
            register_file_check(incremental_checks,'protected_original_'+role,original,(count,digest),row,original_stamp)
            if role in NATIVE or role == 'blend':
                destination = stage / 'inputs' / ('material-source.blend' if role == 'blend' else Path(name).name)
                incremental_checks['staged_expected_'+role] = lambda destination=destination,raw=raw: read_checked(destination)[0] == raw
                with destination.open('xb') as stream:
                    stream.write(raw)
                os.utime(destination, ns=(original.stat().st_atime_ns, row['mtime_ns']))
                _data, staged_identity, staged_stamp = read_checked(destination, (count, digest))
                need(staged_identity == row, 'STAGED_NATIVE_NS_MTIME_DIFFERS')
                staged_stamps[role] = staged_stamp
                register_file_check(incremental_checks,'staged_'+role,destination,(count,digest),staged_identity,staged_stamp)
                if role in NATIVE: native_rows[role] = dict(path=str(destination),bytes=count,sha256=digest)
                else: owned_B_row = dict(path=str(destination),bytes=count,sha256=digest)
        need(len(list((stage / 'inputs').iterdir())) == 4 and owned_B_row is not None,'EXACT_NATIVE_THREE_PLUS_OWNED_B_INPUTS')
        sources, prep_identities, prep_stamps = {}, {}, {}
        for role, path, expected in (('probe', HERE / 'fresh_carrier_probe.py', options.worker_sha256),
                                     ('ledger', HERE / 'current_id_ledger.py', options.ledger_sha256),
                                     ('metadata_reader', HERE / 'material_metadata.py', METADATA_PIN[1]),
                                     ('material_binding', HERE / 'material_binding.py', options.binding_sha256),
                                     ('enumeration_module', HERE / 'library_enumeration.py', ENUMERATION_PIN[1]),
                                     ('inspection_module', HERE / 'material_inspection.py', INSPECTION_PIN[1]),
                                     ('resolved_profile', HERE / 'resolved_profile.py', RESOLVED_PIN[1]),
                                     *((role,HERE/spec[0],spec[2]) for role,spec in CARRIER_MODULES.items())):
            raw, row, prep_stamp = read_checked(path)
            need(sha(raw) == expected, 'ROOT_PREP_SOURCE_HASH_DIFFERS')
            if role in CARRIER_MODULES:
                need((row['bytes'],row['sha256'])==tuple(CARRIER_MODULES[role][1:]),'FROZEN_CARRIER_HELPER_SOURCE_DIFFERS')
            if role in ('metadata_reader','material_binding','enumeration_module','inspection_module','resolved_profile'):
                expected_pin = {'metadata_reader':METADATA_PIN,'material_binding':BINDING_PIN,
                                'enumeration_module':ENUMERATION_PIN,'inspection_module':INSPECTION_PIN,'resolved_profile':RESOLVED_PIN}[role]
                need((row['bytes'], row['sha256']) == expected_pin, 'FROZEN_MATERIAL_HELPER_SOURCE_DIFFERS')
            sources[role] = dict(path=str(path), bytes=row['bytes'], sha256=row['sha256'])
            prep_identities[role], prep_stamps[role] = row, prep_stamp
            register_file_check(incremental_checks,'prep_source_'+role,path,(row['bytes'],row['sha256']),row,prep_stamp)
        sources['owned_B'] = owned_B_row
        sources['qualified_creation']=dict(path=str(qualified_path),bytes=qualified_row['bytes'],sha256=qualified_row['sha256'])
        graphics = dict(format='has_carrier_export_root_graphics_release_1', tested_revision=TESTED, current_head=admission['head'],
                        full_completion_sha256=proof_files['completion']['sha256'], full_launch_sha256=proof_files['launch']['sha256'],
                        full_suite_passed=True, functional_file_count=COUNT, exact_source_hash_bytes_nsmtime=True,
                        physical_observation_is_global_lease=False, exclusive_runtime_lease=True,
                        root_lane_explicitly_confirmed=True, one_owned_coordinator_lock=True,
                        observed_ns=admission['physical']['observed_ns'])
        graphics_row = remember_written_file(incremental_checks, 'worker_input_graphics_release',
            write_new(stage / 'graphics-release.json', graphics))
        closure = dict(admission['physical'], full_completion_sha256=proof_files['completion']['sha256'],
                       full_launch_sha256=proof_files['launch']['sha256'])
        closure_row = remember_written_file(incremental_checks, 'worker_input_physical_closure',
            write_new(stage / 'physical-closure.json', closure))
        full_state_row = dict(path=str(full / 'completion.json'), bytes=proof_files['completion']['bytes'],
                              sha256=proof_files['completion']['sha256'])
        catalogue = {name: {key: row[key] for key in ('bytes', 'sha256')}
                     for name, row in runtime_holder['sourceio_catalogue'].items()}
        lock_row = runtime_holder['lock']
        sources.update(full_state=full_state_row, graphics_release=graphics_row, physical_closure=closure_row,
                       approved_runtime_lock=dict(path=str(options.approved_runtime_lock), bytes=lock_row['bytes'], sha256=LOCK_SHA))
        now = dt.datetime.now(dt.timezone.utc)
        request = dict(format='has_fresh_source_native_carrier_export_request_1', phase='ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED',
                       created_utc=now.isoformat(), expires_utc=(now + dt.timedelta(minutes=30)).isoformat(),
                       private_arrays_public=False, files=sources, sourceio_root=str(SOURCEIO), sourceio_catalogue=catalogue,
                       owned_stage=str(stage), owned_output=str(stage / 'result'), owned_temp=str(stage / 'temp'), native=native_rows,
                       provenance_root_hashes={role: {key: originals[role][key] for key in ('bytes', 'sha256')} for role in PROVENANCE},
                       source_context=dict(full_suite_passed=True, full_job_physically_closed=True, exclusive_runtime_lease=True,
                                           observed_owned_processes=0, functional_file_count=COUNT,
                                           full_state_sha256=full_state_row['sha256'], graphics_release_sha256=graphics_row['sha256'],
                                           physical_closure_sha256=closure_row['sha256'], tested_revision=TESTED, current_head=admission['head']))
        request_row = remember_written_file(incremental_checks, 'worker_input_root_request',
            write_new(stage / 'ROOT_CARRIER_EXPORT_REQUEST.json', request))
        write_new(stage / 'PRIVATE_BEFORE.json', dict(originals=originals, native_staged=native_rows, runtime=runtime_holder,
                                                     full_proof_identities=proof_files, driver=own_identity, git=initial_git))
        env = os.environ.copy()
        for key in ('PYTHONPATH', 'PYTHONHOME', 'BLENDER_SYSTEM_SCRIPTS', 'BLENDER_SYSTEM_DATAFILES', 'BLENDER_SYSTEM_PYTHON'):
            env.pop(key, None)
        env.update(TEMP=str(stage / 'temp'), TMP=str(stage / 'temp'), PYTHONDONTWRITEBYTECODE='1',
                   PYTHONNOUSERSITE='1', BLENDER_USER_CONFIG=str(stage / 'user-config'),
                   BLENDER_USER_SCRIPTS=str(stage / 'user-scripts'), BLENDER_USER_DATAFILES=str(stage / 'user-datafiles'),
                   HOME=str(stage / 'home'), USERPROFILE=str(stage / 'home'))
        command = [str(PYTHONW), '-B', str(ROOT / 'tools/private_desktop.py'), '--receipt', str(stage / 'private-desktop.json'),
                   '--timeout', '150', '--memory-limit-mib', '4096', '--', str(BLENDER), '--background', '--factory-startup',
                   '--disable-autoexec', '--offline-mode', '--python-exit-code', '1', '--python', str(HERE / 'fresh_carrier_probe.py'),
                   '--', '--request', str(stage / 'ROOT_CARRIER_EXPORT_REQUEST.json'), '--request-sha256', request_row['sha256']]
        # Recheck the physical/source lane immediately before the sole native job.
        need(source_snapshot(context['after']) == context['after'] and git_proof() == initial_git, 'PRELAUNCH_SOURCE_OR_HEAD_CHANGED')
        observe_physical(stage, context['launch'], 'PRELAUNCH')
        with (stage / 'PRIVATE_stdout.log').open('xb') as out, (stage / 'PRIVATE_stderr.log').open('xb') as err:
            process = subprocess.Popen(command, cwd=stage, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            launched = True
            wait_recorded_owned(process, lambda: write_new(stage / 'PRIVATE_launch.json', dict(
                pid=process.pid, coordinator_pid=os.getpid(), command=command,
                started_ns=time.time_ns(), visible_fallback=False)))
        need(process.poll() is not None, 'OWNED_LAUNCHER_NOT_REAPED')
        desktop, desktop_identity = json_read(stage / 'private-desktop.json', 64 * 1024)
        need(type(desktop.get('child_pid')) is int and desktop['child_pid'] > 0, 'OWNED_NATIVE_PID_REQUIRED')
        final_physical = observe_physical(stage, dict(pid=process.pid, coordinator_pid=context['launch']['coordinator_pid'],
                                                      extra_absent_pids=[desktop['child_pid'], context['launch']['pid']]), 'AFTER')
        validate_fresh_physical(final_physical)
        physical_confirmed = True
        # Preservation is checked even for an unsuccessful worker, before result qualification.
        need(source_snapshot(context['after']) == context['after'] and git_proof() == initial_git, 'POSTRUN_SOURCE_OR_HEAD_CHANGED')
        need(runtime_check(options.approved_runtime_lock) == runtime_holder, 'POSTRUN_RUNTIME_OR_SOURCEIO_CHANGED')
        for role, (name, count, digest) in {**NATIVE, **PROVENANCE}.items():
            _raw, row, identity_stamp = read_checked(OLD / FAMILY / name, (count, digest))
            need(row == originals[role] and identity_stamp == original_stamps[role], 'ORIGINAL_NATIVE_OR_PROVENANCE_CHANGED')
            if role in NATIVE or role == 'blend':
                staged_row = native_rows[role] if role in NATIVE else owned_B_row
                _raw, staged, staged_stamp = read_checked(staged_row['path'], (count, digest))
                need(staged == row and staged_stamp == staged_stamps[role], 'STAGED_NATIVE_CHANGED')
        for role in ('probe','ledger','metadata_reader','material_binding','enumeration_module','inspection_module','resolved_profile',*CARRIER_MODULES):
            _raw, prep_identity, prep_stamp = read_checked(sources[role]['path'], (sources[role]['bytes'], sources[role]['sha256']))
            need(prep_identity == prep_identities[role] and prep_stamp == prep_stamps[role], 'ROOT_PREP_SOURCE_STAMP_CHANGED')
        _raw, identity, final_stamp = read_checked(Path(__file__), (len(own_raw), options.driver_sha256))
        need(identity == own_identity and final_stamp == own_stamp, 'ROOT_DRIVER_CHANGED')
        for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'), ('before', 'source-before.json'),
                          ('after', 'source-after.json'), ('committed', 'committed-source-blobs.json')):
            _value, row = json_read(full / name)
            need(row == proof_files[key], 'FULL_PROOF_CHANGED_DURING_PROBE')
        preservation_done = True
        for label in ('worker_input_graphics_release', 'worker_input_physical_closure', 'worker_input_root_request'):
            need(incremental_checks[label]() is True, 'NEW_WORKER_INPUT_PROOF_CHANGED')
        result, result_identity = json_read(stage / 'result/PUBLIC_CARRIER_EXPORT.json', 64 * 1024)
        placement, placement_identity = json_read(stage / 'result/PLACEMENT_CARRIER_EXPORT.json', 64 * 1024)
        observation = validate_result(result,placement,desktop,process.returncode)
        validate_owned_B_report(result,expected_owned_path=owned_B_row['path'])
        need(result.get('root_attested_hash_only_provenance') == request['provenance_root_hashes'],
             'WORKER_ROOT_HASH_ONLY_PROVENANCE_DIFFERS')
        # Hash-bound worker reports must describe precisely this request's rows.
        expected_inputs = {role: {key: row[key] for key in ('bytes', 'sha256')} for role, row in sources.items()}
        expected_inputs['root_request'] = {key: request_row[key] for key in ('bytes', 'sha256')}
        for role, name in (('join_policy', next(iter(HELPERS))), ('native_helper', list(HELPERS)[1]),
                           ('instrumentation', list(HELPERS)[2]), ('sentinel_source', list(HELPERS)[3])):
            expected_inputs[role] = dict(bytes=HELPERS[name][0], sha256=HELPERS[name][1])
        importer = catalogue['blender_bindings/models/mdl49/import_mdl.py']
        expected_inputs['importer'] = importer
        expected_inputs['blender_exe'] = dict(bytes=RUNTIME_PINS[str(BLENDER)][0], sha256=RUNTIME_PINS[str(BLENDER)][1])
        expected_inputs.update({'staged/' + role: {key: row[key] for key in ('bytes', 'sha256')} for role, row in native_rows.items()})
        need(result['input_identities'] == expected_inputs, 'WORKER_INPUT_HASH_BINDING_DIFFERS')
        expected_catalogue = {'sourceio/' + name: row for name, row in catalogue.items()}
        need(result['sourceio_catalogue_summary_sha256'] == sha(json.dumps(expected_catalogue, sort_keys=True, separators=(',', ':')).encode()),
             'WORKER_SOURCEIO_CATALOGUE_HASH_DIFFERS')
        exported=result['carrier_export']
        carrier_path=stage/'result/carrier.glb'
        carrier_raw=read_private_carrier(carrier_path,exported['carrier_glb_bytes'],exported['carrier_glb_sha256'])
        _raw,carrier_row,carrier_stamp=read_checked(carrier_path,(exported['carrier_glb_bytes'],exported['carrier_glb_sha256']),limit=128*1024*1024)
        need(_raw==carrier_raw,'PRIVATE_CARRIER_CHANGED_BETWEEN_READS')
        register_file_check(incremental_checks,'private_carrier_glb',carrier_path,
            (carrier_row['bytes'],carrier_row['sha256']),carrier_row,carrier_stamp)
        baseline_raw,baseline_row,baseline_stamp=read_checked(OLD/FAMILY/PROVENANCE['glb'][0],tuple(PROVENANCE['glb'][1:]))
        need(baseline_row==originals['glb'] and baseline_stamp==original_stamps['glb'],'ORIGINAL_BASELINE_CHANGED_BEFORE_COMPARISON')
        domain_module=load_root_comparison_helpers(incremental_checks)
        relation_path=stage/'result/PRIVATE_PRIMITIVE_IDS.json'
        relation_raw,relation_row,relation_stamp=read_checked(relation_path,limit=16*1024*1024)
        need(sha(relation_raw)==exported['private_relation_sha256'],'PRIVATE_OBSERVED_RELATION_DIGEST_DIFFERS')
        register_file_check(incremental_checks,'private_observed_relation',relation_path,
            (relation_row['bytes'],relation_row['sha256']),relation_row,relation_stamp)
        relation=strict_json(relation_raw)
        canonical_relation=json.dumps(relation,sort_keys=True,separators=(',',':')).encode()
        need(sha(canonical_relation)==exported['export_observation']['actual_export_binding']['private_relation_sha256'],
             'PRIVATE_RELATION_DIFFERS_FROM_INDEPENDENT_OBSERVER_BINDING')
        normal_module,native_module=load_root_normal_helpers(incremental_checks)
        native_refs={}
        for role,(name,count,digest) in NATIVE.items():
            native_raw,native_row,native_stamp=read_checked(OLD/FAMILY/name,(count,digest))
            need(native_row==originals[role] and native_stamp==original_stamps[role],'NATIVE_NORMAL_SOURCE_CHANGED')
            native_refs[role]=dict(raw=native_raw,bytes=count,sha256=digest)
        native_source=native_module.derive_native_point_rows(native_refs)
        comparisons=run_carrier_comparisons(baseline_raw,carrier_raw,relation,native_source,
            result['normal_transport_frame'],domain_module,normal_module)
        write_new(stage/'STRICT_CARRIER_COMPARISONS.json',comparisons)
        need(comparisons['passed'],'STRICT_CARRIER_COMPARISON_GATES_FAILED')
        semantic_report=comparisons['non_NORMAL'];normal_report=comparisons['raw_normal']
        need(normal_report.get('format')=='has_exact_carrier_native_normal_measurement_1' and
             normal_report.get('measured') is True and
             normal_report.get('source_normal_metric')=='raw_unnormalized_euclidean_vector_distance' and
             type(normal_report.get('source_normal_threshold')) is float and normal_report['source_normal_threshold']==2e-5 and
             type(normal_report.get('source_normal_max_euclidean_error')) is float and
             math.isfinite(normal_report['source_normal_max_euclidean_error']) and
             0.0<=normal_report['source_normal_max_euclidean_error']<=2e-5,
             'ORIGINAL_RAW_EUCLIDEAN_NORMAL_GATE_REQUIRED')
        need(all(check() is True for check in incremental_checks.values()),'FINAL_ROOT_COMPARISON_INPUT_PRESERVATION_FAILED')
        public = dict(format='has_root_fresh_source_native_carrier_export_run_1', status='CURRENT_IDS_MATERIALS_AND_ACTUAL_CARRIER_EXPORTED',
                      tested_full_revision=TESTED, current_source_head=admission['head'], functional_source_count=COUNT,
                      whole_full_pass_required=True, private_job_closed=True, launcher_reaped=True,
                      fresh_physical_after=final_physical, hidden_placement_verified=True,
                      models=2, points=9661, corners=42702, sourceio_files=574, exact_worker_reads=605,
                      original_and_staged_hash_bytes_nsmtime_unchanged=True, source_and_head_unchanged=True,
                      historical_saved_B_native_causality_qualified=False, normal_fidelity_qualified=False,
                      exporter_qualified=False, carrier_qualified=False, non_normal_semantic_equivalence_qualified=False,
                      application_adoption_qualified=False, native_fidelity_qualified=False,
                      original_B_scene_opened=False,material_library_appended=True,
                      exporter_invoked=True,carrier_written=True,blend_saved=False,native_arrays_published=False,
                      worker_result=result_identity, placement_result=placement_identity, desktop_result=desktop_identity,
                      observation=observation, material_binding=result['material_binding'],
                      inherited_authenticated_reads=590, exact_authenticated_reads=605,
                      resolved_native_default_skin_equivalence_qualified=False, B_dependency_closure_qualified=False,
                      material_resources_loaded=True,owned_B_enumeration=result['owned_B_enumeration'],
                      owned_B_inspection=result['owned_B_inspection'],
                      native_material_path_witness=result['native_material_path_witness'],
                      preloaded_resolver_runtime_attestation=result['preloaded_resolver_runtime_attestation'],
                      readonly_preloaded_material_adaptation=result['readonly_preloaded_material_adaptation'],
                      all_four_source_materials_reuse_admitted_B_refs=True,
                      carrier_export=result['carrier_export'],bounded_image_buffer_readiness=result['bounded_image_buffer_readiness'],
                      actual_carrier_output_generated=True,strict_non_NORMAL_comparison_qualified=True,
                      strict_non_NORMAL_report=semantic_report,source_normal_threshold_unchanged=2e-5,
                      raw_normal_error_measured=True,normal_gate_passed=True,
                      source_normal_metric='raw_unnormalized_euclidean_vector_distance',raw_normal_report=normal_report)
        success_result = public  # Publish only after exact owned lock cleanup below.
    finally:
        primary_error = sys.exc_info()[1]
        failed_audit = None
        if primary_error is not None and stage is not None:
            # Cover every post-Popen exception, including launch-record failures.
            # Only this retained owned handle is ever killed/waited here.
            launcher_reaped = process is not None and reap_owned_launcher(process)
            # A failing worker/receipt/timeout must not bypass the source and
            # protected-original readback. Each independent check is attempted;
            # this scalar failure audit is never native-fidelity qualification.
            checks = dict(incremental_checks)
            failed_audit = failed_run_audit(checks, primary_error=primary_error,
                launcher_reaped=launcher_reaped,
                native_launch_attempted=launched,
                worker_receipt_present=(stage / 'private-desktop.json').is_file(),
                closure_observer=lambda: observe_physical(stage, dict(
                    pid=process.pid if process is not None else context['launch']['pid'], coordinator_pid=context['launch']['coordinator_pid'],
                    extra_absent_pids=[context['launch']['pid']]), 'FAILED'))
            physical_confirmed = failed_audit['physical_closure_confirmed']
        close_error = None
        try:
            os.close(lock_fd)
        except BaseException as error:
            close_error = error
        # Preserve the exact owned lock if closure is unproven. A later Root
        # must inspect it; a subsequent invocation never auto-unlinks a lock.
        lock_removed = False
        lock_error = close_error
        if lock_stamp is not None and (not launched or physical_confirmed):
            try:
                safe(lock_path)
                need(stamp(lock_path.lstat()) == lock_stamp, 'OWNED_LOCK_CHANGED_NOT_REMOVED')
                lock_path.unlink()
                lock_removed = True
            except BaseException as error:
                lock_error = error
        if failed_audit is not None:
            failed_audit['owned_lock_retained'] = not lock_removed
            failed_audit['owned_lock_cleanup_refused'] = lock_error is not None
            # Failed native work remains failed even if closure is confirmed and
            # the owned file was removed. No runtime-lane release claim is made.
            failed_audit['runtime_lane_released'] = False
            try:
                write_new(stage / 'PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json', failed_audit)
            except BaseException:
                pass
        if lock_error is not None and primary_error is None:
            raise Refusal('OWNED_LOCK_CLEANUP_REFUSED')
    need(success_result is not None and lock_removed and physical_confirmed,'COMBINED_SUCCESS_AFTER_CLOSURE_REQUIRED')
    write_new(stage/'PUBLIC_CARRIER_EXPORT_ROOT_RESULT.json',success_result)
    print(json.dumps(dict(status=success_result['status'],models=2,points=9661,corners=42702,folder=stage.name)),flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Refusal, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        # No original paths, owner data, command logs or native arrays in stdout.
        code = str(error) if isinstance(error, Refusal) else type(error).__name__
        print(json.dumps(dict(status='REFUSED', code=code)), flush=True)
        raise SystemExit(1)
