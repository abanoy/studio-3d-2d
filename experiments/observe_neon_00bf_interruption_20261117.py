"""Root-only restart observation. Never invent a terminal state or process exit."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-00bf0f9-20261117T044200'
HELPER = ROOT / 'experiments/neon_00bf_terminal_20261117'
REV = '00bf0f916a549f5e858cb39dd91a149071fd5181'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda p: json.loads(p.read_bytes())
assert sha((HELPER / 'close_terminal.py').read_bytes()) == 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'
assert sha((HELPER / 'legacy_result_gates.py').read_bytes()) == '0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
sys.path.insert(0, str(HELPER))
spec = importlib.util.spec_from_file_location('sealed_restart_scope_observer', HELPER / 'close_terminal.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
context = load(HELPER / 'CONTEXT.json')
assert context['commit'] == REV
for name, pin in context['immutable_run_inputs'].items():
    assert sha((RUN / name).read_bytes()) == pin
state_raw = (RUN / 'state.json').read_bytes()
state = json.loads(state_raw)
assert state['status'] == 'running' and state['source_commit'] == REV
assert not (RUN / 'source-after.json').exists(), 'Do not reclassify an actual terminal run'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW).decode().strip() == REV
before = load(RUN / 'source-before.json')
observer.validate_current_sources(before)
scope_before = observer.observe()  # Only the unchanged read-only absence/scope observer.
boot_code = "@{observed_utc=[DateTime]::UtcNow.ToString('o'); last_boot_utc=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')} | ConvertTo-Json -Compress"
proc = subprocess.Popen([str(observer.PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', boot_code],
    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW)
stdout, stderr = proc.communicate(timeout=60)
assert proc.returncode == 0 and not stderr.strip()
boot = json.loads(stdout)
assert observer.ns(state['started_utc']) < observer.ns(boot['last_boot_utc']) <= observer.ns(boot['observed_utc'])

# Freeze generated text metadata before another run can reuse top-level reports.
# This private snapshot never becomes a public evidence packet.
start = observer.ns(state['started_utc'])
end = observer.ns(boot['observed_utc'])
selected = []
excluded_reparse = []
for base_name, directories, files in os.walk(REVIEW / 'output', followlinks=False):
    base = observer.safe(Path(base_name))
    for name in list(directories):
        path = base / name
        stamp = path.lstat()
        if stat.S_ISLNK(stamp.st_mode) or getattr(stamp, 'st_file_attributes', 0) & 0x400:
            directories.remove(name)
            excluded_reparse.append(path.relative_to(REVIEW / 'output').as_posix())
    for name in files:
        path = base / name
        if path.suffix.lower() not in ('.json', '.log'):
            continue
        stamp = path.lstat()
        if not stat.S_ISREG(stamp.st_mode) or getattr(stamp, 'st_file_attributes', 0) & 0x400:
            excluded_reparse.append(path.relative_to(REVIEW / 'output').as_posix())
            continue
        if start <= stamp.st_mtime_ns <= end:
            observer.safe(path)
            assert stamp.st_size <= 64 * 1024 * 1024
            selected.append((path, stamp))
assert 0 < len(selected) <= 8192
assert sum(stamp.st_size for _, stamp in selected) <= 512 * 1024 * 1024
target = ROOT / 'output' / ('PRIVATE-neon-00bf-interrupted-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
target.mkdir(exist_ok=False)
(target / 'objects').mkdir()
bindings = []
for path, stamp in sorted(selected):
    raw = path.read_bytes()
    after = path.stat()
    assert (stamp.st_size, stamp.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    digest = sha(raw)
    packed = gzip.compress(raw, compresslevel=6, mtime=0)
    obj = target / 'objects' / (digest + '.gz')
    if not obj.exists():
        obj.write_bytes(packed)
    else:
        assert obj.read_bytes() == packed
    bindings.append({'path': path.relative_to(REVIEW / 'output').as_posix(), 'bytes': len(raw),
        'sha256': digest, 'mtime_ns': stamp.st_mtime_ns, 'object': 'objects/' + obj.name})
observer.validate_current_sources(before)
scope_after = observer.observe()
assert (RUN / 'state.json').read_bytes() == state_raw
record = {
    'format': 'has_root_interrupted_run_after_OS_restart_1',
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'run': str(RUN), 'source_commit': REV, 'boot_observation': boot,
    'scope_before': scope_before, 'scope_after': scope_after,
    'original_state_sha256': sha(state_raw), 'original_state_unchanged': True,
    'functional_source_files_unchanged': 1029,
    'result': 'INTERRUPTED_NO_TERMINAL_RESULT', 'suite_exit': None,
    'full_pass_claimed': False, 'graceful_private_job_closure_certified': False,
    'old_OS_resources_ceased_and_current_scopes_empty': True,
    'root_issued_termination': False, 'new_native_lane_available_after_restart': True,
    'snapshot_private_not_publication_authority': True, 'private_metadata_bindings': bindings,
    'excluded_reparse_paths_not_opened': excluded_reparse,
    'script_sha256': sha(Path(__file__).read_bytes()),
    'sealed_scope_observer_sha256': sha((HELPER / 'close_terminal.py').read_bytes()),
}
with (target / 'INTERRUPTION.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps({'private_snapshot': str(target), 'result': record['result'], 'source_files': 1029,
    'metadata_files': len(bindings), 'uncompressed_bytes': sum(row['bytes'] for row in bindings),
    'boot_utc': boot['last_boot_utc'], 'current_scopes_empty': True, 'original_state_unchanged': True}))
