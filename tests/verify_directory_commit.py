"""Actual Godot directory saves: lock refusal, retry and a competing generation."""
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
from tools.has_project import save_lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    folder = (options.output or ROOT / 'output/directory-commit' / str(time.time_ns())).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    project = folder / 'project'
    reports = {}

    def run(label, frame, env=None):
        result_file = folder / (label + '.json')
        result = subprocess.run(command('tests/directory_commit_smoke.gd', headless=True,
                                       extra=['--log-file', str(folder / (label + '-engine.log')), '--',
                                              str(project), str(frame), str(result_file)]),
                                cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=30, env=env)
        log = result.stdout + result.stderr
        (folder / (label + '.log')).write_text(log, encoding='utf-8')
        assert result.returncode == 0 and 'DIRECTORY_COMMIT_SMOKE ' in log and 'ERROR:' not in log, log
        report = json.loads(result_file.read_bytes())
        assert not report['load_error'], report
        reports[label] = report
        return report

    assert run('initial', 0)['error'] == ''
    initial = (project / 'project.json').read_bytes()
    with save_lock(project / 'project.json'):
        report = run('blocked', 1)
        assert 'Another save' in report['error'] and report['frame'] == 0
        assert (project / 'project.json').read_bytes() == initial
        assert not (project / 'project.backup.json').exists()
    report = run('retry', 2)
    assert report['error'] == '' and report['frame'] == 2
    assert (project / 'project.backup.json').read_bytes() == initial
    if os.name == 'posix':
        # The shim commits a second valid generation using the real worker,
        # after Godot prepared its candidate but before its original promotion.
        shim = folder / 'competing-python'
        shim.write_text('#!' + sys.executable + '\n' +
                        'import json,os,sys\nfrom pathlib import Path\n' +
                        'sys.path.insert(0,' + repr(str(ROOT)) + ')\n' +
                        'from tools import directory_commit as dc\n' +
                        'root=Path(sys.argv[2]);doc=json.loads((root/"project.json").read_bytes());doc["editor"]["frame"]=7\n' +
                        'name="project.json.competing.tmp";(root/name).write_text(json.dumps(doc))\n' +
                        'result=dc.commit(root,name,dc.sha(root/"project.json"),dc.sha(root/name),True)\n' +
                        'assert result["ok"]\n' +
                        'os.execv(sys.executable,[sys.executable,*sys.argv[1:]])\n', encoding='utf-8')
        shim.chmod(0o700)
        env = dict(os.environ, HYBRID_PYTHON=str(shim))
        prior = (project / 'project.json').read_bytes()
        report = run('stale', 3, env)
        assert 'Another save changed' in report['error'] and report['frame'] == 7
        assert (project / 'project.backup.json').read_bytes() == prior
        reports['competing_generation'] = 'Real worker committed frame7 between Godot preparation and its original worker; frame3 refused.'
        killed = folder / 'killed-python'
        killed.write_text('#!' + sys.executable + '\n' +
                          'import os,signal,sys\nfrom pathlib import Path\nfrom unittest import mock\n' +
                          'sys.path.insert(0,' + repr(str(ROOT)) + ')\n' +
                          'from tools import directory_commit as dc\n' +
                          'original=dc.os.replace\n' +
                          'def replace(source,target):\n original(source,target)\n if Path(target).name=="project.json":os.kill(os.getpid(),signal.SIGKILL)\n' +
                          'with mock.patch.object(dc.os,"replace",side_effect=replace):dc.commit(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6]=="yes")\n', encoding='utf-8')
        killed.chmod(0o700)
        report = run('lost-status', 9, dict(os.environ, HYBRID_PYTHON=str(killed)))
        assert 'status' in report['error'] and report['frame']==9
        assert 'previous manifest preserved' not in report['error'].lower()
        assert json.loads((project/'project.backup.json').read_bytes())['editor']['frame']==7
    else:
        reports['competing_generation'] = 'SKIPPED: POSIX executable shim; native Windows gate remains'
    result = dict(reports=reports, folder=str(folder),
                  scope='Actual headless Godot/worker exclusion and optimistic generation check; not physical power-loss or hostile filesystem mutation certification.',
                  source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                                 ['src/storage.gd', 'tools/directory_commit.py', 'tools/has_project.py',
                                  'tests/directory_commit_smoke.gd', 'tests/verify_directory_commit.py']})
    (folder / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
