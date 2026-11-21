"""Ordinary headless character-parts flow; generated assets, no native fidelity claim."""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from run import command


def windows_case(args, output, env):
    # Reuse the approved handle API; these limits belong only to this test.
    # A waiting trusted wrapper is assigned before it can start Godot/children.
    from wind_preview_owned import NativeJob
    from private_desktop import ExtendedLimits
    from ctypes import wintypes as W

    class Accounting(ctypes.Structure):
        _fields_ = [(name, ctypes.c_int64) for name in
                    ('user', 'kernel', 'period_user', 'period_kernel')] + [
                    (name, W.DWORD) for name in ('faults', 'total', 'active', 'terminated')]

    owner = NativeJob(ROOT)
    process = None
    exit_code = None
    active = None
    try:
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x8 | 0x200
        limits.BasicLimitInformation.ActiveProcessLimit = 16
        limits.JobMemoryLimit = 4 * 1024 * 1024 * 1024
        if not owner.configure(owner.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise OSError(ctypes.get_last_error(), 'Configure test descendant budget')
        query = owner.kernel.QueryInformationJobObject
        query.restype = W.BOOL
        query.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD)]

        def active_count():
            value = Accounting(); length = W.DWORD()
            if not query(owner.handle, 1, ctypes.byref(value), ctypes.sizeof(value), ctypes.byref(length)) or length.value != ctypes.sizeof(value):
                raise RuntimeError('Cannot query owned test descendants')
            return value.active

        worker = (
            "import json,subprocess,sys; "
            "assert sys.stdin.buffer.readline()==b'START\\n' and sys.stdin.buffer.read(1)==b''; "
            "p=subprocess.Popen(json.loads(sys.argv[1]),cwd=sys.argv[2],stdout=sys.stdout,stderr=sys.stderr,creationflags=subprocess.CREATE_NO_WINDOW); "
            "sys.exit(p.wait(timeout=115))"
        )
        with (output/'process-stdout.log').open('xb') as stdout, (output/'process-stderr.log').open('xb') as stderr:
            process = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', worker,
                                        json.dumps(args), str(ROOT)], cwd=ROOT, env=env,
                                       stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            identity = owner.identity(process)
            owner.assign(process)
            if active_count() != 1:
                raise RuntimeError('Only the waiting test wrapper may precede START')
            process.stdin.write(b'START\n'); process.stdin.close()
            exit_code = process.wait(timeout=125)
            if owner.identity(process) != identity:
                raise RuntimeError('Retained test process identity changed')
    finally:
        if owner.assigned:
            owner.terminate()
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            process._handle.Close()
        if owner.assigned:
            deadline = time.monotonic()+5
            while active_count() and time.monotonic() < deadline:
                time.sleep(.05)
            active = active_count()
        owner.close()
        (output/'ownership.json').write_text(json.dumps({
            'exit': exit_code, 'wrapper_reaped': process is not None and process.returncode is not None,
            'active_zero': active == 0, 'job_closed': owner.closed}), encoding='utf-8')
    if active != 0 or not owner.closed:
        raise RuntimeError('Character-parts test descendants did not close')
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    output = options.output or ROOT/'output'/('character-parts-'+str(time.time_ns()))
    output = output.resolve(); output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', HYBRID_PYTHON=sys.executable)
    for key, leaf in (('APPDATA', 'Roaming'), ('LOCALAPPDATA', 'Local')):
        folder = output/leaf; folder.mkdir(); env[key] = str(folder)
    engine_log = output/'engine.log'
    args = command('tests/character_parts_feature_smoke.gd', headless=True,
                   extra=['--audio-driver', 'Dummy', '--log-file', str(engine_log)])
    if os.name == 'nt':
        code = windows_case(args, output, env)
    else:
        completed = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, timeout=125)
        code = completed.returncode
        (output/'process-stdout.log').write_bytes(completed.stdout)
        (output/'process-stderr.log').write_bytes(completed.stderr)
    text = engine_log.read_text(encoding='utf-8', errors='replace')
    marker = 'CHARACTER_PARTS_FEATURE '
    rows = [json.loads(line[len(marker):]) for line in text.splitlines() if line.startswith(marker)]
    if code != 0 or re.search(r'SCRIPT ERROR|^ERROR:|^FAIL |ObjectDB instances leaked', text, re.M) or rows != [{'checks': 22, 'failures': 0}] or len(re.findall(r'^PASS ', text, re.M)) != 22:
        raise RuntimeError('Character-parts flow failed; see '+str(output))
    result = {'status': 'PASS', 'checks': 22, 'headless': True,
              'directory_save_reload': True, 'packed_has_cold_qualified': False,
              'native_conversion_qualified': False, 'output': str(output)}
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
