"""Pinned Windows completed-import handle ownership with harmless actual children."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if os.name != 'nt':
        parser.error('This control exercises the pinned Windows process-map implementation.')
    folder = (options.output or ROOT/'output/source-import-owner'/str(time.time_ns())).resolve()
    assert folder.is_relative_to((ROOT/'output').resolve()) and not folder.exists()
    folder.mkdir(parents=True)
    names = ['src/source_import.gd', 'tests/source_import_owner_unit.gd',
             'tests/source_import_owner_worker.py', 'tests/verify_source_import_owner.py', 'run.py']
    def snapshot():
        return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    before = snapshot()
    environment = os.environ.copy()
    environment['HYBRID_PYTHON'] = str(Path(sys.executable).resolve())
    args = command('tests/source_import_owner_unit.gd', headless=True,
                   extra=['--log-file', str(folder/'engine.log')])
    (folder/'command.json').write_text(json.dumps(args, indent=2)+'\n', encoding='utf-8')
    process = subprocess.run(args, cwd=ROOT, env=environment, capture_output=True,
                             text=True, encoding='utf-8', errors='replace', timeout=45,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    console = process.stdout + process.stderr
    (folder/'console.log').write_text(console, encoding='utf-8')
    engine = (folder/'engine.log').read_text(encoding='utf-8', errors='replace')
    bad = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'FAIL ', 'ObjectDB instances leaked',
           'unclaimed string names', 'Pages in use exist at exit')
    assert process.returncode == 0 and not any(s in console+engine for s in bad), console+engine
    rows = [json.loads(line[len('SOURCE_IMPORT_OWNER '):]) for line in console.splitlines()
            if line.startswith('SOURCE_IMPORT_OWNER ')]
    assert len(rows) == 1
    result = rows[0]
    assert result['checks'] == 53 and result['failures'] == 0 and len(result['cases']) == 6
    assert result['authored_single_process_Python_only'] and not result['native_converter_or_GPU']
    assert result['source_sha256'] == before['src/source_import.gd'] and snapshot() == before
    report = {'format':'has_source_import_owner_1', 'passed':True, 'exit':process.returncode,
              'result':result, 'source_unchanged':True, 'source_sha256':before,
              'folder':str(folder), 'headless':True, 'native_conversion':False,
              'scope':'Actual harmless Python children and completed Windows map entries; app/pose doubles. No native conversion, rendering, live-child teardown or native fidelity claim.'}
    (folder/'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('SOURCE_IMPORT_OWNER_VERIFIED '+json.dumps({'passed':True, 'checks':53,
                                                    'verification':str(folder/'verification.json')}))


if __name__ == '__main__':
    main()
