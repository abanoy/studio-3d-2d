"""Root CPU-only repeat; creates only synthetic temporary files and evidence."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import time

root = Path(__file__).resolve().parent.parent
folder = root / 'output/source-current-id-prep-20261120'
out = root / 'output/source-current-id-driver-qualification-20261120-02'
assert not out.exists()
out.mkdir()
pins = {
    'run_probe.py': 'f33f979adf71835c6a06701470bb58c7919d0108f7bfd056e876223a9f78f9b1',
    'test_probe_driver.py': 'da1b656d0b8d0d9746d247df563bde811e8354614d95d2d8f54e81368fe2a432',
    'fresh_current_id_probe.py': 'b9ad16319fe6211cffafc08704de78482271eaff28326e9499fc418db583f0bf',
    'current_id_ledger.py': 'ab2d0d3076f63d6a398b209a5a39c2334f3b00664c0fa38d152d4587a54ffee9',
}


def snapshot():
    rows = {}
    for name, digest in pins.items():
        path = folder / name
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, name
        rows[name] = dict(bytes=len(data), sha256=digest, mtime_ns=path.stat().st_mtime_ns)
    return rows


before = snapshot()
started = time.monotonic()
with (out / 'stdout.log').open('wb') as so, (out / 'stderr.log').open('wb') as se:
    child = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', 'discover',
                            '-s', str(folder), '-p', 'test_probe_driver.py', '-v'],
                           cwd=root, stdout=so, stderr=se,
                           creationflags=subprocess.CREATE_NO_WINDOW)
after = snapshot()
log = (out / 'stderr.log').read_text(encoding='utf-8')
match = re.search(r'Ran (\d+) tests? in ([0-9.]+)s', log)
count = int(match.group(1)) if match else 0
result = dict(format='has_current_native_id_driver_cpu_1',
              application_source_commit='9e3b039039833adce4723bbb70681595cd4eef16',
              exit=child.returncode, unittest_methods=count,
              unittest_seconds=float(match.group(2)) if match else None,
              wall_seconds=time.monotonic() - started,
              passed=child.returncode == 0 and count == 51 and log.rstrip().endswith('OK') and before == after,
              source_hash_size_nsmtime_unchanged=before == after, sources=before,
              actual_Blender_SourceIO_CIM_Git_or_native_calls=False,
              native_inputs_or_captures_opened=False,
              actual_native_IDs_normal_or_export_qualified=False,
              host_context_repeat=True,
              predecessor='source-current-id-driver-qualification-20261120-01',
              predecessor_error='WinError5 creating a synthetic temporary hard link; guard not exercised',
              assertions_or_source_changed_for_repeat=False,
              stderr_sha256=hashlib.sha256((out / 'stderr.log').read_bytes()).hexdigest(),
              stdout_sha256=hashlib.sha256((out / 'stdout.log').read_bytes()).hexdigest())
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(log)
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
