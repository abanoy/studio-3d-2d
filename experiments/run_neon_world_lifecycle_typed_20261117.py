"""Actual root-owned hidden lifecycle regression; no native artist models."""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
FOLDER = REVIEW / 'output/neon-world-lifecycle-20261117-attempt2'
SCRIPT = 'experiments/neon_world_teardown_regression_20261117/neon_world_rail_lifecycle.gd'

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def main():
    safety = module(ROOT / 'experiments/run_neon_workspace_followup_20261117.py', 'lifecycle_root_safety')
    assert safety.sha(REVIEW / SCRIPT) == 'f033f975735efe5089dbadb478661f620dceeca4a1328ce090638747c03df202'
    assert safety.sha(REVIEW / 'src/world_selection.gd') == 'f5b877745a63cb4d1aa2ff8d40a05f456c4979664efc70d275599410dab07637'
    assert safety.sha(REVIEW / 'src/workspace_layout.gd') == '7da378b1147266fbecdabf63422e19b1ee06024c40083d6fcf4ed8e93540bcfd'
    runner = module(REVIEW / 'run.py', 'lifecycle_root_runner')
    FOLDER.mkdir(exist_ok=False)
    safety.closed(FOLDER, 'before')
    before = safety.sources()
    safety.save(FOLDER / 'source-before.json', before)
    records = []
    passed = False
    try:
        commands = [('parse', [str(safety.ENGINE), '--headless', '--path', str(REVIEW), '--log-file', str(FOLDER / 'parse-engine.log'),
                               '--script', 'res://' + SCRIPT, '--check-only'], 40),
                    ('app', runner.command(SCRIPT, extra=['--log-file', str(FOLDER / 'app-engine.log'), '--', str(FOLDER / 'case')]), 140)]
        for label, args, timeout in commands:
            safety.save(FOLDER / (label + '-command.json'), args)
            start = time.time_ns()
            p = subprocess.Popen(args, cwd=REVIEW, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            out, err = p.communicate(timeout=timeout)
            (FOLDER / (label + '-stdout.log')).write_bytes(out)
            (FOLDER / (label + '-stderr.log')).write_bytes(err)
            log = (out + err).decode('utf-8', 'replace')
            row = {'label': label, 'pid': p.pid, 'exit': p.returncode, 'retained_Popen_reaped': p.poll() is not None,
                   'timed_out': False, 'seconds': (time.time_ns() - start) / 1e9}
            safety.save(FOLDER / (label + '-process.json'), row)
            records.append(row)
            assert p.returncode == 0 and not any(word in log for word in ('ERROR:', 'SCRIPT ERROR', 'FAIL ', 'ObjectDB instances leaked')), log
            if label == 'app':
                receipt_path = Path(args[args.index('--receipt') + 1])
                receipt = json.loads(receipt_path.read_bytes())
                assert receipt['exit'] == 0 and all(receipt.get(k) is True for k in ('private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'))
                assert all(receipt.get(k) is False for k in ('desktop_switch_requested', 'foreground_child_observed'))
                report = json.loads((FOLDER / 'case/result.json').read_bytes())
                assert report['checks'] == 29 and report['failures'] == 0
                safety.save(FOLDER / 'private-receipt.json', receipt)
                safety.save(FOLDER / 'report.json', report)
                passed = True
            safety.closed(FOLDER, label + '-after')
    finally:
        safety.closed(FOLDER, 'after')
        after = safety.sources()
        safety.save(FOLDER / 'source-after.json', after)
        safety.save(FOLDER / 'verification.json', {'format': 'has_root_neon_world_lifecycle_actual_1',
             'passed': passed and before == after, 'processes': records, 'functional_source_files': len(before),
             'source_unchanged': before == after, 'full_suite_pass_claimed': False,
             'native_artist_assets_used': False})
        assert before == after
    print(json.dumps({'passed': passed, 'checks': 29 if passed else None, 'folder': str(FOLDER)}))

if __name__ == '__main__':
    main()
