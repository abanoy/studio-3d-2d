"""Private metadata link/permission safety and existing headless recovery regressions."""
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
    folder = (options.output or ROOT / 'output/private-metadata' / str(time.time_ns())).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    reports = {}
    for name, marker in [('save_worker_unit', 'SAVE_WORKER_UNIT '),
                         ('private_metadata_unit', 'PRIVATE_METADATA_UNIT '),
                         ('recovery_journal_unit', 'RECOVERY_JOURNAL_UNIT '),
                         ('lesson_recovery_unit', 'LESSON_RECOVERY_UNIT '),
                         ('recovery_identity_unit', 'RECOVERY_IDENTITY_UNIT ')]:
        case = folder / name
        case.mkdir()
        process = subprocess.run(command('tests/' + name + '.gd', headless=True,
                                        extra=['--log-file', str(case / 'engine.log'), '--', str(case), *([str(os.getpid())] if name == 'recovery_identity_unit' else [])]),
                                 cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=65)
        log = process.stdout + process.stderr
        (case / 'console.log').write_text(log, encoding='utf-8')
        assert process.returncode == 0 and marker in log and not any(
            token in log for token in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked']), log
        report = json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)))
        assert report['failures'] == 0 and (report['checks'] > 0 or 'skipped' in report), report
        reports[name] = report
        print(name + ': ' + ('SKIPPED' if 'skipped' in report else 'PASS'), flush=True)
    sources = ['src/save_worker.gd', 'tools/save_sync.py', 'tools/metadata_commit.py', 'src/atomic_metadata.gd', 'src/recovery.gd', 'src/recovery_journal.gd',
               'src/lesson_store.gd', 'tests/private_metadata_unit.gd', 'tests/verify_private_metadata.py']
    result = dict(reports=reports, folder=str(folder),
                  scope='Headless metadata safety; graphical crash/reopen workflows run separately. No power-loss or hostile concurrent filesystem race certification.',
                  source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources})
    (folder / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
