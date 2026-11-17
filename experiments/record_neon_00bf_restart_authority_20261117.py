"""Root-only facts permitting a fresh run after an OS restart, never a full pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-00bf0f9-20261117T044200'
HELPER = ROOT / 'experiments/neon_00bf_terminal_20261117'
REV = '00bf0f916a549f5e858cb39dd91a149071fd5181'
PRIVATE = ROOT / 'output/PRIVATE-neon-00bf-interrupted-bounded-20261117T154921/INTERRUPTED-INVENTORY.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert sha((HELPER / 'close_terminal.py').read_bytes()) == 'c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'
assert sha((HELPER / 'legacy_result_gates.py').read_bytes()) == '0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
sys.path.insert(0, str(HELPER))
spec = importlib.util.spec_from_file_location('sealed_interrupted_absence_observer', HELPER / 'close_terminal.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
context = observer.CONTEXT
assert context['commit'] == REV
for name, pin in context['immutable_run_inputs'].items():
    assert sha((RUN / name).read_bytes()) == pin
state_raw = (RUN / 'state.json').read_bytes()
state = json.loads(state_raw)
assert state['status'] == 'running' and state['source_commit'] == REV
assert not (RUN / 'source-after.json').exists()
before_raw = (RUN / 'source-before.json').read_bytes()
before = json.loads(before_raw)
observer.validate_current_sources(before)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW).decode().strip() == REV
assert sha(PRIVATE.read_bytes()) == '6ea95acc9b13af6bec50781eb705a414e8640282c4b3aa09f67db28cc385fefa'
freeze = json.loads(PRIVATE.read_bytes())
assert freeze['metadata_files'] == 215 and freeze['metadata_bytes'] == 1278549
assert freeze['full_suite_passed'] is False and freeze['final_full_report_used'] is False
assert freeze['suite_exit'] is None and freeze['all_old_jobs_gracefully_closed'] == 'unknown'
assert freeze['interrupted_or_unwritten_receipts'] == 'unknown' and freeze['unresolved_gaps'] == []
scope = observer.observe()
code = "@{observed_utc=[DateTime]::UtcNow.ToString('o');last_boot_utc=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')} | ConvertTo-Json -Compress"
p = subprocess.Popen([str(observer.PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', code],
    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
out, err = p.communicate(timeout=60)
assert p.returncode == 0 and not err.strip()
boot = json.loads(out)
assert observer.ns(state['started_utc']) < observer.ns(boot['last_boot_utc']) <= observer.ns(boot['observed_utc'])
observer.validate_current_sources(before)
assert (RUN / 'state.json').read_bytes() == state_raw
proof = {
    'format': 'has_root_same_candidate_restart_authority_1',
    'observed_utc': datetime.now(timezone.utc).isoformat(), 'revision': REV,
    'checkout': str(REVIEW), 'interrupted_run': str(RUN),
    'interrupted_state_sha256': sha(state_raw), 'interrupted_state_status': 'running',
    'suite_exit': None, 'terminal_result_fabricated': False,
    'known_boot_observations': [
        {'observed_utc': '2026-11-17T13:33:41.2525668Z', 'last_boot_utc': '2026-11-17T13:29:40.5000000Z'},
        {'observed_utc': '2026-11-17T15:46:49.6912177Z', 'last_boot_utc': '2026-11-17T15:44:12.5000000Z'},
    ],
    'latest_boot_observation': boot, 'current_scope_observation': scope,
    'source_files': 1029, 'source_hashes_current_unchanged': True,
    'source_before_sha256': sha(before_raw),
    'private_freeze_manifest_path': str(PRIVATE), 'private_freeze_manifest_sha256': sha(PRIVATE.read_bytes()),
    'metadata_frozen': True, 'native_lane_available_after_OS_restart': True,
    'all_old_jobs_gracefully_closed': 'unknown', 'full_pass_claimed': False,
    'root_issued_termination': False, 'observer_script_sha256': sha(Path(__file__).read_bytes()),
}
folder = ROOT / 'experiments/neon_00bf_OS_interruptions_20261117'
folder.mkdir(exist_ok=False)
path = folder / 'RESTART_AUTHORITY.json'
with path.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, indent=2)
    stream.write('\n')
print(json.dumps({'proof': str(path), 'sha256': sha(path.read_bytes()), 'sources_unchanged': 1029,
    'scope_empty': True, 'old_result': 'INTERRUPTED_NO_TERMINAL_RESULT', 'new_run_permitted': True}))
