"""Execute the reviewed filesystem-only builder; no engine or GUI is launched."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent


def main():
    command_file = ROOT / 'experiments/resume_full_20261115/builder/command.json'
    command = json.loads(command_file.read_bytes())['command']
    assert command[:2] == [r'C:\Program Files\Python313\python.exe', '-B']
    assert command[2] == str(ROOT / 'experiments/resume_full_20261115/builder/build_after_full.py')
    assert command[command.index('--revision') + 1] == 'f0dd57a2e568089d396fecba819ab987da658bf0'
    assert command[command.index('--final') + 1] == str(ROOT.parent / 'HAS-Review-20261115-SFM-Joints-f0dd57a')
    outputs = [BASE / ('review-build' + suffix) for suffix in ['-stdout.log', '-stderr.log', '-process.json']]
    assert not any(path.exists() for path in outputs)
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=600,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    outputs[0].write_bytes(result.stdout)
    outputs[1].write_bytes(result.stderr)
    proof = {'command': command, 'exit': result.returncode, 'seconds': time.monotonic() - started,
             'command_file_sha256': hashlib.sha256(command_file.read_bytes()).hexdigest(),
             'passed': result.returncode == 0, 'graphics_requested': False}
    with outputs[2].open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(proof, indent=2))
    if result.returncode:
        print(result.stderr.decode('utf-8', errors='replace')[-6000:])
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
