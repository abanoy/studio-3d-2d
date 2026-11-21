"""Existing editor regressions after the usable feature additions.

This is a bounded selection from verify.py, not the complete canonical suite.
"""
from pathlib import Path
import array
import io
import json
import math
import os
import struct
import subprocess
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command


def main():
    if os.name != 'nt':
        raise RuntimeError('Use the private Windows test launcher')
    folder = ROOT / 'output' / ('feature-regressions-' + str(time.time_ns()))
    folder.mkdir()
    # Same generated audio prerequisites as the selected verify.py cases.
    fixtures = ROOT / 'output' / 'fixtures'
    fixtures.mkdir(exist_ok=True)
    samples = array.array('h', (int(16000 * math.sin(2 * math.pi * 1000 * n / 44100)) for n in range(22050)))
    if sys.byteorder != 'little':
        samples.byteswap()
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
        wav.writeframes(samples.tobytes())
    payload = b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 3, 1, 44100, 176400, 4, 32) + b'data' + struct.pack('<I', 400) + bytes(400)
    for name, data in [('voice — тест.wav', buffer.getvalue()), ('float.wav', b'RIFF' + struct.pack('<I', len(payload)) + payload)]:
        target = fixtures / name
        if target.exists():
            assert target.read_bytes() == data, 'Preserve an unexpected existing fixture: ' + str(target)
        else:
            target.write_bytes(data)
    result = {'status': 'RUNNING', 'complete_canonical_suite': False, 'cases': {}}
    cases = [
        ('ui', None, ['--ui-smoke'], 'UI_SMOKE '),
        ('editor', None, ['--smoke'], 'APP_SMOKE '),
        ('pose', None, ['--pose-smoke'], 'POSE_SMOKE '),
        ('world_selection', 'tests/world_selection_smoke.gd', [], 'WORLD_SELECTION_SMOKE '),
        ('recovery_write', None, ['--recovery-smoke', '--recovery-write'], 'RECOVERY_WRITE failures=0'),
        ('recovery', None, ['--recovery-smoke'], 'RECOVERY_SMOKE '),
        ('world_runtime', 'tests/world_runtime_smoke.gd', [], 'WORLD_RUNTIME_SMOKE '),
        ('secondary_motion', 'tests/secondary_motion_smoke.gd', [], 'SECONDARY_MOTION '),
        ('fan_motion', 'tests/fan_motion_smoke.gd', [], 'FAN_MOTION '),
    ]
    try:
        for name, script, flags, marker in cases:
            log = folder / (name + '-engine.log')
            extra = ['--log-file', str(log)]
            if script is None:
                extra += ['--', *flags, '--demo-room']
            args = command(script, extra=extra)
            began = time.monotonic()
            process = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=290,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            raw = process.stdout + process.stderr
            (folder / (name + '-launcher.log')).write_bytes(raw)
            text = log.read_text(encoding='utf-8', errors='replace')
            receipt = json.loads(Path(args[args.index('--receipt') + 1]).read_bytes())
            row = {'exit': process.returncode, 'seconds': round(time.monotonic() - began, 3), 'private_receipt': receipt}
            result['cases'][name] = row
            assert process.returncode == 0, text
            assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and receipt['private_window_seen']
            assert not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested']
            assert receipt['job_closed'] and receipt['desktop_closed']
            assert not any(error in text for error in ['SCRIPT ERROR', 'SHADER ERROR', 'Shader compilation failed', 'FAIL ', 'ObjectDB instances leaked']), text
            lines = [line for line in text.splitlines() if line.startswith(marker)]
            assert len(lines) == 1, text
            if name != 'recovery_write':
                details = json.loads(lines[0][len(marker):])
                assert details['failures'] == 0, text
                row['checks'] = details['checks']
            row['skips'] = [line for line in text.splitlines() if line.startswith('SKIP ')]
            row['status'] = 'PASS'
            print('PASS', name, row.get('checks', ''), flush=True)
        result['status'] = 'PASS'
    except BaseException as error:
        result['status'] = 'FAIL'
        result['error'] = str(error)
        raise
    finally:
        (folder / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(str(folder), flush=True)


if __name__ == '__main__':
    main()
