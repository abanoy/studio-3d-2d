"""Read-only ordinary Open of the protected missing-face project, privately.

Captures require visual inspection; passing the automated checks alone does
not approve appearance. Native inputs and images stay in the local output.
"""
from pathlib import Path
import argparse
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
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if os.name != 'nt':
        parser.error('This owner-scene check uses the private Windows desktop launcher')
    project = options.project.resolve(strict=True)
    folder = (options.output or ROOT / 'output' / ('owner-face-' + str(time.time_ns()))).resolve()
    assert folder.is_relative_to(ROOT / 'output') and not folder.exists()
    folder.mkdir(parents=True)
    data = folder / 'Data'
    data.mkdir()
    environment = os.environ.copy()
    for key, leaf in [('APPDATA', 'Roaming'), ('LOCALAPPDATA', 'Local')]:
        profile = folder / 'User' / leaf
        profile.mkdir(parents=True)
        environment[key] = str(profile)
    args = command('tests/posed_bounds_owner_open.gd', extra=[
        '--log-file', str(folder / 'engine.log'), '--', str(project), str(data)])
    process = subprocess.run(args, cwd=ROOT, env=environment, capture_output=True,
                             timeout=230, creationflags=subprocess.CREATE_NO_WINDOW)
    raw = process.stdout + process.stderr
    (folder / 'launcher.log').write_bytes(raw)
    receipt = json.loads(Path(args[args.index('--receipt') + 1]).read_bytes())
    text = (folder / 'engine.log').read_text(encoding='utf-8', errors='replace')
    report = {'status': 'FAIL', 'exit': process.returncode, 'private_receipt': receipt}
    try:
        assert process.returncode == 0, text
        assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and receipt['private_window_seen']
        assert not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested']
        assert receipt['job_closed'] and receipt['desktop_closed']
        assert not any(error in text or error in raw.decode('utf-8', errors='replace') for error in
                       ['SCRIPT ERROR', 'SHADER ERROR', 'ERROR:', 'FAIL ', 'ObjectDB instances leaked']), text
        result = json.loads((data / 'private-ordinary-face-result.json').read_bytes())
        assert result['checks'] == 13 and result['failures'] == 0
        assert result['authored_world_preserved'] and result['shot_keys_preserved'] and result['Undo_count_preserved']
        assert result['readbacks_balanced'] and len(result['images']) == 4
        assert Path(result['user_profile']).resolve().is_relative_to(folder / 'User')
        report.update(status='CAPTURED_FOR_VISUAL_REVIEW', checks=13, captures=4,
                      authored_state_preserved=True, readbacks_balanced=True,
                      isolated_user_profile=True, visual_review_required=True)
    finally:
        (folder / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'folder': str(folder), **report}, indent=2))


if __name__ == '__main__':
    main()
