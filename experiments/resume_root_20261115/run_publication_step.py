"""Run one reviewed metadata-only publication phase, preserving exact logs."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'output/resume-full-publication-f0dd57a-20261115'
RUN = ROOT / 'output/windows-canonical-bone-binding-20261115T225514304'
PYTHON = Path(r'C:\Program Files\Python313\python.exe')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['preflight', 'receipts', 'summary', 'finalize', 'consolidate'])
    phase = parser.parse_args().phase
    state = json.loads((RUN / 'state.json').read_bytes())
    assert state['status'] == 'passed' and state['suite_exit'] == 0 and state['source_unchanged']
    assert Path(sys.executable).resolve() == PYTHON.resolve()
    assert sha(PYTHON) == '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
    index = json.loads((BASE / 'SOURCE-RECIPE-INDEX.json').read_bytes())
    for row in index['files']:
        path = BASE / row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
    host = sha(RUN / 'authoritative-host-termination.json')
    raw_host = sha(RUN / 'authoritative-host-terminal.json')
    shared = ['--terminal-permission']
    if phase == 'preflight':
        script, extra = 'preflight_terminal.py', [*shared, '--host-proof-sha256', host, '--host-raw-sha256', raw_host]
    elif phase == 'receipts':
        script, extra = 'audit_receipts.py', [*shared, '--host-proof-sha256', host, '--host-raw-sha256', raw_host]
    elif phase == 'summary':
        script, extra = 'summarize_canonical.py', [*shared, '--host-proof', str(RUN / 'authoritative-host-termination.json'),
                '--host-sha256', host, '--receipt-inventory', str(BASE / 'receipt-audit/receipt-inventory.json'),
                '--receipt-sha256', sha(BASE / 'receipt-audit/receipt-inventory.json'),
                '--destination', str(BASE / 'actual-summary')]
    elif phase == 'finalize':
        script, extra = 'finalize_receipt_index.py', [*shared, '--inventory-sha256', sha(BASE / 'receipt-audit/receipt-inventory.json'),
                '--release-sha256', sha(RUN / 'graphics-lease-released.json')]
    else:
        script, extra = 'build_consolidated_packet.py', [*shared, '--summary-index-sha256', sha(BASE / 'actual-summary/INDEX.json'),
                '--audit-index-sha256', sha(BASE / 'receipt-audit/INDEX.json')]
    folder = Path(__file__).parent / 'actual-publication'
    folder.mkdir(exist_ok=True)
    outputs = [folder / (phase + suffix) for suffix in ['-stdout.log', '-stderr.log', '-process.json']]
    assert not any(path.exists() for path in outputs)
    command = [str(PYTHON), '-B', str(BASE / script), *extra]
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    outputs[0].write_bytes(result.stdout)
    outputs[1].write_bytes(result.stderr)
    proof = {'phase': phase, 'command': command, 'exit': result.returncode,
             'seconds': time.monotonic() - started, 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'script_sha256': sha(BASE / script), 'stdout_sha256': sha(outputs[0]),
             'stderr_sha256': sha(outputs[1]), 'passed': result.returncode == 0}
    with outputs[2].open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(proof, indent=2))
    if result.returncode:
        print(result.stderr.decode('utf-8', errors='replace')[-5000:])
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
